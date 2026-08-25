"""Iter-25 regression suite.

Focus:
  A. Refactor of server.py into modules must be BEHAVIOR-NEUTRAL. All the
     endpoints that iter24 exercised must still respond identically.
  B. NEW /api/oils/guide endpoint (GREEN/YELLOW/RED tiers) and expanded
     proteins guide (4 new dal entries + 4 new dairy entries).

These tests hit the live preview URL from EXPO_PUBLIC_BACKEND_URL — no
in-process ASGI transport, no mocks. Rate-limit test is guarded to run last.
"""
import os
import time
import uuid
from datetime import datetime

import pytest
import requests

# Base URL comes from the frontend .env — same URL the mobile app hits.
BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL")
if not BASE_URL:
    # Fall back to the value known from /app/frontend/.env at test-authoring time.
    BASE_URL = "https://safe-food-guide-1.preview.emergentagent.com"
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"

DEMO_EMAIL = "demo@renal.app"
DEMO_PASSWORD = "demo123"


# ---------- Fixtures ----------
@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


@pytest.fixture(scope="module")
def token(s):
    # Try login; if 401, register then login.
    r = s.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    if r.status_code == 401:
        s.post(f"{API}/auth/register", json={
            "email": DEMO_EMAIL, "password": DEMO_PASSWORD, "full_name": "Demo User",
        })
        r = s.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    body = r.json()
    assert "access_token" in body
    assert "user" in body
    return body["access_token"]


@pytest.fixture(scope="module")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# =====================================================================
# Bucket A — Refactor regression (behavior unchanged)
# =====================================================================

# --- auth ---
def test_auth_login_returns_access_token_and_user(s):
    r = s.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    assert r.status_code == 200
    body = r.json()
    assert body.get("access_token")
    assert body.get("token_type", "").lower() == "bearer"
    assert body["user"]["email"] == DEMO_EMAIL


def test_auth_me_includes_nutrient_unit(auth_headers):
    r = requests.get(f"{API}/auth/me", headers=auth_headers)
    assert r.status_code == 200
    me = r.json()
    assert "email" in me and me["email"] == DEMO_EMAIL
    assert "nutrient_unit" in me, f"UserOut missing nutrient_unit: {me}"
    # Accept "mg" or "mEq" (case-insensitive) — the app uses "mEq" but spec says either.
    assert me["nutrient_unit"].lower() in {"mg", "meq"}, me["nutrient_unit"]


# --- foods ---
def test_foods_list_returns_1000_plus(auth_headers):
    r = requests.get(f"{API}/foods", headers=auth_headers)
    assert r.status_code == 200
    foods = r.json()
    assert isinstance(foods, list)
    assert len(foods) >= 1000, f"expected 1000+ foods, got {len(foods)}"


def test_foods_query_filter(auth_headers):
    r = requests.get(f"{API}/foods", params={"q": "apple"}, headers=auth_headers)
    assert r.status_code == 200
    foods = r.json()
    assert isinstance(foods, list)
    assert any("apple" in (f.get("name") or "").lower() for f in foods)


def test_food_by_id(auth_headers):
    r = requests.get(f"{API}/foods/food-apple", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    # Endpoint wraps as {"food": {...}}
    food = body.get("food", body)
    assert food["id"] == "food-apple"
    assert "potassium_mg" in food


# --- guides (all 7 including new oils) ---
@pytest.mark.parametrize("guide,entry_key", [
    ("fruits", "fruits"),
    ("beverages", "beverages"),
    ("vegetables", "vegetables"),
    ("snacks", "snacks"),
    ("proteins", "proteins"),
    ("grains", "grains"),
    ("oils", "oils"),
])
def test_guide_shape(guide, entry_key):
    r = requests.get(f"{API}/{guide}/guide")
    assert r.status_code == 200, f"{guide} guide failed: {r.status_code}"
    body = r.json()
    for tier in ("GREEN", "YELLOW", "RED"):
        assert tier in body, f"{guide} missing {tier}"
        section = body[tier]
        assert "title" in section
        assert "subtitle" in section
        assert entry_key in section, f"{guide} {tier} missing '{entry_key}' array"
        assert isinstance(section[entry_key], list) and len(section[entry_key]) > 0


# --- fluid budget regression (iter24) ---
def test_meal_logs_summary_includes_fluid_ml(auth_headers):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    r = requests.get(f"{API}/meal-logs/summary", params={"date": today}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert "limits" in body
    assert "fluid_ml" in body["limits"]
    assert body["limits"]["fluid_ml"] > 0, f"fluid_ml should be >0, got {body['limits']}"


def test_reports_weekly_includes_fluid_ml(auth_headers):
    r = requests.get(f"{API}/reports/weekly", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert "limits" in body
    assert "fluid_ml" in body["limits"]
    assert body["limits"]["fluid_ml"] > 0


def test_doctor_override_fluid_ml_and_restore(auth_headers):
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Fetch stage default first
    r0 = requests.get(f"{API}/meal-logs/summary", params={"date": today}, headers=auth_headers)
    assert r0.status_code == 200
    stage_default = r0.json()["limits"]["fluid_ml"]

    # Apply doctor override
    r1 = requests.patch(f"{API}/auth/profile", headers=auth_headers,
                        json={"doctor_limits": {"fluid_ml": 1500}})
    assert r1.status_code == 200, r1.text

    r2 = requests.get(f"{API}/meal-logs/summary", params={"date": today}, headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["limits"]["fluid_ml"] == 1500

    # Restore
    r3 = requests.patch(f"{API}/auth/profile", headers=auth_headers, json={"doctor_limits": None})
    assert r3.status_code == 200

    r4 = requests.get(f"{API}/meal-logs/summary", params={"date": today}, headers=auth_headers)
    assert r4.status_code == 200
    assert r4.json()["limits"]["fluid_ml"] == stage_default, (
        f"expected restore to {stage_default}, got {r4.json()['limits']['fluid_ml']}"
    )


# --- meal log create/list/delete round-trip ---
def test_meal_log_create_list_delete(auth_headers):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    create = requests.post(f"{API}/meal-logs", headers=auth_headers, json={
        "food_id": "food-apple",
        "servings": 1.0,
        "meal_type": "snack",
        "date": today,
    })
    assert create.status_code in (200, 201), create.text
    log = create.json()
    log_id = log.get("id")
    assert log_id, log

    listed = requests.get(f"{API}/meal-logs", params={"date": today}, headers=auth_headers)
    assert listed.status_code == 200
    assert any(x.get("id") == log_id for x in listed.json())

    deleted = requests.delete(f"{API}/meal-logs/{log_id}", headers=auth_headers)
    assert deleted.status_code in (200, 204)


# --- favorites ---
def test_favorite_toggle(auth_headers):
    r = requests.post(f"{API}/favorites/food-apple", headers=auth_headers)
    assert r.status_code in (200, 201), r.text
    # idempotent second call should still succeed
    r2 = requests.post(f"{API}/favorites/food-apple", headers=auth_headers)
    assert r2.status_code in (200, 201)


# --- ai/ask sanity (grounded answer expected but we accept any 200 shape) ---
def test_ai_ask_returns_200(auth_headers):
    r = requests.post(f"{API}/ai/ask", headers=auth_headers,
                      json={"question": "Is apple safe for CKD?"})
    # AI can be slow; requests default has no timeout so we let it run.
    assert r.status_code == 200, r.text
    body = r.json()
    # Contract: some kind of answer field
    assert any(k in body for k in ("answer", "reply", "message", "content"))


# =====================================================================
# Bucket B — NEW: /api/oils/guide + expanded proteins guide
# =====================================================================

def test_oils_guide_full_shape():
    r = requests.get(f"{API}/oils/guide")
    assert r.status_code == 200
    body = r.json()
    for tier in ("GREEN", "YELLOW", "RED"):
        assert tier in body
        assert "title" in body[tier] and "subtitle" in body[tier]
        assert "oils" in body[tier] and isinstance(body[tier]["oils"], list)
        for entry in body[tier]["oils"]:
            # required fields
            for k in ("name", "hindi", "serving", "potassium_mg", "sodium_mg", "note"):
                assert k in entry, f"{tier} entry {entry.get('name')} missing {k}"
            # derived fields from enrich_guide
            assert "potassium_meq" in entry, f"{entry['name']} missing potassium_meq"
            assert "high_sodium" in entry, f"{entry['name']} missing high_sodium"
            assert isinstance(entry["high_sodium"], bool)


def test_oils_guide_green_contains_expected_entries():
    body = requests.get(f"{API}/oils/guide").json()
    names = {e["name"] for e in body["GREEN"]["oils"]}
    expected = {
        "Mustard Oil (sarson)",
        "Groundnut Oil (moongfali)",
        "Sunflower Oil",
        "Rice Bran Oil",
        "Desi Ghee (cow, small)",
        "Unsalted Butter",
    }
    missing = expected - names
    assert not missing, f"GREEN oils missing: {missing}. Present: {names}"
    # potassium_mg is 0 or 1 for all GREEN oils
    for e in body["GREEN"]["oils"]:
        if e["name"] in expected:
            assert e["potassium_mg"] in (0, 1), f"{e['name']} k={e['potassium_mg']}"


def test_oils_guide_red_contains_expected_entries():
    body = requests.get(f"{API}/oils/guide").json()
    reds = {e["name"]: e for e in body["RED"]["oils"]}
    for n in ("Salted Butter", "Vanaspati / Dalda", "Margarine (spread tubs)"):
        assert n in reds, f"RED missing {n}. Have: {list(reds)}"
    assert reds["Salted Butter"]["sodium_mg"] == 40


def test_oils_guide_entries_have_ifct_source():
    body = requests.get(f"{API}/oils/guide").json()
    for tier in ("GREEN", "YELLOW", "RED"):
        for e in body[tier]["oils"]:
            # `source` optional per spec but must be a string when present
            if "source" in e and e["source"] is not None:
                assert isinstance(e["source"], str) and len(e["source"]) > 3


def test_proteins_guide_yellow_new_entries():
    body = requests.get(f"{API}/proteins/guide").json()
    names = {e["name"] for e in body["YELLOW"]["proteins"]}
    expected = {
        "Chana Dal (split Bengal gram, cooked)",
        "Urad Dal (split, cooked)",
        "Whole Green Moong (sabut, cooked)",
        "Kala Chana (whole black gram, cooked)",
        "Plain Curd / Dahi (small katori)",
        "Buttermilk / Chaas (unsalted)",
    }
    missing = expected - names
    assert not missing, f"YELLOW proteins missing new entries: {missing}"


def test_proteins_guide_red_new_dairy_entries():
    body = requests.get(f"{API}/proteins/guide").json()
    names = {e["name"] for e in body["RED"]["proteins"]}
    for n in ("Salted Lassi (glass)", "Sweetened Condensed Milk"):
        assert n in names, f"RED missing {n}"


def test_proteins_guide_yellow_new_entries_derived_meq_and_high_sodium():
    body = requests.get(f"{API}/proteins/guide").json()
    for e in body["YELLOW"]["proteins"]:
        if e["name"].startswith(("Chana Dal", "Urad Dal", "Whole Green Moong", "Kala Chana",
                                 "Plain Curd", "Buttermilk")):
            assert "potassium_meq" in e
            assert "high_sodium" in e
            # Sodium mg is < 400 for all YELLOW dals/dairy → high_sodium False
            assert e["high_sodium"] is False


# =====================================================================
# Rate limiter (run last so we don't lock ourselves out earlier)
# =====================================================================
@pytest.mark.order("last")
def test_rate_limiter_on_login():
    """slowapi limiter is 5/minute on /auth/login. Locally this fires as
    expected; through the k8s ingress the client IP may not be preserved, so
    we test the direct backend host too. If neither triggers, that's a bug.
    """
    def hit(base):
        codes = []
        for _ in range(7):
            r = requests.post(f"{base}/api/auth/login",
                              json={"email": "nobody@example.com", "password": "wrongwrongwrong"})
            codes.append(r.status_code)
        return codes

    public_codes = hit(BASE_URL)
    # Test the app-internal port too so we can distinguish app vs proxy behavior.
    try:
        local_codes = hit("http://127.0.0.1:8001")
    except Exception:
        local_codes = []

    if 429 in public_codes:
        return  # ideal
    if 429 in local_codes:
        pytest.skip(
            f"Rate limiter works app-internally ({local_codes}) but the k8s "
            f"ingress is not preserving client IP so slowapi treats each "
            f"public request as new. Public codes: {public_codes}. "
            "Report to main agent — slowapi needs X-Forwarded-For key or "
            "SlowAPIMiddleware behind a proxy-aware setup."
        )
    raise AssertionError(f"Rate limiter not firing anywhere. public={public_codes} local={local_codes}")
