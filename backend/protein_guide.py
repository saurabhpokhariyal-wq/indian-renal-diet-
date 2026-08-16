"""Curated protein reference for CKD/dialysis patients.

Every entry stores `potassium_mg` (source of truth); the API layer derives
`potassium_meq` (mg / 39.1) and `high_sodium` (sodium_mg >= 400) via
`guide_utils.enrich_guide` — the two units cannot drift apart. UI renders both
figures side-by-side (e.g. "162 mg / 4.1 mEq").

Sourcing convention (matches the seed-DB audit trail):
  - Entries with a "source" field are directly measured from IFCT 2017 (ICMR-NIN)
    at the code cited; per-serving values are IFCT's per-100g figure scaled by
    the stated serving weight (no other transformation).
  - Entries without a "source" field are still on legacy web-sourced data and
    are candidates for the next IFCT backfill pass.

Legume caveat (do NOT patch cooked-dal rows with IFCT dry-weight figures):
  IFCT's Grain-Legumes group (Bengal gram, black gram, green gram, red gram,
  etc.) reports raw, dry pulses at 700-1400 mg K / 100 g. Cooked dal has been
  through water absorption AND boiling leaching, so its potassium is
  substantially lower. The existing Toor Dal (78 mg / 60 g cooked) and Moong
  Dal (84 mg / 60 g cooked) entries are cooked figures and MUST stay that way.
  Any future backfill from IFCT for cooked pulses must apply an explicit
  conversion (cooked mg/100g ≈ dry mg/100g ÷ ~2.4) and flag it distinctly from
  directly-measured entries."""
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
            {"name": "Whole Egg (boiled)", "hindi": "Sabut anda / साबुत अंडा", "serving": "1 egg (50 g)", "potassium_mg": 63, "phosphorus_mg": 105, "sodium_mg": 61, "note": "Yolk carries ~100 mg P per egg vs ~4 mg in the white — advanced CKD should stick to whites only.", "linked_food_id": None, "source": "IFCT 2017, code M004 (scaled to 50 g)"},
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
            {
                "name": "Egg Yolk (alone)",
                "hindi": "Anda ki zardi / अंडे की जर्दी",
                "serving": "1 yolk (~17 g)",
                "potassium_mg": 18,
                "phosphorus_mg": 100,
                "sodium_mg": 8,
                "note": "Low potassium, but concentrates the large majority of an egg's phosphorus — roughly 100 mg per yolk vs ~4 mg in the white (IFCT 2017 measured values). Advanced CKD / dialysis patients should stick to whites only — this is a phosphorus call, not a potassium one.",
                "linked_food_id": None,
                "source": "IFCT 2017, code M006 (scaled to ~17 g)",
            },
            {
                "name": "Khoa / Mawa",
                "hindi": "Khoa / खोया",
                "serving": "30 g",
                "potassium_mg": 161,
                "phosphorus_mg": 143,
                "sodium_mg": 14,
                "note": "Reduced-milk solid used as the base of gulab jamun, peda, barfi, and most milk-based Indian sweets. This is WHY those sweets are RED — it isn't the sugar, it's the concentrated milk solids stacking both potassium and phosphorus (~143 mg P per 30 g). See Snacks for individual mithai items.",
                "linked_food_id": None,
                "source": "IFCT 2017, code L004 (scaled to 30 g)",
            },
        ]},
}
from guide_utils import enrich_guide


def get_protein_guide() -> dict:
    return enrich_guide(PROTEIN_GUIDE, "proteins")
