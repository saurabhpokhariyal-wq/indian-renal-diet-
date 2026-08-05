"""Backend tests for iteration_16 - /api/vegetables/guide and /api/snacks/guide."""
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


# ---------- Vegetables Guide ----------
def test_vegetables_guide_shape(token):
    r = requests.get(
        f"{BASE_URL}/api/vegetables/guide",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    data = r.json()

    for tier in ("GREEN", "YELLOW", "RED"):
        assert tier in data, f"missing tier {tier}"
        sec = data[tier]
        assert "title" in sec and isinstance(sec["title"], str)
        assert "subtitle" in sec and isinstance(sec["subtitle"], str)
        assert "vegetables" in sec and isinstance(sec["vegetables"], list)

    assert len(data["GREEN"]["vegetables"]) == 10
    assert len(data["YELLOW"]["vegetables"]) == 8
    assert len(data["RED"]["vegetables"]) == 11

    entry = data["GREEN"]["vegetables"][0]
    for key in ("name", "hindi", "serving", "potassium_mg", "note", "linked_food_id"):
        assert key in entry, f"missing {key} in vegetable entry"


def test_veg_green_has_lauki_linked(token):
    r = requests.get(
        f"{BASE_URL}/api/vegetables/guide",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    data = r.json()
    lauki = [v for v in data["GREEN"]["vegetables"] if "Bottle Gourd (Lauki)" in v["name"]]
    assert lauki, f"Bottle Gourd (Lauki) not in GREEN: {[v['name'] for v in data['GREEN']['vegetables']]}"
    assert lauki[0]["linked_food_id"] == "food-lauki-sabzi", lauki[0]


def test_veg_red_has_potato_high_k(token):
    r = requests.get(
        f"{BASE_URL}/api/vegetables/guide",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    data = r.json()
    pot = [v for v in data["RED"]["vegetables"] if "Potato (regular)" in v["name"]]
    assert pot, "Potato (regular) missing from RED"
    assert pot[0]["potassium_mg"] >= 400, pot[0]
    assert pot[0]["linked_food_id"] == "food-aloo-sabzi", pot[0]


def test_veg_red_has_sajina_linked(token):
    r = requests.get(
        f"{BASE_URL}/api/vegetables/guide",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    data = r.json()
    sajina = [v for v in data["RED"]["vegetables"] if "Drumstick Leaves" in v["name"]]
    assert sajina, "Drumstick Leaves (Sajina) not in RED"
    assert sajina[0]["linked_food_id"] == "food-sajina", sajina[0]


# ---------- Snacks Guide ----------
def test_snacks_guide_shape(token):
    r = requests.get(
        f"{BASE_URL}/api/snacks/guide",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    data = r.json()

    for tier in ("GREEN", "YELLOW", "RED"):
        assert tier in data, f"missing tier {tier}"
        sec = data[tier]
        assert "title" in sec and isinstance(sec["title"], str)
        assert "subtitle" in sec and isinstance(sec["subtitle"], str)
        assert "snacks" in sec and isinstance(sec["snacks"], list)

    assert len(data["GREEN"]["snacks"]) == 6
    assert len(data["YELLOW"]["snacks"]) == 8
    assert len(data["RED"]["snacks"]) == 12

    entry = data["GREEN"]["snacks"][0]
    for key in ("name", "hindi", "serving", "potassium_mg", "note", "linked_food_id"):
        assert key in entry, f"missing {key} in snack entry"


def test_snacks_green_has_makhana(token):
    r = requests.get(
        f"{BASE_URL}/api/snacks/guide",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    data = r.json()
    names = [s["name"] for s in data["GREEN"]["snacks"]]
    assert any("Roasted Makhana (unsalted)" in n for n in names), names


def test_snacks_red_has_namkeen_and_maggi(token):
    r = requests.get(
        f"{BASE_URL}/api/snacks/guide",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    data = r.json()
    names = [s["name"] for s in data["RED"]["snacks"]]
    assert any("Namkeen / Bhujia / Mixture" in n for n in names), names
    assert any("Instant Noodles (Maggi etc.)" in n for n in names), names
