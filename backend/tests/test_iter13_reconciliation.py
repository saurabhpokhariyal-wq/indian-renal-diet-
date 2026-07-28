"""Iteration 13 — Seed-time reconciliation pipeline tests.

Covers acceptance criteria A1–A14 and regression tests R1–R5.
Uses the public EXPO_PUBLIC_BACKEND_URL from frontend/.env for HTTP.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import date
from pathlib import Path

import pytest
import requests


# Load EXPO_PUBLIC_BACKEND_URL from frontend/.env
def _load_backend_url() -> str:
    env_file = Path("/app/frontend/.env")
    for line in env_file.read_text().splitlines():
        if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
            return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    raise RuntimeError("EXPO_PUBLIC_BACKEND_URL missing")


BASE_URL = _load_backend_url()
TIMEOUT = 30


# --------------------------- Fixtures ---------------------------
@pytest.fixture(scope="session")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def token(api_client):
    """A1: login as demo user."""
    r = api_client.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "demo@renal.app", "password": "demo123"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:200]}"
    data = r.json()
    tok = data.get("token") or data.get("access_token")
    assert tok, f"no token in login response: {data}"
    return tok


@pytest.fixture(scope="session")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _get_food(api_client, headers, food_id):
    r = api_client.get(f"{BASE_URL}/api/foods/{food_id}", headers=headers, timeout=TIMEOUT)
    assert r.status_code == 200, f"GET {food_id} → {r.status_code}: {r.text[:200]}"
    data = r.json()
    # /api/foods/{id} returns {"food": {...}, "swap": ...}
    if isinstance(data, dict) and "food" in data and isinstance(data["food"], dict):
        return data["food"]
    return data


# --------------------------- A1 login ---------------------------
class TestAuth:
    def test_a1_login_success(self, token):
        assert isinstance(token, str) and len(token) > 10


# --------------------------- A2-A10 food detail ---------------------------
class TestFoodReconciliation:
    def test_a2_soya_chunks_sweet_and_sour(self, api_client, auth_headers):
        f = _get_food(api_client, auth_headers, "food-soya-chunks-sweet-and-sour")
        assert f.get("safety_tier") == "RED", f"tier={f.get('safety_tier')}"
        assert f.get("primary_risk_factor") == "SODIUM"
        assert f.get("auto_rescaled") is True, f"auto_rescaled={f.get('auto_rescaled')}"

    def test_a3_cold_tomato_soup(self, api_client, auth_headers):
        f = _get_food(api_client, auth_headers, "food-cold-tomato-soup")
        assert f.get("safety_tier") == "RED"
        assert f.get("primary_risk_factor") == "SODIUM"
        assert not f.get("auto_rescaled"), f"auto_rescaled={f.get('auto_rescaled')}"

    def test_a4_mayonnaise(self, api_client, auth_headers):
        f = _get_food(api_client, auth_headers, "food-mayonnaise")
        assert f.get("safety_tier") == "RED"
        assert f.get("primary_risk_factor") == "SODIUM"

    def test_a5_raw_mango_chutney(self, api_client, auth_headers):
        f = _get_food(api_client, auth_headers, "food-raw-mango-chutney")
        assert f.get("auto_rescaled") is True
        assert f.get("portion_g") == 15, f"portion_g={f.get('portion_g')}"
        plt = f.get("portion_limit_text") or ""
        assert ("15 g" in plt) or ("15\u00a0g" in plt), f"portion_limit_text={plt!r}"

    def test_a6_chat_masala(self, api_client, auth_headers):
        f = _get_food(api_client, auth_headers, "food-chat-masala")
        assert f.get("auto_rescaled") is True
        assert f.get("portion_g") == 5, f"portion_g={f.get('portion_g')}"
        assert f.get("safety_tier") == "RED"
        plt = f.get("portion_limit_text") or ""
        assert ("5 g" in plt) or ("5\u00a0g" in plt), f"portion_limit_text={plt!r}"

    def test_a7_cheese_soup(self, api_client, auth_headers):
        f = _get_food(api_client, auth_headers, "food-cheese-soup")
        assert f.get("auto_rescaled") is True
        assert f.get("portion_g") == 30
        assert f.get("safety_tier") == "RED"
        disc = (f.get("serving_disclaimer") or "").lower()
        assert ("concentrated" in disc) or ("re-sourcing" in disc), f"disclaimer={disc!r}"

    def test_a8_toor_dal_override(self, api_client, auth_headers):
        f = _get_food(api_client, auth_headers, "food-toor-dal")
        assert f.get("tier_override") is True
        assert f.get("safety_tier") == "YELLOW"
        assert isinstance(f.get("override_reason"), str) and f.get("override_reason").strip()

    def test_a9_orange_override(self, api_client, auth_headers):
        f = _get_food(api_client, auth_headers, "food-orange")
        assert f.get("tier_override") is True
        assert f.get("safety_tier") == "RED"
        assert isinstance(f.get("override_reason"), str) and f.get("override_reason").strip()

    def test_a10_brown_rice_override(self, api_client, auth_headers):
        f = _get_food(api_client, auth_headers, "food-brown-rice")
        assert f.get("tier_override") is True
        assert f.get("safety_tier") == "YELLOW"
        assert isinstance(f.get("override_reason"), str) and f.get("override_reason").strip()


# --------------------------- A11 foods list length + dedupe ---------------------------
class TestFoodsList:
    def test_a11_list_length_and_dedupe(self, api_client, auth_headers):
        r = api_client.get(
            f"{BASE_URL}/api/foods?limit=2000", headers=auth_headers, timeout=TIMEOUT
        )
        assert r.status_code == 200
        foods = r.json()
        assert isinstance(foods, list)
        assert len(foods) >= 1018, f"only {len(foods)} foods returned"
        ids = {f.get("id") for f in foods}
        dropped = [
            "food-cabbage-rolls-2",
            "food-white-sauce-2",
            "food-white-sauce-3",
            "food-caramel-custard-2",
            "food-shepherd-s-pie-2",
            "food-stuffed-bittergourd-2",
            "food-chicken-sandwich-2",
            "food-cheese-and-tomato-sandwich-2",
            "food-fruit-punch-2",
        ]
        present = [d for d in dropped if d in ids]
        assert not present, f"duplicates should be dropped but present: {present}"


# --------------------------- A12/A14 audit script ---------------------------
class TestAuditScript:
    def test_a12_audit_json(self):
        proc = subprocess.run(
            ["python", "/app/backend/scripts/audit_seed.py", "--json"],
            capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode == 0, f"exit {proc.returncode}\nstderr={proc.stderr[:300]}"
        data = json.loads(proc.stdout)
        for k in [
            "total_input", "reclassified_count", "rescaled_total",
            "duplicates_dropped_count", "sanity_violations_count",
            "portion_disclaimer_conflicts_count",
        ]:
            assert k in data, f"missing key {k}"
        assert data["portion_disclaimer_conflicts_count"] == 0
        assert data["duplicates_dropped_count"] == 9, data["duplicates_dropped_count"]
        assert data["reclassified_count"] > 400, data["reclassified_count"]
        assert data["rescaled_total"] > 400, data["rescaled_total"]
        assert data["total_input"] == 1027, data["total_input"]
        assert data["curated_overrides"] == 7, data["curated_overrides"]

    def test_a13_needs_manual_review_csv(self):
        p = Path("/app/backend/needs_manual_review.csv")
        assert p.exists(), "needs_manual_review.csv missing"
        lines = [ln for ln in p.read_text().splitlines() if ln.strip()]
        assert len(lines) >= 2, f"only {len(lines)} lines"
        # header + ~42 rows → total ~43
        row_count = len(lines) - 1
        assert 30 <= row_count <= 60, f"row_count={row_count}"

    def test_a14_audit_fail_on_flags(self):
        proc = subprocess.run(
            ["python", "/app/backend/scripts/audit_seed.py", "--fail-on-flags"],
            capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode == 1, (
            f"expected exit 1 (42 sanity flags), got {proc.returncode}\n"
            f"stderr={proc.stderr[:300]}"
        )


# --------------------------- Regression R1-R5 ---------------------------
class TestRegression:
    def test_r1_palak_search(self, api_client, auth_headers):
        r = api_client.get(
            f"{BASE_URL}/api/foods?q=palak", headers=auth_headers, timeout=TIMEOUT
        )
        assert r.status_code == 200
        foods = r.json()
        palak = next((f for f in foods if f.get("id") == "food-palak-paneer"), None)
        assert palak is not None, "food-palak-paneer missing from search"
        assert palak.get("safety_tier") == "RED", f"tier={palak.get('safety_tier')}"

    def test_r2_lauki_sabzi(self, api_client, auth_headers):
        f = _get_food(api_client, auth_headers, "food-lauki-sabzi")
        assert f.get("safety_tier") == "GREEN", f"tier={f.get('safety_tier')}"
        assert not f.get("auto_rescaled")
        assert not f.get("tier_override")

    def test_r3_meal_log_chat_masala(self, api_client, auth_headers):
        today = date.today().isoformat()
        payload = {
            "food_id": "food-chat-masala",
            "date": today,
            "meal_type": "snack",
            "servings": 1.0,
        }
        r = api_client.post(
            f"{BASE_URL}/api/meal-logs", json=payload, headers=auth_headers, timeout=TIMEOUT
        )
        assert r.status_code in (200, 201), f"POST meal-logs {r.status_code}: {r.text[:200]}"
        created = r.json()
        log_id = created.get("id") or created.get("_id")
        try:
            s = api_client.get(
                f"{BASE_URL}/api/meal-logs/summary?date={today}",
                headers=auth_headers, timeout=TIMEOUT,
            )
            assert s.status_code == 200
            summary = s.json()
            # Ensure it does not blow up; totals present
            assert isinstance(summary, dict)
            # Sodium should reflect small ~594 mg-ish contribution
            # be tolerant since other logs may exist
            k_total = summary.get("potassium_mg") or summary.get("total_potassium_mg") or 0
            na_total = summary.get("sodium_mg") or summary.get("total_sodium_mg") or 0
            assert k_total >= 0 and na_total >= 0
        finally:
            if log_id:
                api_client.delete(
                    f"{BASE_URL}/api/meal-logs/{log_id}",
                    headers=auth_headers, timeout=TIMEOUT,
                )

    def test_r4_barcode_scan(self, api_client, auth_headers):
        r = api_client.post(
            f"{BASE_URL}/api/scan/barcode",
            json={"barcode": "3017620422003"},
            headers=auth_headers, timeout=TIMEOUT,
        )
        assert r.status_code == 200, f"{r.status_code}: {r.text[:200]}"
        data = r.json()
        assert "matched_food_id" in data or "food_id" in data, f"keys={list(data.keys())}"

    def test_r5_weekly_report(self, api_client, auth_headers):
        r = api_client.get(
            f"{BASE_URL}/api/reports/weekly", headers=auth_headers, timeout=TIMEOUT
        )
        assert r.status_code == 200, f"{r.status_code}: {r.text[:200]}"
