"""Curated fruit reference for CKD/dialysis patients.

Common Indian and international fruits grouped by kidney-safety tier. Each row
maps to a realistic single serving (a "1 fruit" mental model, not per-100g),
with potassium/phosphorus/sodium data sourced from IFCT 2017 + USDA composites.

Every entry stores `potassium_mg` (source of truth); the API layer derives
`potassium_meq` (mg / 39.1) and `high_sodium` (sodium_mg >= 400) via
`guide_utils.enrich_guide` — the two units cannot drift apart. UI renders both
figures side-by-side (e.g. "162 mg / 4.1 mEq").

Sourcing convention: entries with a "source" field are directly measured from
IFCT 2017 (ICMR-NIN) at the code cited (per-100g figures scaled to the stated
serving weight — no other transformation). Others are still on legacy web
data and are candidates for the next IFCT backfill.

Guidance rules used to place each fruit:
  GREEN   — potassium under ~200 mg per stated serving; safe daily
  YELLOW  — potassium 200-350 mg per serving; safe if portion-controlled
  RED     — potassium above ~350 mg per serving OR carries a specific renal caveat
            (dried fruit, coconut water, high-oxalate, dialysis contraindication)

This is a patient-facing reference. `linked_food_id` is set when a corresponding
entry exists in db.foods so the UI can deep-link to full nutrient tables. When
unlinked, the fruit is intentionally information-only in the guide.
"""

FRUIT_GUIDE = {
    "GREEN": {
        "title": "Safe — daily portions",
        "subtitle": "Low in potassium per typical serving. Safe for most CKD stages.",
        "fruits": [
            {
                "name": "Apple",
                "hindi": "Seb / सेब",
                "serving": "1 medium (150 g)",
                "potassium_mg": 158,
                "note": "The all-round safest fruit. Keep the skin on for fibre; watch quantity if diabetic.",
                "linked_food_id": "food-apple",
            },
            {
                "name": "Pear",
                "hindi": "Nashpati / नाशपाती",
                "serving": "1 medium (170 g)",
                "potassium_mg": 200,
                "note": "Similar profile to apple. Slice fresh; avoid canned pears in heavy syrup.",
                "linked_food_id": "food-pear",
            },
            {
                "name": "Papaya",
                "hindi": "Papita / पपीता",
                "serving": "1 cup cubes (100 g)",
                "potassium_mg": 180,
                "note": "Excellent digestive-friendly choice. Stick to a small bowl, not half a papaya.",
                "linked_food_id": "food-papaya",
            },
            {
                "name": "Pineapple",
                "hindi": "Ananas / अनानास",
                "serving": "1 slice (~100 g)",
                "potassium_mg": 109,
                "note": "Naturally low in potassium. Prefer fresh over canned (which is high-sodium).",
                "linked_food_id": "food-pineapple",
            },
            {
                "name": "Watermelon",
                "hindi": "Tarbooz / तरबूज",
                "serving": "1 medium slice (150 g)",
                "potassium_mg": 170,
                "note": "Refreshing but counts toward daily FLUID limit — 100 g of watermelon = ~90 ml water.",
                "linked_food_id": "food-watermelon",
            },
            {
                "name": "Blueberries",
                "hindi": "Blueberry",
                "serving": "½ cup (75 g)",
                "potassium_mg": 57,
                "note": "One of the safest fruits, high in antioxidants. Fresh or frozen (unsweetened).",
                "linked_food_id": "food-blueberries",
            },
            {
                "name": "Strawberries",
                "hindi": "Strawberry",
                "serving": "½ cup halves (75 g)",
                "potassium_mg": 115,
                "note": "Safe and low-K. Rinse well and avoid canned versions with added sugar.",
                "linked_food_id": "food-strawberries",
            },
            {
                "name": "Cranberries",
                "hindi": "Cranberry",
                "serving": "¼ cup (30 g)",
                "potassium_mg": 25,
                "note": "Very low potassium. Also supports urinary-tract health. Choose unsweetened.",
                "linked_food_id": "food-cranberries",
            },
            {
                "name": "Grapes (small portion)",
                "hindi": "Angoor / अंगूर",
                "serving": "½ cup (75 g)",
                "potassium_mg": 145,
                "note": "Fine in a small handful. A full cup pushes into YELLOW territory.",
                "linked_food_id": "food-grapes",
            },
            {
                "name": "Lychee",
                "hindi": "Litchi / लीची",
                "serving": "5 pcs (75 g)",
                "potassium_mg": 130,
                "note": "Low-K when eaten in a modest portion. Skip if diabetic (very sweet).",
                "linked_food_id": "food-lychee",
            },
            {
                "name": "Fig, fresh (Anjeer)",
                "hindi": "Anjeer / अंजीर",
                "serving": "1 medium (50 g)",
                "potassium_mg": 116,
                "sodium_mg": 1,
                "note": "Fresh fig is moderate — this is distinct from dried anjeer, which concentrates potassium heavily (see dried fruit section) and is a very different risk profile at the same weight.",
                "linked_food_id": "food-fig-fresh",
                "source": "IFCT 2017, code E020 (scaled to 50 g)",
            },
        ],
    },
    "YELLOW": {
        "title": "Moderate — small portions only",
        "subtitle": "Potassium 200-350 mg per serving. Fine occasionally with portion control.",
        "fruits": [
            {
                "name": "Peach",
                "hindi": "Aadu / आड़ू",
                "serving": "1 medium (150 g)",
                "potassium_mg": 285,
                "note": "Safer than banana. Prefer fresh; avoid canned in heavy syrup.",
                "linked_food_id": "food-peach",
            },
            {
                "name": "Plum",
                "hindi": "Aloo bukhara / आलू बुखारा",
                "serving": "2 small (150 g)",
                "potassium_mg": 236,
                "note": "Fresh plum only — dried prunes are RED (very high K).",
                "linked_food_id": "food-plum",
            },
            {
                "name": "Mango (small portion)",
                "hindi": "Aam / आम",
                "serving": "½ cup cubes (80 g)",
                "potassium_mg": 135,
                "note": "Whole mangoes are RED. A very small portion is OK for the taste. Diabetic patients should skip.",
                "linked_food_id": "food-mango-small",
            },
            {
                "name": "Jackfruit (ripe)",
                "hindi": "Kathal / कटहल",
                "serving": "3-4 pods (75 g)",
                "potassium_mg": 225,
                "note": "Sweet ripe jackfruit — small portion only. Raw jackfruit sabzi is GREEN, ripe is YELLOW/RED.",
                "linked_food_id": "food-jackfruit-kathal",
            },
            {
                "name": "Pomegranate",
                "hindi": "Anaar / अनार",
                "serving": "½ cup arils (75 g)",
                "potassium_mg": 180,
                "note": "Whole seeds only. Pomegranate juice is much more concentrated — RED.",
                "linked_food_id": "food-pomegranate",
            },
            {
                "name": "Kiwi",
                "hindi": "Kiwi",
                "serving": "1 small (75 g)",
                "potassium_mg": 234,
                "note": "Vitamin-C rich. Stick to one small kiwi per day.",
                "linked_food_id": "food-kiwi",
            },
            {
                "name": "Muskmelon (Kharbuja)",
                "hindi": "Kharbuja / खरबूजा",
                "serving": "1 katori cubed (150 g)",
                "potassium_mg": 294,
                "sodium_mg": 24,
                "note": "IFCT-measured value, lower than watermelon per gram but still meaningful at a full katori. High water content also counts toward fluid intake for dialysis patients.",
                "linked_food_id": "food-muskmelon",
                "source": "IFCT 2017, code E046 (scaled to 150 g)",
            },
            {
                "name": "Ber (Indian Jujube / Zizyphus)",
                "hindi": "Ber / बेर",
                "serving": "5-6 small (100 g)",
                "potassium_mg": 237,
                "sodium_mg": 2,
                "note": "Common roadside/seasonal fruit, moderate potassium. Fine in small quantities, not a handful.",
                "linked_food_id": "food-ber",
                "source": "IFCT 2017, code E068",
            },
        ],
    },
    "RED": {
        "title": "Avoid or minimal — high potassium / renal caveat",
        "subtitle": "Above 350 mg K per serving, or carries a specific kidney-diet caution.",
        "fruits": [
            {
                "name": "Banana",
                "hindi": "Kela / केला",
                "serving": "1 medium (120 g)",
                "potassium_mg": 430,
                "note": "The classic high-K fruit. Skip entirely in advanced CKD and dialysis; a half-banana at most in early CKD.",
                "linked_food_id": None,
            },
            {
                "name": "Orange",
                "hindi": "Santra / संतरा",
                "serving": "1 medium (130 g)",
                "potassium_mg": 234,
                "note": "Kept RED by clinician override — citrus is a canonical high-K item and orange juice pushes K much higher.",
                "linked_food_id": "food-orange",
            },
            {
                "name": "Mango (whole)",
                "hindi": "Aam / आम",
                "serving": "1 medium (165 g)",
                "potassium_mg": 275,
                "note": "Whole mangoes push K + sugar too high. Have a small tasting portion only — see YELLOW list.",
                "linked_food_id": "food-mango-whole",
            },
            {
                "name": "Guava",
                "hindi": "Amrood / अमरूद",
                "serving": "1 small (100 g)",
                "potassium_mg": 417,
                "sodium_mg": 2,
                "note": "High in fibre and vitamin C, but one small guava carries a RED-level potassium load. Half a small fruit occasionally at most.",
                "linked_food_id": "food-guava",
                "source": "USDA FDC SR Legacy 'Guavas, common, raw' (per 100 g)",
            },
            {
                "name": "Cherry",
                "hindi": "Cherry",
                "serving": "1 cup (150 g)",
                "potassium_mg": 333,
                "sodium_mg": 0,
                "note": "A full cup of sweet cherries is RED-level potassium. Cherry juice concentrate is higher still — avoid.",
                "linked_food_id": "food-cherry",
                "source": "USDA FDC SR Legacy 'Cherries, sweet, raw' (scaled to 150 g)",
            },
            {
                "name": "Sapota / Chikoo",
                "hindi": "Chikoo / चीकू",
                "serving": "1 medium (100 g)",
                "potassium_mg": 193,
                "note": "K is borderline but sugar load is very high. Diabetic patients must avoid.",
                "linked_food_id": "food-chikoo",
            },
            {
                "name": "Custard Apple",
                "hindi": "Sitaphal / सीताफल",
                "serving": "½ cup (100 g)",
                "potassium_mg": 247,
                "note": "Very sugar-heavy despite modest K. Not recommended.",
                "linked_food_id": "food-custard-apple",
            },
            {
                "name": "Dates",
                "hindi": "Khajoor / खजूर",
                "serving": "5 pcs (40 g)",
                "potassium_mg": 278,
                "note": "Dried fruit — concentrated K + sugar. Avoid regularly. Fresh dates are slightly less severe.",
                "linked_food_id": "food-dates",
            },
            {
                "name": "Raisins",
                "hindi": "Kishmish / किशमिश",
                "serving": "¼ cup (40 g)",
                "potassium_mg": 300,
                "note": "All dried fruits (raisins, apricots, prunes, figs) concentrate potassium 4-5×. Avoid.",
                "linked_food_id": "food-raisins",
            },
            {
                "name": "Dried Apricots",
                "hindi": "Khubani / खुबानी",
                "serving": "5 pcs (40 g)",
                "potassium_mg": 460,
                "note": "Extremely high-K. Never in advanced CKD or dialysis.",
                "linked_food_id": "food-dried-apricots",
            },
            {
                "name": "Prunes",
                "hindi": "Aloo bukhara sukha / आलू बुखारा सूखा",
                "serving": "5 pcs (40 g)",
                "potassium_mg": 290,
                "note": "Dried plums. Also a laxative — some patients think this makes them 'healthy'. Avoid for kidney reasons.",
                "linked_food_id": "food-prunes",
            },
            {
                "name": "Coconut Water",
                "hindi": "Nariyal Paani / नारियल पानी",
                "serving": "1 glass (200 ml)",
                "potassium_mg": 500,
                "note": "Popularly thought of as 'natural and safe' — actually one of the most dangerous drinks for CKD. Avoid.",
                "linked_food_id": "food-coconut-water",
            },
            {
                "name": "Amla / Indian Gooseberry (raw)",
                "hindi": "Amla / आंवला",
                "serving": "1 whole (30 g)",
                "potassium_mg": 60,
                "note": "K is low, but raw amla is high in oxalates — can worsen kidney-stone risk. Cooked/preserved amla (murabba, achar) is heavily sugared or salted — also avoid.",
                "linked_food_id": "food-amla",
            },
            {
                "name": "Bael Fruit (Wood Apple)",
                "hindi": "Bael / बेल",
                "serving": "1 katori pulp (100 g)",
                "potassium_mg": 409,
                "sodium_mg": 2,
                "note": "Popular as a summer sherbet base in North India — the pulp itself is high-potassium. If made into a drink, treat as a RED beverage, not a minor garnish.",
                "linked_food_id": "food-bael",
                "source": "IFCT 2017, code E008",
            },
            {
                "name": "Phalsa",
                "hindi": "Phalsa / फालसा",
                "serving": "1 katori (100 g)",
                "potassium_mg": 362,
                "sodium_mg": 2,
                "note": "Regional North/West Indian summer berry, easy to overlook since it's seasonal and less discussed than mango or watermelon. High potassium per katori.",
                "linked_food_id": "food-phalsa",
                "source": "IFCT 2017, code E052",
            },
        ],
    },
}


from guide_utils import enrich_guide


def get_fruit_guide() -> dict:
    """Return the curated fruit guide grouped by tier (GREEN/YELLOW/RED)."""
    return enrich_guide(FRUIT_GUIDE, "fruits")
