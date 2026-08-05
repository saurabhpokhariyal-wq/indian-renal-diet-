"""Curated protein reference for CKD/dialysis patients."""
PROTEIN_GUIDE = {
    "GREEN": {"title": "Safe — daily portions", "subtitle": "Best protein sources for kidney disease.",
        "proteins": [
            {"name": "Egg White (boiled)", "hindi": "Anda safed / अंडे का सफेद", "serving": "2 whites (60 g)", "potassium_mg": 110, "note": "The gold-standard renal protein: high biological value, low phosphorus, low potassium. Skip the yolk in advanced CKD.", "linked_food_id": None},
            {"name": "Egg White Bhurji", "hindi": "Anda safed bhurji", "serving": "3 whites (90 g)", "potassium_mg": 150, "note": "Cook with minimal salt and unsalted butter or a teaspoon of oil.", "linked_food_id": None},
            {"name": "Grilled/Baked Chicken Breast", "hindi": "Chicken breast / चिकन", "serving": "60 g cooked", "potassium_mg": 200, "note": "Skinless. Avoid tandoori/masala marinades that are salt-heavy. One small piece at a time.", "linked_food_id": None},
            {"name": "Grilled Fish (fresh water)", "hindi": "Machhli / मछली", "serving": "60 g cooked", "potassium_mg": 210, "note": "Rohu, katla, or basa in small portions. Avoid dried/salted fish (extremely high sodium).", "linked_food_id": None},
            {"name": "Cottage Cheese (Paneer, small)", "hindi": "Paneer / पनीर", "serving": "30 g (2 tbsp)", "potassium_mg": 40, "note": "Small cubes as topping only. Full katori of paneer sabzi is RED (phosphorus).", "linked_food_id": None},
        ]},
    "YELLOW": {"title": "Limit — half-katori portions", "subtitle": "Fine occasionally with binders / leaching.",
        "proteins": [
            {"name": "Toor Dal (arhar)", "hindi": "Toor dal / अरहर दाल", "serving": "½ katori (60 g)", "potassium_mg": 78, "note": "Kept YELLOW by clinical override — pulses concentrate potassium in the cooking water. Drain the first boil water before final cooking.", "linked_food_id": "food-toor-dal"},
            {"name": "Moong Dal (yellow)", "hindi": "Moong dal / मूंग दाल", "serving": "½ katori (60 g)", "potassium_mg": 84, "note": "Easiest dal to digest but still requires portion vigilance in CKD.", "linked_food_id": "food-moong-dal"},
            {"name": "Masoor Dal (red split)", "hindi": "Masoor dal / मसूर दाल", "serving": "½ katori (60 g)", "potassium_mg": 90, "note": "Leach potassium by boiling in extra water and draining once before final cooking.", "linked_food_id": None},
            {"name": "Whole Egg (boiled)", "hindi": "Sabut anda / साबुत अंडा", "serving": "1 egg (50 g)", "potassium_mg": 63, "note": "Yolk adds phosphorus and cholesterol. Advanced CKD: whites only.", "linked_food_id": None},
            {"name": "Tofu (plain, unsalted)", "hindi": "Tofu / टोफू", "serving": "50 g", "potassium_mg": 120, "note": "Fine as a paneer alternative. Salted / marinated tofu is RED.", "linked_food_id": None},
            {"name": "Sprouted Moong (small)", "hindi": "Ankurit moong / अंकुरित मूंग", "serving": "¼ katori (30 g)", "potassium_mg": 90, "note": "Small salad quantity only — sprouted pulses concentrate K.", "linked_food_id": None},
        ]},
    "RED": {"title": "Avoid — high phosphorus, K or protein burden", "subtitle": "These commonly-loved proteins are unsafe as routine meals.",
        "proteins": [
            {"name": "Rajma / Chole / Kidney Beans", "hindi": "Rajma / राजमा", "serving": "½ katori (75 g)", "potassium_mg": 400, "note": "Very high K + phosphorus. Skip in advanced CKD; leaching helps only marginally.", "linked_food_id": None},
            {"name": "Palak Paneer", "hindi": "Palak paneer / पालक पनीर", "serving": "1 katori (150 g)", "potassium_mg": 650, "note": "Double whammy — spinach K + paneer phosphorus. Avoid entirely.", "linked_food_id": "food-palak-paneer"},
            {"name": "Mutton / Red Meat", "hindi": "Mutton / मटन", "serving": "60 g cooked", "potassium_mg": 320, "note": "High K + phosphorus + saturated fat. Occasional tiny portion at most.", "linked_food_id": None},
            {"name": "Prawns / Shellfish", "hindi": "Jheenga / झींगा", "serving": "60 g", "potassium_mg": 190, "note": "High sodium (naturally from sea water) + cholesterol. Skip.", "linked_food_id": None},
            {"name": "Processed Meats (sausage, salami)", "hindi": "Sausage / सॉसेज", "serving": "50 g", "potassium_mg": 200, "note": "Extreme sodium + phosphate preservatives. Never.", "linked_food_id": None},
            {"name": "Milk (full glass)", "hindi": "Doodh / दूध", "serving": "1 glass (200 ml)", "potassium_mg": 310, "note": "Full glass drives phosphorus AND K. Half-glass is YELLOW (see Beverages).", "linked_food_id": None},
            {"name": "Cheese (any variety)", "hindi": "Cheese / चीज़", "serving": "30 g", "potassium_mg": 90, "note": "Processed and aged cheeses are loaded with phosphate additives. Skip.", "linked_food_id": None},
            {"name": "Soybean / Soya Chunks (curry)", "hindi": "Soya chunks / सोया चंक्स", "serving": "½ katori (75 g)", "potassium_mg": 850, "note": "Extremely K + protein dense. Never for CKD.", "linked_food_id": "food-soyabean-curry"},
        ]},
}
def get_protein_guide() -> dict: return PROTEIN_GUIDE
