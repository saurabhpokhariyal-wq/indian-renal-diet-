"""Backend tests for /api/beverages/guide (iteration_15)."""
import os
import pytest
import requests

BASE_URL = os.environ.get("EXPO_BACKEND_URL", "http://localhost:3000").rstrip("/")


@pytest.fixture(scope="module")
def token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "demo@renal.app", "password": "demo123"},
        timeout=15,
    )
    assert r.status_code == 200, f"login failed {r.status_code} {r.text}"
    data = r.json()
    tok = data.get("access_token") or data.get("token")
    assert tok, f"no token in login response: {data}"
    return tok


def test_beverages_guide_authenticated(token):
    r = requests.get(
        f"{BASE_URL}/api/beverages/guide",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    data = r.json()

    # Tier keys
    for tier in ("GREEN", "YELLOW", "RED"):
        assert tier in data, f"missing tier {tier}"
        sec = data[tier]
        assert "title" in sec and isinstance(sec["title"], str)
        assert "subtitle" in sec and isinstance(sec["subtitle"], str)
        assert "beverages" in sec and isinstance(sec["beverages"], list)

    # Counts
    assert len(data["GREEN"]["beverages"]) >= 5, len(data["GREEN"]["beverages"])
    assert len(data["YELLOW"]["beverages"]) >= 5, len(data["YELLOW"]["beverages"])
    assert len(data["RED"]["beverages"]) >= 5, len(data["RED"]["beverages"])

    # Shape of first entry
    entry = data["GREEN"]["beverages"][0]
    for key in ("name", "hindi", "serving", "potassium_mg", "fluid_ml", "note", "linked_food_id"):
        assert key in entry, f"missing {key} in beverage entry"
    assert isinstance(entry["potassium_mg"], int)
    assert isinstance(entry["fluid_ml"], int)


def test_green_has_buttermilk(token):
    r = requests.get(
        f"{BASE_URL}/api/beverages/guide",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    data = r.json()
    names = [b["name"] for b in data["GREEN"]["beverages"]]
    assert any("Buttermilk" in n for n in names), f"Buttermilk not found in GREEN: {names}"


def test_yellow_has_masala_chai(token):
    r = requests.get(
        f"{BASE_URL}/api/beverages/guide",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    data = r.json()
    names = [b["name"] for b in data["YELLOW"]["beverages"]]
    assert any("Masala Chai" in n for n in names), f"Masala Chai not found in YELLOW: {names}"


def test_red_has_coconut_water_high_k(token):
    r = requests.get(
        f"{BASE_URL}/api/beverages/guide",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    data = r.json()
    coco = [b for b in data["RED"]["beverages"] if "Coconut Water" in b["name"]]
    assert coco, "Coconut Water not found in RED"
    assert coco[0]["potassium_mg"] >= 400, coco[0]
