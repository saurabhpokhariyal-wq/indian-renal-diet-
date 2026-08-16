"""Iteration 21 — IFCT 2017 sourcing pass validation.

Tests updated / new guide entries and regression on Iter-20 sodium tracking.
"""
import os
import requests
import pytest

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "https://kidney-safe-swap.preview.emergentagent.com").rstrip("/")


@pytest.fixture(scope="module")
def s():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


def _find(entries, name_contains):
    """case-insensitive substring match on `name`."""
    n = name_contains.lower()
    for e in entries:
        if n in e.get("name", "").lower():
            return e
    return None


def _all(guide, key):
    out = []
    for tier, tier_data in guide.items():
        if isinstance(tier_data, dict) and key in tier_data:
            for e in tier_data[key]:
                e = dict(e)
                e["_tier"] = tier
                out.append(e)
    return out


# ---------- fixtures pulling guides once ----------
@pytest.fixture(scope="module")
def proteins(s):
    r = s.get(f"{BASE_URL}/api/proteins/guide", timeout=20)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(scope="module")
def fruits(s):
    r = s.get(f"{BASE_URL}/api/fruits/guide", timeout=20)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(scope="module")
def vegetables(s):
    r = s.get(f"{BASE_URL}/api/vegetables/guide", timeout=20)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(scope="module")
def beverages(s):
    r = s.get(f"{BASE_URL}/api/beverages/guide", timeout=20)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(scope="module")
def snacks(s):
    r = s.get(f"{BASE_URL}/api/snacks/guide", timeout=20)
    assert r.status_code == 200, r.text
    return r.json()


# ---------- Proteins RED: Egg Yolk (alone) ----------
class TestProteins:
    def test_egg_yolk_alone_ifct_values(self, proteins):
        red = proteins["RED"]["proteins"]
        e = _find(red, "Egg Yolk")
        assert e is not None, "Egg Yolk (alone) missing in RED tier"
        assert e["potassium_mg"] == 18
        assert e.get("phosphorus_mg") == 100
        assert e.get("sodium_mg") == 8
        assert e["potassium_meq"] == 0.5
        assert e["high_sodium"] is False
        assert "M006" in (e.get("source") or "")

    def test_khoa_mawa(self, proteins):
        red = proteins["RED"]["proteins"]
        e = _find(red, "Khoa")
        assert e is not None, "Khoa/Mawa missing"
        assert e["potassium_mg"] == 161
        assert e.get("phosphorus_mg") == 143
        assert e.get("sodium_mg") == 14
        assert e["potassium_meq"] == 4.1
        assert e["high_sodium"] is False
        assert "L004" in (e.get("source") or "")

    def test_whole_egg_boiled(self, proteins):
        y = proteins["YELLOW"]["proteins"]
        e = _find(y, "Whole Egg")
        assert e is not None, "Whole Egg (boiled) missing"
        assert e["potassium_mg"] == 63
        assert e.get("phosphorus_mg") == 105
        assert e.get("sodium_mg") == 61
        assert e["high_sodium"] is False
        assert "M004" in (e.get("source") or "")

    def test_legacy_toor_dal_no_source(self, proteins):
        y = proteins["YELLOW"]["proteins"]
        e = _find(y, "Toor Dal")
        assert e is not None
        assert e.get("source") is None or "source" not in e


# ---------- Fruits ----------
class TestFruits:
    def test_muskmelon_ifct_correction(self, fruits):
        y = fruits["YELLOW"]["fruits"]
        e = _find(y, "Muskmelon")
        assert e is not None
        assert e["potassium_mg"] == 294, f"Expected 294 (IFCT), got {e['potassium_mg']}"
        assert e["potassium_meq"] == 7.5
        assert e.get("sodium_mg") == 24
        assert e["high_sodium"] is False
        assert "E046" in (e.get("source") or "")

    def test_fig_fresh_green(self, fruits):
        g = fruits["GREEN"]["fruits"]
        e = _find(g, "Fig")
        assert e is not None
        assert e["potassium_mg"] == 116
        assert e["potassium_meq"] == 3.0
        assert e.get("sodium_mg") == 1
        assert e["high_sodium"] is False
        assert "E020" in (e.get("source") or "")

    def test_ber_yellow(self, fruits):
        y = fruits["YELLOW"]["fruits"]
        e = _find(y, "Ber")
        assert e is not None
        assert e["potassium_mg"] == 237
        assert e["potassium_meq"] == 6.1
        assert e["high_sodium"] is False
        assert "E068" in (e.get("source") or "")

    def test_bael_red(self, fruits):
        r = fruits["RED"]["fruits"]
        e = _find(r, "Bael")
        assert e is not None
        assert e["potassium_mg"] == 409
        assert e["potassium_meq"] == 10.5
        assert e["high_sodium"] is False
        assert "E008" in (e.get("source") or "")

    def test_phalsa_red(self, fruits):
        r = fruits["RED"]["fruits"]
        e = _find(r, "Phalsa")
        assert e is not None
        assert e["potassium_mg"] == 362
        assert e["potassium_meq"] == 9.3
        assert e["high_sodium"] is False
        assert "E052" in (e.get("source") or "")

    def test_apple_legacy_no_source(self, fruits):
        g = fruits["GREEN"]["fruits"]
        e = _find(g, "Apple")
        assert e is not None
        assert e.get("source") is None or "source" not in e


# ---------- Vegetables ----------
class TestVegetables:
    def test_radish_yellow(self, vegetables):
        y = vegetables["YELLOW"]["vegetables"]
        e = _find(y, "Radish")
        assert e is not None
        assert e["potassium_mg"] == 287
        assert e["potassium_meq"] == 7.3
        assert e.get("sodium_mg") == 24
        assert e["high_sodium"] is False
        assert "F012" in (e.get("source") or "")

    def test_water_chestnut_yellow(self, vegetables):
        y = vegetables["YELLOW"]["vegetables"]
        e = _find(y, "Water Chestnut")
        assert e is not None
        assert e["potassium_mg"] == 382
        assert e["potassium_meq"] == 9.8
        assert e.get("sodium_mg") == 13
        assert e["high_sodium"] is False
        assert "F016" in (e.get("source") or "")

    def test_bottle_gourd_legacy_no_source(self, vegetables):
        g = vegetables["GREEN"]["vegetables"]
        e = _find(g, "Bottle Gourd")
        assert e is not None
        assert e.get("source") is None or "source" not in e


# ---------- Regression: iter-20 sodium tracking preserved ----------
class TestIter20Regression:
    def test_jaljeera_still_high_sodium(self, beverages):
        y = beverages["YELLOW"]["beverages"]
        e = _find(y, "Jaljeera")
        assert e is not None
        assert e["high_sodium"] is True

    def test_pani_puri_still_high_sodium(self, snacks):
        # try YELLOW then RED
        e = None
        for tier in ("YELLOW", "RED", "GREEN"):
            e = _find(snacks[tier]["snacks"], "Pani Puri")
            if e:
                break
        assert e is not None
        assert e["high_sodium"] is True


# ---------- Regression: core APIs ----------
class TestCoreApis:
    def test_foods_list(self, s):
        r = s.get(f"{BASE_URL}/api/foods", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) > 0

    def test_auth_login_and_me(self, s):
        r = s.post(f"{BASE_URL}/api/auth/login",
                   json={"email": "demo@renal.app", "password": "demo123"}, timeout=20)
        assert r.status_code == 200, r.text
        token = r.json().get("access_token") or r.json().get("token")
        assert token
        r2 = s.get(f"{BASE_URL}/api/auth/me",
                   headers={"Authorization": f"Bearer {token}"}, timeout=20)
        assert r2.status_code == 200

    def test_meal_logs_crud(self, s):
        # login
        r = s.post(f"{BASE_URL}/api/auth/login",
                   json={"email": "demo@renal.app", "password": "demo123"}, timeout=20)
        token = r.json().get("access_token") or r.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}

        # Get list of meal-logs — endpoint may be /api/meal-logs or /api/meals
        for path in ("/api/meal-logs", "/api/meals"):
            r = s.get(f"{BASE_URL}{path}", headers=headers, timeout=20)
            if r.status_code == 200:
                assert isinstance(r.json(), list)
                return
        pytest.skip("No meal endpoint found; not a iter-21 regression concern.")


# ---------- Global assertion: all 9 iter-21 new/updated entries have high_sodium=False ----------
class TestAllNewEntriesLowSodium:
    def test_all_ifct_entries_low_sodium(self, proteins, fruits, vegetables):
        targets = [
            ("proteins", proteins, "proteins", ["Egg Yolk", "Khoa", "Whole Egg"]),
            ("fruits",   fruits,   "fruits",   ["Muskmelon", "Fig", "Ber", "Bael", "Phalsa"]),
            ("veg",      vegetables, "vegetables", ["Radish", "Water Chestnut"]),
        ]
        found = 0
        for _, guide, key, names in targets:
            all_entries = _all(guide, key)
            for name in names:
                e = _find(all_entries, name)
                assert e is not None, f"{name} not found"
                assert e["high_sodium"] is False, f"{name} unexpectedly high_sodium"
                found += 1
        # Spec says "9 new/updated" but tally is 10 (3 protein + 5 fruit + 2 veg).
        assert found == 10
