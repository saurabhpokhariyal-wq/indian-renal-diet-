"""Iteration 19 — Nutrient display unit (mg/mEq) backend tests.

Covers:
  * PATCH /api/auth/profile persists nutrient_unit ("mg" | "mEq").
  * GET /api/auth/me returns nutrient_unit.
  * Default value is "mg" (new and legacy users).
  * Doctor-limits PATCH still works when nutrient_unit is not sent.
  * Regressions: /api/foods, /api/foods/{id}, /api/meals-log, /api/ai/ask.
"""
from __future__ import annotations

import os
import pytest
import requests

BASE_URL = (
    os.environ.get("EXPO_PUBLIC_BACKEND_URL")
    or os.environ.get("EXPO_BACKEND_URL")
    or "https://safe-food-guide-1.preview.emergentagent.com"
).rstrip("/")

DEMO_EMAIL = "demo@renal.app"
DEMO_PW = "demo123"


# ---------- helpers ----------
def _login() -> str:
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PW},
        timeout=15,
    )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def token() -> str:
    return _login()


@pytest.fixture(scope="module")
def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ---------- nutrient_unit persistence ----------
class TestNutrientUnitField:
    def test_login_response_contains_nutrient_unit(self):
        r = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEMO_EMAIL, "password": DEMO_PW},
            timeout=15,
        )
        assert r.status_code == 200
        u = r.json()["user"]
        assert "nutrient_unit" in u
        assert u["nutrient_unit"] in {"mg", "mEq"}

    def test_me_returns_nutrient_unit(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        assert "nutrient_unit" in r.json()

    def test_patch_to_meq_and_verify_persisted(self, auth_headers):
        r = requests.patch(
            f"{BASE_URL}/api/auth/profile",
            headers=auth_headers,
            json={"nutrient_unit": "mEq"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        assert r.json()["nutrient_unit"] == "mEq"
        # GET verifies persistence
        me = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers, timeout=15)
        assert me.status_code == 200
        assert me.json()["nutrient_unit"] == "mEq"

    def test_patch_back_to_mg(self, auth_headers):
        r = requests.patch(
            f"{BASE_URL}/api/auth/profile",
            headers=auth_headers,
            json={"nutrient_unit": "mg"},
            timeout=15,
        )
        assert r.status_code == 200
        assert r.json()["nutrient_unit"] == "mg"
        me = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers, timeout=15)
        assert me.json()["nutrient_unit"] == "mg"

    def test_patch_invalid_unit_rejected(self, auth_headers):
        r = requests.patch(
            f"{BASE_URL}/api/auth/profile",
            headers=auth_headers,
            json={"nutrient_unit": "kg"},
            timeout=15,
        )
        assert r.status_code in (400, 422)

    def test_new_user_default_is_mg(self):
        # Register fresh throwaway user (skip if rate-limited)
        import uuid as _uu
        email = f"TEST_iter19_{_uu.uuid4().hex[:8]}@renal.app"
        r = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"email": email, "password": "testpass1", "full_name": "TEST Iter19"},
            timeout=15,
        )
        if r.status_code == 429:
            pytest.skip("rate limited on register — cannot verify default")
        assert r.status_code == 200, r.text
        u = r.json()["user"]
        # AuthResponse.user may not include nutrient_unit at register time; check /me.
        headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
        me = requests.get(f"{BASE_URL}/api/auth/me", headers=headers, timeout=15)
        assert me.status_code == 200
        assert me.json()["nutrient_unit"] == "mg"


# ---------- doctor_limits regression ----------
class TestDoctorLimitsRegression:
    def test_patch_only_doctor_limits(self, auth_headers):
        r = requests.patch(
            f"{BASE_URL}/api/auth/profile",
            headers=auth_headers,
            json={
                "doctor_limits": {
                    "potassium_mg": 2001,
                    "phosphorus_mg": 1001,
                    "sodium_mg": 2002,
                }
            },
            timeout=15,
        )
        assert r.status_code == 200, r.text
        dl = r.json().get("doctor_limits")
        assert dl and dl["potassium_mg"] == 2001
        assert dl["phosphorus_mg"] == 1001
        assert dl["sodium_mg"] == 2002

    def test_clear_doctor_limits(self, auth_headers):
        r = requests.patch(
            f"{BASE_URL}/api/auth/profile",
            headers=auth_headers,
            json={"doctor_limits": None},
            timeout=15,
        )
        assert r.status_code == 200
        assert r.json().get("doctor_limits") in (None, {})


# ---------- Foods / Meal-logs regression ----------
class TestFoodsRegression:
    def test_list_foods(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/foods?limit=5", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) > 0
        f = data[0]
        for k in ("id", "name", "safety_tier", "potassium_mg", "sodium_mg", "phosphorus_mg"):
            assert k in f

    def test_food_detail(self, auth_headers):
        # pick first food
        r = requests.get(f"{BASE_URL}/api/foods?limit=1", headers=auth_headers, timeout=15)
        food_id = r.json()[0]["id"]
        r2 = requests.get(f"{BASE_URL}/api/foods/{food_id}", headers=auth_headers, timeout=15)
        assert r2.status_code == 200
        body = r2.json()
        assert body["food"]["id"] == food_id

    def test_meal_logs_endpoint(self, auth_headers):
        from datetime import date as _d
        today = _d.today().isoformat()
        r = requests.get(
            f"{BASE_URL}/api/meal-logs?date={today}",
            headers=auth_headers,
            timeout=15,
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_meal_logs_summary(self, auth_headers):
        from datetime import date as _d
        r = requests.get(
            f"{BASE_URL}/api/meal-logs/summary?date={_d.today().isoformat()}",
            headers=auth_headers,
            timeout=15,
        )
        assert r.status_code == 200
        body = r.json()
        assert "totals" in body and "limits" in body


# ---------- AI regression ----------
class TestAiRegression:
    def test_ai_ask_with_meq_context(self, auth_headers):
        # Set the user to mEq first so _build_ai_context uses that branch.
        set_unit = requests.patch(
            f"{BASE_URL}/api/auth/profile",
            headers=auth_headers,
            json={"nutrient_unit": "mEq"},
            timeout=15,
        )
        assert set_unit.status_code == 200
        r = requests.post(
            f"{BASE_URL}/api/ai/ask",
            headers=auth_headers,
            json={"question": "Is banana safe?", "lang": "en"},
            timeout=60,
        )
        # Reset back to mg for downstream tests
        requests.patch(
            f"{BASE_URL}/api/auth/profile",
            headers=auth_headers,
            json={"nutrient_unit": "mg"},
            timeout=15,
        )
        if r.status_code == 429:
            pytest.skip("AI rate-limited")
        if r.status_code == 502 or r.status_code == 503:
            pytest.skip(f"AI service unavailable: {r.status_code}")
        assert r.status_code == 200, r.text
        assert isinstance(r.json().get("answer"), str) and r.json()["answer"]
