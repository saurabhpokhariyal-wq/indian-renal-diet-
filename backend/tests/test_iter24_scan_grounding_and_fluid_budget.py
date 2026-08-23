"""Iter 24 tests: scan/food + scan/barcode UNVERIFIED grounding, and fluid budget.

Design:
- The scan endpoints require monkey-patching (LLM + httpx.AsyncClient), so those
  tests run in-process against the FastAPI app via httpx.AsyncClient(ASGITransport).
- The fluid budget + regression tests hit the deployed backend HTTP.
"""
import os
import sys
import base64
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
import requests
import httpx

sys.path.insert(0, "/app/backend")

BASE_URL = (os.environ.get("EXPO_PUBLIC_BACKEND_URL", "").rstrip("/")
            or "https://kidney-safe-swap.preview.emergentagent.com")
DEMO_EMAIL = "demo@renal.app"
DEMO_PASSWORD = "demo123"


# ---------- Install fake emergentintegrations before importing server ----------
# We use a per-test reply via a shared mutable holder.
_FAKE_REPLY = {"text": ""}


def _install_fake_llm_module():
    fake_mod = MagicMock()

    class FakeChat:
        def __init__(self, *a, **kw): pass
        def with_model(self, *a, **kw): return self
        async def send_message(self, msg):  # noqa: ARG002
            return _FAKE_REPLY["text"]

    class FakeImageContent:
        def __init__(self, *a, **kw): pass

    class FakeUserMessage:
        def __init__(self, *a, **kw): pass

    fake_mod.LlmChat = FakeChat
    fake_mod.ImageContent = FakeImageContent
    fake_mod.UserMessage = FakeUserMessage
    sys.modules["emergentintegrations.llm.chat"] = fake_mod


# ---------- HTTP-based fixtures for deployed backend ----------
@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}, timeout=30)
    if r.status_code != 200:
        requests.post(f"{BASE_URL}/api/auth/register",
                      json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD, "full_name": "Demo User"},
                      timeout=30)
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ---------- Async in-process client for scan tests ----------
@pytest_asyncio.fixture(loop_scope="module", scope="module")
async def app_client():
    _install_fake_llm_module()
    import server  # noqa: WPS433
    transport = httpx.ASGITransport(app=server.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        # login for token
        r = await c.post("/api/auth/login",
                         json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
        if r.status_code != 200:
            await c.post("/api/auth/register",
                         json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD,
                               "full_name": "Demo User"})
            r = await c.post("/api/auth/login",
                             json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
        assert r.status_code == 200, r.text
        tok = r.json()["access_token"]
        c.headers.update({"Authorization": f"Bearer {tok}"})
        yield c, server


def _fake_image_b64():
    return base64.b64encode(b"\xff\xd8\xff\xe0" + b"A" * 300).decode()


# ==================== BUG-P0: scan/food UNVERIFIED ====================
class TestScanFoodGrounding:
    @pytest.mark.asyncio(loop_scope="module")
    async def test_scan_food_no_db_match_returns_unverified(self, app_client):
        c, _ = app_client
        _FAKE_REPLY["text"] = '{"food_name": "zorplok curry xyz", "hindi_name": null}'
        r = await c.post("/api/scan/food",
                         json={"image_base64": _fake_image_b64()})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["safety_tier"] == "UNVERIFIED", data
        assert data["primary_risk_factor"] == "NONE"
        assert data["portion_limit_text"].startswith("Not in our verified database yet"), data
        assert data["matched_food_id"] is None
        assert data["safety_tier"] not in {"GREEN", "YELLOW", "RED"}

    @pytest.mark.asyncio(loop_scope="module")
    async def test_scan_food_parse_failure_returns_unverified(self, app_client):
        c, server_mod = app_client
        _FAKE_REPLY["text"] = "no json here at all"
        with patch.object(server_mod, "_extract_json", return_value=None):
            r = await c.post("/api/scan/food",
                             json={"image_base64": _fake_image_b64()})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["safety_tier"] == "UNVERIFIED"
        assert data["matched_food_id"] is None
        assert data["primary_risk_factor"] == "NONE"
        assert data["portion_limit_text"].startswith("Not in our verified database yet")

    @pytest.mark.asyncio(loop_scope="module")
    async def test_scan_food_db_match_regression(self, app_client):
        c, _ = app_client
        _FAKE_REPLY["text"] = '{"food_name": "Apple", "hindi_name": "Seb"}'
        r = await c.post("/api/scan/food",
                         json={"image_base64": _fake_image_b64()})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["matched_food_id"] is not None, data
        assert data["safety_tier"] in {"GREEN", "YELLOW", "RED"}, data


# ==================== BUG-P0: scan/barcode UNVERIFIED ====================
def _mock_async_client(off_json: dict):
    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json = MagicMock(return_value=off_json)

    class FakeAsyncClient:
        def __init__(self, *a, **kw): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def get(self, url):  # noqa: ARG002
            return fake_resp

    return FakeAsyncClient


class TestScanBarcodeGrounding:
    @pytest.mark.asyncio(loop_scope="module")
    async def test_barcode_empty_nutriments_returns_unverified_no_synthetic(self, app_client):
        c, server_mod = app_client
        barcode = "9998887776665"

        off_payload = {
            "status": 1,
            "product": {
                "product_name": "Unknown Test Snack Iter24",
                "brands": "TestBrand",
                "nutriments": {},
            },
        }
        FakeAsyncClient = _mock_async_client(off_payload)
        import httpx as _httpx
        with patch.object(_httpx, "AsyncClient", FakeAsyncClient):
            r = await c.post("/api/scan/barcode", json={"barcode": barcode})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["safety_tier"] == "UNVERIFIED", data
        assert data["matched_food_id"] is None, data
        assert data["portion_limit_text"].startswith("Not in our verified database yet"), data

        existing = await server_mod.db.foods.find_one({"id": f"bc_{barcode}"})
        assert existing is None, f"Synthetic food doc created for UNVERIFIED barcode: {existing}"

    @pytest.mark.asyncio(loop_scope="module")
    async def test_barcode_with_nutrients_regression_creates_bc_food(self, app_client):
        c, server_mod = app_client
        barcode = "1112223334445"

        off_payload = {
            "status": 1,
            "product": {
                "product_name": "Test Salty Snack Iter24",
                "brands": "TestBrand",
                "serving_quantity": 30,
                "nutriments": {
                    "potassium_serving": 0.180,   # g → 180 mg
                    "sodium_serving": 0.250,      # g → 250 mg
                    "phosphorus_serving": 0.050,  # g → 50 mg
                    "proteins_serving": 3.0,
                },
            },
        }
        FakeAsyncClient = _mock_async_client(off_payload)
        import httpx as _httpx
        with patch.object(_httpx, "AsyncClient", FakeAsyncClient):
            r = await c.post("/api/scan/barcode", json={"barcode": barcode})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["safety_tier"] in {"GREEN", "YELLOW", "RED"}, data
        assert data["safety_tier"] != "UNVERIFIED", data
        assert data["matched_food_id"] == f"bc_{barcode}", data

        doc = await server_mod.db.foods.find_one({"id": f"bc_{barcode}"}, {"_id": 0})
        assert doc is not None
        assert doc["source"] == "barcode"

        await server_mod.db.foods.delete_one({"id": f"bc_{barcode}"})


# ==================== FLUID BUDGET (HTTP) ====================
class TestFluidBudget:
    def test_summary_returns_fluid_ml(self, auth):
        from datetime import date
        today = date.today().isoformat()
        r = requests.get(f"{BASE_URL}/api/meal-logs/summary?date={today}",
                         headers=auth, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "fluid_ml" in data["limits"], data["limits"]
        assert data["limits"]["fluid_ml"] > 0

    def test_weekly_report_returns_fluid_ml(self, auth):
        r = requests.get(f"{BASE_URL}/api/reports/weekly",
                         headers=auth, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["limits"]["fluid_ml"] > 0

    def test_stage_default_fluid_dialysis_vs_predialysis(self, auth):
        from datetime import date
        today = date.today().isoformat()

        r = requests.post(f"{BASE_URL}/api/auth/stage",
                          json={"stage": "dialysis"}, headers=auth, timeout=30)
        assert r.status_code == 200, r.text
        r = requests.get(f"{BASE_URL}/api/meal-logs/summary?date={today}",
                         headers=auth, timeout=30)
        assert r.status_code == 200
        assert r.json()["limits"]["fluid_ml"] == 1000

        r = requests.post(f"{BASE_URL}/api/auth/stage",
                          json={"stage": "pre_dialysis"}, headers=auth, timeout=30)
        assert r.status_code == 200
        r = requests.get(f"{BASE_URL}/api/meal-logs/summary?date={today}",
                         headers=auth, timeout=30)
        assert r.json()["limits"]["fluid_ml"] == 2000

    def test_doctor_override_fluid(self, auth):
        r = requests.patch(f"{BASE_URL}/api/auth/profile",
                           json={"doctor_limits": {
                               "potassium_mg": None, "phosphorus_mg": None,
                               "sodium_mg": None, "fluid_ml": 1500}},
                           headers=auth, timeout=30)
        assert r.status_code == 200, r.text

        from datetime import date
        today = date.today().isoformat()
        r = requests.get(f"{BASE_URL}/api/meal-logs/summary?date={today}",
                         headers=auth, timeout=30)
        assert r.status_code == 200
        assert r.json()["limits"]["fluid_ml"] == 1500

        r = requests.patch(f"{BASE_URL}/api/auth/profile",
                           json={"doctor_limits": None},
                           headers=auth, timeout=30)
        assert r.status_code == 200


# ==================== REGRESSION (HTTP) ====================
class TestRegression:
    def test_foods_listing(self, auth):
        r = requests.get(f"{BASE_URL}/api/foods", headers=auth, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) > 0

    def test_food_apple(self, auth):
        r = requests.get(f"{BASE_URL}/api/foods/food-apple", headers=auth, timeout=30)
        assert r.status_code == 200

    def test_food_toor_dal(self, auth):
        r = requests.get(f"{BASE_URL}/api/foods/food-toor-dal", headers=auth, timeout=30)
        assert r.status_code == 200

    def test_auth_me(self, auth):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=auth, timeout=30)
        assert r.status_code == 200

    def test_ai_ask_grounded(self, auth):
        r = requests.post(f"{BASE_URL}/api/ai/ask",
                          json={"question": "Is apple safe for me?"},
                          headers=auth, timeout=60)
        assert r.status_code == 200

    def test_no_non_beverage_has_fluid(self, auth):
        r = requests.get(f"{BASE_URL}/api/foods", headers=auth, timeout=30)
        assert r.status_code == 200
        foods = r.json()
        violations = [f for f in foods
                      if (f.get("category") or "").lower() != "beverage"
                      and float(f.get("fluid_ml") or 0) > 0]
        assert not violations, f"Non-beverage foods with fluid_ml>0: {[v['id'] for v in violations[:5]]}"
