# Agentic RAG Masterclass - PRD

## What We're Building

A RAG application with two interfaces[cite: 1]:
1. **Chat** (default view) - Threaded conversations with retrieval-augmented responses[cite: 1]
2. **Ingestion** - Upload files manually, track processing, manage documents[cite: 1]

This is **not** an automated pipeline with connectors[cite: 1]. Files are uploaded manually via drag-and-drop[cite: 1]. Configuration is via environment variables, no admin UI[cite: 1].

## Target Users

Technically-minded people who want to build production RAG systems using AI coding tools (Claude Code, Cursor, etc.)[cite: 1]. They don't need to know Python or React - that's the AI's job[cite: 1].

**They need to understand:**
- RAG concepts deeply (chunking, embeddings, retrieval, reranking)[cite: 1]
- Codebase structure (what sits where, how pieces connect)[cite: 1]
- How to direct AI to build what they need[cite: 1]
- How to direct AI to fix things when they break[cite: 1]

## Scope

### In Scope
- ✅ Document ingestion and processing[cite: 1]
- ✅ Vector search with pgvector[cite: 1]
- ✅ Hybrid search (keyword + vector)[cite: 1]
- ✅ Reranking[cite: 1]
- ✅ Metadata extraction[cite: 1]
- ✅ Record management (deduplication)[cite: 1]
- ✅ Multi-format support (PDF, DOCX, HTML, Markdown)[cite: 1]
- ✅ Text-to-SQL tool[cite: 1]
- ✅ Web search fallback[cite: 1]
- ✅ Sub-agents with isolated context[cite: 1]
- ✅ Chat with threads and memory[cite: 1]
- ✅ Streaming responses[cite: 1]
- ✅ Auth with RLS[cite: 1]

### Out of Scope
- ❌ Knowledge graphs / GraphRAG[cite: 1]
- ❌ Code execution / sandboxing[cite: 1]
- ❌ Image/audio/video processing[cite: 1]
- ❌ Fine-tuning[cite: 1]
- ❌ Multi-tenant admin features[cite: 1]
- ❌ Billing/payments[cite: 1]
- ❌ Data connectors (Google Drive, SFTP, APIs, webhooks)[cite: 1]
- ❌ Scheduled/automated ingestion[cite: 1]
- ❌ Admin UI (config via env vars)[cite: 1]

## Stack

| Layer | Choice |
|-------|--------|
| Frontend | React + TypeScript + Vite + Tailwind + shadcn/ui[cite: 1] |
| Backend | Python + FastAPI[cite: 1] |
| Database | Supabase (Postgres + pgvector + Auth + Storage + Realtime)[cite: 1] |
| LLM (Module 1) | OpenAI Responses API (managed threads + file_search)[cite: 1] |
| LLM (Module 2+) | Any OpenAI-compatible endpoint (OpenRouter, Ollama, LM Studio, etc.)[cite: 1] |
| Observability | LangSmith[cite: 1] |

## Constraints

- No LLM frameworks - raw OpenAI SDK using the standard Chat Completions API (OpenAI-compatible), Pydantic for structured outputs[cite: 1]
- Row-Level Security on all tables - users only see their own data[cite: 1]
- Streaming chat via SSE[cite: 1]
- Ingestion status via Supabase Realtime[cite: 1]

---

## Architectural Decision: Module 1 → Module 2 Transition

At the end of Module 1, you have a working chat app using OpenAI's **Responses API**—a managed solution where OpenAI handles threads, memory, and file search[cite: 1]. In Module 2, you switch to the standard **Chat Completions API** to support any OpenAI-compatible provider (OpenRouter, Ollama, LM Studio, etc.)[cite: 1].

**The decision you need to make:** What do you do with the Responses API code[cite: 1]? Here are two common approaches, but you're not limited to these—come up with your own if it makes sense for your use case[cite: 1].

| Option | Approach | Pros | Cons |
|--------|----------|------|------|
| **A: Replace** | Remove Responses API code entirely, rebuild on Chat Completions[cite: 1] | Clean codebase, single pattern, easier to maintain[cite: 1] | Lose the ability to use OpenAI's managed RAG[cite: 1] |
| **B: Dual Support** | Keep Responses API alongside Chat Completions, configurable per request[cite: 1] | Flexibility to use either approach, compare them side-by-side[cite: 1] | More complex codebase, two patterns to understand[cite: 1] |

There is no right answer—this is a real architectural choice you'll face in building production systems[cite: 1].

**In the video, I chose Option A**—completely removing the Responses API code from the codebase and any related schema from the database[cite: 1]. This keeps things simple and focused on the OpenAI-compatible Chat Completions pattern going forward[cite: 1].

**This is a lesson in steering Claude Code**: you need to clearly communicate your decision and guide the AI to implement it correctly[cite: 1]. Be explicit about what you want removed, refactored, or kept[cite: 1].

---

## Implementation Modules & Technical Specifications

### Module 1: The App Shell + Observability
**Core Focus:** Auth, chat UI, OpenAI Responses API (manages threads + file_search), LangSmith tracing[cite: 1].
**Learning Objective:** What RAG is, why managed RAG exists, its limitations (OpenAI handles memory and retrieval - black box)[cite: 1].

#### Technical Specifications & Features
*   **Authentication & User Management:** Secure sign-up/sign-in via Supabase Auth with Row Level Security (RLS) configured on all primary tables.
*   **Interactive Chat Interface:** Thread list view layout, real-time message streaming using Server-Sent Events (SSE), styled using modern pre-built shadcn UI components.
*   **OpenAI Assistant & RAG:** Seamless OpenAI Responses API integration executing managed threads and out-of-the-box `file_search` capabilities.
*   **Observability & Tracing:** Full integration with LangSmith tracing to actively monitor execution loops, token footprints, and debug RAG API flows.

---

### Module 2: BYO Retrieval + Provider Abstraction
**Core Focus:** Ingestion UI, file storage, chunking $\rightarrow$ embedding $\rightarrow$ pgvector, retrieval tool, Chat Completions API integration (OpenRouter/Ollama/LM Studio), chat history storage (stateless API - you manage memory now), realtime ingestion status[cite: 1].
**Learning Objective:** Chunking, embeddings, vector search, tool calling, relevance thresholds, managing conversation history, **steering AI agents through architectural refactoring**[cite: 1].

#### Technical Specifications & Features
*   **LLM & Embedding Provider Abstraction:** Implementation of a generic ChatCompletions Client (targeting OpenRouter, Ollama, LM Studio, etc.) with a separate Embedding Service Client, allowing configurable Base URLs and API Keys alongside standardized tool calling support.
*   **Vector Database Schema (pgvector):** Database structural migration to establish explicit `documents` and `chunks` tables, enable the PostgreSQL `pgvector` extension, allocate space for 1536-dimension embeddings, and apply tenant isolation using Row Level Security (RLS).
*   **Custom Ingestion Pipeline:** End-to-end background orchestration logic handling Upload $\rightarrow$ Extract (TXT/MD text formats) $\rightarrow$ Chunk $\rightarrow$ Embed $\rightarrow$ Batch insert directly to pgvector. Real-time workflow visibility is maintained using live Supabase Realtime event state broadcasts.
*   **Retrieval Tool & Management UI:** Creation of custom `match_chunks` remote procedure calls (RPC) for mathematical vector search processing. Features an operational tool loop for RAG execution alongside a front-end Documents Page to handle Upload, List, and Delete functionalities with status visualization blocks.

---

### Module 3: Record Manager + Deduplication
**Core Focus:** Content hashing, detect changes, only process what's new/modified[cite: 1].
**Learning Objective:** Why naive ingestion duplicates, incremental updates[cite: 1].

#### Technical Specifications & Features
*   **Content Hash Schema:** Schema extension introducing a cryptographic SHA-256 `content_hash` column inside the database, backed by a performance index (`idx_documents_content_hash`) and a `uq_user_filename` unique layout constraint. The setup is designated nullable to ensure backward compatibility.
*   **Deduplication Logic:** Low-level pipeline parsing function executing `compute_file_hash(bytes) -> hex` to evaluate incoming payloads against an explicit `check_existing_document()` check, computing a functional `determine_action() -> new/skip/update` pipeline direction. Triggers a database-level `delete_existing_chunks()` RPC cleanup vector where applicable.
*   **Upload Flow Actions:** Precise management of file mutation states:
    *   `"created"`: Fires complete file processing, chunking, and embedding allocations.
    *   `"skipped"`: Intercepts matching hashes and yields back the existing record payload instantly.
    *   `"updated"`: Deletes downstream vector fragments and schedules clean chunk re-embedding.
    *   Overwrites existing binary physical storage files and updates document record data rows.
*   **Frontend Feedback:** Dynamic user status indicators displaying clear interface states for `"processing"` (new items), `"unchanged"` (safely skipped items), and `"re-processing"` (modified file structural overrides).

---

### Module 4: Metadata Extraction + Dynamic Schema
**Core Focus:** LLM extracts structured metadata, filter retrieval by metadata[cite: 1].
**Learning Objective:** Structured extraction, schema design, metadata-enhanced retrieval[cite: 1].

#### Technical Specifications & Features
*   **Schema Storage & Definition:** Persistent runtime schema management through a dynamic `metadata_schema` JSONB target column stored within a `global_settings` configuration matrix. Sets up 5 core standard production defaults: title, summary, document_type, topics, and language across core types (string, list, enum, number, boolean) validating directly via an internal `MetadataFieldDefinition` Pydantic layout layer.
*   **LLM Metadata Extraction:** Dynamic generation of extraction prompt arrays constructed directly from your metadata definitions, processing the initial 8000 structural characters of text via a deterministic `json_object` format completion call. Handled by an isolated backend `extract_metadata()` service utility featuring automated fallback schema default properties.
*   **Filtered Retrieval:** RAG engine adjustment enabling an operational `p_metadata_filter` JSONB parameter block inside the `match_chunks` logic loop. Performance is guaranteed by a targeted Generalized Inverted Index (GIN) on the `chunks.metadata` column using `jsonb_path_ops`. Propagates structural data properties seamlessly down from base document layers directly into search target chunk frames.
*   **Detail Panel Display:** User interface additions allowing for clickable structural table rows inside `DocumentList.tsx`. Employs type-aware context rendering modules (badges, icon layouts, tag components) connecting to structured endpoints (`GET /documents/{id}` and `/chunks`).

---

### Module 5: Multi-Format Document Processing with Docling
**Core Focus:** PDF/DOCX/HTML/Markdown via docling, cascade deletes[cite: 1].
**Learning Objective:** Document parsing challenges, format considerations[cite: 1].

#### Technical Specifications & Features
*   **Dependency Integration:** Python integration running `docling>=2.3.0` managed through a thread-safe global Singleton `DocumentConverter` architecture design framework, optimizing background lookups via a Dedicated Thread Pool Executor engine.
*   **Async Extraction Pipeline:** High-performance architectural routing utilizing a text/markdown pass-through (skipping parsing overhead via direct UTF-8 decoding arrays), while piping binary items (PDF, DOCX, PPTX, XLSX) through unified layout pipelines. Ensures proper runtime stability via temporary file memory cleanups before converting to Markdown.
*   **Upload Endpoint Expansion:** Ingestion boundary extension allowing 12 distinct document extensions using deterministic `EXTENSION_TO_CONTENT_TYPE` map objects. Implements a maximum hard file volume threshold cap of 50 MB alongside explicit validation error reporting modules.
*   **Frontend Integration:** Global client-side validation logic adjustments targeting file pickers, rendering native status feedback bars as ingestion transitions across lifecycle states.

---

### Module 6: Hybrid Search & Reranking
**Core Focus:** Keyword + vector search, RRF combination, reranking[cite: 1].
**Learning Objective:** Why vector alone isn't enough, hybrid strategies, reranking[cite: 1].

#### Technical Specifications & Features
*   **Database Migration & FTS:** Database structural enhancement introducing a Full-Text Search (`tsvector`) tracker column with specialized Generalized Inverted Indexing (GIN). Employs direct database triggers on row insertions and updates, running a `keyword_search_chunks` RPC engine mapping native `ts_rank_cd` metrics.
*   **Hybrid Retrieval Pipeline:** Multimodal retrieval execution architecture processing concurrent `keyword_search()` and deep semantic `vector_search()` data frames. Aggregates results natively via Reciprocal Rank Fusion (RRF) calculation algorithms, providing runtime options for standalone hybrid, vector, or keyword behaviors.
*   **Reranking Service:** Extensible processing layer interacting via a Cohere-compliant `/rerank` API layout structure. Supports configurable `base_url` variables pointing to local hosting providers or external production instances, ensuring safe degradation and runtime error interception with score data injection.
*   **Integration & Configuration:** Administration dashboard setup controlling target re-ranking parameter definitions (such as checking `top_n` dimensions, endpoints, keys, and operational parameters).

---

### Module 7: Additional Tools + Multi-Tool Agents
**Core Focus:** Text-to-SQL tool (query structured data), web search fallback (when docs don't have the answer)[cite: 1].
**Learning Objective:** Multi-tool agents, routing between structured/unstructured data, graceful fallbacks, attribution for trust[cite: 1].

#### Technical Specifications & Features
*   **Database-Level SQL Security:** Production database security isolation implementing a distinct restricted Postgres security engine group called `sql_agent_reader`. Grants exclusive `SELECT` access to the target schema tables (`sales_data`), blocking any access attempts to identity authentication configurations or vector index frames.
*   **Text-to-SQL Tool:** Backend tool capability empowering the LLM model to generate and execute raw text queries. Ensures strict query boundaries by enforcing a runtime execution wrapper pattern (`SET ROLE sql_agent_reader`) against pre-populated structural database models.
*   **Web Search Fallback:** Dynamic internet access extension calling the external Tavily search engine interface, performing content summaries and rendering visible reference hyperlinks back to source URLs for end-user audit verification.
*   **Multi-Tool Routing:** Contextual framework handling tool routing, execution loops, dynamic permission validation tables, and target prompt patterns.

---

### Module 8: Sub-Agents + Dark Mode Implementation
**Core Focus:** Detect full-document scenarios, spawn isolated sub-agent with its own tools, nested tool call display in UI, show reasoning from both main agent and sub-agents[cite: 1].
**Learning Objective:** Context management, agent delegation, hierarchical agent display, when to isolate[cite: 1].

#### Technical Specifications & Features
*   **Token & Document Services:** Token utility framework leveraging `tiktoken` processing architectures to compute strict contextual capacity verification filters via `estimate_tokens()` and `can_fit_in_context()` routines. Features single-shot whole-document string generation models (`get_full_document_content()`) adhering to Row Level Security constraints.
*   **Sub-Agent Architecture:** Isolated multi-agent tool execution model launching specialized `analyze_document` workers. Spawns dedicated child agent instances operating inside a completely isolated context workspace, streaming step-by-step thinking outputs to the application core via asynchronous SSE generator pipelines.
*   **Frontend Streaming UI:** User interface component library extensions creating highly descriptive `ToolCallIndicator` components. Supports collapsible multi-agent interface components (`SubAgentPanel`) displaying live backend tool call transformations.
*   **Theme & Integration:** Dynamic styling framework running a modern custom `useTheme` management engine backed by automated client-side data cache storage (`localStorage`), delivering immediate system dark/light layout modifications.

---

## Success Criteria

By the end, students should have:
- ✅ A working RAG application they built with AI assistance[cite: 1]
- ✅ Deep understanding of RAG concepts (chunking, embedding, retrieval, reranking)[cite: 1]
- ✅ Understanding of codebase structure - what lives where, how pieces connect[cite: 1]
- ✅ Ability to direct AI coding tools to build new features[cite: 1]
- ✅ Ability to direct AI coding tools to debug and fix issues[cite: 1]
- ✅ Experience with agentic patterns (multi-tool, sub-agents)[cite: 1]
- ✅ Observability set up from day one[cite: 1]