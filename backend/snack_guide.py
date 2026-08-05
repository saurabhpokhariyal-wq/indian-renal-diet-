"""Curated snack reference for CKD/dialysis patients.

Snacks are the sneakiest source of sodium and phosphorus in an Indian diet.
Even 'homemade' items can be problematic once salt/besan/dairy get involved.
"""

SNACK_GUIDE = {
    "GREEN": {
        "title": "Safe — daily snacking",
        "subtitle": "Low in sodium, potassium AND phosphorus at these portion sizes.",
        "snacks": [
            {"name": "Roasted Makhana (unsalted)", "hindi": "Makhana / मखाना", "serving": "1 cup (30 g)", "potassium_mg": 90, "note": "The gold-standard CKD snack when roasted plain. Skip the flavoured/salted packets — they add heavy sodium.", "linked_food_id": None},
            {"name": "Puffed Rice (unsalted)", "hindi": "Murmura / मुरमुरा", "serving": "1 cup (30 g)", "potassium_mg": 25, "note": "Very low in everything. Base for safer 'bhel' at home — skip the sev/chutneys/onion-tomato which push it to RED.", "linked_food_id": None},
            {"name": "Homemade Khakhra (plain)", "hindi": "Khakhra / खाखरा", "serving": "1 piece (~15 g)", "potassium_mg": 55, "note": "Plain, low-salt khakhra is fine. Masala/methi/pudina versions carry extra sodium.", "linked_food_id": None},
            {"name": "Apple / Pear slices", "hindi": "Seb / Nashpati", "serving": "1 small fruit", "potassium_mg": 158, "note": "See Fruit Guide. Ready-to-grab safe snack.", "linked_food_id": "food-apple"},
            {"name": "Cucumber Sticks", "hindi": "Kheera / खीरा", "serving": "½ medium (100 g)", "potassium_mg": 150, "note": "Serve with a squeeze of lemon and pepper — NOT salt.", "linked_food_id": "food-cucumber"},
            {"name": "Rice Puffs / Kurmura chivda (unsalted homemade)", "hindi": "Chivda / चिवड़ा", "serving": "½ cup (25 g)", "potassium_mg": 60, "note": "Homemade with just puffed rice + a few peanuts + jeera; commercial chivda is RED.", "linked_food_id": None},
        ],
    },
    "YELLOW": {
        "title": "Limit — small handfuls only",
        "subtitle": "Moderate K/P or salt — one small portion, not multiple servings.",
        "snacks": [
            {"name": "Roasted Chana (small handful)", "hindi": "Bhuna chana / भुना चना", "serving": "2 tbsp (20 g)", "potassium_mg": 155, "note": "Protein-rich but concentrates K in a full-cup portion. Two tablespoons only.", "linked_food_id": None},
            {"name": "Peanut Chikki (small piece)", "hindi": "Moongfali chikki / मूंगफली चिक्की", "serving": "1 piece (25 g)", "potassium_mg": 110, "note": "OK as an occasional sweet. Sugar-heavy — skip if diabetic.", "linked_food_id": None},
            {"name": "Dry Fruit Trail (very small)", "hindi": "Sukha meva / सूखा मेवा", "serving": "1 tbsp (10 g)", "potassium_mg": 90, "note": "Almonds/walnuts add phosphorus; raisins add K. One small spoon at a time.", "linked_food_id": None},
            {"name": "Sabudana Khichdi (small katori)", "hindi": "Sabudana khichdi / साबूदाना खिचड़ी", "serving": "½ katori (75 g)", "potassium_mg": 155, "note": "Sabudana itself is low-K but the recipe uses peanuts + salt. Keep portion small.", "linked_food_id": None},
            {"name": "Poha (small portion)", "hindi": "Poha / पोहा", "serving": "½ katori (75 g)", "potassium_mg": 175, "note": "Fine in a half-katori. Avoid heavy garnish with peanuts + onion + potato which push K + sodium up.", "linked_food_id": None},
            {"name": "Idli (1 piece)", "hindi": "Idli / इडली", "serving": "1 piece (60 g)", "potassium_mg": 90, "note": "One idli with mild chutney is fine. Sambar is very high sodium — skip or use a spoonful only.", "linked_food_id": None},
            {"name": "Upma (small portion)", "hindi": "Upma / उपमा", "serving": "½ katori (75 g)", "potassium_mg": 130, "note": "Small portions OK. Watch added mustard-seed tempering + salt.", "linked_food_id": None},
            {"name": "Bread Toast (plain, no butter)", "hindi": "Bread toast / ब्रेड टोस्ट", "serving": "1 slice (30 g)", "potassium_mg": 55, "note": "One slice with jam OR unsalted butter — not both. Multigrain bread is HIGHER phosphorus.", "linked_food_id": None},
        ],
    },
    "RED": {
        "title": "Avoid — routine renal danger",
        "subtitle": "Extreme sodium, phosphorus additives, or hidden K. Skip these as daily snacks.",
        "snacks": [
            {"name": "Namkeen / Bhujia / Mixture", "hindi": "Namkeen / नमकीन", "serving": "50 g pack", "potassium_mg": 320, "note": "Extremely high sodium (1000+ mg per small pack) + fried oils. THE single worst snack category for CKD.", "linked_food_id": None},
            {"name": "Potato Chips (Lays, Kurkure)", "hindi": "Chips / चिप्स", "serving": "1 small pack (30 g)", "potassium_mg": 350, "note": "High K (potato base) AND high sodium AND industrial oils. Never.", "linked_food_id": None},
            {"name": "Papad (fried or roasted)", "hindi": "Papad / पापड़", "serving": "1 papad (10 g)", "potassium_mg": 45, "note": "One papad = ~500 mg sodium. The K is low but the salt load is brutal.", "linked_food_id": None},
            {"name": "Pakoras (any variety)", "hindi": "Pakora / पकौड़ा", "serving": "4 pieces (60 g)", "potassium_mg": 280, "note": "Besan (chickpea flour) is high in phosphorus + potassium. Deep-fried in reused oil. Skip.", "linked_food_id": None},
            {"name": "Samosa", "hindi": "Samosa / समोसा", "serving": "1 piece (100 g)", "potassium_mg": 380, "note": "Potato filling + fried maida + heavy salt. Occasional single piece maximum.", "linked_food_id": None},
            {"name": "Kachori", "hindi": "Kachori / कचौड़ी", "serving": "1 piece (75 g)", "potassium_mg": 280, "note": "Fried, salt-heavy, often stuffed with dal (phosphorus). Skip.", "linked_food_id": None},
            {"name": "Sev / Ganthiya", "hindi": "Sev / सेव", "serving": "30 g", "potassium_mg": 200, "note": "Besan + salt + oil. Small amounts as chaat garnish stack up quickly.", "linked_food_id": None},
            {"name": "Cheese-based snacks (cubes, sticks)", "hindi": "Cheese snacks", "serving": "30 g", "potassium_mg": 100, "note": "Processed cheese is loaded with phosphate additives — one of the worst phosphorus sources.", "linked_food_id": None},
            {"name": "Chocolate / Dark Chocolate", "hindi": "Chocolate", "serving": "1 small bar (30 g)", "potassium_mg": 210, "note": "Dark chocolate is high in potassium AND phosphorus. Occasional tiny square only.", "linked_food_id": None},
            {"name": "Commercial Biscuits (Marie, cream, cookies)", "hindi": "Biskut / बिस्कुट", "serving": "4 biscuits (30 g)", "potassium_mg": 100, "note": "Phosphate-based leavening agents. Sodium adds up. Better as a very occasional single biscuit only.", "linked_food_id": None},
            {"name": "Instant Noodles (Maggi etc.)", "hindi": "Maggi / मैगी", "serving": "1 pack (70 g)", "potassium_mg": 200, "note": "Sodium bomb (1500+ mg per pack) plus phosphate additives in the masala. Never.", "linked_food_id": None},
            {"name": "Popcorn (salted/buttered)", "hindi": "Popcorn / पॉपकॉर्न", "serving": "1 small tub (50 g)", "potassium_mg": 130, "note": "Cinema-style popcorn is drowned in salt and phosphorus-laden 'butter flavour'. Plain air-popped at home is YELLOW.", "linked_food_id": None},
        ],
    },
}

def get_snack_guide() -> dict:
    return SNACK_GUIDE
