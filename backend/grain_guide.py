"""Curated grains & rotis reference for CKD/dialysis patients.

Every entry stores `potassium_mg` (source of truth); the API layer derives
`potassium_meq` (mg / 39.1) and `high_sodium` (sodium_mg >= 400) via
`guide_utils.enrich_guide` so the two units cannot drift apart. UI renders both
figures side-by-side (e.g. "162 mg / 4.1 mEq")."""
GRAIN_GUIDE = {
    "GREEN": {"title": "Safe — daily portions", "subtitle": "Refined grains are usually kinder to kidneys than whole grains here.",
        "grains": [
            {"name": "Boiled White Rice", "hindi": "Chawal / चावल", "serving": "1 katori (75 g cooked)", "potassium_mg": 35, "note": "Refined white rice is one of the safest daily grains for CKD. Basmati is fine.", "linked_food_id": None},
            {"name": "Semolina (Suji/Rava)", "hindi": "Suji / सूजी", "serving": "½ katori (50 g)", "potassium_mg": 90, "note": "Base for upma, halwa (unsweetened), idli. Low in K and phosphorus.", "linked_food_id": None},
            {"name": "Refined Wheat Flour (Maida) Roti", "hindi": "Maida roti / मैदा", "serving": "1 roti (30 g)", "potassium_mg": 50, "note": "Lower phosphorus than atta. Not a fibre-champion but safer for kidneys.", "linked_food_id": None},
            {"name": "White Bread (plain)", "hindi": "White bread", "serving": "1 slice (30 g)", "potassium_mg": 35, "note": "Occasional slice OK — avoid multigrain / whole-wheat bread which are higher phosphorus.", "linked_food_id": None},
            {"name": "Vermicelli (Sevaiyan, plain)", "hindi": "Sevaiyan / सेवइयां", "serving": "½ katori (50 g)", "potassium_mg": 40, "note": "Great base for a low-K evening meal.", "linked_food_id": None},
            {"name": "Sago (Sabudana, boiled)", "hindi": "Sabudana / साबूदाना", "serving": "½ katori (75 g)", "potassium_mg": 30, "note": "Very low K and phosphorus. Watch the peanuts + salt in most sabudana recipes.", "linked_food_id": None},
        ]},
    "YELLOW": {"title": "Limit — small roti portions", "subtitle": "Whole-grain rotis carry more phosphorus and modest K.",
        "grains": [
            {"name": "Whole Wheat Atta Roti", "hindi": "Atta roti / आटा रोटी", "serving": "1 roti (30 g)", "potassium_mg": 60, "note": "1–2 rotis per meal is fine. Multigrain atta jumps higher — treat as RED.", "linked_food_id": "food-atta-roti"},
            {"name": "Bajra Roti", "hindi": "Bajra roti / बाजरा रोटी", "serving": "1 small (30 g)", "potassium_mg": 110, "note": "Millets have more K and phosphorus than wheat. Alternate with white rice.", "linked_food_id": None},
            {"name": "Jowar Roti", "hindi": "Jowar roti / ज्वार रोटी", "serving": "1 small (30 g)", "potassium_mg": 100, "note": "Sorghum — moderate K. Better than bajra for kidneys.", "linked_food_id": None},
            {"name": "Oats (plain, small)", "hindi": "Oats / जई", "serving": "¼ cup dry (25 g)", "potassium_mg": 110, "note": "Cook with water not milk to keep phosphorus low. Small serving.", "linked_food_id": None},
            {"name": "Brown Rice", "hindi": "Brown chawal / ब्राउन चावल", "serving": "½ katori (75 g)", "potassium_mg": 59, "note": "Kept YELLOW by clinical override — bran layer adds phosphorus. Rotate with white rice, don't fully replace it.", "linked_food_id": "food-brown-rice"},
            {"name": "Poha (small serving)", "hindi": "Poha / पोहा", "serving": "½ katori (75 g)", "potassium_mg": 175, "note": "Beaten rice is low-K but garnishes push it up. See Snacks Guide.", "linked_food_id": None},
        ]},
    "RED": {"title": "Avoid — high phosphorus / K load", "subtitle": "Skip these as staples; small tasting portions only.",
        "grains": [
            {"name": "Multigrain Roti / Bread", "hindi": "Multigrain roti", "serving": "1 slice/roti (30 g)", "potassium_mg": 170, "note": "Extra grains = extra phosphorus (soy, oats, ragi, flax). Marketed as 'healthy' — not for CKD.", "linked_food_id": None},
            {"name": "Ragi (Finger Millet)", "hindi": "Ragi / रागी", "serving": "1 roti (30 g)", "potassium_mg": 150, "note": "Extremely high in phosphorus and calcium. Popular 'healthy' choice that is NOT kidney-safe.", "linked_food_id": None},
            {"name": "Quinoa", "hindi": "Quinoa", "serving": "½ katori (75 g)", "potassium_mg": 250, "note": "High K + phosphorus. Skip in advanced CKD.", "linked_food_id": None},
            {"name": "Whole Wheat Pasta", "hindi": "Whole wheat pasta", "serving": "1 katori (100 g)", "potassium_mg": 155, "note": "Refined pasta is safer for CKD than whole-wheat varieties.", "linked_food_id": None},
            {"name": "Millets (Kodo, Foxtail, etc.)", "hindi": "Bajra / जौ", "serving": "1 katori (100 g)", "potassium_mg": 220, "note": "Whole-grain millet meals concentrate K + phosphorus. Small tasting bowl only.", "linked_food_id": None},
            {"name": "Muesli / Granola", "hindi": "Muesli", "serving": "1 katori (50 g)", "potassium_mg": 300, "note": "Dried fruit + nuts + oats = a K + phosphorus bomb. Never as breakfast.", "linked_food_id": None},
            {"name": "Cornflakes with Milk", "hindi": "Cornflakes", "serving": "1 katori (30 g)", "potassium_mg": 199, "note": "Milk pushes phosphorus over the RED line. Fortified cornflakes add phosphate additives.", "linked_food_id": "food-cornflakes-with-milk"},
        ]},
}
from guide_utils import enrich_guide


def get_grain_guide() -> dict:
    return enrich_guide(GRAIN_GUIDE, "grains")
