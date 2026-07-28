"""Iteration 13b retest — verify A11 fix (stale seed row purge) and no regressions.

Scope from review request:
  R1 — 9 dropped IDs must 404 from GET /api/foods/{id} AND be absent from GET /api/foods list.
  R2 — Patient-unsafe fixes still correct (RED tier / auto_rescaled).
  R3 — 8 kept "primary" duplicate IDs still return 200.
  R4 — GET /api/foods count >= 1018 AND POST /api/meal-logs food-lauki-sabzi works.
  R5 — Beverage disclaimers now use the bucket-default 225ml text.
"""
import os
from datetime import date

import pytest
import requests

BASE_URL = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
TIMEOUT = 30

DROPPED_IDS = [
    "food-cabbage-rolls-2",
    "food-white-sauce-2",
    "food-white-sauce-3",
    "food-caramel-custard-2",
    "food-shepherd-s-pie-2",
    "food-stuffed-bittergourd-2",
    "food-chicken-sandwich-2",
    "food-cheese-and-tomato-sandwich-2",
    "food-fruit-punch-2",
]

KEPT_PRIMARY_IDS = [
    "food-cabbage-rolls",
    "food-white-sauce",
    "food-caramel-custard",
    "food-shepherd-s-pie",
    "food-stuffed-bittergourd",
    "food-chicken-sandwich",
    "food-cheese-and-tomato-sandwich",
    "food-fruit-punch",
]


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def all_foods(api):
    r = api.get(f"{BASE_URL}/api/foods?limit=2000", timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(scope="module")
def token(api):
    r = api.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "demo@renal.app", "password": "demo123"},
        timeout=TIMEOUT,
    )
    if r.status_code != 200:
        api.post(
            f"{BASE_URL}/api/auth/register",
            json={"email": "demo@renal.app", "password": "demo123", "full_name": "Demo User"},
            timeout=TIMEOUT,
        )
        r = api.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "demo@renal.app", "password": "demo123"},
            timeout=TIMEOUT,
        )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _get_food(api, food_id, headers=None):
    r = api.get(f"{BASE_URL}/api/foods/{food_id}", headers=headers or {}, timeout=TIMEOUT)
    return r


def _unwrap(resp_json):
    if isinstance(resp_json, dict) and "food" in resp_json and isinstance(resp_json["food"], dict):
        return resp_json["food"]
    return resp_json


# ---------- R1: dropped IDs are 404 and absent from list ----------
class TestR1DroppedIds:
    @pytest.mark.parametrize("food_id", DROPPED_IDS)
    def test_dropped_id_returns_404(self, api, food_id):
        r = _get_food(api, food_id)
        assert r.status_code == 404, f"{food_id} returned {r.status_code}, expected 404"

    def test_dropped_ids_absent_from_list(self, all_foods):
        list_ids = {f["id"] for f in all_foods}
        overlap = set(DROPPED_IDS) & list_ids
        assert overlap == set(), f"Dropped IDs still in list: {overlap}"


# ---------- R2: patient-unsafe fixes ----------
class TestR2UnsafeFixes:
    def test_soya_chunks_red(self, api):
        f = _unwrap(_get_food(api, "food-soya-chunks-sweet-and-sour").json())
        assert f.get("safety_tier") == "RED", f"tier={f.get('safety_tier')}"

    def test_cold_tomato_soup_red(self, api):
        f = _unwrap(_get_food(api, "food-cold-tomato-soup").json())
        assert f.get("safety_tier") == "RED", f"tier={f.get('safety_tier')}"

    def test_mayonnaise_red(self, api):
        f = _unwrap(_get_food(api, "food-mayonnaise").json())
        assert f.get("safety_tier") == "RED", f"tier={f.get('safety_tier')}"

    def test_raw_mango_chutney_rescaled(self, api):
        f = _unwrap(_get_food(api, "food-raw-mango-chutney").json())
        assert f.get("auto_rescaled") is True, f"auto_rescaled={f.get('auto_rescaled')}"
        assert f.get("portion_g") == 15, f"portion_g={f.get('portion_g')}"


# ---------- R3: kept primary duplicate IDs still present ----------
class TestR3KeptPrimaryIds:
    @pytest.mark.parametrize("food_id", KEPT_PRIMARY_IDS)
    def test_primary_id_returns_200(self, api, food_id):
        r = _get_food(api, food_id)
        assert r.status_code == 200, f"{food_id} returned {r.status_code}"
        f = _unwrap(r.json())
        assert f.get("id") == food_id


# ---------- R4: regression sanity ----------
class TestR4Regression:
    def test_foods_count_at_least_1018(self, all_foods):
        assert len(all_foods) >= 1018, f"got {len(all_foods)} foods, expected >= 1018"

    def test_meal_log_lauki_sabzi_works(self, api, token):
        headers = {"Authorization": f"Bearer {token}"}
        today = date.today().isoformat()
        payload = {
            "food_id": "food-lauki-sabzi",
            "date": today,
            "meal_type": "lunch",
            "servings": 1.0,
        }
        r = api.post(
            f"{BASE_URL}/api/meal-logs", json=payload, headers=headers, timeout=TIMEOUT
        )
        assert r.status_code in (200, 201), r.text
        log_id = r.json().get("id")
        if log_id:
            api.delete(f"{BASE_URL}/api/meal-logs/{log_id}", headers=headers, timeout=TIMEOUT)


# ---------- R5: beverage disclaimer freshness ----------
class TestR5BeverageDisclaimer:
    EXPECTED_BUCKET_DEFAULT = "Beverage — counts as fluid. Values shown per 225 ml glass."

    def _sd(self, api, fid):
        f = _unwrap(_get_food(api, fid).json())
        return f, (f.get("serving_disclaimer") or "").strip()

    def test_rasam_with_lemon_disclaimer(self, api):
        f, sd = self._sd(api, "food-rasam-with-lemon")
        print(f"rasam serving_disclaimer={sd!r}, portion_g={f.get('portion_g')}, "
              f"portion_limit_text={f.get('portion_limit_text')!r}")
        assert "150 ml" not in sd and "150ml" not in sd, f"Stale 150ml text still present: {sd!r}"
        assert sd.endswith("225 ml glass.") or sd == self.EXPECTED_BUCKET_DEFAULT, (
            f"Unexpected disclaimer: {sd!r}"
        )

    def test_cold_coffee_disclaimer(self, api):
        f, sd = self._sd(api, "food-cold-coffee")
        print(f"cold-coffee serving_disclaimer={sd!r}, portion_g={f.get('portion_g')}, "
              f"portion_limit_text={f.get('portion_limit_text')!r}")
        assert "150 ml" not in sd and "150ml" not in sd, f"Stale 150ml text still present: {sd!r}"
        assert sd.endswith("225 ml glass.") or sd == self.EXPECTED_BUCKET_DEFAULT, (
            f"Unexpected disclaimer: {sd!r}"
        )
