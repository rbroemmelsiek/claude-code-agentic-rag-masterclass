# Module 1 validation results

Handoff detail for agents. Summary lives in `PROGRESS.md` (validation log).

## Run metadata

| Field | Value |
|-------|--------|
| Date | 2026-06-03 |
| API script | `scripts/api-smoke-test.py` |
| Stack | backend :8000, frontend :5173 |

## API smoke test

**Result:** 21/21 after thread 404 fix (was 18/21 — API-13, API-14, API-15 failed with 500).

| ID | Area | Result |
|----|------|--------|
| Schema | `threads`, `messages` tables | Pass |
| API-01–03 | Health, unauthenticated guards | Pass |
| ENV | `service_role` JWT distinct from `anon` | Pass |
| API-04–11 | Auth, thread CRUD | Pass |
| API-12 | User2 cannot list user1 threads | Pass |
| API-13–15 | User2 GET/PATCH/DELETE user1 thread by ID → 404 | Pass (fixed) |
| API-16–18 | Messages, SSE stream, persistence | Pass |

## Browser live test

- User `test2@test.com` / `password1`: New Chat, streaming reply ("2+2 equals 4.")
- Sign out → `test@test.com` / `password1`: login; sidebar shows only that user's threads

## Environment pitfalls (resolved)

- `SUPABASE_URL` must be `https://<project>.supabase.co` — not `.../rest/v1/`
- `SUPABASE_SERVICE_ROLE_KEY` must be the **service_role** secret, not the anon key
- Restart backend after `.env` changes; use `stop-all.ps1` before `start-all.ps1` to avoid duplicate listeners on 8000

## References

- Test users: `CLOUD.md`
- Start/stop: `CLAUDE.md` → Managing services
- Full suite template (Module 2+): `reference/CC-Rag-Tutorial-0.2/.agent/validation/full-suite.md`
