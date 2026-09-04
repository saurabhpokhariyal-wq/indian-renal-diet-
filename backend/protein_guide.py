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
            {"name": "Egg White (boiled)", "hindi": "Anda safed / अंडे का सफेद", "serving": "2 whites (60 g)", "potassium_mg": 110, "note": "The gold-standard renal protein: high biological value, low phosphorus, low potassium. Skip the yolk in advanced CKD.", "linked_food_id": "food-egg-white-boiled"},
            {"name": "Egg White Bhurji", "hindi": "Anda safed bhurji", "serving": "3 whites (90 g)", "potassium_mg": 150, "note": "Cook with minimal salt and unsalted butter or a teaspoon of oil.", "linked_food_id": "food-egg-white-bhurji"},
            {"name": "Grilled/Baked Chicken Breast", "hindi": "Chicken breast / चिकन", "serving": "60 g cooked", "potassium_mg": 200, "note": "Skinless. Avoid tandoori/masala marinades that are salt-heavy. One small piece at a time.", "linked_food_id": "food-grilled-baked-chicken-breast"},
            {"name": "Grilled Fish (fresh water)", "hindi": "Machhli / मछली", "serving": "60 g cooked", "potassium_mg": 210, "note": "Rohu, katla, or basa in small portions. Avoid dried/salted fish (extremely high sodium).", "linked_food_id": "food-grilled-fish-fresh-water"},
            {"name": "Cottage Cheese (Paneer, small)", "hindi": "Paneer / पनीर", "serving": "30 g (2 tbsp)", "potassium_mg": 40, "note": "Small cubes as topping only. Full katori of paneer sabzi is RED (phosphorus).", "linked_food_id": "food-cottage-cheese-paneer-small"},
        ]},
    "YELLOW": {"title": "Limit — half-katori portions", "subtitle": "Fine occasionally with binders / leaching.",
        "proteins": [
            {"name": "Toor Dal (arhar)", "hindi": "Toor dal / अरहर दाल", "serving": "½ katori (60 g)", "potassium_mg": 78, "note": "Kept YELLOW by clinical override — pulses concentrate potassium in the cooking water. Drain the first boil water before final cooking.", "linked_food_id": "food-toor-dal"},
            {"name": "Moong Dal (yellow)", "hindi": "Moong dal / मूंग दाल", "serving": "½ katori (60 g)", "potassium_mg": 84, "note": "Easiest dal to digest but still requires portion vigilance in CKD.", "linked_food_id": "food-moong-dal"},
            {"name": "Masoor Dal (red split)", "hindi": "Masoor dal / मसूर दाल", "serving": "½ katori (60 g)", "potassium_mg": 90, "note": "Leach potassium by boiling in extra water and draining once before final cooking.", "linked_food_id": "food-masoor-dal-red-split"},
            {
                "name": "Chana Dal (split Bengal gram, cooked)",
                "hindi": "Chana dal / चना दाल",
                "serving": "½ katori (60 g cooked)",
                "potassium_mg": 105,
                "phosphorus_mg": 85,
                "sodium_mg": 3,
                "note": "Common in dal fry and mixed dals. Slightly higher K than toor — keep to ½ katori and drain the first boil water.",
                "linked_food_id": "food-chana-dal-split-bengal-gram-cooked",
                "source": "IFCT 2017, code L006 (dry) with ~2.4× cooked-leaching factor",
            },
            {
                "name": "Urad Dal (split, cooked)",
                "hindi": "Urad dal / उड़द दाल",
                "serving": "½ katori (60 g cooked)",
                "potassium_mg": 130,
                "phosphorus_mg": 100,
                "sodium_mg": 3,
                "note": "The base of dal makhani (which is RED because of cream + butter). On its own, plain tempered urad in a small portion is manageable.",
                "linked_food_id": "food-urad-dal-split-cooked",
                "source": "IFCT 2017, code L003 (dry) with ~2.4× cooked-leaching factor",
            },
            {
                "name": "Whole Green Moong (sabut, cooked)",
                "hindi": "Sabut moong / साबुत मूंग",
                "serving": "½ katori (60 g cooked)",
                "potassium_mg": 130,
                "phosphorus_mg": 90,
                "sodium_mg": 3,
                "note": "Whole pulses carry slightly more K than split dals. Presoak overnight and drain the soak-water before cooking.",
                "linked_food_id": "food-whole-green-moong-sabut-cooked",
                "source": "IFCT 2017, code L004 (dry) with ~2.4× cooked-leaching factor",
            },
            {
                "name": "Kala Chana (whole black gram, cooked)",
                "hindi": "Kala chana / काला चना",
                "serving": "½ katori (60 g cooked)",
                "potassium_mg": 150,
                "phosphorus_mg": 105,
                "sodium_mg": 4,
                "note": "Common in chaat and Sunday chana masala. Small portion only; skip the tangy masala salt topping.",
                "linked_food_id": "food-kala-chana-whole-black-gram-cooked",
                "source": "IFCT 2017, code L001 (dry) with ~2.4× cooked-leaching factor",
            },
            {"name": "Whole Egg (boiled)", "hindi": "Sabut anda / साबुत अंडा", "serving": "1 egg (50 g)", "potassium_mg": 63, "phosphorus_mg": 105, "sodium_mg": 61, "note": "Yolk carries ~100 mg P per egg vs ~4 mg in the white — advanced CKD should stick to whites only.", "linked_food_id": "food-whole-egg-boiled", "source": "IFCT 2017, code M004 (scaled to 50 g)"},
            {"name": "Tofu (plain, unsalted)", "hindi": "Tofu / टोफू", "serving": "50 g", "potassium_mg": 120, "note": "Fine as a paneer alternative. Salted / marinated tofu is RED.", "linked_food_id": "food-tofu-plain-unsalted"},
            {"name": "Sprouted Moong (small)", "hindi": "Ankurit moong / अंकुरित मूंग", "serving": "¼ katori (30 g)", "potassium_mg": 90, "note": "Small salad quantity only — sprouted pulses concentrate K.", "linked_food_id": "food-sprouted-moong-small"},
            {
                "name": "Plain Curd / Dahi (small katori)",
                "hindi": "Dahi / दही",
                "serving": "½ katori (100 g)",
                "potassium_mg": 137,
                "phosphorus_mg": 100,
                "sodium_mg": 60,
                "note": "A small katori is fine; a full 200 g katori doubles the phosphorus load. Cool with jeera/pudina rather than salt.",
                "linked_food_id": "food-plain-curd-dahi-small-katori",
                "source": "IFCT 2017, code L003 (whole-milk curd)",
            },
            {
                "name": "Buttermilk / Chaas (unsalted)",
                "hindi": "Chaas / छाछ",
                "serving": "1 glass (200 ml)",
                "potassium_mg": 140,
                "phosphorus_mg": 60,
                "sodium_mg": 50,
                "note": "Diluted curd; safer than a glass of milk. UNSALTED only — the salted street chaas adds 400+ mg Na per glass.",
                "linked_food_id": "food-buttermilk-chaas-unsalted",
                "source": "IFCT 2017, code L003 (curd diluted ~1:2 with water)",
            },
        ]},
    "RED": {"title": "Avoid — high phosphorus, K or protein burden", "subtitle": "These commonly-loved proteins are unsafe as routine meals.",
        "proteins": [
            {"name": "Rajma / Chole / Kidney Beans", "hindi": "Rajma / राजमा", "serving": "½ katori (75 g)", "potassium_mg": 400, "note": "Very high K + phosphorus. Skip in advanced CKD; leaching helps only marginally.", "linked_food_id": "food-rajma-chole-kidney-beans"},
            {"name": "Palak Paneer", "hindi": "Palak paneer / पालक पनीर", "serving": "1 katori (150 g)", "potassium_mg": 650, "note": "Double whammy — spinach K + paneer phosphorus. Avoid entirely.", "linked_food_id": "food-palak-paneer"},
            {"name": "Mutton / Red Meat", "hindi": "Mutton / मटन", "serving": "60 g cooked", "potassium_mg": 320, "note": "High K + phosphorus + saturated fat. Occasional tiny portion at most.", "linked_food_id": "food-mutton-red-meat"},
            {"name": "Prawns / Shellfish", "hindi": "Jheenga / झींगा", "serving": "60 g", "potassium_mg": 190, "note": "High sodium (naturally from sea water) + cholesterol. Skip.", "linked_food_id": "food-prawns-shellfish"},
            {"name": "Processed Meats (sausage, salami)", "hindi": "Sausage / सॉसेज", "serving": "50 g", "potassium_mg": 200, "note": "Extreme sodium + phosphate preservatives. Never.", "linked_food_id": "food-processed-meats-sausage-salami"},
            {"name": "Milk (full glass)", "hindi": "Doodh / दूध", "serving": "1 glass (200 ml)", "potassium_mg": 310, "note": "Full glass drives phosphorus AND K. Half-glass is YELLOW (see Beverages).", "linked_food_id": "food-milk-full-glass"},
            {"name": "Cheese (any variety)", "hindi": "Cheese / चीज़", "serving": "30 g", "potassium_mg": 90, "note": "Processed and aged cheeses are loaded with phosphate additives. Skip.", "linked_food_id": "food-cheese-any-variety"},
            {
                "name": "Salted Lassi (glass)",
                "hindi": "Namkeen lassi / नमकीन लस्सी",
                "serving": "1 glass (250 ml)",
                "potassium_mg": 250,
                "phosphorus_mg": 155,
                "sodium_mg": 450,
                "note": "Salted street lassi stacks a full glass of curd's K + P + 400+ mg added Na. Sweet lassi drops the sodium but doubles sugar — RED for diabetics either way.",
                "linked_food_id": "food-salted-lassi-glass",
                "source": "IFCT 2017, code L003 (curd) + typical 400 mg added Na per glass",
            },
            {
                "name": "Sweetened Condensed Milk",
                "hindi": "Milkmaid / गाढ़ा मीठा दूध",
                "serving": "2 tbsp (30 g)",
                "potassium_mg": 110,
                "phosphorus_mg": 75,
                "sodium_mg": 40,
                "note": "The base of many mithais and chai variations. Concentrated milk solids = concentrated phosphorus. Also disqualifying for diabetics.",
                "linked_food_id": "food-sweetened-condensed-milk",
                "source": "IFCT 2017, code L010",
            },
            {"name": "Soybean / Soya Chunks (curry)", "hindi": "Soya chunks / सोया चंक्स", "serving": "½ katori (75 g)", "potassium_mg": 850, "note": "Extremely K + protein dense. Never for CKD.", "linked_food_id": "food-soyabean-curry"},
            {
                "name": "Egg Yolk (alone)",
                "hindi": "Anda ki zardi / अंडे की जर्दी",
                "serving": "1 yolk (~17 g)",
                "potassium_mg": 18,
                "phosphorus_mg": 100,
                "sodium_mg": 8,
                "note": "Low potassium, but concentrates the large majority of an egg's phosphorus — roughly 100 mg per yolk vs ~4 mg in the white (IFCT 2017 measured values). Advanced CKD / dialysis patients should stick to whites only — this is a phosphorus call, not a potassium one.",
                "linked_food_id": "food-egg-yolk-alone",
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
                "linked_food_id": "food-khoa-mawa",
                "source": "IFCT 2017, code L004 (scaled to 30 g)",
            },
        ]},
}
from guide_utils import enrich_guide


def get_protein_guide() -> dict:
    return enrich_guide(PROTEIN_GUIDE, "proteins")
