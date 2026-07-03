"""Iteration 8 backend tests:
   - POST /api/ai/ask grounded prompt behavior
   - POST /api/scan/food DB override behavior
   - Quick regression on iter 1-7 endpoints.
"""
import base64
import os
import time
import uuid

import pytest
import requests

BASE_URL = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")


# ---------- helpers ----------
def _register(email=None):
    email = email or f"TEST_{uuid.uuid4().hex[:8]}@renal.app"
    r = requests.post(f"{BASE_URL}/api/auth/register",
                      json={"email": email, "password": "TestPass123", "full_name": "T"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"], email


def _login_demo():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": "demo@renal.app", "password": "demo123"})
    if r.status_code != 200:
        # first-time: register
        r = requests.post(f"{BASE_URL}/api/auth/register",
                          json={"email": "demo@renal.app", "password": "demo123",
                                "full_name": "Demo User"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _hdr(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def _set_stage(tok, stage):
    r = requests.post(f"{BASE_URL}/api/auth/stage", headers=_hdr(tok),
                      json={"stage": stage})
    assert r.status_code == 200, r.text
    return r.json()


# ============ AI grounding tests ============
class TestAiGrounding:
    def test_red_palak_paneer_dialysis(self):
        tok = _login_demo()
        _set_stage(tok, "dialysis")
        r = requests.post(f"{BASE_URL}/api/ai/ask", headers=_hdr(tok),
                          json={"question": "Can I eat palak paneer for dinner?",
                                "lang": "en"})
        assert r.status_code == 200, r.text
        ans = r.json()["answer"].lower()
        assert ans, "empty answer"
        # Must classify as avoid/red/dangerous
        assert any(k in ans for k in ["avoid", "red", "danger", "unsafe",
                                      "not safe", "shouldn't", "should not",
                                      "harmful", "risky"]), f"Expected AVOID-tier language. Got: {ans[:400]}"
        # Should NOT say palak paneer itself is safe/green/ok (must be avoid-tier).
        # We check that the phrase "palak paneer is safe / is green / is fine"
        # doesn't appear — but the answer may still call the SWAP (lauki) safe.
        forbidden = [
            "palak paneer is safe",
            "palak paneer is green",
            "palak paneer is fine",
            "palak paneer is ok",
            "palak paneer is okay",
            "you can eat palak paneer",
            "palak paneer is perfectly",
        ]
        assert not any(bad in ans for bad in forbidden), \
            f"Answer wrongly says palak paneer itself is safe: {ans[:400]}"
        # Should mention DB potassium value OR swap food OR benefit
        signals = ["650", "lauki", "80%", "519", "80 %"]
        assert any(s in ans for s in signals), \
            f"Expected 650mg / Lauki / 80% / 519mg signal. Got: {ans[:400]}"

    def test_toor_dal_softened_predialysis(self):
        tok, _ = _register()
        _set_stage(tok, "pre_dialysis")
        # allow rate-limit budget
        time.sleep(1)
        r = requests.post(f"{BASE_URL}/api/ai/ask", headers=_hdr(tok),
                          json={"question": "Is toor dal ok for me?", "lang": "en"})
        assert r.status_code == 200, r.text
        ans = r.json()["answer"].lower()
        # Should NOT flatly avoid it
        assert "avoid" not in ans or "don't avoid" in ans or "not avoid" in ans, \
            f"Should NOT tell pre-dialysis to avoid toor dal. Got: {ans[:400]}"
        # Should mention softened / individualized / safe-with-portion
        # signals: safe/green/individual/pre-dialysis/soak/portion
        assert any(s in ans for s in [
            "safe", "green", "fine", "ok", "okay", "individual", "kdoqi",
            "pre-dialysis", "predialysis", "soak", "portion", "half katori",
            "half a katori", "half-katori"
        ]), f"Expected softened guidance. Got: {ans[:400]}"

    def test_no_match_still_200(self):
        tok, _ = _register()
        time.sleep(1)
        r = requests.post(f"{BASE_URL}/api/ai/ask", headers=_hdr(tok),
                          json={"question": "Hello, how are you?"})
        assert r.status_code == 200, r.text
        assert r.json().get("answer"), "empty answer for greeting"

    def test_hindi_palak_paneer_red(self):
        tok, _ = _register()
        _set_stage(tok, "dialysis")
        time.sleep(1)
        r = requests.post(f"{BASE_URL}/api/ai/ask", headers=_hdr(tok),
                          json={"question": "क्या मैं पालक पनीर खा सकता हूँ?",
                                "lang": "hi"})
        assert r.status_code == 200, r.text
        ans = r.json()["answer"]
        # Devanagari present
        assert any('\u0900' <= c <= '\u097F' for c in ans), \
            f"Expected Devanagari script. Got: {ans[:400]}"
        low = ans.lower()
        # RED / avoid / टालें / न खाएं / avoid keywords
        assert any(k in ans for k in ["टालें", "न खाएं", "मना", "बचें",
                                       "नहीं", "avoid", "RED"]) \
               or any(k in low for k in ["avoid", "red", "danger", "unsafe"]), \
            f"Expected RED/avoid classification in Hindi. Got: {ans[:400]}"

    def test_rate_limit_429(self):
        tok, _ = _register()
        # 10/minute limit — 11th should 429
        codes = []
        for i in range(12):
            r = requests.post(f"{BASE_URL}/api/ai/ask", headers=_hdr(tok),
                              json={"question": f"tiny question {i}"})
            codes.append(r.status_code)
            if r.status_code == 429:
                break
        assert 429 in codes, f"Expected 429 after 10 requests. Got codes: {codes}"


# ============ Scan override tests ============
class TestScanOverride:
    @staticmethod
    def _b64(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()

    def test_scan_match_overrides_db(self):
        tok = _login_demo()
        _set_stage(tok, "dialysis")
        # Samosa image reliably identified as "Samosa" by the vision model,
        # which matches seed food-samosa (RED / SODIUM).
        img_path = "/tmp/scan_samosa1.jpg"
        if not os.path.exists(img_path):
            pytest.skip("Test image not available")
        b64 = self._b64(img_path)
        r = requests.post(f"{BASE_URL}/api/scan/food", headers=_hdr(tok),
                          json={"image_base64": b64}, timeout=90)
        assert r.status_code == 200, r.text
        data = r.json()
        if not data.get("matched_food_id"):
            pytest.skip(f"Vision did not match a seeded food ({data.get('food_name')}). "
                        f"Cannot verify DB override.")
        fid = data["matched_food_id"]
        # Fetch DB card
        r2 = requests.get(f"{BASE_URL}/api/foods/{fid}", headers=_hdr(tok))
        assert r2.status_code == 200, r2.text
        food = r2.json()["food"]
        # DB override fields must match exactly
        assert data["portion_limit_text"] == food["portion_limit_text"], \
            f"portion mismatch: scan={data['portion_limit_text']!r} db={food['portion_limit_text']!r}"
        assert data["clinical_tip"] == food["actionable_clinical_tip"], \
            f"tip mismatch: scan={data['clinical_tip']!r} db={food['actionable_clinical_tip']!r}"
        assert data["food_name"] == food["name"]
        assert data["hindi_name"] == food["hindi_name"]
        # tier should equal personal_tier (dialysis)
        assert data["safety_tier"] == food["personal_tier"], \
            f"tier mismatch: scan={data['safety_tier']} personal={food['personal_tier']}"

    def test_scan_no_match_passes_through(self):
        tok = _login_demo()
        # Random Picsum photo (not food) → vision returns Unknown or an unseeded dish.
        img_path = "/tmp/img_480.jpg"
        if not os.path.exists(img_path):
            pytest.skip("Test image not available")
        b64 = self._b64(img_path)
        time.sleep(15)  # respect scan rate limit (5/min)
        r = requests.post(f"{BASE_URL}/api/scan/food", headers=_hdr(tok),
                          json={"image_base64": b64}, timeout=90)
        assert r.status_code == 200, r.text
        data = r.json()
        # For a non-food or unseeded dish, matched_food_id must be null and
        # the tier / name should be whatever the vision model returned.
        assert data.get("matched_food_id") is None, \
            f"Expected no match. Got matched_food_id={data.get('matched_food_id')} food={data.get('food_name')}"
        assert data["safety_tier"] in {"GREEN", "YELLOW", "RED"}
        assert data["food_name"]  # non-empty


# ============ Regression on iter 1-7 endpoints ============
class TestRegression:
    def test_full_flow(self):
        tok, email = _register()
        h = _hdr(tok)

        # /auth/me
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=h)
        assert r.status_code == 200 and r.json()["email"].lower() == email.lower()

        # /foods?q
        r = requests.get(f"{BASE_URL}/api/foods?q=lauki", headers=h)
        assert r.status_code == 200
        foods = r.json()
        assert any(f["id"] == "food-lauki-sabzi" for f in foods)

        # favorites toggle
        r = requests.post(f"{BASE_URL}/api/favorites/food-lauki-sabzi", headers=h)
        assert r.status_code == 200 and r.json()["is_favorite"] is True
        r = requests.post(f"{BASE_URL}/api/favorites/food-lauki-sabzi", headers=h)
        assert r.status_code == 200 and r.json()["is_favorite"] is False

        # meal log CRUD
        today = "2026-01-15"
        r = requests.post(f"{BASE_URL}/api/meal-logs", headers=h,
                          json={"food_id": "food-lauki-sabzi", "date": today,
                                "meal_type": "lunch"})
        assert r.status_code == 200, r.text
        log_id = r.json()["id"]
        r = requests.get(f"{BASE_URL}/api/meal-logs?date={today}", headers=h)
        assert r.status_code == 200 and any(m["id"] == log_id for m in r.json())
        r = requests.delete(f"{BASE_URL}/api/meal-logs/{log_id}", headers=h)
        assert r.status_code == 200

        # PATCH /auth/profile with {doctor_limits: null}
        r = requests.patch(f"{BASE_URL}/api/auth/profile", headers=h,
                           json={"doctor_limits": None})
        assert r.status_code == 200, r.text
        assert r.json()["doctor_limits"] is None

        # /reports/weekly
        r = requests.get(f"{BASE_URL}/api/reports/weekly", headers=h)
        assert r.status_code == 200
        body = r.json()
        for k in ("start_date", "end_date", "days", "avg_daily", "limits"):
            assert k in body
