"""Iter-37 data invariants (replace count assertions).

Pure-python — runs the same reconciliation the server runs at boot, no HTTP.
Each test is an invariant over the whole catalog, so a new bad entry fails
here no matter how many entries exist.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reconciliation import (  # noqa: E402
    DATA_QUALITY_FLAG_CONCENTRATED,
    DATA_QUALITY_FLAG_ESTIMATED,
    build_catalog,
    reconcile_seed,
)
from routes.scan import _looks_like_salt_substitute  # noqa: E402
from seed_data import SEED_FOODS  # noqa: E402
from seed_data_indb import SEED_FOODS_INDB  # noqa: E402
from seed_guide_staples import SEED_GUIDE_STAPLES  # noqa: E402

TIER_STEP = {"GREEN": 0, "YELLOW": 1, "RED": 2}
NUTRIENT_KEYS = ("potassium_mg", "phosphorus_mg", "sodium_mg", "protein_g", "portion_g")


def _norm(name: str) -> str:
    base = re.sub(r"\(.*?\)", "", (name or "").lower())
    return re.sub(r"\s+", " ", base).strip()


@pytest.fixture(scope="module")
def catalog():
    foods, stats = build_catalog()
    return foods, stats


# ---------- P0-1: hand-authored entries are never rescaled ----------
def test_every_staple_is_rescale_exempt():
    assert all(e.get("rescale_exempt") for e in SEED_GUIDE_STAPLES)


def test_rescale_exempt_values_equal_authored(catalog):
    foods, _ = catalog
    by_id = {f["id"]: f for f in foods}
    authored = [e for e in SEED_FOODS + SEED_FOODS_INDB + SEED_GUIDE_STAPLES if e.get("rescale_exempt")]
    assert authored
    drift = []
    for e in authored:
        final = by_id.get(e["id"])
        if final is None:
            continue  # dropped as a duplicate — covered by collision test
        for k in NUTRIENT_KEYS:
            if float(final.get(k) or 0) != float(e.get(k) or 0):
                drift.append((e["id"], k, e.get(k), final.get(k)))
        assert not final.get("auto_rescaled"), e["id"]
    assert not drift, drift


def test_beverage_staples_keep_own_portion(catalog):
    foods, _ = catalog
    by_id = {f["id"]: f for f in foods}
    beer = by_id["food-beer-alcohol"]
    assert beer["portion_g"] == 330 and beer["potassium_mg"] == 90
    chai = by_id["food-masala-chai-with-milk"]
    assert chai["portion_g"] == 100 and chai["potassium_mg"] == 130


# ---------- P0-2: no same-base-name pair two tier-steps apart ----------
def test_no_base_name_tier_conflict(catalog):
    foods, _ = catalog
    groups: dict[str, list[tuple[str, str]]] = {}
    for f in foods:
        tier = f.get("safety_tier")
        if tier in TIER_STEP:
            groups.setdefault(_norm(f.get("name")), []).append((f["id"], tier))
    conflicts = {
        name: rows for name, rows in groups.items()
        if len(rows) > 1
        and max(TIER_STEP[t] for _, t in rows) - min(TIER_STEP[t] for _, t in rows) > 1
    }
    assert not conflicts, conflicts


def test_papad_staple_duplicate_removed(catalog):
    foods, _ = catalog
    ids = {f["id"] for f in foods}
    assert "food-papad-fried-or-roasted" not in ids
    papad = next(f for f in foods if f["id"] == "food-papad")
    assert papad["safety_tier"] == "RED" and papad["sodium_mg"] >= 400


# ---------- P1-3: provenance ----------
def test_every_unsourced_staple_is_flagged(catalog):
    foods, _ = catalog
    by_id = {f["id"]: f for f in foods}
    for e in SEED_GUIDE_STAPLES:
        final = by_id[e["id"]]
        if e.get("source"):
            continue
        assert final.get("data_quality_flag") == DATA_QUALITY_FLAG_ESTIMATED, e["id"]


@pytest.mark.parametrize("fid", [
    "food-instant-noodles-maggi-etc", "food-bournvita-horlicks-boost",
    "food-potato-chips-lays-kurkure", "food-commercial-biscuits-marie-cream-cookies",
])
def test_named_commercial_products_flagged_or_labelled(catalog, fid):
    foods, _ = catalog
    f = next(x for x in foods if x["id"] == fid)
    assert f.get("source") or f.get("data_quality_flag"), fid


def test_corrected_staples_match_cited_values(catalog):
    foods, _ = catalog
    by_id = {f["id"]: f for f in foods}
    rice = by_id["food-boiled-white-rice"]
    assert rice["protein_g"] == 2.0 and rice["phosphorus_mg"] == 32 and rice.get("source")
    sago = by_id["food-sago-sabudana-boiled"]
    assert sago["protein_g"] <= 0.2 and sago["phosphorus_mg"] <= 5 and sago.get("source")
    tea = by_id["food-weak-black-tea-no-milk"]
    assert tea["protein_g"] == 0 and tea["phosphorus_mg"] <= 5 and tea.get("source")


def test_iter33_refined_entries_marked(catalog):
    foods, _ = catalog
    marked = [f for f in foods if f.get("source_note", "").startswith("iter-33")]
    assert len({f["id"] for f in marked}) == len(marked) and marked


def test_every_fruit_has_source_or_flag(catalog):
    foods, _ = catalog
    missing = [f["id"] for f in foods
               if f.get("category") == "fruit" and f["id"] in {e["id"] for e in SEED_FOODS}
               and not (f.get("source") or f.get("data_quality_flag"))]
    assert not missing, missing


def test_guava_matches_usda(catalog):
    foods, _ = catalog
    g = next(f for f in foods if f["id"] == "food-guava")
    assert g["potassium_mg"] == 417 and g["safety_tier"] == "RED"


def test_flag_values_are_known(catalog):
    foods, _ = catalog
    allowed = {None, DATA_QUALITY_FLAG_CONCENTRATED, DATA_QUALITY_FLAG_ESTIMATED}
    assert {f.get("data_quality_flag") for f in foods} <= allowed


def test_concentrated_flag_only_on_concentrates(catalog):
    """Step 7b must not label a non-rescaled entry a concentrated base."""
    from reconciliation import CONCENTRATED_BASE_IDS
    foods, _ = catalog
    wrong = [f["id"] for f in foods
             if f.get("data_quality_flag") == DATA_QUALITY_FLAG_CONCENTRATED
             and not f.get("auto_rescaled") and f["id"] not in CONCENTRATED_BASE_IDS
             and f["id"] != "food-tata-saltlite"]
    assert not wrong, wrong


def test_step7b_non_concentrate_gets_estimated_flag():
    synthetic = {"id": "food-x-synthetic", "name": "Synthetic noodle", "category": "snack",
                 "portion_g": 70, "potassium_mg": 100, "phosphorus_mg": 50,
                 "sodium_mg": 1500, "protein_g": 5, "safety_tier": "RED"}
    foods, _ = reconcile_seed([synthetic], [])
    assert foods[0]["data_quality_flag"] == DATA_QUALITY_FLAG_ESTIMATED


# ---------- P1-4: a sourced entry always wins a collision ----------
def test_no_staple_collides_with_sourced_entry():
    others = SEED_FOODS + SEED_FOODS_INDB
    other_ids = {e["id"] for e in others}
    other_names = {_norm(e["name"]) for e in others}
    clashes = [e["id"] for e in SEED_GUIDE_STAPLES
               if e["id"] in other_ids or _norm(e["name"]) in other_names]
    assert not clashes, clashes


def test_no_staple_collides_by_id_or_exact_name():
    others = SEED_FOODS + SEED_FOODS_INDB
    other_ids = {e["id"] for e in others}
    other_names = {(e["name"] or "").strip().lower() for e in others}
    clashes = [e["id"] for e in SEED_GUIDE_STAPLES
               if e["id"] in other_ids or (e["name"] or "").strip().lower() in other_names]
    assert not clashes, clashes


# ---------- Task 1: one load order for live boot and the audit ----------
@pytest.mark.parametrize("rel", ["lifespan.py", "scripts/audit_seed.py"])
def test_catalog_built_only_via_build_catalog(rel):
    src = (Path(__file__).resolve().parents[1] / rel).read_text()
    assert "build_catalog(" in src, f"{rel} must call reconciliation.build_catalog()"
    assert "reconcile_seed(" not in src, f"{rel} must not call reconcile_seed() directly"
    for name in ("SEED_FOODS_INDB", "SEED_GUIDE_STAPLES"):
        assert name not in src, f"{rel} must not assemble the catalog from {name} itself"


def test_sweet_lassi_is_the_sourced_indb_entry(catalog):
    foods, _ = catalog
    lassi = [f for f in foods if f["id"] == "food-sweet-lassi"]
    assert len(lassi) == 1
    indb = next(e for e in SEED_FOODS_INDB if e["id"] == "food-sweet-lassi")
    assert lassi[0]["actionable_clinical_tip"] == indb["actionable_clinical_tip"]
    assert "added sugar" in lassi[0]["actionable_clinical_tip"]


# ---------- Guide tier block must match the linked catalog tier ----------
def _guide_links():
    import beverage_guide, fruit_guide, grain_guide, oil_guide, protein_guide, snack_guide, vegetable_guide  # noqa: E401
    guides = [
        ("fruit", fruit_guide.FRUIT_GUIDE, "fruits"),
        ("vegetable", vegetable_guide.VEGETABLE_GUIDE, "vegetables"),
        ("snack", snack_guide.SNACK_GUIDE, "snacks"),
        ("beverage", beverage_guide.BEVERAGE_GUIDE, "beverages"),
        ("protein", protein_guide.PROTEIN_GUIDE, "proteins"),
        ("grain", grain_guide.GRAIN_GUIDE, "grains"),
        ("oil", oil_guide.OIL_GUIDE, "oils"),
    ]
    for gname, guide, key in guides:
        for tier, block in guide.items():
            if isinstance(block, dict) and key in block:
                for e in block[key]:
                    if e.get("linked_food_id"):
                        yield gname, tier, e["name"], e["linked_food_id"]


def test_guide_tier_matches_linked_catalog_tier(catalog):
    foods, _ = catalog
    by_id = {f["id"]: f for f in foods}
    mismatches = [
        (g, name, fid, tier, by_id[fid]["safety_tier"])
        for g, tier, name, fid in _guide_links()
        if fid in by_id and by_id[fid]["safety_tier"] != tier
    ]
    assert not mismatches, "\n".join(map(str, mismatches))


# ---------- P2: Sub-Salt regex ----------
@pytest.mark.parametrize("text", ["Sub-Salt", "SubSalt", "sub salt seasoning"])
def test_sub_salt_triggers_warning(text):
    assert _looks_like_salt_substitute(text)


def test_sub_salt_no_false_positive():
    assert not _looks_like_salt_substitute("Subway sandwich, salted butter")
