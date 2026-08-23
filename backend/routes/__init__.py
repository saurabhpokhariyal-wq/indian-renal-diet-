"""Route package — aggregates individual routers under a single /api prefix.

`build_api_router()` is called once from `server.py` at startup. Kept as a
factory (not a module-level `api = APIRouter(...)`) so unit tests importing
individual route modules never accidentally include a leftover registration.
"""
from fastapi import APIRouter

from routes import ai as ai_routes
from routes import auth as auth_routes
from routes import favorites as favorites_routes
from routes import foods as foods_routes
from routes import guides as guides_routes
from routes import meal_logs as meal_logs_routes
from routes import reports as reports_routes
from routes import scan as scan_routes


def build_api_router() -> APIRouter:
    api = APIRouter(prefix="/api")
    api.include_router(auth_routes.router)
    api.include_router(guides_routes.router)
    api.include_router(foods_routes.router)
    api.include_router(favorites_routes.router)
    api.include_router(reports_routes.router)
    api.include_router(meal_logs_routes.router)
    api.include_router(scan_routes.router)
    api.include_router(ai_routes.router)

    @api.get("/")
    async def root():
        return {"service": "Indian Renal Diet API", "status": "ok"}

    return api
