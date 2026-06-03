# MCP setup (Gemini CLI / Antigravity CLI)

This repo can ship **project-scoped** MCP and extensions under `.gemini/`. Your **user-global** config in `~/.gemini/settings.json` also applies in every folder unless a project overrides it.

## Why MCP is not always “universal”

| Scope | File | Applies to |
|--------|------|------------|
| **User** | `%USERPROFILE%\.gemini\settings.json` | All projects (merged in) |
| **Project** | `.gemini/settings.json` in repo root | This repo only (safe to commit if no secrets) |
| **Extensions** | `~/.gemini/extensions/` or `.gemini/extensions/` | Extra MCP servers bundled in extensions |

`gemini mcp add` defaults to **project** scope. Use `-s user` for all repos.

**Your machine today:** `google-developer-knowledge` is already in **user** settings and shows **Connected** from this repo. You do not need to reinstall it unless you want a **project copy** for teammates (use OAuth or each developer’s own API key—never commit keys).

---

## 1. Google Developer Knowledge MCP

Official Google docs (Cloud, Firebase, Android, Maps, …).

**One-time GCP (per project):**

```powershell
gcloud services enable developerknowledge.googleapis.com --project=YOUR_PROJECT_ID
gcloud beta services mcp enable developerknowledge.googleapis.com --project=YOUR_PROJECT_ID
```

**Install — all projects (recommended if you already use it elsewhere):**

```powershell
gemini mcp add -s user -t http -H "X-Goog-Api-Key: YOUR_KEY" google-developer-knowledge https://developerknowledge.googleapis.com/mcp
```

**Or OAuth (no API key in config):** see [Connect to Developer Knowledge MCP](https://developers.google.com/knowledge/mcp) and copy from `.gemini/settings.example.json`.

**Install — this repo only:**

```powershell
cd E:\Dev\Claude-masterclass
gemini mcp add -t http -H "X-Goog-Api-Key: YOUR_KEY" google-developer-knowledge https://developerknowledge.googleapis.com/mcp
```

**Verify:** `gemini mcp list` or inside CLI: `/mcp list`

**Tools:** `search_documents`, `get_documents`, `answer_query` (preview)

---

## 2. ADK Docs MCP

Agent Development Kit documentation via [adk-docs-ext](https://github.com/derailed-dash/adk-docs-ext) (uses `uvx` + `mcpdoc`).

**Prerequisites:** [Git](https://git-scm.com/), [uv](https://docs.astral.sh/uv/) (`uvx` on PATH)

**Option A — extension (already cloned in this repo):**

```powershell
cd E:\Dev\Claude-masterclass
# If missing:
git clone https://github.com/derailed-dash/adk-docs-ext.git .gemini\extensions\adk-docs-ext
```

Project `.gemini/settings.json` sets `"admin.extensions.enabled": true` so Gemini loads `.gemini/extensions/`.

**Option B — CLI install (needs Git on PATH):**

```powershell
gemini extensions install https://github.com/derailed-dash/adk-docs-ext
```

**Verify:** `/mcp list` → `adk-docs-mcp` (from adk-docs-ext) with tools `fetch_docs`, `list_doc_sources`

---

## 3. Chrome DevTools MCP

Browser inspection / performance from the agent. Docs: [Chrome DevTools for agents](https://developer.chrome.com/docs/devtools/agents/get-started)

**Requirements:** Node **22.12+**, Chrome installed. For Gemini sandbox issues, start Chrome yourself or use `--autoConnect` (see Chrome MCP README).

**Already added for this project** in `.gemini/settings.json`. To reinstall:

```powershell
cd E:\Dev\Claude-masterclass
gemini mcp add chrome-devtools npx -y chrome-devtools-mcp@latest
```

**All projects:**

```powershell
gemini mcp add -s user chrome-devtools npx -y chrome-devtools-mcp@latest
```

**Optional — extension (MCP + skills):**

```powershell
gemini extensions install --auto-update https://github.com/ChromeDevTools/chrome-devtools-mcp
```

**Verify:** `gemini mcp list` → `chrome-devtools` Connected. Test prompt: `Check the performance of https://developers.chrome.com`

**Note:** `gemini -e none` disables **extensions** only; project `mcpServers` (e.g. chrome-devtools) still load.

---

## 4. Playwright MCP (Cursor — browser E2E)

Used by `.agent/validation/full-suite.md` for auth/chat E2E tests (`browser_navigate`, `browser_snapshot`, etc.).

**Cursor (this repo):** `.cursor/mcp.json` is already configured:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    }
  }
}
```

**One-time browsers:**

```powershell
cd E:\Dev\Claude-masterclass\frontend
npx -y playwright install chromium
```

**Activate in Cursor:** Restart Cursor (or toggle the server off/on in **Settings → MCP**). New agent sessions should expose `mcp__playwright__*` tools.

**Verify:** Ask the agent to `browser_navigate` to `http://localhost:5173/auth` and snapshot the sign-in form.

**Note:** Cursor also ships **cursor-ide-browser** (built-in). Playwright MCP matches the validation suite tool names from the reference tutorial.

---

## Quick check (from repo root)

```powershell
cd E:\Dev\Claude-masterclass
gemini mcp list
```

Expect at least:

- `google-developer-knowledge` — Connected (from user settings)
- `chrome-devtools` — Connected (from project settings)
- `adk-docs-mcp` — Connected (after uv + extensions enabled)

---

## Reduce noise (optional)

Your user config may load many **data-agent-kit** MCPs. To limit MCPs in this repo, add to `.gemini/settings.json`:

```json
{
  "mcp": {
    "allowed": [
      "google-developer-knowledge",
      "chrome-devtools",
      "adk-docs-mcp"
    ]
  }
}
```

---

## Antigravity CLI (`agy`)

After migration: `agy plugin import gemini`. MCP moves to `mcp_config.json`; `url` → `serverUrl`. See [Antigravity transition blog](https://developers.googleblog.com/en/an-important-update-transitioning-gemini-cli-to-antigravity-cli/).

---

## Security

- Do **not** commit API keys in `.gemini/settings.json`.
- Restrict Developer Knowledge keys to that API only.
- Prefer OAuth / `google_credentials` for Developer Knowledge when using Code Assist login.
