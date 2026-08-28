"""iter-28 backend tests:

1) Salt substitute chemistry correction — elemental K/Na values match K/KCl=0.525, Na/NaCl=0.394
2) All 6 salt substitutes have non-empty `source` field; conversion factor cited
3) guide_needs_sourcing.csv contains a Tata Salt Lite flag row
4) Regression: >1000 foods total; category=salt_substitute returns exactly 6
"""
import csv
import os

import pytest
import requests

BASE_URL = os.environ.get(
    "EXPO_PUBLIC_BACKEND_URL",
    "https://safe-food-guide-1.preview.emergentagent.com",
).rstrip("/")

EMAIL = "demo@renal.app"
PASSWORD = "demo123"

CSV_PATH = "/app/backend/guide_needs_sourcing.csv"

# expected values after chemistry correction
EXPECTED = {
    "food-lo-salt-substitute": {
        # iter-29: recomputed 660 × 0.525 = 346 (was 350 rounding)
        "potassium_mg": 346, "sodium_mg": 131,
        "safety_tier": "RED", "primary_risk_factor": "POTASSIUM",
    },
    "food-nosalt-substitute": {
        "potassium_mg": 525, "sodium_mg": 0,
        "safety_tier": "RED", "primary_risk_factor": "POTASSIUM",
    },
    "food-tata-saltlite": {
        "potassium_mg": 184, "sodium_mg": 256,
        "safety_tier": "YELLOW", "primary_risk_factor": "POTASSIUM",
    },
    "food-himalayan-pink-salt": {
        "potassium_mg": 3, "sodium_mg": 390,
        "safety_tier": "YELLOW", "primary_risk_factor": "SODIUM",
    },
    "food-kala-namak": {
        "potassium_mg": 5, "sodium_mg": 380,
        "safety_tier": "YELLOW", "primary_risk_factor": "SODIUM",
    },
    "food-lemon-herb-seasoning": {
        "potassium_mg": 25, "sodium_mg": 0,
        "safety_tier": "GREEN",
    },
}


@pytest.fixture(scope="module")
def auth_headers():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=15,
    )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}", "Content-Type": "application/json"}


# --------------------------------------------------------------------
# 1) chemistry-corrected values
# --------------------------------------------------------------------
class TestSaltChemistry:
    @pytest.mark.parametrize("fid,expected", list(EXPECTED.items()))
    def test_food_values_match_expected(self, auth_headers, fid, expected):
        r = requests.get(f"{BASE_URL}/api/foods/{fid}", headers=auth_headers, timeout=15)
        assert r.status_code == 200, f"{fid} lookup failed: {r.status_code}"
        food = r.json()["food"]
        for key, val in expected.items():
            actual = food.get(key)
            # numeric comparison tolerates float vs int
            if isinstance(val, (int, float)):
                assert float(actual) == float(val), f"{fid} {key} expected {val}, got {actual}"
            else:
                assert actual == val, f"{fid} {key} expected {val}, got {actual}"


# --------------------------------------------------------------------
# 2) source field populated + conversion factor cited
# --------------------------------------------------------------------
class TestSaltSources:
    def test_all_have_non_empty_source(self, auth_headers):
        for fid in EXPECTED.keys():
            r = requests.get(f"{BASE_URL}/api/foods/{fid}", headers=auth_headers, timeout=15)
            assert r.status_code == 200
            food = r.json()["food"]
            src = food.get("source")
            assert isinstance(src, str) and src.strip(), f"{fid} source empty: {src!r}"

    def test_conversion_factors_cited(self, auth_headers):
        # These entries should reference either K = KCl × 0.525 or Na = NaCl × 0.394.
        # iter-29: Tata Salt Lite source was rewritten to "COMPOSITION NOT YET SOURCED"
        # (data_quality_flag=concentrated_base_pending_resourcing) — it intentionally
        # no longer carries the chemistry factor. Only 4 entries must cite now.
        chem_expected = {
            "food-lo-salt-substitute",
            "food-nosalt-substitute",
            "food-himalayan-pink-salt",
            "food-kala-namak",
        }
        hits = 0
        for fid in chem_expected:
            r = requests.get(f"{BASE_URL}/api/foods/{fid}", headers=auth_headers, timeout=15)
            assert r.status_code == 200
            src = (r.json()["food"].get("source") or "").lower()
            if "0.525" in src or "0.394" in src:
                hits += 1
        assert hits >= 4, f"expected chemistry conversion factor in >=4 sources, got {hits}"


# --------------------------------------------------------------------
# 3) CSV flag row
# --------------------------------------------------------------------
class TestSourcingCSV:
    def test_csv_exists_and_has_tata_salt_lite_row(self):
        assert os.path.exists(CSV_PATH), f"{CSV_PATH} not found"
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        assert len(rows) > 1, "CSV appears empty"
        # search all cells for 'Tata Salt Lite'
        found = any(
            any("tata salt lite" in (cell or "").lower() for cell in row)
            for row in rows
        )
        assert found, "no row mentioning 'Tata Salt Lite' in guide_needs_sourcing.csv"


# --------------------------------------------------------------------
# 4) Regression: catalog size + category filter
# --------------------------------------------------------------------
class TestRegression:
    def test_food_catalog_still_over_1000(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/foods?limit=5000", headers=auth_headers, timeout=30)
        assert r.status_code == 200
        assert len(r.json()) > 1000

    def test_salt_substitute_category_returns_exactly_6(self, auth_headers):
        r = requests.get(
            f"{BASE_URL}/api/foods?category=salt_substitute",
            headers=auth_headers,
            timeout=15,
        )
        assert r.status_code == 200
        foods = r.json()
        assert len(foods) == 6, f"expected 6 salt_substitute entries, got {len(foods)}"
        ids = {f["id"] for f in foods}
        assert ids == set(EXPECTED.keys()), f"unexpected ids: {ids ^ set(EXPECTED.keys())}"
