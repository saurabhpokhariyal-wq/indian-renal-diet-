"""iter-29 backend tests:

1) Lo-Salt values updated: K=346, Na=131, RED-POTASSIUM, source cites Klinge Foods + OFF barcode
2) Tata Salt Lite has data_quality_flag=concentrated_base_pending_resourcing,
   source starts with "COMPOSITION NOT YET SOURCED"
3) guide_needs_sourcing.csv still contains a Tata Salt Lite row
4) Barcode warning — Lo-Salt (5011544070034) → salt_substitute_warning=True
5) Barcode warning — Nutella (3017620422003) → salt_substitute_warning=False
6) _looks_like_salt_substitute regex catches expected terms and does not false-positive
7) Code-read: scan_food's early no-data return branch also computes the warning flag
"""
import csv
import inspect
import os
import sys

import pytest
import requests

# Ensure backend package is importable for unit-testing the helper directly
sys.path.insert(0, "/app/backend")

BASE_URL = os.environ.get(
    "EXPO_PUBLIC_BACKEND_URL",
    "https://safe-food-guide-1.preview.emergentagent.com",
).rstrip("/")

EMAIL = "demo@renal.app"
PASSWORD = "demo123"

CSV_PATH = "/app/backend/guide_needs_sourcing.csv"


# ---- Auth fixture ----
@pytest.fixture(scope="module")
def auth_headers():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=15,
    )
    if r.status_code != 200:
        # Try register-then-login just in case
        requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"email": EMAIL, "password": PASSWORD, "full_name": "Demo"},
            timeout=15,
        )
        r = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
            timeout=15,
        )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    tok = r.json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


# ---- 1) Lo-Salt corrected chemistry ----
class TestLoSaltComposition:
    def test_lo_salt_values(self, auth_headers):
        r = requests.get(
            f"{BASE_URL}/api/foods/food-lo-salt-substitute",
            headers=auth_headers,
            timeout=15,
        )
        assert r.status_code == 200, r.text
        food = r.json()["food"] if "food" in r.json() else r.json()
        assert food["potassium_mg"] == 346, f"Expected K=346, got {food['potassium_mg']}"
        assert food["sodium_mg"] == 131, f"Expected Na=131, got {food['sodium_mg']}"
        assert food["safety_tier"] == "RED"
        assert food["primary_risk_factor"] == "POTASSIUM"
        assert food.get("data_quality_flag") in (None, ""), \
            f"Lo-Salt should NOT be flagged as pending sourcing, got {food.get('data_quality_flag')}"
        source = food.get("source", "")
        assert "klinge-foods.com" in source.lower(), f"Source missing Klinge Foods: {source}"
        assert "5011544070034" in source, f"Source missing OFF barcode: {source}"


# ---- 2) Tata Salt Lite pending flag ----
class TestTataSaltLitePending:
    def test_tata_saltlite_flag(self, auth_headers):
        r = requests.get(
            f"{BASE_URL}/api/foods/food-tata-saltlite",
            headers=auth_headers,
            timeout=15,
        )
        assert r.status_code == 200, r.text
        food = r.json()["food"] if "food" in r.json() else r.json()
        assert food.get("data_quality_flag") == "concentrated_base_pending_resourcing", \
            f"Missing pending flag, got {food.get('data_quality_flag')}"
        assert food["potassium_mg"] == 184
        assert food["sodium_mg"] == 256
        source = food.get("source", "")
        assert source.startswith("COMPOSITION NOT YET SOURCED"), \
            f"Source must start with 'COMPOSITION NOT YET SOURCED', got: {source[:80]}"


# ---- 3) guide_needs_sourcing.csv row present ----
class TestGuideNeedsSourcing:
    def test_tata_saltlite_row(self):
        assert os.path.exists(CSV_PATH), f"Missing CSV: {CSV_PATH}"
        with open(CSV_PATH, encoding="utf-8") as fp:
            content = fp.read()
        assert "Tata Salt Lite" in content, "guide_needs_sourcing.csv missing Tata Salt Lite row"


# ---- 4) Barcode warning: real Lo-Salt on OFF ----
class TestBarcodeSaltWarning:
    def test_lo_salt_barcode_triggers_warning(self, auth_headers):
        r = requests.post(
            f"{BASE_URL}/api/scan/barcode",
            json={"barcode": "5011544070034"},
            headers=auth_headers,
            timeout=30,
        )
        # If OFF is down / rate-limited we surface 502 -> mark as expected skip
        if r.status_code == 502:
            pytest.skip(f"Open Food Facts unavailable ({r.status_code}): {r.text}")
        assert r.status_code == 200, f"Lo-Salt barcode failed: {r.status_code} {r.text}"
        data = r.json()
        assert data.get("salt_substitute_warning") is True, \
            f"Expected warning=True for Lo-Salt barcode, got {data.get('salt_substitute_warning')}. Body: {data}"

    def test_nutella_barcode_no_warning(self, auth_headers):
        r = requests.post(
            f"{BASE_URL}/api/scan/barcode",
            json={"barcode": "3017620422003"},
            headers=auth_headers,
            timeout=30,
        )
        if r.status_code == 502:
            pytest.skip(f"Open Food Facts unavailable ({r.status_code}): {r.text}")
        assert r.status_code == 200, f"Nutella barcode failed: {r.status_code} {r.text}"
        data = r.json()
        assert data.get("salt_substitute_warning") is False, \
            f"Expected warning=False for Nutella, got {data.get('salt_substitute_warning')}. Body: {data}"


# ---- 5) Regex unit tests on the helper ----
class TestSaltSubstituteRegex:
    """Direct import of the pattern helper — unit-level, no HTTP."""

    def test_positive_keywords(self):
        from routes.scan import _looks_like_salt_substitute

        positives = [
            "Potassium Chloride",
            "KCl",
            "Low Sodium Salt",
            "lite salt",
            "salt substitute",
            "salt alternative",
            "sendha namak",
            "rock salt",
            "Himalayan Pink Salt",
            "pink salt",
            "Lo-Salt",
            "NoSalt",
            "kala namak",
            "Black Salt",
            "Tata Salt Lite",
        ]
        failures = [t for t in positives if not _looks_like_salt_substitute(t)]
        assert not failures, f"Should have matched but did not: {failures}"

    def test_negative_keywords(self):
        from routes.scan import _looks_like_salt_substitute

        negatives = ["Nutella", "Ghee", "regular table salt", "", None]
        false_positives = [t for t in negatives if _looks_like_salt_substitute(t)]
        assert not false_positives, f"Should NOT have matched: {false_positives}"

    def test_multi_arg_matching(self):
        from routes.scan import _looks_like_salt_substitute

        # any positional matching → True
        assert _looks_like_salt_substitute("Ghee", "Amul", "contains potassium chloride", "") is True
        assert _looks_like_salt_substitute("Ghee", "Amul", "milk fat", "dairy") is False


# ---- 6) Code-read: scan_food no-match branch also computes the warning ----
class TestScanFoodWarningBranches:
    """Static code-read only: routes/scan.py's scan_food must have TWO return
    points and BOTH must include `salt_substitute_warning=` in their kwargs.
    We assert this by parsing the source file so a future refactor that drops
    the flag on the early-return path is caught immediately.
    """

    def test_two_return_branches_include_flag(self):
        with open("/app/backend/routes/scan.py", encoding="utf-8") as fp:
            src = fp.read()
        # Split into function definitions and check the scan_food body only
        import re
        body_match = re.search(
            r"async def scan_food\([^)]*\).*?(?=\nasync def |\Z)",
            src,
            re.DOTALL,
        )
        assert body_match, "Could not locate scan_food body"
        body = body_match.group(0)
        occurrences = body.count("salt_substitute_warning=")
        assert occurrences >= 2, (
            f"scan_food should set salt_substitute_warning in BOTH return "
            f"branches, found {occurrences} occurrences."
        )
