"""One-off patcher for iter-23 data-quality fixes.

Two fixes to seed_data_indb.py:
1. food-sajina  — rescale K/P/Na/protein from 150 g stored to a 40 g reference
                  portion (mid-point of the 30-50 g cooked guidance). The reconciliation
                  pipeline's reclassify_tier() will recompute safety_tier from the new
                  numbers automatically at startup.
2. 26 entries mislabeled category="beverage" — 19 clearly-wrong (real dishes) and
                  7 judgment-call. Each gets a decisive category assignment recorded
                  in category_review.csv. The reconciliation pipeline then regenerates
                  disclaimer/portion_limit_text/fluid_ml from the corrected category
                  — we NEVER hand-edit those derived fields here.

Idempotent — safe to re-run. Prints a summary at the end.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

SEED = Path(__file__).resolve().parent.parent / "seed_data_indb.py"
REVIEW_CSV = Path(__file__).resolve().parent.parent / "category_review.csv"

# ---------- Sajina rescale ----------
SAJINA_TARGETS = {
    "portion_g": 40,
    "potassium_mg": 233,   # 874 * 40/150
    "phosphorus_mg": 100,  # 375 * 40/150
    "sodium_mg": 5,        # 18  * 40/150
    "protein_g": 4.3,      # 16.2 * 40/150
}

# ---------- Category decisions ----------
# Each row = (food_id, new_category, human-facing reason for the audit trail).
# The reconciliation pipeline (classify_bucket + rescale_food) will then take
# over: setting the right portion_g / portion_limit_text / serving_disclaimer /
# fluid_ml. We do NOT patch those fields here — that's the whole point.
CATEGORY_FIXES = [
    # 19 clearly-wrong solid dishes previously category="beverage"
    ("food-classic-club-sandwich",             "snack",     "Sandwich — solid meal, not a drink"),
    ("food-buttermilk-biscuit",                "snack",     "Biscuit — routes through the sweet bucket via name pattern"),
    ("food-coffee-biscuit",                    "snack",     "Biscuit — routes through the sweet bucket via name pattern"),
    ("food-kadhai-paneer",                     "dairy",     "Paneer curry — cheese-based main"),
    ("food-classic-seasoned-black-beans",      "dal",       "Legume dish — belongs in the dal/legume taxonomy"),
    ("food-milk-cake",                         "dairy",     "Milk-solids sweet — dairy triggers the sweet bucket via name"),
    ("food-orange-gateau",                     "snack",     "Cake — sweet bucket via SWEET_PATTERNS"),
    ("food-black-forest-gateau",               "snack",     "Cake — sweet bucket via SWEET_PATTERNS"),
    ("food-macaroni-salad",                    "snack",     "Pasta salad — cold side; snack fits best in current taxonomy"),
    ("food-vanilla-souffle",                   "snack",     "Souffle — SWEET_PATTERNS bucket"),
    ("food-vanilla-ice-cream-with-egg",        "dairy",     "Ice cream — dairy-based frozen sweet"),
    ("food-vanilla-ice-cream-without-egg",     "dairy",     "Ice cream — dairy-based frozen sweet"),
    ("food-lemon-souffle",                     "snack",     "Souffle — SWEET_PATTERNS bucket"),
    ("food-pineapple-souffle",                 "snack",     "Souffle — SWEET_PATTERNS bucket"),
    ("food-orange-souffle",                    "snack",     "Souffle — SWEET_PATTERNS bucket"),
    ("food-chocolate-souffle",                 "snack",     "Souffle — SWEET_PATTERNS bucket"),
    ("food-steamed-orange-pudding",            "snack",     "Pudding — SWEET_PATTERNS bucket"),
    ("food-milk-cookies",                      "snack",     "Cookie — SWEET_PATTERNS bucket"),
    ("food-steamed-cake-with-chocolate-sauce", "snack",     "Cake — SWEET_PATTERNS bucket"),

    # 7 judgment-call — explicit per-dish decision, recorded in the review CSV.
    ("food-mayonnaise-without-eggs",  "condiment",  "Mayo is a spread/dressing, not a drink — belongs in condiment bucket"),
    ("food-french-dressing",          "condiment",  "Salad dressing — condiment bucket"),
    ("food-curd-dressing",            "condiment",  "Yogurt-based dressing — condiment bucket"),
    ("food-coffee-drops",             "snack",      "Candy drop — solid confection, not a drink"),
    ("food-curried-cauliflower-soup", "snack",      "Soup — the reconciliation soup bucket (Na>3000 + name pattern) can catch it; snack keeps solids framing"),
    ("food-chicken-stock",            "beverage",   "KEEP as beverage — stock IS a liquid base sipped or drunk; app taxonomy has no dedicated stock category"),
    ("food-egg-nog",                  "beverage",   "KEEP as beverage — egg nog is drunk from a glass, ~200 ml is a realistic serving"),

    # Additional entries surfaced by the new audit_seed category-plausibility
    # check — same class of bug as the user's original 19, applied only to
    # unambiguous cases (dessert ice creams; vada mis-tagged as condiment).
    # Milkshake/shake-with-ice-cream hybrids are LEFT as beverage — they're
    # primarily liquid; a solids-first framing would misdirect fluid-restricted
    # patients. The audit still flags them for a human judgment call.
    ("food-choconut-ice-cream",       "dairy",      "Ice cream — dairy-based frozen sweet (matches vanilla-ice-cream category)"),
    ("food-peach-melba-ice-cream",    "dairy",      "Ice cream — dairy-based frozen sweet"),
    ("food-coffee-ice-cream",         "dairy",      "Ice cream — dairy-based frozen sweet"),
    ("food-fruit-ice-cream",          "dairy",      "Ice cream — dairy-based frozen sweet"),
    ("food-chocolate-ice-cream",      "dairy",      "Ice cream — dairy-based frozen sweet"),
    ("food-mango-ice-cream",          "dairy",      "Ice cream — dairy-based frozen sweet"),
    ("food-chocochip-ice-cream",      "dairy",      "Ice cream — dairy-based frozen sweet"),
    ("food-caramel-ice-cream",        "dairy",      "Ice cream — dairy-based frozen sweet"),
    ("food-strawberry-ice-cream",     "dairy",      "Ice cream — dairy-based frozen sweet"),
    ("food-masala-urad-dal-vada",     "snack",      "Vada is a fried lentil snack, NOT a condiment — audit-plausibility catch"),
]


def _patch_food_block(source: str, food_id: str, replacements: dict[str, object]) -> tuple[str, dict[str, object]]:
    """Rewrite the field values inside the dict entry for `food_id`.

    Returns (new_source, {field: old_value}) so callers can log what changed.
    """
    # Find the block bounded by the food's id.
    pattern = re.compile(
        r'(\{\s*"id":\s*"' + re.escape(food_id) + r'".*?\})',
        re.DOTALL,
    )
    match = pattern.search(source)
    if not match:
        return source, {}
    block = match.group(1)
    original = block
    diffs: dict[str, object] = {}
    for field, new_val in replacements.items():
        # Match either "field": <number> or "field": "<string>"
        if isinstance(new_val, (int, float)):
            fpat = re.compile(r'("' + re.escape(field) + r'":\s*)([\-\d.]+)')
            def _num_sub(m: re.Match, nv=new_val, fld=field) -> str:
                diffs[fld] = float(m.group(2))
                return f'{m.group(1)}{nv}'
            block = fpat.sub(_num_sub, block, count=1)
        else:
            fpat = re.compile(r'("' + re.escape(field) + r'":\s*)"([^"]*)"')
            def _str_sub(m: re.Match, nv=new_val, fld=field) -> str:
                diffs[fld] = m.group(2)
                return f'{m.group(1)}"{nv}"'
            block = fpat.sub(_str_sub, block, count=1)
    if block == original:
        return source, {}
    return source[: match.start(1)] + block + source[match.end(1) :], diffs


def main() -> int:
    src = SEED.read_text(encoding="utf-8")
    log_rows: list[dict[str, object]] = []

    # 1. Sajina rescale
    src, diffs = _patch_food_block(src, "food-sajina", SAJINA_TARGETS)
    if diffs:
        log_rows.append({
            "food_id": "food-sajina",
            "kind": "rescale",
            "before": str(diffs),
            "after": str(SAJINA_TARGETS),
            "reason": "portion_g 150→40 (mid-point of guidance 30-50g); K/P/Na/protein scaled by 40/150 ≈ 0.267",
        })
        print(f"food-sajina rescaled: {diffs} → {SAJINA_TARGETS}")
    else:
        print("food-sajina: already patched or not found — skipped")

    # 2. Category fixes (19 clearly-wrong + 7 judgment-call decisions)
    for food_id, new_cat, reason in CATEGORY_FIXES:
        src, diffs = _patch_food_block(src, food_id, {"category": new_cat})
        if diffs:
            log_rows.append({
                "food_id": food_id,
                "kind": "category-change",
                "before": diffs.get("category", "?"),
                "after": new_cat,
                "reason": reason,
            })
            print(f"{food_id:55s}  category: {diffs.get('category')!r} → {new_cat!r}")
        else:
            log_rows.append({
                "food_id": food_id,
                "kind": "category-unchanged",
                "before": new_cat,
                "after": new_cat,
                "reason": f"already {new_cat} — {reason}",
            })

    SEED.write_text(src, encoding="utf-8")
    with REVIEW_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["food_id", "kind", "before", "after", "reason"])
        writer.writeheader()
        writer.writerows(log_rows)
    print(f"\nWrote decision log: {REVIEW_CSV} ({len(log_rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
