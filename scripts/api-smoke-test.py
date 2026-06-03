"""Module 1 API smoke test (run from repo root with backend venv)."""
from __future__ import annotations

import base64
import json
import sys
import uuid
from pathlib import Path

import os

import httpx

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.config import get_settings
from app.db.supabase import get_supabase_client

BASE = os.environ.get("API_BASE", "http://localhost:8000")
TEST_PASSWORD = "password1"
TEST_EMAILS = ["test@test.com", "test2@test.com"]


def mark(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def jwt_role(key: str) -> str | None:
    try:
        payload = key.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload))
        return data.get("role")
    except Exception:
        return None


def get_token(settings, email: str, password: str) -> tuple[str | None, str]:
    url = settings.supabase_url.rstrip("/") + "/auth/v1/token?grant_type=password"
    r = httpx.post(
        url,
        headers={"apikey": settings.supabase_anon_key, "Content-Type": "application/json"},
        json={"email": email, "password": password},
        timeout=15,
    )
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}: {r.text[:120]}"
    return r.json().get("access_token"), ""


def signup_token(settings, email: str, password: str) -> tuple[str | None, str]:
    url = settings.supabase_url.rstrip("/") + "/auth/v1/signup"
    r = httpx.post(
        url,
        headers={"apikey": settings.supabase_anon_key, "Content-Type": "application/json"},
        json={"email": email, "password": password},
        timeout=15,
    )
    if r.status_code not in (200, 201):
        return None, f"HTTP {r.status_code}: {r.text[:120]}"
    data = r.json()
    token = data.get("access_token") or (data.get("session") or {}).get("access_token")
    return token, ""


def main() -> int:
    settings = get_settings()
    results: list[tuple[str, bool, str]] = []

    def record(test_id: str, passed: bool, detail: str = "") -> None:
        results.append((test_id, passed, detail))
        print(f"[{mark(passed)}] {test_id}: {detail[:220]}")

    print("=== Schema ===")
    client = get_supabase_client()
    for table in ("threads", "messages"):
        try:
            rows = client.table(table).select("id").limit(1).execute().data
            record(f"table {table}", True, f"exists ({len(rows)} sample rows)")
        except Exception as exc:
            record(f"table {table}", False, str(exc)[:200])
            print("\n=== Summary: schema missing — apply migration first ===")
            return 1

    print("\n=== Health & Auth (no token) ===")
    r = httpx.get(f"{BASE}/health", timeout=10)
    record("API-01", r.status_code == 200 and r.json().get("status") == "ok", str(r.json()))

    r = httpx.get(f"{BASE}/threads", timeout=10)
    record("API-02", r.status_code == 403, f"HTTP {r.status_code}")

    r = httpx.get(
        f"{BASE}/threads",
        headers={"Authorization": "Bearer invalid-token-abc123"},
        timeout=10,
    )
    record("API-03", r.status_code in (401, 403), f"HTTP {r.status_code}")

    svc_role = jwt_role(settings.supabase_service_role_key)
    record(
        "ENV service_role key",
        svc_role == "service_role",
        f'JWT role is "{svc_role}" (need service_role from Supabase Settings > API)',
    )

    print("\n=== Authenticated API ===")
    token: str | None = None
    email_used = ""

    for email in TEST_EMAILS:
        token, err = get_token(settings, email, TEST_PASSWORD)
        if token:
            email_used = email
            break
        print(f"[SKIP] login {email}: {err}")

    if not token and svc_role == "service_role":
        for email in TEST_EMAILS:
            try:
                client.auth.admin.create_user(
                    {"email": email, "password": TEST_PASSWORD, "email_confirm": True}
                )
            except Exception:
                pass
            token, _ = get_token(settings, email, TEST_PASSWORD)
            if token:
                email_used = email
                break

    if not token:
        fallback = f"smoke.{uuid.uuid4().hex[:10]}@gmail.com"
        token, err = signup_token(settings, fallback, TEST_PASSWORD)
        if token:
            email_used = fallback
        else:
            print(f"[SKIP] signup fallback: {err}")

    if not token:
        record(
            "API-04..18",
            False,
            "No user token — sign up in the app at http://localhost:5173/auth "
            "or fix SUPABASE_SERVICE_ROLE_KEY (currently anon) and create test users",
        )
        return summarize(results)

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    r = httpx.get(f"{BASE}/auth/me", headers=headers, timeout=10)
    data = r.json() if r.status_code == 200 else {}
    record(
        "API-04",
        r.status_code == 200 and bool(data.get("id")),
        f"email={data.get('email')} (expected one of {TEST_EMAILS} or new signup)",
    )

    r = httpx.post(f"{BASE}/threads", headers=headers, json={}, timeout=90)
    thread1 = r.json() if r.status_code == 201 else {}
    record(
        "API-05",
        r.status_code == 201 and thread1.get("title") == "New Chat",
        f"HTTP {r.status_code} {str(r.text)[:150]}",
    )
    tid = thread1.get("id")

    r = httpx.post(
        f"{BASE}/threads",
        headers=headers,
        json={"title": "Test Thread for Deletion"},
        timeout=90,
    )
    thread2 = r.json() if r.status_code == 201 else {}
    record(
        "API-06",
        r.status_code == 201 and thread2.get("title") == "Test Thread for Deletion",
        f"id={thread2.get('id')}",
    )
    tid2 = thread2.get("id")

    if not tid or not tid2:
        return summarize(results)

    r = httpx.get(f"{BASE}/threads", headers=headers, timeout=10)
    ids = {t.get("id") for t in (r.json() if r.status_code == 200 else [])}
    record("API-07", tid in ids and tid2 in ids, f"count={len(ids)}")

    r = httpx.get(f"{BASE}/threads/{tid}", headers=headers, timeout=10)
    one = r.json() if r.status_code == 200 else {}
    record("API-08", one.get("id") == tid, str(one.get("title")))

    r = httpx.patch(
        f"{BASE}/threads/{tid}",
        headers=headers,
        json={"title": "Updated Test Thread"},
        timeout=10,
    )
    upd = r.json() if r.status_code == 200 else {}
    record("API-09", upd.get("title") == "Updated Test Thread", str(upd.get("title")))

    r = httpx.get(f"{BASE}/threads/{tid}", headers=headers, timeout=10)
    record("API-10", r.json().get("title") == "Updated Test Thread", r.json().get("title", ""))

    r = httpx.delete(f"{BASE}/threads/{tid2}", headers=headers, timeout=30)
    record("API-11", r.status_code == 204, f"HTTP {r.status_code}")

    token2, _ = get_token(
        settings,
        "test2@test.com" if email_used != "test2@test.com" else "test@test.com",
        TEST_PASSWORD,
    )
    if token2:
        h2 = {"Authorization": f"Bearer {token2}", "Content-Type": "application/json"}
        t2ids = {
            t.get("id")
            for t in (
                httpx.get(f"{BASE}/threads", headers=h2, timeout=10).json()
                if httpx.get(f"{BASE}/threads", headers=h2, timeout=10).status_code == 200
                else []
            )
        }
        record("API-12", tid not in t2ids, f"user2 cannot see user1 thread")
        record(
            "API-13",
            httpx.get(f"{BASE}/threads/{tid}", headers=h2, timeout=10).status_code == 404,
            "",
        )
        record(
            "API-14",
            httpx.patch(
                f"{BASE}/threads/{tid}",
                headers=h2,
                json={"title": "Hacked"},
                timeout=10,
            ).status_code
            == 404,
            "",
        )
        record(
            "API-15",
            httpx.delete(f"{BASE}/threads/{tid}", headers=h2, timeout=10).status_code == 404,
            "",
        )
    else:
        for test_id in ("API-12", "API-13", "API-14", "API-15"):
            record(test_id, False, "test2@test.com not available")

    r = httpx.get(f"{BASE}/threads/{tid}/messages", headers=headers, timeout=10)
    msgs = r.json() if r.status_code == 200 else None
    record("API-16", msgs == [], f"messages={msgs}")

    print("[....] API-17: SSE streaming (up to 90s)...")
    events: list[str] = []
    status = 0
    with httpx.stream(
        "POST",
        f"{BASE}/threads/{tid}/messages",
        headers=headers,
        json={"content": "Hello, what is 2+2?"},
        timeout=90,
    ) as resp:
        status = resp.status_code
        buf = ""
        for chunk in resp.iter_text():
            buf += chunk
        for line in buf.splitlines():
            if line.startswith("event:"):
                events.append(line.split(":", 1)[1].strip())
    record(
        "API-17",
        status == 200 and "text_delta" in events and "done" in events,
        f"HTTP {status} events={events}",
    )

    r = httpx.get(f"{BASE}/threads/{tid}/messages", headers=headers, timeout=10)
    msgs = r.json() if r.status_code == 200 else []
    user_ok = any(
        m.get("role") == "user" and "2+2" in (m.get("content") or "") for m in msgs
    )
    asst_ok = any(m.get("role") == "assistant" for m in msgs)
    record("API-18", len(msgs) >= 2 and user_ok and asst_ok, f"count={len(msgs)}")

    httpx.delete(f"{BASE}/threads/{tid}", headers=headers, timeout=30)
    return summarize(results)


def summarize(results: list[tuple[str, bool, str]]) -> int:
    passed = sum(1 for _, ok, _ in results if ok)
    failed = [(t, d) for t, ok, d in results if not ok]
    print(f"\n=== Summary: {passed}/{len(results)} passed ===")
    for test_id, detail in failed:
        print(f"  - {test_id}: {detail}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
