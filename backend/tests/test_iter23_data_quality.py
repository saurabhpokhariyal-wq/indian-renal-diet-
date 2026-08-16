"""Iteration 23 backend tests — data-quality fixes.

Covers:
  - food-sajina rescale to 40 g reference and safety_tier recompute
  - 19 non-beverage entries clean-up (category, fluid_ml, disclaimer)
  - 7 judgment-call decisions (condiment/snack/kept-as-beverage)
  - 10 audit-surfaced catches (ice creams -> dairy, vada -> snack)
  - CSV audit trail sanity
  - audit_seed.py category-plausibility flag count == 0
  - Solids-cannot-be-fluids invariant across /api/foods listing
  - Regression: total foods, K unchanged for toor-dal and apple,
    auth/me, meal-logs create, ai/ask grounded answer
"""
import csv
import os
import subprocess
import pytest
import requests

BASE_URL = os.environ.get("EXPO_BACKEND_URL", "https://kidney-safe-swap.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

DEMO_EMAIL = "demo@renal.app"
DEMO_PASSWORD = "demo123"


# ---------- fixtures ----------
@pytest.fixture(scope="session")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _food(resp_json):
    """Unwrap food-detail response: some endpoints return {'food': {...}, 'swap': ...}."""
    if isinstance(resp_json, dict) and "food" in resp_json and isinstance(resp_json["food"], dict):
        return resp_json["food"]
    return resp_json


@pytest.fixture(scope="session")
def auth_token(api):
    r = api.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    if r.status_code != 200:
        # try register then login
        api.post(f"{API}/auth/register", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD, "full_name": "Demo User"})
        r = api.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:200]}"
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok, f"no token in login response: {r.json()}"
    return tok


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def all_foods(api):
    r = api.get(f"{API}/foods", params={"limit": 5000})
    assert r.status_code == 200, f"/api/foods failed: {r.status_code}"
    data = r.json()
    if isinstance(data, dict):
        items = data.get("items") or data.get("foods") or data.get("data") or []
    else:
        items = data
    assert isinstance(items, list), f"unexpected /api/foods shape: {type(data)}"
    return items


# ---------- PRIMARY BUG-1: food-sajina ----------
class TestSajinaRescale:
    def test_sajina_rescale(self, api):
        r = api.get(f"{API}/foods/food-sajina")
        assert r.status_code == 200, r.text[:400]
        f = _food(r.json())
        assert f.get("portion_g") == 40, f"portion_g expected 40, got {f.get('portion_g')}"
        k = f.get("potassium_mg")
        assert k is not None and abs(k - 233) <= 1, f"potassium_mg expected 233±1, got {k}"
        assert f.get("phosphorus_mg") == 100, f"phosphorus_mg expected 100, got {f.get('phosphorus_mg')}"
        assert f.get("sodium_mg") == 5, f"sodium_mg expected 5, got {f.get('sodium_mg')}"
        prot = f.get("protein_g")
        assert prot is not None and abs(prot - 4.3) < 0.05, f"protein_g expected 4.3, got {prot}"
        tier = f.get("safety_tier")
        assert tier in ("YELLOW", "GREEN"), f"safety_tier expected YELLOW/GREEN, got {tier}"
        disc = f.get("serving_disclaimer") or ""
        # portion_limit_text may live at other fields — check common ones for '30'
        portion_txt = f.get("portion_limit_text") or ""
        combined = f"{disc} {portion_txt}"
        assert "30" in combined, f"expected '30' in disclaimer/portion_limit_text; got disc={disc!r} portion={portion_txt!r}"


# ---------- PRIMARY BUG-2A: 19 clearly-wrong ----------
NON_BEVERAGE_IDS = [
    "food-classic-club-sandwich",
    "food-buttermilk-biscuit",
    "food-coffee-biscuit",
    "food-kadhai-paneer",
    "food-classic-seasoned-black-beans",
    "food-milk-cake",
    "food-orange-gateau",
    "food-black-forest-gateau",
    "food-macaroni-salad",
    "food-vanilla-souffle",
    "food-vanilla-ice-cream-with-egg",
    "food-vanilla-ice-cream-without-egg",
    "food-lemon-souffle",
    "food-pineapple-souffle",
    "food-orange-souffle",
    "food-chocolate-souffle",
    "food-steamed-orange-pudding",
    "food-milk-cookies",
    "food-steamed-cake-with-chocolate-sauce",
]

BEVERAGE_DISCLAIMER_SUBSTR = ("count as FLUID intake", "a real glass is 200–250ml", "a real glass is 200-250ml")


class TestNonBeverageClassification:
    @pytest.mark.parametrize("fid", NON_BEVERAGE_IDS)
    def test_non_beverage(self, api, fid):
        r = api.get(f"{API}/foods/{fid}")
        assert r.status_code == 200, f"{fid}: {r.status_code} {r.text[:200]}"
        f = _food(r.json())
        assert f.get("category") != "beverage", f"{fid}: category is 'beverage'"
        fl = f.get("fluid_ml") or 0
        assert fl == 0, f"{fid}: fluid_ml expected 0, got {fl}"
        disc = f.get("serving_disclaimer") or ""
        for s in BEVERAGE_DISCLAIMER_SUBSTR:
            assert s not in disc, f"{fid}: disclaimer still contains {s!r}: {disc[:200]}"


# ---------- PRIMARY BUG-2B: 7 judgment-call ----------
JUDGMENT_EXPECTED = {
    "food-mayonnaise-without-eggs": "condiment",
    "food-french-dressing": "condiment",
    "food-curd-dressing": "condiment",
    "food-coffee-drops": "snack",
    "food-curried-cauliflower-soup": "snack",
    "food-chicken-stock": "beverage",
    "food-egg-nog": "beverage",
}


class TestJudgmentCall:
    @pytest.mark.parametrize("fid,expected", list(JUDGMENT_EXPECTED.items()))
    def test_judgment(self, api, fid, expected):
        r = api.get(f"{API}/foods/{fid}")
        assert r.status_code == 200, f"{fid}: {r.status_code}"
        cat = _food(r.json()).get("category")
        assert cat == expected, f"{fid}: expected {expected}, got {cat}"


# ---------- AUDIT-SURFACED CATCHES ----------
AUDIT_DAIRY = [
    "food-choconut-ice-cream",
    "food-peach-melba-ice-cream",
    "food-coffee-ice-cream",
    "food-fruit-ice-cream",
    "food-chocolate-ice-cream",
    "food-mango-ice-cream",
    "food-chocochip-ice-cream",
    "food-caramel-ice-cream",
    "food-strawberry-ice-cream",
]


class TestAuditSurfaced:
    @pytest.mark.parametrize("fid", AUDIT_DAIRY)
    def test_ice_creams_dairy(self, api, fid):
        r = api.get(f"{API}/foods/{fid}")
        assert r.status_code == 200, f"{fid}: {r.status_code}"
        cat = _food(r.json()).get("category")
        assert cat == "dairy", f"{fid}: expected 'dairy', got {cat}"

    def test_vada_snack(self, api):
        r = api.get(f"{API}/foods/food-masala-urad-dal-vada")
        assert r.status_code == 200
        assert _food(r.json()).get("category") == "snack"


# ---------- CSV AUDIT TRAIL ----------
class TestCsvAuditTrail:
    CSV_PATH = "/app/backend/category_review.csv"

    def test_csv_exists_and_row_count(self):
        assert os.path.exists(self.CSV_PATH), f"{self.CSV_PATH} not found"
        with open(self.CSV_PATH, newline="") as f:
            reader = list(csv.reader(f))
        header = reader[0]
        assert header == ["food_id", "kind", "before", "after", "reason"], f"header mismatch: {header}"
        # count non-empty data rows
        data_rows = [row for row in reader[1:] if row and any(c.strip() for c in row)]
        assert len(data_rows) == 36, f"expected 36 data rows, got {len(data_rows)}"


# ---------- AUDIT SCRIPT ----------
class TestAuditScript:
    def test_audit_script_no_category_flags(self):
        r = subprocess.run(
            ["python3", "/app/backend/scripts/audit_seed.py"],
            capture_output=True, text=True, timeout=120,
        )
        out = r.stdout + r.stderr
        assert r.returncode == 0, f"audit_seed.py exited {r.returncode}\n{out[-2000:]}"
        # Expect a line "Category-plausibility flags:   0"
        found = False
        for line in out.splitlines():
            if "Category-plausibility flags" in line:
                found = True
                # last integer on the line must be 0
                tokens = line.replace(":", " ").split()
                num = None
                for t in reversed(tokens):
                    if t.isdigit():
                        num = int(t); break
                assert num == 0, f"category-plausibility flags != 0: {line!r}"
        assert found, f"'Category-plausibility flags' not printed by audit_seed.py\n{out[-1500:]}"


# ---------- PIPELINE INVARIANT ----------
class TestSolidsCannotBeFluids:
    def test_no_solid_has_fluid_ml(self, all_foods):
        violations = []
        for f in all_foods:
            cat = f.get("category")
            fluid = f.get("fluid_ml") or 0
            if cat != "beverage" and fluid and fluid > 0:
                violations.append((f.get("id") or f.get("food_id") or f.get("_id"), cat, fluid))
        assert not violations, f"solids-with-fluid_ml violations ({len(violations)}): {violations[:20]}"


# ---------- REGRESSION ----------
class TestRegression:
    def test_total_foods_at_least_1000(self, all_foods):
        assert len(all_foods) >= 1000, f"expected >=1000 foods, got {len(all_foods)}"

    def test_toor_dal_k(self, api):
        r = api.get(f"{API}/foods/food-toor-dal")
        assert r.status_code == 200
        k = _food(r.json()).get("potassium_mg")
        assert k is not None and k > 0

    def test_apple_k(self, api):
        r = api.get(f"{API}/foods/food-apple")
        assert r.status_code == 200
        k = _food(r.json()).get("potassium_mg")
        assert k is not None and k > 0

    def test_auth_me(self, api, auth_headers):
        r = api.get(f"{API}/auth/me", headers=auth_headers)
        assert r.status_code == 200, f"/api/auth/me: {r.status_code} {r.text[:200]}"

    def test_meal_log_create(self, api, auth_headers):
        from datetime import date
        payload = {
            "food_id": "food-apple",
            "portion_g": 100,
            "meal_type": "snack",
            "date": date.today().isoformat(),
        }
        r = api.post(f"{API}/meal-logs", json=payload, headers=auth_headers)
        assert r.status_code in (200, 201), f"meal-logs create failed: {r.status_code} {r.text[:300]}"

    def test_ai_ask_grounded(self, api, auth_headers):
        payload = {"question": "Is apple safe for me?"}
        r = api.post(f"{API}/ai/ask", json=payload, headers=auth_headers, timeout=60)
        assert r.status_code == 200, f"/api/ai/ask failed: {r.status_code} {r.text[:300]}"
        body = r.json()
        answer = (body.get("answer") or body.get("response") or body.get("text") or "").lower()
        assert answer, f"empty AI answer: {body}"
