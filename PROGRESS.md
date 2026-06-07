# Progress

Track your progress through the masterclass. Agents: read this for **current module** and **validation status**; use links for setup and test detail.

## Convention

- `[ ]` = Not started
- `[-]` = In progress
- `[x]` = Completed

## Modules

### Module 1: App Shell + Observability

- [x] Task 1: Backend Skeleton (FastAPI, config, health endpoint, venv)
- [x] Task 2: Supabase Client module
- [x] Task 3: Database Schema (SQL migration with RLS)
- [x] Task 4: Auth Middleware + /auth/me endpoint
- [x] Task 5: Frontend Setup (Vite + Tailwind + shadcn/ui)
- [x] Task 6: Frontend Supabase Client + utils
- [x] Task 7: Auth UI + Hook (AuthForm, useAuth)
- [x] Task 8: OpenAI Responses API Service (Stateful Conversations)
- [x] Task 9: Thread API (CRUD endpoints with OpenAI sync)
- [x] Task 10: Chat API with SSE Streaming (Stateful)
- [x] Task 11: Thread List UI + api.ts
- [x] Task 12: Chat View UI with streaming
- [x] Task 13: App Assembly + Layout (ChatPage, App, routing)
- [x] Task 14: LangSmith Tracing
- [x] Task 15: PowerShell Helper Scripts

**Status:** Complete

**Validation:** API 21/21, E2E pass (2026-06-03); RAG suite available — [details](.agent/validation/module-1-results.md)

### Module 1.5: Global Admin Settings (Phase A)

- [ ] Not started — plan: [2.global-settings.md](.agent/plans/2.global-settings.md)
- Decisions: `test@test.com` only admin; Phase A before Module 2; signups non-admin

### Module 2: BYO Retrieval + Memory

Plan: [2.module-2-byo-retrieval.md](.agent/plans/2.module-2-byo-retrieval.md)

**Stage A — Parallel**
- [ ] Phase 1a: Config refactor (remove OpenAI fields, add LLM + embedding provider config)
- [ ] Phase 1b: Update LangSmith client factories (accept base_url + api_key)
- [ ] Phase 1c: Replace openai_service.py → llm_service.py (ChatCompletions streaming + tool buffer)
- [ ] Phase 1d: Rewrite threads.py (remove OpenAI calls, stateless thread creation)
- [ ] Phase 1e: Rewrite chat.py (stateless message history + tool-calling loop)
- [ ] Phase 1f: Update .env / .env.example (new vars, remove old)
- [ ] Phase 2a: Migration — pgvector, documents table, chunks table, RLS, match_chunks function
- [ ] Phase 2b: Migration — Supabase Storage bucket + upload/read/delete policies
- [ ] Phase 2c: Migration — REPLICA IDENTITY FULL on documents (Realtime payloads)
- [ ] Phase 2d: Migration — drop openai_thread_id and openai_message_id columns
- [ ] Phase 2e: Remove OpenAI fields from frontend types/index.ts

**Stage B — Sequential (needs Stage A)**
- [ ] Phase 3a: embedding_service.py
- [ ] Phase 3b: chunking_service.py (recursive text splitter, no dependencies)
- [ ] Phase 3c: ingestion_service.py (orchestrate download → extract → chunk → embed → store)
- [ ] Phase 3d: routers/documents.py (upload, list, delete) + schemas + register in main.py
- [ ] Phase 3e: Add python-multipart to requirements.txt

**Stage C — Parallel (needs Stage B)**
- [ ] Phase 4a: retrieval_service.py (match_chunks RPC wrapper)
- [ ] Phase 4b: tool_executor.py (dispatch tool calls by name)
- [ ] Phase 4c: Add RAG_TOOLS to llm_service.py + has_user_documents helper
- [ ] Phase 5a: useRealtimeDocuments.ts hook (Supabase Realtime subscription)
- [ ] Phase 5b: DocumentUpload.tsx (drag-and-drop, .txt/.md only)
- [ ] Phase 5c: DocumentList.tsx (status badges, chunk count, delete)
- [ ] Phase 5d: DocumentsPage.tsx + /documents route + nav link in App.tsx

**Status:** Not started

### Module 3: Record Manager

- [ ] Not started

### Module 4: Metadata Extraction

- [ ] Not started

### Module 5: Multi-Format Support

- [ ] Not started

### Module 6: Hybrid Search & Reranking

- [ ] Not started

### Module 7: Additional Tools

- [ ] Not started

### Module 8: Sub-Agents

- [ ] Not started

## Validation log

| Module | Date | API | RAG | E2E | Notes |
|--------|------|-----|-----|-----|-------|
| 1 | 2026-06-06 | 21/21 | 13/13 EXCELLENT | pass | Full validate-all re-run; api-smoke-test dotenv fix; see rag-latest.json |

## Agent pointers

- **Credentials / env:** `CLOUD.md`
- **Start / stop services:** `CLAUDE.md` → Managing services
- **Plans:** `.agent/plans/` — Module 2: [2.module-2-byo-retrieval.md](.agent/plans/2.module-2-byo-retrieval.md)
- **Module 1 test detail:** `.agent/validation/module-1-results.md`
- **RAG validation:** `scripts/rag-validation.py`, `scripts/validate-all.ps1`, `.agent/validation/rag-validation-playbook.md`
- **Full API/E2E suite (later modules):** `reference/CC-Rag-Tutorial-0.2/.agent/validation/full-suite.md`

## Service URLs

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Health: http://localhost:8000/health
