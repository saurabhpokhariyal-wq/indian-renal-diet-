"""iter-30 backend tests — three follow-up fixes from iter-29 review.

Fix 1: Salt-substitute regex tightened (bare low/reduced-sodium removed;
       no-salt has negative lookahead for "added").
Fix 2: Tata Salt Lite tier_override RED (curated_overrides 7 -> 8).
Fix 3: Missing CONCENTRATED_BASE_IDS entries + Step 7b backstop
       (data_quality_flagged 39 -> 41).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, "/app/backend")

BASE_URL = os.environ.get(
    "EXPO_PUBLIC_BACKEND_URL",
    "https://safe-food-guide-1.preview.emergentagent.com",
).rstrip("/")
TIMEOUT = 20
AUDIT_SCRIPT = Path("/app/backend/scripts/audit_seed.py")

EMAIL = "demo@renal.app"
PASSWORD = "demo123"


# --------------------------- fixtures ---------------------------
@pytest.fixture(scope="module")
def auth_headers():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=TIMEOUT,
    )
    if r.status_code != 200:
        requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"email": EMAIL, "password": PASSWORD, "full_name": "Demo"},
            timeout=TIMEOUT,
        )
        r = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
            timeout=TIMEOUT,
        )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token") or r.json().get("token")
    return {"Authorization": f"Bearer {tok}"}


def _unwrap(j):
    if isinstance(j, dict) and "food" in j and isinstance(j["food"], dict):
        return j["food"]
    return j


def _get_food(food_id, headers=None):
    r = requests.get(f"{BASE_URL}/api/foods/{food_id}",
                     headers=headers or {}, timeout=TIMEOUT)
    assert r.status_code == 200, f"GET {food_id} -> {r.status_code}: {r.text[:200]}"
    return _unwrap(r.json())


# --------------------------- FIX 1: regex ---------------------------
class TestFix1SaltSubstituteRegex:
    """Tightened salt-substitute regex — new negatives + all 15 positives."""

    def test_new_negatives(self):
        from routes.scan import _looks_like_salt_substitute
        negatives = [
            "Low Sodium Bread",
            "Reduced Sodium Namkeen",
            "No Salt Added Canned Tomatoes",
            "No-salt-added chickpeas",
        ]
        false_positives = [t for t in negatives if _looks_like_salt_substitute(t)]
        assert not false_positives, f"Should NOT have matched (iter-30): {false_positives}"

    def test_all_15_positives_still_match(self):
        from routes.scan import _looks_like_salt_substitute
        positives = [
            "Potassium Chloride", "KCl", "Low Sodium Salt", "lite salt",
            "salt substitute", "salt alternative", "sendha namak",
            "rock salt", "Himalayan Pink Salt", "pink salt", "Lo-Salt",
            "NoSalt", "kala namak", "Black Salt", "Tata Salt Lite",
        ]
        missing = [t for t in positives if not _looks_like_salt_substitute(t)]
        assert not missing, f"Regressions — must still match: {missing}"

    def test_bare_no_salt_still_matches(self):
        """'no salt' without 'added' should still fire (covers 'NoSalt' the product)."""
        from routes.scan import _looks_like_salt_substitute
        assert _looks_like_salt_substitute("no salt") is True
        assert _looks_like_salt_substitute("NoSalt") is True


# --------------------------- FIX 2: Tata tier_override ---------------------------
class TestFix2TataSaltLiteTierOverride:
    """Tata Salt Lite is now RED via tier_override; K/Na values unchanged."""

    def test_curated_overrides_contains_key(self):
        from reconciliation import CURATED_TIER_OVERRIDES
        assert "food-tata-saltlite" in CURATED_TIER_OVERRIDES, (
            f"food-tata-saltlite missing from CURATED_TIER_OVERRIDES. "
            f"Keys: {list(CURATED_TIER_OVERRIDES.keys())}"
        )

    def test_tata_saltlite_endpoint(self, auth_headers):
        f = _get_food("food-tata-saltlite", auth_headers)
        assert f.get("safety_tier") == "RED", f"safety_tier={f.get('safety_tier')}"
        assert f.get("tier_override") is True, f"tier_override={f.get('tier_override')!r}"
        assert f.get("data_quality_flag") == "concentrated_base_pending_resourcing", (
            f"data_quality_flag={f.get('data_quality_flag')!r}"
        )
        assert "Avoid" in (f.get("portion_limit_text") or ""), (
            f"portion_limit_text={f.get('portion_limit_text')!r}"
        )
        assert f.get("primary_risk_factor") == "POTASSIUM", (
            f"primary_risk_factor={f.get('primary_risk_factor')!r}"
        )
        assert f.get("potassium_mg") == 184, f"K={f.get('potassium_mg')}"
        assert f.get("sodium_mg") == 256, f"Na={f.get('sodium_mg')}"


# --------------------------- FIX 3: CONCENTRATED_BASE_IDS + backstop ---------------------------
class TestFix3ConcentratedBaseIdsAndBackstop:
    """New IDs added + Step 7b backstop auto-flags stragglers."""

    def test_new_ids_in_set(self):
        from reconciliation import CONCENTRATED_BASE_IDS
        assert "food-curried-cauliflower-soup" in CONCENTRATED_BASE_IDS
        assert "food-classic-seasoned-black-beans" in CONCENTRATED_BASE_IDS

    def test_curried_cauliflower_soup_flagged(self, auth_headers):
        f = _get_food("food-curried-cauliflower-soup", auth_headers)
        assert f.get("data_quality_flag") == "concentrated_base_pending_resourcing", (
            f"data_quality_flag={f.get('data_quality_flag')!r}"
        )

    def test_classic_seasoned_black_beans_flagged(self, auth_headers):
        f = _get_food("food-classic-seasoned-black-beans", auth_headers)
        assert f.get("data_quality_flag") == "concentrated_base_pending_resourcing", (
            f"data_quality_flag={f.get('data_quality_flag')!r}"
        )

    def test_step_7b_backstop_via_reconcile_seed(self):
        """Feed a synthetic entry with K=5000 that would fail sanity_check()
        and has no tier_override; the backstop must auto-flag it."""
        from reconciliation import reconcile_seed
        synthetic = {
            "id": "food-iter30-backstop-test",
            "name": "Iter-30 Backstop Test Food",
            "category": "snack",
            "safety_tier": "RED",
            "primary_risk_factor": "POTASSIUM",
            "portion_g": 100,
            "potassium_mg": 5000,
            "phosphorus_mg": 50,
            "sodium_mg": 50,
            "protein_g": 5,
            "fluid_ml": 0,
            "portion_limit_text": "test",
            "actionable_clinical_tip": "test",
        }
        deduped, stats = reconcile_seed([synthetic], [])
        assert len(deduped) == 1
        entry = deduped[0]
        assert entry.get("data_quality_flag") == "concentrated_base_pending_resourcing", (
            f"backstop did not flag: {entry.get('data_quality_flag')!r}"
        )

    def test_step_7b_backstop_exempts_tier_override(self):
        """A tier_override entry that fails sanity_check must NOT be
        auto-flagged (the clinical-judgement lane is exempt)."""
        from reconciliation import reconcile_seed
        synthetic = {
            "id": "food-iter30-override-test",
            "name": "Iter-30 Override Exempt Test",
            "category": "snack",
            "safety_tier": "RED",
            "primary_risk_factor": "POTASSIUM",
            "portion_g": 100,
            "potassium_mg": 5000,
            "phosphorus_mg": 50,
            "sodium_mg": 50,
            "protein_g": 5,
            "fluid_ml": 0,
            "tier_override": True,
            "override_reason": "clinical test",
            "portion_limit_text": "test",
            "actionable_clinical_tip": "test",
        }
        deduped, _ = reconcile_seed([synthetic], [])
        entry = deduped[0]
        assert not entry.get("data_quality_flag"), (
            f"tier_override must be exempt from backstop; "
            f"got data_quality_flag={entry.get('data_quality_flag')!r}"
        )


# --------------------------- Audit script + counts ---------------------------
class TestAuditSeedJson:
    @pytest.fixture(scope="class")
    def audit_json(self):
        proc = subprocess.run(
            ["python", str(AUDIT_SCRIPT), "--json"],
            capture_output=True, text=True, timeout=60,
        )
        return proc

    def test_exit_zero(self, audit_json):
        assert audit_json.returncode == 0, (
            f"exit={audit_json.returncode} stderr={audit_json.stderr[:500]}"
        )

    def test_data_quality_flagged_41(self, audit_json):
        data = json.loads(audit_json.stdout)
        # iter-30 finalize: counter now recomputes from final deduped list, so
        # Tata Salt Lite's pre-set seed flag is included -> 41 becomes 42.
        assert data.get("data_quality_flagged") == 42, (
            f"data_quality_flagged={data.get('data_quality_flagged')} (expected 42)"
        )

    def test_sanity_violations_count_41(self, audit_json):
        data = json.loads(audit_json.stdout)
        assert data.get("sanity_violations_count") == 41, (
            f"sanity_violations_count={data.get('sanity_violations_count')} (expected 41)"
        )

    def test_curated_overrides_8_via_reconcile(self):
        """Curated_overrides bumped 7 -> 8 (Tata Salt Lite added)."""
        from reconciliation import reconcile_seed, CURATED_TIER_OVERRIDES
        # Build synthetic entries so reconcile_seed can count overrides
        synthetic = [{"id": fid, "name": fid, "category": "test",
                      "portion_g": 100, "potassium_mg": 0,
                      "phosphorus_mg": 0, "sodium_mg": 0}
                     for fid in CURATED_TIER_OVERRIDES.keys()]
        _, stats = reconcile_seed(synthetic, [])
        assert stats["curated_overrides"] == 8, (
            f"curated_overrides={stats['curated_overrides']} (expected 8)"
        )
        assert len(CURATED_TIER_OVERRIDES) == 8, (
            f"CURATED_TIER_OVERRIDES has {len(CURATED_TIER_OVERRIDES)} keys, expected 8"
        )


# --------------------------- Barcode regression (real OFF) ---------------------------
class TestBarcodeRegression:
    def test_lo_salt_barcode_still_warns(self, auth_headers):
        r = requests.post(
            f"{BASE_URL}/api/scan/barcode",
            json={"barcode": "5011544070034"},
            headers=auth_headers, timeout=30,
        )
        if r.status_code == 502:
            pytest.skip(f"OFF unavailable: {r.text}")
        assert r.status_code == 200, f"{r.status_code}: {r.text[:200]}"
        assert r.json().get("salt_substitute_warning") is True

    def test_nutella_barcode_no_warning(self, auth_headers):
        r = requests.post(
            f"{BASE_URL}/api/scan/barcode",
            json={"barcode": "3017620422003"},
            headers=auth_headers, timeout=30,
        )
        if r.status_code == 502:
            pytest.skip(f"OFF unavailable: {r.text}")
        assert r.status_code == 200, f"{r.status_code}: {r.text[:200]}"
        assert r.json().get("salt_substitute_warning") is False
