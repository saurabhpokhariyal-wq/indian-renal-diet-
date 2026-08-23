"""Motor client + async db handle.

Kept as a single-line module so every route/service that needs the DB just
does `from db import db` — that avoids each module holding its own client and
matches the pattern the tests already probe (`server.db` is re-exported for
in-process tests that reach into Mongo directly).
"""
from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient

from config import DB_NAME, MONGO_URL

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]
