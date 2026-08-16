"""Indian Renal Diet backend — FastAPI + MongoDB.

Endpoints (all prefixed /api):
- POST   /api/auth/register
- POST   /api/auth/login
- GET    /api/auth/me
- POST   /api/auth/stage
- GET    /api/foods                (?q=search&tier=RED,YELLOW,GREEN)
- GET    /api/foods/{id}
- POST   /api/favorites/{food_id}
- GET    /api/meal-logs?date=YYYY-MM-DD
- POST   /api/meal-logs
- DELETE /api/meal-logs/{id}
- GET    /api/reports/weekly
- POST   /api/ai/ask
- POST   /api/scan/food
"""

import base64
import logging
import os
import re
import uuid
from contextlib import asynccontextmanager
from datetime import date as date_cls, datetime, timedelta, timezone
from pathlib import Path
from typing import List, Literal, Optional, Set

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field, field_validator
from pymongo.errors import DuplicateKeyError
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from seed_data import SEED_FOODS, SEED_SWAPS
from seed_data_indb import SEED_FOODS_INDB
from reconciliation import reconcile_seed
from fruit_guide import get_fruit_guide, FRUIT_GUIDE
from beverage_guide import get_beverage_guide, BEVERAGE_GUIDE
from vegetable_guide import get_vegetable_guide, VEGETABLE_GUIDE
from snack_guide import get_snack_guide, SNACK_GUIDE
from protein_guide import get_protein_guide, PROTEIN_GUIDE
from grain_guide import get_grain_guide, GRAIN_GUIDE
from guide_utils import collect_needs_sourcing, write_needs_sourcing_csv

Stage = Literal["pre_dialysis", "dialysis", "unknown"]
MealType = Literal["breakfast", "lunch", "dinner", "snack", "meal"]
NutrientUnit = Literal["mg", "mEq"]

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# -------- Environment --------
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALG = "HS256"
JWT_EXPIRE_HOURS = 24 * 30  # 30 days
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
CORS_ORIGINS = [
    o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()
]

# -------- Mongo --------
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# -------- Auth utils --------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
_dummy_hash = pwd_context.hash("dummy-password-for-timing")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("renal-diet")


def hash_pw(p: str) -> str:
    return pwd_context.hash(p)


def verify_pw(p: str, h: str) -> bool:
    return pwd_context.verify(p, h)


def create_token(user_id: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    return jwt.encode({"sub": user_id, "exp": exp}, JWT_SECRET, algorithm=JWT_ALG)


def _decode_user_id(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        uid = payload.get("sub")
        return uid if isinstance(uid, str) else None
    except JWTError:
        return None


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)):
    user_id = _decode_user_id(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_optional_user(token: Optional[str] = Depends(oauth2_scheme)):
    user_id = _decode_user_id(token)
    if not user_id:
        return None
    return await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})


# -------- Rate limiter --------
def _rate_key_user(request: Request) -> str:
    """Rate-limit key per user id when available, otherwise per IP."""
    auth = request.headers.get("Authorization", "")
    token = auth.split(" ", 1)[1] if auth.lower().startswith("bearer ") else None
    uid = _decode_user_id(token)
    if uid:
        return f"user:{uid}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=get_remote_address)


# -------- Models --------
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    stage: Stage = "unknown"
    diabetic: bool = False
    doctor_limits: Optional["DoctorLimits"] = None
    nutrient_unit: NutrientUnit = "mg"


class DoctorLimits(BaseModel):
    potassium_mg: Optional[float] = Field(default=None, ge=0)
    phosphorus_mg: Optional[float] = Field(default=None, ge=0)
    sodium_mg: Optional[float] = Field(default=None, ge=0)
    fluid_ml: Optional[float] = Field(default=None, ge=0)


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


class MealLogCreate(BaseModel):
    food_id: str
    date: str
    meal_type: MealType = "meal"
    # How many "one portion" units of the food were eaten. 1.0 = one standard
    # portion (the food's stored per-portion K/P/Na/protein/fluid values).
    # Capped at 10 to catch obvious NLP-parse errors like "twenty rotis".
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
    # Frontend renders a confirmation screen; on confirm it fires
    # POST /meal-logs per item with the food_id + quantity_multiplier.
    notice: Optional[str] = None


class AiAskRequest(BaseModel):
    question: str
    lang: Optional[Literal["en", "hi", "ta", "bn", "mr"]] = "en"


class AiAskResponse(BaseModel):
    answer: str


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


class FavoriteToggleResponse(BaseModel):
    food_id: str
    is_favorite: bool


class WeeklyReportDay(BaseModel):
    date: str
    green: int
    yellow: int
    red: int


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


class MealLogSummary(BaseModel):
    date: str
    total_meals: int
    totals: NutrientTotals
    limits: NutrientLimits


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


# -------- Personalization --------
PRE_DIALYSIS_K_NOTE = (
    "Often fine before dialysis — confirm your serum potassium with your doctor. "
    "Portion sizes and lab values matter more than a blanket 'yellow' at this stage (KDOQI 2020)."
)


def personal_tier_for(food: dict, stage: Stage) -> str:
    """Compute the tier shown to the user based on their CKD stage.

    - dialysis + YELLOW + (K / P / Fluid) → tightened to RED
    - pre_dialysis + YELLOW + POTASSIUM → softened to GREEN
      (KDOQI 2020 recommends individualized K targets before dialysis;
       we never soften sodium or phosphorus items).
    - unknown stage never changes the tier.
    """
    base = food["safety_tier"]
    risk = food.get("primary_risk_factor")
    if stage == "dialysis" and base == "YELLOW" and risk in {"POTASSIUM", "PHOSPHORUS", "FLUID"}:
        return "RED"
    if stage == "pre_dialysis" and base == "YELLOW" and risk == "POTASSIUM":
        return "GREEN"
    return base


def personalized_note_for(food: dict, stage: Stage) -> Optional[str]:
    if (
        stage == "pre_dialysis"
        and food["safety_tier"] == "YELLOW"
        and food.get("primary_risk_factor") == "POTASSIUM"
    ):
        return PRE_DIALYSIS_K_NOTE
    return None


# Default daily limits by stage — used when the doctor hasn't set custom targets.
DEFAULT_LIMITS_BY_STAGE: dict = {
    "dialysis": {"potassium_mg": 2000, "phosphorus_mg": 1000, "sodium_mg": 2000, "fluid_ml": 1000},
    "pre_dialysis": {"potassium_mg": 2400, "phosphorus_mg": 1200, "sodium_mg": 2300, "fluid_ml": 2000},
    "unknown": {"potassium_mg": 2400, "phosphorus_mg": 1200, "sodium_mg": 2300, "fluid_ml": 2000},
}


def limits_for_user(user: dict) -> NutrientLimits:
    """Doctor-set limits win; otherwise stage-based defaults."""
    stage: Stage = user.get("stage", "unknown") or "unknown"  # type: ignore
    defaults = DEFAULT_LIMITS_BY_STAGE.get(stage, DEFAULT_LIMITS_BY_STAGE["unknown"])
    doc = user.get("doctor_limits") or {}
    return NutrientLimits(
        potassium_mg=float(doc.get("potassium_mg") or defaults["potassium_mg"]),
        phosphorus_mg=float(doc.get("phosphorus_mg") or defaults["phosphorus_mg"]),
        sodium_mg=float(doc.get("sodium_mg") or defaults["sodium_mg"]),
    )


async def get_user_favorite_ids(user: Optional[dict]) -> Set[str]:
    if not user:
        return set()
    ids = [f["food_id"] async for f in db.favorites.find({"user_id": user["id"]}, {"_id": 0, "food_id": 1})]
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


# -------- Lifespan --------
@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    await db.foods.create_index("id", unique=True)
    await db.foods.create_index("name")
    await db.swaps.create_index("trigger_food_id")
    await db.meal_logs.create_index([("user_id", 1), ("date", 1)])
    await db.favorites.create_index([("user_id", 1), ("food_id", 1)], unique=True)

    all_foods, recon_stats = reconcile_seed(SEED_FOODS, SEED_FOODS_INDB, logger=logger)
    reconciled_ids = {food["id"] for food in all_foods}
    for food in all_foods:
        # replace_one (not $set) so fields no longer applicable in the current
        # reconciliation (e.g. a stale auto_rescaled from an earlier run whose
        # bucket rules were looser) are removed on write.
        await db.foods.replace_one({"id": food["id"]}, food, upsert=True)
    # Purge stale seed rows from earlier iterations (e.g. dropped duplicates,
    # renamed IDs). Preserve barcode-persisted user data via source filter.
    purge = await db.foods.delete_many(
        {"id": {"$nin": list(reconciled_ids)}, "source": {"$ne": "barcode"}}
    )
    if purge.deleted_count:
        logger.info("Purged %d stale seed rows no longer in reconciled catalog", purge.deleted_count)
    for swap in SEED_SWAPS:
        await db.swaps.update_one({"id": swap["id"]}, {"$set": swap}, upsert=True)
    logger.info("Seeded %d foods, %d swaps", len(all_foods), len(SEED_SWAPS))

    # Write sanity-ceiling violations to a review CSV (Step 7 output).
    if recon_stats["sanity_violations"]:
        import csv as _csv
        review_path = Path(__file__).parent / "needs_manual_review.csv"
        with open(review_path, "w", newline="", encoding="utf-8") as fh:
            w = _csv.writer(fh)
            w.writerow(["id", "name", "violations"])
            for _id, _name, _vio in recon_stats["sanity_violations"]:
                w.writerow([_id, _name, "; ".join(_vio)])
        logger.info(
            "Wrote %d rows to %s for manual review",
            len(recon_stats["sanity_violations"]), review_path,
        )

    # Write guide_needs_sourcing.csv — every guide entry missing sodium_mg plus
    # the 7 explicitly-flagged dishes we chose not to add without a real number.
    try:
        missing_rows = collect_needs_sourcing([
            ("fruit",     FRUIT_GUIDE,     "fruits"),
            ("vegetable", VEGETABLE_GUIDE, "vegetables"),
            ("snack",     SNACK_GUIDE,     "snacks"),
            ("beverage",  BEVERAGE_GUIDE,  "beverages"),
            ("protein",   PROTEIN_GUIDE,   "proteins"),
            ("grain",     GRAIN_GUIDE,     "grains"),
        ])
        write_needs_sourcing_csv(
            Path(__file__).parent / "guide_needs_sourcing.csv",
            missing_rows,
        )
    except Exception:
        logger.exception("Failed to write guide_needs_sourcing.csv")
    yield
    # Shutdown
    client.close()


# -------- App --------
app = FastAPI(title="Indian Renal Diet API", lifespan=lifespan)
app.state.limiter = limiter


async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": "Too many requests. Please slow down."})


app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

api = APIRouter(prefix="/api")


# ==================== AUTH ====================
@api.post("/auth/register", response_model=AuthResponse)
@limiter.limit("5/minute", key_func=get_remote_address)
async def register(request: Request, body: UserRegister):
    email = body.email.lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = str(uuid.uuid4())
    doc = {
        "id": user_id,
        "email": email,
        "full_name": body.full_name or "",
        "stage": "unknown",
        "diabetic": False,
        "doctor_limits": None,
        "hashed_password": hash_pw(body.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        await db.users.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Email already registered")
    return AuthResponse(
        access_token=create_token(user_id),
        user=UserOut(
            id=user_id,
            email=email,
            full_name=body.full_name or "",
            stage="unknown",
            diabetic=False,
            doctor_limits=None,
        ),
    )


def _user_to_out(user: dict) -> UserOut:
    dl = user.get("doctor_limits")
    return UserOut(
        id=user["id"],
        email=user["email"],
        full_name=user.get("full_name", ""),
        stage=user.get("stage", "unknown"),
        diabetic=bool(user.get("diabetic", False)),
        doctor_limits=DoctorLimits(**dl) if dl else None,
        nutrient_unit=user.get("nutrient_unit", "mg"),
    )


@api.post("/auth/login", response_model=AuthResponse)
@limiter.limit("5/minute", key_func=get_remote_address)
async def login(request: Request, body: UserLogin):
    user = await db.users.find_one({"email": body.email.lower()})
    if not user:
        verify_pw(body.password, _dummy_hash)  # timing-safe
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not verify_pw(body.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return AuthResponse(access_token=create_token(user["id"]), user=_user_to_out(user))


@api.get("/auth/me", response_model=UserOut)
async def me(current_user=Depends(get_current_user)):
    return _user_to_out(current_user)


@api.post("/auth/stage", response_model=UserOut)
async def set_stage(body: StageUpdate, current_user=Depends(get_current_user)):
    await db.users.update_one({"id": current_user["id"]}, {"$set": {"stage": body.stage}})
    current_user["stage"] = body.stage
    return _user_to_out(current_user)


@api.patch("/auth/profile", response_model=UserOut)
async def update_profile(body: ProfileUpdate, current_user=Depends(get_current_user)):
    update: dict = {}
    set_fields = body.model_fields_set
    if "diabetic" in set_fields and body.diabetic is not None:
        update["diabetic"] = bool(body.diabetic)
    if "doctor_limits" in set_fields:
        if body.doctor_limits is None:
            update["doctor_limits"] = None  # explicit null clears
        else:
            dl = body.doctor_limits.model_dump(exclude_none=True)
            update["doctor_limits"] = dl if dl else None
    if "nutrient_unit" in set_fields and body.nutrient_unit is not None:
        update["nutrient_unit"] = body.nutrient_unit
    if update:
        await db.users.update_one({"id": current_user["id"]}, {"$set": update})
        current_user.update(update)
    return _user_to_out(current_user)


@api.get("/fruits/guide")
async def fruits_guide():
    """Patient-facing curated fruit reference for CKD/dialysis."""
    return get_fruit_guide()


@api.get("/beverages/guide")
async def beverages_guide():
    """Patient-facing curated beverage reference for CKD/dialysis."""
    return get_beverage_guide()


@api.get("/vegetables/guide")
async def vegetables_guide():
    """Patient-facing curated vegetable reference for CKD/dialysis."""
    return get_vegetable_guide()


@api.get("/snacks/guide")
async def snacks_guide():
    """Patient-facing curated snack reference for CKD/dialysis."""
    return get_snack_guide()


@api.get("/proteins/guide")
async def proteins_guide():
    """Patient-facing curated protein reference for CKD/dialysis."""
    return get_protein_guide()


@api.get("/grains/guide")
async def grains_guide():
    """Patient-facing curated grains & rotis reference for CKD/dialysis."""
    return get_grain_guide()



# ==================== FOODS ====================
@api.get("/foods", response_model=List[FoodOut])
async def list_foods(
    q: Optional[str] = Query(None, description="Search text"),
    tier: Optional[str] = Query(None, description="Comma-separated: GREEN,YELLOW,RED"),
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

    fav_ids = await get_user_favorite_ids(current_user) if current_user else set()

    if favorites_only:
        if not current_user:
            raise HTTPException(status_code=401, detail="Login required for favorites")
        if not fav_ids:
            return []
        query["id"] = {"$in": list(fav_ids)}

    cursor = db.foods.find(query, {"_id": 0}).sort("name", 1).limit(limit)
    return [enrich_food_sync(doc, current_user, fav_ids) async for doc in cursor]


@api.get("/foods/{food_id}", response_model=FoodDetailOut)
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


# ==================== FAVORITES ====================
@api.post("/favorites/{food_id}", response_model=FavoriteToggleResponse)
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


# ==================== WEEKLY REPORT ====================
@api.get("/reports/weekly", response_model=WeeklyReportResponse)
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


@api.get("/meal-logs/summary", response_model=MealLogSummary)
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


# ==================== FOOD SCAN (Vision) ====================
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


def _extract_json(text: str) -> Optional[dict]:
    import json

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


@api.post("/scan/food", response_model=FoodScanResponse)
@limiter.limit("5/minute", key_func=_rate_key_user)
async def scan_food(request: Request, body: FoodScanRequest, current_user=Depends(get_current_user)):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=503, detail="Vision service not configured")
    raw = (body.image_base64 or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="image_base64 is required")
    if raw.startswith("data:"):
        raw = raw.split(",", 1)[-1]
    try:
        decoded = base64.b64decode(raw, validate=True)
        if len(decoded) < 200:
            raise HTTPException(status_code=400, detail="Image is empty or too small")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 image data")

    try:
        from emergentintegrations.llm.chat import ImageContent, LlmChat, UserMessage

        chat = (
            LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"scan-{current_user['id']}-{uuid.uuid4().hex[:8]}",
                system_message=_SCAN_SYSTEM,
            )
            .with_model("anthropic", "claude-sonnet-4-5-20250929")
        )
        image_content = ImageContent(image_base64=raw)
        reply = await chat.send_message(
            UserMessage(text="Identify this Indian dish and classify its CKD safety.", file_contents=[image_content])
        )
        text = str(reply).strip()
    except Exception:
        logger.exception("Vision scan failed")
        raise HTTPException(status_code=502, detail="Vision service temporarily unavailable")

    data = _extract_json(text) or {}
    food_name = str(data.get("food_name") or "Unknown Dish").strip()
    tier = str(data.get("safety_tier") or "YELLOW").upper()
    if tier not in {"GREEN", "YELLOW", "RED"}:
        tier = "YELLOW"
    hindi_name = data.get("hindi_name")
    primary_risk = str(data.get("primary_risk_factor") or "NONE").upper()
    portion_limit_text = str(data.get("portion_limit_text") or "Consult your nephrologist.")
    clinical_tip = str(data.get("clinical_tip") or "Verify this identification with your care team.")

    matched_id: Optional[str] = None
    if food_name and food_name.lower() != "unknown":
        match = await db.foods.find_one(
            {"name": {"$regex": re.escape(food_name), "$options": "i"}}, {"_id": 0}
        )
        if match:
            matched_id = match["id"]
            # Authoritative override: the food card is the source of truth.
            # Use the user's effective (personalized) tier so scan and search never disagree.
            stage: Stage = current_user.get("stage", "unknown") or "unknown"  # type: ignore
            tier = personal_tier_for(match, stage)
            primary_risk = match.get("primary_risk_factor", "NONE")
            portion_limit_text = match.get("portion_limit_text", portion_limit_text)
            clinical_tip = match.get("actionable_clinical_tip", clinical_tip)
            hindi_name = match.get("hindi_name", hindi_name)
            food_name = match["name"]

    return FoodScanResponse(
        food_name=food_name,
        hindi_name=hindi_name,
        safety_tier=tier,
        primary_risk_factor=primary_risk,
        portion_limit_text=portion_limit_text,
        clinical_tip=clinical_tip,
        matched_food_id=matched_id,
        raw=text if not data else None,
    )


# ==================== BARCODE SCAN (Open Food Facts) ====================
def _classify_from_nutrients(k_mg: float, p_mg: float, na_mg: float) -> tuple[str, str]:
    """Return (safety_tier, primary_risk_factor) from per-portion nutrients."""
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


@api.post("/scan/barcode", response_model=FoodScanResponse)
@limiter.limit("15/minute", key_func=_rate_key_user)
async def scan_barcode(request: Request, body: BarcodeScanRequest, current_user=Depends(get_current_user)):
    import httpx

    barcode = re.sub(r"\D", "", body.barcode)
    if len(barcode) < 6:
        raise HTTPException(status_code=400, detail="Invalid barcode")

    url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
    try:
        async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "IndianRenalDiet/1.0"}) as hc:
            r = await hc.get(url)
    except Exception:
        logger.exception("Open Food Facts request failed")
        raise HTTPException(status_code=502, detail="Barcode lookup temporarily unavailable")
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="Barcode lookup temporarily unavailable")
    doc = r.json() or {}
    if int(doc.get("status", 0)) != 1 or not doc.get("product"):
        raise HTTPException(status_code=404, detail="Product not found for this barcode")

    product = doc["product"]
    product_name = (product.get("product_name") or product.get("product_name_en") or "").strip() or "Unknown packaged food"
    brand = (product.get("brands") or "").split(",")[0].strip() or None
    nutriments = product.get("nutriments") or {}

    def _val(key: str) -> float:
        v = nutriments.get(key)
        try:
            return float(v) if v is not None else 0.0
        except (TypeError, ValueError):
            return 0.0

    # Prefer per-serving values when available, else per-100g.
    portion_g = 0.0
    try:
        portion_g = float(product.get("serving_quantity") or 0)
    except (TypeError, ValueError):
        portion_g = 0.0

    if portion_g and _val("potassium_serving"):
        k_mg = _val("potassium_serving") * 1000  # OFF stores in grams
        p_mg = _val("phosphorus_serving") * 1000
        na_mg = _val("sodium_serving") * 1000 if _val("sodium_serving") else _val("salt_serving") * 400  # salt→Na
        protein_g = _val("proteins_serving")
    else:
        # per-100g, scale to serving if we know it, else use 100g as reference portion
        ref = portion_g if portion_g else 100.0
        k_mg = _val("potassium_100g") * 1000 * ref / 100
        p_mg = _val("phosphorus_100g") * 1000 * ref / 100
        na_mg = (_val("sodium_100g") * 1000 * ref / 100) if _val("sodium_100g") else (_val("salt_100g") * 400 * ref / 100)
        protein_g = _val("proteins_100g") * ref / 100
        if not portion_g:
            portion_g = 100.0

    tier, primary_risk = _classify_from_nutrients(k_mg, p_mg, na_mg)
    portion_limit_text = f"Serving size: {int(portion_g)}g"
    clinical_tip = (
        f"Per serving: potassium {int(k_mg)}mg, phosphorus {int(p_mg)}mg, sodium {int(na_mg)}mg. "
        "Always cross-check with the pack label; some manufacturers under-report additives."
    )
    hindi_name: Optional[str] = None

    # Authoritative DB override: if the product name matches a seeded food.
    matched_id: Optional[str] = None
    if product_name and product_name.lower() != "unknown packaged food":
        match = await db.foods.find_one(
            {"name": {"$regex": re.escape(product_name), "$options": "i"}, "source": {"$ne": "barcode"}},
            {"_id": 0},
        )
        if match:
            matched_id = match["id"]
            stage: Stage = current_user.get("stage", "unknown") or "unknown"  # type: ignore
            tier = personal_tier_for(match, stage)
            primary_risk = match.get("primary_risk_factor", primary_risk)
            portion_limit_text = match.get("portion_limit_text", portion_limit_text)
            clinical_tip = match.get("actionable_clinical_tip", clinical_tip)
            hindi_name = match.get("hindi_name")
            portion_g = float(match.get("portion_g") or portion_g)
            k_mg = float(match.get("potassium_mg") or k_mg)
            p_mg = float(match.get("phosphorus_mg") or p_mg)
            na_mg = float(match.get("sodium_mg") or na_mg)
            protein_g = float(match.get("protein_g") or protein_g)
            product_name = match["name"]

    # If no authoritative seed match, upsert the scanned pack as a barcode-sourced food
    # so users can favorite it and log it directly via existing endpoints. Idempotent by barcode.
    if not matched_id:
        display_name = f"{product_name} ({brand})" if brand else product_name
        food_id = f"bc_{barcode}"
        food_doc = {
            "id": food_id,
            "name": display_name,
            "hindi_name": hindi_name or "",
            "category": "Packaged",
            "safety_tier": tier,
            "primary_risk_factor": primary_risk,
            "portion_limit_text": portion_limit_text,
            "actionable_clinical_tip": clinical_tip,
            "portion_g": round(portion_g, 1),
            "potassium_mg": round(k_mg, 1),
            "phosphorus_mg": round(p_mg, 1),
            "sodium_mg": round(na_mg, 1),
            "protein_g": round(protein_g, 1),
            "fluid_ml": 0,
            "source": "barcode",
            "barcode": barcode,
            "brand": brand,
            "swaps": [],
        }
        await db.foods.update_one({"id": food_id}, {"$set": food_doc}, upsert=True)
        matched_id = food_id

    return FoodScanResponse(
        food_name=product_name,
        hindi_name=hindi_name,
        safety_tier=tier,
        primary_risk_factor=primary_risk,
        portion_limit_text=portion_limit_text,
        clinical_tip=clinical_tip,
        matched_food_id=matched_id,
        barcode=barcode,
        brand=brand,
        portion_g=round(portion_g, 1),
        potassium_mg=round(k_mg, 1),
        phosphorus_mg=round(p_mg, 1),
        sodium_mg=round(na_mg, 1),
        protein_g=round(protein_g, 1),
    )


# ==================== MEAL LOG ====================
@api.get("/meal-logs", response_model=List[MealLogOut])
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


@api.post("/meal-logs", response_model=MealLogOut)
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


@api.delete("/meal-logs/{log_id}")
async def delete_meal_log(log_id: str, current_user=Depends(get_current_user)):
    res = await db.meal_logs.delete_one({"id": log_id, "user_id": current_user["id"]})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Log not found")
    return {"success": True}


# ==================== AI ASK ====================
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
        f"sodium {int(limits.sodium_mg)} mg ({limits.sodium_mg/23:.1f} mEq)\n"
        f"- Today's intake so far: potassium {int(totals['potassium_mg'])} mg "
        f"({totals['potassium_mg']/39.1:.1f} mEq), "
        f"phosphorus {int(totals['phosphorus_mg'])} mg, "
        f"sodium {int(totals['sodium_mg'])} mg ({totals['sodium_mg']/23:.1f} mEq), "
        f"protein {totals['protein_g']:.1f} g, fluid {int(totals['fluid_ml'])} ml"
    )
    if user.get("diabetic"):
        ctx += "\n- Because the patient is diabetic, also flag foods with high glycemic load."

    if lang == "hi":
        ctx += _lang_instruction("Hindi", "Devanagari", "लौकी (Lauki)")
    elif lang == "ta":
        ctx += _lang_instruction("Tamil", "Tamil script", "லௌகி (Lauki)")
    elif lang == "bn":
        ctx += _lang_instruction("Bengali", "Bengali script", "লাউ (Lauki)")
    elif lang == "mr":
        ctx += _lang_instruction("Marathi", "Devanagari", "दुधी (Lauki)")
    return ctx


def _lang_instruction(name: str, script: str, sample: str) -> str:
    return (
        f"\n\nIMPORTANT: The user's app language is {name}. "
        f"Answer entirely in conversational {name} ({script}). "
        f"Keep English food names in brackets where helpful, e.g. '{sample}'."
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


# Guide files that /ai/ask needs to see. Kept in one place so a future addition
# (e.g. dessert_guide.py) can be plugged in by extending this list.
_GUIDE_SOURCES: List[tuple[str, str, "callable"]] = []  # populated at import


def _register_guides() -> None:
    """Late binding — imports the guide getters here to avoid a circular import
    order concern with this module's own top-level guide imports."""
    global _GUIDE_SOURCES
    _GUIDE_SOURCES = [
        ("fruit",     "fruits",     get_fruit_guide),
        ("vegetable", "vegetables", get_vegetable_guide),
        ("snack",     "snacks",     get_snack_guide),
        ("beverage",  "beverages",  get_beverage_guide),
        ("protein",   "proteins",   get_protein_guide),
        ("grain",     "grains",     get_grain_guide),
    ]


def _find_relevant_guide_entries(question: str, limit: int = 6) -> List[dict]:
    """Second retrieval path — matches the same tokens against the 5+ curated
    guide files. Returns a flat list of {guide, tier, entry} rows so the
    grounded-food block can render them alongside DB foods. Some guide entries
    are intentionally reference-only (linked_food_id=None) and never make it
    into db.foods, so this path is required to close the visibility gap for
    /ai/ask questions like 'is khoa safe?' or 'what about water chestnut?'."""
    if not _GUIDE_SOURCES:
        _register_guides()
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


async def _build_grounded_food_block(question: str, user: dict) -> str:
    """Inject authoritative food classifications matching the question.

    Also queries the 5 curated guide files so that reference-only entries
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


@api.post("/ai/ask", response_model=AiAskResponse)
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


# ==================== AI LOG-MEAL (natural-language meal parsing) ====================
_LOG_MEAL_EXTRACT_PROMPT = (
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
    ParsedMealItem with outcome + candidates. Reuses _find_relevant_foods so
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


@api.post("/ai/log-meal", response_model=AiLogMealResponse)
@limiter.limit("10/minute", key_func=_rate_key_user)
async def ai_log_meal(
    request: Request, body: AiLogMealRequest,
    current_user=Depends(get_current_user),
):
    """Parse free-text meal description into loggable items.

    Strictly retrieval-then-confirm — the LLM only extracts structure from the
    user's own words; every food identity + nutrient number comes from
    _find_relevant_foods against the app's verified DB. The endpoint NEVER
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
                system_message=_LOG_MEAL_EXTRACT_PROMPT,
            )
            .with_model("anthropic", "claude-sonnet-4-5-20250929")
        )
        raw = await chat.send_message(UserMessage(text=text))
        raw_str = str(raw).strip()
        # Strip ```json fences if the model added them.
        if raw_str.startswith("```"):
            raw_str = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_str, flags=re.IGNORECASE)
        import json as _json
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


@api.get("/")
async def root():
    return {"service": "Indian Renal Diet API", "status": "ok"}


app.include_router(api)

# CORS — allow_origins=["*"] with allow_credentials=True is invalid and insecure.
# Origins come from CORS_ORIGINS env var (comma-separated).
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
