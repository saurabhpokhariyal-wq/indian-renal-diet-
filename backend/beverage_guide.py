"""Curated beverage reference for CKD/dialysis patients.

Grouping is potassium-forward but also flags FLUID impact — for advanced CKD
and dialysis patients, every drink counts toward the daily fluid limit
regardless of its potassium score.

Guidance rules used to place each drink:
  GREEN   — potassium ≤150 mg per typical glass AND no phosphorus/oxalate/sugar caveat
  YELLOW  — 150-300 mg K per glass OR milk-based (phosphorus) OR sugar-heavy
  RED     — >300 mg K per glass OR carries a specific renal caveat (concentrated juice,
            electrolyte drink, malt drink, alcohol)

Every entry lists FLUID mL per serving so patients on a restricted fluid budget
can add it up. `linked_food_id` deep-links to a matching seed entry when one exists.
"""

BEVERAGE_GUIDE = {
    "GREEN": {
        "title": "Safe — daily portions",
        "subtitle": "Low potassium per glass. Still counts toward your daily fluid limit.",
        "beverages": [
            {
                "name": "Water",
                "hindi": "Paani / पानी",
                "serving": "1 glass (200 ml)",
                "potassium_mg": 0,
                "fluid_ml": 200,
                "note": "The safest choice. Track total daily volume against your fluid budget — even water isn't unlimited in advanced CKD.",
                "linked_food_id": None,
            },
            {
                "name": "Buttermilk (Chaas)",
                "hindi": "Chaas / छाछ",
                "serving": "1 small glass (150 ml)",
                "potassium_mg": 150,
                "fluid_ml": 150,
                "note": "Fresh, unsalted chaas is a summer-safe drink. Keep to one small glass — added salt and dairy phosphorus become issues at higher volumes.",
                "linked_food_id": None,
            },
            {
                "name": "Herbal Tea (unsweetened)",
                "hindi": "Herbal chai",
                "serving": "1 cup (150 ml)",
                "potassium_mg": 20,
                "fluid_ml": 150,
                "note": "Peppermint, chamomile, tulsi — minimal potassium. Avoid pre-mixed sachets with added electrolytes or salt.",
                "linked_food_id": None,
            },
            {
                "name": "Rice Water (Kanji)",
                "hindi": "Kanji / कांजी",
                "serving": "1 small glass (150 ml)",
                "potassium_mg": 40,
                "fluid_ml": 150,
                "note": "Traditional cooling drink. Naturally low in potassium if made from leached-and-drained rice water.",
                "linked_food_id": None,
            },
            {
                "name": "Barley Water",
                "hindi": "Jau ka paani / जौ का पानी",
                "serving": "1 glass (200 ml)",
                "potassium_mg": 30,
                "fluid_ml": 200,
                "note": "Safe and hydrating. Skip commercial ready-mixes — they usually add salt and sugar.",
                "linked_food_id": None,
            },
            {
                "name": "Ginger-Lemon Water",
                "hindi": "Adrak-nimbu paani / अदरक-नींबू पानी",
                "serving": "1 glass (200 ml)",
                "potassium_mg": 40,
                "fluid_ml": 200,
                "note": "Fresh ginger + a squeeze of lemon in warm water. Unsweetened or lightly sweetened only.",
                "linked_food_id": None,
            },
            {
                "name": "Weak Black Tea (no milk)",
                "hindi": "Bina doodh ki chai / बिना दूध की चाय",
                "serving": "1 cup (150 ml)",
                "potassium_mg": 40,
                "fluid_ml": 150,
                "note": "1-2 cups a day is fine. Adding milk moves this into YELLOW because of phosphorus and potassium in milk.",
                "linked_food_id": None,
            },
        ],
    },
    "YELLOW": {
        "title": "Limit — small cups only",
        "subtitle": "Milk-based or moderately-K drinks. One small cup at a time, not multiple.",
        "beverages": [
            {
                "name": "Masala Chai (with milk)",
                "hindi": "Masala chai / मसाला चाय",
                "serving": "1 small cup (100 ml)",
                "potassium_mg": 130,
                "fluid_ml": 100,
                "note": "Milk adds potassium and phosphorus. Keep to 1-2 small cups per day and use less milk if you're on phosphate binders.",
                "linked_food_id": None,
            },
            {
                "name": "Filter Coffee (with milk)",
                "hindi": "Coffee / कॉफी",
                "serving": "1 small cup (100 ml)",
                "potassium_mg": 140,
                "fluid_ml": 100,
                "note": "South Indian filter coffee with milk sits at the top of YELLOW because of dairy phosphorus. Black filter coffee without milk drops back to GREEN.",
                "linked_food_id": None,
            },
            {
                "name": "Green Tea",
                "hindi": "Green tea",
                "serving": "1 cup (150 ml)",
                "potassium_mg": 80,
                "fluid_ml": 150,
                "note": "Naturally low in K but concentrated antioxidants can interfere with some medications. Limit to 2 cups; ask your doctor if you're on blood thinners.",
                "linked_food_id": None,
            },
            {
                "name": "Sweet Lassi",
                "hindi": "Meethi lassi / मीठी लस्सी",
                "serving": "1 small glass (150 ml)",
                "potassium_mg": 210,
                "fluid_ml": 150,
                "note": "Yogurt base means moderate potassium AND phosphorus. Occasional treat only; skip if diabetic.",
                "linked_food_id": None,
            },
            {
                "name": "Sugarcane Juice",
                "hindi": "Ganne ka ras / गन्ने का रस",
                "serving": "½ glass (100 ml)",
                "potassium_mg": 195,
                "fluid_ml": 100,
                "note": "Naturally sugary and moderately K-rich. A very small tasting glass only; not for diabetic patients.",
                "linked_food_id": None,
            },
            {
                "name": "Nimbu Paani (lightly sweetened)",
                "hindi": "Nimbu paani / नींबू पानी",
                "serving": "1 glass (200 ml)",
                "potassium_mg": 90,
                "fluid_ml": 200,
                "note": "Lemon juice + water + a pinch of sugar is fine. Avoid the salt-heavy version and skip if diabetic (or use no sugar).",
                "linked_food_id": None,
            },
            {
                "name": "Milk (plain, small glass)",
                "hindi": "Doodh / दूध",
                "serving": "½ glass (100 ml)",
                "potassium_mg": 155,
                "fluid_ml": 100,
                "note": "Toned milk is safer than full-cream for kidneys. Half-glass at a time; avoid multiple servings across the day.",
                "linked_food_id": None,
            },
        ],
    },
    "RED": {
        "title": "Avoid — high potassium or renal caveat",
        "subtitle": "Concentrated K, added electrolytes, or dairy-heavy drinks. Skip these routinely.",
        "beverages": [
            {
                "name": "Coconut Water (Nariyal Paani)",
                "hindi": "Nariyal paani / नारियल पानी",
                "serving": "1 glass (200 ml)",
                "potassium_mg": 500,
                "fluid_ml": 200,
                "note": "Widely thought of as 'natural and safe' — actually one of the most dangerous drinks in CKD. A single tender coconut can push you over the daily potassium limit.",
                "linked_food_id": None,
            },
            {
                "name": "Fresh Orange Juice",
                "hindi": "Santra juice / संतरे का रस",
                "serving": "1 glass (200 ml)",
                "potassium_mg": 500,
                "fluid_ml": 200,
                "note": "Juicing concentrates the potassium 3-4× compared to eating a whole orange. Avoid — including 'fresh-pressed' varieties.",
                "linked_food_id": None,
            },
            {
                "name": "Mosambi (Sweet Lime) Juice",
                "hindi": "Mosambi juice / मोसंबी का रस",
                "serving": "1 glass (200 ml)",
                "potassium_mg": 400,
                "fluid_ml": 200,
                "note": "Common 'get-well' drink in India that is actually unsafe for CKD. Whole fresh mosambi in tiny portions is different from juicing multiple fruits into a glass.",
                "linked_food_id": None,
            },
            {
                "name": "Pomegranate Juice",
                "hindi": "Anaar juice / अनार का रस",
                "serving": "1 glass (200 ml)",
                "potassium_mg": 530,
                "fluid_ml": 200,
                "note": "Extremely K-dense. Half a cup of arils is safer if you crave the flavour.",
                "linked_food_id": None,
            },
            {
                "name": "Bottled Fruit Juice",
                "hindi": "Bottled juice",
                "serving": "1 glass (200 ml)",
                "potassium_mg": 350,
                "fluid_ml": 200,
                "note": "Real Activ, Tropicana, Paper Boat etc. also carry added sugar and preservatives. Avoid — even '100% pure' bottled juices concentrate K.",
                "linked_food_id": None,
            },
            {
                "name": "Sports / Energy Drinks",
                "hindi": "Energy drinks",
                "serving": "1 bottle (250 ml)",
                "potassium_mg": 200,
                "fluid_ml": 250,
                "note": "Marketed as 'electrolyte replenishment' — deliberately loaded with sodium AND potassium. Never for CKD patients.",
                "linked_food_id": None,
            },
            {
                "name": "Bournvita / Horlicks / Boost",
                "hindi": "Malt drinks",
                "serving": "1 glass (200 ml)",
                "potassium_mg": 300,
                "fluid_ml": 200,
                "note": "Milk-based malt drinks are extremely high in phosphorus (added milk-solids and cocoa). Skip entirely.",
                "linked_food_id": None,
            },
            {
                "name": "Tomato Juice",
                "hindi": "Tamatar juice / टमाटर का रस",
                "serving": "1 glass (200 ml)",
                "potassium_mg": 530,
                "fluid_ml": 200,
                "note": "Both potassium AND sodium are dangerously high, especially in canned/bottled tomato juice.",
                "linked_food_id": None,
            },
            {
                "name": "Beetroot Juice",
                "hindi": "Chukandar juice / चुकंदर का रस",
                "serving": "1 glass (200 ml)",
                "potassium_mg": 640,
                "fluid_ml": 200,
                "note": "Very high potassium and oxalates (kidney-stone risk). Occasionally recommended for blood pressure but not appropriate for CKD.",
                "linked_food_id": None,
            },
            {
                "name": "Beer / Alcohol",
                "hindi": "Sharab / शराब",
                "serving": "1 bottle (330 ml)",
                "potassium_mg": 90,
                "fluid_ml": 330,
                "note": "Even though K is modest, alcohol worsens BP control and dehydrates. Every drink counts toward the strict fluid limit. Ask your nephrologist before any alcohol.",
                "linked_food_id": None,
            },
        ],
    },
}


def get_beverage_guide() -> dict:
    """Return the curated beverage guide grouped by tier (GREEN/YELLOW/RED)."""
    return BEVERAGE_GUIDE
