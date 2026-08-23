"""Scan-specific helpers.

`_extract_json` is monkey-patched by iter24 tests via
`patch.object(server_mod, "_extract_json", return_value=None)` — that entry
point stays re-exported from `server.py` so the existing tests keep working.
"""
from __future__ import annotations

import json
import re
from typing import List, Optional


_SCAN_SYSTEM = (
    "You are an Indian food identifier for CKD/dialysis patients. "
    "Look at the image and identify the primary Indian dish. "
    "Then classify its kidney safety. "
    "ALWAYS respond in strict JSON with this exact schema and nothing else — no markdown, no prose:\n"
    "{\n"
    '  "food_name": "English name",\n'
    '  "hindi_name": "Hindi name in Devanagari",\n'
    '  "safety_tier": "GREEN" | "YELLOW" | "RED",\n'
    '  "primary_risk_factor": "POTASSIUM" | "PHOSPHORUS" | "SODIUM" | "FLUID" | "NONE",\n'
    '  "portion_limit_text": "short portion guidance",\n'
    '  "clinical_tip": "one sentence clinical guidance"\n'
    "}\n"
    "If you cannot identify a food, still return the schema with food_name='Unknown', safety_tier='YELLOW' and a caution tip."
)


# UNVERIFIED marker constants — used when we truly don't know the food.
# See /ai/ask iter-22 grounding fix and /scan iter-24: we must not return a
# colored tier when there's no verified DB match, or the patient gets a
# confident GREEN/YELLOW/RED that the app has no basis for.
UNVERIFIED_TIER = "UNVERIFIED"
UNVERIFIED_PORTION = (
    "Not in our verified database yet — please check with your dietitian before eating."
)
UNVERIFIED_TIP = (
    "We couldn't confidently match this to a verified dish. Try the manual food search, "
    "or ask your care team."
)


def _extract_json(text: str) -> Optional[dict]:
    """Best-effort JSON extractor from an LLM reply that may be wrapped in
    markdown / prose. Returns None on failure — callers must fall through to
    the UNVERIFIED path in that case."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _classify_from_nutrients(k_mg: float, p_mg: float, na_mg: float) -> tuple[str, str]:
    """Return (safety_tier, primary_risk_factor) from per-portion nutrients.

    IMPORTANT: if every nutrient is 0 the caller almost certainly received
    a product with no nutritional data on Open Food Facts — returning GREEN
    in that case would falsely reassure the patient. Fall back to UNVERIFIED
    with primary_risk=NONE so the frontend renders a neutral (not green)
    badge and the label makes the app's ignorance explicit.
    """
    if not (k_mg or p_mg or na_mg):
        return "UNVERIFIED", "NONE"
    reasons: List[tuple[str, str, int]] = []  # (risk, tier, severity)
    if k_mg >= 300:
        reasons.append(("POTASSIUM", "RED", 3))
    elif k_mg >= 150:
        reasons.append(("POTASSIUM", "YELLOW", 2))
    if na_mg >= 400:
        reasons.append(("SODIUM", "RED", 3))
    elif na_mg >= 200:
        reasons.append(("SODIUM", "YELLOW", 2))
    if p_mg >= 150:
        reasons.append(("PHOSPHORUS", "RED", 3))
    elif p_mg >= 100:
        reasons.append(("PHOSPHORUS", "YELLOW", 2))
    if not reasons:
        return "GREEN", "NONE"
    reasons.sort(key=lambda r: r[2], reverse=True)
    return reasons[0][1], reasons[0][0]
