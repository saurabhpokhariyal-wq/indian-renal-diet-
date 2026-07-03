"""
Iteration 9 tests — Barcode scanning (POST /api/scan/barcode) + multi-language regression.

Covers:
  - Auth login (demo user)
  - Barcode: Nutella (3017620422003) → 200 with expected fields
  - Barcode: 000000000000 → 404
  - Barcode: 12345 (too short) → 422 validation
  - Barcode: no auth → 401/403
  - Regression: /api/scan/food unauthenticated → 401/403 (light)
  - Regression: /api/foods?q=palak
  - Regression: /api/foods/{id}
  - Regression: /api/meal-logs POST + summary GET
  - Regression: /api/ai/ask with lang=ta returns Tamil/answer
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


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def token(session):
    # Try login; if not exists, register.
    r = session.post(f"{BASE_URL}/api/auth/login",
                     json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    if r.status_code != 200:
        session.post(f"{BASE_URL}/api/auth/register",
                     json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD,
                           "full_name": "Demo User"})
        r = session.post(f"{BASE_URL}/api/auth/login",
                         json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "access_token" in data
    return data["access_token"]


@pytest.fixture(scope="module")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ---------------- Auth ----------------
class TestAuth:
    def test_login_returns_token_and_user(self, session):
        r = session.post(f"{BASE_URL}/api/auth/login",
                         json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
        assert r.status_code == 200
        j = r.json()
        assert j.get("access_token")
        assert j.get("user", {}).get("email") == DEMO_EMAIL


# ---------------- Barcode scan ----------------
class TestBarcodeScan:
    def test_barcode_nutella_returns_expected_fields(self, session, auth_headers):
        r = session.post(f"{BASE_URL}/api/scan/barcode",
                         headers=auth_headers,
                         json={"barcode": NUTELLA_BARCODE})
        if r.status_code == 502:
            pytest.skip(f"Open Food Facts environment-blocked: {r.text}")
        assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
        j = r.json()
        # Expected fields
        for f in ["food_name", "safety_tier", "primary_risk_factor",
                  "portion_limit_text", "clinical_tip", "brand",
                  "potassium_mg", "phosphorus_mg", "sodium_mg",
                  "protein_g", "portion_g"]:
            assert f in j, f"Missing field: {f}"
        # Sanity values
        assert j["safety_tier"] in ("GREEN", "YELLOW", "RED")
        assert j["food_name"], "food_name should be non-empty"
        # Nutella is by Ferrero → brand should typically contain 'Ferrero' or 'Nutella'
        assert isinstance(j["brand"], (str, type(None)))
        assert isinstance(j["portion_g"], (int, float))
        assert isinstance(j["potassium_mg"], (int, float))

    def test_barcode_not_found_returns_404(self, session, auth_headers):
        r = session.post(f"{BASE_URL}/api/scan/barcode",
                         headers=auth_headers,
                         json={"barcode": "000000000000"})
        if r.status_code == 502:
            pytest.skip("Open Food Facts environment-blocked")
        assert r.status_code == 404, f"Expected 404 got {r.status_code}: {r.text}"
        assert "Product not found" in r.json().get("detail", "")

    def test_barcode_too_short_returns_422(self, session, auth_headers):
        r = session.post(f"{BASE_URL}/api/scan/barcode",
                         headers=auth_headers,
                         json={"barcode": "12345"})
        assert r.status_code == 422, f"Expected 422 got {r.status_code}: {r.text}"

    def test_barcode_no_auth_returns_401_or_403(self, session):
        r = session.post(f"{BASE_URL}/api/scan/barcode",
                         json={"barcode": NUTELLA_BARCODE})
        assert r.status_code in (401, 403), f"Expected 401/403 got {r.status_code}"


# ---------------- Regression ----------------
class TestRegression:
    def test_foods_search_palak(self, session, auth_headers):
        r = session.get(f"{BASE_URL}/api/foods?q=palak", headers=auth_headers)
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)
        assert len(items) >= 1
        assert any("palak" in (i.get("name", "").lower()) for i in items)

    def test_get_food_by_id(self, session, auth_headers):
        r = session.get(f"{BASE_URL}/api/foods?q=palak", headers=auth_headers)
        assert r.status_code == 200
        items = r.json()
        assert items
        fid = items[0]["id"]
        r2 = session.get(f"{BASE_URL}/api/foods/{fid}", headers=auth_headers)
        assert r2.status_code == 200
        detail = r2.json()
        assert detail.get("food", {}).get("id") == fid

    def test_meal_log_create_and_summary(self, session, auth_headers):
        # Get a food
        r = session.get(f"{BASE_URL}/api/foods?q=palak", headers=auth_headers)
        food_id = r.json()[0]["id"]
        today = dt.date.today().isoformat()
        # Create meal log
        cr = session.post(f"{BASE_URL}/api/meal-logs", headers=auth_headers,
                          json={"food_id": food_id, "date": today, "meal_type": "meal"})
        assert cr.status_code in (200, 201), f"{cr.status_code}: {cr.text}"
        log_id = cr.json().get("id")
        # Summary
        s = session.get(f"{BASE_URL}/api/meal-logs/summary?date={today}",
                        headers=auth_headers)
        assert s.status_code == 200
        j = s.json()
        assert j.get("total_meals", 0) >= 1
        assert "totals" in j and "limits" in j
        # Cleanup
        if log_id:
            session.delete(f"{BASE_URL}/api/meal-logs/{log_id}", headers=auth_headers)

    def test_scan_food_requires_auth(self, session):
        # Light regression — no image, unauthenticated → 401/403 before validation
        r = session.post(f"{BASE_URL}/api/scan/food", json={"image_base64": "AAA"})
        assert r.status_code in (401, 403)

    def test_ai_ask_tamil(self, session, auth_headers):
        r = session.post(f"{BASE_URL}/api/ai/ask",
                         headers=auth_headers,
                         json={"question": "Is palak paneer safe?", "lang": "ta"})
        if r.status_code == 429:
            pytest.skip("Rate limited")
        assert r.status_code == 200, f"{r.status_code}: {r.text}"
        j = r.json()
        assert j.get("answer"), "AI answer should be non-empty"
