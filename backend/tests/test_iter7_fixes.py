"""Iteration 7 spot-check: PATCH /auth/profile doctor_limits null/empty/absent semantics."""
import os
import uuid
import time

import pytest
import requests

BASE_URL = (
    os.environ.get("EXPO_PUBLIC_BACKEND_URL")
    or os.environ.get("EXPO_BACKEND_URL")
    or "https://kidney-safe-swap.preview.emergentagent.com"
).rstrip("/")
API = f"{BASE_URL}/api"


def _register():
    email = f"TEST_{uuid.uuid4().hex[:10]}@renal.app"
    r = requests.post(
        f"{API}/auth/register",
        json={"email": email, "password": "pass1234", "full_name": "T"},
        timeout=20,
    )
    # tolerate 429 by retrying
    if r.status_code == 429:
        time.sleep(65)
        r = requests.post(
            f"{API}/auth/register",
            json={"email": email, "password": "pass1234", "full_name": "T"},
            timeout=20,
        )
    assert r.status_code == 200, r.text
    return {
        "email": email,
        "headers": {
            "Authorization": f"Bearer {r.json()['access_token']}",
            "Content-Type": "application/json",
        },
    }


@pytest.fixture(scope="module")
def user():
    return _register()


def _me(u):
    r = requests.get(f"{API}/auth/me", headers=u["headers"], timeout=15)
    assert r.status_code == 200, r.text
    return r.json()


def _patch(u, payload):
    r = requests.patch(f"{API}/auth/profile", headers=u["headers"], json=payload, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()


class TestDoctorLimitsSemantics:
    def test_1_set_partial_doctor_limits(self, user):
        out = _patch(user, {"doctor_limits": {"potassium_mg": 1800}})
        assert out["doctor_limits"] is not None
        assert out["doctor_limits"]["potassium_mg"] == 1800
        assert out["doctor_limits"]["phosphorus_mg"] is None
        assert out["doctor_limits"]["sodium_mg"] is None
        assert out["doctor_limits"]["fluid_ml"] is None
        me = _me(user)
        assert me["doctor_limits"]["potassium_mg"] == 1800

    def test_2_explicit_null_clears(self, user):
        # ensure something is set first
        _patch(user, {"doctor_limits": {"potassium_mg": 1800}})
        out = _patch(user, {"doctor_limits": None})
        assert out["doctor_limits"] is None
        me = _me(user)
        assert me["doctor_limits"] is None

    def test_3_summary_reverts_to_stage_defaults_after_clear(self, user):
        # stage=unknown for fresh user → 2400/1200/2300
        from datetime import date
        today = date.today().isoformat()
        r = requests.get(
            f"{API}/meal-logs/summary",
            params={"date": today},
            headers=user["headers"],
            timeout=15,
        )
        assert r.status_code == 200
        limits = r.json()["limits"]
        assert limits == {"potassium_mg": 2400, "phosphorus_mg": 1200, "sodium_mg": 2300}

    def test_4_empty_object_clears(self, user):
        _patch(user, {"doctor_limits": {"potassium_mg": 1800}})
        out = _patch(user, {"doctor_limits": {}})
        assert out["doctor_limits"] is None

    def test_5_empty_payload_is_noop(self, user):
        # first set a known state
        _patch(user, {"doctor_limits": {"phosphorus_mg": 900}})
        _patch(user, {"diabetic": True})
        before = _me(user)
        out = _patch(user, {})
        assert out["doctor_limits"] == before["doctor_limits"]
        assert out["diabetic"] == before["diabetic"]
        # explicitly still set
        assert out["doctor_limits"] is not None
        assert out["doctor_limits"]["phosphorus_mg"] == 900
        assert out["diabetic"] is True

    def test_6_diabetic_only_does_not_touch_doctor_limits(self, user):
        # ensure limits set
        _patch(user, {"doctor_limits": {"sodium_mg": 1500}})
        before = _me(user)
        assert before["doctor_limits"]["sodium_mg"] == 1500
        out = _patch(user, {"diabetic": False})
        assert out["diabetic"] is False
        # doctor_limits UNTOUCHED
        assert out["doctor_limits"] is not None
        assert out["doctor_limits"]["sodium_mg"] == 1500
        me = _me(user)
        assert me["doctor_limits"]["sodium_mg"] == 1500
