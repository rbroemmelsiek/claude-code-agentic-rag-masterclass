# LangSmith debug cheatsheet (Module 1)

Quick reference for tracing OpenAI Responses API + managed RAG (`file_search`) in this project.

**Stack:** `wrap_openai()` in `backend/app/services/langsmith.py` → project `rag-masterclass` (from `LANGSMITH_PROJECT`).

**Console:** https://smith.langchain.com (US) — match `LANGSMITH_ENDPOINT` in `backend/.env`.

---

## Before opening LangSmith

1. Confirm the run you care about (note the time you sent the chat message).
2. Check the **running** backend wired RAG:

   ```text
   GET http://localhost:8000/health
   ```

   Expect:

   ```json
   {
     "status": "ok",
     "rag_enabled": true,
     "vector_store_id": "vs_...",
     "tool_choice": "required"
   }
   ```

   If you only see `{"status":"ok"}`, an **old backend** is still serving port 8000. Run `scripts/stop-all.ps1`, then `scripts/start-all.ps1`.

3. Refresh the LangSmith traces page — the UI does **not** auto-update (see [Why traces appear late](#why-traces-appear-late)).

---

## 30-second trace checklist

Open the latest root run named **`ChatOpenAI`** and check:

| # | Where | Healthy | Red flag |
|---|--------|---------|----------|
| 1 | Status | `success` | `error` → read error message |
| 2 | Inputs → `tools` | `file_search` + `vector_store_ids` | Missing → config/backend issue |
| 3 | Inputs → `tool_choice` | `required` | `auto` / absent → search may be skipped |
| 4 | Inputs → `input` | Your user message | Wrong or empty |
| 5 | Outputs | Grounded doc answer | “Please upload…” or generic fluff |
| 6 | Latency | ~5–15s for RAG is common | Timeouts / very long hangs |
| 7 | Timestamp | Matches your test | Old run → wrong trace |

**Decision tree**

- **#2 fails** → fix `.env`, restart backend, kill stale port 8000 listeners.
- **#2 passes, #5 fails** → try a **new chat thread**; rephrase query; check vector store file status in OpenAI dashboard.
- **#1 fails** → API key, rate limit (`429`), or bad request (`400`).

---

## Trace detail panel — what each section means

### Inputs (most important for RAG)

| Field | What it is |
|-------|------------|
| `input` | User message sent to OpenAI |
| `tools` | Tool config — must include `file_search` and your `vector_store_ids` |
| `tool_choice` | `required` forces retrieval when tools are set |
| `instructions` | System prompt from `openai_service.py` |
| `conversation` | OpenAI `conv_...` thread id (stateful memory) |
| `model` | e.g. `gpt-4o` |
| `stream` | `true` for SSE chat |

### Outputs

- Final assistant text (may be sparse in list view with streaming).
- Expand nested items if present — look for `file_search_call` or tool-related output.

### Metadata

- **Latency** — end-to-end OpenAI call time.
- **Tokens** — may show `0` with Responses API + streaming (`wrap_openai` quirk); don’t use as sole signal.
- **Project** — should be `rag-masterclass`.

---

## Seven cases (~90% of debugging)

### 1. “RAG doesn’t see my documents”

**Symptom:** “Please upload the PDF”, generic answers.

**Look for:** `tools` with `file_search`; `tool_choice: required`; substantive output.

**Common causes:** Stale backend without `OPENAI_VECTOR_STORE_ID`; poisoned conversation thread; vague query.

**Fix:** `/health` → new thread → specific question (*“what does the pdf say about article 5”*).

---

### 2. “Vector store has files; app doesn’t”

**Symptom:** OpenAI Storage shows completed files; chat ignores them.

**Look for:** App trace missing `tools` vs direct OpenAI test trace that has them.

**Common causes:** App not passing `file_search`; wrong `vector_store_id` in `.env`.

**Fix:** Match `OPENAI_VECTOR_STORE_ID` to dashboard; restart backend.

---

### 3. “Changed `.env` but nothing changed”

**Symptom:** Added keys/vector store id; behavior unchanged.

**Look for:** Old traces without `tools`; new traces after restart with `tools`.

**Common causes:** `get_settings()` cached until restart; `uvicorn --reload` does not watch `.env`; zombie process on port 8000.

**Fix:** `stop-all.ps1` → `start-all.ps1` → verify `/health`.

---

### 4. “Works in one thread, fails in another”

**Symptom:** Same question, different outcomes.

**Look for:** Different `conversation` ids; earlier assistant messages denying document access.

**Common causes:** OpenAI conversation history bias.

**Fix:** **New Chat** for RAG tests.

---

### 5. “Responses are slow”

**Symptom:** 10–30s waits.

**Look for:** Latency on trace; rate-limit errors.

**Common causes:** `file_search` + long PDF + streaming; OpenAI rate limits.

**Fix:** Normal for RAG; retry after rate limit; compare doc vs non-doc questions.

---

### 6. “Hard error in chat”

**Symptom:** SSE `error` event or HTTP 500.

**Look for:** Trace status `error` and message body.

**Common causes:** `401` bad API key; `429` rate limit; `400` invalid tools/request.

**Fix:** Error text in trace is usually definitive.

---

### 7. “Uploaded new files — not in answers yet”

**Symptom:** New PDF in vector store; answers still old.

**Look for:** Correct `vector_store_ids` (same store); answers missing new-only facts.

**Common causes:** OpenAI still indexing (`completed` not shown); question answerable without new file.

**Fix:** Wait for file `completed` in OpenAI dashboard; no backend restart needed for new files in the **same** store.

---

## Why traces appear late

- LangSmith SDK **batches** trace uploads in the background (by design).
- Cloud ingestion and the web UI add more delay.
- The traces list does **not** live-update — refresh the page.

**Faster alternatives**

- Poll via LangSmith Python client (agents can run this with `backend/.env`).
- Optional: [LangSmith CLI](https://github.com/gigaverse-app/langsmith-cli) `runs watch --project rag-masterclass --interval 2`.

---

## What LangSmith will not show

| Not in traces | Check instead |
|---------------|---------------|
| Files in vector store | [OpenAI Storage → Vector stores](https://platform.openai.com/storage/vector_stores) |
| Full chunk text (often) | OpenAI dashboard; expand trace output when available |
| Supabase / pgvector RAG | Not used in Module 1 — only OpenAI managed RAG |
| Per-user document isolation | Module 1 store is shared via env var |

---

## Good test messages (Module 1)

Use a **new thread** and one of:

- `what does the pdf say about article 5`
- `what does the pdf say about blockbusting`
- `search your documents and summarize fair housing topics`

Avoid relying on old threads named “trace test” or “vector store test” from setup.

---

## Agent / automation access

No LangSmith MCP is configured in Cursor by default. Agents can still:

1. Query recent runs via `langsmith.Client` + `backend/.env` credentials.
2. Use trace URLs pasted by the user.
3. Optional: install LangSmith CLI or MCP for richer access.

---

## Related docs

- Wiring: `backend/app/services/langsmith.py`, `backend/app/services/openai_service.py`
- Env: `backend/.env.example`
- Known tracing quirks: `reference/CC-Rag-Tutorial-0.2/.agent/plans/2.fix-langsmith-tracing.md`
- Module 1 validation: `.agent/validation/module-1-results.md`
