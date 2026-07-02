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

Stage = Literal["pre_dialysis", "dialysis", "unknown"]
MealType = Literal["breakfast", "lunch", "dinner", "snack", "meal"]

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


class StageUpdate(BaseModel):
    stage: Stage


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
    personal_tier: Optional[str] = None
    is_favorite: bool = False


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
    food: FoodOut
    created_at: str


class AiAskRequest(BaseModel):
    question: str


class AiAskResponse(BaseModel):
    answer: str


class FoodScanRequest(BaseModel):
    image_base64: str


class FoodScanResponse(BaseModel):
    food_name: str
    hindi_name: Optional[str] = None
    safety_tier: str
    primary_risk_factor: str
    portion_limit_text: str
    clinical_tip: str
    matched_food_id: Optional[str] = None
    raw: Optional[str] = None


class FavoriteToggleResponse(BaseModel):
    food_id: str
    is_favorite: bool


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


# -------- Personalization --------
def personal_tier_for(food: dict, stage: Stage) -> str:
    """For dialysis patients tighten YELLOW → RED when risk is potassium/phosphorus/fluid."""
    base = food["safety_tier"]
    if stage == "dialysis" and base == "YELLOW" and food.get("primary_risk_factor") in {"POTASSIUM", "PHOSPHORUS", "FLUID"}:
        return "RED"
    return base


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
        personal_tier=personal_tier_for(food, stage),
        is_favorite=food["id"] in fav_ids,
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

    for food in SEED_FOODS:
        await db.foods.update_one({"id": food["id"]}, {"$set": food}, upsert=True)
    for swap in SEED_SWAPS:
        await db.swaps.update_one({"id": swap["id"]}, {"$set": swap}, upsert=True)
    logger.info("Seeded %d foods, %d swaps", len(SEED_FOODS), len(SEED_SWAPS))
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
        "hashed_password": hash_pw(body.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        await db.users.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Email already registered")
    return AuthResponse(
        access_token=create_token(user_id),
        user=UserOut(id=user_id, email=email, full_name=body.full_name or "", stage="unknown"),
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
    return AuthResponse(
        access_token=create_token(user["id"]),
        user=UserOut(
            id=user["id"],
            email=user["email"],
            full_name=user.get("full_name", ""),
            stage=user.get("stage", "unknown"),
        ),
    )


@api.get("/auth/me", response_model=UserOut)
async def me(current_user=Depends(get_current_user)):
    return UserOut(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user.get("full_name", ""),
        stage=current_user.get("stage", "unknown"),
    )


@api.post("/auth/stage", response_model=UserOut)
async def set_stage(body: StageUpdate, current_user=Depends(get_current_user)):
    await db.users.update_one({"id": current_user["id"]}, {"$set": {"stage": body.stage}})
    return UserOut(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user.get("full_name", ""),
        stage=body.stage,
    )


# ==================== FOODS ====================
@api.get("/foods", response_model=List[FoodOut])
async def list_foods(
    q: Optional[str] = Query(None, description="Search text"),
    tier: Optional[str] = Query(None, description="Comma-separated: GREEN,YELLOW,RED"),
    favorites_only: bool = Query(False),
    limit: int = 100,
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

    cursor = db.foods.find(query, {"_id": 0}).limit(limit)
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

    for log in logs:
        food = foods_by_id.get(log["food_id"])
        if not food:
            continue
        tier = personal_tier_for(food, current_user.get("stage", "unknown"))
        totals[tier] += 1
        bucket = day_map.setdefault(log["date"], {"green": 0, "yellow": 0, "red": 0})
        bucket[tier.lower()] += 1
        name_by_tier[tier][food["name"]] = name_by_tier[tier].get(food["name"], 0) + 1

    def top(d: dict, n: int = 3) -> List[str]:
        return [k for k, _ in sorted(d.items(), key=lambda kv: kv[1], reverse=True)[:n]]

    days = [
        WeeklyReportDay(date=d, green=v["green"], yellow=v["yellow"], red=v["red"])
        for d, v in sorted(day_map.items())
    ]
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

    matched_id: Optional[str] = None
    if food_name and food_name.lower() != "unknown":
        match = await db.foods.find_one(
            {"name": {"$regex": re.escape(food_name), "$options": "i"}}, {"_id": 0}
        )
        if match:
            matched_id = match["id"]

    return FoodScanResponse(
        food_name=food_name,
        hindi_name=data.get("hindi_name"),
        safety_tier=tier,
        primary_risk_factor=str(data.get("primary_risk_factor") or "NONE").upper(),
        portion_limit_text=str(data.get("portion_limit_text") or "Consult your nephrologist."),
        clinical_tip=str(data.get("clinical_tip") or "Verify this identification with your care team."),
        matched_food_id=matched_id,
        raw=text if not data else None,
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
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.meal_logs.insert_one(log)
    fav_ids = await get_user_favorite_ids(current_user)
    return MealLogOut(
        id=log["id"],
        food_id=log["food_id"],
        date=log["date"],
        meal_type=log["meal_type"],
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
AI_SYSTEM_PROMPT = (
    "You are a friendly Indian Renal Diet coach for CKD/dialysis patients. "
    "You answer in short, plain language (max 6 sentences). "
    "Always classify Indian foods as SAFE (green), CAUTION (yellow) or AVOID (red) "
    "based on potassium, phosphorus, sodium and fluid load. "
    "When something is unsafe, ALWAYS suggest a kidney-friendly Indian swap. "
    "Do NOT give medical dosages. Always add a one-line reminder to check with the patient's nephrologist "
    "for personal targets. Use warm, encouraging tone. When helpful, add the Hindi name in brackets."
)


@api.post("/ai/ask", response_model=AiAskResponse)
@limiter.limit("10/minute", key_func=_rate_key_user)
async def ai_ask(request: Request, body: AiAskRequest, current_user=Depends(get_current_user)):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=503, detail="AI service is not configured")
    question = (body.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        session_id = f"user-{current_user['id']}"
        chat = (
            LlmChat(api_key=EMERGENT_LLM_KEY, session_id=session_id, system_message=AI_SYSTEM_PROMPT)
            .with_model("anthropic", "claude-sonnet-4-5-20250929")
        )
        reply = await chat.send_message(UserMessage(text=question))
        return AiAskResponse(answer=str(reply).strip())
    except Exception:
        logger.exception("AI ask failed")
        raise HTTPException(status_code=502, detail="AI service temporarily unavailable")


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
