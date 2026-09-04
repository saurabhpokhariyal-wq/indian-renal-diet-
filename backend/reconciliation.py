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
    # Iter-31: mango is the classic Indian seasonal high-K fruit in
    # renal-diet counselling — even a small portion is aspirationally
    # YELLOW as a portion-vigilance signal, because patients rarely stop
    # at 80g cubes. Whole mango stays RED. Matches the fruit_guide.py
    # tier blocks so the guide screen and food detail don't disagree.
    "food-mango-small": "Aspirational YELLOW — 80g cube is formula-GREEN but mango is a canonical portion-vigilance case in Indian renal counselling.",
    "food-mango-whole": "Whole mango is a canonical high-K seasonal fruit in renal counselling — kept RED regardless of per-portion classifier.",
    # Iter-30: composition is explicitly unverified (data_quality_flag set),
    # portion_limit_text says "Avoid" — the tier text and the tier must
    # agree, so hold at RED until a real pack is photographed. The
    # formula's YELLOW at K=184 assumes we trust the estimate, which we
    # explicitly don't.
    "food-tata-saltlite": "Composition unverified (see data_quality_flag); portion_limit says 'Avoid' — hold RED until a physical pack's cation panel is sourced.",
}


# --------------------------- Data-quality flags ---------------------------
# These entries have RAW sodium/potassium values that appear to be per-100g of a
# concentrated base (dry stock, bouillon cube, dry seasoning) rather than a
# prepared serving. Their computed tier (RED) is a SAFE DEFAULT while awaiting a
# clinician / IFCT re-sourcing pass — this is NOT the same as CURATED_TIER_OVERRIDES,
# which is reserved for deliberate clinical judgement calls that disagree with
# the formula.
CONCENTRATED_BASE_IDS: set[str] = {
    # 30 soups whose ÷5 rescaled sodium still exceeds 1000mg — original source
    # was clearly per-100g of dry stock, not per-serving prepared soup.
    "food-spinach-soup", "food-cheese-soup", "food-meat-consomme",
    "food-consomme-au-vermicelli", "food-egg-drop-soup",
    "food-chicken-sweet-corn-soup", "food-mulligatawny-soup",
    "food-talaumein-soup", "food-green-pea-soup", "food-millet-soup",
    "food-french-onion-soup", "food-lentil-soup",
    "food-consomme-au-julienne", "food-cold-summer-garden-soup",
    "food-mixed-vegetable-soup", "food-chicken-consomme",
    "food-minestrone-soup", "food-cream-of-broccoli-soup",
    "food-cream-of-carrot-soup", "food-cream-of-potato-soup",
    "food-almond-soup", "food-cream-of-mixed-vegetable-soup",
    "food-spaghetti-bolognese", "food-cream-of-mushroom-soup",
    "food-clear-tomato-soup", "food-cream-of-green-peas-soup",
    "food-cream-of-tomato-soup", "food-cream-of-spinach-soup",
    "food-chinese-cabbage-and-meat-ball-soup", "food-instant-idli",
    # 2 solids whose raw values are also implausible without a soup framing —
    # likely dry-mix / dry-rub contamination.
    "food-instant-dhokla", "food-cajun-chicken",
    # 6 non-soup dishes surfaced by the tightened bucket-4 rule (previously
    # got the ÷5 rescale under the loose Na>3000 rule); their raw Na values
    # look like dry seasoning / restaurant-portion salt, not per-serving.
    "food-chicken-manchurian", "food-mutton-pulao", "food-chicken-pulao",
    "food-meat-and-macaroni-casserole", "food-savoury-puffs",
    "food-minced-meat-pancake",
    # 1 grain/porridge whose values look like dry pearl-millet flour, not
    # prepared porridge — awaiting real cooked-portion source.
    "food-pearl-millet-infant-food",
    # Iter-30: surfaced by audit_seed.py post-reconciliation as still
    # violating sanity_check() ceilings but not previously flagged.
    "food-curried-cauliflower-soup",   # 2193mg Na after /5 rescale
    "food-classic-seasoned-black-beans",  # 11984mg Na, never rescaled
    # (dal-like bean category isn't bucketed for the soup rescale rule)
}
DATA_QUALITY_FLAG_CONCENTRATED = "concentrated_base_pending_resourcing"



SPICE_MIX_PATTERNS = re.compile(
    r"\b(masala|powder|spice blend|chutney podi|garam|sambar|rasam powder|kashmiri)\b",
    re.IGNORECASE,
)

# End-anchored — only "X seeds baghar" / "X seed baghar" (a tempering-only dish)
# should be treated as a spice mix. Full curries like "Onion tomato baghar" or
# "Green gram whole with baghar" must NOT match.
BAGHAR_SPICE_PATTERN = re.compile(
    r"^\s*\w+\s+seeds?\s+baghar\s*$",
    re.IGNORECASE,
)

# Only proper soups, consommes, stocks, broths, and clear liquid rasams get the
# concentrated-base÷5 rescale — solid dishes with the same raw-Na pattern do not.
SOUP_NAME_PATTERN = re.compile(
    r"\b(soup|consomme|stock|shorba|broth)\b|\brasam\b(?!\s+powder)",
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
    ) or (BAGHAR_SPICE_PATTERN.match(name) and at_150):
        return "spice"

    # Bucket 3 — wet condiment
    if at_150 and category == "condiment":
        return "condiment"

    # Bucket 4 — soup / stock / consomme / broth / clear rasam.
    # Requires BOTH extreme sodium AND a soup/stock name pattern — a solid
    # dish that happens to carry very high stored sodium (e.g. minced-meat-pancake)
    # does NOT belong here because the "concentrate diluted into a small bowl"
    # framing that justifies ÷5 does not apply to solids.
    if at_150 and na > 3000 and SOUP_NAME_PATTERN.search(name):
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
    # Always regenerate portion_limit_text on rescale — the stored value
    # describes the OLD (pre-rescale) portion and would contradict the new
    # numbers otherwise. Hand-authored portion text is rare and lives in
    # curated entries which get tier_override (bucket=None, no rescale).
    out["portion_limit_text"] = spec["portion_limit_text"]

    # Regenerate disclaimer when there's none stored OR the stored one looks
    # auto-generated by a previous pipeline run under a different bucket.
    # `_STALE_DISCLAIMER_MARKERS` catches every bucket-default template in
    # both the current spec strings AND known older versions (e.g. beverage
    # entries pre-Iter-23 stored "count as FLUID intake … 150 ml here").
    # Genuinely hand-authored disclaimers (sajina, curated overrides) never
    # match these markers and are preserved.
    stored = out.get("serving_disclaimer") or ""
    if (
        bucket == "beverage"
        or not stored
        or any(marker in stored for marker in _STALE_DISCLAIMER_MARKERS)
    ):
        out["serving_disclaimer"] = spec["disclaimer"]
    out["auto_rescaled"] = True
    return out


# Substrings that identify an auto-generated bucket-default disclaimer from
# any prior pipeline run (current OR older). Missing/short entries fall
# through the empty-string check; hand-authored disclaimers must not include
# any of these phrases (they're phrased for machine-generated output).
_STALE_DISCLAIMER_MARKERS: tuple[str, ...] = (
    "Beverage — count as FLUID intake",       # pre-iter-23 beverage template
    "Beverage — counts as fluid",             # current beverage template
    "Values shown per 225 ml glass",          # current beverage tail
    "Spice mix — values shown per",           # current spice template
    "Values shown per realistic 15 g",        # current condiment template
    "Auto-rescaled from a concentrated base", # current soup template
    "Values shown per single piece, not a 150", # current sweet template
    "count as FLUID intake",                  # older shorter variant
)


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


def apply_data_quality_flags(foods: list[dict]) -> int:
    """In-place: set data_quality_flag on entries with untrustworthy raw values.

    Distinct from tier_override — these entries KEEP their formula-derived tier
    (typically RED, which is safe while their real values are being re-sourced).
    Returns the count of entries flagged.
    """
    count = 0
    for food in foods:
        if food.get("id") in CONCENTRATED_BASE_IDS:
            food["data_quality_flag"] = DATA_QUALITY_FLAG_CONCENTRATED
            count += 1
    return count


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
        "data_quality_flagged": 0,
    }

    all_foods = [dict(f) for f in curated] + [dict(f) for f in indb]
    stats["total_input"] = len(all_foods)

    # Step 4 (early): curated overrides — so classify_bucket() skips them.
    apply_curated_overrides(all_foods)
    stats["curated_overrides"] = sum(1 for f in all_foods if f.get("tier_override"))

    # Data-quality flag (independent of bucket assignment).
    stats["data_quality_flagged"] = apply_data_quality_flags(all_foods)

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

    # Step 2b — solids-cannot-be-fluids sanity pass. A non-beverage entry with
    # a stored fluid_ml > 0 is a data-model contradiction (a sandwich can't
    # count as 150 ml of drinking water). Strip the fluid_ml and — if the
    # stored disclaimer also looks like an auto-generated beverage template
    # from a previous run — replace it with a neutral solids-food default.
    # This catches the exact class of bug fixed by the iter-23 category
    # relabel where an entry no longer bucket-rescales but still carries
    # stale beverage-flavored metadata.
    _SOLID_FALLBACK_DISCLAIMER = "Values shown per stored portion."
    for food in processed:
        if (food.get("category") or "").lower() == "beverage":
            continue
        if float(food.get("fluid_ml") or 0) > 0:
            food["fluid_ml"] = 0
            disc = food.get("serving_disclaimer") or ""
            if any(marker in disc for marker in _STALE_DISCLAIMER_MARKERS):
                food["serving_disclaimer"] = _SOLID_FALLBACK_DISCLAIMER
                food["auto_rescaled"] = True
            stats.setdefault("solid_fluid_stripped", []).append(
                (food.get("id"), food.get("name"))
            )

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

    # Step 7b (iter-30): any entry that STILL fails a sanity ceiling after
    # reconciliation and isn't already tier_override'd gets the
    # concentrated-base-pending-resourcing flag automatically. This is a
    # backstop so future entries in odd categories (dal-like beans, etc.)
    # don't slip past CONCENTRATED_BASE_IDS unnoticed the way
    # food-classic-seasoned-black-beans did. tier_override entries are
    # exempt because that's the deliberate clinical-judgement lane.
    for food in deduped:
        if food.get("tier_override"):
            continue
        if food.get("data_quality_flag"):
            continue
        if sanity_check(food):
            food["data_quality_flag"] = DATA_QUALITY_FLAG_CONCENTRATED
            stats["data_quality_flagged"] += 1

    # Recompute data_quality_flagged as the FINAL count of every entry
    # in `deduped` carrying the flag (not just entries this reconciliation
    # step added the flag to). This matters when a seed entry declares
    # data_quality_flag directly (e.g. Tata Salt Lite, whose composition
    # is unverified independent of any sanity-ceiling breach) — that flag
    # is preserved through every step above but would otherwise never get
    # counted, causing the audit total to drift below the true Mongo count.
    stats["data_quality_flagged"] = sum(
        1 for f in deduped if f.get("data_quality_flag")
    )

    if logger:
        logger.info(
            "Reconciliation: input=%d, reclassified=%d, rescaled=%d, duplicates_dropped=%d, "
            "sanity_violations=%d, portion/disclaimer_conflicts=%d, curated_overrides=%d, "
            "data_quality_flagged=%d",
            stats["total_input"],
            len(stats["reclassified"]),
            len(stats["rescaled"]),
            len(stats["duplicates_dropped"]),
            len(stats["sanity_violations"]),
            len(stats["portion_disclaimer_conflicts"]),
            stats["curated_overrides"],
            stats["data_quality_flagged"],
        )
        for dup_id, dup_name, kept_id in stats["duplicates_dropped"]:
            logger.info("  duplicate dropped: %s '%s' (kept %s)", dup_id, dup_name, kept_id)

    return deduped, stats
