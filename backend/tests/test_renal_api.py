"""End-to-end backend tests for Indian Renal Diet API."""
import os
import uuid
from datetime import date

import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL") or "https://safe-food-guide-1.preview.emergentagent.com"
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"

DEMO_EMAIL = "demo@renal.app"
DEMO_PASSWORD = "demo123"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def token(session):
    # Try login first
    r = session.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}, timeout=15)
    if r.status_code != 200:
        # Register the demo user if missing
        r = session.post(f"{API}/auth/register", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD, "full_name": "Demo User"}, timeout=15)
    assert r.status_code == 200, f"auth failed: {r.status_code} {r.text}"
    data = r.json()
    assert "access_token" in data and "user" in data
    return data["access_token"]


@pytest.fixture(scope="module")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ---------- AUTH ----------
class TestAuth:
    def test_register_new_user(self, session):
        email = f"test_{uuid.uuid4().hex[:8]}@renal.app"
        r = session.post(f"{API}/auth/register", json={"email": email, "password": "pass1234", "full_name": "T"}, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["token_type"] == "bearer"
        assert d["user"]["email"] == email
        assert "access_token" in d

    def test_register_duplicate_rejected(self, session):
        r = session.post(f"{API}/auth/register", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}, timeout=15)
        assert r.status_code == 400

    def test_login_wrong_pw(self, session):
        r = session.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": "wrongwrong"}, timeout=15)
        assert r.status_code == 401

    def test_me_requires_auth(self, session):
        r = session.get(f"{API}/auth/me", timeout=15)
        assert r.status_code == 401

    def test_me_with_token(self, session, auth_headers):
        r = session.get(f"{API}/auth/me", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["email"] == DEMO_EMAIL


# ---------- FOODS ----------
class TestFoods:
    def test_list_all_foods_35(self, session):
        r = session.get(f"{API}/foods", timeout=15)
        assert r.status_code == 200
        foods = r.json()
        assert len(foods) >= 35, f"expected >=35 seeded foods, got {len(foods)}"
        # sanity check on fields
        f0 = foods[0]
        for k in ("id", "name", "hindi_name", "safety_tier", "primary_risk_factor"):
            assert k in f0

    def test_search_palak(self, session):
        r = session.get(f"{API}/foods", params={"q": "palak"}, timeout=15)
        assert r.status_code == 200
        results = r.json()
        assert any(f["id"] == "food-palak-paneer" for f in results)

    def test_search_besan(self, session):
        r = session.get(f"{API}/foods", params={"q": "besan"}, timeout=15)
        assert r.status_code == 200
        assert any(f["id"] == "food-besan-chilla" for f in r.json())

    def test_search_lauki(self, session):
        r = session.get(f"{API}/foods", params={"q": "lauki"}, timeout=15)
        assert r.status_code == 200
        assert any(f["id"] == "food-lauki-sabzi" for f in r.json())

    def test_tier_filter_red(self, session):
        r = session.get(f"{API}/foods", params={"tier": "RED"}, timeout=15)
        assert r.status_code == 200
        foods = r.json()
        assert len(foods) > 0
        assert all(f["safety_tier"] == "RED" for f in foods)

    def test_food_detail_red_has_swap(self, session):
        r = session.get(f"{API}/foods/food-palak-paneer", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["food"]["id"] == "food-palak-paneer"
        assert data["food"]["safety_tier"] == "RED"
        assert data["swap"] is not None
        assert data["swap"]["recommended_food"]["id"] == "food-lauki-sabzi"
        assert data["swap"]["clinical_benefit_explanation"]

    def test_food_detail_green_no_swap(self, session):
        r = session.get(f"{API}/foods/food-lauki-sabzi", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["food"]["safety_tier"] == "GREEN"
        assert data["swap"] is None

    def test_food_detail_not_found(self, session):
        r = session.get(f"{API}/foods/does-not-exist", timeout=15)
        assert r.status_code == 404


# ---------- MEAL LOGS ----------
class TestMealLogs:
    _today = date.today().isoformat()
    _created_id = None

    def test_list_requires_auth(self, session):
        r = session.get(f"{API}/meal-logs", params={"date": self._today}, timeout=15)
        assert r.status_code == 401

    def test_create_meal_log(self, session, auth_headers):
        r = session.post(
            f"{API}/meal-logs",
            headers=auth_headers,
            json={"food_id": "food-lauki-sabzi", "date": self._today, "meal_type": "lunch"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        log = r.json()
        assert log["food_id"] == "food-lauki-sabzi"
        assert log["date"] == self._today
        assert log["food"]["name"] == "Lauki Sabzi"
        TestMealLogs._created_id = log["id"]

    def test_list_shows_created(self, session, auth_headers):
        r = session.get(f"{API}/meal-logs", params={"date": self._today}, headers=auth_headers, timeout=15)
        assert r.status_code == 200
        ids = [l["id"] for l in r.json()]
        assert TestMealLogs._created_id in ids

    def test_delete_meal_log(self, session, auth_headers):
        assert TestMealLogs._created_id
        r = session.delete(f"{API}/meal-logs/{TestMealLogs._created_id}", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        # verify deletion
        r2 = session.get(f"{API}/meal-logs", params={"date": self._today}, headers=auth_headers, timeout=15)
        assert TestMealLogs._created_id not in [l["id"] for l in r2.json()]

    def test_create_meal_log_invalid_food(self, session, auth_headers):
        r = session.post(
            f"{API}/meal-logs",
            headers=auth_headers,
            json={"food_id": "nope", "date": self._today, "meal_type": "meal"},
            timeout=15,
        )
        assert r.status_code == 404


# ---------- AI ----------
class TestAI:
    def test_ai_requires_auth(self, session):
        r = session.post(f"{API}/ai/ask", json={"question": "Is palak paneer safe?"}, timeout=30)
        assert r.status_code == 401

    def test_ai_empty_question(self, session, auth_headers):
        r = session.post(f"{API}/ai/ask", headers=auth_headers, json={"question": "   "}, timeout=30)
        assert r.status_code == 400

    def test_ai_ask_returns_answer(self, session, auth_headers):
        r = session.post(
            f"{API}/ai/ask",
            headers=auth_headers,
            json={"question": "Is palak paneer safe for a CKD patient on dialysis?"},
            timeout=90,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "answer" in data
        assert len(data["answer"]) > 20
