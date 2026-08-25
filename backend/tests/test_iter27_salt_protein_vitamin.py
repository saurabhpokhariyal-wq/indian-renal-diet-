"""iter-27 backend tests:

1) Salt substitute seed foods appear in /api/foods?q=salt with correct tiers
2) protein_g on NutrientLimits: onboarding suggestion + doctor override + stage defaults
3) meal-logs summary + weekly report include protein_g in limits
4) doctor_limits: null clears overrides
5) AI /ask handles salt-substitute, whey-protein, coconut-water questions (grounded)
6) Regression: FoodDetail, MealLogSummary, WeeklyReport schemas complete
"""
import os
import time

import pytest
import requests

BASE_URL = os.environ.get(
    "EXPO_PUBLIC_BACKEND_URL",
    "https://safe-food-guide-1.preview.emergentagent.com",
).rstrip("/")

EMAIL = "demo@renal.app"
PASSWORD = "demo123"


@pytest.fixture(scope="module")
def token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=15,
    )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# --------------------------------------------------------------------------
# Feature 1: salt substitute foods
# --------------------------------------------------------------------------
class TestSaltSubstitutes:
    def test_search_salt_returns_new_seeds(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/foods?q=salt", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        foods = r.json()
        assert isinstance(foods, list)
        ids = {f["id"] for f in foods}
        expected = {
            "food-lo-salt-substitute",
            "food-nosalt-substitute",
            "food-tata-saltlite",
            "food-himalayan-pink-salt",
            "food-kala-namak",
            "food-lemon-herb-seasoning",
        }
        missing = expected - ids
        assert not missing, f"missing salt-substitute seeds: {missing}"

    def test_kcl_salt_substitutes_are_red_potassium(self, auth_headers):
        # These three are KCl-based → must be RED with POTASSIUM primary risk
        for fid in ["food-lo-salt-substitute", "food-nosalt-substitute", "food-tata-saltlite"]:
            r = requests.get(f"{BASE_URL}/api/foods/{fid}", headers=auth_headers, timeout=15)
            assert r.status_code == 200, f"{fid} lookup failed"
            food = r.json()["food"]
            assert food["safety_tier"] == "RED", f"{fid} base tier expected RED, got {food['safety_tier']}"
            assert food["primary_risk_factor"] == "POTASSIUM", (
                f"{fid} risk factor should be POTASSIUM, got {food['primary_risk_factor']}"
            )
            assert food["potassium_mg"] > 300, f"{fid} K should be very high"

    def test_pink_and_kala_namak_are_sodium_flagged(self, auth_headers):
        for fid in ["food-himalayan-pink-salt", "food-kala-namak"]:
            r = requests.get(f"{BASE_URL}/api/foods/{fid}", headers=auth_headers, timeout=15)
            assert r.status_code == 200
            food = r.json()["food"]
            # tier may be YELLOW or RED after reconciliation; just verify SODIUM risk
            assert food["primary_risk_factor"] == "SODIUM", (
                f"{fid} should be SODIUM-flagged, got {food['primary_risk_factor']}"
            )
            assert food["sodium_mg"] > 200

    def test_lemon_herb_seasoning_is_green(self, auth_headers):
        r = requests.get(
            f"{BASE_URL}/api/foods/food-lemon-herb-seasoning",
            headers=auth_headers,
            timeout=15,
        )
        assert r.status_code == 200
        food = r.json()["food"]
        assert food["safety_tier"] == "GREEN"
        assert food["sodium_mg"] < 20


# --------------------------------------------------------------------------
# Feature 2: protein_g on limits + doctor override
# --------------------------------------------------------------------------
class TestProteinLimits:
    def test_default_summary_has_protein_g(self, auth_headers):
        r = requests.get(
            f"{BASE_URL}/api/meal-logs/summary?date=2026-01-15",
            headers=auth_headers,
            timeout=15,
        )
        assert r.status_code == 200, r.text
        payload = r.json()
        assert "limits" in payload
        limits = payload["limits"]
        assert "protein_g" in limits, f"protein_g missing from limits: {limits}"
        # demo user is stage=dialysis → default protein_g = 75
        assert limits["protein_g"] == 75, (
            f"expected 75g dialysis default, got {limits['protein_g']}"
        )

    def test_weekly_report_has_protein_g_in_limits(self, auth_headers):
        r = requests.get(
            f"{BASE_URL}/api/reports/weekly?end_date=2026-01-15",
            headers=auth_headers,
            timeout=20,
        )
        assert r.status_code == 200, r.text
        payload = r.json()
        assert "limits" in payload
        assert "protein_g" in payload["limits"]
        assert payload["limits"]["protein_g"] == 75
        # regression: avg_daily should still have all nutrient fields
        assert "protein_g" in payload["avg_daily"]

    def test_set_doctor_protein_override_and_persist(self, auth_headers):
        r = requests.patch(
            f"{BASE_URL}/api/auth/profile",
            headers=auth_headers,
            json={"doctor_limits": {"protein_g": 90}},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        user = r.json()
        assert user["doctor_limits"] is not None
        assert user["doctor_limits"].get("protein_g") == 90

        # /auth/me should return it too
        me = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers, timeout=10)
        assert me.status_code == 200
        assert me.json()["doctor_limits"].get("protein_g") == 90

        # summary should now use 90 as override
        s = requests.get(
            f"{BASE_URL}/api/meal-logs/summary?date=2026-01-15",
            headers=auth_headers,
            timeout=15,
        )
        assert s.status_code == 200
        assert s.json()["limits"]["protein_g"] == 90

    def test_clear_doctor_limits_falls_back_to_stage_default(self, auth_headers):
        r = requests.patch(
            f"{BASE_URL}/api/auth/profile",
            headers=auth_headers,
            json={"doctor_limits": None},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        assert r.json()["doctor_limits"] is None

        me = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers, timeout=10)
        assert me.json()["doctor_limits"] is None

        s = requests.get(
            f"{BASE_URL}/api/meal-logs/summary?date=2026-01-15",
            headers=auth_headers,
            timeout=15,
        )
        assert s.status_code == 200
        # back to stage default (dialysis → 75)
        assert s.json()["limits"]["protein_g"] == 75


# --------------------------------------------------------------------------
# Feature 3: AI ask — vitamin/myth grounded answers (non-empty, on-topic)
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "question,expected_any",
    [
        (
            "Is Lo-Salt safe for me?",
            ["avoid", "danger", "potassium", "not safe", "unsafe", "harmful"],
        ),
        (
            "Can I take whey protein powder?",
            ["avoid", "not recommend", "discourag", "egg white", "chicken", "too much", "high"],
        ),
        (
            "Is coconut water healthy for kidneys?",
            ["false", "avoid", "potassium", "high", "danger", "not"],
        ),
    ],
)
def test_ai_ask_vitamin_and_myths(auth_headers, question, expected_any):
    r = requests.post(
        f"{BASE_URL}/api/ai/ask",
        headers=auth_headers,
        json={"question": question, "lang": "en"},
        timeout=60,
    )
    assert r.status_code == 200, f"ai/ask failed ({r.status_code}): {r.text[:400]}"
    answer = r.json().get("answer", "")
    assert answer, f"empty answer for question: {question}"
    lowered = answer.lower()
    assert any(k in lowered for k in expected_any), (
        f"answer for '{question}' did not include any expected keyword.\n"
        f"answer: {answer[:400]}"
    )
    # brief pause to be gentle to rate limiter
    time.sleep(1)


# --------------------------------------------------------------------------
# Regression: schema completeness + food catalog size
# --------------------------------------------------------------------------
class TestRegression:
    def test_food_catalog_still_has_1000_plus_entries(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/foods?limit=5000", headers=auth_headers, timeout=30)
        assert r.status_code == 200
        foods = r.json()
        assert len(foods) > 1000, f"expected >1000 foods, got {len(foods)}"

    def test_food_detail_has_expected_fields(self, auth_headers):
        r = requests.get(
            f"{BASE_URL}/api/foods/food-paneer-small", headers=auth_headers, timeout=15
        )
        assert r.status_code == 200
        data = r.json()
        assert "food" in data
        food = data["food"]
        for key in [
            "id", "name", "hindi_name", "category", "safety_tier",
            "primary_risk_factor", "portion_g", "potassium_mg",
            "phosphorus_mg", "sodium_mg", "protein_g", "fluid_ml",
        ]:
            assert key in food, f"food missing {key}"

    def test_meal_log_summary_schema_complete(self, auth_headers):
        r = requests.get(
            f"{BASE_URL}/api/meal-logs/summary?date=2026-01-15",
            headers=auth_headers,
            timeout=15,
        )
        assert r.status_code == 200
        d = r.json()
        for key in ["date", "total_meals", "totals", "limits"]:
            assert key in d
        for k in ["potassium_mg", "phosphorus_mg", "sodium_mg", "protein_g", "fluid_ml"]:
            assert k in d["totals"], f"totals missing {k}"
            assert k in d["limits"], f"limits missing {k}"

    def test_weekly_report_schema_complete(self, auth_headers):
        r = requests.get(
            f"{BASE_URL}/api/reports/weekly?end_date=2026-01-15",
            headers=auth_headers,
            timeout=20,
        )
        assert r.status_code == 200
        d = r.json()
        for key in [
            "start_date", "end_date", "total_meals", "green", "yellow", "red",
            "days", "top_safe_foods", "top_avoid_foods", "avg_daily", "limits",
        ]:
            assert key in d, f"weekly report missing {key}"
        for k in ["potassium_mg", "phosphorus_mg", "sodium_mg", "protein_g", "fluid_ml"]:
            assert k in d["avg_daily"]
            assert k in d["limits"]
