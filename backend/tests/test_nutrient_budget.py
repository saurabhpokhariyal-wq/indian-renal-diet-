"""Backend tests for iteration 5: nutrient data + daily budget + weekly avg_daily."""
import os
import uuid
from datetime import date

import pytest
import requests

BASE_URL = (
    os.environ.get("EXPO_PUBLIC_BACKEND_URL")
    or "https://kidney-safe-swap.preview.emergentagent.com"
).rstrip("/")
API = f"{BASE_URL}/api"

REQUIRED_NUTRIENT_FIELDS = (
    "portion_g",
    "potassium_mg",
    "phosphorus_mg",
    "sodium_mg",
    "protein_g",
    "fluid_ml",
)


def _register(session: requests.Session) -> dict:
    email = f"TEST_{uuid.uuid4().hex[:10]}@renal.app"
    r = session.post(
        f"{API}/auth/register",
        json={"email": email, "password": "pass1234", "full_name": "Test User"},
        timeout=20,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    return {
        "email": email,
        "token": d["access_token"],
        "headers": {
            "Authorization": f"Bearer {d['access_token']}",
            "Content-Type": "application/json",
        },
        "user": d["user"],
    }


@pytest.fixture(scope="module")
def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def user(session):
    return _register(session)


# ==================== 1. Nutrient fields per food ====================
class TestFoodNutrients:
    def test_palak_paneer_nutrient_values(self, session, user):
        r = session.get(f"{API}/foods/food-palak-paneer", headers=user["headers"], timeout=15)
        assert r.status_code == 200, r.text
        food = r.json()["food"]
        assert food["potassium_mg"] == 650
        assert food["phosphorus_mg"] == 180
        assert food["sodium_mg"] == 350
        assert food["protein_g"] == 10.0
        assert food["portion_g"] == 150
        assert food["fluid_ml"] == 0

    def test_palak_paneer_swap_benefit_is_computed(self, session, user):
        # Palak Paneer is RED for everyone; swap should exist.
        r = session.get(f"{API}/foods/food-palak-paneer", headers=user["headers"], timeout=15)
        data = r.json()
        assert data["swap"] is not None, "swap should exist for RED palak paneer"
        expl = data["swap"]["clinical_benefit_explanation"]
        assert expl.startswith("About 519mg less potassium"), (
            f"expected computed delta '519mg less potassium', got: {expl!r}"
        )
        # Must NOT be the old hard-coded string
        assert "70%" not in expl

    def test_orange_tip_is_factual(self, session, user):
        r = session.get(f"{API}/foods/food-orange", headers=user["headers"], timeout=15)
        assert r.status_code == 200, r.text
        tip = r.json()["food"]["actionable_clinical_tip"]
        assert "Moderately high potassium" in tip, f"tip missing phrase: {tip!r}"
        assert "dangerous" not in tip.lower()

    def test_idli_tip_mentions_added_salt(self, session, user):
        r = session.get(f"{API}/foods/food-idli", headers=user["headers"], timeout=15)
        assert r.status_code == 200
        tip = r.json()["food"]["actionable_clinical_tip"]
        assert "fermentation" not in tip.lower(), f"tip should not mention fermentation: {tip!r}"
        assert ("added salt" in tip.lower()) or ("sambar" in tip.lower()), (
            f"tip should reference added salt/sambar: {tip!r}"
        )


# ==================== 2. All seeded foods carry all nutrient fields ====================
class TestAllFoodsHaveNutrients:
    def test_all_35_foods_have_all_nutrient_fields(self, session, user):
        r = session.get(f"{API}/foods", headers=user["headers"], timeout=20)
        assert r.status_code == 200
        foods = r.json()
        assert len(foods) >= 25, f"expected at least 25 seeded foods, got {len(foods)}"
        for f in foods:
            for k in REQUIRED_NUTRIENT_FIELDS:
                assert k in f, f"food {f.get('id')} missing field {k}"
                assert f[k] is not None, f"food {f['id']} has null {k}"
                assert isinstance(f[k], (int, float)), (
                    f"food {f['id']}.{k} must be numeric, got {type(f[k]).__name__}"
                )


# ==================== 3. /meal-logs/summary ====================
class TestMealLogSummary:
    def test_requires_auth(self, session):
        today = date.today().isoformat()
        r = session.get(f"{API}/meal-logs/summary", params={"date": today}, timeout=15)
        assert r.status_code == 401

    def test_invalid_date_returns_400(self, session, user):
        r = session.get(
            f"{API}/meal-logs/summary",
            params={"date": "not-a-date"},
            headers=user["headers"],
            timeout=15,
        )
        assert r.status_code == 400

    def test_empty_summary_defaults(self, session):
        u = _register(session)
        today = date.today().isoformat()
        r = session.get(
            f"{API}/meal-logs/summary",
            params={"date": today},
            headers=u["headers"],
            timeout=15,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["date"] == today
        assert d["total_meals"] == 0
        assert d["totals"]["potassium_mg"] == 0
        assert d["limits"] == {
            "potassium_mg": 2000,
            "phosphorus_mg": 1000,
            "sodium_mg": 2000,
        }

    def test_summary_totals_after_logging(self, session):
        """Palak Paneer(K650,P180,Na350) + Lauki(K131,P20,Na3) + Egg Whites(K110,P10,Na110)."""
        u = _register(session)
        today = date.today().isoformat()
        for fid in ("food-palak-paneer", "food-lauki-sabzi", "food-egg-whites"):
            rr = session.post(
                f"{API}/meal-logs",
                headers=u["headers"],
                json={"food_id": fid, "date": today, "meal_type": "lunch"},
                timeout=15,
            )
            assert rr.status_code == 200, rr.text

        r = session.get(
            f"{API}/meal-logs/summary",
            params={"date": today},
            headers=u["headers"],
            timeout=15,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["total_meals"] == 3
        # allow ±1 for rounding
        assert abs(d["totals"]["potassium_mg"] - 891) <= 1, d["totals"]
        assert abs(d["totals"]["phosphorus_mg"] - 210) <= 1, d["totals"]
        assert abs(d["totals"]["sodium_mg"] - 463) <= 1, d["totals"]
        assert d["limits"]["potassium_mg"] == 2000
        assert d["limits"]["phosphorus_mg"] == 1000
        assert d["limits"]["sodium_mg"] == 2000


# ==================== 4. Weekly report avg_daily + limits ====================
class TestWeeklyAvgDaily:
    def test_weekly_empty_has_avg_and_limits(self, session):
        u = _register(session)
        r = session.get(f"{API}/reports/weekly", headers=u["headers"], timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "avg_daily" in d
        assert "limits" in d
        assert d["avg_daily"]["potassium_mg"] == 0
        assert d["limits"] == {
            "potassium_mg": 2000,
            "phosphorus_mg": 1000,
            "sodium_mg": 2000,
        }

    def test_weekly_avg_daily_math(self, session):
        u = _register(session)
        today = date.today().isoformat()
        # Log Palak Paneer (K=650) once this week → avg K = round(650/7,1)
        rr = session.post(
            f"{API}/meal-logs",
            headers=u["headers"],
            json={"food_id": "food-palak-paneer", "date": today, "meal_type": "lunch"},
            timeout=15,
        )
        assert rr.status_code == 200
        r = session.get(f"{API}/reports/weekly", headers=u["headers"], timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["avg_daily"]["potassium_mg"] == round(650 / 7, 1)
        assert d["avg_daily"]["phosphorus_mg"] == round(180 / 7, 1)
        assert d["avg_daily"]["sodium_mg"] == round(350 / 7, 1)


# ==================== 5. Regression spot-checks (auth / favorites / tier filter) ====================
class TestRegression:
    def test_register_duplicate_returns_400(self, session, user):
        r = session.post(
            f"{API}/auth/register",
            json={"email": user["email"], "password": "pass1234", "full_name": "dup"},
            timeout=15,
        )
        assert r.status_code == 400

    def test_food_schema_has_required_keys(self, session, user):
        r = session.get(f"{API}/foods", headers=user["headers"], timeout=15)
        assert r.status_code == 200
        f = r.json()[0]
        for k in ("id", "name", "safety_tier", "primary_risk_factor", "personal_tier"):
            assert k in f

    def test_tier_filter_red_only(self, session, user):
        r = session.get(
            f"{API}/foods", params={"tier": "RED"}, headers=user["headers"], timeout=15
        )
        assert r.status_code == 200
        foods = r.json()
        assert len(foods) > 0
        assert all(f["safety_tier"] == "RED" for f in foods)

    def test_favorite_toggle_still_works(self, session):
        u = _register(session)
        r = session.post(
            f"{API}/favorites/food-lauki-sabzi", headers=u["headers"], timeout=15
        )
        assert r.status_code == 200
        assert r.json()["is_favorite"] is True
