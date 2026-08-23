"""Auth + rate-limit primitives shared by every route.

- `hash_pw` / `verify_pw` — bcrypt via passlib.
- `create_token` / `_decode_user_id` — HS256 JWTs, ~30-day expiry.
- `get_current_user` / `get_optional_user` — FastAPI dependencies.
- `limiter` / `_rate_key_user` — slowapi-based, per-user when authed
  otherwise per-IP.

`_dummy_hash` is used by the login endpoint as a timing-safe branch
when the email is unknown (constant-time compare hides account enumeration).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from slowapi import Limiter
from slowapi.util import get_remote_address

from config import JWT_ALG, JWT_EXPIRE_HOURS, JWT_SECRET
from db import db

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


def _rate_key_user(request: Request) -> str:
    """Rate-limit key per user id when available, otherwise per IP."""
    auth = request.headers.get("Authorization", "")
    token = auth.split(" ", 1)[1] if auth.lower().startswith("bearer ") else None
    uid = _decode_user_id(token)
    if uid:
        return f"user:{uid}"
    return f"ip:{get_remote_address(request)}"


# Single shared limiter — routes decorate their handlers with @limiter.limit(...).
limiter = Limiter(key_func=get_remote_address)
