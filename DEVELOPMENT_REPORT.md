# Development Report — FLINT Rule Editor
### Branch: `feature/inspect-export-git-service`

---

## Task 1 — Server-Side GitHub Integration

**The problem:** The original design required every user to paste their own GitHub Personal Access Token into the browser each time they wanted to push files. This is bad UX and bad security — tokens are sensitive credentials that should never live in a browser form.

**What we built:** A standalone Python/FastAPI microservice called `git-service` that holds the GitHub token on the server. The browser never sees the token. Users just type a repo name and click Push.

### How it works end-to-end

1. The user fills in `owner/repo` in the **Inspect & Export** tab and clicks **Push to GitHub**.
2. The Vue frontend calls `POST /git-service/push` with a JSON body containing the repo name, file contents, and a commit message.
3. The Vite dev proxy (or nginx in production) forwards this to the git-service on port 8103.
4. `git-service/app.py` picks up the request, reads `GITHUB_TOKEN` from its `.env` file, and calls the GitHub REST API on behalf of the user.
5. If the repo doesn't exist yet, it creates it automatically with `auto_init: true` so it has an initial commit and a valid `main` branch.
6. Each file is pushed via `PUT /repos/{owner}/{repo}/contents/{path}`. If the file already exists, its SHA is fetched first (GitHub requires this to update a file without conflict).
7. The response returns the repo URL, the branch, the version folder used, and a per-file status list. The frontend shows this as a log.

### Files

| File | Purpose |
|------|---------|
| `git-service/app.py` | The entire service — FastAPI app, GitHub API calls, version logic, alert hook |
| `git-service/Dockerfile` | Packages the service as a container (`python:3.11-slim`, runs via uvicorn) |
| `git-service/requirements.txt` | `fastapi`, `uvicorn`, `httpx`, `pydantic`, `python-dotenv` |
| `git-service/.env.example` | Template — admin copies this to `.env` and sets `GITHUB_TOKEN` |
| `gui/src/views/ExportInspectView.vue` | New UI tab — push panel, file inspector, export-to-ZIP button |
| `gui/src/App.vue` | Registers the new Inspect & Export route/tab |

### Why Python / FastAPI?

The rest of the backend (auth-service, mongo-api, flint-to-eflint) is already Python/FastAPI. Staying consistent means the same Dockerfile pattern, the same health-check convention, the same `python-dotenv` config loading, and no new runtime to maintain.

---

## Task 2 — Automatic Version Folders (v1, v2, v3…)

**The problem:** Every time a task was pushed to GitHub, the files were overwritten in place. There was no history of what the task looked like at push time — just the latest state.

**What we built:** Every push now creates a new numbered subfolder (`v1`, `v2`, `v3`, …) inside the task's folder. The first push creates `v1/`, the second creates `v2/`, and so on. Old versions are never touched.

### How it works

Before pushing any files, `git-service/app.py` calls `_next_version()` (lines 68–86):

1. It calls `GET /repos/{owner}/{repo}/contents/{slug}` to list what's already in the task's top-level folder on GitHub.
2. It scans the folder names for entries that match the pattern `v` + a number (e.g. `v1`, `v2`).
3. It returns the next number: if `v1` and `v2` exist, it returns `v3`.
4. All incoming file paths are then rewritten from `{slug}/file.txt` to `{slug}/v3/file.txt` before being pushed.

### What the repo looks like after two pushes

```
batyou0ne/rule-editor-github-pushes/
└── rental_subsidy/
    ├── v1/
    │   ├── README.md
    │   ├── metadata.json
    │   ├── flint/frames.json
    │   └── eflint/specification.eflint
    └── v2/
        ├── README.md          ← updated version
        ├── metadata.json
        ├── flint/frames.json
        └── eflint/specification.eflint
```

### Files

| File | Lines | What it does |
|------|-------|-------------|
| `git-service/app.py` | 68–86 | `_next_version()` — reads GitHub, finds highest vN, returns next |
| `git-service/app.py` | 166–174 | Path rewrite loop — prepends `{slug}/{version}/` to every file path |

---

## Task 3 — Multi-Task Slug Prefix

A related fix that came up during testing: two different tasks (e.g. `vfl_demo` and `rental_subsidy`) were overwriting each other because both sent a file called `README.md` with no prefix.

**Fix:** The frontend's `buildFileMap()` in `ExportInspectView.vue` converts the task title to a URL-safe slug (spaces → underscores, lowercased) and prefixes every file path before sending to git-service. So `README.md` becomes `rental_subsidy/README.md`, which then becomes `rental_subsidy/v2/README.md` after versioning.

---

## Task 4 — Docker Compose Integration

**The problem:** Before this, the git-service had to be started manually (`python3 app.py`) and the GUI had to be run with `npm run dev`. There was no single-command way to start the full production stack.

**What we built:** Added `gui` and `git-service` as first-class services in `docker-compose.yml`. Now `docker compose up -d` starts everything.

### GUI container

The GUI is built as a two-stage Docker image:

1. **Stage 1 (build):** `node:20-alpine` runs `npm install` + `npm run build`, producing a static `/dist` folder.
2. **Stage 2 (serve):** `nginxinc/nginx-unprivileged:1.23-alpine` serves the static files and reverse-proxies API calls to the backend services by name (Docker internal DNS).

The nginx config (`gui/nginx.conf`) routes:
- `/auth/` → `http://auth-service:8001/`
- `/mongo-api/` → `http://mongo-api:8002/`
- `/git-service/` → `http://git-service:8103/`
- Everything else → `index.html` (SPA fallback for Vue Router)

The `gui` service has `depends_on` with `condition: service_healthy` for `auth-service`, `mongo-api`, and `git-service` — it won't start until all three pass their health checks.

### Files

| File | Change |
|------|--------|
| `docker-compose.yml` | Added `gui` and `git-service` service definitions |
| `gui/Dockerfile` | Two-stage build (was Node 18, upgraded to Node 20 to fix `npm install` EBADPLATFORM errors) |
| `gui/nginx.conf` | New — production reverse proxy config |
| `.env.stack.example` | Added `GITHUB_TOKEN` field |

---

## Task 5 — Monitoring Integration (Grafana + Prometheus)

**Context:** The project already had a monitoring stack in `deploy/monitoring/` with Prometheus, Grafana, Loki, and a blackbox exporter. It was scraping the existing services but not the new git-service.

**What we added:** One line in `deploy/monitoring/prometheus.yml` adds `http://git-service:8103/health` to the existing `service-health` scrape job. The blackbox exporter checks that this URL returns HTTP 2xx every 15 seconds. If the service goes down, Prometheus detects it and Grafana can alert on it.

Access:
- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`

### Files

| File | Change |
|------|--------|
| `deploy/monitoring/prometheus.yml` | Added `http://git-service:8103/health` to the scrape target list |

---

## Task 6 — Webhook Alerts on Push Failure

**The problem:** If a push to GitHub fails (token expired, rate limit, GitHub outage), it fails silently — the admin has no idea unless a user complains.

**What we built:** A lightweight alert hook in `git-service/app.py`. When a push fails, the service POSTs a message to `ALERT_WEBHOOK_URL`. This is intentionally provider-agnostic: it works with Slack, Discord, Microsoft Teams, or any custom webhook — whatever the admin configures. If the URL is not set, alerts are silently skipped.

The message format is plain JSON `{"text": "..."}` which Slack and Discord both accept natively.

### When an alert fires

- Any HTTP exception with status ≥ 500
- Any `"Failed to push"` error (GitHub rejected a file write)

### Files

| File | Lines | What it does |
|------|-------|-------------|
| `git-service/app.py` | 50–57 | `_send_alert()` — fires the webhook POST |
| `git-service/app.py` | 215–224 | FastAPI exception handler — decides when to trigger an alert |
| `git-service/.env.example` | — | Documents `ALERT_WEBHOOK_URL` — leave empty to disable |

---

## Task 7 — Admin Guide: How to Change the Target Repo

**What we wrote:** `docs/change-repo-guide.md` — a two-part guide:

- **For users** (no technical setup): explains that the repo field in the UI is all they need to fill in. Describes what happens if the repo doesn't exist (auto-created), and shows the folder structure they'll see on GitHub.
- **For administrators**: step-by-step instructions for generating a new Classic PAT (not fine-grained — fine-grained tokens lack the required scopes), updating `.env.stack` or `git-service/.env`, restarting the service, and verifying with `curl /health`.

Key warnings documented: the token must start with `ghp_`, must have the full `repo` scope, and must never be committed to git (`.gitignore` already covers `.env` and `.env.stack`).
