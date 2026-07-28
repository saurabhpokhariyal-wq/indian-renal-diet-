"""Seed-time reconciliation for the food nutrition catalog.

Applied by server.py at startup (and re-runnable via scripts/audit_seed.py).
Reference files backend/seed_data.py and backend/seed_data_indb.py stay
untouched — this module produces the fully-reconciled entries that get
upserted into MongoDB.

Steps (order matters):
  1. Classify every entry into a scaling bucket using ORIGINAL values only.
  2. Rescale nutrients per bucket (÷30, ÷10, ÷5, ÷4.3, ×1.5).
  3. Reclassify safety_tier from possibly-rescaled numbers via
     _classify_from_nutrients (unless tier_override is set).
  4. Apply the 7 curated clinical overrides.
  5. Mark auto-rescaled entries with 'auto_rescaled': True.
  6. Deduplicate by lowercase name (first wins).
  7. Sanity ceiling pass — log solid-food entries over K>800 / P>400 / Na>1000
     into needs_manual_review.csv.
"""

from __future__ import annotations

import re
from typing import Iterable, Optional, Tuple


# ------------------------------ Classifier ------------------------------
def classify_from_nutrients(k_mg: float, p_mg: float, na_mg: float) -> Tuple[str, str]:
    """Canonical safety-tier classifier (same thresholds as server._classify_from_nutrients)."""
    reasons: list[Tuple[str, str, int]] = []
    if k_mg >= 300:
        reasons.append(("POTASSIUM", "RED", 3))
    elif k_mg >= 150:
        reasons.append(("POTASSIUM", "YELLOW", 2))
    if na_mg >= 400:
        reasons.append(("SODIUM", "RED", 3))
    elif na_mg >= 200:
        reasons.append(("SODIUM", "YELLOW", 2))
    if p_mg >= 150:
        reasons.append(("PHOSPHORUS", "RED", 3))
    elif p_mg >= 100:
        reasons.append(("PHOSPHORUS", "YELLOW", 2))
    if not reasons:
        return "GREEN", "NONE"
    reasons.sort(key=lambda r: r[2], reverse=True)
    return reasons[0][1], reasons[0][0]


# --------------------------- Curated overrides ---------------------------
# From the CSV audit + user sign-off. These 7 entries deliberately deviate
# from formula-derived tiers for clinical reasons.
CURATED_TIER_OVERRIDES: dict[str, str] = {
    "food-toor-dal": "Pulses concentrate potassium during cooking; keep YELLOW for pre-dialysis leaching-diet guidance.",
    "food-moong-dal": "Pulses concentrate potassium during cooking; keep YELLOW for pre-dialysis leaching-diet guidance.",
    "food-curd": "Dairy phosphorus burden is cumulative — YELLOW keeps daily-intake caution.",
    "food-tomato": "Fresh tomato per 60g is low, but usage across curries and chutneys drives cumulative potassium.",
    "food-onion": "Kept YELLOW as a portion-vigilance signal — cooked onion is used in nearly every Indian dish.",
    "food-brown-rice": "Whole grains carry higher phosphorus bioavailability than white rice — YELLOW keeps daily caution.",
    "food-orange": "Citrus fruit is a canonical high-K item in renal-diet counselling; kept RED regardless of raw potassium.",
}


# --------------------------- Bucket detection ---------------------------
SPICE_MIX_PATTERNS = re.compile(
    r"\b(masala|powder|spice blend|chutney podi|garam|sambar|rasam powder|kashmiri)\b",
    re.IGNORECASE,
)
SWEET_PATTERNS = re.compile(
    r"\b(ladoo|laddu|burfi|barfi|biscuit|cookie|halwa|kheer|rasgulla|jamun|jalebi|"
    r"pudding|custard|mousse|souffle|pastry|cake|swiss roll|chiffon|pie|gulab|"
    r"chocolate chip|shortbread|scone|muffin|danish)\b",
    re.IGNORECASE,
)


def classify_bucket(food: dict) -> Optional[str]:
    """Return exactly one bucket key or None. Uses ORIGINAL values (Step 1).

    Priority order matters — first match wins.
    """
    if food.get("tier_override"):
        return None
    category = (food.get("category") or "").lower().strip()
    name = food.get("name") or ""
    k = float(food.get("potassium_mg") or 0)
    p = float(food.get("phosphorus_mg") or 0)
    na = float(food.get("sodium_mg") or 0)
    portion = float(food.get("portion_g") or 0)
    at_150 = abs(portion - 150) < 0.5

    # Bucket 2 — spice mix / dry masala (most specific first)
    if (at_150 and category == "condiment" and (k > 1500 or na > 3000)) or (
        SPICE_MIX_PATTERNS.search(name) and at_150
    ):
        return "spice"

    # Bucket 3 — wet condiment
    if at_150 and category == "condiment":
        return "condiment"

    # Bucket 4 — soup / stock / consomme (extreme sodium)
    if at_150 and na > 3000:
        return "soup"

    # Bucket 5 — sweet / biscuit / confection
    existing_disc = (food.get("serving_disclaimer") or "").lower()
    disc_signals_piece = (
        "1 piece" in existing_disc
        or "one piece" in existing_disc
        or "not 150g" in existing_disc
        or "not 150 g" in existing_disc
    )
    if at_150 and (
        (category in {"snack", "dairy"} and (p > 300 or k > 400))
        or SWEET_PATTERNS.search(name)
        or (category in {"snack", "dairy"} and disc_signals_piece)
    ):
        return "sweet"

    # Bucket 6 — beverage
    if category == "beverage":
        return "beverage"

    return None


# --------------------------- Bucket rescale specs ---------------------------
BUCKET_SPEC: dict[str, dict] = {
    "spice": {
        "portion_g": 5.0,
        "factor": 5.0 / 150.0,
        "portion_limit_text": "½–1 tsp (5 g) per dish, not a standalone serving",
        "disclaimer": "Spice mix — values shown per 5 g (≈1 tsp) added to a dish, not eaten as a portion on its own.",
    },
    "condiment": {
        "portion_g": 15.0,
        "factor": 15.0 / 150.0,
        "portion_limit_text": "1–2 tbsp (15 g) per meal",
        "disclaimer": "Values shown per realistic 15 g serving (about 1 tbsp).",
    },
    "soup": {
        "portion_g": 30.0,
        "factor": 30.0 / 150.0,
        "portion_limit_text": "Small bowl only — source data needs manual re-verification",
        "disclaimer": "Auto-rescaled from a concentrated base; flagged for manual re-sourcing.",
    },
    "sweet": {
        "portion_g": 35.0,
        "factor": 35.0 / 150.0,
        "portion_limit_text": "1 piece (~35 g), occasional only",
        "disclaimer": "Values shown per single piece, not a 150 g portion.",
    },
    "beverage": {
        "portion_ml": 225.0,
        "factor": 225.0 / 150.0,
        "portion_limit_text": "1 glass (~225 ml) — counts toward daily fluid limit",
        "disclaimer": "Beverage — counts as fluid. Values shown per 225 ml glass.",
    },
}


def rescale_food(food: dict, bucket: str) -> dict:
    """Return a new dict with nutrients rescaled per bucket (Step 2)."""
    spec = BUCKET_SPEC[bucket]
    factor = spec["factor"]
    out = dict(food)
    for key in ("potassium_mg", "phosphorus_mg", "sodium_mg", "protein_g"):
        v = float(food.get(key) or 0)
        out[key] = round(v * factor, 1)
    if bucket == "beverage":
        out["portion_ml"] = spec["portion_ml"]
        # Keep portion_g numeric so existing code paths (e.g. FoodOut.portion_g) remain valid.
        out["portion_g"] = spec["portion_ml"]
        out["fluid_ml"] = spec["portion_ml"]
    else:
        out["portion_g"] = spec["portion_g"]
        out["fluid_ml"] = 0
    out["portion_limit_text"] = spec["portion_limit_text"]
    # For beverages, always use the bucket default (INDB entries reference the
    # stale 150 ml portion that we've now rescaled to 225 ml — keeping their
    # text would leave the disclaimer contradicting the new portion). For all
    # other buckets, preserve any hand-authored disclaimer if present.
    if bucket == "beverage" or not out.get("serving_disclaimer"):
        out["serving_disclaimer"] = spec["disclaimer"]
    out["auto_rescaled"] = True
    return out


# --------------------------- Reclassify tier ---------------------------
def reclassify_tier(food: dict) -> dict:
    if food.get("tier_override"):
        return food
    tier, risk = classify_from_nutrients(
        float(food.get("potassium_mg") or 0),
        float(food.get("phosphorus_mg") or 0),
        float(food.get("sodium_mg") or 0),
    )
    out = dict(food)
    out["safety_tier"] = tier
    out["primary_risk_factor"] = risk
    return out


# --------------------------- Sanity ceilings ---------------------------
SANITY_MAX = {"potassium_mg": 800.0, "phosphorus_mg": 400.0, "sodium_mg": 1000.0}


def sanity_check(food: dict) -> list[str]:
    """Return list of violated ceilings for solid foods with portion ≤150 g."""
    if (food.get("category") or "").lower() == "beverage":
        return []
    portion = float(food.get("portion_g") or 0)
    if portion <= 0 or portion > 150:
        return []
    violations = []
    for key, ceiling in SANITY_MAX.items():
        if float(food.get(key) or 0) > ceiling:
            violations.append(f"{key}={food.get(key)}>{ceiling:g}")
    return violations


# --------------------------- Curated override tag ---------------------------
def apply_curated_overrides(foods: list[dict]) -> None:
    """In-place: annotate the 7 curated entries with tier_override + reason."""
    for food in foods:
        reason = CURATED_TIER_OVERRIDES.get(food.get("id"))
        if reason:
            food["tier_override"] = True
            food["override_reason"] = reason


# --------------------------- Portion-limit vs disclaimer sanity ---------------------------
def portion_disclaimer_conflict(food: dict) -> bool:
    """Return True if portion_limit_text says '150 g' but serving_disclaimer disagrees."""
    text = (food.get("portion_limit_text") or "").lower()
    disc = (food.get("serving_disclaimer") or "").lower()
    if not disc:
        return False
    if "150" in text and any(k in disc for k in ("5 g", "5g", "15 g", "15g", "35 g", "35g", "225 ml", "1 glass", "one glass", "1 piece", "one piece")):
        return True
    return False


# --------------------------- Main pipeline ---------------------------
def reconcile_seed(
    curated: Iterable[dict],
    indb: Iterable[dict],
    logger=None,
) -> Tuple[list[dict], dict]:
    """Run steps 1-7 and return (reconciled_food_list, stats).

    curated is placed FIRST so it wins any name-collision dedupe against INDB.
    """
    stats: dict = {
        "total_input": 0,
        "reclassified": [],
        "rescaled": [],
        "duplicates_dropped": [],
        "sanity_violations": [],
        "portion_disclaimer_conflicts": [],
        "curated_overrides": 0,
    }

    all_foods = [dict(f) for f in curated] + [dict(f) for f in indb]
    stats["total_input"] = len(all_foods)

    # Step 4 (early): curated overrides — so classify_bucket() skips them.
    apply_curated_overrides(all_foods)
    stats["curated_overrides"] = sum(1 for f in all_foods if f.get("tier_override"))

    # Step 1: bucket assignment using ORIGINAL values.
    buckets: list[Optional[str]] = [classify_bucket(f) for f in all_foods]

    # Step 2 + Step 5 (auto_rescaled tag inside rescale_food).
    processed: list[dict] = []
    for food, bucket in zip(all_foods, buckets):
        if bucket:
            processed.append(rescale_food(food, bucket))
            stats["rescaled"].append((food.get("id"), bucket))
        else:
            processed.append(food)

    # Step 3: reclassify tiers.
    final: list[dict] = []
    for food in processed:
        old_tier = food.get("safety_tier")
        reclassed = reclassify_tier(food)
        if not food.get("tier_override") and reclassed.get("safety_tier") != old_tier:
            stats["reclassified"].append(
                (food.get("id"), old_tier, reclassed.get("safety_tier"))
            )
        final.append(reclassed)

    # Step 6: dedupe by lowercase name (first wins).
    seen: dict[str, str] = {}
    deduped: list[dict] = []
    for food in final:
        key = (food.get("name") or "").strip().lower()
        if not key:
            deduped.append(food)
            continue
        if key in seen:
            stats["duplicates_dropped"].append(
                (food.get("id"), food.get("name"), seen[key])
            )
            continue
        seen[key] = food.get("id") or "?"
        deduped.append(food)

    # Step 7: sanity ceiling flag.
    for food in deduped:
        violations = sanity_check(food)
        if violations:
            stats["sanity_violations"].append(
                (food.get("id"), food.get("name"), violations)
            )
        if portion_disclaimer_conflict(food):
            stats["portion_disclaimer_conflicts"].append(
                (food.get("id"), food.get("name"))
            )

    if logger:
        logger.info(
            "Reconciliation: input=%d, reclassified=%d, rescaled=%d, duplicates_dropped=%d, "
            "sanity_violations=%d, portion/disclaimer_conflicts=%d, curated_overrides=%d",
            stats["total_input"],
            len(stats["reclassified"]),
            len(stats["rescaled"]),
            len(stats["duplicates_dropped"]),
            len(stats["sanity_violations"]),
            len(stats["portion_disclaimer_conflicts"]),
            stats["curated_overrides"],
        )
        for dup_id, dup_name, kept_id in stats["duplicates_dropped"]:
            logger.info("  duplicate dropped: %s '%s' (kept %s)", dup_id, dup_name, kept_id)

    return deduped, stats
