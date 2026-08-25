"""Pydantic v2 models + shared type aliases.

Kept in one file so routes never have to guess where a model lives, and any
UI-facing shape change here is auditable in one diff.
"""
from __future__ import annotations

from datetime import date as date_cls
from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

# ---- Shared enums / literals ----
Stage = Literal["pre_dialysis", "dialysis", "unknown"]
MealType = Literal["breakfast", "lunch", "dinner", "snack", "meal"]
NutrientUnit = Literal["mg", "mEq"]


# ---- Auth ----
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class DoctorLimits(BaseModel):
    potassium_mg: Optional[float] = Field(default=None, ge=0)
    phosphorus_mg: Optional[float] = Field(default=None, ge=0)
    sodium_mg: Optional[float] = Field(default=None, ge=0)
    fluid_ml: Optional[float] = Field(default=None, ge=0)
    protein_g: Optional[float] = Field(default=None, ge=0)


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    stage: Stage = "unknown"
    diabetic: bool = False
    doctor_limits: Optional[DoctorLimits] = None
    nutrient_unit: NutrientUnit = "mg"


UserOut.model_rebuild()


class StageUpdate(BaseModel):
    stage: Stage


class ProfileUpdate(BaseModel):
    diabetic: Optional[bool] = None
    doctor_limits: Optional[DoctorLimits] = None
    nutrient_unit: Optional[NutrientUnit] = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---- Foods ----
class FoodOut(BaseModel):
    id: str
    name: str
    hindi_name: str
    category: str
    safety_tier: str
    primary_risk_factor: str
    portion_limit_text: str
    actionable_clinical_tip: str
    portion_g: float = 0
    potassium_mg: float = 0
    phosphorus_mg: float = 0
    sodium_mg: float = 0
    protein_g: float = 0
    fluid_ml: float = 0
    personal_tier: Optional[str] = None
    personalized_note: Optional[str] = None
    serving_disclaimer: Optional[str] = None
    is_favorite: bool = False
    brand: Optional[str] = None
    source: Optional[str] = None
    tier_override: Optional[bool] = None
    override_reason: Optional[str] = None
    auto_rescaled: Optional[bool] = None
    data_quality_flag: Optional[str] = None


class SwapOut(BaseModel):
    id: str
    trigger_food_id: str
    recommended_swap_food_id: str
    recommended_food: FoodOut
    clinical_benefit_explanation: str


class FoodDetailOut(BaseModel):
    food: FoodOut
    swap: Optional[SwapOut] = None


class FavoriteToggleResponse(BaseModel):
    food_id: str
    is_favorite: bool


# ---- Meal logs ----
class MealLogCreate(BaseModel):
    food_id: str
    date: str
    meal_type: MealType = "meal"
    quantity_multiplier: float = Field(default=1.0, gt=0.0, le=10.0)

    @field_validator("date")
    @classmethod
    def _validate_date(cls, v: str) -> str:
        try:
            date_cls.fromisoformat(v)
        except (ValueError, TypeError) as e:
            raise ValueError("date must be a valid YYYY-MM-DD calendar date") from e
        return v


class MealLogOut(BaseModel):
    id: str
    food_id: str
    date: str
    meal_type: str
    quantity_multiplier: float = 1.0
    food: FoodOut
    created_at: str


# ---- AI: log-meal ----
class AiLogMealRequest(BaseModel):
    """Free-text meal description to parse into loggable items.

    Example: {"text":"2 rotis, 1 katori dal, small bowl curd",
              "date":"2026-08-20", "meal_type":"lunch", "lang":"en"}
    """
    text: str
    date: str
    meal_type: MealType = "meal"
    lang: Optional[Literal["en", "hi", "ta", "bn", "mr"]] = "en"

    @field_validator("date")
    @classmethod
    def _v_date(cls, v: str) -> str:
        try:
            date_cls.fromisoformat(v)
        except (ValueError, TypeError) as e:
            raise ValueError("date must be a valid YYYY-MM-DD calendar date") from e
        return v


class ParsedMealItem(BaseModel):
    """One item extracted from the user's free-text meal description.

    * `item_text` is the exact user words (never LLM-invented food name).
    * `quantity_multiplier` is what the LLM extracted from phrases like
      "2 rotis" (→ 2.0) or "half katori" (→ 0.5).
    * `outcome` tells the frontend what to render:
        - "match_single": one confident match; needs one-tap confirmation
        - "match_multiple": several candidates; user must pick
        - "no_match": nothing found; user can search manually or skip
    * `candidates` is a compact list of {food_id, name, hindi_name, safety_tier}
      the frontend can render as choices. Nutrient totals are NEVER included
      here — they're computed at commit time from the canonical food doc.
    """
    item_text: str
    quantity_multiplier: float = Field(default=1.0, gt=0.0, le=10.0)
    outcome: Literal["match_single", "match_multiple", "no_match"]
    candidates: List[dict] = []


class AiLogMealResponse(BaseModel):
    parsed_items: List[ParsedMealItem]
    notice: Optional[str] = None


# ---- AI: ask ----
class AiAskRequest(BaseModel):
    question: str
    lang: Optional[Literal["en", "hi", "ta", "bn", "mr"]] = "en"


class AiAskResponse(BaseModel):
    answer: str


# ---- Scan ----
class FoodScanRequest(BaseModel):
    image_base64: str


class BarcodeScanRequest(BaseModel):
    barcode: str = Field(min_length=6, max_length=32)


class FoodScanResponse(BaseModel):
    food_name: str
    hindi_name: Optional[str] = None
    safety_tier: str
    primary_risk_factor: str
    portion_limit_text: str
    clinical_tip: str
    matched_food_id: Optional[str] = None
    barcode: Optional[str] = None
    brand: Optional[str] = None
    portion_g: Optional[float] = None
    potassium_mg: Optional[float] = None
    phosphorus_mg: Optional[float] = None
    sodium_mg: Optional[float] = None
    protein_g: Optional[float] = None
    raw: Optional[str] = None


# ---- Reports / summaries ----
class NutrientTotals(BaseModel):
    potassium_mg: float
    phosphorus_mg: float
    sodium_mg: float
    protein_g: float
    fluid_ml: float


class NutrientLimits(BaseModel):
    potassium_mg: float = 2000
    phosphorus_mg: float = 1000
    sodium_mg: float = 2000
    fluid_ml: float = 2000
    protein_g: float = 60


class MealLogSummary(BaseModel):
    date: str
    total_meals: int
    totals: NutrientTotals
    limits: NutrientLimits


class WeeklyReportDay(BaseModel):
    date: str
    green: int
    yellow: int
    red: int


class WeeklyReportResponse(BaseModel):
    start_date: str
    end_date: str
    total_meals: int
    green: int
    yellow: int
    red: int
    days: List[WeeklyReportDay]
    top_safe_foods: List[str]
    top_avoid_foods: List[str]
    avg_daily: NutrientTotals
    limits: NutrientLimits
