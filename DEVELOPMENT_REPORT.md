# Development Report: Inspect & Export Feature

**Project:** FLINT Rule Editor — University of Amsterdam  
**Author:** Batuhan Keskin  
**Date:** July 2026  

---

## What Was Built

### 1. Inspect & Export Tab (front-end)

A new **Inspect & Export** tab was added to the navigation bar (`gui/src/views/ExportInspectView.vue`). It displays the currently loaded interpretation in three collapsible panels:

- **Metadata** — title, description, editor, task IRI, frame counts
- **FLINT Frames** — filterable list of all facts, acts, and claim-duties
- **eFLINT Specification** — generated eFLINT code with copy button

Two export actions are available:

- **Export to folder** — downloads a ZIP containing `metadata.json`, `flint/frames.json`, and `eflint/specification.eflint`
- **Push to GitHub** — sends files to the git-service back-end, which pushes them to a GitHub repository. Each task is stored in its own subfolder (e.g. `rental_subsidy/README.md`) so multiple exports coexist in one repo.

### 2. Git Service (back-end)

A new Python/FastAPI micro-service (`git-service/`) handles all GitHub communication server-side. The GitHub token is stored in `git-service/.env` — the browser never sees it.

**Endpoints:**
- `GET /health` — check if service is running and token is configured
- `POST /push` — accepts `{ repo, files, commit_message }`, creates the repo if needed, and pushes all files

The service is included in `docker-compose.yml` and starts with `docker compose up -d`.

### 3. Data Model Scripts (CLI)

Two Python scripts split and reassemble the large export JSON:

```bash
python3 scripts/split.py export.json          # → model_v1_2026-07-13/
python3 scripts/combine.py model_v1_2026-07-13/  # → combined.json
```

Output folder contains: `metadata.json`, `FLINT_spec.json`, `eflint.eflint`, `eflint_meta.json`.  
Round-trip verified — all fields preserved.

---

## Files Changed

| File | Change |
|---|---|
| `gui/src/views/ExportInspectView.vue` | New — Inspect & Export tab |
| `gui/src/components/NavigationBar.vue` | Added tab registration |
| `gui/package.json` | Added `jszip` dependency |
| `gui/vite.config.js` | Added `/git-service` proxy |
| `gui/Dockerfile` + `gui/nginx.conf` | Production nginx config with proxy routes |
| `git-service/app.py` | New — FastAPI git service |
| `git-service/requirements.txt` | New |
| `git-service/.env.example` | New |
| `git-service/Dockerfile` | New |
| `docker-compose.yml` | Added `gui` and `git-service` services |
| `scripts/split.py` | New |
| `scripts/combine.py` | New |
| `.env.stack.example` | Added `GITHUB_TOKEN` |

---

## How to Run

```bash
# Start everything
docker compose up -d --build

# GUI available at http://localhost:5173
```

For local development without Docker:
```bash
# Terminal 1 — front-end
cd gui && npm run dev

# Terminal 2 — git service
cd git-service && source .venv/bin/activate && python3 app.py
```
