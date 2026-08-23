"""Meal-log CRUD + per-day nutrient summary."""
import uuid
from datetime import date as date_cls, datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from db import db
from food_enrichment import enrich_food_sync, get_user_favorite_ids
from personalization import limits_for_user
from schemas import (
    MealLogCreate,
    MealLogOut,
    MealLogSummary,
    NutrientTotals,
)
from security import get_current_user

router = APIRouter()


@router.get("/meal-logs/summary", response_model=MealLogSummary)
async def meal_log_summary(
    date: str = Query(..., description="YYYY-MM-DD"),
    current_user=Depends(get_current_user),
):
    try:
        date_cls.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be a valid YYYY-MM-DD calendar date")

    logs = [
        log
        async for log in db.meal_logs.find(
            {"user_id": current_user["id"], "date": date}, {"_id": 0}
        )
    ]
    totals = {"potassium_mg": 0.0, "phosphorus_mg": 0.0, "sodium_mg": 0.0, "protein_g": 0.0, "fluid_ml": 0.0}
    if logs:
        food_ids = list({log["food_id"] for log in logs})
        foods_by_id: dict = {}
        async for f in db.foods.find({"id": {"$in": food_ids}}, {"_id": 0}):
            foods_by_id[f["id"]] = f
        for log in logs:
            food = foods_by_id.get(log["food_id"])
            if not food:
                continue
            qty = float(log.get("quantity_multiplier", 1.0) or 1.0)
            for k in totals:
                totals[k] += float(food.get(k, 0) or 0) * qty

    return MealLogSummary(
        date=date,
        total_meals=len(logs),
        totals=NutrientTotals(
            potassium_mg=round(totals["potassium_mg"], 1),
            phosphorus_mg=round(totals["phosphorus_mg"], 1),
            sodium_mg=round(totals["sodium_mg"], 1),
            protein_g=round(totals["protein_g"], 1),
            fluid_ml=round(totals["fluid_ml"], 1),
        ),
        limits=limits_for_user(current_user),
    )


@router.get("/meal-logs", response_model=List[MealLogOut])
async def list_meal_logs(
    date: str = Query(..., description="YYYY-MM-DD"),
    current_user=Depends(get_current_user),
):
    try:
        date_cls.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be a valid YYYY-MM-DD calendar date")

    logs = [
        log
        async for log in db.meal_logs.find(
            {"user_id": current_user["id"], "date": date}, {"_id": 0}
        ).sort("created_at", 1)
    ]
    if not logs:
        return []

    food_ids = list({log["food_id"] for log in logs})
    foods_by_id: dict = {}
    async for f in db.foods.find({"id": {"$in": food_ids}}, {"_id": 0}):
        foods_by_id[f["id"]] = f

    fav_ids = await get_user_favorite_ids(current_user)

    out: List[MealLogOut] = []
    for log in logs:
        food = foods_by_id.get(log["food_id"])
        if not food:
            continue
        out.append(MealLogOut(
            id=log["id"],
            food_id=log["food_id"],
            date=log["date"],
            meal_type=log.get("meal_type", "meal"),
            quantity_multiplier=float(log.get("quantity_multiplier", 1.0)),
            food=enrich_food_sync(food, current_user, fav_ids),
            created_at=log["created_at"],
        ))
    return out


@router.post("/meal-logs", response_model=MealLogOut)
async def create_meal_log(body: MealLogCreate, current_user=Depends(get_current_user)):
    food = await db.foods.find_one({"id": body.food_id}, {"_id": 0})
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    log = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "food_id": body.food_id,
        "date": body.date,
        "meal_type": body.meal_type,
        "quantity_multiplier": float(body.quantity_multiplier),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.meal_logs.insert_one(log)
    fav_ids = await get_user_favorite_ids(current_user)
    return MealLogOut(
        id=log["id"],
        food_id=log["food_id"],
        date=log["date"],
        meal_type=log["meal_type"],
        quantity_multiplier=log["quantity_multiplier"],
        food=enrich_food_sync(food, current_user, fav_ids),
        created_at=log["created_at"],
    )


@router.delete("/meal-logs/{log_id}")
async def delete_meal_log(log_id: str, current_user=Depends(get_current_user)):
    res = await db.meal_logs.delete_one({"id": log_id, "user_id": current_user["id"]})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Log not found")
    return {"success": True}
