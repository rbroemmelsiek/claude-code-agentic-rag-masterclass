# Onboard (Gemini CLI / Antigravity CLI)

Human-readable spec for `/onboard`. The executable command is **`onboard.toml`** in this folder (Gemini discovers `.toml` only).

## When to run

First session in this repo, after cloning, or when you need a fresh project summary before `/build`.

## Tooling

| Tool | Command | Notes |
|------|---------|--------|
| **Gemini CLI** (today) | `gemini` | Slash commands from `.gemini/commands/` |
| **Antigravity CLI** (successor) | `agy` | Run `agy plugin import gemini` to migrate MCP, keybindings, extensions |
| **IDE** | Cursor (or any editor) | Terminal runs the CLI; not Cursor Chat |

Google is consolidating Gemini CLI into **Antigravity CLI** (consumer sunset **June 18, 2026** for many accounts). This repo’s commands work in both until you fully migrate.

## Recommended model (`/model`)

Pick in the CLI footer or `/model`:

| Task | Suggested model |
|------|-----------------|
| **Onboard / explore / summarize** | Fast preview (e.g. `gemini-3-flash-preview`) — low latency, enough for reading docs |
| **Implement plans (`/build`)** | Strongest coding model available (e.g. `gemini-3-pro` or latest Pro) |
| **Long refactors** | Pro; use subagents/background tasks in Antigravity when available |

Do not change models mid-plan unless needed; note the active model in your summary.

## Google Developer Knowledge MCP

Official docs MCP for Firebase, Google Cloud, Android, Maps, etc. Use it for **authoritative** answers about Google APIs—not for Supabase/React/FastAPI (use repo docs).

**Enable (once per GCP project):**

```bash
gcloud services enable developerknowledge.googleapis.com --project=PROJECT_ID
gcloud beta services mcp enable developerknowledge.googleapis.com --project=PROJECT_ID
```

**Configure (Gemini CLI — pick one auth method):**

- **OAuth (recommended with Code Assist login):** `authProviderType: google_credentials` + `gcloud auth application-default login` — see [Connect to Developer Knowledge MCP](https://developers.google.com/knowledge/mcp)
- **API key:** restrict to Developer Knowledge API only; header `X-Goog-Api-Key`

```bash
gemini mcp add -t http -H "X-Goog-Api-Key: YOUR_KEY" google-developer-knowledge \
  https://developerknowledge.googleapis.com/mcp --scope user
```

**Verify:** `/mcp list` → `google-developer-knowledge` connected.

**Tools:** `search_documents`, `get_documents`, `answer_query` (preview). Prefer `search_documents` → `get_documents` for implementation details; use `answer_query` for direct Q&A from the corpus.

**Antigravity:** MCP moves to `mcp_config.json`; field `url` → `serverUrl`. OAuth may require Desktop client setup per Google docs.

## Process

1. **Scan structure**
   - Review tracked files (`git ls-files` output injected by the command).
   - Note `frontend/`, `backend/`, `.agent/plans/`, `reference/`.

2. **Read key files**
   - `CLAUDE.md` — stack, rules, planning workflow (authoritative for implementation).
   - `GEMINI.md` — Gemini/Antigravity-specific pointers.
   - `PRD.md` — product spec and eight modules.
   - `PROGRESS.md` — what is done vs not started.

3. **Check state**
   - `git status` and recent commits (injected by the command).
   - Confirm branch and whether there are uncommitted changes.

4. **Verify MCP (optional but recommended)**
   - If Developer Knowledge MCP is connected, you may use it to confirm any **Google Cloud** pieces of the stack (e.g. Cloud Run, IAM) when relevant.
   - Do not block onboarding if MCP is offline; report status in the summary.

## Output

Provide a brief summary:

- What this project does
- Tech stack (frontend, backend, DB, LLM, observability)
- How it is organised (main directories)
- Current branch and recent activity
- **Progress:** module completion from `PROGRESS.md`
- **Next sensible step** (e.g. Module 2) — do not implement unless the user asks
- **Environment:** Gemini vs Antigravity CLI, model name, MCP status (`/mcp list`)

## Related commands

- `/build .agent/plans/<plan>.md` — execute a plan after onboarding
- `/commands reload` — reload `.toml` commands after edits
- `?` or `/help` — CLI shortcuts

## Voice (optional)

Gemini/Antigravity voice uses `/voice` and **Space** (toggle or hold). Requires mic, SoX `rec` on Windows, and for cloud backend a valid API key + **Generative Language API** enabled. Run `.\scripts\Test-VoicePipeline.ps1` from the repo before relying on voice.
