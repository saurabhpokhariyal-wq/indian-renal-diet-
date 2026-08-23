"""Curated fats & oils reference for CKD/dialysis patients.

Cooking fats are the most under-appreciated category in Indian renal diets —
patients commonly avoid ghee (which is actually fine for kidneys, calories
aside) while liberally using salted butter and vanaspati (both high in
sodium/trans-fats). Pure fats are almost universally near-zero for potassium
and phosphorus, so the safety story here is dominated by SODIUM (salted vs
unsalted) and, for diabetics/heart patients, saturated-fat quantity.

Per-serving values are IFCT 2017 per-100g figures scaled to the stated
serving weight (typically 1 tsp = 5 g or 1 tbsp = 15 g).
"""
OIL_GUIDE = {
    "GREEN": {
        "title": "Safe — daily cooking fats",
        "subtitle": "Low in K/P/Na, use in moderate amounts.",
        "oils": [
            {
                "name": "Mustard Oil (sarson)",
                "hindi": "Sarson tel / सरसों का तेल",
                "serving": "1 tsp (5 ml)",
                "potassium_mg": 0,
                "phosphorus_mg": 0,
                "sodium_mg": 0,
                "note": "The default cooking oil across North & East India. Zero K/P/Na. Reheating repeatedly damages the fat profile — cook fresh.",
                "linked_food_id": None,
                "source": "IFCT 2017, code J001 (pure oil)",
            },
            {
                "name": "Groundnut Oil (moongfali)",
                "hindi": "Moongfali tel / मूंगफली तेल",
                "serving": "1 tsp (5 ml)",
                "potassium_mg": 0,
                "phosphorus_mg": 0,
                "sodium_mg": 0,
                "note": "Popular in Gujarat and South India. Zero K/P/Na. Good high-smoke-point option for tadka.",
                "linked_food_id": None,
                "source": "IFCT 2017, code J002 (pure oil)",
            },
            {
                "name": "Sunflower Oil",
                "hindi": "Suryamukhi tel / सूरजमुखी तेल",
                "serving": "1 tsp (5 ml)",
                "potassium_mg": 0,
                "phosphorus_mg": 0,
                "sodium_mg": 0,
                "note": "Refined sunflower is neutral for kidney safety. Prefer it fresh; avoid used deep-fry oil from restaurants.",
                "linked_food_id": None,
                "source": "IFCT 2017, code J004 (pure oil)",
            },
            {
                "name": "Rice Bran Oil",
                "hindi": "Chawal ka tel / चावल तेल",
                "serving": "1 tsp (5 ml)",
                "potassium_mg": 0,
                "phosphorus_mg": 0,
                "sodium_mg": 0,
                "note": "Neutral-taste high-smoke-point option. Same K/P/Na story as any pure vegetable oil.",
                "linked_food_id": None,
                "source": "IFCT 2017, code J005 (pure oil)",
            },
            {
                "name": "Desi Ghee (cow, small)",
                "hindi": "Desi ghee / देसी घी",
                "serving": "1 tsp (5 g)",
                "potassium_mg": 0,
                "phosphorus_mg": 0,
                "sodium_mg": 0,
                "note": "Traditional Indian clarified butter — near-zero for K/P/Na. Fine for CKD in small amounts (1 tsp on roti). Watch calorie load if overweight.",
                "linked_food_id": None,
                "source": "IFCT 2017, code L011 (cow ghee)",
            },
            {
                "name": "Unsalted Butter",
                "hindi": "Bina namak makhan / बिना नमक मक्खन",
                "serving": "1 tsp (5 g)",
                "potassium_mg": 1,
                "phosphorus_mg": 1,
                "sodium_mg": 1,
                "note": "The unsalted stick from the dairy aisle. Sodium is negligible when unsalted. Note: white butter (makhan) whipped fresh at home is also unsalted.",
                "linked_food_id": None,
                "source": "IFCT 2017, code L012 (unsalted butter)",
            },
        ],
    },
    "YELLOW": {
        "title": "Limit — use small amounts",
        "subtitle": "Fine occasionally, watch total intake.",
        "oils": [
            {
                "name": "Coconut Oil (unrefined)",
                "hindi": "Nariyal tel / नारियल तेल",
                "serving": "1 tsp (5 ml)",
                "potassium_mg": 0,
                "phosphorus_mg": 0,
                "sodium_mg": 0,
                "note": "Zero K/P/Na like any pure oil, BUT ~90% saturated fat. Fine for CKD safety; caution if you also have heart disease or high cholesterol.",
                "linked_food_id": None,
                "source": "IFCT 2017, code J003 (pure oil)",
            },
            {
                "name": "Olive Oil (extra virgin)",
                "hindi": "Zaitun tel / जैतून तेल",
                "serving": "1 tsp (5 ml)",
                "potassium_mg": 0,
                "phosphorus_mg": 0,
                "sodium_mg": 0,
                "note": "Kidney-neutral but not always suited to high-flame Indian tadka. Use raw for salads or low-flame dishes.",
                "linked_food_id": None,
                "source": "Kidney-neutral by composition (pure oil, negligible minerals)",
            },
            {
                "name": "Sesame Oil (til)",
                "hindi": "Til ka tel / तिल का तेल",
                "serving": "1 tsp (5 ml)",
                "potassium_mg": 0,
                "phosphorus_mg": 0,
                "sodium_mg": 0,
                "note": "Common in South Indian pickle bases and Tamil cooking. Kidney-neutral as a fat, but the pickles it goes into are very high in sodium — see Snacks.",
                "linked_food_id": None,
                "source": "IFCT 2017, code J006 (pure oil)",
            },
        ],
    },
    "RED": {
        "title": "Avoid — high sodium or trans-fat",
        "subtitle": "Add hidden sodium or damage kidneys long-term.",
        "oils": [
            {
                "name": "Salted Butter",
                "hindi": "Namkeen makhan / नमकीन मक्खन",
                "serving": "1 tsp (5 g)",
                "potassium_mg": 1,
                "phosphorus_mg": 1,
                "sodium_mg": 40,
                "note": "One innocent-looking teaspoon adds 40 mg sodium — a whole tablespoon on toast is 120 mg. Switch to unsalted or ghee. Amul salted butter is the most common culprit at home.",
                "linked_food_id": None,
                "source": "IFCT 2017, code L013 (salted butter, ~800 mg Na / 100 g)",
            },
            {
                "name": "Vanaspati / Dalda",
                "hindi": "Vanaspati / वनस्पति",
                "serving": "1 tsp (5 g)",
                "potassium_mg": 0,
                "phosphorus_mg": 0,
                "sodium_mg": 0,
                "note": "Hydrogenated vegetable fat — no K/Na issue but heavy in trans-fats which drive cardiovascular risk (the #1 killer in CKD). Switch to any liquid oil or ghee.",
                "linked_food_id": None,
                "source": "IFCT 2017, code J007 (hydrogenated fat)",
            },
            {
                "name": "Margarine (spread tubs)",
                "hindi": "Margarine",
                "serving": "1 tsp (5 g)",
                "potassium_mg": 2,
                "phosphorus_mg": 2,
                "sodium_mg": 35,
                "note": "Combines added salt with hydrogenated fats and phosphate stabilisers. The 'heart-healthy spread' label is misleading for CKD.",
                "linked_food_id": None,
                "source": "IFCT 2017, code L014",
            },
            {
                "name": "Restaurant Deep-Fry Oil (reused)",
                "hindi": "Bahar ka tala hua tel",
                "serving": "1 samosa (~10 g absorbed)",
                "potassium_mg": 3,
                "phosphorus_mg": 3,
                "sodium_mg": 5,
                "note": "Any pure oil is kidney-neutral fresh, but street-vendor reused oil accumulates oxidation products that inflame kidneys long-term. Skip the daily samosa/pakora habit.",
                "linked_food_id": None,
                "source": "Composition varies; sodium picked up from surrounding salted food",
            },
        ],
    },
}


from guide_utils import enrich_guide


def get_oil_guide() -> dict:
    return enrich_guide(OIL_GUIDE, "oils")
