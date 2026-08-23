"""Environment/config constants for the Indian Renal Diet backend.

Centralises the env-var reads so no other module needs to touch `os.environ`
directly (except test hooks). Also pins the JWT algorithm/expiry so the
security module and any signed-link generators can share the same values.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# --- Required (fail loud on missing so we never boot in a half-configured state) ---
MONGO_URL: str = os.environ["MONGO_URL"]
DB_NAME: str = os.environ["DB_NAME"]
JWT_SECRET: str = os.environ["JWT_SECRET"]

# --- Optional ---
EMERGENT_LLM_KEY: str = os.environ.get("EMERGENT_LLM_KEY", "")

CORS_ORIGINS: List[str] = [
    o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()
]

# --- Constants ---
JWT_ALG: str = "HS256"
JWT_EXPIRE_HOURS: int = 24 * 30  # 30 days
