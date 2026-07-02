"""Iteration 6 backend tests — user profile / doctor_limits / personal_tier / AI context.

Covers:
- GET /api/auth/me — new diabetic + doctor_limits fields
- PATCH /api/auth/profile — partial updates, clearing, empty patch, auth
- GET /api/meal-logs/summary + /api/reports/weekly — limits use doctor_limits when set
- Personal-tier & personalized_note across stages (dialysis / pre_dialysis / unknown)
- POST /api/ai/ask — accepts lang, Hindi returns Devanagari, works with 0 meal logs
"""

import os
import re
import uuid
import time
import pytest
import requests

BASE_URL = os.environ["EXPO_BACKEND_URL"].rstrip("/")


# ---------- Fixtures ----------
@pytest.fixture(scope="module")
def http():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _register(http, email=None, password="TestPass1"):
    email = email or f"TEST_{uuid.uuid4().hex[:8]}@renal.app"
    r = http.post(f"{BASE_URL}/api/auth/register",
                  json={"email": email, "password": password, "full_name": "Test User"})
    assert r.status_code == 200, r.text
    data = r.json()
    return data["access_token"], data["user"], email


def _auth(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def fresh_user(http):
    token, user, email = _register(http)
    return {"token": token, "user": user, "email": email}


# ---------- /auth/me new fields ----------
class TestAuthMeNewFields:
    def test_me_returns_diabetic_and_doctor_limits_defaults(self, http, fresh_user):
        r = http.get(f"{BASE_URL}/api/auth/me", headers=_auth(fresh_user["token"]))
        assert r.status_code == 200, r.text
        me = r.json()
        assert me["diabetic"] is False
        assert me["doctor_limits"] is None
        assert me["stage"] == "unknown"


# ---------- PATCH /auth/profile ----------
class TestProfilePatch:
    def test_patch_requires_auth(self, http):
        r = http.patch(f"{BASE_URL}/api/auth/profile", json={"diabetic": True})
        assert r.status_code == 401

    def test_set_diabetic_true(self, http, fresh_user):
        r = http.patch(f"{BASE_URL}/api/auth/profile",
                       json={"diabetic": True}, headers=_auth(fresh_user["token"]))
        assert r.status_code == 200
        assert r.json()["diabetic"] is True
        # Verify via /me
        me = http.get(f"{BASE_URL}/api/auth/me", headers=_auth(fresh_user["token"])).json()
        assert me["diabetic"] is True

    def test_partial_doctor_limits(self, http, fresh_user):
        r = http.patch(f"{BASE_URL}/api/auth/profile",
                       json={"doctor_limits": {"potassium_mg": 1800, "sodium_mg": 1500}},
                       headers=_auth(fresh_user["token"]))
        assert r.status_code == 200
        dl = r.json()["doctor_limits"]
        assert dl is not None
        assert dl["potassium_mg"] == 1800
        assert dl["sodium_mg"] == 1500
        assert dl.get("phosphorus_mg") is None
        assert dl.get("fluid_ml") is None
        # Verify persisted
        me = http.get(f"{BASE_URL}/api/auth/me", headers=_auth(fresh_user["token"])).json()
        assert me["doctor_limits"]["potassium_mg"] == 1800
        assert me["doctor_limits"]["sodium_mg"] == 1500

    def test_empty_patch_returns_unchanged(self, http, fresh_user):
        before = http.get(f"{BASE_URL}/api/auth/me", headers=_auth(fresh_user["token"])).json()
        r = http.patch(f"{BASE_URL}/api/auth/profile", json={}, headers=_auth(fresh_user["token"]))
        assert r.status_code == 200
        after = r.json()
        assert after["diabetic"] == before["diabetic"]
        assert after["doctor_limits"] == before["doctor_limits"]

    def test_clear_doctor_limits(self, http, fresh_user):
        r = http.patch(f"{BASE_URL}/api/auth/profile",
                       json={"doctor_limits": None}, headers=_auth(fresh_user["token"]))
        # Setting None currently means "don't update" per implementation. Verify via re-set to empty dict clearing.
        # Per server code: doctor_limits None means skip. So test the explicit-empty behavior instead.
        assert r.status_code == 200
        # Now clear via empty-fields dict (server treats empty-after-exclude_none as None)
        r2 = http.patch(f"{BASE_URL}/api/auth/profile",
                        json={"doctor_limits": {}}, headers=_auth(fresh_user["token"]))
        assert r2.status_code == 200
        assert r2.json()["doctor_limits"] is None


# ---------- Limits in summary + weekly ----------
class TestLimitsForUser:
    def test_summary_uses_doctor_limits_when_set(self, http):
        token, _u, _email = _register(http)
        # dialysis stage
        r = http.post(f"{BASE_URL}/api/auth/stage", json={"stage": "dialysis"}, headers=_auth(token))
        assert r.status_code == 200
        # set only potassium override
        r = http.patch(f"{BASE_URL}/api/auth/profile",
                       json={"doctor_limits": {"potassium_mg": 1800}}, headers=_auth(token))
        assert r.status_code == 200
        # summary
        today = time.strftime("%Y-%m-%d")
        s = http.get(f"{BASE_URL}/api/meal-logs/summary?date={today}", headers=_auth(token)).json()
        assert s["limits"]["potassium_mg"] == 1800
        assert s["limits"]["phosphorus_mg"] == 1000  # dialysis default
        assert s["limits"]["sodium_mg"] == 2000  # dialysis default
        # weekly
        w = http.get(f"{BASE_URL}/api/reports/weekly", headers=_auth(token)).json()
        assert w["limits"]["potassium_mg"] == 1800
        assert w["limits"]["phosphorus_mg"] == 1000
        assert w["limits"]["sodium_mg"] == 2000
        # clear limits and expect stage defaults everywhere
        http.patch(f"{BASE_URL}/api/auth/profile",
                   json={"doctor_limits": {}}, headers=_auth(token))
        s2 = http.get(f"{BASE_URL}/api/meal-logs/summary?date={today}", headers=_auth(token)).json()
        assert s2["limits"] == {"potassium_mg": 2000, "phosphorus_mg": 1000, "sodium_mg": 2000}

    def test_pre_dialysis_defaults(self, http):
        token, _u, _e = _register(http)
        http.post(f"{BASE_URL}/api/auth/stage", json={"stage": "pre_dialysis"}, headers=_auth(token))
        today = time.strftime("%Y-%m-%d")
        s = http.get(f"{BASE_URL}/api/meal-logs/summary?date={today}", headers=_auth(token)).json()
        assert s["limits"] == {"potassium_mg": 2400, "phosphorus_mg": 1200, "sodium_mg": 2300}


# ---------- Personal tier & note ----------
class TestPersonalTier:
    @pytest.fixture(scope="class")
    def tokens(self, http):
        pre = _register(http)[0]
        http.post(f"{BASE_URL}/api/auth/stage", json={"stage": "pre_dialysis"}, headers=_auth(pre))
        dia = _register(http)[0]
        http.post(f"{BASE_URL}/api/auth/stage", json={"stage": "dialysis"}, headers=_auth(dia))
        unk = _register(http)[0]
        return {"pre": pre, "dia": dia, "unk": unk}

    def _food(self, http, token, food_id):
        r = http.get(f"{BASE_URL}/api/foods/{food_id}", headers=_auth(token))
        assert r.status_code == 200, r.text
        return r.json()["food"]

    def test_dialysis_phosphorus_tightens_to_red(self, http, tokens):
        f = self._food(http, tokens["dia"], "food-atta-roti")
        assert f["safety_tier"] == "YELLOW"
        assert f["primary_risk_factor"] == "PHOSPHORUS"
        assert f["personal_tier"] == "RED"
        assert f.get("personalized_note") in (None, "")

    def test_pre_dialysis_potassium_softens_to_green(self, http, tokens):
        f = self._food(http, tokens["pre"], "food-toor-dal")
        assert f["safety_tier"] == "YELLOW"
        assert f["primary_risk_factor"] == "POTASSIUM"
        assert f["personal_tier"] == "GREEN"
        assert f["personalized_note"], "note must be present"
        assert f["personalized_note"].startswith("Often fine before dialysis")

    def test_pre_dialysis_sodium_not_softened(self, http, tokens):
        f = self._food(http, tokens["pre"], "food-idli")
        assert f["safety_tier"] == "YELLOW"
        assert f["primary_risk_factor"] == "SODIUM"
        assert f["personal_tier"] == "YELLOW"
        assert f.get("personalized_note") in (None, "")

    def test_pre_dialysis_phosphorus_not_softened(self, http, tokens):
        f = self._food(http, tokens["pre"], "food-atta-roti")
        assert f["safety_tier"] == "YELLOW"
        assert f["primary_risk_factor"] == "PHOSPHORUS"
        assert f["personal_tier"] == "YELLOW"
        assert f.get("personalized_note") in (None, "")

    def test_unknown_stage_no_change_no_note(self, http, tokens):
        f = self._food(http, tokens["unk"], "food-toor-dal")
        assert f["personal_tier"] == "YELLOW"
        assert f.get("personalized_note") in (None, "")


# ---------- Ask AI ----------
class TestAskAI:
    def test_ask_english(self, http, fresh_user):
        r = http.post(f"{BASE_URL}/api/ai/ask",
                      json={"question": "Is lauki safe?", "lang": "en"},
                      headers=_auth(fresh_user["token"]))
        assert r.status_code == 200, r.text
        ans = r.json()["answer"]
        assert isinstance(ans, str) and len(ans) > 10
        # Should not be mostly Devanagari
        deva = sum(1 for ch in ans if "\u0900" <= ch <= "\u097F")
        assert deva < len(ans) * 0.2, f"English answer had too much Devanagari: {ans[:200]}"

    def test_ask_hindi_returns_devanagari(self, http, fresh_user):
        r = http.post(f"{BASE_URL}/api/ai/ask",
                      json={"question": "Is lauki safe?", "lang": "hi"},
                      headers=_auth(fresh_user["token"]))
        assert r.status_code == 200, r.text
        ans = r.json()["answer"]
        deva = sum(1 for ch in ans if "\u0900" <= ch <= "\u097F")
        assert deva >= 20, f"Expected Devanagari content, got: {ans[:200]}"
        # Cheap sanity: at least one common Hindi word
        assert re.search(r"है|हैं|नहीं|सुरक्षित|के|के लिए|मे|में", ans), f"No common Hindi words: {ans[:200]}"

    def test_ask_works_with_zero_meal_logs(self, http):
        # Fresh user has no meal logs
        token, _u, _e = _register(http)
        r = http.post(f"{BASE_URL}/api/ai/ask",
                      json={"question": "What should I eat?", "lang": "en"},
                      headers=_auth(token))
        assert r.status_code == 200, r.text
        assert isinstance(r.json()["answer"], str)
