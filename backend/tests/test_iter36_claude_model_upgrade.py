# Iter-36: Claude model upgrade (claude-sonnet-5-5) — AI ask, NL meal logging, vision scan
import base64
import datetime
import os
import re
from pathlib import Path

import pytest
import requests

BASE_URL = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL")).rstrip("/")
API = f"{BASE_URL}/api"
FIXTURE = Path(__file__).parent / "fixtures" / "indian_food.jpg"
BACKEND = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def auth():
    r = requests.post(f"{API}/auth/login", json={"email": "demo@renal.app", "password": "demo123"}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"login failed {r.status_code}")
    tok = r.json().get("access_token") or r.json().get("token")
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


# --- Config wiring ---
class TestModelConfig:
    def test_config_model_value(self):
        src = (BACKEND / "config.py").read_text()
        assert '"claude-sonnet-5-5"' in src

    def test_routes_use_config_model(self):
        ai = (BACKEND / "routes" / "ai.py").read_text()
        scan = (BACKEND / "routes" / "scan.py").read_text()
        assert len(re.findall(r'with_model\("anthropic",\s*CLAUDE_MODEL\)', ai)) == 2
        assert len(re.findall(r'with_model\("anthropic",\s*CLAUDE_MODEL\)', scan)) == 1
        # No stale hard-coded model ids left anywhere in routes
        assert "claude-sonnet-4" not in ai + scan


# --- AI ask ---
class TestAiAsk:
    def test_ask_banana(self, auth):
        r = requests.post(f"{API}/ai/ask", headers=auth,
                          json={"question": "Can I eat banana on dialysis? Answer briefly.", "lang": "en"}, timeout=90)
        assert r.status_code == 200, r.text
        ans = r.json()["answer"]
        assert isinstance(ans, str) and len(ans) > 40
        assert "potassium" in ans.lower()

    def test_ask_hindi(self, auth):
        r = requests.post(f"{API}/ai/ask", headers=auth,
                          json={"question": "क्या मैं दाल खा सकता हूँ?", "lang": "hi"}, timeout=90)
        assert r.status_code == 200, r.text
        ans = r.json()["answer"]
        assert re.search(r"[\u0900-\u097F]", ans), "expected Devanagari in Hindi answer"

    def test_ask_empty_400(self, auth):
        r = requests.post(f"{API}/ai/ask", headers=auth, json={"question": "   "}, timeout=20)
        assert r.status_code == 400

    def test_ask_unauth(self):
        r = requests.post(f"{API}/ai/ask", json={"question": "hi"}, timeout=20)
        assert r.status_code in (401, 403)


# --- AI log meal ---
class TestAiLogMeal:
    def test_log_meal_parses_items(self, auth):
        today = datetime.date.today().isoformat()
        r = requests.post(f"{API}/ai/log-meal", headers=auth,
                          json={"text": "2 rotis, 1 katori dal and half bowl rice", "date": today,
                                "meal_type": "lunch", "lang": "en"}, timeout=90)
        assert r.status_code == 200, r.text
        items = r.json()["parsed_items"]
        # LLM extraction must split into >=3 items (fallback would return 1 whole-string item)
        assert len(items) >= 3, items
        texts = " ".join(i["item_text"].lower() for i in items)
        assert "roti" in texts and "dal" in texts and "rice" in texts
        roti = next(i for i in items if "roti" in i["item_text"].lower())
        assert roti["quantity_multiplier"] == pytest.approx(2.0)
        rice = next(i for i in items if "rice" in i["item_text"].lower())
        assert rice["quantity_multiplier"] == pytest.approx(0.5)
        for i in items:
            assert i["outcome"] in ("match_single", "match_multiple", "no_match")
        matched = [i for i in items if i["outcome"] != "no_match"]
        assert matched, "expected at least one DB match"
        c = matched[0]["candidates"][0]
        for k in ("food_id", "name", "safety_tier", "portion_limit_text"):
            assert k in c

    def test_candidate_nutrients_from_db(self, auth):
        today = datetime.date.today().isoformat()
        r = requests.post(f"{API}/ai/log-meal", headers=auth,
                          json={"text": "1 roti", "date": today}, timeout=90)
        assert r.status_code == 200, r.text
        items = r.json()["parsed_items"]
        assert items and items[0]["candidates"]
        fid = items[0]["candidates"][0]["food_id"]
        g = requests.get(f"{API}/foods/{fid}", headers=auth, timeout=20)
        assert g.status_code == 200
        food = g.json().get("food", g.json())
        for k in ("potassium_mg", "phosphorus_mg", "sodium_mg", "protein_g"):
            assert isinstance(food.get(k), (int, float))

    def test_log_meal_empty_400(self, auth):
        r = requests.post(f"{API}/ai/log-meal", headers=auth, json={"text": " ", "date": "2026-01-10"}, timeout=20)
        assert r.status_code == 400


# --- Vision scan ---
class TestScanFood:
    def test_scan_real_photo(self, auth):
        b64 = base64.b64encode(FIXTURE.read_bytes()).decode()
        r = requests.post(f"{API}/scan/food", headers=auth, json={"image_base64": b64}, timeout=120)
        assert r.status_code == 200, r.text
        d = r.json()
        print("SCAN RESULT:", {k: d.get(k) for k in ("food_name", "safety_tier", "matched_food_id", "primary_risk_factor")})
        assert d["food_name"] and d["food_name"] != "Unknown dish"
        assert d["safety_tier"] in ("GREEN", "YELLOW", "RED", "UNVERIFIED")
        assert d["portion_limit_text"] and d["clinical_tip"]
        assert isinstance(d["salt_substitute_warning"], bool)
        if d["matched_food_id"] is None:
            assert d["safety_tier"] == "UNVERIFIED"

    def test_scan_data_uri_prefix(self, auth):
        b64 = "data:image/jpeg;base64," + base64.b64encode(FIXTURE.read_bytes()).decode()
        r = requests.post(f"{API}/scan/food", headers=auth, json={"image_base64": b64}, timeout=120)
        assert r.status_code == 200, r.text
        assert r.json()["food_name"]

    def test_scan_invalid_b64(self, auth):
        r = requests.post(f"{API}/scan/food", headers=auth, json={"image_base64": "not-base64!!"}, timeout=20)
        assert r.status_code == 400
