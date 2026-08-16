"""Iteration 20 backend tests — sodium_mg + high_sodium + potassium_meq derived fields.

Covers:
- Every guide entry has potassium_meq (float) and high_sodium (bool).
- Specific new entries added in this iteration are present with correct values.
- guide_needs_sourcing.csv exists with correct header, 7 flagged-not-added rows,
  and ~140-150 sodium-null rows.
- Regression: /api/foods, /api/foods/food-toor-dal, /api/auth/register+login,
  /api/auth/profile nutrient_unit round-trip, /api/meals CRUD.
"""
from __future__ import annotations

import os
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback to public URL in frontend/.env for the k8s ingress path
    with open("/app/frontend/.env") as fh:
        for line in fh:
            if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

DEMO_EMAIL = "demo@renal.app"
DEMO_PASSWORD = "demo123"


# ---------- Fixtures ----------
@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def auth_headers(api) -> Dict[str, str]:
    # Try login; register if it doesn't exist
    r = api.post(f"{BASE_URL}/api/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    if r.status_code != 200:
        api.post(
            f"{BASE_URL}/api/auth/register",
            json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD, "full_name": "Demo User"},
        )
        r = api.post(f"{BASE_URL}/api/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok, f"no token in login response: {r.json()}"
    return {"Authorization": f"Bearer {tok}"}


# ---------- Helpers ----------
def _flatten_entries(guide_json: Dict[str, Any], entries_key: str) -> List[Tuple[str, Dict[str, Any]]]:
    """Return [(tier_key, entry), ...] for a guide JSON payload."""
    out: List[Tuple[str, Dict[str, Any]]] = []
    for tier_key, tier_data in guide_json.items():
        if isinstance(tier_data, dict) and entries_key in tier_data:
            for e in tier_data[entries_key]:
                out.append((tier_key, e))
    return out


def _find(entries: List[Tuple[str, Dict[str, Any]]], name_substr: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    for tier, e in entries:
        if name_substr.lower() in str(e.get("name", "")).lower():
            return tier, e
    return None


# ---------- Guide utility (unit) ----------
def test_potassium_meq_helper_roundtrip():
    from backend.guide_utils import mg_to_meq_potassium  # type: ignore
    assert mg_to_meq_potassium(158) == round(158 / 39.1, 1)  # ~4.0
    assert mg_to_meq_potassium(0) == 0.0


# ---------- FRUITS ----------
class TestFruitsGuide:
    def test_all_entries_have_derived_fields(self, api):
        r = api.get(f"{BASE_URL}/api/fruits/guide")
        assert r.status_code == 200
        data = r.json()
        entries = _flatten_entries(data, "fruits")
        assert len(entries) > 0
        for _tier, e in entries:
            assert "potassium_meq" in e and isinstance(e["potassium_meq"], (int, float))
            assert "high_sodium" in e and isinstance(e["high_sodium"], bool)

    def test_apple_potassium_meq(self, api):
        r = api.get(f"{BASE_URL}/api/fruits/guide")
        entries = _flatten_entries(r.json(), "fruits")
        found = _find(entries, "Apple")
        assert found is not None
        tier, e = found
        assert e["potassium_mg"] == 158
        assert abs(e["potassium_meq"] - 4.0) < 0.15  # 158/39.1 = 4.04

    def test_muskmelon_new_entry(self, api):
        r = api.get(f"{BASE_URL}/api/fruits/guide")
        entries = _flatten_entries(r.json(), "fruits")
        found = _find(entries, "Muskmelon")
        assert found is not None, "Muskmelon (Kharbuja) must be added"
        tier, e = found
        assert tier.upper() == "YELLOW"
        assert e["potassium_mg"] == 400
        assert e["sodium_mg"] == 24
        assert e["high_sodium"] is False


# ---------- VEGETABLES ----------
class TestVegetablesGuide:
    def test_karela_new_entry(self, api):
        r = api.get(f"{BASE_URL}/api/vegetables/guide")
        assert r.status_code == 200
        entries = _flatten_entries(r.json(), "vegetables")
        found = _find(entries, "Bitter Gourd")
        assert found is not None
        tier, e = found
        assert tier.upper() == "YELLOW"
        assert e["potassium_mg"] == 280
        assert e["sodium_mg"] is None
        assert e["high_sodium"] is False

    def test_raw_banana_new_entry(self, api):
        r = api.get(f"{BASE_URL}/api/vegetables/guide")
        entries = _flatten_entries(r.json(), "vegetables")
        found = _find(entries, "Raw Banana")
        assert found is not None
        tier, e = found
        assert tier.upper() == "YELLOW"
        assert e["potassium_mg"] == 400
        assert e["sodium_mg"] is None
        assert e["high_sodium"] is False

    def test_all_have_meq_and_flag(self, api):
        r = api.get(f"{BASE_URL}/api/vegetables/guide")
        for _t, e in _flatten_entries(r.json(), "vegetables"):
            assert "potassium_meq" in e
            assert "high_sodium" in e


# ---------- SNACKS ----------
class TestSnacksGuide:
    def test_dhokla(self, api):
        r = api.get(f"{BASE_URL}/api/snacks/guide")
        assert r.status_code == 200
        entries = _flatten_entries(r.json(), "snacks")
        found = _find(entries, "Dhokla")
        assert found is not None
        _tier, e = found
        assert e["potassium_mg"] == 240
        assert e["sodium_mg"] == 310
        assert e["high_sodium"] is False

    def test_pani_puri_high_sodium(self, api):
        r = api.get(f"{BASE_URL}/api/snacks/guide")
        entries = _flatten_entries(r.json(), "snacks")
        found = _find(entries, "Pani Puri")
        assert found is not None
        _tier, e = found
        assert e["potassium_mg"] == 250
        assert e["sodium_mg"] == 450
        assert e["high_sodium"] is True

    def test_banana_chips(self, api):
        r = api.get(f"{BASE_URL}/api/snacks/guide")
        entries = _flatten_entries(r.json(), "snacks")
        found = _find(entries, "Banana Chips")
        assert found is not None
        _tier, e = found
        assert _tier.upper() == "YELLOW"
        assert e["potassium_mg"] == 140
        assert e["sodium_mg"] is None
        assert e["high_sodium"] is False


# ---------- BEVERAGES ----------
class TestBeveragesGuide:
    def test_almond_milk(self, api):
        r = api.get(f"{BASE_URL}/api/beverages/guide")
        assert r.status_code == 200
        entries = _flatten_entries(r.json(), "beverages")
        found = _find(entries, "Almond Milk")
        assert found is not None
        tier, e = found
        assert tier.upper() == "GREEN"
        assert e["potassium_mg"] == 67
        assert e["sodium_mg"] == 60
        assert e["high_sodium"] is False

    def test_jaljeera(self, api):
        r = api.get(f"{BASE_URL}/api/beverages/guide")
        entries = _flatten_entries(r.json(), "beverages")
        found = _find(entries, "Jaljeera")
        assert found is not None
        tier, e = found
        assert tier.upper() == "YELLOW"
        assert e["potassium_mg"] == 150
        assert e["sodium_mg"] == 600
        assert e["high_sodium"] is True

    def test_aam_panna(self, api):
        r = api.get(f"{BASE_URL}/api/beverages/guide")
        entries = _flatten_entries(r.json(), "beverages")
        found = _find(entries, "Aam Panna")
        assert found is not None
        tier, e = found
        assert tier.upper() == "YELLOW"
        assert e["potassium_mg"] == 150
        assert e["sodium_mg"] == 800
        assert e["high_sodium"] is True

    def test_thandai(self, api):
        r = api.get(f"{BASE_URL}/api/beverages/guide")
        entries = _flatten_entries(r.json(), "beverages")
        found = _find(entries, "Thandai")
        assert found is not None
        tier, e = found
        assert tier.upper() == "RED"
        assert e["potassium_mg"] == 425
        assert e["sodium_mg"] == 109
        assert e["high_sodium"] is False


# ---------- PROTEINS ----------
class TestProteinsGuide:
    def test_egg_yolk_alone(self, api):
        r = api.get(f"{BASE_URL}/api/proteins/guide")
        assert r.status_code == 200
        entries = _flatten_entries(r.json(), "proteins")
        # Must match "Egg Yolk" (alone) — not just Egg White or Whole Egg
        found = None
        for tier, e in entries:
            n = str(e.get("name", "")).lower()
            if "egg yolk" in n:
                found = (tier, e)
                break
        assert found is not None, "Egg Yolk (alone) must be added"
        tier, e = found
        assert tier.upper() == "RED"
        assert e["potassium_mg"] == 19
        assert e["sodium_mg"] == 8
        assert e["high_sodium"] is False
        assert abs(e["potassium_meq"] - 0.5) < 0.1


# ---------- GRAINS regression ----------
class TestGrainsGuide:
    def test_regression(self, api):
        r = api.get(f"{BASE_URL}/api/grains/guide")
        assert r.status_code == 200
        entries = _flatten_entries(r.json(), "grains")
        assert len(entries) > 0
        for _t, e in entries:
            assert "potassium_meq" in e
            assert "high_sodium" in e and isinstance(e["high_sodium"], bool)


# ---------- CSV file ----------
class TestNeedsSourcingCSV:
    CSV_PATH = Path("/app/backend/guide_needs_sourcing.csv")
    EXPECTED_FLAGGED = {"Vada Pav", "Misal Pav", "Sattu Sharbat", "Sol Kadhi", "Momos", "Bhel Puri", "Sev Puri"}

    def test_exists_and_header(self):
        assert self.CSV_PATH.exists()
        with self.CSV_PATH.open() as fh:
            reader = csv.reader(fh)
            header = next(reader)
        assert header == ["guide", "tier", "name", "hindi", "reason"]

    def test_flagged_rows_present(self):
        with self.CSV_PATH.open() as fh:
            reader = csv.DictReader(fh)
            flagged_names = {r["name"] for r in reader if r["guide"] == "flagged-not-added"}
        assert self.EXPECTED_FLAGGED.issubset(flagged_names), (
            f"missing: {self.EXPECTED_FLAGGED - flagged_names}"
        )

    def test_total_row_count(self):
        with self.CSV_PATH.open() as fh:
            rows = list(csv.DictReader(fh))
        # 7 flagged + ~140-150 sodium-null rows
        assert 140 <= len(rows) <= 200, f"unexpected row count: {len(rows)}"


# ---------- Regression: core APIs ----------
class TestRegression:
    def test_root(self, api):
        r = api.get(f"{BASE_URL}/api/")
        assert r.status_code == 200

    def test_foods_list(self, api):
        r = api.get(f"{BASE_URL}/api/foods")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, (list, dict))

    def test_food_toor_dal(self, api):
        r = api.get(f"{BASE_URL}/api/foods/food-toor-dal")
        assert r.status_code == 200
        body = r.json()
        # Endpoint returns {"food": {...}, "swap": ...} envelope
        food = body.get("food", body)
        assert food.get("id") == "food-toor-dal"

    def test_login_still_works(self, auth_headers):
        assert "Authorization" in auth_headers

    def test_nutrient_unit_roundtrip(self, api, auth_headers):
        # Get, then patch to mEq, then read back, restore to mg
        r = api.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert r.status_code == 200
        original = r.json().get("nutrient_unit", "mg")

        # PATCH to mEq
        r2 = api.patch(
            f"{BASE_URL}/api/auth/profile",
            json={"nutrient_unit": "mEq"},
            headers=auth_headers,
        )
        assert r2.status_code == 200, f"{r2.status_code} {r2.text}"

        r3 = api.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert r3.json().get("nutrient_unit") == "mEq"

        # Restore
        api.patch(
            f"{BASE_URL}/api/auth/profile",
            json={"nutrient_unit": original},
            headers=auth_headers,
        )

    def test_meals_crud(self, api, auth_headers):
        # Endpoint is /api/meal-logs (per server.py)
        from datetime import date as date_cls
        payload = {
            "food_id": "food-toor-dal",
            "date": date_cls.today().isoformat(),
            "meal_type": "breakfast",
        }
        r = api.post(f"{BASE_URL}/api/meal-logs", json=payload, headers=auth_headers)
        assert r.status_code in (200, 201), f"{r.status_code} {r.text}"
        meal = r.json()
        meal_id = meal.get("id")
        # List
        r2 = api.get(
            f"{BASE_URL}/api/meal-logs",
            params={"date": payload["date"]},
            headers=auth_headers,
        )
        assert r2.status_code == 200
        # Delete
        if meal_id:
            r3 = api.delete(f"{BASE_URL}/api/meal-logs/{meal_id}", headers=auth_headers)
            assert r3.status_code == 200
