# Development Report: Inspect & Export Feature + Data Model Scripts

**Project:** FLINT Rule Editor — University of Amsterdam  
**Author:** Batuhan Keskin  
**Date:** 12 July 2026  
**Branch:** main  

---

## 1. Task Overview

The supervisor assigned the following improvements:

**Front-end**
- Create a new tab displaying metadata, FLINT frames, and eFLINT code in collapsible panels
- Add a button to export the project (first step: local filesystem as a folder/ZIP)
- Add a button to push directly to a git service

**Back-end**
- Make a connection with git via REST API linking front-end to the git service

**Data model**
- Analyse the JSON export structure and separate it into three parts: metadata, FLINT, eFLINT
- Write scripts to split the large JSON into those parts
- Write scripts to combine them back together
- Auto-generate metadata: export datetime, name/version
- Naming convention: `model_v<N>_<date>/`, `FLINT_spec`, `eflint.eflint`, `metadata`

---

## 2. Summary of Changes

| Area | File / Location | Status |
|---|---|---|
| New Vue tab | `gui/src/views/ExportInspectView.vue` | ✅ New file |
| Tab registration | `gui/src/components/NavigationBar.vue` | ✅ Modified |
| New dependency | `gui/package.json` (jszip) | ✅ Added |
| Split script | `scripts/split.py` | ✅ New file |
| Combine script | `scripts/combine.py` | ✅ New file |
| Git service | `git-service/app.py` | ✅ New file |
| Git service config | `git-service/.env.example`, `Dockerfile` | ✅ New files |
| Vite proxy | `gui/vite.config.js` (`/git-service`) | ✅ Modified |
| Documentation | `DEVELOPMENT_REPORT.md` | ✅ This file |

---

## 3. Front-End: Inspect & Export Tab

### 3.1 What was built

A new seventh tab — **Inspect & Export** — was added to the navigation bar. It shows all data layers of the currently loaded interpretation in one place, and provides two export paths.

**File:** `gui/src/views/ExportInspectView.vue` (722 lines)

### 3.2 Tab registration

**File:** `gui/src/components/NavigationBar.vue`

```js
import ExportInspectView from "../views/ExportInspectView.vue";

// Added to views array in data():
{
  id: 6,
  label: "Inspect & Export",
  component: markRaw(ExportInspectView),
  completed: false,
  icon: 'mdi-export-variant'
}
```

`markRaw()` prevents Vue from wrapping the component object in a reactive Proxy — consistent with all other tabs in the project.

### 3.3 Collapsible panels

Four collapsible `q-expansion-item` panels are shown when an interpretation is loaded:

| Panel | Default | Contents |
|---|---|---|
| Push to GitHub | Collapsed | Token input, repo input, commit message, progress log |
| Metadata | Open | Task title, description, editor, IRI, frame counts |
| FLINT Frames | Open | Filterable list of all facts, acts, claim-duties with expandable detail |
| eFLINT Specification | Open | Generated eFLINT code block with copy button and line count |

If no interpretation is loaded, an empty state message is shown instead.

### 3.4 Data sources (Vuex store — read-only)

```
$store.state.task                  → Metadata panel
$store.state.frames                → FLINT Frames panel
$store.state.executableEflintBase  → eFLINT Specification panel
```

The view never writes to the store — it has zero side effects on application state.

### 3.5 New dependency: JSZip

```bash
npm install jszip --save
```

Used to build a multi-file ZIP archive in the browser without a server. The project already had `file-saver` which handles the download step (`saveAs(blob, filename)`).

---

## 4. Front-End: Export to Folder (ZIP)

Clicking **Export to folder** calls `exportToFolder()`, which:

1. Calls `buildFileMap()` to assemble the file contents
2. Creates a ZIP with JSZip
3. Triggers a browser download via `file-saver`

**ZIP structure:**
```
<task-slug>_<timestamp>.zip
├── README.md                      ← auto-generated with title and export date
├── metadata.json                  ← title, description, editor, task IRI, exported_at
├── flint/
│   └── frames.json                ← all frames serialised via .toFlatObject()
└── eflint/
    └── specification.eflint       ← plain-text eFLINT code
```

`buildFileMap()` is shared between the ZIP export and the GitHub push to avoid code duplication.

---

## 5. Front-End: Push to GitHub

Clicking **Push to GitHub** opens a panel. The user enters a repository name and clicks Push. The browser sends the files to the `git-service` back-end, which pushes them to GitHub using a token stored server-side. The user never handles a GitHub token.

### 5.1 Authentication

A GitHub **Personal Access Token** with `repo` scope is stored in `git-service/.env` on the server. The service reads it at startup via `python-dotenv`. The browser never sees the token. The repository name is stored in the browser's `localStorage` for convenience, but that information is not sensitive.

### 5.2 Push flow

```
1. GET  /repos/{owner}/{repo}           → check if repo exists
2. POST /user/repos                     → create it automatically if 404
3. GET  /repos/{owner}/{repo}           → read default branch name
4. For each file:
     GET /repos/{owner}/{repo}/contents/{path}  → fetch existing SHA (if file exists)
     PUT /repos/{owner}/{repo}/contents/{path}  → create or update file
```

The SHA from step 4 is required by GitHub when updating an existing file. Creating a new file does not need it.

### 5.3 UTF-8 safe base64 encoding

The GitHub API requires file content as base64. Standard `btoa()` fails on non-ASCII characters (e.g. `€` in eFLINT code). Safe pattern used:

```js
btoa(unescape(encodeURIComponent(content)))
```

### 5.4 Progress log

Each step appends a colour-coded entry to a dark terminal-style log rendered inside the panel:

| Colour | Type | Example |
|---|---|---|
| Green | `ok` | `✓ flint/frames.json` |
| Red | `error` | Failed to push — error message |
| Yellow | `warn` | Repository not found — creating it… |
| Blue-grey | `info` | Checking repository owner/name… |

On success, a toast notification appears with an **Open repo** button.

### 5.5 Location in codebase

```
gui/src/views/ExportInspectView.vue
└── methods
    ├── buildFileMap()     line ~435   shared file map
    └── pushToGithub()     line ~468   GitHub REST API calls
```

---

## 6. Back-End: Git Service

### Architecture

GitHub communication is handled by a dedicated Python micro-service — `git-service/` — consistent with the other back-end services in the project (`mongo-api`, `auth-service`, `eflint_server`).

```
Browser → Vite proxy (/git-service) → FastAPI (port 8103) → GitHub REST API → GitHub repository
```

The GitHub Personal Access Token is stored in `git-service/.env` on the server. The browser never sees or sends the token.

### Files

| File | Purpose |
|---|---|
| `git-service/app.py` | FastAPI application — one endpoint: `POST /push` |
| `git-service/requirements.txt` | Python dependencies (fastapi, uvicorn, httpx, pydantic, python-dotenv) |
| `git-service/.env.example` | Template — copy to `.env` and set `GITHUB_TOKEN` |
| `git-service/Dockerfile` | Container definition for deployment |

### API

**`GET /health`**

Returns `{ "status": "ok", "token_configured": true/false }`. Useful for checking the service is running and the token is set.

**`POST /push`**

Request body:
```json
{
  "repo": "owner/repository-name",
  "files": {
    "README.md": "# My project\n...",
    "metadata.json": "{ ... }",
    "flint/frames.json": "[ ... ]",
    "eflint/specification.eflint": "Fact ..."
  },
  "commit_message": "FLINT export: 2026-07-13"
}
```

Successful response:
```json
{
  "repo_url": "https://github.com/owner/repository-name",
  "branch": "main",
  "pushed": [
    { "path": "README.md", "status": "created" },
    { "path": "metadata.json", "status": "updated" }
  ]
}
```

Error responses are standard HTTP status codes with a `detail` field describing the problem.

### Push flow (server-side)

The service replicates — server-side — the same GitHub REST API flow that was previously in the browser:

1. `GET /repos/{owner}/{repo}` — check if repository exists
2. `POST /user/repos` — create it with `auto_init: true` if it doesn't exist
3. `GET /repos/{owner}/{repo}` — read `default_branch` and `html_url`
4. For each file:
   - `GET /repos/{owner}/{repo}/contents/{path}` — fetch existing SHA (needed for updates)
   - `PUT /repos/{owner}/{repo}/contents/{path}` — create or update the file

File content is base64-encoded using Python's `base64.b64encode(content.encode("utf-8"))`, which is fully UTF-8 safe (equivalent to the `btoa(unescape(encodeURIComponent(...)))` pattern used in JavaScript).

### Setup

```bash
cd git-service

# Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env: set GITHUB_TOKEN to a Classic PAT with 'repo' scope

# Run
python3 app.py
# Service is now available at http://localhost:8103
```

Or with Docker:
```bash
docker build -t flint-git-service .
docker run -p 8103:8103 --env-file .env flint-git-service
```

### Front-end changes

`ExportInspectView.vue` was updated to call the service instead of GitHub directly:

- **Removed**: Personal Access Token input field and eye-toggle button
- **Added**: Info banner: "Your GitHub token is stored on the server — you never need to enter it here."
- **Changed**: `pushToGithub()` now sends one `POST /git-service/push` request with all files at once
- **Simplified**: `localStorage` no longer stores or loads the token
- **Vite proxy** (`gui/vite.config.js`): `/git-service/*` → `http://localhost:8103/*`

### Security improvement

| Before | After |
|---|---|
| Token entered by user in browser field | Token stored in `.env` on server |
| Token stored in `localStorage` | Never reaches the browser |
| All GitHub API calls made from browser | All GitHub API calls made from server |
| Token visible in browser dev tools Network tab | Not visible anywhere in the browser |

---

## 7. Data Model Scripts

### 7.1 JSON structure analysis

The FLINT Rule Editor export file has the following top-level structure:

```
{
  task_id             — IRI identifying the task
  metadata            — owner, title, created_at, modified_at
  flint_spec          — id, label, description, hasEditor, sourceDocs, frames, interpretation
  saved_artifact      — pre-serialised flint_spec blob (format + content)
  eflint              — specification, scenario, query, generated_at, generator_version
  executable_selection — selected frame IDs, act selections, query selections
}
```

### 7.2 Three-part data model

| File | Contents |
|---|---|
| `metadata.json` | task_id, name, slug, model_version, data_version, owner, timestamps, executable_selection, export provenance |
| `FLINT_spec.json` | id, label, description, hasEditor, frames (14+), sourceDocs (JSON-LD), interpretation, saved_artifact |
| `eflint.eflint` | Plain-text eFLINT specification; scenario and query appended as `//` comments |
| `eflint_meta.json` | scenario, query, generator_version, generated_at — sidecar needed for lossless round-trip |

### 7.3 Output folder naming

```
model_v<N>_<YYYY-MM-DD>/
```

Examples: `model_v1_2026-07-12/`, `model_v2_2026-07-12/`

The `N` is passed via `--model-version` flag (default: 1).

### 7.4 split.py

**File:** `scripts/split.py`

```bash
python3 scripts/split.py <export.json>
python3 scripts/split.py <export.json> --model-version 2
python3 scripts/split.py <export.json> --out ./custom_dir
```

Reads the raw export JSON and writes four files into `model_v<N>_<date>/`.

**Auto-generated metadata fields:**

| Field | Source | Example |
|---|---|---|
| `export.exported_at` | Current UTC time | `2026-07-12T10:30:00+00:00` |
| `slug` | Derived from title | `renovation_rentals_demo` |
| `model_version` | CLI flag `--model-version` | `v1` |
| `data_version` | `eflint.generator_version` → else `modified_at` date → else `"1"` | `2026-03-31` |

**eflint.eflint format:**

The eFLINT specification is written as plain text. Scenario and query are appended as commented blocks so a human can read them without needing a JSON parser:

```
Fact [landlords] Identified by string.
...

// -- SCENARIO --
// +[landlords]("landlords_1") .

// -- QUERY --
// ?Holds([request subsidy ...]) .
```

### 7.5 combine.py

**File:** `scripts/combine.py`

```bash
python3 scripts/combine.py model_v1_2026-07-12/
python3 scripts/combine.py model_v1_2026-07-12/ --out my_export.json
```

Reads all four files in the split directory and reconstructs a JSON file that the Rule Editor can load. The output filename is auto-generated as `<title>_<timestamp>_combined.json` if `--out` is not specified.

### 7.6 Round-trip verification

All fields survive a split → combine cycle without data loss:

| Field | Round-trip result |
|---|---|
| task_id | ✓ |
| metadata.title | ✓ |
| frames (count + content) | ✓ |
| eflint.specification | ✓ |
| eflint.scenario | ✓ |
| eflint.query | ✓ |
| sourceDocs | ✓ |
| executable_selection | ✓ |

---

## 8. How the Parts Work Together

```
┌─────────────────────────────────────────────────────┐
│                  FLINT Rule Editor                   │
│                  (Vue 3 + Quasar)                    │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │         Inspect & Export Tab                 │   │
│  │  [Metadata] [FLINT Frames] [eFLINT Spec]     │   │
│  │                                              │   │
│  │   [Export to folder] → ZIP download          │   │
│  │   [Push to GitHub]   → git-service → GitHub  │   │
│  └──────────────────────────────────────────────┘   │
│                    ↑ reads                           │
│             Vuex Store (in-memory)                   │
│         task / frames / executableEflintBase         │
└─────────────────────────────────────────────────────┘
                        ↑ loaded from
          Export JSON  (rental_subsidy_…_export.json)
                        ↑ split / combined by
┌─────────────────────────────────────────────────────┐
│           Python Scripts (offline / CLI)             │
│                                                      │
│   split.py   →  model_v1_2026-07-12/                │
│                   metadata.json                      │
│                   FLINT_spec.json                    │
│                   eflint.eflint                      │
│                   eflint_meta.json                   │
│                                                      │
│   combine.py ←  model_v1_2026-07-12/                │
│              →  <title>_combined.json                │
└─────────────────────────────────────────────────────┘
```

**Important distinction:** The front-end export and the Python scripts serve different purposes and produce intentionally different outputs:

| | Front-end (browser) | Scripts (Python CLI) |
|---|---|---|
| Input | Vuex store (live loaded data) | Raw export JSON file |
| Output | ZIP or GitHub push | `model_v<N>_<date>/` folder |
| Frame detail | Flat objects only | Full including sourceDocs |
| Intended use | Quick sharing / git commit | Archiving, version control, round-trip |

---

## 9. Libraries and APIs Used

| Library / API | Where | Role |
|---|---|---|
| Vue 3 Options API | `ExportInspectView.vue` | Component system |
| Vuex 4 | `ExportInspectView.vue` | Read task, frames, eFLINT from store |
| Quasar 2 | `ExportInspectView.vue` | UI components, Notify plugin |
| **jszip** (new) | `ExportInspectView.vue` | Build ZIP archive in browser |
| file-saver | `ExportInspectView.vue` | Trigger browser file download |
| GitHub REST API | `ExportInspectView.vue` | Check/create repo, push files |
| Python 3.9+ stdlib | `scripts/split.py`, `scripts/combine.py` | JSON parsing, file I/O, datetime |

---

## 10. How to Use

### Front-end export (browser)

1. Open the FLINT Rule Editor and load an interpretation (Load button, top bar).
2. Click **Inspect & Export** tab.
3. **Export to folder** → downloads a ZIP file.
4. **Push to GitHub** → opens panel, enter the repository name (`owner/name`), then click Push. (Token is configured on the server in `git-service/.env`.)

### Python scripts (command line)

```bash
# Split a full export JSON into three parts
python3 scripts/split.py path/to/export.json

# Split with explicit version number
python3 scripts/split.py path/to/export.json --model-version 2

# Combine back into a loadable export JSON
python3 scripts/combine.py model_v1_2026-07-12/
```

---

## 11. Possible Next Steps

| Task | Description |
|---|---|
| GitHub OAuth | Replace `.env` PAT with GitHub OAuth flow — users authorise individually without admin setup |
| GitLab / Bitbucket support | Extend `git-service/app.py` to support other platforms via an abstraction layer |
| Script → front-end alignment | Align the front-end ZIP structure (`flint/frames.json`) with the script structure (`FLINT_spec.json`) |
| Export version history | Each save to MongoDB becomes a separate git commit, reconstructing evolution as git history |
| Include sourceDocs | Toggle to include raw JSON-LD source documents in the export |
