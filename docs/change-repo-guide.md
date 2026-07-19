# How to Change the Target GitHub Repository

This guide explains how to change which GitHub repository the FLINT Rule Editor pushes exported files to.

---

## For Users (no technical setup needed)

The repository is chosen each time you push — there is nothing to install or configure.

1. Open the FLINT Rule Editor
2. Load an interpretation (click **Load** in the top bar)
3. Go to the **Inspect & Export** tab
4. Click **Push to GitHub**
5. In the **Repository (owner/name)** field, type the target repository
   - Example: `my-org/flint-exports` or `johndoe/my-project`
6. Optionally edit the **Commit message**
7. Click **Push to GitHub**

The repository name is saved in your browser — next time you open the editor it will be pre-filled. You can change it at any time by typing a different name.

### What happens if the repository doesn't exist?

The service will automatically create a **public** repository under the token owner's GitHub account. If you want to push to an existing repository owned by someone else, that repository must grant write access to the token configured on the server.

### Where do my files end up?

Each task is stored in its own subfolder based on the task title:

```
my-org/flint-exports/
├── rental_subsidy/
│   ├── README.md
│   ├── metadata.json
│   ├── flint/frames.json
│   └── eflint/specification.eflint
└── vfl_demo/
    ├── README.md
    ├── metadata.json
    ├── flint/frames.json
    └── eflint/specification.eflint
```

Pushing the same task again **updates** the existing files (does not create duplicates).

---

## For Administrators (server-side setup)

The GitHub Personal Access Token is stored on the server. Users never see or handle it. If you need to change which GitHub account is used for pushing, follow these steps.

### 1. Generate a new token

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Click **Generate new token (classic)** — not fine-grained
3. Check the **`repo`** scope (all sub-options will be selected automatically)
4. Click **Generate token**
5. Copy the token (starts with `ghp_`)

### 2. Update the server configuration

**If running with Docker Compose:**

Edit `.env.stack` in the project root:

```bash
# Open the file
nano .env.stack

# Find or add this line:
GITHUB_TOKEN=ghp_your_new_token_here
```

Then restart the git-service:

```bash
docker compose restart git-service
```

**If running locally (without Docker):**

Edit `git-service/.env`:

```bash
nano git-service/.env

# Update this line:
GITHUB_TOKEN=ghp_your_new_token_here
```

Then restart the service (Ctrl+C in the terminal, then `python3 app.py`).

### 3. Verify the token works

Open in your browser or run:

```bash
curl http://localhost:8103/health
```

You should see:

```json
{"status": "ok", "token_configured": true}
```

### Important notes

- The token determines **who** is pushing. All commits will appear as the token owner's GitHub account.
- The token must be a **Classic** token (starts with `ghp_`). Fine-grained tokens require additional permissions and may not work.
- The token needs the **`repo`** scope to create repositories and push files.
- Never commit `.env` or `.env.stack` to git — they are already in `.gitignore`.
- If users want to push to a repository owned by a different organisation, the token owner must have write access to that organisation/repository.
