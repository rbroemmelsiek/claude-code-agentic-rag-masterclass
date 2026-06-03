# Cloud & remote agent guide

Use this file when running in **Cursor Cloud Agents**, Linux CI, macOS, or **WSL** — environments where **bash** works reliably. On native **Windows**, use the PowerShell scripts in `scripts/*.ps1` instead (Git Bash often breaks `npm` output).

## Prerequisites

1. **Repo root** as working directory.
2. **Env files** (not committed; copy from examples if needed):
   - `backend/.env` — `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, LangSmith vars as needed
   - `frontend/.env` — `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_URL=http://localhost:8000`
3. **Backend venv** (once per machine):

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. **Frontend deps** (once per machine):

```bash
cd frontend && npm install
```

## Start services (bash)

Make scripts executable once:

```bash
chmod +x scripts/start-services.sh scripts/stop-services.sh
```

| Goal | Command |
|------|---------|
| Start backend + frontend (background) | `./scripts/start-services.sh` |
| Backend only | `./scripts/start-services.sh backend` |
| Frontend only | `./scripts/start-services.sh frontend` |
| Blocking dev server (one terminal) | `./scripts/start-services.sh backend --foreground` |

Background processes write:

- PIDs: `.run/backend.pid`, `.run/frontend.pid`
- Logs: `.logs/backend.log`, `.logs/frontend.log`

## Stop services (bash)

```bash
./scripts/stop-services.sh          # both
./scripts/stop-services.sh backend
./scripts/stop-services.sh frontend
```

## Verify

```bash
curl -s http://localhost:8000/health    # {"status":"ok"} or similar
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:5173/   # 200
```

Optional API smoke test (backend must be running, venv active):

```bash
cd backend && source venv/bin/activate && cd .. && python scripts/api-smoke-test.py
```

## Windows (local desktop)

Do **not** use the bash scripts for day-to-day Windows dev if `npm` fails in Git Bash. Use PowerShell from repo root:

```powershell
powershell -File scripts/start-all.ps1
powershell -File scripts/stop-all.ps1    # after adding stop scripts
```

| Script | URL |
|--------|-----|
| `start-backend.ps1` | http://localhost:8000 |
| `start-frontend.ps1` | http://localhost:5173 |
| `start-all.ps1` | Opens both in new windows |

## Agent workflow

1. Read `PROGRESS.md` and `CLAUDE.md` for module status and rules.
2. Ensure `.env` files exist; do not commit secrets.
3. `./scripts/start-services.sh` and wait for health URLs.
4. Run validation (browser MCP, smoke test, or plan checklist).
5. `./scripts/stop-services.sh` when finished to free ports.

## Test credentials

For browser/E2E validation (see reference validation suite):

- `test@test.com` / `password1`
- `test2@test.com` / `password1` (second user / isolation)

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `venv not found` | Run backend venv setup above |
| `node_modules not found` | `cd frontend && npm install` |
| Port already in use | `./scripts/stop-services.sh` then retry |
| Backend exits immediately | `tail -n 50 .logs/backend.log` — usually missing `.env` or bad API key |
| Frontend 404 on API | Check `VITE_API_URL` points to `http://localhost:8000` |
