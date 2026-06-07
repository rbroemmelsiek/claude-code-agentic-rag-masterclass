# RAG validation playbook

How to automate **ingest → index → query → assert → debug** loops as the pipeline matures. Agents and humans follow the same contract.

**Related:** `langsmith-debug-cheatsheet.md`, `module-1-results.md`, reference `full-suite.md` (Module 2+ template).

---

## Why MD instructions here

| Approach | Role |
|----------|------|
| **`.agent/validation/*.md`** | Human + agent contract: steps, acceptance criteria, golden answers |
| **`scripts/*-test.py`** | Runnable automation (CI, local, agent loops) |
| **`.agent/validation/fixtures/`** | Small committed files + manifest for large/private PDFs |
| **LangSmith** | Debug layer when assertions fail |

Plans (`.agent/plans/`) say *what to build*. Validation docs say *how to prove it still works*.

Add a new **API-XX / RAG-XX** entry to the suite **whenever** ingestion or retrieval behavior changes.

---

## Verification loop (all modules)

```text
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│ 1. Ingest   │───▶│ 2. Index OK  │───▶│ 3. RAG query│───▶│ 4. Assert    │
│ upload/file │    │ completed +  │    │ golden Q    │    │ text/tools/  │
│             │    │ chunk/embed  │    │ new thread  │    │ chunks       │
└─────────────┘    └──────────────┘    └─────────────┘    └──────┬───────┘
                                                                    │ fail
                                                                    ▼
                                                            ┌──────────────┐
                                                            │ 5. Debug     │
                                                            │ /health,     │
                                                            │ LangSmith,   │
                                                            │ cheatsheet   │
                                                            └──────────────┘
```

**Loop rules**

1. **New chat thread** per RAG query test (avoids poisoned OpenAI conversation history).
2. **Poll ingestion** until `completed` (or OpenAI vector file `completed`) — never assert immediately after upload.
3. **Assert on facts**, not prose (regex / keyword groups from golden manifest).
4. On failure, collect: `/health`, latest LangSmith `ChatOpenAI` trace, ingestion status — before changing code.

---

## Module 1 vs Module 2+ (current vs future)

| Stage | Module 1 (now) | Module 2+ (BYO retrieval) |
|-------|----------------|---------------------------|
| **Ingest** | Manual upload to OpenAI vector store (dashboard/API) | `POST /documents/upload` → Supabase storage |
| **Index gate** | OpenAI file status `completed` | DB `documents.status = completed`, `chunk_count > 0` |
| **Retrieval gate** | Trace `tools` → `file_search` + `vector_store_ids` | Tool call / retrieval endpoint + `chunks` rows |
| **Query** | `POST /threads/{id}/messages` (SSE) | Same (+ explicit retrieval in trace) |
| **Debug** | LangSmith + `/health` `rag_enabled` | + Supabase `documents`/`chunks`, Realtime |

Automation scripts should branch on `VALIDATION_MODE=module1|module2` or detect API surface (`/documents/upload` exists or not).

---

## Named fixture pattern (e.g. Form PDF)

Do **not** commit large or licensed PDFs unless you have rights. Use a **golden manifest** instead:

```text
.agent/validation/fixtures/
  README.md
  manifests/
    ca-ethics-form.golden.yaml   # questions + expected fact patterns
  small/                         # committed tiny .txt/.md for CI
    test_rag_document.txt
```

### Manifest schema (`*.golden.yaml`)

```yaml
fixture_id: ca-ethics-form
description: California salesperson ethics reference PDF (private — not in repo)
source:
  module1:
    type: openai_vector_store
    vector_store_id_env: OPENAI_VECTOR_STORE_ID
    filename_contains: "Risk-CA Salesperson Ethics"
  module2:
    type: upload
    file_env: RAG_FIXTURE_CA_ETHICS_PDF   # absolute path on runner machine
ingestion:
  timeout_seconds: 300
  poll_interval_seconds: 5
  success_status: completed
golden_queries:
  - id: article-5
    question: "what does the pdf say about article 5"
    expect_any:
      - "article 5"
      - "professional services"
      - "present or contemplated interest"
    reject_any:
      - "upload the pdf"
      - "upload the document"
  - id: blockbusting
    question: "what does the pdf say about blockbusting"
    expect_any:
      - "blockbust"
      - "minority"
      - "fair housing"
    reject_any:
      - "upload the pdf"
```

**Why manifests:** Same automation runs in CI (small fixtures) and locally (full Form PDF via env path) without committing the PDF.

---

## Automation layers (build in this order)

### Layer 1 — Smoke (exists today)

- `scripts/api-smoke-test.py` — auth, threads, SSE (no RAG assertions yet)
- Extend with optional `--rag` flag reading a golden manifest

### Layer 2 — RAG API loop (**implemented**)

`scripts/rag-validation.py`:

```powershell
# From repo root (backend venv active or use validate-all.ps1)
python scripts/rag-validation.py --manifest-dir .agent/validation/fixtures/manifests --langsmith
python scripts/rag-validation.py --manifest .agent/validation/fixtures/manifests/ca-ethics-form.golden.yaml --ingestion manual
python scripts/rag-validation.py --ingestion both --module 2   # Module 2+ upload with manual fallback
```

1. `GET /health` → RAG-01 `rag_enabled`
2. Ingestion gate RAG-02 — **manual** | **upload** | **both** (manifest `ingestion_mode` or `--ingestion`)
3. Each `golden_queries` entry → new thread → SSE → RAG-03/04/06 assertions
4. Optional `--langsmith` → RAG-05 file_search in latest trace
5. Coverage report vs `rag-coverage-registry.yaml`; writes JSON with `--write-results`

**Full module gate:** `powershell -File scripts/validate-all.ps1 -LangSmith`

### Layer 3 — Ingestion loop (Module 2+)

Add before RAG queries:

1. Upload fixture file (or skip if `documents` already has matching filename)
2. Poll `GET /documents/{id}` or Supabase until `completed`
3. Assert `chunk_count >= N`
4. Then run Layer 2 queries

### Layer 4 — E2E (browser MCP)

Mirror reference `full-suite.md` E2E-16/17: upload in UI, wait for Realtime status, ask golden question.

### Layer 5 — CI

- Commit only **small** fixtures (`test_rag_document.txt`)
- Large Form PDF: optional scheduled/manual workflow with secret path
- Fail build on `rag-validation.py` + `api-smoke-test.py`

---

## Test IDs convention (extend full-suite)

| Prefix | Scope |
|--------|--------|
| `API-XX` | HTTP/curl (existing) |
| `RAG-XX` | Ingestion + retrieval + golden Q&A |
| `E2E-XX` | Browser (existing) |
| `DBG-XX` | LangSmith / health diagnostics (manual or scripted) |

Example entries to add when implementing automation:

- **RAG-01:** `/health` reports `rag_enabled: true`
- **RAG-02:** Golden manifest `article-5` returns expected facts, not upload prompt
- **RAG-03:** LangSmith latest run includes `file_search` in inputs
- **RAG-04 (M2):** Upload manifest file → `completed` within timeout
- **RAG-05 (M2):** `chunk_count > 0` for uploaded doc

---

## Agent-driven validation loop

After any ingestion/RAG change, agents should:

1. Read this playbook + relevant module plan
2. Run `scripts/stop-all.ps1` → `scripts/start-all.ps1`
3. `curl /health` (RAG fields)
4. Run `python scripts/rag-validation.py --manifest fixtures/manifests/ca-ethics-form.golden.yaml` (when script exists)
5. On failure → `langsmith-debug-cheatsheet.md` checklist
6. Append results to `.agent/validation/module-N-results.md`

---

## When to update this playbook

| Change | Update |
|--------|--------|
| New file format (PDF, DOCX, …) | New manifest + RAG-XX criteria |
| New retrieval mode (hybrid, rerank) | New `expect_*` fields or sub-queries |
| New env vars | Document in manifest `source` section |
| Stricter latency SLO | Add `max_latency_seconds` per query |
| User isolation (RLS) | Second user + negative assertions |

---

## Local setup for a private Form PDF

```powershell
# User machine only — do not commit the path or file
$env:RAG_FIXTURE_CA_ETHICS_PDF = "C:\path\to\Risk-CA-Salesperson-Ethics.pdf"
```

Module 1: upload once to OpenAI vector store; manifest `module1` block points at that store.

Module 2: script uploads from `RAG_FIXTURE_CA_ETHICS_PDF` each run (or uses record manager dedup).

---

## Summary

**Yes — MD instructions in `.agent/validation/` are the right foundation.** They stay stable while scripts and pipelines evolve. Pair every manifest with a script assertion and a LangSmith debug path so failures are actionable in one loop.

**End-of-module gate:** run `validate-all.ps1`, record scores in `module-N-results.md`, update `PROGRESS.md` validation log (API + RAG + coverage rating).

See `rag-coverage-registry.yaml` for test IDs, LangSmith case mapping, and minimum manifest requirements.
