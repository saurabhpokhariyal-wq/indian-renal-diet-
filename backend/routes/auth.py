"""Auth routes — register, login, me, stage update, profile patch."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pymongo.errors import DuplicateKeyError
from slowapi.util import get_remote_address

from db import db
from schemas import (
    AuthResponse,
    DoctorLimits,
    ProfileUpdate,
    StageUpdate,
    UserLogin,
    UserOut,
    UserRegister,
)
from security import (
    _dummy_hash,
    create_token,
    get_current_user,
    hash_pw,
    limiter,
    verify_pw,
)


router = APIRouter()


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


@router.post("/auth/register", response_model=AuthResponse)
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


@router.post("/auth/login", response_model=AuthResponse)
@limiter.limit("5/minute", key_func=get_remote_address)
async def login(request: Request, body: UserLogin):
    user = await db.users.find_one({"email": body.email.lower()})
    if not user:
        verify_pw(body.password, _dummy_hash)  # timing-safe
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not verify_pw(body.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return AuthResponse(access_token=create_token(user["id"]), user=_user_to_out(user))


@router.get("/auth/me", response_model=UserOut)
async def me(current_user=Depends(get_current_user)):
    return _user_to_out(current_user)


@router.post("/auth/stage", response_model=UserOut)
async def set_stage(body: StageUpdate, current_user=Depends(get_current_user)):
    await db.users.update_one({"id": current_user["id"]}, {"$set": {"stage": body.stage}})
    current_user["stage"] = body.stage
    return _user_to_out(current_user)


@router.patch("/auth/profile", response_model=UserOut)
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
