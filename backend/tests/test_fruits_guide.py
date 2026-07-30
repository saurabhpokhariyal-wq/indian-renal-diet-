"""Iteration 14 — Fruit Guide endpoint tests."""
import os
import requests

BASE_URL = os.environ.get("EXPO_BACKEND_URL", "http://localhost:8001").rstrip("/")


def _login():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "demo@renal.app", "password": "demo123"},
        timeout=15,
    )
    assert r.status_code == 200, f"login failed {r.status_code}: {r.text}"
    return r.json()["access_token"]


class TestFruitsGuide:
    def test_b1_login(self):
        assert _login()

    def test_b2_fruits_guide_authed(self):
        token = _login()
        r = requests.get(
            f"{BASE_URL}/api/fruits/guide",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert set(["GREEN", "YELLOW", "RED"]).issubset(body.keys())
        for tier in ("GREEN", "YELLOW", "RED"):
            sec = body[tier]
            assert isinstance(sec.get("title"), str) and sec["title"]
            assert isinstance(sec.get("subtitle"), str) and sec["subtitle"]
            assert isinstance(sec.get("fruits"), list)
        f0 = body["GREEN"]["fruits"][0]
        for key in ("name", "hindi", "serving", "potassium_mg", "note", "linked_food_id"):
            assert key in f0, f"missing key {key} in first GREEN fruit"

        assert len(body["GREEN"]["fruits"]) >= 8
        assert len(body["YELLOW"]["fruits"]) >= 6
        assert len(body["RED"]["fruits"]) >= 8

        green_linked = [f for f in body["GREEN"]["fruits"] if f.get("linked_food_id")]
        red_linked = [f for f in body["RED"]["fruits"] if f.get("linked_food_id")]
        assert green_linked, "expected at least one GREEN fruit with linked_food_id"
        assert red_linked, "expected at least one RED fruit with linked_food_id"

        # Sanity: known links
        green_ids = {f["linked_food_id"] for f in green_linked}
        red_ids = {f["linked_food_id"] for f in red_linked}
        assert "food-apple" in green_ids
        assert "food-orange" in red_ids

    def test_b3_fruits_guide_unauth_behavior(self):
        r = requests.get(f"{BASE_URL}/api/fruits/guide", timeout=15)
        # Public or 401 — both acceptable, just record.
        assert r.status_code in (200, 401), r.text
        print(f"unauth /api/fruits/guide -> {r.status_code}")
