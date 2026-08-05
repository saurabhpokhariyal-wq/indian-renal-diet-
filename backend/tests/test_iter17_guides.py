"""Iteration 17 — new Proteins & Grains guides + regression sweep on existing guides and foods."""
import os
import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "http://localhost:8001").rstrip("/")


@pytest.fixture(scope="module")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


TIERS = ("GREEN", "YELLOW", "RED")


def _assert_tier_shape(payload: dict, item_key: str):
    for tier in TIERS:
        assert tier in payload, f"missing tier {tier}"
        sec = payload[tier]
        assert isinstance(sec.get("title"), str) and sec["title"]
        assert isinstance(sec.get("subtitle"), str) and sec["subtitle"]
        items = sec.get(item_key)
        assert isinstance(items, list) and len(items) >= 3, f"{tier}.{item_key} needs >=3 items"
        for it in items:
            assert isinstance(it.get("name"), str) and it["name"]
            assert "serving" in it
            assert "note" in it and it["note"]
            assert "potassium_mg" in it


# ---- New guides ----
class TestProteinsGuide:
    def test_returns_200_and_shape(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/proteins/guide")
        assert r.status_code == 200
        _assert_tier_shape(r.json(), "proteins")

    def test_has_linked_toor_dal(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/proteins/guide")
        yellow = r.json()["YELLOW"]["proteins"]
        assert any(p.get("linked_food_id") == "food-toor-dal" for p in yellow)


class TestGrainsGuide:
    def test_returns_200_and_shape(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/grains/guide")
        assert r.status_code == 200
        _assert_tier_shape(r.json(), "grains")

    def test_has_linked_atta_roti(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/grains/guide")
        yellow = r.json()["YELLOW"]["grains"]
        assert any(g.get("linked_food_id") == "food-atta-roti" for g in yellow)


# ---- Regression on existing guides ----
@pytest.mark.parametrize("path,key", [
    ("/api/fruits/guide", "fruits"),
    ("/api/beverages/guide", "beverages"),
    ("/api/vegetables/guide", "vegetables"),
    ("/api/snacks/guide", "snacks"),
])
def test_existing_guides_still_ok(api_client, path, key):
    r = api_client.get(f"{BASE_URL}{path}")
    assert r.status_code == 200, path
    body = r.json()
    for tier in TIERS:
        assert tier in body
        assert isinstance(body[tier].get(key), list)


# ---- Foods regression ----
class TestFoodsRegression:
    def test_foods_count(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/foods?limit=5000")
        assert r.status_code == 200
        assert len(r.json()) >= 1018

    @pytest.mark.parametrize("fid,expected_base_tier", [
        ("food-toor-dal", "YELLOW"),
        ("food-brown-rice", "YELLOW"),
        ("food-orange", None),  # just verify fetch works
    ])
    def test_food_detail(self, api_client, fid, expected_base_tier):
        r = api_client.get(f"{BASE_URL}/api/foods/{fid}")
        assert r.status_code == 200, f"{fid} not found"
        food = r.json()["food"]
        assert food["id"] == fid
        if expected_base_tier:
            assert food["safety_tier"] == expected_base_tier
            # tier_override should be True for the clinically-held YELLOW rows
            assert food.get("tier_override") is True, f"{fid} missing tier_override"

    def test_orange_exists_and_has_tier(self, api_client):
        r = api_client.get(f"{BASE_URL}/api/foods/food-orange")
        assert r.status_code == 200
        assert r.json()["food"]["safety_tier"] in TIERS
