"""Vitamin, supplement and dietary-myth guidance for CKD/dialysis patients.

Consolidated into ONE grounded knowledge block so /ai/ask can answer questions
like "Should I take multivitamins?" or "Is coconut water actually good for
kidneys?" without needing a separate 'Learn' tab (see iter-26 nav
consolidation rule: fold into unified Search/Ask AI, do NOT add new screens).

Sources: KDOQI 2020 Nutrition in CKD, ISN GN-CKD Handbook, ISPD Peritoneal
Dialysis Nutrition Guidelines, and NKF-KDIGO Vitamin & Mineral supplement
recommendations. Content is *educational and generalized* — the AI still
appends a "check with your nephrologist" reminder per the base prompt.
"""

VITAMIN_GUIDANCE = [
    {
        "topic": "Water-soluble vitamins (B-complex, C, folate) on dialysis",
        "guidance": (
            "Dialysis removes water-soluble vitamins during every session. "
            "Most dialysis patients benefit from a renal-specific multivitamin "
            "(B1, B2, B6, B12, folate, vitamin C ≤100mg). AVOID standard "
            "over-the-counter multivitamins — they usually contain too much "
            "vitamin A (fat-soluble, accumulates) and can contain potassium."
        ),
        "stages": ["dialysis"],
    },
    {
        "topic": "Vitamin C — the hidden potassium risk",
        "guidance": (
            "Standard vitamin C supplements are usually safe under 100 mg/day. "
            "High-dose vitamin C (>500 mg) is metabolized to oxalate and can "
            "damage kidneys; effervescent tablets also add ~300 mg sodium per "
            "tablet. Skip fizzy 'immunity boosters' — get vitamin C from small "
            "portions of amla, guava, or bell pepper."
        ),
        "stages": ["pre_dialysis", "dialysis"],
    },
    {
        "topic": "Vitamin D and bone health",
        "guidance": (
            "Active vitamin D (calcitriol / alfacalcidol) is often prescribed "
            "by nephrologists for renal bone disease — but only if your PTH "
            "and calcium levels support it. Do NOT self-supplement with "
            "over-the-counter cholecalciferol without checking with your "
            "nephrologist; excess can raise calcium × phosphorus product."
        ),
        "stages": ["pre_dialysis", "dialysis"],
    },
    {
        "topic": "Vitamin A, E and K — fat-soluble supplements",
        "guidance": (
            "Fat-soluble vitamins accumulate in kidney disease. AVOID standalone "
            "vitamin A supplements — toxicity is common in dialysis. Vitamin E "
            "and K supplements are also usually unnecessary. Get these vitamins "
            "from food (small amounts of paneer, ghee, eggs) rather than pills."
        ),
        "stages": ["pre_dialysis", "dialysis"],
    },
    {
        "topic": "Iron supplements",
        "guidance": (
            "Iron deficiency is common in CKD due to reduced erythropoietin. "
            "Take iron supplements only if your doctor prescribes them based on "
            "ferritin/TSAT labs. Take iron 2 hours apart from phosphate binders "
            "or milk-based drinks — those block absorption."
        ),
        "stages": ["pre_dialysis", "dialysis"],
    },
    {
        "topic": "Calcium supplements",
        "guidance": (
            "Some phosphate binders (calcium acetate, calcium carbonate) are "
            "already calcium-based — never add extra OTC calcium on top without "
            "your doctor's OK. Excess calcium worsens vascular calcification."
        ),
        "stages": ["pre_dialysis", "dialysis"],
    },
    {
        "topic": "Herbal, ayurvedic and 'kidney cleanse' supplements",
        "guidance": (
            "Never take herbal 'kidney cleanse' products, Punarnava, Gokshura, "
            "Chandraprabha vati, star fruit / bilimbi extracts, or noni juice "
            "without your nephrologist's clearance — several are nephrotoxic or "
            "hyperkalemic. Bring the product bottle to your next appointment."
        ),
        "stages": ["pre_dialysis", "dialysis", "unknown"],
    },
    {
        "topic": "Protein powders and 'gym' supplements",
        "guidance": (
            "Whey and pea protein powders are usually too concentrated in "
            "phosphorus, potassium and total protein for a CKD patient. Creatine "
            "raises serum creatinine and confuses your labs — avoid. If you need "
            "more protein (typically on dialysis), egg whites and small pieces "
            "of grilled chicken/fish are the safest sources."
        ),
        "stages": ["pre_dialysis", "dialysis"],
    },
]

DIETARY_MYTHS = [
    {
        "myth": "'Coconut water is natural and healthy for kidneys.'",
        "reality": (
            "FALSE. 200ml of coconut water contains ~500 mg potassium — that "
            "alone crosses a dialysis patient's whole daily potassium budget. "
            "Never drink coconut water for kidney health."
        ),
    },
    {
        "myth": "'All bananas must be avoided in CKD.'",
        "reality": (
            "Partly true. A whole banana (~430 mg K) is unsafe, but half a "
            "SMALL banana (~215 mg K) can occasionally fit into a pre-dialysis "
            "K budget. Never a daily choice; substitute with apple or pear."
        ),
    },
    {
        "myth": "'Lemon water / apple cider vinegar dissolves kidney stones and cleans kidneys.'",
        "reality": (
            "There is no evidence any drink 'cleans' or 'repairs' kidneys. "
            "Extra fluid can actually be harmful for dialysis patients on "
            "fluid restriction."
        ),
    },
    {
        "myth": "'Dals and lentils must be completely avoided.'",
        "reality": (
            "Not true across the board. Rajma, chole, urad and lobia are "
            "high in K and P — avoid. But soaked-and-rinsed yellow moong dal "
            "(cook, discard first boil water) and small portions of toor dal "
            "are usually safe. Portion size matters more than a blanket ban."
        ),
    },
    {
        "myth": "'Pink Himalayan salt / sendha namak is lower in sodium than table salt.'",
        "reality": (
            "FALSE. Pink salt is ~98% sodium chloride — chemically nearly "
            "identical to regular table salt. It provides no sodium benefit. "
            "Watch the pinch."
        ),
    },
    {
        "myth": "'Low-sodium salt or salt substitutes are safe alternatives.'",
        "reality": (
            "DANGEROUS. Most 'low-sodium' salts (Lo-Salt, NoSalt, Tata Salt "
            "Lite) replace sodium with POTASSIUM chloride. Just 1g of Lo-Salt "
            "has ~660 mg potassium. Use herbs, lemon, spices, garlic and "
            "black pepper instead."
        ),
    },
    {
        "myth": "'Drinking lots of water is good for kidneys — even on dialysis.'",
        "reality": (
            "Not on dialysis. Fluid restriction (usually 1000-1500 ml/day "
            "including all drinks and soups) is one of the tightest constraints "
            "on hemodialysis, because your kidneys are no longer removing "
            "water. Weigh yourself daily and match doctor's fluid target."
        ),
    },
    {
        "myth": "'Milk is a complete food — the more the better.'",
        "reality": (
            "One cup of milk (~200 ml) has ~310 mg potassium AND ~186 mg "
            "phosphorus — both very high. Keep total dairy under 100 ml/day. "
            "Egg white is a better daily protein choice."
        ),
    },
    {
        "myth": "'Brown rice and multigrain roti are always healthier than white rice.'",
        "reality": (
            "Not for CKD. Whole grains carry ~2× the phosphorus of refined "
            "grains. White rice, suji, maida-based roti and vermicelli are "
            "actually kinder to CKD kidneys. Rotate whole wheat atta with "
            "white rice — don't switch fully to multigrain."
        ),
    },
    {
        "myth": "'ORS / electrolyte drinks are safe for kidney patients when I feel weak.'",
        "reality": (
            "ORS packets contain ~250 mg potassium and ~800 mg sodium per "
            "serving — both dangerous for CKD. Do NOT self-medicate weakness "
            "with ORS. Call your nephrologist first."
        ),
    },
]


def get_vitamin_myth_context(stage: str) -> str:
    """Return the vitamin + myth guidance block for the given CKD stage.

    Stage-aware filtering ensures pre-dialysis patients don't receive
    dialysis-specific supplement advice.
    """
    lines = [
        "\n\n---\nVITAMIN, SUPPLEMENT & MYTH REFERENCE "
        "(use when the user asks about vitamins, supplements, minerals, "
        "'natural remedies', or nutrition myths — quote the specific point "
        "that matches their question; do NOT dump the whole list):",
        "\nVITAMINS & SUPPLEMENTS:",
    ]
    for item in VITAMIN_GUIDANCE:
        if stage in item["stages"]:
            lines.append(f"- {item['topic']}: {item['guidance']}")

    lines.append("\nCOMMON DIETARY MYTHS TO CORRECT:")
    for m in DIETARY_MYTHS:
        lines.append(f"- {m['myth']} → {m['reality']}")
    return "\n".join(lines)
