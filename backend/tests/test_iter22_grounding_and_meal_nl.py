"""Iter 22 backend tests: AI grounding P0 fix, /ai/log-meal parse, quantity_multiplier
propagation, guide visibility, and regression on existing endpoints."""
from __future__ import annotations

import os
import re
import time
from typing import Any, Dict, Optional

import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL",
    "https://safe-food-guide-1.preview.emergentagent.com").rstrip("/")
EMAIL = "demo@renal.app"
PASSWORD = "demo123"

TIER_WORDS = re.compile(r"\b(SAFE|CAUTION|AVOID)\b", re.IGNORECASE)
DISCLAIMER_KEYWORDS = (
    "don't have verified", "do not have verified", "not in", "database",
    "search or scan", "dietitian", "verified data",
)


# ---- fixtures ----------------------------------------------------------------
@pytest.fixture(scope="module")
def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def token(session: requests.Session) -> str:
    # Try login, register if missing.
    r = session.post(f"{BASE_URL}/api/auth/login",
                     json={"email": EMAIL, "password": PASSWORD})
    if r.status_code == 401:
        r = session.post(f"{BASE_URL}/api/auth/register",
                         json={"email": EMAIL, "password": PASSWORD, "full_name": "Demo"})
    assert r.status_code == 200, f"auth failed {r.status_code}: {r.text}"
    tok = r.json()["access_token"]
    return tok


@pytest.fixture(scope="module")
def auth(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _ask(session, auth, question: str, lang: str = "en") -> Dict[str, Any]:
    time.sleep(0.4)  # be gentle on rate-limits
    r = session.post(f"{BASE_URL}/api/ai/ask", headers=auth,
                     json={"question": question, "lang": lang})
    return {"status": r.status_code, "body": r.json() if r.headers.get("content-type","" ).startswith("application/json") else r.text}


# ---- P0 grounding fix -------------------------------------------------------
class TestAiAskGrounding:
    def test_made_up_dish_not_classified(self, session, auth):
        # zorplok curry is invented — model MUST NOT emit SAFE/CAUTION/AVOID.
        res = _ask(session, auth, "is zorplok curry safe for me?")
        assert res["status"] == 200, res
        ans: str = res["body"]["answer"]
        print("Zorplok answer:\n", ans)
        # Must mention lack of verified data / not in DB.
        lower = ans.lower()
        assert any(k in lower for k in DISCLAIMER_KEYWORDS), \
            f"Expected 'no data' disclaimer, got: {ans}"
        # Must NOT include a hard classification tier for the invented food.
        # It's OK to mention 'safe' in general phrases; the RED-flag is the
        # confident SAFE/CAUTION/AVOID triad the base prompt was using.
        tiers = TIER_WORDS.findall(ans)
        # Zero explicit tier verdicts is the P0 success criterion.
        assert len(tiers) == 0, f"Model still emitted tier(s) {tiers} for made-up dish: {ans}"

    def test_known_food_potato_grounded(self, session, auth):
        res = _ask(session, auth, "is potato safe for me?")
        assert res["status"] == 200, res
        ans = res["body"]["answer"].lower()
        print("Potato answer:\n", ans)
        # Should mention potato/aloo and reference safety.
        assert ("potato" in ans or "aloo" in ans), f"Should mention potato/aloo: {ans}"

    def test_guide_only_khoa(self, session, auth):
        res = _ask(session, auth, "is khoa safe?")
        assert res["status"] == 200, res
        ans = res["body"]["answer"].lower()
        print("Khoa answer:\n", ans)
        assert ("khoa" in ans or "mawa" in ans), f"Should mention khoa/mawa: {ans}"
        # Should convey a red/avoid or high-phosphorus notion.
        assert any(k in ans for k in ["red", "avoid", "phosphorus", "not safe", "limit"]), \
            f"Expected red/phosphorus signal: {ans}"

    def test_guide_only_water_chestnut(self, session, auth):
        res = _ask(session, auth, "what about water chestnut?")
        assert res["status"] == 200, res
        ans = res["body"]["answer"].lower()
        print("Water chestnut answer:\n", ans)
        assert "water chestnut" in ans or "singhara" in ans or "singhare" in ans, \
            f"Should mention water chestnut/singhara: {ans}"

    def test_tamil_unicode_preserved(self, session, auth):
        # Tamil for mango is மாம்பழம் — endpoint must not crash and must not strip it.
        res = _ask(session, auth, "மாம்பழம் safe?", lang="ta")
        assert res["status"] == 200, res
        # Just verify the endpoint returns a non-empty answer without 500.
        assert isinstance(res["body"].get("answer"), str)
        assert len(res["body"]["answer"]) > 0


# ---- AI log-meal parse -------------------------------------------------------
class TestAiLogMeal:
    def test_meal_parse_returns_items(self, session, auth):
        # Count logs before.
        pre = session.get(f"{BASE_URL}/api/meal-logs?date=2026-08-16", headers=auth)
        assert pre.status_code == 200
        pre_count = len(pre.json())

        r = session.post(
            f"{BASE_URL}/api/ai/log-meal", headers=auth,
            json={"text": "2 rotis, 1 katori dal, small bowl of curd",
                  "date": "2026-08-16", "meal_type": "lunch", "lang": "en"},
        )
        assert r.status_code == 200, f"{r.status_code}: {r.text}"
        body = r.json()
        items = body["parsed_items"]
        print("Parsed items:", items)
        assert len(items) >= 2, f"Expected >=2 items, got {len(items)}: {items}"

        for it in items:
            assert isinstance(it["item_text"], str) and it["item_text"]
            assert isinstance(it["quantity_multiplier"], (int, float))
            assert it["outcome"] in {"match_single", "match_multiple", "no_match"}
            assert isinstance(it["candidates"], list)
            for cand in it["candidates"]:
                # Nutrients MUST NOT leak into candidates.
                assert "potassium_mg" not in cand, f"potassium_mg leaked: {cand}"
                assert "phosphorus_mg" not in cand
                assert "food_id" in cand and "name" in cand and "safety_tier" in cand

        # Find roti item and check quantity >=2.
        roti_items = [it for it in items if "roti" in it["item_text"].lower()]
        if roti_items:
            assert roti_items[0]["quantity_multiplier"] >= 2.0, \
                f"Expected roti qty>=2, got {roti_items[0]}"

        # No writes to meal_logs.
        post = session.get(f"{BASE_URL}/api/meal-logs?date=2026-08-16", headers=auth)
        assert post.status_code == 200
        assert len(post.json()) == pre_count, "ai/log-meal should not write"


# ---- Quantity multiplier propagation ----------------------------------------
class TestQuantityMultiplier:
    def test_create_and_verify_summary(self, session, auth):
        # Get apple K value first.
        r = session.get(f"{BASE_URL}/api/foods/food-apple", headers=auth)
        assert r.status_code == 200, r.text
        apple_k = r.json()["food"]["potassium_mg"]

        # Create log with qty=2.0
        c = session.post(f"{BASE_URL}/api/meal-logs", headers=auth,
                         json={"food_id": "food-apple", "date": "2026-08-16",
                               "meal_type": "lunch", "quantity_multiplier": 2.0})
        assert c.status_code == 200, c.text
        log_id = c.json()["id"]
        assert c.json()["quantity_multiplier"] == 2.0

        try:
            # GET returns log with qty=2.
            g = session.get(f"{BASE_URL}/api/meal-logs?date=2026-08-16", headers=auth)
            assert g.status_code == 200
            match = [x for x in g.json() if x["id"] == log_id]
            assert match and match[0]["quantity_multiplier"] == 2.0

            # Summary reflects 2x apple K.
            s = session.get(f"{BASE_URL}/api/meal-logs/summary?date=2026-08-16", headers=auth)
            assert s.status_code == 200
            k_total = s.json()["totals"]["potassium_mg"]
            # Should be >= 2×apple K (may include other logs, so lower bound only).
            assert k_total >= round(2 * apple_k, 0) - 1, \
                f"Expected >= {2*apple_k}, got {k_total}"
        finally:
            session.delete(f"{BASE_URL}/api/meal-logs/{log_id}", headers=auth)

    def test_quantity_validation_zero_rejected(self, session, auth):
        r = session.post(f"{BASE_URL}/api/meal-logs", headers=auth,
                         json={"food_id": "food-apple", "date": "2026-08-16",
                               "meal_type": "lunch", "quantity_multiplier": 0})
        assert r.status_code == 422, r.status_code

    def test_quantity_validation_high_rejected(self, session, auth):
        r = session.post(f"{BASE_URL}/api/meal-logs", headers=auth,
                         json={"food_id": "food-apple", "date": "2026-08-16",
                               "meal_type": "lunch", "quantity_multiplier": 15})
        assert r.status_code == 422, r.status_code

    def test_quantity_default_one(self, session, auth):
        r = session.post(f"{BASE_URL}/api/meal-logs", headers=auth,
                         json={"food_id": "food-apple", "date": "2026-08-16",
                               "meal_type": "lunch"})
        assert r.status_code == 200, r.text
        assert r.json()["quantity_multiplier"] == 1.0
        session.delete(f"{BASE_URL}/api/meal-logs/{r.json()['id']}", headers=auth)


# ---- Weekly report scaling ---------------------------------------------------
class TestWeeklyReport:
    def test_weekly_scales_with_qty(self, session, auth):
        from datetime import date
        today = date.today().isoformat()

        # Fetch apple K value.
        f = session.get(f"{BASE_URL}/api/foods/food-apple", headers=auth)
        assert f.status_code == 200
        apple_k = f.json()["food"]["potassium_mg"]

        # Baseline weekly.
        b = session.get(f"{BASE_URL}/api/reports/weekly", headers=auth)
        assert b.status_code == 200
        base_avg_k = b.json()["avg_daily"]["potassium_mg"]

        # Create qty=3 apple log today.
        c = session.post(f"{BASE_URL}/api/meal-logs", headers=auth,
                         json={"food_id": "food-apple", "date": today,
                               "meal_type": "lunch", "quantity_multiplier": 3.0})
        assert c.status_code == 200, c.text
        log_id = c.json()["id"]

        try:
            w = session.get(f"{BASE_URL}/api/reports/weekly", headers=auth)
            assert w.status_code == 200
            new_avg_k = w.json()["avg_daily"]["potassium_mg"]
            expected_delta = round(3 * apple_k / 7, 1)
            actual_delta = round(new_avg_k - base_avg_k, 1)
            print(f"apple_k={apple_k} expected_delta≈{expected_delta} actual_delta={actual_delta}")
            # Allow ±1 mg rounding slack.
            assert abs(actual_delta - expected_delta) <= 1.5, \
                f"Delta mismatch: expected ~{expected_delta}, got {actual_delta}"
        finally:
            session.delete(f"{BASE_URL}/api/meal-logs/{log_id}", headers=auth)


# ---- Regression --------------------------------------------------------------
class TestRegression:
    def test_foods_list(self, session, auth):
        r = session.get(f"{BASE_URL}/api/foods?limit=5", headers=auth)
        assert r.status_code == 200
        assert isinstance(r.json(), list) and len(r.json()) > 0

    def test_toor_dal_detail(self, session, auth):
        r = session.get(f"{BASE_URL}/api/foods/food-toor-dal", headers=auth)
        assert r.status_code == 200
        assert r.json()["food"]["id"] == "food-toor-dal"

    def test_auth_me(self, session, auth):
        r = session.get(f"{BASE_URL}/api/auth/me", headers=auth)
        assert r.status_code == 200
        assert r.json()["email"] == EMAIL

    def test_meal_logs_list_ok(self, session, auth):
        r = session.get(f"{BASE_URL}/api/meal-logs?date=2026-08-16", headers=auth)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
