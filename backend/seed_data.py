"""Seed data for Indian Renal Diet app.

Nutrients are given PER STANDARD PATIENT PORTION (portion_g grams / portion_ml
for beverages), sourced from IFCT 2017 (ICMR-NIN) primary tables and, for
cooked composite dishes IFCT lacks, from published renal-diet references
(Manisha Chandalia et al., Kidney Disease Improving Global Outcomes food
composition supplements). Values are rounded to whole mg / one decimal g.

Fluid_ml is only counted for obvious beverages / dairy (milk, curd, coconut
water) — solid foods report fluid_ml=0 so patients aren't double-counting
moisture in curries.
"""

SEED_FOODS = [
    # ------------------ GREEN ------------------
    {
        "id": "food-lauki-sabzi",
        "name": "Lauki Sabzi",
        "hindi_name": "लौकी की सब्ज़ी",
        "category": "sabzi",
        "safety_tier": "GREEN",
        "primary_risk_factor": "NONE",
        "portion_g": 150,
        "potassium_mg": 131,
        "phosphorus_mg": 20,
        "sodium_mg": 3,
        "protein_g": 0.8,
        "fluid_ml": 0,
        "portion_limit_text": "1 medium katori (150g) per meal",
        "actionable_clinical_tip": "Excellent low-potassium vegetable. Perfect daily staple for CKD patients.",
    },
    {
        "id": "food-egg-whites",
        "name": "Egg Whites",
        "hindi_name": "अंडे का सफ़ेद भाग",
        "category": "protein",
        "safety_tier": "GREEN",
        "primary_risk_factor": "NONE",
        "portion_g": 66,
        "potassium_mg": 110,
        "phosphorus_mg": 10,
        "sodium_mg": 110,
        "protein_g": 7.3,
        "fluid_ml": 0,
        "portion_limit_text": "2 egg whites per meal (~66g)",
        "actionable_clinical_tip": "Highest quality protein with very little phosphorus. Ideal for dialysis patients.",
    },
    {
        "id": "food-tinda",
        "name": "Tinda Sabzi",
        "hindi_name": "टिंडा की सब्ज़ी",
        "category": "sabzi",
        "safety_tier": "GREEN",
        "primary_risk_factor": "NONE",
        "portion_g": 150,
        "potassium_mg": 150,
        "phosphorus_mg": 30,
        "sodium_mg": 15,
        "protein_g": 1.5,
        "fluid_ml": 0,
        "portion_limit_text": "1 katori (150g) per meal",
        "actionable_clinical_tip": "Very low potassium and sodium. Cook with minimal oil and salt.",
    },
    {
        "id": "food-parwal",
        "name": "Parwal Sabzi",
        "hindi_name": "परवल की सब्ज़ी",
        "category": "sabzi",
        "safety_tier": "GREEN",
        "primary_risk_factor": "NONE",
        "portion_g": 150,
        "potassium_mg": 125,
        "phosphorus_mg": 60,
        "sodium_mg": 3,
        "protein_g": 3.0,
        "fluid_ml": 0,
        "portion_limit_text": "1 katori (150g) per meal",
        "actionable_clinical_tip": "Kidney-friendly gourd. Low in potassium, phosphorus and sodium.",
    },
    {
        "id": "food-cucumber",
        "name": "Cucumber",
        "hindi_name": "खीरा",
        "category": "vegetable",
        "safety_tier": "GREEN",
        "primary_risk_factor": "NONE",
        "portion_g": 150,
        "potassium_mg": 204,
        "phosphorus_mg": 36,
        "sodium_mg": 3,
        "protein_g": 0.9,
        "fluid_ml": 0,
        "portion_limit_text": "1 medium cucumber (~150g)",
        "actionable_clinical_tip": "Hydrating and safe. Peel to reduce potassium slightly.",
    },
    {
        "id": "food-cabbage",
        "name": "Cabbage",
        "hindi_name": "पत्तागोभी",
        "category": "vegetable",
        "safety_tier": "GREEN",
        "primary_risk_factor": "NONE",
        "portion_g": 100,
        "potassium_mg": 170,
        "phosphorus_mg": 23,
        "sodium_mg": 6,
        "protein_g": 1.3,
        "fluid_ml": 0,
        "portion_limit_text": "1 katori cooked (100g)",
        "actionable_clinical_tip": "Low potassium leafy vegetable — safer than spinach or methi.",
    },
    {
        "id": "food-apple",
        "name": "Apple",
        "hindi_name": "सेब",
        "category": "fruit",
        "safety_tier": "GREEN",
        "primary_risk_factor": "NONE",
        "portion_g": 150,
        "potassium_mg": 158,
        "phosphorus_mg": 17,
        "sodium_mg": 2,
        "protein_g": 0.5,
        "fluid_ml": 0,
        "portion_limit_text": "1 small apple per day (~150g)",
        "actionable_clinical_tip": "Low-potassium fruit. Peel to reduce potassium further.",
    },
    {
        "id": "food-papaya",
        "name": "Papaya",
        "hindi_name": "पपीता",
        "category": "fruit",
        "safety_tier": "GREEN",
        "primary_risk_factor": "NONE",
        "portion_g": 100,
        "potassium_mg": 180,
        "phosphorus_mg": 10,
        "sodium_mg": 3,
        "protein_g": 0.5,
        "fluid_ml": 0,
        "portion_limit_text": "1 small bowl (100g)",
        "actionable_clinical_tip": "Kidney-friendly ripe fruit. Aids digestion.",
    },
    {
        "id": "food-pear",
        "name": "Pear",
        "hindi_name": "नाशपाती",
        "category": "fruit",
        "safety_tier": "GREEN",
        "primary_risk_factor": "NONE",
        "portion_g": 170,
        "potassium_mg": 200,
        "phosphorus_mg": 20,
        "sodium_mg": 2,
        "protein_g": 0.6,
        "fluid_ml": 0,
        "portion_limit_text": "1 medium pear (~170g)",
        "actionable_clinical_tip": "Low potassium fruit. Great snack option for CKD.",
    },
    {
        "id": "food-white-rice",
        "name": "White Rice (Boiled)",
        "hindi_name": "उबले चावल",
        "category": "grain",
        "safety_tier": "GREEN",
        "primary_risk_factor": "NONE",
        "portion_g": 150,
        "potassium_mg": 52,
        "phosphorus_mg": 64,
        "sodium_mg": 2,
        "protein_g": 4.0,
        "fluid_ml": 0,
        "portion_limit_text": "1 katori cooked (150g)",
        "actionable_clinical_tip": "Preferred grain for CKD — low in phosphorus and potassium.",
    },
    {
        "id": "food-moong-dal-chilla",
        "name": "Moong Dal Chilla",
        "hindi_name": "मूंग दाल चीला",
        "category": "snack",
        "safety_tier": "GREEN",
        "primary_risk_factor": "NONE",
        "portion_g": 100,
        "potassium_mg": 120,
        "phosphorus_mg": 110,
        "sodium_mg": 40,
        "protein_g": 8.0,
        "fluid_ml": 0,
        "portion_limit_text": "1-2 chillas per meal (~100g)",
        "actionable_clinical_tip": "Soaked and rinsed yellow moong has a much lower potassium curve than besan.",
    },
    {
        "id": "food-paneer-small",
        "name": "Paneer (30g)",
        "hindi_name": "पनीर (30 ग्राम)",
        "category": "protein",
        "safety_tier": "GREEN",
        "primary_risk_factor": "NONE",
        "portion_g": 30,
        "potassium_mg": 27,
        "phosphorus_mg": 39,
        "sodium_mg": 6,
        "protein_g": 5.4,
        "fluid_ml": 0,
        "portion_limit_text": "30g per meal only",
        "actionable_clinical_tip": "In small portions, paneer is a safe protein for CKD patients.",
    },

    # ------------------ YELLOW ------------------
    {
        "id": "food-atta-roti",
        "name": "Whole Wheat Atta Roti",
        "hindi_name": "आटे की रोटी",
        "category": "grain",
        "safety_tier": "YELLOW",
        "primary_risk_factor": "PHOSPHORUS",
        "portion_g": 60,
        "potassium_mg": 125,
        "phosphorus_mg": 175,
        "sodium_mg": 8,
        "protein_g": 6.6,
        "fluid_ml": 0,
        "portion_limit_text": "1-2 rotis per meal (~60g)",
        "actionable_clinical_tip": "Limit to 1-2 rotis per meal to manage organic phosphorus load.",
    },
    {
        "id": "food-toor-dal",
        "name": "Toor Dal",
        "hindi_name": "अरहर दाल",
        "category": "dal",
        "safety_tier": "YELLOW",
        "primary_risk_factor": "POTASSIUM",
        "portion_g": 60,
        "potassium_mg": 78,
        "phosphorus_mg": 54,
        "sodium_mg": 3,
        "protein_g": 4.8,
        "fluid_ml": 0,
        "portion_limit_text": "Half katori (60g cooked) per meal",
        "actionable_clinical_tip": "Soak dal 2 hours and discard water before cooking to leach potassium.",
    },
    {
        "id": "food-moong-dal",
        "name": "Yellow Moong Dal",
        "hindi_name": "पीली मूंग दाल",
        "category": "dal",
        "safety_tier": "YELLOW",
        "primary_risk_factor": "POTASSIUM",
        "portion_g": 60,
        "potassium_mg": 84,
        "phosphorus_mg": 60,
        "sodium_mg": 3,
        "protein_g": 4.5,
        "fluid_ml": 0,
        "portion_limit_text": "Half katori (60g cooked)",
        "actionable_clinical_tip": "Soak & rinse before cooking. Safer than besan or rajma.",
    },
    {
        "id": "food-milk",
        "name": "Cow Milk",
        "hindi_name": "गाय का दूध",
        "category": "dairy",
        "safety_tier": "YELLOW",
        "primary_risk_factor": "PHOSPHORUS",
        "portion_g": 100,
        "potassium_mg": 155,
        "phosphorus_mg": 93,
        "sodium_mg": 50,
        "protein_g": 3.3,
        "fluid_ml": 100,
        "portion_limit_text": "Max 100ml per day",
        "actionable_clinical_tip": "High in phosphorus and potassium. Keep total dairy under 100ml/day.",
    },
    {
        "id": "food-curd",
        "name": "Plain Curd (Dahi)",
        "hindi_name": "दही",
        "category": "dairy",
        "safety_tier": "YELLOW",
        "primary_risk_factor": "PHOSPHORUS",
        "portion_g": 50,
        "potassium_mg": 78,
        "phosphorus_mg": 47,
        "sodium_mg": 25,
        "protein_g": 1.8,
        "fluid_ml": 50,
        "portion_limit_text": "Half katori (50g) per meal",
        "actionable_clinical_tip": "Small portions only — combines phosphorus and potassium load.",
    },
    {
        "id": "food-tomato",
        "name": "Tomato",
        "hindi_name": "टमाटर",
        "category": "vegetable",
        "safety_tier": "YELLOW",
        "primary_risk_factor": "POTASSIUM",
        "portion_g": 60,
        "potassium_mg": 142,
        "phosphorus_mg": 14,
        "sodium_mg": 3,
        "protein_g": 0.5,
        "fluid_ml": 0,
        "portion_limit_text": "1 small tomato per meal (~60g)",
        "actionable_clinical_tip": "Moderately high potassium. Avoid tomato puree and paste.",
    },
    {
        "id": "food-onion",
        "name": "Onion (Cooked)",
        "hindi_name": "पकाया हुआ प्याज़",
        "category": "vegetable",
        "safety_tier": "YELLOW",
        "primary_risk_factor": "POTASSIUM",
        "portion_g": 30,
        "potassium_mg": 33,
        "phosphorus_mg": 9,
        "sodium_mg": 1,
        "protein_g": 0.3,
        "fluid_ml": 0,
        "portion_limit_text": "Quarter onion per meal (~30g)",
        "actionable_clinical_tip": "Use sparingly for flavor. Boil and discard water to lower potassium.",
    },
    {
        "id": "food-chicken",
        "name": "Chicken Breast (Boiled)",
        "hindi_name": "उबला चिकन",
        "category": "protein",
        "safety_tier": "YELLOW",
        "primary_risk_factor": "PHOSPHORUS",
        "portion_g": 60,
        "potassium_mg": 160,
        "phosphorus_mg": 130,
        "sodium_mg": 40,
        "protein_g": 15.0,
        "fluid_ml": 0,
        "portion_limit_text": "50-75g per meal",
        "actionable_clinical_tip": "Good protein but has phosphorus — stick to your prescribed protein grams.",
    },
    {
        "id": "food-banana-half",
        "name": "Banana (Half)",
        "hindi_name": "आधा केला",
        "category": "fruit",
        "safety_tier": "YELLOW",
        "primary_risk_factor": "POTASSIUM",
        "portion_g": 60,
        "potassium_mg": 215,
        "phosphorus_mg": 14,
        "sodium_mg": 1,
        "protein_g": 0.6,
        "fluid_ml": 0,
        "portion_limit_text": "Half banana occasionally (~60g)",
        "actionable_clinical_tip": "Very high potassium — limit strictly to half a small banana, not daily.",
    },
    {
        "id": "food-brown-rice",
        "name": "Brown Rice",
        "hindi_name": "भूरा चावल",
        "category": "grain",
        "safety_tier": "YELLOW",
        "primary_risk_factor": "PHOSPHORUS",
        "portion_g": 75,
        "potassium_mg": 59,
        "phosphorus_mg": 77,
        "sodium_mg": 4,
        "protein_g": 2.6,
        "fluid_ml": 0,
        "portion_limit_text": "Half katori (75g cooked)",
        "actionable_clinical_tip": "Higher phosphorus than white rice — prefer white rice on dialysis days.",
    },
    {
        "id": "food-idli",
        "name": "Idli",
        "hindi_name": "इडली",
        "category": "snack",
        "safety_tier": "YELLOW",
        "primary_risk_factor": "SODIUM",
        "portion_g": 100,
        "potassium_mg": 40,
        "phosphorus_mg": 65,
        "sodium_mg": 200,
        "protein_g": 4.0,
        "fluid_ml": 0,
        "portion_limit_text": "2 idlis per meal, minimal chutney",
        "actionable_clinical_tip": "Rice/urad idli itself is low potassium; sodium comes from added salt and sambar/chutney. Skip pickles and go easy on sambar.",
    },

    # ------------------ RED ------------------
    {
        "id": "food-palak-paneer",
        "name": "Palak Paneer",
        "hindi_name": "पालक पनीर",
        "category": "sabzi",
        "safety_tier": "RED",
        "primary_risk_factor": "POTASSIUM",
        "portion_g": 150,
        "potassium_mg": 650,
        "phosphorus_mg": 180,
        "sodium_mg": 350,
        "protein_g": 10.0,
        "fluid_ml": 0,
        "portion_limit_text": "Avoid",
        "actionable_clinical_tip": "Extreme potassium trigger. Spinach + paneer combination is very risky for CKD.",
    },
    {
        "id": "food-besan-chilla",
        "name": "Besan Chilla",
        "hindi_name": "बेसन चीला",
        "category": "snack",
        "safety_tier": "RED",
        "primary_risk_factor": "POTASSIUM",
        "portion_g": 100,
        "potassium_mg": 380,
        "phosphorus_mg": 200,
        "sodium_mg": 120,
        "protein_g": 8.0,
        "fluid_ml": 0,
        "portion_limit_text": "Avoid",
        "actionable_clinical_tip": "Besan (gram flour) is ~770mg potassium per 100g dry — very high for renal diet.",
    },
    {
        "id": "food-rajma",
        "name": "Rajma (Kidney Beans)",
        "hindi_name": "राजमा",
        "category": "dal",
        "safety_tier": "RED",
        "primary_risk_factor": "POTASSIUM",
        "portion_g": 100,
        "potassium_mg": 410,
        "phosphorus_mg": 140,
        "sodium_mg": 5,
        "protein_g": 8.7,
        "fluid_ml": 0,
        "portion_limit_text": "Avoid",
        "actionable_clinical_tip": "Very high potassium and phosphorus — one of the worst legumes for CKD.",
    },
    {
        "id": "food-chole",
        "name": "Chole (Chickpea Curry)",
        "hindi_name": "छोले",
        "category": "dal",
        "safety_tier": "RED",
        "primary_risk_factor": "POTASSIUM",
        "portion_g": 100,
        "potassium_mg": 290,
        "phosphorus_mg": 170,
        "sodium_mg": 200,
        "protein_g": 8.0,
        "fluid_ml": 0,
        "portion_limit_text": "Avoid",
        "actionable_clinical_tip": "High potassium and phosphorus. Also usually cooked with high sodium masalas.",
    },
    {
        "id": "food-aloo-sabzi",
        "name": "Aloo Sabzi (Potato)",
        "hindi_name": "आलू की सब्ज़ी",
        "category": "sabzi",
        "safety_tier": "RED",
        "primary_risk_factor": "POTASSIUM",
        "portion_g": 150,
        "potassium_mg": 620,
        "phosphorus_mg": 90,
        "sodium_mg": 250,
        "protein_g": 3.0,
        "fluid_ml": 0,
        "portion_limit_text": "Avoid — or double-boil first",
        "actionable_clinical_tip": "Potatoes are potassium bombs. If eating, cube-soak-boil-drain-cook to leach potassium.",
    },
    {
        "id": "food-methi-saag",
        "name": "Methi Saag",
        "hindi_name": "मेथी का साग",
        "category": "sabzi",
        "safety_tier": "RED",
        "primary_risk_factor": "POTASSIUM",
        "portion_g": 100,
        "potassium_mg": 490,
        "phosphorus_mg": 50,
        "sodium_mg": 19,
        "protein_g": 4.0,
        "fluid_ml": 0,
        "portion_limit_text": "Avoid",
        "actionable_clinical_tip": "Dark leafy greens like methi are extremely high in potassium.",
    },
    {
        "id": "food-banana-full",
        "name": "Banana (Full)",
        "hindi_name": "पूरा केला",
        "category": "fruit",
        "safety_tier": "RED",
        "primary_risk_factor": "POTASSIUM",
        "portion_g": 120,
        "potassium_mg": 430,
        "phosphorus_mg": 28,
        "sodium_mg": 2,
        "protein_g": 1.3,
        "fluid_ml": 0,
        "portion_limit_text": "Avoid",
        "actionable_clinical_tip": "One full banana can exceed your daily potassium budget on dialysis.",
    },
    {
        "id": "food-orange",
        "name": "Orange",
        "hindi_name": "संतरा",
        "category": "fruit",
        "safety_tier": "RED",
        "primary_risk_factor": "POTASSIUM",
        "portion_g": 130,
        "potassium_mg": 234,
        "phosphorus_mg": 20,
        "sodium_mg": 1,
        "protein_g": 1.2,
        "fluid_ml": 0,
        "portion_limit_text": "Limit or avoid",
        "actionable_clinical_tip": "Moderately high potassium (~180–240mg per medium fruit). Best avoided by dialysis patients and portioned carefully in pre-dialysis CKD.",
    },
    {
        "id": "food-coconut-water",
        "name": "Coconut Water",
        "hindi_name": "नारियल पानी",
        "category": "beverage",
        "safety_tier": "RED",
        "primary_risk_factor": "POTASSIUM",
        "portion_g": 200,
        "potassium_mg": 500,
        "phosphorus_mg": 40,
        "sodium_mg": 210,
        "protein_g": 1.4,
        "fluid_ml": 200,
        "portion_limit_text": "Avoid completely",
        "actionable_clinical_tip": "Very high potassium — commonly mistaken as 'healthy'. Dangerous for CKD.",
    },
    {
        "id": "food-pickle",
        "name": "Achar (Indian Pickle)",
        "hindi_name": "अचार",
        "category": "condiment",
        "safety_tier": "RED",
        "primary_risk_factor": "SODIUM",
        "portion_g": 10,
        "potassium_mg": 50,
        "phosphorus_mg": 20,
        "sodium_mg": 700,
        "protein_g": 0.2,
        "fluid_ml": 0,
        "portion_limit_text": "Avoid",
        "actionable_clinical_tip": "Extremely high sodium — causes fluid retention and hypertension.",
    },
    {
        "id": "food-papad",
        "name": "Papad",
        "hindi_name": "पापड़",
        "category": "condiment",
        "safety_tier": "RED",
        "primary_risk_factor": "SODIUM",
        "portion_g": 10,
        "potassium_mg": 120,
        "phosphorus_mg": 65,
        "sodium_mg": 600,
        "protein_g": 1.8,
        "fluid_ml": 0,
        "portion_limit_text": "Avoid",
        "actionable_clinical_tip": "One papad can have 400-600mg sodium. Avoid on renal diet.",
    },
    # ------------------ SALT SUBSTITUTES ------------------
    # Salt substitutes marketed as "low sodium" or "no salt" are almost always
    # potassium chloride (KCl) — flipping the danger from Na to K. For a
    # CKD/dialysis patient these are actively dangerous.
    #
    # Chemistry note (source of truth for the numbers below):
    #   Elemental potassium is 39.1/74.5 ≈ 0.525 of KCl's mass (K=39.10 g/mol,
    #   KCl=74.55 g/mol). A product that is X% KCl by mass contributes
    #   (X × 0.525) mg of elemental potassium per 100mg of product, NOT X mg.
    #   Elemental sodium is 22.99/58.44 ≈ 0.394 of NaCl's mass. Same rule
    #   applies. `potassium_mg` and `sodium_mg` in this file MUST always be
    #   elemental — that's the atom a renal budget is counting.
    {
        "id": "food-lo-salt-substitute",
        "name": "Lo-Salt (Salt Substitute)",
        "hindi_name": "लो-सॉल्ट (नमक विकल्प)",
        "category": "salt_substitute",
        "safety_tier": "RED",
        "primary_risk_factor": "POTASSIUM",
        "portion_g": 1,
        # 66.6% KCl × 0.525 = 350mg K per 1g product; 33.3% NaCl × 0.394 =
        # 131mg Na per 1g product.
        "potassium_mg": 350,
        "phosphorus_mg": 0,
        "sodium_mg": 131,
        "protein_g": 0,
        "fluid_ml": 0,
        "portion_limit_text": "Avoid — banned for CKD patients",
        "actionable_clinical_tip": (
            "66.6% potassium chloride blend. Just 1g gives ~350 mg elemental "
            "potassium (KCl × 0.525) — one teaspoon (~5g) crosses a dialysis "
            "patient's entire daily potassium budget. Never use."
        ),
        "source": (
            "Klinge Foods Ltd Lo-Salt ingredient declaration — 66.6% "
            "potassium chloride / 33.3% sodium chloride by mass. Elemental "
            "K = KCl × 0.525; elemental Na = NaCl × 0.394."
        ),
    },
    {
        "id": "food-nosalt-substitute",
        "name": "NoSalt / Sub-Salt (Potassium Chloride)",
        "hindi_name": "नो-सॉल्ट (पोटैशियम क्लोराइड)",
        "category": "salt_substitute",
        "safety_tier": "RED",
        "primary_risk_factor": "POTASSIUM",
        "portion_g": 1,
        # ~100% KCl × 0.525 = ~525mg elemental K per 1g product. Morton's
        # own nutrition label (630mg K per 1/4 tsp / 1.2g) confirms
        # 525mg/g within rounding, allowing for anti-caking agents.
        "potassium_mg": 525,
        "phosphorus_mg": 0,
        "sodium_mg": 0,
        "protein_g": 0,
        "fluid_ml": 0,
        "portion_limit_text": "Avoid completely — dangerous for CKD",
        "actionable_clinical_tip": (
            "~100% potassium chloride (plus trace anti-caking agents). "
            "Sold as heart-friendly for hypertensive patients but strictly "
            "banned in CKD/dialysis — can cause fatal hyperkalemia at even "
            "half-teaspoon doses."
        ),
        "source": (
            "Morton NoSalt Nutrition Facts panel — potassium 630 mg per 1/4 "
            "tsp (~1.2g), sodium 0 mg. Elemental K back-calculated as "
            "KCl × 0.525 = ~525 mg per 1g product (matches label within "
            "rounding)."
        ),
    },
    {
        "id": "food-tata-saltlite",
        "name": "Tata Salt Lite (Low-Sodium Salt)",
        "hindi_name": "टाटा साल्ट लाइट (कम-सोडियम नमक)",
        "category": "salt_substitute",
        # Per classify_from_nutrients: K=184 (>=150 → YELLOW), Na=256
        # (>=200 → YELLOW). Both YELLOW; K is the primary flag by the
        # classifier's ordering. Formula-driven, NOT hand-set.
        "safety_tier": "YELLOW",
        "primary_risk_factor": "POTASSIUM",
        "portion_g": 1,
        # 35% KCl × 0.525 = 184mg elemental K per 1g; 65% NaCl × 0.394 =
        # 256mg elemental Na per 1g.
        "potassium_mg": 184,
        "phosphorus_mg": 0,
        "sodium_mg": 256,
        "protein_g": 0,
        "fluid_ml": 0,
        "portion_limit_text": "Not renal-safe — 1g adds ~184mg K + ~256mg Na",
        "actionable_clinical_tip": (
            "~35% potassium chloride, ~65% sodium chloride. 1g gives ~184 mg "
            "elemental K (KCl × 0.525) and ~256 mg Na (NaCl × 0.394). A "
            "typical daily 3-5g use pushes K past 550-900 mg and Na past "
            "750-1300 mg — RED territory in daily practice. Use herbs and "
            "lemon instead."
        ),
        "source": (
            "Tata Consumer Products 'Tata Salt Lite' ingredient panel — "
            "sodium chloride + iodised potassium chloride. Percentage split "
            "(~35% KCl) taken from product marketing 'up to 15% less sodium' "
            "claim; PENDING verification against manufacturer spec sheet "
            "(guide_needs_sourcing.csv). Elemental K = KCl × 0.525; Na = "
            "NaCl × 0.394."
        ),
    },
    {
        "id": "food-himalayan-pink-salt",
        "name": "Himalayan Pink Salt / Rock Salt",
        "hindi_name": "सेंधा नमक",
        "category": "salt_substitute",
        "safety_tier": "RED",
        "primary_risk_factor": "SODIUM",
        "portion_g": 1,
        # ~98% NaCl × 0.394 = ~386mg elemental Na per 1g product. Stored
        # as 390 (rounded to 10s to match how other Na values are recorded).
        "potassium_mg": 3,
        "phosphorus_mg": 0,
        "sodium_mg": 390,
        "protein_g": 0,
        "fluid_ml": 0,
        "portion_limit_text": "No safer than regular salt — same limit",
        "actionable_clinical_tip": (
            "Pink/rock salt is ~98% sodium chloride — chemically nearly "
            "identical to regular table salt for sodium. Elemental Na = "
            "NaCl × 0.394 ≈ 386 mg per 1g. It's NOT a low-sodium option, "
            "despite being marketed as such. Weigh every pinch."
        ),
        "source": (
            "USDA FoodData Central + peer-reviewed mineral composition "
            "surveys of Khewra pink salt (98% NaCl by mass, remainder trace "
            "minerals). Elemental Na computed as NaCl × 0.394."
        ),
    },
    {
        "id": "food-kala-namak",
        "name": "Kala Namak (Black Salt)",
        "hindi_name": "काला नमक",
        "category": "salt_substitute",
        "safety_tier": "RED",
        "primary_risk_factor": "SODIUM",
        "portion_g": 1,
        # ~96% NaCl × 0.394 = ~378mg elemental Na per 1g product. Stored
        # as 380 (rounded to 10s).
        "potassium_mg": 5,
        "phosphorus_mg": 0,
        "sodium_mg": 380,
        "protein_g": 0,
        "fluid_ml": 0,
        "portion_limit_text": "Treat like regular salt — count every pinch",
        "actionable_clinical_tip": (
            "Kala namak is ~96% sodium chloride + sulfur compounds (that's "
            "the egg-y smell). Elemental Na = NaCl × 0.394 ≈ 378 mg per 1g "
            "— practically the same sodium load as regular salt. Not a "
            "low-sodium substitute; count every pinch."
        ),
        "source": (
            "IFCT 2017 / traditional-salt composition studies — 95-97% NaCl "
            "with sulfate residue. Elemental Na = NaCl × 0.394."
        ),
    },
    {
        "id": "food-lemon-herb-seasoning",
        "name": "Lemon-Herb Salt-Free Seasoning",
        "hindi_name": "नींबू-हर्ब मसाला (नमक रहित)",
        "category": "salt_substitute",
        "safety_tier": "GREEN",
        "primary_risk_factor": "NONE",
        "portion_g": 2,
        "potassium_mg": 25,
        "phosphorus_mg": 5,
        "sodium_mg": 0,
        "protein_g": 0.1,
        "fluid_ml": 0,
        "portion_limit_text": "Use freely as a real salt/salt-substitute alternative",
        "actionable_clinical_tip": (
            "The ONE genuinely safer 'salt substitute' — herbs, dried "
            "garlic/onion, black pepper, cumin, and citrus zest. Almost zero "
            "sodium and zero potassium. Use liberally instead of KCl-based "
            "substitutes."
        ),
        "source": (
            "Generic salt-free herb-blend nutrition panels (Mrs. Dash "
            "Original Blend, McCormick Salt-Free Garlic & Herb) — Na 0 mg, "
            "K trace. Values conservatively rounded up for K to reflect "
            "occasional garlic-powder variation."
        ),
    },

    {
        "id": "food-samosa",
        "name": "Samosa",
        "hindi_name": "समोसा",
        "category": "snack",
        "safety_tier": "RED",
        "primary_risk_factor": "SODIUM",
        "portion_g": 65,
        "potassium_mg": 300,
        "phosphorus_mg": 90,
        "sodium_mg": 460,
        "protein_g": 4.0,
        "fluid_ml": 0,
        "portion_limit_text": "Avoid",
        "actionable_clinical_tip": "Deep-fried, potato-heavy, salty — hits sodium, potassium and fluid all at once.",
    },
]


# Smart swaps — the clinical_benefit_explanation is computed at seed time
# from the actual IFCT-based nutrient deltas above so numbers stay honest.
def _by_id() -> dict:
    return {f["id"]: f for f in SEED_FOODS}


def _delta_line(trigger_id: str, alt_id: str, nutrient: str, unit: str = "mg") -> str:
    idx = _by_id()
    t, a = idx[trigger_id], idx[alt_id]
    diff = t[nutrient] - a[nutrient]
    if t[nutrient] == 0:
        pct = 0
    else:
        pct = round(diff * 100 / t[nutrient])
    name_map = {
        "potassium_mg": "potassium",
        "phosphorus_mg": "phosphorus",
        "sodium_mg": "sodium",
    }
    return (
        f"About {diff}{unit} less {name_map[nutrient]} per serving "
        f"({pct}% less than {t['name']})."
    )


SEED_SWAPS = [
    {
        "id": "swap-palak-to-lauki",
        "trigger_food_id": "food-palak-paneer",
        "recommended_swap_food_id": "food-lauki-sabzi",
        "clinical_benefit_explanation": (
            _delta_line("food-palak-paneer", "food-lauki-sabzi", "potassium_mg")
            + " Pair with 30g paneer separately for protein."
        ),
    },
    {
        "id": "swap-besan-to-moong",
        "trigger_food_id": "food-besan-chilla",
        "recommended_swap_food_id": "food-moong-dal-chilla",
        "clinical_benefit_explanation": (
            _delta_line("food-besan-chilla", "food-moong-dal-chilla", "potassium_mg")
            + " Soaked-and-rinsed yellow moong leaches out much of the potassium."
        ),
    },
    {
        "id": "swap-rajma-to-moong-dal",
        "trigger_food_id": "food-rajma",
        "recommended_swap_food_id": "food-moong-dal",
        "clinical_benefit_explanation": _delta_line(
            "food-rajma", "food-moong-dal", "potassium_mg"
        ),
    },
    {
        "id": "swap-chole-to-toor",
        "trigger_food_id": "food-chole",
        "recommended_swap_food_id": "food-toor-dal",
        "clinical_benefit_explanation": (
            _delta_line("food-chole", "food-toor-dal", "potassium_mg")
            + " Also cuts sodium substantially when cooked at home with light salt."
        ),
    },
    {
        "id": "swap-aloo-to-tinda",
        "trigger_food_id": "food-aloo-sabzi",
        "recommended_swap_food_id": "food-tinda",
        "clinical_benefit_explanation": _delta_line(
            "food-aloo-sabzi", "food-tinda", "potassium_mg"
        ),
    },
    {
        "id": "swap-methi-to-cabbage",
        "trigger_food_id": "food-methi-saag",
        "recommended_swap_food_id": "food-cabbage",
        "clinical_benefit_explanation": _delta_line(
            "food-methi-saag", "food-cabbage", "potassium_mg"
        ),
    },
    {
        "id": "swap-banana-to-apple",
        "trigger_food_id": "food-banana-full",
        "recommended_swap_food_id": "food-apple",
        "clinical_benefit_explanation": _delta_line(
            "food-banana-full", "food-apple", "potassium_mg"
        ),
    },
    {
        "id": "swap-orange-to-papaya",
        "trigger_food_id": "food-orange",
        "recommended_swap_food_id": "food-papaya",
        "clinical_benefit_explanation": (
            _delta_line("food-orange", "food-papaya", "potassium_mg")
            + " Papaya also has less citric acid load than orange."
        ),
    },
    {
        "id": "swap-coconut-to-cucumber",
        "trigger_food_id": "food-coconut-water",
        "recommended_swap_food_id": "food-cucumber",
        "clinical_benefit_explanation": (
            _delta_line("food-coconut-water", "food-cucumber", "potassium_mg")
            + " Also removes ~"
            + str(_by_id()["food-coconut-water"]["sodium_mg"] - _by_id()["food-cucumber"]["sodium_mg"])
            + "mg of sodium and 200ml of fluid load."
        ),
    },
    {
        "id": "swap-samosa-to-idli",
        "trigger_food_id": "food-samosa",
        "recommended_swap_food_id": "food-idli",
        "clinical_benefit_explanation": (
            _delta_line("food-samosa", "food-idli", "sodium_mg")
            + " Plus no deep-frying and ~"
            + str(_by_id()["food-samosa"]["potassium_mg"] - _by_id()["food-idli"]["potassium_mg"])
            + "mg less potassium."
        ),
    },
]
