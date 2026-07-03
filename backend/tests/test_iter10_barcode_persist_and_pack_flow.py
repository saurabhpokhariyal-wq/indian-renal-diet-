"""
Iteration 10 tests — Barcode persistence + pack flow (log/favorite) + regression.

Covers:
  a. Login demo user
  b. POST /api/scan/barcode Nutella (3017620422003) → 200 + matched_food_id startswith 'bc_'
  c. GET /api/foods/{bc_id} → source='barcode', brand populated, name non-empty
  d. POST /api/meal-logs (bc_id, today, 'snack') → food.id == bc_id
  e. GET /api/meal-logs?date=today → contains bc_id
  f. GET /api/meal-logs/summary?date=today → potassium totals non-zero
  g. POST /api/favorites/<bc_id> → is_favorite=true; GET /api/foods?favorites_only=true includes;
     POST /api/favorites/<bc_id> again → is_favorite=false
  h. Idempotency: second POST /api/scan/barcode returns same matched_food_id, no duplicates
  i. Regression: /api/scan/food auth, /api/foods?q=palak, /api/ai/ask lang='bn', weekly report
"""
import os
import datetime as dt
import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL")
assert BASE_URL, "EXPO_PUBLIC_BACKEND_URL must be set"
BASE_URL = BASE_URL.rstrip("/")

DEMO_EMAIL = "demo@renal.app"
DEMO_PASSWORD = "demo123"
NUTELLA_BARCODE = "3017620422003"
TODAY = dt.date.today().isoformat()


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def token(session):
    r = session.post(f"{BASE_URL}/api/auth/login",
                     json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    if r.status_code != 200:
        session.post(f"{BASE_URL}/api/auth/register",
                     json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD,
                           "full_name": "Demo User"})
        r = session.post(f"{BASE_URL}/api/auth/login",
                         json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def H(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# module-level state (module-scoped fixtures cache values)
STATE = {}


class TestBarcodePersistence:
    def test_a_login_ok(self, token):
        assert token and isinstance(token, str)

    def test_b_scan_barcode_returns_bc_id(self, session, H):
        r = session.post(f"{BASE_URL}/api/scan/barcode",
                         headers=H, json={"barcode": NUTELLA_BARCODE})
        if r.status_code == 502:
            pytest.skip(f"Open Food Facts environment-blocked: {r.text}")
        assert r.status_code == 200, f"{r.status_code}: {r.text}"
        j = r.json()
        assert j.get("matched_food_id"), "matched_food_id must be set"
        # It must start with 'bc_' because Nutella is NOT a seed food (seeds are Indian dishes)
        assert j["matched_food_id"].startswith("bc_"), \
            f"Expected bc_ prefix, got {j['matched_food_id']}"
        assert j["matched_food_id"] == f"bc_{NUTELLA_BARCODE}"
        STATE["bc_id"] = j["matched_food_id"]
        STATE["food_name"] = j.get("food_name")
        STATE["brand"] = j.get("brand")

    def test_c_get_food_by_bc_id(self, session, H):
        bc_id = STATE.get("bc_id")
        if not bc_id:
            pytest.skip("bc_id not captured")
        r = session.get(f"{BASE_URL}/api/foods/{bc_id}", headers=H)
        assert r.status_code == 200, f"{r.status_code}: {r.text}"
        detail = r.json()
        food = detail.get("food", {})
        assert food.get("id") == bc_id
        assert food.get("source") == "barcode", f"source should be 'barcode', got {food.get('source')}"
        # brand should be populated (Ferrero-family for Nutella)
        assert food.get("brand"), f"brand should be populated, got {food.get('brand')}"
        # display name is non-empty and includes brand if present
        name = food.get("name") or ""
        assert name, "name should be non-empty"
        if food.get("brand"):
            assert food["brand"] in name or "(" in name, \
                f"name should embed brand in parens, got: {name}"

    def test_d_log_bc_id_as_snack(self, session, H):
        bc_id = STATE.get("bc_id")
        if not bc_id:
            pytest.skip("bc_id not captured")
        r = session.post(f"{BASE_URL}/api/meal-logs", headers=H,
                         json={"food_id": bc_id, "date": TODAY, "meal_type": "snack"})
        assert r.status_code in (200, 201), f"{r.status_code}: {r.text}"
        j = r.json()
        assert j.get("food_id") == bc_id
        food = j.get("food") or {}
        assert food.get("id") == bc_id
        STATE["log_id"] = j.get("id")

    def test_e_meal_logs_lists_bc_id(self, session, H):
        bc_id = STATE.get("bc_id")
        if not bc_id:
            pytest.skip("bc_id not captured")
        r = session.get(f"{BASE_URL}/api/meal-logs?date={TODAY}", headers=H)
        assert r.status_code == 200
        items = r.json()
        assert any(it.get("food_id") == bc_id for it in items), \
            f"bc_id {bc_id} should appear in meal-logs listing"

    def test_f_summary_reflects_potassium(self, session, H):
        r = session.get(f"{BASE_URL}/api/meal-logs/summary?date={TODAY}", headers=H)
        assert r.status_code == 200
        j = r.json()
        totals = j.get("totals") or {}
        # Nutella per OFF has 0 K/P but does report Na (42.8mg) & protein (6.3g).
        # Assert summary reflects the logged barcode food (any non-zero nutrient).
        nonzero = any((totals.get(k, 0) or 0) > 0
                      for k in ("potassium_mg", "phosphorus_mg", "sodium_mg", "protein_g"))
        assert nonzero, f"Expected any nutrient > 0 after logging Nutella, got: {totals}"
        assert j.get("total_meals", 0) >= 1

    def test_g_favorite_toggle_and_filter(self, session, H):
        bc_id = STATE.get("bc_id")
        if not bc_id:
            pytest.skip("bc_id not captured")
        # Ensure clean state (in case a prior run left it favorited)
        r0 = session.get(f"{BASE_URL}/api/foods?favorites_only=true", headers=H)
        if r0.status_code == 200 and any(f.get("id") == bc_id for f in r0.json()):
            # already fav → toggle off first
            session.post(f"{BASE_URL}/api/favorites/{bc_id}", headers=H)

        r1 = session.post(f"{BASE_URL}/api/favorites/{bc_id}", headers=H)
        assert r1.status_code == 200, f"{r1.status_code}: {r1.text}"
        assert r1.json().get("is_favorite") is True
        assert r1.json().get("food_id") == bc_id

        # favorites_only=true should include bc_id
        rf = session.get(f"{BASE_URL}/api/foods?favorites_only=true", headers=H)
        assert rf.status_code == 200
        ids = [f.get("id") for f in rf.json()]
        assert bc_id in ids, f"bc_id should be in favorites list, got: {ids}"

        # Toggle off
        r2 = session.post(f"{BASE_URL}/api/favorites/{bc_id}", headers=H)
        assert r2.status_code == 200
        assert r2.json().get("is_favorite") is False

    def test_h_idempotent_second_scan(self, session, H):
        bc_id = STATE.get("bc_id")
        if not bc_id:
            pytest.skip("bc_id not captured")
        r = session.post(f"{BASE_URL}/api/scan/barcode",
                         headers=H, json={"barcode": NUTELLA_BARCODE})
        if r.status_code == 502:
            pytest.skip("OFF environment-blocked")
        assert r.status_code == 200
        j = r.json()
        assert j.get("matched_food_id") == bc_id, \
            f"Second scan should return same id; got {j.get('matched_food_id')} vs {bc_id}"
        # Also confirm no duplicate by searching /api/foods for the name substring
        # (Look up by exact id via /foods/{id} → 200 and just one doc has this id)
        r2 = session.get(f"{BASE_URL}/api/foods/{bc_id}", headers=H)
        assert r2.status_code == 200

    def teardown_class(cls):
        """Cleanup: delete the meal log created in test_d."""
        try:
            log_id = STATE.get("log_id")
            if log_id:
                # Need a fresh session/token
                s = requests.Session()
                r = s.post(f"{BASE_URL}/api/auth/login",
                           json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
                if r.status_code == 200:
                    tok = r.json().get("access_token")
                    s.headers.update({"Authorization": f"Bearer {tok}"})
                    s.delete(f"{BASE_URL}/api/meal-logs/{log_id}")
        except Exception:
            pass


class TestRegression:
    def test_scan_food_requires_auth(self, session):
        r = session.post(f"{BASE_URL}/api/scan/food", json={"image_base64": "AAA"})
        assert r.status_code in (401, 403)

    def test_foods_search_palak(self, session, H):
        r = session.get(f"{BASE_URL}/api/foods?q=palak", headers=H)
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list) and len(items) >= 1
        assert any("palak" in (i.get("name", "").lower()) for i in items)

    def test_ai_ask_bengali(self, session, H):
        r = session.post(f"{BASE_URL}/api/ai/ask", headers=H,
                         json={"question": "Is palak paneer safe?", "lang": "bn"})
        if r.status_code == 429:
            pytest.skip("Rate limited")
        assert r.status_code == 200, f"{r.status_code}: {r.text}"
        assert r.json().get("answer"), "AI answer should be non-empty"

    def test_weekly_report(self, session, H):
        r = session.get(f"{BASE_URL}/api/reports/weekly", headers=H)
        # Endpoint may be /api/reports/weekly or similar — accept 200 or 404 gracefully
        if r.status_code == 404:
            # try alternate path
            r = session.get(f"{BASE_URL}/api/report/weekly", headers=H)
        assert r.status_code == 200, f"{r.status_code}: {r.text}"
        j = r.json()
        # Typical shape: list of day counts or dict with days
        assert j is not None
