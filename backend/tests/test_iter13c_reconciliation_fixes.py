"""Iteration 13c focused verification of the four follow-up reconciliation fixes.

Scope (from main-agent review request):
  T1  poached-egg sodium data correction (1745 -> 186; RED tier; not auto_rescaled)
  T2  minced-meat-pancake no longer soup-rescaled
  T3  spaghetti-bolognese no longer soup-rescaled; carries concentrated_base flag
  T4  Real soups (cheese-soup, meat-consomme, mulligatawny-soup) still auto_rescaled
  T5  Baghar precision — only "* seeds baghar" get 5g rescale
  T6  Mongo counts: concentrated_base_pending_resourcing == 32, tier_override == 7, no overlap
  T7  audit_seed.py --json produces expected fields
  T8  needs_manual_review.csv: 45 data rows + inclusion/exclusion invariants
  R1  Light regression from iteration_13/13b (patient-unsafe reds + dropped dupes)
"""

import csv
import json
import os
import subprocess
from pathlib import Path

import pytest
import requests

BASE_URL = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
TIMEOUT = 30
REVIEW_CSV = Path("/app/backend/needs_manual_review.csv")
AUDIT_SCRIPT = Path("/app/backend/scripts/audit_seed.py")


# ---------- fixtures ----------
@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _unwrap(resp_json):
    if isinstance(resp_json, dict) and "food" in resp_json and isinstance(resp_json["food"], dict):
        return resp_json["food"]
    return resp_json


def _get_food(api, food_id):
    r = api.get(f"{BASE_URL}/api/foods/{food_id}", timeout=TIMEOUT)
    assert r.status_code == 200, f"GET {food_id} -> {r.status_code}: {r.text[:200]}"
    return _unwrap(r.json())


# ---------- T1: poached-egg data correction ----------
class TestT1PoachedEgg:
    def test_sodium_corrected_to_186(self, api):
        f = _get_food(api, "food-poached-egg")
        assert f.get("sodium_mg") == 186, f"expected sodium_mg=186, got {f.get('sodium_mg')}"

    def test_tier_red_phosphorus(self, api):
        f = _get_food(api, "food-poached-egg")
        assert f.get("safety_tier") == "RED", f"expected RED, got {f.get('safety_tier')}"
        assert f.get("primary_risk_factor") == "PHOSPHORUS", (
            f"expected primary_risk_factor=PHOSPHORUS, got {f.get('primary_risk_factor')}"
        )

    def test_not_auto_rescaled(self, api):
        f = _get_food(api, "food-poached-egg")
        assert f.get("auto_rescaled") is not True, (
            f"poached-egg should not be auto_rescaled: {f.get('auto_rescaled')}"
        )


# ---------- T2: minced-meat-pancake solid dish must NOT get soup rescale ----------
class TestT2MincedMeatPancake:
    def test_not_auto_rescaled(self, api):
        f = _get_food(api, "food-minced-meat-pancake")
        assert f.get("auto_rescaled") is not True, (
            f"minced-meat-pancake should not be auto_rescaled: {f.get('auto_rescaled')}"
        )

    def test_portion_150g_raw_sodium(self, api):
        f = _get_food(api, "food-minced-meat-pancake")
        assert f.get("portion_g") == 150, f"portion_g={f.get('portion_g')}"
        assert f.get("sodium_mg") == 7413, f"sodium_mg={f.get('sodium_mg')} (expected raw 7413)"


# ---------- T3: spaghetti-bolognese solid dish, no soup rescale, concentrated_base flag ----------
class TestT3SpaghettiBolognese:
    def test_not_auto_rescaled(self, api):
        f = _get_food(api, "food-spaghetti-bolognese")
        assert f.get("auto_rescaled") is not True, (
            f"spaghetti-bolognese should not be auto_rescaled: {f.get('auto_rescaled')}"
        )

    def test_portion_150g(self, api):
        f = _get_food(api, "food-spaghetti-bolognese")
        assert f.get("portion_g") == 150, f"portion_g={f.get('portion_g')}"

    def test_concentrated_base_flag(self, api):
        f = _get_food(api, "food-spaghetti-bolognese")
        assert f.get("data_quality_flag") == "concentrated_base_pending_resourcing", (
            f"data_quality_flag={f.get('data_quality_flag')!r}"
        )


# ---------- T4: real soups regression (still auto_rescaled) ----------
class TestT4RealSoups:
    @pytest.mark.parametrize("food_id", [
        "food-cheese-soup",
        "food-meat-consomme",
        "food-mulligatawny-soup",
    ])
    def test_real_soup_still_rescaled(self, api, food_id):
        f = _get_food(api, food_id)
        assert f.get("auto_rescaled") is True, (
            f"{food_id} auto_rescaled={f.get('auto_rescaled')} (expected True)"
        )
        assert f.get("portion_g") == 30, (
            f"{food_id} portion_g={f.get('portion_g')} (expected 30)"
        )
        # data_quality_flag should be set to something (any non-null value ok)
        assert f.get("data_quality_flag"), (
            f"{food_id} data_quality_flag missing: {f.get('data_quality_flag')!r}"
        )


# ---------- T5: baghar precision ----------
class TestT5BagharPrecision:
    def test_mustard_seeds_baghar_rescaled(self, api):
        f = _get_food(api, "food-mustard-seeds-baghar")
        assert f.get("auto_rescaled") is True, f"auto_rescaled={f.get('auto_rescaled')}"
        assert f.get("portion_g") == 5, f"portion_g={f.get('portion_g')}"
        assert f.get("safety_tier") in {"GREEN", "YELLOW", "RED"}, (
            f"safety_tier missing: {f.get('safety_tier')!r}"
        )

    def test_cumin_seeds_baghar_rescaled(self, api):
        f = _get_food(api, "food-cumin-seeds-baghar")
        assert f.get("auto_rescaled") is True, f"auto_rescaled={f.get('auto_rescaled')}"
        assert f.get("portion_g") == 5, f"portion_g={f.get('portion_g')}"

    def test_onion_tomato_baghar_not_rescaled(self, api):
        f = _get_food(api, "food-onion-tomato-baghar")
        assert f.get("auto_rescaled") is not True, (
            f"onion-tomato-baghar auto_rescaled={f.get('auto_rescaled')} (should not be)"
        )
        assert f.get("portion_g") == 150, f"portion_g={f.get('portion_g')} (expected 150)"

    def test_green_gram_whole_with_baghar_not_rescaled(self, api):
        f = _get_food(api, "food-green-gram-whole-with-baghar")
        assert f.get("auto_rescaled") is not True, (
            f"green-gram-whole-with-baghar auto_rescaled={f.get('auto_rescaled')}"
        )
        assert f.get("portion_g") == 150, f"portion_g={f.get('portion_g')} (expected 150)"


# ---------- T6: Mongo field-count invariants ----------
class TestT6MongoInvariants:
    @pytest.fixture(scope="class")
    def mongo_counts(self):
        import asyncio
        from motor.motor_asyncio import AsyncIOMotorClient
        from dotenv import load_dotenv

        load_dotenv("/app/backend/.env")
        mongo_url = os.environ["MONGO_URL"]
        db_name = os.environ["DB_NAME"]

        async def _fetch():
            client = AsyncIOMotorClient(mongo_url)
            db = client[db_name]
            flagged = await db.foods.count_documents(
                {"data_quality_flag": "concentrated_base_pending_resourcing"}
            )
            overrides = await db.foods.count_documents({"tier_override": True})
            overlap = await db.foods.count_documents({
                "tier_override": True,
                "data_quality_flag": "concentrated_base_pending_resourcing",
            })
            client.close()
            return flagged, overrides, overlap

        return asyncio.get_event_loop().run_until_complete(_fetch())

    def test_concentrated_base_count_is_32(self, mongo_counts):
        flagged, _, _ = mongo_counts
        assert flagged == 32, f"concentrated_base_pending_resourcing count={flagged} (expected 32)"

    def test_tier_override_count_is_7(self, mongo_counts):
        _, overrides, _ = mongo_counts
        assert overrides == 7, f"tier_override count={overrides} (expected 7)"

    def test_sets_do_not_overlap(self, mongo_counts):
        _, _, overlap = mongo_counts
        assert overlap == 0, f"tier_override ∩ concentrated_base overlap={overlap} (expected 0)"


# ---------- T7: audit_seed.py --json ----------
class TestT7AuditScript:
    @pytest.fixture(scope="class")
    def audit_json(self):
        proc = subprocess.run(
            ["python", str(AUDIT_SCRIPT), "--json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert proc.returncode == 0, (
            f"audit_seed exit={proc.returncode}, stderr={proc.stderr[:400]}"
        )
        return json.loads(proc.stdout), proc.returncode

    def test_exit_zero_and_data_quality_flagged_32(self, audit_json):
        data, rc = audit_json
        assert rc == 0
        assert data.get("data_quality_flagged") == 32, (
            f"data_quality_flagged={data.get('data_quality_flagged')}"
        )

    def test_soup_bucket_around_29(self, audit_json):
        data, _ = audit_json
        buckets = data.get("rescaled_by_bucket") or {}
        soup = buckets.get("soup")
        assert soup is not None, f"soup bucket missing: {buckets}"
        # "around 29" — allow ±3 tolerance
        assert 26 <= soup <= 32, f"rescaled_by_bucket.soup={soup} (expected ~29)"

    def test_spice_bucket_around_35(self, audit_json):
        data, _ = audit_json
        buckets = data.get("rescaled_by_bucket") or {}
        spice = buckets.get("spice")
        assert spice is not None, f"spice bucket missing: {buckets}"
        # "about 35 total including the 2 new baghar entries"
        assert 33 <= spice <= 38, f"rescaled_by_bucket.spice={spice} (expected ~35)"

    def test_portion_disclaimer_conflicts_zero(self, audit_json):
        data, _ = audit_json
        assert data.get("portion_disclaimer_conflicts_count") == 0, (
            f"portion_disclaimer_conflicts_count="
            f"{data.get('portion_disclaimer_conflicts_count')}"
        )

    def test_curated_overrides_seven(self, audit_json):
        data, _ = audit_json
        assert data.get("curated_overrides") == 7, (
            f"curated_overrides={data.get('curated_overrides')}"
        )


# ---------- T8: needs_manual_review.csv ----------
class TestT8ManualReviewCSV:
    @pytest.fixture(scope="class")
    def rows(self):
        with REVIEW_CSV.open() as f:
            reader = csv.DictReader(f)
            return list(reader)

    @pytest.fixture(scope="class")
    def id_set(self, rows):
        return {r["id"] for r in rows}

    def test_row_count_around_45(self, rows):
        # "roughly 45 data rows" — allow ±3 tolerance
        assert 42 <= len(rows) <= 48, f"got {len(rows)} data rows, expected ~45"

    def test_poached_egg_not_in_csv(self, id_set):
        assert "food-poached-egg" not in id_set, "food-poached-egg should NOT be in review csv"

    @pytest.mark.parametrize("food_id", [
        "food-minced-meat-pancake",
        "food-spaghetti-bolognese",
        "food-cajun-chicken",
        "food-instant-idli",
        "food-instant-dhokla",
    ])
    def test_expected_id_in_csv(self, id_set, food_id):
        assert food_id in id_set, f"{food_id} missing from needs_manual_review.csv"


# ---------- R1: light regression from iteration_13/13b ----------
DROPPED_IDS = [
    "food-cabbage-rolls-2", "food-white-sauce-2", "food-white-sauce-3",
    "food-caramel-custard-2", "food-shepherd-s-pie-2", "food-stuffed-bittergourd-2",
    "food-chicken-sandwich-2", "food-cheese-and-tomato-sandwich-2", "food-fruit-punch-2",
]


class TestR1Regression:
    @pytest.mark.parametrize("food_id", DROPPED_IDS)
    def test_dropped_dupes_still_404(self, api, food_id):
        r = api.get(f"{BASE_URL}/api/foods/{food_id}", timeout=TIMEOUT)
        assert r.status_code == 404, f"{food_id} -> {r.status_code}"

    def test_soya_chunks_still_red(self, api):
        f = _get_food(api, "food-soya-chunks-sweet-and-sour")
        assert f.get("safety_tier") == "RED"

    def test_mayonnaise_still_red(self, api):
        f = _get_food(api, "food-mayonnaise")
        assert f.get("safety_tier") == "RED"
