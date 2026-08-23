"""Favorites toggle."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError

from db import db
from schemas import FavoriteToggleResponse
from security import get_current_user

router = APIRouter()


@router.post("/favorites/{food_id}", response_model=FavoriteToggleResponse)
async def toggle_favorite(food_id: str, current_user=Depends(get_current_user)):
    food = await db.foods.find_one({"id": food_id})
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    existing = await db.favorites.find_one({"user_id": current_user["id"], "food_id": food_id})
    if existing:
        await db.favorites.delete_one({"user_id": current_user["id"], "food_id": food_id})
        return FavoriteToggleResponse(food_id=food_id, is_favorite=False)
    try:
        await db.favorites.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "food_id": food_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    except DuplicateKeyError:
        pass
    return FavoriteToggleResponse(food_id=food_id, is_favorite=True)
