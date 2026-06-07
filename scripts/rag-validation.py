"""RAG validation loop — health, ingestion gate, golden SSE queries, optional LangSmith.

Run from repo root with backend venv active:

  python scripts/rag-validation.py --manifest .agent/validation/fixtures/manifests/ca-ethics-form.golden.yaml
  python scripts/rag-validation.py --manifest-dir .agent/validation/fixtures/manifests
  python scripts/rag-validation.py --manifest ... --ingestion both --write-results .agent/validation/rag-latest.json

Ingestion modes (--ingestion overrides manifest ingestion_mode):
  manual  — assume docs pre-indexed (OpenAI vector store / existing DB rows)
  upload  — upload fixture via POST /documents/upload when available (Module 2+)
  both    — upload when API exists, else fall back to manual verification
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

_REPO = Path(__file__).resolve().parents[1]
_BACKEND = _REPO / "backend"
_REGISTRY = _REPO / ".agent" / "validation" / "rag-coverage-registry.yaml"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Run: pip install pyyaml")
    sys.exit(1)

from dotenv import load_dotenv

load_dotenv(_BACKEND / ".env")

from app.config import get_settings

BASE = os.environ.get("API_BASE", "http://localhost:8000")
TEST_PASSWORD = os.environ.get("RAG_TEST_PASSWORD", "password1")
TEST_EMAIL = os.environ.get("RAG_TEST_EMAIL", "test@test.com")


def mark(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def get_token(settings) -> tuple[str | None, str]:
    url = settings.supabase_url.rstrip("/") + "/auth/v1/token?grant_type=password"
    r = httpx.post(
        url,
        headers={"apikey": settings.supabase_anon_key, "Content-Type": "application/json"},
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=15,
    )
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}: {r.text[:120]}"
    return r.json().get("access_token"), ""


def parse_sse_text(buf: str) -> tuple[list[str], str, str | None]:
    events: list[str] = []
    text = ""
    error: str | None = None
    for block in buf.split("\n\n"):
        if not block.strip():
            continue
        event_name = ""
        for line in block.splitlines():
            if line.startswith("event:"):
                event_name = line.split(":", 1)[1].strip()
                events.append(event_name)
            elif line.startswith("data:") and event_name == "text_delta":
                try:
                    data = json.loads(line[5:].strip())
                    text += data.get("content", "")
                except json.JSONDecodeError:
                    pass
            elif line.startswith("data:") and event_name == "error":
                try:
                    data = json.loads(line[5:].strip())
                    error = data.get("error", str(data))
                except json.JSONDecodeError:
                    error = line[5:].strip()
    return events, text, error


def documents_upload_available(headers: dict[str, str]) -> bool:
    """True when Module 2+ documents API is mounted."""
    r = httpx.get(f"{BASE}/documents", headers=headers, timeout=5)
    return r.status_code != 404


def verify_openai_vector_store(manifest: dict[str, Any]) -> tuple[bool, str]:
    settings = get_settings()
    m1 = (manifest.get("source") or {}).get("module1") or {}
    vs_env = m1.get("vector_store_id_env", "OPENAI_VECTOR_STORE_ID")
    vs_id = os.environ.get(vs_env) or getattr(settings, "openai_vector_store_id", "")
    if not vs_id:
        return False, f"{vs_env} not set"

    filename_needle = (m1.get("filename_contains") or "").lower()
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        vs = client.vector_stores.retrieve(vs_id)
        if vs.status != "completed" and vs.file_counts.completed == 0:
            return False, f"vector store {vs_id} not ready (status={vs.status})"

        files = client.vector_stores.files.list(vs_id, limit=20)
        if not files.data:
            return False, "vector store has 0 files"

        meta = [client.files.retrieve(f.id) for f in files.data]
        names = [m.filename for m in meta]
        completed = sum(1 for f in files.data if f.status == "completed")

        if filename_needle:
            matched = [n for n in names if filename_needle in (n or "").lower()]
            if matched:
                return True, f"vs={vs_id} files={len(files.data)} completed={completed} match={matched[0][:50]}"
            require_match = manifest.get("require_filename_match", False)
            if require_match:
                return False, f"no file matching '{filename_needle}' in {[n[:40] for n in names]}"
            return True, (
                f"vs={vs_id} files={len(files.data)} completed={completed} "
                f"(filename hint not found; set require_filename_match: true to enforce)"
            )

        return True, f"vs={vs_id} files={len(files.data)} completed={completed}"
    except Exception as exc:
        return False, str(exc)[:200]


def upload_document(file_path: Path, headers: dict[str, str], timeout: int) -> tuple[bool, str, str | None]:
    if not file_path.is_file():
        return False, f"file not found: {file_path}", None

    with file_path.open("rb") as f:
        files = {"file": (file_path.name, f, "application/octet-stream")}
        r = httpx.post(f"{BASE}/documents/upload", headers=headers, files=files, timeout=timeout)

    if r.status_code not in (200, 201):
        return False, f"upload HTTP {r.status_code}: {r.text[:150]}", None

    doc_id = (r.json() or {}).get("id")
    return True, f"uploaded {file_path.name}", doc_id


def poll_document_completed(
    doc_id: str, headers: dict[str, str], timeout: int, interval: int
) -> tuple[bool, str]:
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = httpx.get(f"{BASE}/documents/{doc_id}", headers=headers, timeout=10)
        if r.status_code != 200:
            return False, f"GET document HTTP {r.status_code}"
        data = r.json()
        status = data.get("status")
        chunks = data.get("chunk_count") or 0
        if status == "completed" and chunks > 0:
            return True, f"status=completed chunk_count={chunks}"
        if status == "failed":
            return False, f"ingestion failed: {data.get('error_message', '')[:120]}"
        time.sleep(interval)
    return False, f"timeout after {timeout}s (last status={status})"


def check_langsmith_tools(settings, project: str) -> tuple[bool, str]:
    if not settings.langsmith_api_key:
        return False, "LANGSMITH_API_KEY not set (skipped)"
    try:
        from langsmith import Client

        client = Client(api_key=settings.langsmith_api_key, api_url=settings.langsmith_endpoint)
        runs = list(client.list_runs(project_name=project, limit=1, is_root=True))
        if not runs:
            return False, "no runs in project"
        run = runs[0]
        tools = (run.inputs or {}).get("tools") or []
        has_fs = any(
            (t.get("type") if isinstance(t, dict) else getattr(t, "type", None)) == "file_search"
            for t in tools
        )
        if not has_fs:
            return False, f"latest run {run.id} missing file_search in tools"
        return True, f"run {str(run.id)[:8]}... has file_search"
    except Exception as exc:
        return False, str(exc)[:200]


def assert_golden(response: str, query: dict[str, Any]) -> tuple[bool, str]:
    text = response.lower()
    if not text.strip():
        return False, "empty response"

    for phrase in query.get("reject_any") or []:
        if phrase.lower() in text:
            return False, f"rejected phrase found: {phrase!r}"

    expect_any = query.get("expect_any") or []
    if not expect_any:
        return True, "no expect_any configured (accept non-empty)"

    matched = [p for p in expect_any if p.lower() in text]
    if not matched:
        return False, f"none of {expect_any!r} found in response"
    return True, f"matched: {matched}"


def resolve_ingestion_mode(manifest: dict[str, Any], override: str | None, headers: dict[str, str]) -> str:
    if override:
        return override
    mode = manifest.get("ingestion_mode")
    if mode:
        return mode
    return "both"


def run_ingestion_gate(
    manifest: dict[str, Any],
    mode: str,
    headers: dict[str, str],
    record,
) -> None:
    ing = manifest.get("ingestion") or {}
    timeout = int(ing.get("timeout_seconds", 300))
    interval = int(ing.get("poll_interval_seconds", 5))

    upload_api = documents_upload_available(headers)
    m2 = (manifest.get("source") or {}).get("module2") or {}
    file_env = m2.get("file_env", "RAG_FIXTURE_CA_ETHICS_PDF")
    file_path = os.environ.get(file_env)
    path = Path(file_path) if file_path else None

    if mode == "manual":
        ok, detail = verify_openai_vector_store(manifest)
        record("RAG-02", ok, f"[manual] {detail}")
        return

    if mode == "upload":
        if not upload_api:
            record("RAG-02", False, "[upload] /documents/upload not available (Module 2+)")
            record("RAG-07", False, "upload API missing")
            return
        if not path:
            record("RAG-02", False, f"[upload] env {file_env} not set")
            return
        ok, detail, doc_id = upload_document(path, headers, timeout=120)
        record("RAG-07", ok, detail)
        if not ok or not doc_id:
            record("RAG-02", False, detail)
            record("RAG-08", False, "no document id")
            return
        ok2, detail2 = poll_document_completed(doc_id, headers, timeout, interval)
        record("RAG-08", ok2, detail2)
        record("RAG-02", ok2, f"[upload] {detail2}")
        return

    # both
    if upload_api and path and path.is_file():
        ok, detail, doc_id = upload_document(path, headers, timeout=120)
        record("RAG-07", ok, detail)
        if ok and doc_id:
            ok2, detail2 = poll_document_completed(doc_id, headers, timeout, interval)
            record("RAG-08", ok2, detail2)
            record("RAG-02", ok2, f"[upload] {detail2}")
            return
        record("RAG-02", False, f"[upload] failed: {detail}")

    ok, detail = verify_openai_vector_store(manifest)
    record("RAG-02", ok, f"[manual fallback] {detail}")


def _results_for_base(results: list[tuple[str, bool, str]], base_id: str) -> list[bool]:
    out: list[bool] = []
    for tid, ok, _ in results:
        if tid == base_id or tid.startswith(f"{base_id}:"):
            out.append(ok)
    return out


def _base_passed(results: list[tuple[str, bool, str]], base_id: str) -> bool | None:
    vals = _results_for_base(results, base_id)
    if not vals:
        return None
    return all(vals)


def compute_coverage(
    results: list[tuple[str, bool, str]],
    manifest: dict[str, Any],
    registry: dict[str, Any],
    module: int,
    langsmith_checked: bool,
) -> dict[str, Any]:
    tests = registry.get("tests") or {}
    module_req = (registry.get("module_requirements") or {}).get(module) or {}
    required_ids = set(module_req.get("required_tests") or [])

    applicable = []
    for tid, meta in tests.items():
        req_mod = meta.get("required_from_module", 99)
        ran = _base_passed(results, tid)
        if req_mod > module and ran is None:
            continue
        if meta.get("optional") and ran is None:
            continue
        applicable.append(tid)

    passed = [tid for tid in applicable if _base_passed(results, tid)]
    failed = [tid for tid in applicable if _base_passed(results, tid) is False]
    not_run = [tid for tid in required_ids if _base_passed(results, tid) is None]

    result_map = {tid: ok for tid, ok, _ in results}

    queries = manifest.get("golden_queries") or []
    min_q = module_req.get("min_golden_queries", 0)
    query_count_ok = len(queries) >= min_q

    langsmith_cases = registry.get("langsmith_cases") or {}
    cases_addressed = 0
    for _cid, case in langsmith_cases.items():
        covered_by = case.get("covered_by") or []
        if any(_base_passed(results, t) for t in covered_by if _base_passed(results, t) is not None):
            cases_addressed += 1

    total_cases = len(langsmith_cases)
    case_pct = round(100 * cases_addressed / total_cases, 1) if total_cases else 0

    test_pct = round(100 * len(passed) / len(applicable), 1) if applicable else 0

    gaps: list[str] = []
    if not query_count_ok:
        gaps.append(f"manifest has {len(queries)} golden_queries; module {module} needs >= {min_q}")
    if not_run:
        gaps.append(f"required tests not executed: {', '.join(not_run)}")
    for tid in failed:
        gaps.append(f"failed: {tid}")
    if module >= 1 and not langsmith_checked:
        gaps.append("LangSmith RAG-05 not checked (pass --langsmith or set LANGSMITH_API_KEY)")
    if module >= 2 and "upload" not in (module_req.get("ingestion_modes") or []):
        gaps.append("Module 2 should use upload or both ingestion mode in manifest")

    guidance = registry.get("coverage_guidance") or {}
    if test_pct >= 85 and query_count_ok and not failed:
        rating = "excellent"
    elif test_pct >= 70:
        rating = "acceptable"
    else:
        rating = "insufficient"

    return {
        "module": module,
        "rating": rating,
        "rating_guidance": guidance.get(rating, ""),
        "tests_applicable": len(applicable),
        "tests_passed": len(passed),
        "tests_failed": len(failed),
        "test_pass_pct": test_pct,
        "langsmith_cases_addressed": cases_addressed,
        "langsmith_cases_total": total_cases,
        "langsmith_case_pct": case_pct,
        "golden_queries": len(queries),
        "min_golden_queries": min_q,
        "golden_queries_met": query_count_ok,
        "gaps": gaps,
        "should_provide": build_should_provide(registry, module, manifest, gaps),
    }


def build_should_provide(
    registry: dict[str, Any], module: int, manifest: dict[str, Any], gaps: list[str]
) -> list[str]:
    items: list[str] = []
    req = (registry.get("module_requirements") or {}).get(module) or {}
    items.append(f">= {req.get('min_golden_queries', 2)} golden_queries with expect_any and reject_any")
    items.append(f"ingestion_mode: one of {req.get('ingestion_modes', ['manual'])}")
    for _cid, case in (registry.get("langsmith_cases") or {}).items():
        if case.get("manifest_should_include"):
            items.append(f"LangSmith case '{case.get('title')}': {case['manifest_should_include']}")
    if gaps:
        items.append("Address current gaps: " + "; ".join(gaps[:3]))
    fixture_id = manifest.get("fixture_id", "unknown")
    items.append(f"Record results in .agent/validation/module-{module}-results.md after run")
    items.append(f"Fixture '{fixture_id}' can add queries via YAML only (no code change)")
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="RAG validation loop")
    parser.add_argument("--manifest", type=Path, help="Single golden manifest YAML")
    parser.add_argument(
        "--manifest-dir",
        type=Path,
        help="Directory of *.golden.yaml manifests",
    )
    parser.add_argument(
        "--ingestion",
        choices=["manual", "upload", "both"],
        help="Override manifest ingestion_mode",
    )
    parser.add_argument("--module", type=int, default=1, help="Module number for coverage requirements")
    parser.add_argument("--langsmith", action="store_true", help="Check latest LangSmith run for file_search")
    parser.add_argument("--sse-timeout", type=int, default=120, help="SSE timeout seconds per query")
    parser.add_argument("--write-results", type=Path, help="Write JSON summary to this path")
    args = parser.parse_args()

    manifests: list[Path] = []
    if args.manifest:
        manifests.append(args.manifest)
    if args.manifest_dir:
        manifests.extend(sorted(args.manifest_dir.glob("*.golden.yaml")))
    if not manifests:
        default = _REPO / ".agent" / "validation" / "fixtures" / "manifests"
        manifests = sorted(default.glob("*.golden.yaml"))
    if not manifests:
        print("ERROR: No manifests found. Use --manifest or --manifest-dir")
        return 1

    settings = get_settings()
    results: list[tuple[str, bool, str]] = []

    def record(test_id: str, passed: bool, detail: str = "") -> None:
        results.append((test_id, passed, detail))
        print(f"[{mark(passed)}] {test_id}: {detail[:220]}")

    print("=== RAG Validation ===")
    print(f"API_BASE={BASE} module={args.module}")

    token, err = get_token(settings)
    if not token:
        record("RAG-AUTH", False, err or "no token — sign up test@test.com / password1")
        return summarize(results, None, args)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    record("RAG-AUTH", True, TEST_EMAIL)

    r = httpx.get(f"{BASE}/health", timeout=10)
    health = r.json() if r.status_code == 200 else {}
    rag_ok = (
        health.get("status") == "ok"
        and health.get("rag_enabled") is True
        and bool(health.get("vector_store_id"))
    )
    record("RAG-01", rag_ok, json.dumps(health)[:200])

    for mp in manifests:
        manifest = load_yaml(mp)
        if manifest.get("active") is False:
            print(f"\n=== Skipping inactive fixture: {mp.name} ===")
            continue
        min_mod = int(manifest.get("min_module", 1))
        if min_mod > args.module:
            print(f"\n=== Skipping {mp.name} (min_module={min_mod}) ===")
            continue
        fixture_id = manifest.get("fixture_id", mp.stem)
        print(f"\n=== Fixture: {fixture_id} ({mp.name}) ===")

        mode = resolve_ingestion_mode(manifest, args.ingestion, headers)
        print(f"Ingestion mode: {mode}")
        run_ingestion_gate(manifest, mode, headers, record)

        for q in manifest.get("golden_queries") or []:
            qid = q.get("id", "query")
            test_sse = f"RAG-03:{fixture_id}:{qid}"
            test_reject = f"RAG-04:{fixture_id}:{qid}"

            tr = httpx.post(f"{BASE}/threads", headers=headers, json={}, timeout=30)
            if tr.status_code != 201:
                record(test_sse, False, f"create thread HTTP {tr.status_code}")
                record(test_reject, False, "skipped")
                continue
            tid = tr.json().get("id")

            buf = ""
            status = 0
            sse_err: str | None = None
            try:
                with httpx.stream(
                    "POST",
                    f"{BASE}/threads/{tid}/messages",
                    headers=headers,
                    json={"content": q.get("question", "")},
                    timeout=args.sse_timeout,
                ) as resp:
                    status = resp.status_code
                    for chunk in resp.iter_text():
                        buf += chunk
            except Exception as exc:
                record("RAG-06", False, str(exc)[:120])
                httpx.delete(f"{BASE}/threads/{tid}", headers=headers, timeout=30)
                continue

            events, text, sse_err = parse_sse_text(buf)
            stream_ok = status == 200 and "text_delta" in events and "done" in events and not sse_err
            record(f"RAG-06:{fixture_id}:{qid}", stream_ok, f"HTTP {status} len={len(text)} err={sse_err}")

            ok, detail = assert_golden(text, q)
            record(test_sse, ok and stream_ok, detail[:200])
            record(test_reject, ok and stream_ok, detail[:200])

            httpx.delete(f"{BASE}/threads/{tid}", headers=headers, timeout=30)

    langsmith_checked = False
    if args.langsmith:
        ls_ok, ls_detail = check_langsmith_tools(settings, settings.langsmith_project)
        record("RAG-05", ls_ok, ls_detail)
        langsmith_checked = True

    registry = load_yaml(_REGISTRY) if _REGISTRY.is_file() else {}
    combined_manifest = load_yaml(manifests[0]) if manifests else {}
    total_queries = sum(len(load_yaml(m).get("golden_queries") or []) for m in manifests)
    combined_manifest["golden_queries"] = [{"id": f"q{i}"} for i in range(total_queries)]
    coverage = compute_coverage(results, combined_manifest, registry, args.module, langsmith_checked)

    return summarize(results, coverage, args)


def summarize(
    results: list[tuple[str, bool, str]],
    coverage: dict[str, Any] | None,
    args: argparse.Namespace,
) -> int:
    passed = sum(1 for _, ok, _ in results if ok)
    failed = [(t, d) for t, ok, d in results if not ok]
    print(f"\n=== Summary: {passed}/{len(results)} passed ===")
    for test_id, detail in failed:
        print(f"  - {test_id}: {detail[:180]}")

    if coverage:
        print("\n=== Coverage ===")
        print(f"Rating: {coverage['rating'].upper()} — {coverage.get('rating_guidance', '')}")
        print(
            f"Tests: {coverage['tests_passed']}/{coverage['tests_applicable']} passed "
            f"({coverage['test_pass_pct']}%)"
        )
        print(
            f"LangSmith cases addressed: {coverage['langsmith_cases_addressed']}/"
            f"{coverage['langsmith_cases_total']} ({coverage['langsmith_case_pct']}%)"
        )
        print(
            f"Golden queries: {coverage['golden_queries']} "
            f"(min {coverage['min_golden_queries']}, met={coverage['golden_queries_met']})"
        )
        if coverage.get("gaps"):
            print("Gaps:")
            for g in coverage["gaps"]:
                print(f"  - {g}")
        print("\nWhat you should provide:")
        for item in coverage.get("should_provide", []):
            print(f"  • {item}")

    if args.write_results and coverage:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "module": args.module,
            "passed": passed,
            "total": len(results),
            "results": [{"id": t, "ok": ok, "detail": d} for t, ok, d in results],
            "coverage": coverage,
        }
        args.write_results.parent.mkdir(parents=True, exist_ok=True)
        args.write_results.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nWrote {args.write_results}")

    if coverage and coverage.get("rating") == "insufficient":
        return 1
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
