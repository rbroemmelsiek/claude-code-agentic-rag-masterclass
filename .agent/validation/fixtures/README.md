# Validation fixtures

## Layout

```text
fixtures/
  README.md                 # this file
  manifests/*.golden.yaml   # golden questions + expected fact patterns
  small/                    # tiny files safe to commit (Module 2+ CI)
```

## Private / large PDFs (e.g. Form reference)

- **Do not commit** licensed or large PDFs unless you explicitly have rights and want them in git.
- Set a local path: `$env:RAG_FIXTURE_CA_ETHICS_PDF = "C:\path\to\file.pdf"`
- **Module 1:** upload to OpenAI vector store once; tests use `OPENAI_VECTOR_STORE_ID`.
- **Module 2+:** automation uploads from `RAG_FIXTURE_CA_ETHICS_PDF` per run.

## Adding golden queries (no code change)

Edit or copy a `manifests/*.golden.yaml` file:

```yaml
ingestion_mode: manual   # or upload | both
golden_queries:
  - id: my-new-fact
    question: "what does the pdf say about X"
    expect_any: ["keyword1", "keyword2"]
    reject_any: ["upload the pdf"]
```

Run: `python scripts/rag-validation.py --manifest manifests/your-fixture.golden.yaml`

## Ingestion modes

| Mode | When to use |
|------|-------------|
| `manual` | Module 1 — files pre-uploaded to OpenAI vector store |
| `upload` | Module 2+ — script uploads from `file_env` path |
| `both` | Upload if `/documents` API exists, else verify vector store |

Set `active: false` or `min_module: 2` on template manifests to skip them in Module 1 runs.

## Adding a new fixture

1. Copy `manifests/ca-ethics-form.golden.yaml` → `manifests/your-fixture.golden.yaml`
2. Set `ingestion_mode`, `golden_queries` with `expect_any` / `reject_any`
3. For CI-safe tests, add a minimal `small/*.txt` with 2–3 verifiable facts
4. Check coverage output — `rag-coverage-registry.yaml` lists gaps to fill

## Golden query design tips

- Use **fact patterns** the model cannot guess reliably (`expect_any` lists)
- Add **reject_any** for known failure modes ("upload the pdf", hallucinated RAG tutorial text)
- One **new thread** per query in automation
- Keep questions stable across runs for regression comparison
