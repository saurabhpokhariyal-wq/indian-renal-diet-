"""Foods listing + detail routes."""
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from db import db
from food_enrichment import enrich_food_sync, get_user_favorite_ids
from schemas import FoodDetailOut, FoodOut, SwapOut
from security import get_optional_user

router = APIRouter()

# Frontend-facing category chips → the underlying db.foods.category values they
# fold in. Keep this dict in sync with the chips in app/(app)/search.tsx.
CATEGORY_MAP: dict = {
    "fruit":     ["fruit"],
    "vegetable": ["vegetable", "sabzi"],
    "grain":     ["grain"],
    "snack":     ["snack"],
    "protein":   ["protein", "dal", "dairy"],
    "beverage":  ["beverage"],
}


@router.get("/foods", response_model=List[FoodOut])
async def list_foods(
    q: Optional[str] = Query(None, description="Search text"),
    tier: Optional[str] = Query(None, description="Comma-separated: GREEN,YELLOW,RED"),
    category: Optional[str] = Query(
        None,
        description=(
            "Comma-separated high-level category filter, e.g. 'fruit' or "
            "'protein,dal,dairy'. Matches db.foods.category case-insensitively "
            "against any of the given tokens. See routes/foods.py::CATEGORY_MAP."
        ),
    ),
    favorites_only: bool = Query(False),
    limit: int = Query(2000, ge=1, le=5000),
    current_user=Depends(get_optional_user),
):
    query: dict = {}
    if q:
        safe_q = re.escape(q)
        query["$or"] = [
            {"name": {"$regex": safe_q, "$options": "i"}},
            {"hindi_name": {"$regex": safe_q, "$options": "i"}},
            {"category": {"$regex": safe_q, "$options": "i"}},
        ]
    if tier:
        tiers = [t.strip().upper() for t in tier.split(",") if t.strip()]
        query["safety_tier"] = {"$in": tiers}
    if category:
        # Expand each user-facing category to the underlying DB categories.
        # This mirrors the six guide screens the frontend previously had —
        # e.g. "protein" folds in the dal + dairy DB rows because the protein
        # guide already lists dals and dairy together (see protein_guide.py).
        cats: list[str] = []
        for tok in category.split(","):
            key = tok.strip().lower()
            if not key:
                continue
            cats.extend(CATEGORY_MAP.get(key, [key]))
        if cats:
            cats_pattern = "|".join(re.escape(c) for c in set(cats))
            query["category"] = {"$regex": f"^({cats_pattern})$", "$options": "i"}

    fav_ids = await get_user_favorite_ids(current_user) if current_user else set()

    if favorites_only:
        if not current_user:
            raise HTTPException(status_code=401, detail="Login required for favorites")
        if not fav_ids:
            return []
        query["id"] = {"$in": list(fav_ids)}

    cursor = db.foods.find(query, {"_id": 0}).sort("name", 1).limit(limit)
    return [enrich_food_sync(doc, current_user, fav_ids) async for doc in cursor]


@router.get("/foods/{food_id}", response_model=FoodDetailOut)
async def get_food(food_id: str, current_user=Depends(get_optional_user)):
    food = await db.foods.find_one({"id": food_id}, {"_id": 0})
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    fav_ids = await get_user_favorite_ids(current_user) if current_user else set()
    food_out = enrich_food_sync(food, current_user, fav_ids)
    swap_out: Optional[SwapOut] = None
    tier = food_out.personal_tier or food_out.safety_tier
    if tier == "RED":
        swap = await db.swaps.find_one({"trigger_food_id": food_id}, {"_id": 0})
        if not swap and food["safety_tier"] != "RED":
            green_alt = await db.foods.find_one(
                {"category": food["category"], "safety_tier": "GREEN"}, {"_id": 0}
            )
            if green_alt:
                swap = {
                    "id": f"auto-{food_id}",
                    "trigger_food_id": food_id,
                    "recommended_swap_food_id": green_alt["id"],
                    "clinical_benefit_explanation": (
                        f"For dialysis patients, {green_alt['name']} is a safer daily option in this category."
                    ),
                }
        if swap:
            rec = await db.foods.find_one({"id": swap["recommended_swap_food_id"]}, {"_id": 0})
            if rec:
                rec_out = enrich_food_sync(rec, current_user, fav_ids)
                swap_out = SwapOut(
                    id=swap["id"],
                    trigger_food_id=swap["trigger_food_id"],
                    recommended_swap_food_id=swap["recommended_swap_food_id"],
                    recommended_food=rec_out,
                    clinical_benefit_explanation=swap["clinical_benefit_explanation"],
                )
    return FoodDetailOut(food=food_out, swap=swap_out)
