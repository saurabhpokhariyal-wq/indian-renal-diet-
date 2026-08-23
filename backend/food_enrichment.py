"""Turn a raw `foods` doc into a stage-personalised `FoodOut`.

Split out from routes so the meal-log / weekly-report / scan endpoints can all
reuse the same enrichment without pulling in FastAPI route code.
"""
from __future__ import annotations

from typing import Optional, Set

from db import db
from personalization import personal_tier_for, personalized_note_for
from schemas import FoodOut, Stage


async def get_user_favorite_ids(user: Optional[dict]) -> Set[str]:
    if not user:
        return set()
    ids = [
        f["food_id"]
        async for f in db.favorites.find(
            {"user_id": user["id"]}, {"_id": 0, "food_id": 1}
        )
    ]
    return set(ids)


def enrich_food_sync(food: dict, user: Optional[dict], fav_ids: Set[str]) -> FoodOut:
    stage: Stage = (user or {}).get("stage", "unknown")  # type: ignore
    return FoodOut(
        id=food["id"],
        name=food["name"],
        hindi_name=food["hindi_name"],
        category=food["category"],
        safety_tier=food["safety_tier"],
        primary_risk_factor=food["primary_risk_factor"],
        portion_limit_text=food["portion_limit_text"],
        actionable_clinical_tip=food["actionable_clinical_tip"],
        portion_g=food.get("portion_g", 0),
        potassium_mg=food.get("potassium_mg", 0),
        phosphorus_mg=food.get("phosphorus_mg", 0),
        sodium_mg=food.get("sodium_mg", 0),
        protein_g=food.get("protein_g", 0),
        fluid_ml=food.get("fluid_ml", 0),
        personal_tier=personal_tier_for(food, stage),
        personalized_note=personalized_note_for(food, stage),
        serving_disclaimer=food.get("serving_disclaimer"),
        is_favorite=food["id"] in fav_ids,
        brand=food.get("brand"),
        source=food.get("source"),
        tier_override=food.get("tier_override"),
        override_reason=food.get("override_reason"),
        auto_rescaled=food.get("auto_rescaled"),
        data_quality_flag=food.get("data_quality_flag"),
    )


async def enrich_food(food: dict, user: Optional[dict]) -> FoodOut:
    """Single-food enrichment (fetches favorites for user if any)."""
    fav_ids = await get_user_favorite_ids(user) if user else set()
    return enrich_food_sync(food, user, fav_ids)
