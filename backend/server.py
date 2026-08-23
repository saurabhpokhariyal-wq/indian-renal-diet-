"""Indian Renal Diet backend — FastAPI + MongoDB.

Thin composition entrypoint. Actual logic lives in:
  - `config.py`, `db.py`, `security.py`, `schemas.py`
  - `personalization.py`, `food_enrichment.py`
  - `ai_service.py`, `scan_service.py`
  - `lifespan.py`
  - `routes/` (auth, foods, favorites, meal_logs, reports, guides, scan, ai)

Public endpoints (all prefixed /api):
  - POST   /api/auth/register | /login   GET /me   POST /stage   PATCH /profile
  - GET    /api/foods                     (?q=&tier=)
  - GET    /api/foods/{id}
  - POST   /api/favorites/{food_id}
  - GET    /api/meal-logs?date=YYYY-MM-DD  POST/DELETE
  - GET    /api/meal-logs/summary
  - GET    /api/reports/weekly
  - POST   /api/ai/ask | /api/ai/log-meal
  - POST   /api/scan/food | /api/scan/barcode
  - GET    /api/{fruits,beverages,vegetables,snacks,proteins,grains}/guide

Re-exports for in-process tests:
  - `app`   — the FastAPI instance
  - `db`    — the Motor db handle (iter24 tests reach into Mongo directly)
  - `_extract_json` — monkey-patched by iter24 scan tests
"""
from __future__ import annotations

import logging

from fastapi import Request
from slowapi.errors import RateLimitExceeded
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

# ---- Local imports (all live next to this file) ----
from config import CORS_ORIGINS
from db import db  # noqa: F401 — re-exported for tests
from lifespan import lifespan
from routes import build_api_router
# _extract_json is re-exported so iter24 tests can monkey-patch
# `server._extract_json` — the scan route reads it via `import server` too.
from scan_service import _extract_json  # noqa: F401
from security import limiter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("renal-diet")


# ---- FastAPI app ----
from fastapi import FastAPI  # placed after logging to keep import order tidy

app = FastAPI(title="Indian Renal Diet API", lifespan=lifespan)
app.state.limiter = limiter


async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": "Too many requests. Please slow down."})


app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

# Aggregate all /api/* routes.
app.include_router(build_api_router())

# CORS — allow_origins=["*"] with allow_credentials=True is invalid and insecure.
# Origins come from CORS_ORIGINS env var (comma-separated).
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
