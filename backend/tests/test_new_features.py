"""Tests for the 4 NEW features in Indian Renal Diet API.

Features under test:
1. POST /api/auth/stage       - onboarding stage quiz
2. GET  /api/foods/{id}       - personal_tier upgrade & auto-fallback swap
3. POST /api/favorites/{food} - toggle
4. GET  /api/foods?favorites_only=true
5. GET  /api/reports/weekly
6. POST /api/scan/food        - Claude Sonnet 4.5 vision
"""
import base64
import os
import uuid
from datetime import date, timedelta
from pathlib import Path

import pytest
import requests

BASE_URL = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or "https://safe-food-guide-1.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

# Real Indian-food JPEG downloaded to /tmp/food.jpg (unsplash Indian food, 600x800)
IMAGE_PATH = Path("/tmp/food.jpg")


# ---------- helpers ----------
def _make_user(session: requests.Session) -> dict:
    """Register a fresh user and return {token, headers, email, user}."""
    email = f"TEST_{uuid.uuid4().hex[:10]}@renal.app"
    r = session.post(
        f"{API}/auth/register",
        json={"email": email, "password": "pass1234", "full_name": "Test User"},
        timeout=20,
    )
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text}"
    d = r.json()
    return {
        "token": d["access_token"],
        "headers": {"Authorization": f"Bearer {d['access_token']}", "Content-Type": "application/json"},
        "email": email,
        "user": d["user"],
    }


@pytest.fixture(scope="module")
def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def fresh_user(session):
    return _make_user(session)


@pytest.fixture(scope="module")
def dialysis_user(session):
    """User whose stage is set to 'dialysis' via /auth/stage."""
    u = _make_user(session)
    r = session.post(f"{API}/auth/stage", headers=u["headers"], json={"stage": "dialysis"}, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["stage"] == "dialysis"
    u["user"] = body
    return u


# ==================== 1. AUTH / STAGE ====================
class TestStage:
    def test_new_user_has_stage_unknown(self, fresh_user):
        assert fresh_user["user"]["stage"] == "unknown"

    def test_stage_requires_auth(self, session):
        r = session.post(f"{API}/auth/stage", json={"stage": "dialysis"}, timeout=15)
        assert r.status_code == 401

    def test_set_stage_dialysis(self, session):
        u = _make_user(session)
        r = session.post(f"{API}/auth/stage", headers=u["headers"], json={"stage": "dialysis"}, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["stage"] == "dialysis"
        assert body["id"] == u["user"]["id"]

        # Verify via /auth/me
        me = session.get(f"{API}/auth/me", headers=u["headers"], timeout=15)
        assert me.status_code == 200
        assert me.json()["stage"] == "dialysis"

    def test_set_stage_pre_dialysis(self, session):
        u = _make_user(session)
        r = session.post(f"{API}/auth/stage", headers=u["headers"], json={"stage": "pre_dialysis"}, timeout=15)
        assert r.status_code == 200
        assert r.json()["stage"] == "pre_dialysis"

    def test_set_stage_invalid_value(self, session, fresh_user):
        r = session.post(
            f"{API}/auth/stage", headers=fresh_user["headers"], json={"stage": "bogus"}, timeout=15
        )
        assert r.status_code == 422  # Pydantic literal validation


# ==================== 2. PERSONAL TIER + AUTO SWAP ====================
class TestPersonalTier:
    def test_atta_roti_yellow_upgrades_to_red_for_dialysis(self, session, dialysis_user):
        r = session.get(f"{API}/foods/food-atta-roti", headers=dialysis_user["headers"], timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        # base YELLOW / PHOSPHORUS risk → personal RED for dialysis
        assert data["food"]["safety_tier"] == "YELLOW"
        assert data["food"]["primary_risk_factor"] == "PHOSPHORUS"
        assert data["food"]["personal_tier"] == "RED"
        # Auto-generated fallback swap should be present (GREEN alternative in same category)
        assert data["swap"] is not None, "expected auto swap for YELLOW→RED upgrade"
        assert data["swap"]["recommended_food"]["safety_tier"] == "GREEN"
        assert data["swap"]["clinical_benefit_explanation"]

    def test_atta_roti_stays_yellow_for_unknown_stage(self, session, fresh_user):
        r = session.get(f"{API}/foods/food-atta-roti", headers=fresh_user["headers"], timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["food"]["personal_tier"] == "YELLOW"
        # No swap since not RED
        assert data["swap"] is None

    def test_lauki_stays_green_for_dialysis(self, session, dialysis_user):
        r = session.get(f"{API}/foods/food-lauki-sabzi", headers=dialysis_user["headers"], timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["food"]["safety_tier"] == "GREEN"
        assert data["food"]["personal_tier"] == "GREEN"
        assert data["swap"] is None


# ==================== 3. FAVORITES ====================
class TestFavorites:
    def test_toggle_favorite_requires_auth(self, session):
        r = session.post(f"{API}/favorites/food-lauki-sabzi", timeout=15)
        assert r.status_code == 401

    def test_toggle_favorite_twice(self, session):
        u = _make_user(session)
        r1 = session.post(f"{API}/favorites/food-lauki-sabzi", headers=u["headers"], timeout=15)
        assert r1.status_code == 200, r1.text
        assert r1.json() == {"food_id": "food-lauki-sabzi", "is_favorite": True}

        r2 = session.post(f"{API}/favorites/food-lauki-sabzi", headers=u["headers"], timeout=15)
        assert r2.status_code == 200
        assert r2.json() == {"food_id": "food-lauki-sabzi", "is_favorite": False}

    def test_favorite_missing_food_404(self, session, fresh_user):
        r = session.post(f"{API}/favorites/does-not-exist", headers=fresh_user["headers"], timeout=15)
        assert r.status_code == 404

    def test_favorites_only_requires_auth(self, session):
        r = session.get(f"{API}/foods", params={"favorites_only": "true"}, timeout=15)
        assert r.status_code == 401

    def test_favorites_only_returns_only_favorited(self, session):
        u = _make_user(session)
        # Initially empty
        r = session.get(f"{API}/foods", params={"favorites_only": "true"}, headers=u["headers"], timeout=15)
        assert r.status_code == 200
        assert r.json() == []
        # Favorite two foods
        for fid in ("food-lauki-sabzi", "food-besan-chilla"):
            rr = session.post(f"{API}/favorites/{fid}", headers=u["headers"], timeout=15)
            assert rr.status_code == 200 and rr.json()["is_favorite"] is True
        r2 = session.get(f"{API}/foods", params={"favorites_only": "true"}, headers=u["headers"], timeout=15)
        assert r2.status_code == 200
        foods = r2.json()
        got_ids = sorted(f["id"] for f in foods)
        assert got_ids == ["food-besan-chilla", "food-lauki-sabzi"]
        assert all(f["is_favorite"] is True for f in foods)

    def test_food_detail_reflects_favorite(self, session):
        u = _make_user(session)
        session.post(f"{API}/favorites/food-lauki-sabzi", headers=u["headers"], timeout=15)
        r = session.get(f"{API}/foods/food-lauki-sabzi", headers=u["headers"], timeout=15)
        assert r.status_code == 200
        assert r.json()["food"]["is_favorite"] is True


# ==================== 4. WEEKLY REPORT ====================
class TestWeeklyReport:
    def test_requires_auth(self, session):
        r = session.get(f"{API}/reports/weekly", timeout=15)
        assert r.status_code == 401

    def test_weekly_report_empty(self, session, fresh_user):
        r = session.get(f"{API}/reports/weekly", headers=fresh_user["headers"], timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["total_meals"] == 0
        assert d["green"] == 0 and d["yellow"] == 0 and d["red"] == 0
        assert len(d["days"]) == 7
        # start/end 6 days apart
        s = date.fromisoformat(d["start_date"])
        e = date.fromisoformat(d["end_date"])
        assert (e - s).days == 6
        assert d["top_safe_foods"] == []
        assert d["top_avoid_foods"] == []

    def test_weekly_report_counts(self, session):
        u = _make_user(session)
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        # Log a GREEN today, a RED today, a YELLOW yesterday
        for food_id, d in (("food-lauki-sabzi", today), ("food-palak-paneer", today), ("food-atta-roti", yesterday)):
            r = session.post(
                f"{API}/meal-logs",
                headers=u["headers"],
                json={"food_id": food_id, "date": d, "meal_type": "lunch"},
                timeout=15,
            )
            assert r.status_code == 200, r.text
        r = session.get(f"{API}/reports/weekly", headers=u["headers"], timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["total_meals"] == 3
        assert d["green"] == 1
        assert d["yellow"] == 1
        assert d["red"] == 1
        assert "Lauki Sabzi" in d["top_safe_foods"]
        assert "Palak Paneer" in d["top_avoid_foods"]
        # days array covers 7 dates ending today
        days = {row["date"]: row for row in d["days"]}
        assert today in days
        assert days[today]["green"] == 1 and days[today]["red"] == 1
        assert days[yesterday]["yellow"] == 1

    def test_weekly_report_dialysis_promotes_yellow_to_red(self, session):
        """For dialysis user, atta-roti (YELLOW/PHOSPHORUS) counted as RED in the report."""
        u = _make_user(session)
        # set stage
        session.post(f"{API}/auth/stage", headers=u["headers"], json={"stage": "dialysis"}, timeout=15)
        today = date.today().isoformat()
        session.post(
            f"{API}/meal-logs",
            headers=u["headers"],
            json={"food_id": "food-atta-roti", "date": today, "meal_type": "lunch"},
            timeout=15,
        )
        r = session.get(f"{API}/reports/weekly", headers=u["headers"], timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["total_meals"] == 1
        assert d["red"] == 1
        assert d["yellow"] == 0
        assert any("Atta Roti" in name for name in d["top_avoid_foods"])


# ==================== 5. SCAN FOOD (Vision) ====================
class TestScanFood:
    def test_requires_auth(self, session):
        r = session.post(f"{API}/scan/food", json={"image_base64": "abc"}, timeout=30)
        assert r.status_code == 401

    def test_empty_image_400(self, session, fresh_user):
        r = session.post(f"{API}/scan/food", headers=fresh_user["headers"], json={"image_base64": ""}, timeout=30)
        assert r.status_code == 400

    def test_invalid_base64_400(self, session, fresh_user):
        r = session.post(
            f"{API}/scan/food",
            headers=fresh_user["headers"],
            json={"image_base64": "!!!not-valid-base64!!!"},
            timeout=30,
        )
        assert r.status_code == 400

    def test_scan_real_indian_food_image(self, session, fresh_user):
        assert IMAGE_PATH.exists(), f"missing test image at {IMAGE_PATH}"
        raw = IMAGE_PATH.read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")
        r = session.post(
            f"{API}/scan/food",
            headers=fresh_user["headers"],
            json={"image_base64": b64},
            timeout=120,
        )
        assert r.status_code == 200, f"scan failed: {r.status_code} {r.text[:400]}"
        d = r.json()
        # Contract validation
        for key in ("food_name", "safety_tier", "primary_risk_factor", "portion_limit_text", "clinical_tip"):
            assert key in d and d[key], f"missing/empty key: {key}"
        assert d["safety_tier"] in {"GREEN", "YELLOW", "RED"}
        assert d["primary_risk_factor"].upper() in {"POTASSIUM", "PHOSPHORUS", "SODIUM", "FLUID", "NONE"}
        # sanity length
        assert len(d["clinical_tip"]) > 10
        print(f"SCAN RESULT -> food_name={d['food_name']}, tier={d['safety_tier']}, risk={d['primary_risk_factor']}")

    def test_scan_data_url_prefix_stripped(self, session, fresh_user):
        raw = IMAGE_PATH.read_bytes()
        b64 = "data:image/jpeg;base64," + base64.b64encode(raw).decode("ascii")
        r = session.post(
            f"{API}/scan/food",
            headers=fresh_user["headers"],
            json={"image_base64": b64},
            timeout=120,
        )
        assert r.status_code == 200, r.text
