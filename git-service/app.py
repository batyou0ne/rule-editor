import asyncio
import base64
import os
from typing import Dict, List

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_API = "https://api.github.com"
ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "")
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app = FastAPI(title="FLINT Git Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PushRequest(BaseModel):
    repo: str                  # "owner/name"
    files: Dict[str, str]      # file path → plain-text content
    commit_message: str = "FLINT export"


class FilePushResult(BaseModel):
    path: str
    status: str  # "created" | "updated"


class PushResponse(BaseModel):
    repo_url: str
    branch: str
    version: str
    pushed: List[FilePushResult]


async def _send_alert(message: str) -> None:
    if not ALERT_WEBHOOK_URL:
        return
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(ALERT_WEBHOOK_URL, json={"text": message})
    except Exception:
        pass  # alert failure must never break the main flow


def _gh_headers() -> dict:
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


async def _next_version(client, repo: str, slug: str, branch: str, headers: dict) -> str:
    """Return the next version folder name (v1, v2, ...) for a given task slug."""
    res = await client.get(
        f"/repos/{repo}/contents/{slug}",
        headers=headers,
        params={"ref": branch},
    )
    if not res.is_success:
        return "v1"
    entries = res.json()
    if not isinstance(entries, list):
        return "v1"
    version_numbers = []
    for entry in entries:
        name = entry.get("name", "")
        if name.startswith("v") and name[1:].isdigit():
            version_numbers.append(int(name[1:]))
    next_n = max(version_numbers) + 1 if version_numbers else 1
    return f"v{next_n}"


@app.get("/health")
def health():
    return {"status": "ok", "token_configured": bool(GITHUB_TOKEN)}


@app.post("/push", response_model=PushResponse)
async def push(req: PushRequest):
    #! GITHUB TOKEN CHECK
    if not GITHUB_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="GITHUB_TOKEN is not configured on the server. "
                   "Add it to git-service/.env and restart the service.",
        )

    _, _, repo_name = req.repo.partition("/")
    if not repo_name:
        raise HTTPException(status_code=400, detail="repo must be 'owner/name'")

    headers = _gh_headers()

    #! CREATE A CLIENT
    async with httpx.AsyncClient(base_url=GITHUB_API, timeout=30.0) as client:

        #! REPO CHECK (if not create a new one)
        repo_res = await client.get(f"/repos/{req.repo}", headers=headers)
        if repo_res.status_code == 404:
            create_res = await client.post(
                "/user/repos",
                headers=headers,
                json={"name": repo_name, "private": False, "auto_init": True},
            )
            if not create_res.is_success:
                msg = create_res.json().get("message", create_res.text)
                raise HTTPException(
                    status_code=create_res.status_code,
                    detail=f"Failed to create repo: {msg}",
                )
        #! STATUS CODE CONTROL
        elif not repo_res.is_success:
            msg = repo_res.json().get("message", repo_res.text)
            raise HTTPException(
                status_code=repo_res.status_code,
                detail=f"GitHub error: {msg}",
            )

        # 2. Read default branch and repo URL
        repo_info_res = await client.get(f"/repos/{req.repo}", headers=headers)
        repo_data = repo_info_res.json()
        branch = repo_data.get("default_branch", "main")
        repo_url = repo_data.get("html_url", f"https://github.com/{req.repo}")

        #! If the repo is empty (no branches), delete and recreate with auto_init
        #! so GitHub creates the initial commit and the main branch exists.
        branch_res = await client.get(
            f"/repos/{req.repo}/branches/{branch}", headers=headers
        )
        if branch_res.status_code == 404:
            await client.delete(f"/repos/{req.repo}", headers=headers)
            create_res = await client.post(
                "/user/repos",
                headers=headers,
                json={"name": repo_name, "private": False, "auto_init": True},
            )
            if not create_res.is_success:
                msg = create_res.json().get("message", create_res.text)
                raise HTTPException(status_code=create_res.status_code,
                                    detail=f"Failed to reinitialise repo: {msg}")
            await asyncio.sleep(2)

            # Re-read repo info after reinit
            repo_info_res = await client.get(f"/repos/{req.repo}", headers=headers)
            repo_data = repo_info_res.json()
            branch = repo_data.get("default_branch", "main")
            repo_url = repo_data.get("html_url", repo_url)

        # Determine slug (first path component) and next version folder
        first_path = next(iter(req.files))
        slug = first_path.split("/")[0]
        version = await _next_version(client, req.repo, slug, branch, headers)

        # Rewrite paths: {slug}/file → {slug}/{version}/file
        versioned_files = {}
        for path, content in req.files.items():
            rest = "/".join(path.split("/")[1:])
            versioned_files[f"{slug}/{version}/{rest}"] = content

        #! PUSH EACH FILE
        pushed: List[FilePushResult] = []
        for path, content in versioned_files.items():
            encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")

            #? Fetch existing SHA so GitHub allows updating the file. Github collision protection.
            existing_res = await client.get(
                f"/repos/{req.repo}/contents/{path}",
                headers=headers,
                params={"ref": branch},
            )
            sha = existing_res.json().get("sha") if existing_res.is_success else None

            #! PUT BODY
            body: dict = {
                "message": req.commit_message,
                "content": encoded,
                "branch": branch,
            }
            if sha:
                body["sha"] = sha

            put_res = await client.put(
                f"/repos/{req.repo}/contents/{path}",
                headers=headers,
                json=body,
            )
            if not put_res.is_success:
                msg = put_res.json().get("message", put_res.text)
                raise HTTPException(
                    status_code=put_res.status_code,
                    detail=f"Failed to push {path}: {msg}",
                )

            pushed.append(FilePushResult(path=path, status="updated" if sha else "created"))

    return PushResponse(repo_url=repo_url, branch=branch, version=version, pushed=pushed)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    if exc.status_code >= 500 or "Failed to push" in str(exc.detail):
        await _send_alert(
            f":x: *FLINT git-service error*\n"
            f"Status: {exc.status_code}\n"
            f"Detail: {exc.detail}"
        )
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

#! Start the service
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8103"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
