import asyncio
import datetime as dt
import json
import logging
import os
import shutil
import socket
import subprocess
import threading
import time
import traceback
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SERVICE_NAME = "eflint-server"
APP_ENV = os.getenv("APP_ENV", "dev")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def _to_python_log_level(level: str) -> int:
    normalized = (level or "INFO").upper()
    if normalized == "WARN":
        normalized = "WARNING"
    return getattr(logging, normalized, logging.INFO)


def _configure_logging() -> logging.Logger:
    service_logger = logging.getLogger(SERVICE_NAME)
    service_logger.setLevel(_to_python_log_level(LOG_LEVEL))
    service_logger.propagate = False

    if not service_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        service_logger.addHandler(handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    return service_logger


logger = _configure_logging()


def _log(level: str, message: str, **fields) -> None:
    event = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "level": level,
        "service": SERVICE_NAME,
        "env": APP_ENV,
        "message": message,
        **fields,
    }
    logger.log(_to_python_log_level(level), json.dumps(event, default=str))


def _parse_allowed_origins() -> list[str]:
    raw = os.getenv(
        "AUTH_ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:8888,http://127.0.0.1:5173,http://127.0.0.1:8888",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


EFLINT_HOST = "127.0.0.1"
EFLINT_DEFAULT_SPEC_PATH = Path(os.getenv("EFLINT_SPEC_PATH", "/app/default_spec.eflint"))
EFLINT_SESSIONS_DIR = Path(os.getenv("EFLINT_SESSIONS_DIR", "/tmp/eflint_sessions"))
EFLINT_BASE_PORT = int(os.getenv("EFLINT_BASE_PORT", "9001"))
EFLINT_MAX_SESSIONS = int(os.getenv("EFLINT_MAX_SESSIONS", "10"))
EFLINT_SESSION_TTL_SECONDS = int(os.getenv("EFLINT_SESSION_TTL_SECONDS", "1800"))
EFLINT_CLEANUP_INTERVAL_SECONDS = int(os.getenv("EFLINT_CLEANUP_INTERVAL_SECONDS", "60"))
EFLINT_CONNECT_RETRIES = int(os.getenv("EFLINT_CONNECT_RETRIES", "30"))
EFLINT_CONNECT_RETRY_DELAY_SECONDS = float(os.getenv("EFLINT_CONNECT_RETRY_DELAY_SECONDS", "0.1"))
EFLINT_STARTUP_DELAY_SECONDS = float(os.getenv("EFLINT_STARTUP_DELAY_SECONDS", "0.3"))

SESSION_HEADER_NAME = "X-Session-Id"


@dataclass
class SessionInfo:
    session_id: str
    process: subprocess.Popen
    port: int
    spec_path: Path
    created_at: float
    last_used_at: float


_sessions: dict[str, SessionInfo] = {}
_sessions_lock = threading.Lock()
_cleanup_task: asyncio.Task | None = None


# ---------------------------------------------------------------------------
# Session lifecycle
# ---------------------------------------------------------------------------

def _is_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((EFLINT_HOST, port))
            return True
        except OSError:
            return False


def _allocate_port_locked() -> int:
    used_ports = {session.port for session in _sessions.values()}
    for offset in range(max(EFLINT_MAX_SESSIONS * 4, 20)):
        port = EFLINT_BASE_PORT + offset
        if port not in used_ports and _is_port_available(port):
            return port
    raise RuntimeError("no free port available for a new eFLINT session")


def _copy_default_spec(destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if EFLINT_DEFAULT_SPEC_PATH.exists():
        shutil.copyfile(EFLINT_DEFAULT_SPEC_PATH, destination)
    else:
        destination.write_text("", encoding="utf-8")


def _start_eflint(port: int, spec_path: Path) -> subprocess.Popen:
    proc = subprocess.Popen(
        ["/usr/bin/eflint-server", str(spec_path), str(port)],
        stdout=None,
        stderr=None,
    )
    time.sleep(EFLINT_STARTUP_DELAY_SECONDS)
    return proc


def _terminate_process(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def _destroy_session(session: SessionInfo) -> None:
    _terminate_process(session.process)
    shutil.rmtree(session.spec_path.parent, ignore_errors=True)


def _touch_session(session: SessionInfo) -> None:
    session.last_used_at = time.time()


def _get_session(session_id: str) -> SessionInfo:
    with _sessions_lock:
        session = _sessions.get(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail=f"unknown session '{session_id}'")
        _touch_session(session)
        return session


def _create_session(session_id: str | None = None) -> SessionInfo:
    now = time.time()
    with _sessions_lock:
        if len(_sessions) >= EFLINT_MAX_SESSIONS:
            raise HTTPException(status_code=429, detail="maximum number of sessions reached")

        sid = session_id or uuid.uuid4().hex
        if sid in _sessions:
            raise HTTPException(status_code=409, detail=f"session '{sid}' already exists")

        port = _allocate_port_locked()
        spec_path = EFLINT_SESSIONS_DIR / sid / "spec.eflint"
        _copy_default_spec(spec_path)
        process = _start_eflint(port, spec_path)
        session = SessionInfo(
            session_id=sid,
            process=process,
            port=port,
            spec_path=spec_path,
            created_at=now,
            last_used_at=now,
        )
        _sessions[sid] = session
        _log("INFO", "session_created", session_id=sid, port=port)
        return session


def _delete_session(session_id: str) -> None:
    with _sessions_lock:
        session = _sessions.pop(session_id, None)
    if session is None:
        raise HTTPException(status_code=404, detail=f"unknown session '{session_id}'")
    _destroy_session(session)
    _log("INFO", "session_deleted", session_id=session_id)


def _cleanup_expired_sessions() -> None:
    now = time.time()
    expired: list[SessionInfo] = []
    with _sessions_lock:
        expired_ids = [
            sid
            for sid, session in _sessions.items()
            if now - session.last_used_at > EFLINT_SESSION_TTL_SECONDS
        ]
        for sid in expired_ids:
            expired.append(_sessions.pop(sid))

    for session in expired:
        _log("INFO", "session_expired_cleanup", session_id=session.session_id)
        _destroy_session(session)


async def _cleanup_loop() -> None:
    while True:
        await asyncio.sleep(EFLINT_CLEANUP_INTERVAL_SECONDS)
        _cleanup_expired_sessions()


def _shutdown_all_sessions() -> None:
    with _sessions_lock:
        sessions = list(_sessions.values())
        _sessions.clear()
    _log("INFO", "shutdown_sessions_cleanup", session_count=len(sessions))
    for session in sessions:
        _destroy_session(session)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _cleanup_task
    EFLINT_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    _cleanup_task = asyncio.create_task(_cleanup_loop())
    _log("INFO", "startup", log_level=LOG_LEVEL)
    yield
    if _cleanup_task is not None:
        _cleanup_task.cancel()
        try:
            await _cleanup_task
        except asyncio.CancelledError:
            pass
    _shutdown_all_sessions()


# ---------------------------------------------------------------------------
# TCP helper
# ---------------------------------------------------------------------------

def _send_command(session: SessionInfo, payload: dict) -> dict:
    if session.process.poll() is not None:
        raise RuntimeError(f"session '{session.session_id}' is no longer running")

    line = json.dumps(payload) + "\n"
    sock = None
    for _ in range(EFLINT_CONNECT_RETRIES):
        try:
            sock = socket.create_connection((EFLINT_HOST, session.port), timeout=1.0)
            break
        except OSError:
            time.sleep(EFLINT_CONNECT_RETRY_DELAY_SECONDS)
    if sock is None:
        raise RuntimeError(f"could not connect to eflint-server for session '{session.session_id}'")

    with sock:
        sock.sendall(line.encode("utf-8"))
        chunks = []
        while True:
            data = sock.recv(65536)
            if not data:
                break
            chunks.append(data)
    raw = b"".join(chunks).decode("utf-8").strip()
    return json.loads(raw)


def _execute(session_id: str, payload: dict) -> dict:
    session = _get_session(session_id)
    try:
        result = _send_command(session, payload)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if result.get("response") == "invalid input":
        raise HTTPException(status_code=422, detail=result)
    if result.get("response") == "invalid command":
        raise HTTPException(status_code=400, detail=result)
    return result


def _append_to_session_spec(session_id: str, text: str) -> None:
    session = _get_session(session_id)
    with session.spec_path.open("a", encoding="utf-8") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")


def _require_session_id(x_session_id: str | None) -> str:
    if not x_session_id:
        raise HTTPException(status_code=400, detail=f"missing {SESSION_HEADER_NAME} header")
    return x_session_id


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

app = FastAPI(title="eFLINT server API", lifespan=lifespan)
SessionHeader = Annotated[str | None, Header(alias=SESSION_HEADER_NAME)]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    started = time.perf_counter()
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as exc:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        _log(
            "ERROR",
            "request_failed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=500,
            duration_ms=duration_ms,
            error_type=type(exc).__name__,
            error_message=str(exc),
            stack_trace=traceback.format_exc(),
        )
        raise

    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    if request.url.path == "/health":
        level = "DEBUG"
    else:
        level = "ERROR" if status_code >= 500 else "WARN" if status_code >= 400 else "INFO"
    _log(
        level,
        "health_check" if request.url.path == "/health" else "request_completed",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=status_code,
        duration_ms=duration_ms,
    )
    return response


class StatementRequest(BaseModel):
    text: str


class PhrasesRequest(BaseModel):
    text: str


class RevertRequest(BaseModel):
    value: int = -1
    destructive: bool = False


class CreateSessionRequest(BaseModel):
    session_id: str | None = None


@app.post("/sessions")
def create_session(req: CreateSessionRequest | None = None):
    session = _create_session(req.session_id if req else None)
    return {
        "session_id": session.session_id,
        "port": session.port,
        "spec_path": str(session.spec_path),
        "created_at": session.created_at,
        "last_used_at": session.last_used_at,
    }


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    _delete_session(session_id)
    return {"status": "deleted", "session_id": session_id}


@app.get("/sessions")
def list_sessions():
    with _sessions_lock:
        sessions = [
            {
                "session_id": session.session_id,
                "port": session.port,
                "spec_path": str(session.spec_path),
                "created_at": session.created_at,
                "last_used_at": session.last_used_at,
                "running": session.process.poll() is None,
            }
            for session in _sessions.values()
        ]
    return {
        "count": len(sessions),
        "max_sessions": EFLINT_MAX_SESSIONS,
        "sessions": sessions,
    }


@app.post("/statement")
def add_statement(req: StatementRequest, x_session_id: SessionHeader = None):
    session_id = _require_session_id(x_session_id)
    return _execute(session_id, {"command": "phrase", "text": req.text})


@app.post("/statements")
def add_statements(req: PhrasesRequest, x_session_id: SessionHeader = None):
    session_id = _require_session_id(x_session_id)
    return _execute(session_id, {"command": "phrases", "text": req.text})


@app.post("/spec/register")
def register_spec(req: PhrasesRequest, x_session_id: SessionHeader = None):
    session_id = _require_session_id(x_session_id)
    result = _execute(session_id, {"command": "phrases", "text": req.text})
    if not result.get("errors"):
        _append_to_session_spec(session_id, req.text)
    return result


@app.post("/query/enabled")
def query_enabled(req: StatementRequest, x_session_id: SessionHeader = None):
    session_id = _require_session_id(x_session_id)
    return _execute(session_id, {"command": "phrase", "text": req.text})


@app.post("/reset")
def reset_state(req: RevertRequest, x_session_id: SessionHeader = None):
    session_id = _require_session_id(x_session_id)
    return _execute(session_id, {"command": "revert", "value": req.value, "destructive": req.destructive})


@app.get("/status")
def get_status(x_session_id: SessionHeader = None):
    session_id = _require_session_id(x_session_id)
    return _execute(session_id, {"command": "status"})


@app.get("/facts")
def get_facts(x_session_id: SessionHeader = None):
    session_id = _require_session_id(x_session_id)
    return _execute(session_id, {"command": "facts"})


@app.get("/types")
def get_types(x_session_id: SessionHeader = None):
    session_id = _require_session_id(x_session_id)
    return _execute(session_id, {"command": "types"})


@app.get("/history")
def get_history(x_session_id: SessionHeader = None):
    session_id = _require_session_id(x_session_id)
    return _execute(session_id, {"command": "history"})


@app.get("/trace-heads")
def get_trace_heads(x_session_id: SessionHeader = None):
    session_id = _require_session_id(x_session_id)
    return _execute(session_id, {"command": "trace-heads"})


@app.get("/health")
def health():
    return {"status": "ok"}
