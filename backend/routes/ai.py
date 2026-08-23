"""`/ai/ask` (grounded chat) + `/ai/log-meal` (natural-language meal parser)."""
import json as _json
import logging
import re
from typing import List, Literal

from fastapi import APIRouter, Depends, HTTPException, Request

from ai_service import (
    AI_SYSTEM_PROMPT_BASE,
    LOG_MEAL_EXTRACT_PROMPT,
    _build_ai_context,
    _build_grounded_food_block,
    _find_relevant_foods,
)
from config import EMERGENT_LLM_KEY
from personalization import personal_tier_for
from schemas import (
    AiAskRequest,
    AiAskResponse,
    AiLogMealRequest,
    AiLogMealResponse,
    ParsedMealItem,
)
from security import _rate_key_user, get_current_user, limiter

router = APIRouter()
logger = logging.getLogger("renal-diet")


@router.post("/ai/ask", response_model=AiAskResponse)
@limiter.limit("10/minute", key_func=_rate_key_user)
async def ai_ask(request: Request, body: AiAskRequest, current_user=Depends(get_current_user)):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=503, detail="AI service is not configured")
    question = (body.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    lang = body.lang or "en"
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        patient_ctx = await _build_ai_context(current_user, lang)
        grounded = await _build_grounded_food_block(question, current_user)
        system_prompt = AI_SYSTEM_PROMPT_BASE + patient_ctx + grounded
        session_id = f"user-{current_user['id']}-{lang}"
        chat = (
            LlmChat(api_key=EMERGENT_LLM_KEY, session_id=session_id, system_message=system_prompt)
            .with_model("anthropic", "claude-sonnet-4-5-20250929")
        )
        reply = await chat.send_message(UserMessage(text=question))
        return AiAskResponse(answer=str(reply).strip())
    except Exception:
        logger.exception("AI ask failed")
        raise HTTPException(status_code=502, detail="AI service temporarily unavailable")


def _safety_summary_for_candidate(food: dict, user: dict) -> dict:
    """Compact food summary shipped as a candidate for user confirmation. No
    computed nutrient totals — the frontend needs enough to render a choice."""
    return {
        "food_id": food["id"],
        "name": food.get("name", ""),
        "hindi_name": food.get("hindi_name", ""),
        "category": food.get("category", ""),
        "safety_tier": personal_tier_for(food, user.get("stage", "unknown")),
        "portion_limit_text": food.get("portion_limit_text", ""),
    }


async def _resolve_meal_item(item: dict, user: dict) -> ParsedMealItem:
    """Turn one {item_text, quantity_multiplier} extracted item into a
    ParsedMealItem with outcome + candidates. Reuses `_find_relevant_foods` so
    /ai/log-meal and /ai/ask share ONE retrieval implementation."""
    text = str(item.get("item_text", "")).strip()
    try:
        qty = float(item.get("quantity_multiplier", 1.0))
    except (TypeError, ValueError):
        qty = 1.0
    qty = max(0.1, min(qty, 10.0))

    if not text:
        return ParsedMealItem(
            item_text=text, quantity_multiplier=qty,
            outcome="no_match", candidates=[]
        )

    matches = await _find_relevant_foods(text, user, limit=5)
    if not matches:
        return ParsedMealItem(
            item_text=text, quantity_multiplier=qty,
            outcome="no_match", candidates=[]
        )

    candidates = [_safety_summary_for_candidate(f, user) for f in matches]
    outcome: Literal["match_single", "match_multiple"] = (
        "match_single" if len(candidates) == 1 else "match_multiple"
    )
    return ParsedMealItem(
        item_text=text, quantity_multiplier=qty,
        outcome=outcome, candidates=candidates
    )


@router.post("/ai/log-meal", response_model=AiLogMealResponse)
@limiter.limit("10/minute", key_func=_rate_key_user)
async def ai_log_meal(
    request: Request, body: AiLogMealRequest,
    current_user=Depends(get_current_user),
):
    """Parse free-text meal description into loggable items.

    Strictly retrieval-then-confirm — the LLM only extracts structure from the
    user's own words; every food identity + nutrient number comes from
    `_find_relevant_foods` against the app's verified DB. The endpoint NEVER
    writes to meal_logs on its own — the frontend renders a confirmation
    screen and calls POST /meal-logs per confirmed item.
    """
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=503, detail="AI service is not configured")
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Meal description cannot be empty")

    # 1. LLM extraction — structure only, no nutrient generation.
    extracted: List[dict] = []
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        session_id = f"user-{current_user['id']}-mealparse"
        chat = (
            LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=session_id,
                system_message=LOG_MEAL_EXTRACT_PROMPT,
            )
            .with_model("anthropic", "claude-sonnet-4-5-20250929")
        )
        raw = await chat.send_message(UserMessage(text=text))
        raw_str = str(raw).strip()
        # Strip ```json fences if the model added them.
        if raw_str.startswith("```"):
            raw_str = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_str, flags=re.IGNORECASE)
        parsed = _json.loads(raw_str)
        if isinstance(parsed, list):
            extracted = [x for x in parsed if isinstance(x, dict)]
    except Exception:
        logger.exception("Meal-text extraction failed; falling back to whole-string retrieval")
        extracted = [{"item_text": text, "quantity_multiplier": 1.0}]

    if not extracted:
        return AiLogMealResponse(
            parsed_items=[],
            notice="Couldn't identify any food items in that message. Please describe your meal like '2 rotis, 1 katori dal'.",
        )

    # 2. Retrieval per item — reuses the same _find_relevant_foods as /ai/ask.
    resolved: List[ParsedMealItem] = []
    for item in extracted[:20]:  # protective cap
        resolved.append(await _resolve_meal_item(item, current_user))

    return AiLogMealResponse(parsed_items=resolved)
