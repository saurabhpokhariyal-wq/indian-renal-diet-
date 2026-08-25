"""AI helpers shared by `/ai/ask` and `/ai/log-meal`.

Contents:
- System prompts (base ask prompt, meal-parse prompt).
- Multilingual stopword set + tokenizer used across every retrieval path.
- `_find_relevant_foods` — DB retrieval by token OR-regex.
- `_find_relevant_guide_entries` — the 6 curated guide-file retrieval path,
  needed because some guide entries are reference-only and never enter
  `db.foods` (Khoa, Water Chestnut, Bael, etc.).
- `_build_ai_context` / `_build_grounded_food_block` — compose the prompt
  additions that ground the LLM to the app's verified data.
"""
from __future__ import annotations

import re
from datetime import date as date_cls
from typing import List, Optional, Set

from beverage_guide import get_beverage_guide
from db import db
from fruit_guide import get_fruit_guide
from grain_guide import get_grain_guide
from oil_guide import get_oil_guide
from personalization import (
    limits_for_user,
    personal_tier_for,
    personalized_note_for,
)
from protein_guide import get_protein_guide
from schemas import Stage
from snack_guide import get_snack_guide
from vegetable_guide import get_vegetable_guide
from vitamin_myth_guide import get_vitamin_myth_context


AI_SYSTEM_PROMPT_BASE = (
    "You are a friendly Indian Renal Diet coach for CKD/dialysis patients. "
    "You answer in short, plain language (max 6 sentences). "
    "Use warm, encouraging tone. Do NOT give medical dosages. Always add a "
    "one-line reminder to check with the patient's nephrologist for personal targets. "
    "\n\n"
    "GROUNDING RULE — READ CAREFULLY:\n"
    "You may ONLY classify a specific food as SAFE (green), CAUTION (yellow) or "
    "AVOID (red) when that exact food appears in the GROUNDED FOOD DATA block "
    "below. Do NOT estimate a food's safety from general knowledge — the app's "
    "verified database is the single source of truth, and general nutrition data "
    "for Indian foods often differs from what CKD patients actually need.\n"
    "\n"
    "If the patient asks about a food that is NOT in the GROUNDED FOOD DATA "
    "block, respond plainly: 'I don't have verified data for that food in the "
    "app's database yet. Please use the Search or Scan feature to look it up, "
    "or ask your dietitian.' — do NOT guess a tier, do NOT invent K/P/Na numbers. "
    "You can still answer general (non-food-specific) questions about CKD diet "
    "principles without needing a grounded match.\n"
    "\n"
    "When a food IS in the grounded block and its tier is RED, ALWAYS suggest a "
    "kidney-friendly Indian swap using the 'recommended swap' line if provided."
    "\n\n"
    "VITAMIN, SUPPLEMENT AND MYTH QUESTIONS:\n"
    "For questions about vitamins, supplements, herbal products, protein "
    "powders, salt substitutes, coconut water, or common CKD nutrition myths, "
    "quote from the VITAMIN, SUPPLEMENT & MYTH REFERENCE block below. Do not "
    "invent new supplement advice — that block is the source of truth. Still "
    "close with the 'check with your nephrologist' reminder."
)


LOG_MEAL_EXTRACT_PROMPT = (
    "You are a strict structural parser for a renal-diet meal logger. Extract only "
    "the eaten items and their portion counts from the user's free-text meal "
    "description. NEVER invent food names not mentioned by the user. NEVER add "
    "nutrient values, safety tiers, or database identifiers — that is done by the "
    "application after your response.\n"
    "\n"
    "Output ONLY a JSON array. Each element must be an object with exactly these "
    "keys:\n"
    "  item_text: str  — the food-item words as the user wrote them (lower-cased, "
    "singular-form OK if obvious, no editorial changes)\n"
    "  quantity_multiplier: number — count of servings. '2 rotis' → 2.0, "
    "'half katori' or 'half cup' → 0.5, 'one small bowl' → 1.0. Default 1.0 when "
    "not stated. Cap absurd values at 10.\n"
    "\n"
    "Example input: '2 rotis, 1 katori dal, small bowl of curd'\n"
    "Example output: [\n"
    '  {"item_text":"roti","quantity_multiplier":2.0},\n'
    '  {"item_text":"dal","quantity_multiplier":1.0},\n'
    '  {"item_text":"curd","quantity_multiplier":1.0}\n'
    "]\n"
    "\n"
    "Reply with ONLY the JSON array and nothing else."
)


# Common filler words across the app's 5 supported languages. Stripped from
# the user's question before token search — anything else of length >= 3 is a
# candidate search term. Missing a language's stopwords doesn't break search,
# but it *pollutes* the OR-regex with grammatical particles and degrades match
# quality specifically for that language.
_AI_STOPWORDS: Set[str] = {
    # English
    "the", "and", "for", "are", "any", "can", "you", "will", "have", "has", "had", "with",
    "this", "that", "these", "those", "what", "which", "when", "where", "how", "why",
    "safe", "eat", "ate", "eating", "food", "foods", "should", "shall", "would", "could",
    "kidney", "renal", "dialysis", "ckd", "ok", "okay", "good", "bad", "high", "low",
    "diet", "much", "many", "some", "more", "less", "than", "then", "into", "about",
    "please", "help", "give", "tell", "know", "much",
    # Hindi (Devanagari)
    "क्या", "है", "हैं", "हो", "कर", "करना", "मुझे", "मेरे", "मेरा", "मेरी",
    "खा", "खाना", "खाऊं", "खाऊँ", "सकते", "सकता", "सकती", "किसे", "किन",
    "और", "या", "के", "की", "का", "को", "में", "पर", "से", "यह", "वह",
    # Marathi (Devanagari — some overlap with Hindi is OK)
    "आहे", "आहेत", "मला", "माझे", "माझा", "माझी", "तुम्ही", "तुझे",
    "खाऊ", "खाणे", "शकतो", "शकते", "शकतात", "कशाला",
    "आणि", "किंवा", "साठी", "मध्ये", "पण", "जर", "तर",
    # Tamil script
    "நான்", "நீ", "நீங்கள்", "என்", "என்ன", "எப்படி", "எப்போது", "எங்கே", "ஏன்",
    "சாப்பிட", "சாப்பிடலாமா", "சாப்பிட்டேன்", "சாப்பாடு",
    "மற்றும்", "அல்லது", "ஒரு", "இது", "அது", "இல்லை",
    "பாதுகாப்பான", "பாதுகாப்பு", "சிறுநீரக",
    # Bengali script
    "আমি", "তুমি", "আপনি", "আমার", "তোমার", "আপনার",
    "কি", "কী", "কেন", "কেমন", "কোথায়", "কখন",
    "খাবার", "খাওয়া", "খেতে", "পারি", "পারব", "পারবো",
    "এবং", "অথবা", "একটি", "এটি", "সেটি", "নয়", "না",
    "নিরাপদ", "কিডনি", "ডায়ালিসিস",
}


def _tokenize_question(question: str) -> List[str]:
    """Shared tokenizer used by every retrieval path (foods, guides, meal-log
    extraction). Splits on whitespace/punctuation, keeps Devanagari, Tamil,
    and Bengali intact, drops multilingual stopwords, deduplicates."""
    if not question:
        return []
    cleaned = re.sub(
        r"[^\w"
        r"\u0900-\u097F"  # Devanagari
        r"\u0B80-\u0BFF"  # Tamil
        r"\u0980-\u09FF"  # Bengali
        r"]+",
        " ",
        question,
        flags=re.UNICODE,
    ).strip()
    if not cleaned:
        return []
    tokens: List[str] = []
    seen: Set[str] = set()
    for raw in cleaned.split():
        t = raw.lower()
        if len(t) < 3 or t in _AI_STOPWORDS or t in seen:
            continue
        seen.add(t)
        tokens.append(t)
    return tokens


async def _find_relevant_foods(
    question: str, user: Optional[dict], limit: int = 6
) -> List[dict]:
    """Find seeded foods that appear in the user's question.

    Splits on whitespace + punctuation, drops stopwords, then does a
    case-insensitive regex OR-match on food name / hindi_name / category.
    Returns at most `limit` distinct food docs.
    """
    tokens = _tokenize_question(question)
    if not tokens:
        return []

    or_clauses: List[dict] = []
    for tok in tokens[:12]:  # protective cap
        safe = re.escape(tok)
        or_clauses.append({"name": {"$regex": safe, "$options": "i"}})
        or_clauses.append({"hindi_name": {"$regex": safe, "$options": "i"}})
        or_clauses.append({"category": {"$regex": safe, "$options": "i"}})

    found: List[dict] = []
    ids_seen: Set[str] = set()
    async for food in db.foods.find({"$or": or_clauses}, {"_id": 0}).limit(limit * 3):
        if food["id"] in ids_seen:
            continue
        ids_seen.add(food["id"])
        found.append(food)
        if len(found) >= limit:
            break
    return found


# Guide files that /ai/ask needs to see. Kept in one place so a future addition
# (e.g. dessert_guide.py) can be plugged in by extending this list.
_GUIDE_SOURCES: List[tuple[str, str, "callable"]] = [
    ("fruit",     "fruits",     get_fruit_guide),
    ("vegetable", "vegetables", get_vegetable_guide),
    ("snack",     "snacks",     get_snack_guide),
    ("beverage",  "beverages",  get_beverage_guide),
    ("protein",   "proteins",   get_protein_guide),
    ("grain",     "grains",     get_grain_guide),
    ("oil",       "oils",       get_oil_guide),
]


def _find_relevant_guide_entries(question: str, limit: int = 6) -> List[dict]:
    """Second retrieval path — matches the same tokens against the 6 curated
    guide files. Returns a flat list of {guide, tier, entry} rows so the
    grounded-food block can render them alongside DB foods. Some guide entries
    are intentionally reference-only (linked_food_id=None) and never make it
    into db.foods, so this path is required to close the visibility gap for
    /ai/ask questions like 'is khoa safe?' or 'what about water chestnut?'."""
    tokens = _tokenize_question(question)
    if not tokens:
        return []
    lower_tokens = [t.lower() for t in tokens]
    matches: List[dict] = []
    seen: Set[str] = set()
    for guide_name, entries_key, getter in _GUIDE_SOURCES:
        try:
            guide = getter()
        except Exception:
            continue
        for tier_key, tier_data in guide.items():
            if not isinstance(tier_data, dict) or entries_key not in tier_data:
                continue
            for entry in tier_data[entries_key]:
                haystack = f"{entry.get('name','')} {entry.get('hindi','')}".lower()
                if not any(tok in haystack for tok in lower_tokens):
                    continue
                dedupe_key = f"{guide_name}|{entry.get('name','')}"
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                matches.append({
                    "guide": guide_name,
                    "tier": tier_key,
                    "entry": entry,
                })
                if len(matches) >= limit:
                    return matches
    return matches


def _lang_instruction(name: str, script: str, sample: str) -> str:
    return (
        f"\n\nIMPORTANT: The user's app language is {name}. "
        f"Answer entirely in conversational {name} ({script}). "
        f"Keep English food names in brackets where helpful, e.g. '{sample}'."
    )


async def _build_ai_context(user: dict, lang: str) -> str:
    """Compose the patient-context block appended to the AI system prompt."""
    stage = user.get("stage", "unknown") or "unknown"
    diabetic = "yes" if user.get("diabetic") else "no"
    limits = limits_for_user(user)

    today = date_cls.today().isoformat()
    logs = [
        log
        async for log in db.meal_logs.find(
            {"user_id": user["id"], "date": today}, {"_id": 0}
        )
    ]
    totals = {"potassium_mg": 0.0, "phosphorus_mg": 0.0, "sodium_mg": 0.0, "protein_g": 0.0, "fluid_ml": 0.0}
    if logs:
        food_ids = list({log["food_id"] for log in logs})
        foods_by_id: dict = {
            f["id"]: f async for f in db.foods.find({"id": {"$in": food_ids}}, {"_id": 0})
        }
        for log in logs:
            food = foods_by_id.get(log["food_id"])
            if not food:
                continue
            qty = float(log.get("quantity_multiplier", 1.0) or 1.0)
            for k in totals:
                totals[k] += float(food.get(k, 0) or 0) * qty

    stage_label = {
        "dialysis": "on dialysis (hemodialysis or peritoneal)",
        "pre_dialysis": "pre-dialysis CKD (not yet on dialysis)",
        "unknown": "CKD stage not specified",
    }[stage]

    ctx = (
        "\n\n---\nPATIENT CONTEXT (use this to personalize your advice):\n"
        f"- CKD stage: {stage_label}\n"
        f"- Diabetic: {diabetic}\n"
        f"- Preferred display unit for K and Na: {user.get('nutrient_unit','mg')} "
        f"(1 mEq K = 39.1 mg; 1 mEq Na = 23 mg — use the patient's preferred unit "
        f"first in your answer, then include the other in brackets)\n"
        f"- Daily limits: potassium {int(limits.potassium_mg)} mg "
        f"({limits.potassium_mg/39.1:.1f} mEq), "
        f"phosphorus {int(limits.phosphorus_mg)} mg, "
        f"sodium {int(limits.sodium_mg)} mg ({limits.sodium_mg/23:.1f} mEq), "
        f"protein {int(limits.protein_g)} g\n"
        f"- Today's intake so far: potassium {int(totals['potassium_mg'])} mg "
        f"({totals['potassium_mg']/39.1:.1f} mEq), "
        f"phosphorus {int(totals['phosphorus_mg'])} mg, "
        f"sodium {int(totals['sodium_mg'])} mg ({totals['sodium_mg']/23:.1f} mEq), "
        f"protein {totals['protein_g']:.1f} g, fluid {int(totals['fluid_ml'])} ml"
    )
    if user.get("diabetic"):
        ctx += "\n- Because the patient is diabetic, also flag foods with high glycemic load."

    # Vitamin + myths reference — folded into Ask AI grounded context per
    # iter-26 nav consolidation rule (no separate 'Learn' tab).
    ctx += get_vitamin_myth_context(stage)

    if lang == "hi":
        ctx += _lang_instruction("Hindi", "Devanagari", "लौकी (Lauki)")
    elif lang == "ta":
        ctx += _lang_instruction("Tamil", "Tamil script", "லௌகி (Lauki)")
    elif lang == "bn":
        ctx += _lang_instruction("Bengali", "Bengali script", "লাউ (Lauki)")
    elif lang == "mr":
        ctx += _lang_instruction("Marathi", "Devanagari", "दुधी (Lauki)")
    return ctx


async def _build_grounded_food_block(question: str, user: dict) -> str:
    """Inject authoritative food classifications matching the question.

    Also queries the 6 curated guide files so that reference-only entries
    (Khoa, Water Chestnut, Bael, etc. — no linked_food_id) are still visible
    to /ai/ask. Returns an explicit "no match" marker rather than an empty
    string when nothing matches — the base system prompt's grounding rule
    depends on this signal to stop the model from guessing."""
    foods = await _find_relevant_foods(question, user)
    guide_hits = _find_relevant_guide_entries(question, limit=6)

    if not foods and not guide_hits:
        return (
            "\n\n---\nGROUNDED FOOD DATA:\n"
            "(no matching food found in the app's verified database or curated "
            "guides for this question — per the grounding rule above, do NOT "
            "invent a tier or numbers for whatever food the user named)"
        )

    stage: Stage = user.get("stage", "unknown") or "unknown"  # type: ignore
    lines: List[str] = [
        "\n\n---\nGROUNDED FOOD DATA (authoritative — the app's food cards use these exact "
        "classifications; do NOT contradict them. If the user asks about any food below, "
        "quote the effective tier and portion limit shown here. Use the personalized tier "
        "when it differs from the base tier — that is the tier the patient sees):"
    ]
    for f in foods:
        base_tier = f["safety_tier"]
        p_tier = personal_tier_for(f, stage)
        note = personalized_note_for(f, stage)
        tier_str = base_tier if p_tier == base_tier else f"{p_tier} (personalized from base {base_tier})"
        parts = [
            f"- {f['name']} ({f['hindi_name']}) — tier: {tier_str}",
            f"  portion: {f.get('portion_limit_text','')} · per portion: "
            f"K {int(f.get('potassium_mg', 0))} mg ({f.get('potassium_mg',0)/39.1:.1f} mEq), "
            f"P {int(f.get('phosphorus_mg', 0))} mg, "
            f"Na {int(f.get('sodium_mg', 0))} mg ({f.get('sodium_mg',0)/23:.1f} mEq), "
            f"protein {f.get('protein_g', 0):.1f} g",
            f"  tip: {f.get('actionable_clinical_tip','')}",
        ]
        if note:
            parts.append(f"  personalized note: {note}")
        if p_tier == "RED":
            swap = await db.swaps.find_one({"trigger_food_id": f["id"]}, {"_id": 0})
            if swap:
                rec = await db.foods.find_one(
                    {"id": swap["recommended_swap_food_id"]}, {"_id": 0}
                )
                if rec:
                    parts.append(
                        f"  recommended swap: {rec['name']} "
                        f"— {swap.get('clinical_benefit_explanation','')}"
                    )
        lines.extend(parts)

    # Guide-only matches (reference-only, sometimes not present in db.foods).
    for hit in guide_hits:
        e = hit["entry"]
        na = e.get("sodium_mg")
        na_str = f"Na {int(na)} mg" if isinstance(na, (int, float)) else "Na not sourced"
        p_val = e.get("phosphorus_mg")
        p_str = f"P {int(p_val)} mg, " if isinstance(p_val, (int, float)) else ""
        src = f"  source: {e['source']}" if e.get("source") else ""
        lines.append(
            f"- {e.get('name','')} ({e.get('hindi','')}) — tier: {hit['tier']} [from {hit['guide']}_guide]"
        )
        lines.append(
            f"  portion: {e.get('serving','')} · per portion: "
            f"K {int(e.get('potassium_mg', 0))} mg "
            f"({e.get('potassium_meq', e.get('potassium_mg',0)/39.1):.1f} mEq), "
            f"{p_str}{na_str}"
            + (f" — HIGH SODIUM WARNING" if e.get('high_sodium') else "")
        )
        if e.get("note"):
            lines.append(f"  note: {e['note']}")
        if src:
            lines.append(src)

    return "\n".join(lines)
