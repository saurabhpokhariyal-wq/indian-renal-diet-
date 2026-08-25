"""Tests for backend security & correctness fixes (iteration 3).

Covers:
1. CORS allowlist (no wildcard)
2. Regex-injection safe /api/foods?q=...
3. Generic 502 messages (source-level check)
4. Meal-log validation (date + meal_type)
5. Register race → DuplicateKeyError → 400
6. Rate limits via slowapi (register/login/ai/scan)
7. Lifespan seeding (35 foods, no on_event deprecation)
8. N+1 fix: meal-logs shape, is_favorite, personal_tier
9. Regression: API response shapes preserved
"""
from __future__ import annotations

import os
import re
import time
import uuid
from datetime import date, timedelta
from pathlib import Path

import pytest
import requests

BASE_URL = (
    os.environ.get("EXPO_PUBLIC_BACKEND_URL")
    or "https://safe-food-guide-1.preview.emergentagent.com"
).rstrip("/")
API = f"{BASE_URL}/api"
# App-level testing (bypasses cloudflare/ingress CORS + rate-limit interference).
# The public ingress rewrites CORS to `*` and load-balances across multiple IPs
# which defeats per-IP slowapi — behaviour we must test against the app directly.
LOCAL_API = "http://localhost:8001/api"
SERVER_PY = Path("/app/backend/server.py")


def _restart_backend(sleep_s: float = 2.5) -> None:
    """Restart backend via supervisor to reset slowapi in-memory counters."""
    os.system("sudo supervisorctl restart backend > /dev/null 2>&1")
    time.sleep(sleep_s)
    # Wait until server responds
    for _ in range(20):
        try:
            r = requests.get(f"{API}/", timeout=3)
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(0.5)


def _register(session: requests.Session, email: str | None = None, password: str = "pass1234") -> dict:
    email = email or f"TEST_{uuid.uuid4().hex[:10]}@renal.app"
    r = session.post(
        f"{API}/auth/register",
        json={"email": email, "password": password, "full_name": "Test"},
        timeout=20,
    )
    assert r.status_code == 200, f"register failed {r.status_code}: {r.text}"
    d = r.json()
    return {
        "email": email,
        "password": password,
        "token": d["access_token"],
        "user": d["user"],
        "headers": {"Authorization": f"Bearer {d['access_token']}", "Content-Type": "application/json"},
    }


@pytest.fixture(scope="module")
def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ==================== 1. CORS ====================
class TestCORS:
    # NOTE: These hit http://localhost:8001 (the app) directly because the
    # Cloudflare/K8s ingress rewrites CORS headers to `*` for its own reasons.
    # We must verify the app-level CORS middleware, which is what actually
    # protects against browser-based CSRF from disallowed origins.
    def test_allowed_origin_echoed(self, session):
        r = session.options(
            f"{LOCAL_API}/foods",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
            timeout=15,
        )
        assert r.status_code in (200, 204), r.text
        acao = r.headers.get("Access-Control-Allow-Origin", "")
        assert acao == "http://localhost:3000", f"ACAO={acao!r}"

    def test_disallowed_origin_not_echoed(self, session):
        r = session.options(
            f"{LOCAL_API}/foods",
            headers={
                "Origin": "http://evil.example.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
            timeout=15,
        )
        acao = r.headers.get("Access-Control-Allow-Origin", "")
        assert acao != "http://evil.example.com", f"evil origin was echoed: {acao!r}"
        assert acao != "*", "wildcard must not be present"

    def test_no_wildcard_in_source(self):
        src = SERVER_PY.read_text()
        # Extract the actual middleware call (skip comments)
        # Look for CORSMiddleware add_middleware block
        m = re.search(
            r"add_middleware\s*\(\s*CORSMiddleware[^)]*\)", src, re.DOTALL
        )
        assert m, "CORSMiddleware add_middleware block not found"
        block = m.group(0)
        assert 'allow_origins=["*"]' not in block
        assert "allow_origins=CORS_ORIGINS" in block or "allow_origins=[" in block


# ==================== 2. REGEX INJECTION ====================
class TestRegexInjection:
    def test_unbalanced_paren(self, session):
        r = session.get(f"{API}/foods", params={"q": "a(b"}, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_bracket_and_star(self, session):
        r = session.get(f"{API}/foods", params={"q": "[*("}, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_palak_still_matches(self, session):
        r = session.get(f"{API}/foods", params={"q": "Palak"}, timeout=15)
        assert r.status_code == 200
        names = [f["name"] for f in r.json()]
        assert any("Palak Paneer" == n for n in names), names


# ==================== 3. ERROR LEAKAGE ====================
class TestErrorLeakage:
    def test_no_exception_string_in_502(self):
        src = SERVER_PY.read_text()
        # Ensure no `raise HTTPException(status_code=502, detail=f"...{e}")` pattern
        bad = re.findall(
            r"raise\s+HTTPException\s*\(\s*status_code\s*=\s*502[^)]*\{\s*e\s*\}",
            src,
            re.DOTALL,
        )
        assert not bad, f"Found leaky 502 patterns: {bad}"

    def test_ai_ask_and_scan_use_generic_message(self):
        src = SERVER_PY.read_text()
        assert 'AI service temporarily unavailable' in src
        assert 'Vision service temporarily unavailable' in src


# ==================== 4. MEAL-LOG VALIDATION ====================
class TestMealLogValidation:
    @pytest.fixture(scope="class")
    def user(self, session):
        return _register(session)

    def test_invalid_calendar_date_422(self, session, user):
        r = session.post(
            f"{API}/meal-logs",
            headers=user["headers"],
            json={"food_id": "food-lauki-sabzi", "date": "2026-13-45", "meal_type": "lunch"},
            timeout=15,
        )
        assert r.status_code == 422, r.text

    def test_not_a_date_422(self, session, user):
        r = session.post(
            f"{API}/meal-logs",
            headers=user["headers"],
            json={"food_id": "food-lauki-sabzi", "date": "not-a-date", "meal_type": "lunch"},
            timeout=15,
        )
        assert r.status_code == 422

    def test_invalid_meal_type_422(self, session, user):
        r = session.post(
            f"{API}/meal-logs",
            headers=user["headers"],
            json={"food_id": "food-lauki-sabzi", "date": "2026-02-15", "meal_type": "dessert"},
            timeout=15,
        )
        assert r.status_code == 422

    def test_valid_meal_log_200_and_shape(self, session, user):
        r = session.post(
            f"{API}/meal-logs",
            headers=user["headers"],
            json={"food_id": "food-lauki-sabzi", "date": "2026-02-15", "meal_type": "lunch"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("id", "food_id", "date", "meal_type", "food", "created_at"):
            assert k in d, f"missing {k}"
        assert d["date"] == "2026-02-15"
        assert d["meal_type"] == "lunch"
        # embedded food (FoodOut)
        for k in ("id", "name", "safety_tier", "personal_tier", "is_favorite"):
            assert k in d["food"], f"missing food.{k}"

    def test_get_meal_logs_bad_date_400(self, session, user):
        r = session.get(f"{API}/meal-logs", params={"date": "bad"}, headers=user["headers"], timeout=15)
        assert r.status_code == 400


# ==================== 5. REGISTER RACE ====================
class TestRegisterRace:
    def test_duplicate_email_400_not_500(self, session):
        # Restart to give ourselves fresh rate-limit quota
        _restart_backend()
        email = f"TEST_dup_{uuid.uuid4().hex[:8]}@renal.app"
        r1 = session.post(
            f"{API}/auth/register",
            json={"email": email, "password": "pass1234", "full_name": "Dup"},
            timeout=20,
        )
        assert r1.status_code == 200, r1.text
        r2 = session.post(
            f"{API}/auth/register",
            json={"email": email, "password": "pass1234", "full_name": "Dup2"},
            timeout=20,
        )
        assert r2.status_code == 400, r2.text
        assert "already registered" in r2.json().get("detail", "").lower()


# ==================== 6. RATE LIMITS ====================
class TestRateLimits:
    # NOTE: These hit http://localhost:8001 directly because the public
    # ingress load-balances across multiple upstream IPs, which effectively
    # defeats per-IP slowapi (each request sees a different get_remote_address).
    # Verifying app-level enforcement matches slowapi contract.
    def test_register_6th_returns_429(self, session):
        _restart_backend()
        codes: list[int] = []
        for _ in range(6):
            email = f"TEST_rl_{uuid.uuid4().hex[:8]}@renal.app"
            r = session.post(
                f"{LOCAL_API}/auth/register",
                json={"email": email, "password": "pass1234", "full_name": "RL"},
                timeout=20,
            )
            codes.append(r.status_code)
        assert codes[:5].count(200) == 5, f"first 5 must be 200 got {codes}"
        assert codes[5] == 429, f"6th must be 429 got {codes}"

    def test_login_6th_returns_429(self, session):
        _restart_backend()
        # Register via localhost so both share same rate-limit key namespace
        email = f"TEST_ll_{uuid.uuid4().hex[:8]}@renal.app"
        rreg = session.post(
            f"{LOCAL_API}/auth/register",
            json={"email": email, "password": "pass1234", "full_name": "LL"},
            timeout=20,
        )
        assert rreg.status_code == 200
        codes: list[int] = []
        for _ in range(6):
            r = session.post(
                f"{LOCAL_API}/auth/login",
                json={"email": email, "password": "pass1234"},
                timeout=20,
            )
            codes.append(r.status_code)
        assert codes[:5].count(200) == 5, f"first 5 logins must be 200 got {codes}"
        assert codes[5] == 429, f"6th login must be 429 got {codes}"

    def test_ai_ask_11th_returns_429(self, session):
        _restart_backend()
        # Register via localhost & use resulting token — same server, same limiter
        email = f"TEST_ai_{uuid.uuid4().hex[:8]}@renal.app"
        rreg = session.post(
            f"{LOCAL_API}/auth/register",
            json={"email": email, "password": "pass1234", "full_name": "AI"},
            timeout=20,
        )
        assert rreg.status_code == 200
        token = rreg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        codes: list[int] = []
        # Use empty question to force fast 400 (avoids 60s LLM latency that
        # would let the 1-minute rate window reset). Rate-limit decorator
        # still increments per request.
        for _ in range(11):
            r = session.post(
                f"{LOCAL_API}/ai/ask",
                headers=headers,
                json={"question": ""},
                timeout=15,
            )
            codes.append(r.status_code)
        assert codes[10] == 429, f"11th must be 429 got {codes}"
        assert 429 not in codes[:10], f"pre-limit had 429: {codes}"

    def test_scan_food_6th_returns_429(self, session):
        _restart_backend()
        email = f"TEST_sc_{uuid.uuid4().hex[:8]}@renal.app"
        rreg = session.post(
            f"{LOCAL_API}/auth/register",
            json={"email": email, "password": "pass1234", "full_name": "SC"},
            timeout=20,
        )
        assert rreg.status_code == 200
        token = rreg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {"image_base64": ""}
        codes: list[int] = []
        for _ in range(6):
            r = session.post(
                f"{LOCAL_API}/scan/food",
                headers=headers,
                json=payload,
                timeout=30,
            )
            codes.append(r.status_code)
        assert codes[5] == 429, f"6th must be 429 got {codes}"
        assert 429 not in codes[:5], f"pre-limit had 429: {codes}"


# ==================== 7. LIFESPAN ====================
class TestLifespan:
    def test_foods_seeded_35(self, session):
        _restart_backend()
        r = session.get(f"{API}/foods", params={"limit": 1000}, timeout=15)
        assert r.status_code == 200
        foods = r.json()
        assert len(foods) == 35, f"expected 35 foods, got {len(foods)}"

    def test_no_on_event_in_source(self):
        src = SERVER_PY.read_text()
        assert "@app.on_event" not in src
        assert "lifespan" in src


# ==================== 8. N+1 FIX ====================
class TestN1Fix:
    def test_meal_logs_shape_after_three_foods(self, session):
        _restart_backend()
        u = _register(session)
        today = date.today().isoformat()
        food_ids = ["food-lauki-sabzi", "food-besan-chilla", "food-palak-paneer"]
        for fid in food_ids:
            r = session.post(
                f"{API}/meal-logs",
                headers=u["headers"],
                json={"food_id": fid, "date": today, "meal_type": "lunch"},
                timeout=15,
            )
            assert r.status_code == 200, r.text
        r = session.get(f"{API}/meal-logs", params={"date": today}, headers=u["headers"], timeout=15)
        assert r.status_code == 200
        logs = r.json()
        assert len(logs) == 3
        for log in logs:
            for k in ("id", "food_id", "date", "meal_type", "food", "created_at"):
                assert k in log
            assert log["food"]["id"] == log["food_id"]

    def test_is_favorite_correct_per_food(self, session):
        u = _register(session)
        fav_id = "food-lauki-sabzi"
        session.post(f"{API}/favorites/{fav_id}", headers=u["headers"], timeout=15)
        r = session.get(f"{API}/foods", params={"limit": 1000}, headers=u["headers"], timeout=15)
        assert r.status_code == 200
        foods = r.json()
        favs = [f for f in foods if f["is_favorite"]]
        assert len(favs) == 1
        assert favs[0]["id"] == fav_id
        for f in foods:
            assert isinstance(f["is_favorite"], bool)

    def test_personal_tier_dialysis_vs_unknown(self, session):
        u1 = _register(session)  # unknown
        u2 = _register(session)
        session.post(f"{API}/auth/stage", headers=u2["headers"], json={"stage": "dialysis"}, timeout=15)
        r1 = session.get(f"{API}/foods/food-atta-roti", headers=u1["headers"], timeout=15)
        r2 = session.get(f"{API}/foods/food-atta-roti", headers=u2["headers"], timeout=15)
        assert r1.status_code == 200 and r2.status_code == 200
        assert r1.json()["food"]["personal_tier"] == "YELLOW"
        assert r2.json()["food"]["personal_tier"] == "RED"


# ==================== 9. REGRESSION SHAPES ====================
class TestShapesRegression:
    def test_register_and_login_shape(self, session):
        _restart_backend()
        u = _register(session)
        d = {"access_token": u["token"], "user": u["user"]}  # from register
        assert "access_token" in d
        for k in ("id", "email", "full_name", "stage"):
            assert k in d["user"], f"user missing {k}"

        r = session.post(
            f"{API}/auth/login",
            json={"email": u["email"], "password": u["password"]},
            timeout=15,
        )
        assert r.status_code == 200
        lg = r.json()
        assert lg["token_type"] == "bearer"
        assert "access_token" in lg
        for k in ("id", "email", "full_name", "stage"):
            assert k in lg["user"]

    def test_food_detail_shape(self, session):
        r = session.get(f"{API}/foods/food-lauki-sabzi", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert set(d.keys()) == {"food", "swap"}
        for k in ("id", "name", "safety_tier", "personal_tier", "is_favorite"):
            assert k in d["food"]

    def test_weekly_report_shape(self, session):
        u = _register(session)
        r = session.get(f"{API}/reports/weekly", headers=u["headers"], timeout=20)
        assert r.status_code == 200
        d = r.json()
        for k in (
            "start_date",
            "end_date",
            "total_meals",
            "green",
            "yellow",
            "red",
            "days",
            "top_safe_foods",
            "top_avoid_foods",
        ):
            assert k in d, f"weekly missing {k}"
        assert len(d["days"]) == 7

    def test_favorite_toggle_shape(self, session):
        u = _register(session)
        r = session.post(f"{API}/favorites/food-lauki-sabzi", headers=u["headers"], timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert set(d.keys()) == {"food_id", "is_favorite"}
        assert d["food_id"] == "food-lauki-sabzi"
        assert d["is_favorite"] is True
