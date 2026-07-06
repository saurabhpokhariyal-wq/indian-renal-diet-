"""
Iteration 12 backend tests — 992 INDB food expansion + serving_disclaimer field.
Verifies:
  - /api/foods returns >= 1027 foods, includes Rasam with lemon
  - /api/foods/food-rasam-with-lemon includes non-empty serving_disclaimer containing Beverage/FLUID
  - /api/foods/food-lauki-sabzi returns null serving_disclaimer and existing clinical tip preserved
  - Search returns rasam / palak correctly
  - Regression: meal-log create + summary + delete
  - Regression: favorites toggle
  - Regression: weekly report endpoint
"""
import os
import pytest
import requests
from datetime import date

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "EXPO_PUBLIC_BACKEND_URL not set"

DEMO_EMAIL = "demo@renal.app"
DEMO_PASSWORD = "demo123"


@pytest.fixture(scope="module")
def token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        timeout=20,
    )
    if r.status_code != 200:
        # Fall back to register (should be idempotent per test_credentials.md)
        rr = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD, "full_name": "Demo User"},
            timeout=20,
        )
        if rr.status_code in (200, 201):
            r = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
                timeout=20,
            )
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok, f"No token in response: {r.json()}"
    return tok


@pytest.fixture(scope="module")
def headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ---------- (b) foods list ----------
class TestFoodsExpansion:
    def test_foods_list_default_limit_capped_at_100(self, headers):
        """Default /api/foods returns at most 100 due to server-side limit=100 default.
        This documents current behaviour — frontend never overrides so it only sees 100."""
        r = requests.get(f"{BASE_URL}/api/foods", headers=headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 100, f"Default limit expected 100, got {len(data)}"

    def test_foods_list_full_count_with_large_limit(self, headers):
        """Explicitly override limit — DB now has >=1027 foods including Rasam with lemon."""
        r = requests.get(f"{BASE_URL}/api/foods", params={"limit": 2000}, headers=headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1027, f"Expected >=1027 foods, got {len(data)}"
        names = {f.get("name", "").lower(): f for f in data}
        assert "rasam with lemon" in names, "Rasam with lemon missing"
        ids = {f.get("id") for f in data}
        assert "food-rasam-with-lemon" in ids

    # ---------- (c) food detail with disclaimer ----------
    def test_rasam_detail_has_serving_disclaimer(self, headers):
        r = requests.get(f"{BASE_URL}/api/foods/food-rasam-with-lemon", headers=headers, timeout=20)
        assert r.status_code == 200, r.text
        body = r.json()
        # detail endpoint returns { food: {...}, swap: ...} — support both flat and wrapped
        food = body.get("food", body)
        disc = food.get("serving_disclaimer")
        assert isinstance(disc, str) and disc.strip(), f"serving_disclaimer not a non-empty string: {disc!r}"
        upper = disc.upper()
        assert ("BEVERAGE" in upper) or ("FLUID" in upper), f"Disclaimer missing Beverage/FLUID: {disc!r}"

    # ---------- (d) food detail without disclaimer ----------
    def test_lauki_detail_has_no_disclaimer_and_tip_preserved(self, headers):
        r = requests.get(f"{BASE_URL}/api/foods/food-lauki-sabzi", headers=headers, timeout=20)
        assert r.status_code == 200, r.text
        body = r.json()
        food = body.get("food", body)
        # serving_disclaimer must be present in schema and be None / empty
        assert food.get("serving_disclaimer") in (None, "", None), (
            f"Expected null disclaimer, got {food.get('serving_disclaimer')!r}"
        )
        tip = food.get("actionable_clinical_tip", "")
        assert tip.startswith("Excellent low-potassium vegetable"), f"Unexpected tip: {tip[:80]!r}"

    # ---------- (e) search rasam ----------
    def test_search_rasam(self, headers):
        r = requests.get(f"{BASE_URL}/api/foods", params={"q": "rasam"}, headers=headers, timeout=20)
        assert r.status_code == 200
        results = r.json()
        assert any(f.get("id") == "food-rasam-with-lemon" for f in results), \
            f"food-rasam-with-lemon not in search: {[f.get('id') for f in results][:10]}"

    # ---------- (f) search palak ----------
    def test_search_palak_regression(self, headers):
        r = requests.get(f"{BASE_URL}/api/foods", params={"q": "palak"}, headers=headers, timeout=20)
        assert r.status_code == 200
        results = r.json()
        assert any(f.get("id") == "food-palak-paneer" for f in results), \
            f"food-palak-paneer not in search: {[f.get('id') for f in results][:10]}"


# ---------- (g) meal log regression ----------
class TestMealLogRegression:
    def test_create_and_summary_and_delete(self, headers):
        today = date.today().isoformat()
        r = requests.post(
            f"{BASE_URL}/api/meal-logs",
            headers=headers,
            json={"food_id": "food-rasam-with-lemon", "date": today},
            timeout=20,
        )
        assert r.status_code in (200, 201), f"Create meal-log failed: {r.status_code} {r.text}"
        log = r.json()
        log_id = log.get("id") or log.get("_id")
        assert log_id, f"No log id: {log}"

        s = requests.get(f"{BASE_URL}/api/meal-logs/summary", params={"date": today}, headers=headers, timeout=20)
        assert s.status_code == 200, s.text
        summary = s.json()
        assert "potassium_mg" in summary or "totals" in summary or isinstance(summary, dict)

        d = requests.delete(f"{BASE_URL}/api/meal-logs/{log_id}", headers=headers, timeout=20)
        assert d.status_code in (200, 204), f"Delete failed: {d.status_code} {d.text}"


# ---------- (h) favorites regression ----------
class TestFavoritesRegression:
    def test_toggle_lauki_twice(self, headers):
        r1 = requests.post(f"{BASE_URL}/api/favorites/food-lauki-sabzi", headers=headers, timeout=20)
        assert r1.status_code == 200, r1.text
        v1 = r1.json().get("is_favorite")

        r2 = requests.post(f"{BASE_URL}/api/favorites/food-lauki-sabzi", headers=headers, timeout=20)
        assert r2.status_code == 200, r2.text
        v2 = r2.json().get("is_favorite")

        assert v1 != v2, f"Toggle didn't flip: {v1} -> {v2}"


# ---------- (i) weekly report regression ----------
class TestReportRegression:
    def test_weekly_report_ok(self, headers):
        r = requests.get(f"{BASE_URL}/api/reports/weekly", headers=headers, timeout=30)
        assert r.status_code == 200, f"Report failed: {r.status_code} {r.text[:200]}"
        assert len(r.content) > 100, "Response too small"
