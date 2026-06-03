# Gemini CLI / Antigravity CLI context

This masterclass repo uses **CLAUDE.md** for agent rules (stack, conventions, planning workflow). Follow it for all implementation work.

## CLI

| Tool | Install / run | Slash commands |
|------|----------------|----------------|
| **Gemini CLI** | `npm i -g @google/gemini-cli` → `gemini` | `.gemini/commands/*.toml` |
| **Antigravity CLI** | [Antigravity CLI](https://developers.google.com/) → `agy` | Import via `agy plugin import gemini`; also reads `GEMINI.md` / `AGENTS.md` |

Google is transitioning Gemini CLI → Antigravity CLI (many consumer accounts: **June 18, 2026**). This repo supports both during the transition.

## Getting started

1. Open repo in Cursor (or VS Code).
2. Terminal: `cd` to repo root (`E:\Dev\Claude-masterclass`).
3. Run **`/onboard`** (loads git state + docs; see `.gemini/commands/onboard.md`).
4. When ready to implement: **`/build .agent/plans/<plan>.md`** (only when you intend to build).

Reload commands after edits: `/commands reload`

## Docs

- **Progress:** `PROGRESS.md`
- **Product spec:** `PRD.md`
- **Rules:** `CLAUDE.md`
- **Spin up services (cloud/Linux/WSL):** `CLOUD.md` — `./scripts/start-services.sh`
- **Spin up services (Windows):** `powershell -File scripts/start-all.ps1`
- **Plans:** `.agent/plans/`
- **Onboard spec:** `.gemini/commands/onboard.md`
- **MCP template:** `.gemini/settings.example.json` (copy keys to `~/.gemini/settings.json` or project `.gemini/settings.json`)

## MCP servers

Full install guide (Developer Knowledge, ADK Docs, Chrome DevTools): **`.gemini/MCP-SETUP.md`**

| MCP | Scope on your machine | Status |
|-----|------------------------|--------|
| **google-developer-knowledge** | User (`~/.gemini/settings.json`) | Works in all folders |
| **chrome-devtools** | Project (`.gemini/settings.json`) | Installed in this repo |
| **adk-docs-mcp** | Extension (`.gemini/extensions/adk-docs-ext`) | Needs **uv** (`uvx` on PATH) |

Verify: `gemini mcp list` or `/mcp list` inside the CLI.

## Models

- **Onboard / Q&A:** fast model (e.g. `gemini-3-flash-preview`) via `/model`
- **Build / coding:** strongest available Pro-class model

## Voice (Windows)

Optional: `/voice` then Space (toggle). Preflight: `.\scripts\Test-VoicePipeline.ps1`. Launcher: `.\scripts\Launch-GeminiVoice.bat` or `gemini-voice.ps1`.
