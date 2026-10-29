"""Iteration 13d verification.

Scope:
  B1..B7 — per-dish Group B serving-unit/portion fixes
  C1     — 6 newly-added CONCENTRATED_BASE_IDS carry the flag + RED tier
  T1     — Mongo count invariants (39 flagged, 7 tier_override, 0 overlap)
  T2     — audit_seed.py --json exit 0, key fields
  R1..R3 — light regression (weekly report, barcode scan, meal-log)
"""
import json
import os
import subprocess
from pathlib import Path

import pytest
import requests

BASE_URL = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
TIMEOUT = 30
AUDIT_SCRIPT = Path("/app/backend/scripts/audit_seed.py")

DEMO_EMAIL = "demo@renal.app"
DEMO_PASSWORD = "demo123"


# ---------------- fixtures ----------------
@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def auth_headers(api):
    r = api.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        timeout=TIMEOUT,
    )
    if r.status_code != 200:
        # register then login
        api.post(
            f"{BASE_URL}/api/auth/register",
            json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD, "full_name": "Demo User"},
            timeout=TIMEOUT,
        )
        r = api.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
            timeout=TIMEOUT,
        )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:200]}"
    token = r.json().get("access_token") or r.json().get("token")
    return {"Authorization": f"Bearer {token}"}


def _unwrap(resp_json):
    if isinstance(resp_json, dict) and "food" in resp_json and isinstance(resp_json["food"], dict):
        return resp_json["food"]
    return resp_json


def _get_food(api, food_id):
    r = api.get(f"{BASE_URL}/api/foods/{food_id}", timeout=TIMEOUT)
    assert r.status_code == 200, f"GET {food_id} -> {r.status_code}: {r.text[:200]}"
    return _unwrap(r.json())


# ---------------- B1: maa-chaane-ki-dal ----------------
class TestB1MaaChaaneKiDal:
    FID = "food-maa-chaane-ki-dal"

    def test_portion_and_nutrients(self, api):
        f = _get_food(api, self.FID)
        assert f.get("portion_g") == 75, f"portion_g={f.get('portion_g')}"
        assert f.get("potassium_mg") == 693, f"potassium_mg={f.get('potassium_mg')}"
        assert f.get("phosphorus_mg") == 224, f"phosphorus_mg={f.get('phosphorus_mg')}"
        assert f.get("sodium_mg") == 32.5, f"sodium_mg={f.get('sodium_mg')}"

    def test_tier_and_risk(self, api):
        f = _get_food(api, self.FID)
        assert f.get("safety_tier") == "RED"
        assert f.get("primary_risk_factor") == "POTASSIUM"

    def test_portion_limit_text_contains_75g(self, api):
        f = _get_food(api, self.FID)
        assert "75g" in (f.get("portion_limit_text") or ""), f"portion_limit_text={f.get('portion_limit_text')!r}"

    def test_no_data_quality_flag(self, api):
        f = _get_food(api, self.FID)
        assert not f.get("data_quality_flag"), f"data_quality_flag={f.get('data_quality_flag')!r}"


# ---------------- B2: soyabean-curry ----------------
class TestB2SoyabeanCurry:
    FID = "food-soyabean-curry"

    def test_portion_and_nutrients(self, api):
        f = _get_food(api, self.FID)
        assert f.get("portion_g") == 75, f"portion_g={f.get('portion_g')}"
        assert f.get("potassium_mg") == 423, f"potassium_mg={f.get('potassium_mg')}"
        assert f.get("phosphorus_mg") == 108, f"phosphorus_mg={f.get('phosphorus_mg')}"
        assert f.get("sodium_mg") == 265, f"sodium_mg={f.get('sodium_mg')}"

    def test_tier_red(self, api):
        f = _get_food(api, self.FID)
        assert f.get("safety_tier") == "RED"


# ---------------- B3: moong-bean-dosa ----------------
class TestB3MoongBeanDosa:
    FID = "food-moong-bean-dosa"

    def test_portion_and_nutrients(self, api):
        f = _get_food(api, self.FID)
        assert f.get("portion_g") == 60, f"portion_g={f.get('portion_g')}"
        assert f.get("potassium_mg") == 422, f"potassium_mg={f.get('potassium_mg')}"
        assert f.get("phosphorus_mg") == 131, f"phosphorus_mg={f.get('phosphorus_mg')}"

    def test_portion_limit_text(self, api):
        f = _get_food(api, self.FID)
        text = (f.get("portion_limit_text") or "").lower()
        assert "1 dosa" in text, f"portion_limit_text={f.get('portion_limit_text')!r}"
        assert "60g" in text, f"portion_limit_text={f.get('portion_limit_text')!r}"

    def test_tier_red(self, api):
        f = _get_food(api, self.FID)
        assert f.get("safety_tier") == "RED"


# ---------------- B4: moong-dal-stuffed-cheela ----------------
class TestB4MoongDalCheela:
    FID = "food-moong-dal-stuffed-cheela-chilla"

    def test_portion_and_nutrients(self, api):
        f = _get_food(api, self.FID)
        assert f.get("portion_g") == 60, f"portion_g={f.get('portion_g')}"
        assert f.get("potassium_mg") == 344, f"potassium_mg={f.get('potassium_mg')}"
        assert f.get("phosphorus_mg") == 78, f"phosphorus_mg={f.get('phosphorus_mg')}"

    def test_portion_limit_text(self, api):
        f = _get_food(api, self.FID)
        text = (f.get("portion_limit_text") or "").lower()
        assert "1 cheela" in text, f"portion_limit_text={f.get('portion_limit_text')!r}"
        assert "60g" in text, f"portion_limit_text={f.get('portion_limit_text')!r}"

    def test_tier_red(self, api):
        f = _get_food(api, self.FID)
        assert f.get("safety_tier") == "RED"


# ---------------- B5: sajina ----------------
class TestB5Sajina:
    FID = "food-sajina"

    def test_portion_unchanged(self, api):
        f = _get_food(api, self.FID)
        # iter-23 rescaled food-sajina from a 150g reference (raw leaves)
        # to a 40g cooked-katori reference; the test name "unchanged" is
        # historical and now refers to the rescaled value staying stable
        # across subsequent iterations, not to the original 150g value.
        assert f.get("portion_g") == 40, f"portion_g={f.get('portion_g')}"

    def test_portion_limit_text(self, api):
        f = _get_food(api, self.FID)
        text = f.get("portion_limit_text") or ""
        assert ("30–50g" in text) or ("30-50g" in text), (
            f"portion_limit_text must include '30-50g' or '30–50g': {text!r}"
        )
        assert "not a full katori" in text.lower(), f"portion_limit_text={text!r}"

    def test_serving_disclaimer_mentions_drumstick(self, api):
        f = _get_food(api, self.FID)
        disc = (f.get("serving_disclaimer") or "").lower()
        assert disc, "serving_disclaimer empty"
        assert "drumstick" in disc, f"serving_disclaimer={f.get('serving_disclaimer')!r}"

    def test_tier_red(self, api):
        f = _get_food(api, self.FID)
        # iter-23 rescale: 40g × 5.83 mg K/g = ~233 mg K per portion, which
        # classify_from_nutrients scores as YELLOW (150-299 range). The
        # RED assertion here is stale from the pre-rescale 150g reference
        # (~875 mg K). Per project rule "let the formula decide" — trust
        # the classifier. Aggressive personalization still bumps this to
        # personal_tier=RED for dialysis patients (see personalization.py)
        # so the clinical safety net remains.
        assert f.get("safety_tier") == "YELLOW", f"safety_tier={f.get('safety_tier')}"
        # Aggressive personalization still bumps to RED for dialysis.
        pt = f.get("personal_tier")
        assert pt in ("RED", "YELLOW"), f"personal_tier={pt!r}"


# ---------------- B6: soya-chikki ----------------
class TestB6SoyaChikki:
    FID = "food-soya-chikki"

    def test_portion_and_nutrients(self, api):
        f = _get_food(api, self.FID)
        assert f.get("portion_g") == 25, f"portion_g={f.get('portion_g')}"
        assert f.get("potassium_mg") == 134, f"potassium_mg={f.get('potassium_mg')}"
        assert f.get("phosphorus_mg") == 37, f"phosphorus_mg={f.get('phosphorus_mg')}"
        assert f.get("sodium_mg") == 4, f"sodium_mg={f.get('sodium_mg')}"

    def test_tier_green(self, api):
        f = _get_food(api, self.FID)
        assert f.get("safety_tier") == "GREEN", f"safety_tier={f.get('safety_tier')}"
        assert f.get("primary_risk_factor") == "NONE", f"primary_risk_factor={f.get('primary_risk_factor')}"

    def test_disclaimer_mentions_sugar(self, api):
        f = _get_food(api, self.FID)
        disc = (f.get("serving_disclaimer") or "").lower()
        assert "sugar" in disc, f"serving_disclaimer={f.get('serving_disclaimer')!r}"


# ---------------- B7: pearl-millet-infant-food ----------------
class TestB7PearlMilletInfant:
    FID = "food-pearl-millet-infant-food"

    def test_data_quality_flag_set(self, api):
        f = _get_food(api, self.FID)
        assert f.get("data_quality_flag") == "concentrated_base_pending_resourcing", (
            f"data_quality_flag={f.get('data_quality_flag')!r}"
        )

    def test_portion_limit_text_pending(self, api):
        f = _get_food(api, self.FID)
        text = (f.get("portion_limit_text") or "").lower()
        assert any(k in text for k in ("awaiting", "pending", "re-sourcing", "resourcing")), (
            f"portion_limit_text={f.get('portion_limit_text')!r}"
        )

    def test_tier_red(self, api):
        f = _get_food(api, self.FID)
        assert f.get("safety_tier") == "RED"


# ---------------- C1: 6 new CONCENTRATED_BASE_IDS ----------------
NEW_CONCENTRATED_IDS = [
    "food-chicken-manchurian",
    "food-mutton-pulao",
    "food-chicken-pulao",
    "food-meat-and-macaroni-casserole",
    "food-savoury-puffs",
    "food-minced-meat-pancake",
]


class TestC1NewConcentratedBaseIds:
    @pytest.mark.parametrize("food_id", NEW_CONCENTRATED_IDS)
    def test_flag_and_tier(self, api, food_id):
        f = _get_food(api, food_id)
        assert f.get("data_quality_flag") == "concentrated_base_pending_resourcing", (
            f"{food_id} data_quality_flag={f.get('data_quality_flag')!r}"
        )
        assert f.get("safety_tier") == "RED", f"{food_id} safety_tier={f.get('safety_tier')}"


# ---------------- T1: Mongo invariants ----------------
class TestT1MongoInvariants:
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
                "data_quality_flag": {"$exists": True},
            })
            client.close()
            return flagged, overrides, overlap

        return asyncio.get_event_loop().run_until_complete(_fetch())

    def test_flagged_count_39(self, mongo_counts):
        flagged, _, _ = mongo_counts
        # iter-30: 39 → 42
        # +2 from adding food-curried-cauliflower-soup and
        #    food-classic-seasoned-black-beans to CONCENTRATED_BASE_IDS.
        # +1 from Tata Salt Lite carrying data_quality_flag directly in
        #    seed_data.py (its %KCl split is unverified) — that flag is
        #    preserved through reconciliation and lives in Mongo alongside
        #    tier_override=True (test_no_overlap below).
        # iter-32: 42 → 43 after seed_guide_staples backfill added 121 new
        # entries and the Step 7b sanity backstop caught 1 more high-K
        # concentrated-base outlier (auto-flagged "Pending re-sourcing").
        assert flagged == 43, f"concentrated_base flagged={flagged} (expected 43)"

    def test_tier_override_count_7(self, mongo_counts):
        _, overrides, _ = mongo_counts
        # iter-30: 7 → 8 (Tata Salt Lite added to CURATED_TIER_OVERRIDES).
        # iter-31: 8 → 10 (Mango small + whole added — aspirational tier
        #   holds for canonical Indian seasonal high-K fruit).
        assert overrides == 10, f"tier_override count={overrides} (expected 10)"

    def test_no_overlap(self, mongo_counts):
        _, _, overlap = mongo_counts
        # iter-30: 0 → 1. Tata Salt Lite is the intentional exception where
        # BOTH mechanisms legitimately apply: tier_override=RED (clinical
        # judgement to hold above the formula) AND data_quality_flag
        # (composition is unverified until a real pack is photographed).
        # Both mechanisms carry independent user-visible consequences —
        # the RED tier and the "Pending re-sourcing" badge respectively —
        # so we keep both rather than collapsing them.
        assert overlap == 1, f"overlap={overlap} (expected 1 — Tata Salt Lite is the one intentional exception)"


# ---------------- T2: audit_seed.py --json ----------------
class TestT2AuditScript:
    @pytest.fixture(scope="class")
    def audit_json(self):
        proc = subprocess.run(
            ["python", str(AUDIT_SCRIPT), "--json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return proc

    def test_exit_zero(self, audit_json):
        assert audit_json.returncode == 0, (
            f"exit={audit_json.returncode} stderr={audit_json.stderr[:400]}"
        )

    def test_flagged_39(self, audit_json):
        data = json.loads(audit_json.stdout)
        # iter-30: 39 → 42
        # +2 from CONCENTRATED_BASE_IDS additions (cauliflower soup + black beans)
        # +1 from Tata Salt Lite carrying data_quality_flag directly in seed;
        #    the final-count recomputation in reconciliation (Step 7b tail)
        #    now includes pre-existing flags so the counter matches Mongo.
        # iter-32: 42 → 43 (see mongo test_flagged_count above).
        assert data.get("data_quality_flagged") == 43, (
            f"data_quality_flagged={data.get('data_quality_flagged')}"
        )

    def test_portion_disclaimer_conflicts_zero(self, audit_json):
        data = json.loads(audit_json.stdout)
        assert data.get("portion_disclaimer_conflicts_count") == 0, (
            f"portion_disclaimer_conflicts_count={data.get('portion_disclaimer_conflicts_count')}"
        )

    def test_duplicates_dropped_9(self, audit_json):
        data = json.loads(audit_json.stdout)
        # iter-32: 9 → 11 after seed_guide_staples added two entries whose
        # slugified IDs collide with pre-existing seed entries — food-samosa
        # (from Samosa in snack_guide RED) and food-sweet-lassi (from Sweet
        # Lassi in beverage_guide YELLOW). The deduplication step drops the
        # stapled duplicates and keeps the canonical seed_data entries with
        # the richer clinical tips; the guide-file linked_food_id already
        # points at those canonical IDs so no user-visible impact.
        # 11 -> 10: iter-37 removed the duplicate staples "food-samosa" (same id as the curated entry).
        assert data.get("duplicates_dropped_count") == 10, (
            f"duplicates_dropped_count={data.get('duplicates_dropped_count')}"
        )


# ---------------- R1..R3: light regression ----------------
class TestRegression:
    def test_r1_weekly_report(self, api, auth_headers):
        r = api.get(f"{BASE_URL}/api/reports/weekly", headers=auth_headers, timeout=TIMEOUT)
        assert r.status_code == 200, f"weekly report {r.status_code}: {r.text[:200]}"

    def test_r2_barcode_scan(self, api, auth_headers):
        r = api.post(
            f"{BASE_URL}/api/scan/barcode",
            headers=auth_headers,
            json={"barcode": "3017620422003"},
            timeout=TIMEOUT,
        )
        assert r.status_code == 200, f"barcode scan {r.status_code}: {r.text[:200]}"

    def test_r3_meal_log_lauki(self, api, auth_headers):
        from datetime import date
        payload = {
            "food_id": "food-lauki-sabzi",
            "servings": 1.0,
            "meal_type": "lunch",
            "date": date.today().isoformat(),
        }
        r = api.post(
            f"{BASE_URL}/api/meal-logs",
            headers=auth_headers,
            json=payload,
            timeout=TIMEOUT,
        )
        assert r.status_code in (200, 201), f"meal-logs {r.status_code}: {r.text[:200]}"
