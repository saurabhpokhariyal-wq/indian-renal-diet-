"""Iteration 37 — offline pipeline-integrity tests (no HTTP, no Mongo, no env vars).

These assert INVARIANTS rather than counts, so a regression like the iter-32
beverage bug (28 new drinks silently x1.5'd, +28 in an audit counter nobody
asserted on) fails here instead of passing quietly.

Run:  cd backend && python -m pytest tests/test_iter37_staples_integrity.py -q
"""
import glob
import re
import sys
from collections import Counter
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from reconciliation import SUPERSEDED_IDS, classify_bucket, reconcile_seed  # noqa: E402
from seed_data import SEED_FOODS  # noqa: E402
from seed_data_indb import SEED_FOODS_INDB  # noqa: E402
from seed_guide_staples import SEED_GUIDE_STAPLES  # noqa: E402

# Staples entries that currently collide with a non-staples entry. This is a
# RATCHET: the set must match exactly, so fixing a collision forces its removal
# from this list, and a new collision fails the build. food-sweet-lassi is left
# in because resolving it changes a patient-visible tier (see review notes).
KNOWN_COLLISIONS = {"food-sweet-lassi"}

NUTRIENT_KEYS = ("portion_g", "potassium_mg", "phosphorus_mg", "sodium_mg", "protein_g")


@pytest.fixture(scope="module")
def pipeline():
    final, stats = reconcile_seed(SEED_FOODS + SEED_GUIDE_STAPLES, SEED_FOODS_INDB, logger=None)
    return final, stats, {f["id"]: f for f in final}


# ---------------- A. rescale_exempt invariants (the beverage regression) ----------------
def test_every_staple_is_rescale_exempt():
    missing = [f["id"] for f in SEED_GUIDE_STAPLES if not f.get("rescale_exempt")]
    assert not missing, f"staples missing rescale_exempt: {missing[:5]}"


def test_exempt_entries_are_never_bucketed():
    bucketed = [f["id"] for f in SEED_GUIDE_STAPLES if classify_bucket(f) is not None]
    assert not bucketed, f"rescale_exempt entries still bucketed: {bucketed[:5]}"


def test_staples_values_pass_through_reconciliation_unchanged(pipeline):
    _, _, by_id = pipeline
    diffs = [
        (f["id"], k, f[k], by_id[f["id"]][k])
        for f in SEED_GUIDE_STAPLES
        if f["id"] in by_id
        for k in NUTRIENT_KEYS
        if by_id[f["id"]][k] != f[k]
    ]
    assert not diffs, f"pipeline altered authored staple values: {diffs[:5]}"


def test_beverage_staples_keep_their_real_fluid_ml(pipeline):
    """fluid_ml feeds the fluid budget — must equal the authored serving, and be > 0."""
    _, _, by_id = pipeline
    for f in SEED_GUIDE_STAPLES:
        if f["category"] != "beverage":
            continue
        got = by_id[f["id"]]["fluid_ml"]
        assert got == f["fluid_ml"] and got > 0, f"{f['id']}: fluid_ml {got} (authored {f['fluid_ml']})"


def test_legacy_150g_beverages_are_still_rescaled(pipeline):
    """Guard against over-fixing: legacy placeholder beverages MUST still be rescaled.

    Selected via classify_bucket() rather than category, because a few legacy rows
    tagged category=beverage are (deliberately or not) claimed by an earlier bucket
    (e.g. mousse -> sweet; 'Kashmiri tea' -> spice, a separate pre-existing bug).
    Known staples/INDB id collisions are excluded (the staples copy wins there).
    """
    _, _, by_id = pipeline
    legacy = [
        f for f in SEED_FOODS_INDB
        if classify_bucket(f) == "beverage"
        and f["id"] in by_id
        and f["id"] not in KNOWN_COLLISIONS
    ]
    assert len(legacy) > 30, f"expected a sizeable legacy beverage set, got {len(legacy)}"
    wrong = [f["id"] for f in legacy if by_id[f["id"]]["portion_g"] != 225.0]
    assert not wrong, f"legacy beverages no longer rescaled to 225 ml: {wrong[:5]}"


def test_beverage_rescale_count_is_legacy_only(pipeline):
    _, stats, _ = pipeline
    # KNOWN_COLLISIONS excluded: the INDB twin shares the id and legitimately rescales.
    staple_ids = {f["id"] for f in SEED_GUIDE_STAPLES} - KNOWN_COLLISIONS
    leaked = [i for i, _b in stats["rescaled"] if i in staple_ids]
    assert not leaked, f"staples went through a rescale bucket: {leaked[:5]}"


# ---------------- B. duplicate / contradiction guards ----------------
def _norm(name):
    return (name or "").strip().lower()


def test_staples_collisions_match_the_known_list_exactly():
    others = SEED_FOODS + SEED_FOODS_INDB
    other_ids = {f["id"] for f in others}
    other_names = {_norm(f["name"]) for f in others}
    collided = {f["id"] for f in SEED_GUIDE_STAPLES if f["id"] in other_ids or _norm(f["name"]) in other_names}
    assert collided == KNOWN_COLLISIONS, (
        f"new collisions: {sorted(collided - KNOWN_COLLISIONS)}; "
        f"fixed (remove from KNOWN_COLLISIONS): {sorted(KNOWN_COLLISIONS - collided)}"
    )


def test_staples_ids_unique_within_file():
    dup = [i for i, n in Counter(f["id"] for f in SEED_GUIDE_STAPLES).items() if n > 1]
    assert not dup, dup


def test_papad_has_single_red_high_sodium_entry(pipeline):
    final, _, _ = pipeline
    papads = [f for f in final if re.search(r"\bpapad\b", f["name"], re.I)]
    assert [f["id"] for f in papads] == ["food-papad"], [f["id"] for f in papads]
    p = papads[0]
    assert p["safety_tier"] == "RED" and p["sodium_mg"] >= 400, (p["safety_tier"], p["sodium_mg"])


def test_sev_resolves_to_one_non_green_entry(pipeline):
    final, stats, by_id = pipeline
    sevs = [f for f in final if re.match(r"^sev\b", f["name"], re.I)]
    assert [f["id"] for f in sevs] == ["food-sev-ganthiya"], [f["id"] for f in sevs]
    assert sevs[0]["safety_tier"] != "GREEN"
    assert "food-sev" not in by_id
    assert "food-sev" in [i for i, _ in stats["superseded"]]


def test_superseded_ids_have_a_reason_and_exist_in_a_source():
    all_ids = {f["id"] for f in SEED_FOODS + SEED_GUIDE_STAPLES + SEED_FOODS_INDB}
    for sid, reason in SUPERSEDED_IDS.items():
        assert reason and len(reason) > 30, f"{sid} needs a documented reason"
        assert sid in all_ids, f"{sid} is superseded but no longer exists in any source (stale entry)"


def test_superseded_never_overlaps_tier_override_or_quality_flag(pipeline):
    """Three different concepts must never be conflated (standing principle #3)."""
    from reconciliation import CURATED_TIER_OVERRIDES, CONCENTRATED_BASE_IDS
    overlap = set(SUPERSEDED_IDS) & (set(CURATED_TIER_OVERRIDES) | CONCENTRATED_BASE_IDS)
    assert not overlap, overlap


# ---------------- C. guide links must resolve ----------------
def test_every_guide_linked_food_id_resolves(pipeline):
    _, _, by_id = pipeline
    broken = []
    total = 0
    for path in sorted(glob.glob(str(BACKEND / "*_guide.py"))):
        for m in re.finditer(r'"linked_food_id":\s*"([^"]+)"', Path(path).read_text()):
            total += 1
            if m.group(1) not in by_id:
                broken.append((Path(path).name, m.group(1)))
    assert total > 100, f"suspiciously few guide links found: {total}"
    assert not broken, f"guide links to missing catalog entries: {broken[:10]}"


# ---------------- D. audit trail ----------------
def test_superseded_sev_is_logged_for_real_sourcing():
    """guide_needs_sourcing.csv is regenerated on every boot, so manual rows must live in
    guide_utils._FLAGGED_UNSOURCED (editing the CSV by hand would be silently overwritten)."""
    from guide_utils import _FLAGGED_UNSOURCED
    assert any("Sev / Ganthiya" in r["name"] for r in _FLAGGED_UNSOURCED)
