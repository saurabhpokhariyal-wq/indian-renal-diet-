"""Curated vegetable reference for CKD/dialysis patients.

Grouped by potassium content and preparation notes (leaching, boiling).
Every entry stores `potassium_mg` (source of truth); the API layer derives
`potassium_meq` (mg / 39.1) and `high_sodium` (sodium_mg >= 400) via
`guide_utils.enrich_guide` so the two units never drift apart. UI renders
both figures side-by-side (e.g. "162 mg / 4.1 mEq").

Sourcing convention: entries with a "source" field are directly measured from
IFCT 2017 (ICMR-NIN) at the code cited. Others are on legacy web data and are
candidates for the next IFCT backfill."""

VEGETABLE_GUIDE = {
    "GREEN": {
        "title": "Safe — daily portions",
        "subtitle": "Low potassium at a normal katori serving. Safe daily.",
        "vegetables": [
            {"name": "Bottle Gourd (Lauki)", "hindi": "Lauki / लौकी", "serving": "1 katori (150 g)", "potassium_mg": 130, "note": "The safest daily sabzi — very low potassium, gentle on the kidney. Keep the peel off; cook simply with jeera + minimal salt.", "linked_food_id": "food-lauki-sabzi"},
            {"name": "Round Gourd (Tinda)", "hindi": "Tinda / टिंडा", "serving": "1 katori (150 g)", "potassium_mg": 150, "note": "Another safe daily-driver sabzi. Excellent in stew-form with rice.", "linked_food_id": "food-tinda"},
            {"name": "Ridge Gourd (Turai)", "hindi": "Turai / तुरई", "serving": "1 katori (150 g)", "potassium_mg": 140, "note": "Low-K, high-fibre. Skin can be tough — peel before cooking.", "linked_food_id": "food-ridge-gourd-turai"},
            {"name": "Ash Gourd (Petha)", "hindi": "Petha / पेठा", "serving": "1 katori (150 g)", "potassium_mg": 120, "note": "Very kidney-friendly. The candy version (Agra petha) is sugar-heavy — avoid.", "linked_food_id": "food-ash-gourd-petha"},
            {"name": "Cabbage", "hindi": "Patta gobi / पत्ता गोभी", "serving": "1 katori cooked (100 g)", "potassium_mg": 170, "note": "Boiled cabbage is a classic 'reduced-K' vegetable used in renal diets worldwide.", "linked_food_id": "food-cabbage"},
            {"name": "Cauliflower", "hindi": "Phool gobi / फूल गोभी", "serving": "1 katori (100 g)", "potassium_mg": 150, "note": "Safe when boiled and drained. Skip the heavily-salted aloo-gobi versions.", "linked_food_id": "food-cauliflower"},
            {"name": "Cucumber", "hindi": "Kheera / खीरा", "serving": "½ medium (100 g)", "potassium_mg": 150, "note": "Great salad base. Avoid salted-cucumber preparations.", "linked_food_id": "food-cucumber"},
            {"name": "Green Beans (French/Cluster)", "hindi": "Beans / बीन्स", "serving": "1 katori (100 g)", "potassium_mg": 145, "note": "Steam or boil. Excellent daily side.", "linked_food_id": "food-green-beans-french-cluster"},
            {"name": "Bell Pepper (Capsicum)", "hindi": "Shimla mirch / शिमला मिर्च", "serving": "½ medium (75 g)", "potassium_mg": 130, "note": "Fine as a stir-fry vegetable. Roasted red capsicums concentrate K — small portions only.", "linked_food_id": "food-bell-pepper-capsicum"},
            {"name": "Onion (raw/cooked)", "hindi": "Pyaz / प्याज", "serving": "¼ cup (30 g)", "potassium_mg": 33, "note": "Small quantities as a cooking base are fine. Kept YELLOW in the seed DB as a portion-vigilance signal since it's used in nearly every dish.", "linked_food_id": "food-onion"},
        ],
    },
    "YELLOW": {
        "title": "Moderate — small katori only",
        "subtitle": "Use half-katori portions or apply leaching (soak-boil-drain).",
        "vegetables": [
            {"name": "Tomato (fresh)", "hindi": "Tamatar / टमाटर", "serving": "1 small (60 g)", "potassium_mg": 142, "note": "Fresh tomato per 60 g is low, but usage in curries + chutneys stacks up. Kept YELLOW as a curated portion-vigilance signal.", "linked_food_id": "food-tomato"},
            {"name": "Carrot", "hindi": "Gajar / गाजर", "serving": "½ medium (60 g)", "potassium_mg": 190, "note": "Small portions OK. Carrot halwa concentrates K + sugar heavily — treat as RED.", "linked_food_id": "food-carrot"},
            {"name": "Brinjal (Aubergine)", "hindi": "Baingan / बैंगन", "serving": "1 katori (100 g)", "potassium_mg": 230, "note": "Fine occasionally in a small portion. Baingan bharta uses more oil and salt.", "linked_food_id": "food-brinjal-aubergine"},
            {"name": "Green Peas", "hindi": "Matar / मटर", "serving": "¼ cup (40 g)", "potassium_mg": 240, "note": "Fresh green peas are moderate — small handful only. Dried peas are RED.", "linked_food_id": "food-green-peas"},
            {"name": "Okra (Bhindi)", "hindi": "Bhindi / भिंडी", "serving": "1 katori (100 g)", "potassium_mg": 300, "note": "Just above the safe cut-off — half-katori portions preferred.", "linked_food_id": "food-okra-bhindi"},
            {"name": "Kaddu (Pumpkin)", "hindi": "Kaddu / कद्दू", "serving": "1 katori (100 g)", "potassium_mg": 340, "note": "Contains vitamins but modest K. Half-katori for advanced CKD.", "linked_food_id": "food-kaddu-pumpkin"},
            {"name": "Beetroot (small portion)", "hindi": "Chukandar / चुकंदर", "serving": "¼ cup (40 g)", "potassium_mg": 130, "note": "Small pieces in a salad only. Beetroot juice is RED.", "linked_food_id": "food-beetroot-small-portion"},
            {"name": "Mushroom", "hindi": "Khumbi / खुम्बी", "serving": "½ katori (50 g)", "potassium_mg": 158, "note": "Small portions. Avoid canned mushrooms (heavy sodium).", "linked_food_id": "food-mushroom"},
            {
                "name": "Bitter Gourd (Karela)",
                "hindi": "Karela / करेला",
                "serving": "1 katori cooked (100 g)",
                "potassium_mg": 280,
                "sodium_mg": None,  # naturally low (~6–11 mg raw per USDA); recipe salt not sourced
                "note": "Moderate potassium naturally, and boiling further reduces it. Salt is added during prep in most recipes — go light. Naturally low sodium if unsalted.",
                "linked_food_id": "food-bitter-gourd-karela",
            },
            {
                "name": "Raw Banana (Kaccha Kela)",
                "hindi": "Kaccha kela / कच्चा केला",
                "serving": "1 katori sabzi (100 g)",
                "potassium_mg": 400,
                "sodium_mg": None,
                "note": "Similar potassium load to ripe banana — starchy but still K-dense. Half-katori portions preferred. Deep-fried banana chips concentrate this further — see Snacks.",
                "linked_food_id": "food-raw-banana-kaccha-kela",
            },
            {
                "name": "Radish (Mooli)",
                "hindi": "Mooli / मूली",
                "serving": "1 katori (100 g)",
                "potassium_mg": 287,
                "sodium_mg": 24,
                "note": "Often assumed 'light' because it's watery, but potassium is meaningfully higher than most gourds. Half-katori portions preferred, whether eaten raw as salad or cooked as mooli sabzi/paratha stuffing.",
                "linked_food_id": "food-radish-mooli",
                "source": "IFCT 2017, code F012",
            },
            {
                "name": "Water Chestnut (Singhada)",
                "hindi": "Singhada / सिंघाड़ा",
                "serving": "1 katori (100 g)",
                "potassium_mg": 382,
                "sodium_mg": 13,
                "note": "Common fasting-day (vrat) food, often overlooked in renal diet planning because it isn't a 'regular' vegetable. Moderate-high potassium — worth flagging specifically for patients who fast regularly.",
                "linked_food_id": "food-water-chestnut-singhada",
                "source": "IFCT 2017, code F016",
            },
        ],
    },
    "RED": {
        "title": "Avoid or minimal",
        "subtitle": "High potassium or renal caveat — use only tiny portions with leaching if at all.",
        "vegetables": [
            {"name": "Potato (regular)", "hindi": "Aloo / आलू", "serving": "1 medium (100 g)", "potassium_mg": 420, "note": "One of the highest-K everyday foods. Safer preparation: peel, cube, SOAK in water for 2+ hours, then boil in fresh water and drain — leaches ~50% of the potassium.", "linked_food_id": "food-aloo-sabzi"},
            {"name": "Sweet Potato", "hindi": "Shakarkandi / शकरकंदी", "serving": "½ medium (75 g)", "potassium_mg": 350, "note": "Even higher K than regular potato in some varieties. Small portions only, well-leached.", "linked_food_id": "food-sweet-potato"},
            {"name": "Yam (Suran)", "hindi": "Suran / सूरन", "serving": "½ katori (75 g)", "potassium_mg": 500, "note": "Very high K. Avoid or eat only in tiny portions after thorough boiling.", "linked_food_id": "food-yam-suran"},
            {"name": "Colocasia (Arbi)", "hindi": "Arbi / अरबी", "serving": "½ katori (75 g)", "potassium_mg": 450, "note": "High K. Also raises oxalate — kidney-stone risk. Skip in advanced CKD.", "linked_food_id": "food-colocasia-arbi"},
            {"name": "Spinach (Palak)", "hindi": "Palak / पालक", "serving": "¼ katori cooked (50 g)", "potassium_mg": 280, "note": "Cooked spinach concentrates K sharply. A few leaves in mixed dishes is fine, a full katori is not. Palak paneer is RED because of BOTH spinach AND dairy phosphorus.", "linked_food_id": "food-spinach-palak"},
            {"name": "Drumstick Leaves (Sajina)", "hindi": "Sajina saag / सजिना साग", "serving": "30–50 g cooked", "potassium_mg": 874, "note": "Extremely K-dense. Safe portion is 30–50 g cooked, NOT a full katori. Best avoided in advanced CKD.", "linked_food_id": "food-sajina"},
            {"name": "Amaranth Leaves (Chaulai)", "hindi": "Chaulai / चौलाई", "serving": "¼ katori (50 g)", "potassium_mg": 430, "note": "High K + oxalates. Occasional small portion only.", "linked_food_id": "food-amaranth-leaves-chaulai"},
            {"name": "Fenugreek Leaves (Methi)", "hindi": "Methi / मेथी", "serving": "¼ katori cooked (50 g)", "potassium_mg": 340, "note": "Bitter greens concentrate K. A few leaves in dal or paratha is fine; a full sabzi is not.", "linked_food_id": "food-fenugreek-leaves-methi"},
            {"name": "Mustard Leaves (Sarson)", "hindi": "Sarson / सरसों", "serving": "¼ katori cooked (50 g)", "potassium_mg": 380, "note": "Sarson-ka-saag is a K + phosphorus bomb — small tasting portion at most.", "linked_food_id": "food-mustard-leaves-sarson"},
            {"name": "Bamboo Shoots", "hindi": "Bans / बांस", "serving": "n/a", "potassium_mg": 500, "note": "High K and often preserved in brine (very high sodium). Avoid.", "linked_food_id": "food-bamboo-shoots"},
            {"name": "Avocado", "hindi": "Avocado", "serving": "½ small (50 g)", "potassium_mg": 240, "note": "Trendy 'superfood' but very K-dense per serving. Skip in advanced CKD.", "linked_food_id": "food-avocado"},
        ],
    },
}

from guide_utils import enrich_guide


def get_vegetable_guide() -> dict:
    return enrich_guide(VEGETABLE_GUIDE, "vegetables")
