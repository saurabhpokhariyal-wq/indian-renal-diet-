"""Weekly report — 7-day rolling K/P/Na/protein/fluid summary + tier counts."""
from datetime import date as date_cls, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from db import db
from personalization import limits_for_user, personal_tier_for
from schemas import NutrientTotals, WeeklyReportDay, WeeklyReportResponse
from security import get_current_user

router = APIRouter()


@router.get("/reports/weekly", response_model=WeeklyReportResponse)
async def weekly_report(
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD (default: today)"),
    current_user=Depends(get_current_user),
):
    try:
        end = date_cls.fromisoformat(end_date) if end_date else date_cls.today()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid end_date")
    start = end - timedelta(days=6)
    start_s, end_s = start.isoformat(), end.isoformat()

    logs = [
        log
        async for log in db.meal_logs.find(
            {"user_id": current_user["id"], "date": {"$gte": start_s, "$lte": end_s}}, {"_id": 0}
        )
    ]

    # Batch fetch foods with $in
    food_ids = list({log["food_id"] for log in logs})
    foods_by_id: dict = {}
    if food_ids:
        async for f in db.foods.find({"id": {"$in": food_ids}}, {"_id": 0}):
            foods_by_id[f["id"]] = f

    day_map: dict = {(start + timedelta(days=i)).isoformat(): {"green": 0, "yellow": 0, "red": 0} for i in range(7)}
    name_by_tier: dict = {"GREEN": {}, "YELLOW": {}, "RED": {}}
    totals = {"GREEN": 0, "YELLOW": 0, "RED": 0}
    nutrient_totals = {"potassium_mg": 0.0, "phosphorus_mg": 0.0, "sodium_mg": 0.0, "protein_g": 0.0, "fluid_ml": 0.0}

    for log in logs:
        food = foods_by_id.get(log["food_id"])
        if not food:
            continue
        qty = float(log.get("quantity_multiplier", 1.0) or 1.0)
        tier = personal_tier_for(food, current_user.get("stage", "unknown"))
        totals[tier] += 1
        bucket = day_map.setdefault(log["date"], {"green": 0, "yellow": 0, "red": 0})
        bucket[tier.lower()] += 1
        name_by_tier[tier][food["name"]] = name_by_tier[tier].get(food["name"], 0) + 1
        for k in nutrient_totals:
            nutrient_totals[k] += float(food.get(k, 0) or 0) * qty

    def top(d: dict, n: int = 3) -> List[str]:
        return [k for k, _ in sorted(d.items(), key=lambda kv: kv[1], reverse=True)[:n]]

    days = [
        WeeklyReportDay(date=d, green=v["green"], yellow=v["yellow"], red=v["red"])
        for d, v in sorted(day_map.items())
    ]
    avg_daily = NutrientTotals(
        potassium_mg=round(nutrient_totals["potassium_mg"] / 7, 1),
        phosphorus_mg=round(nutrient_totals["phosphorus_mg"] / 7, 1),
        sodium_mg=round(nutrient_totals["sodium_mg"] / 7, 1),
        protein_g=round(nutrient_totals["protein_g"] / 7, 1),
        fluid_ml=round(nutrient_totals["fluid_ml"] / 7, 1),
    )
    return WeeklyReportResponse(
        start_date=start_s,
        end_date=end_s,
        total_meals=totals["GREEN"] + totals["YELLOW"] + totals["RED"],
        green=totals["GREEN"],
        yellow=totals["YELLOW"],
        red=totals["RED"],
        days=days,
        top_safe_foods=top(name_by_tier["GREEN"]),
        top_avoid_foods=top(name_by_tier["RED"]),
        avg_daily=avg_daily,
        limits=limits_for_user(current_user),
    )
