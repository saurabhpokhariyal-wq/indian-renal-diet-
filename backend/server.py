"""Indian Renal Diet backend — FastAPI + MongoDB.

Endpoints (all prefixed /api):
- POST   /api/auth/register
- POST   /api/auth/login
- GET    /api/auth/me
- GET    /api/foods                (?q=search&tier=RED,YELLOW,GREEN)
- GET    /api/foods/{id}           (returns food + swap if RED)
- GET    /api/meal-logs?date=YYYY-MM-DD
- POST   /api/meal-logs
- DELETE /api/meal-logs/{id}
- POST   /api/ai/ask               (Claude Sonnet 4.5 via Emergent LLM key)
"""

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from starlette.middleware.cors import CORSMiddleware

from seed_data import SEED_FOODS, SEED_SWAPS

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# -------- Environment --------
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALG = "HS256"
JWT_EXPIRE_HOURS = 24 * 30  # 30 days
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")

# -------- Mongo --------
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# -------- Auth utils --------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
_dummy_hash = pwd_context.hash("dummy-password-for-timing")


def hash_pw(p: str) -> str:
    return pwd_context.hash(p)


def verify_pw(p: str, h: str) -> bool:
    return pwd_context.verify(p, h)


def create_token(user_id: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    return jwt.encode({"sub": user_id, "exp": exp}, JWT_SECRET, algorithm=JWT_ALG)


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


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
    date: str  # YYYY-MM-DD
    meal_type: str = "meal"  # breakfast/lunch/dinner/snack/meal


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


# -------- App --------
app = FastAPI(title="Indian Renal Diet API")
api = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("renal-diet")


@app.on_event("startup")
async def startup() -> None:
    # Indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    await db.foods.create_index("id", unique=True)
    await db.foods.create_index("name")
    await db.swaps.create_index("trigger_food_id")
    await db.meal_logs.create_index([("user_id", 1), ("date", 1)])

    # Seed foods (idempotent upsert)
    for food in SEED_FOODS:
        await db.foods.update_one({"id": food["id"]}, {"$set": food}, upsert=True)
    for swap in SEED_SWAPS:
        await db.swaps.update_one({"id": swap["id"]}, {"$set": swap}, upsert=True)
    logger.info("Seeded %d foods, %d swaps", len(SEED_FOODS), len(SEED_SWAPS))


@app.on_event("shutdown")
async def shutdown() -> None:
    client.close()


# ==================== AUTH ====================
@api.post("/auth/register", response_model=AuthResponse)
async def register(body: UserRegister):
    existing = await db.users.find_one({"email": body.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = str(uuid.uuid4())
    doc = {
        "id": user_id,
        "email": body.email.lower(),
        "full_name": body.full_name or "",
        "hashed_password": hash_pw(body.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(doc)
    return AuthResponse(
        access_token=create_token(user_id),
        user=UserOut(id=user_id, email=body.email.lower(), full_name=body.full_name or ""),
    )


@api.post("/auth/login", response_model=AuthResponse)
async def login(body: UserLogin):
    user = await db.users.find_one({"email": body.email.lower()})
    if not user:
        verify_pw(body.password, _dummy_hash)  # timing-safe
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not verify_pw(body.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return AuthResponse(
        access_token=create_token(user["id"]),
        user=UserOut(id=user["id"], email=user["email"], full_name=user.get("full_name", "")),
    )


@api.get("/auth/me", response_model=UserOut)
async def me(current_user=Depends(get_current_user)):
    return UserOut(id=current_user["id"], email=current_user["email"], full_name=current_user.get("full_name", ""))


# ==================== FOODS ====================
@api.get("/foods", response_model=List[FoodOut])
async def list_foods(
    q: Optional[str] = Query(None, description="Search text"),
    tier: Optional[str] = Query(None, description="Comma-separated: GREEN,YELLOW,RED"),
    limit: int = 100,
):
    query: dict = {}
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"hindi_name": {"$regex": q, "$options": "i"}},
            {"category": {"$regex": q, "$options": "i"}},
        ]
    if tier:
        tiers = [t.strip().upper() for t in tier.split(",") if t.strip()]
        query["safety_tier"] = {"$in": tiers}
    cursor = db.foods.find(query, {"_id": 0}).limit(limit)
    return [FoodOut(**doc) async for doc in cursor]


@api.get("/foods/{food_id}", response_model=FoodDetailOut)
async def get_food(food_id: str):
    food = await db.foods.find_one({"id": food_id}, {"_id": 0})
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    swap_out: Optional[SwapOut] = None
    if food["safety_tier"] == "RED":
        swap = await db.swaps.find_one({"trigger_food_id": food_id}, {"_id": 0})
        if swap:
            rec = await db.foods.find_one({"id": swap["recommended_swap_food_id"]}, {"_id": 0})
            if rec:
                swap_out = SwapOut(
                    id=swap["id"],
                    trigger_food_id=swap["trigger_food_id"],
                    recommended_swap_food_id=swap["recommended_swap_food_id"],
                    recommended_food=FoodOut(**rec),
                    clinical_benefit_explanation=swap["clinical_benefit_explanation"],
                )
    return FoodDetailOut(food=FoodOut(**food), swap=swap_out)


# ==================== MEAL LOG ====================
@api.get("/meal-logs", response_model=List[MealLogOut])
async def list_meal_logs(
    date: str = Query(..., description="YYYY-MM-DD"),
    current_user=Depends(get_current_user),
):
    cursor = db.meal_logs.find({"user_id": current_user["id"], "date": date}, {"_id": 0}).sort("created_at", 1)
    out: List[MealLogOut] = []
    async for log in cursor:
        food = await db.foods.find_one({"id": log["food_id"]}, {"_id": 0})
        if not food:
            continue
        out.append(MealLogOut(
            id=log["id"],
            food_id=log["food_id"],
            date=log["date"],
            meal_type=log.get("meal_type", "meal"),
            food=FoodOut(**food),
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
    return MealLogOut(
        id=log["id"],
        food_id=log["food_id"],
        date=log["date"],
        meal_type=log["meal_type"],
        food=FoodOut(**food),
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
async def ai_ask(body: AiAskRequest, current_user=Depends(get_current_user)):
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
    except Exception as e:  # noqa: BLE001
        logger.exception("AI ask failed")
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")


@api.get("/")
async def root():
    return {"service": "Indian Renal Diet API", "status": "ok"}


app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
