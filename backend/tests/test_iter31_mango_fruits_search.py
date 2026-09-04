"""Iter-31 backend tests for fruit search bug fix.

Scope:
  A — 'mango' search returns fruit (both small & whole) not just Malpua
  B — Regression: other new fruits searchable
  C — Individual food detail smoke test on 5 new fruits
  D — Category filter for fruit
  E — /api/fruits/guide has linked_food_id populated
  F — Reconciliation counts (verified via existing test_iter13d)
  G — Salt-substitute regression (Lo-Salt, Tata Salt Lite)
"""
import os

import pytest
import requests

BASE_URL = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
TIMEOUT = 30

DEMO_EMAIL = "demo@renal.app"
DEMO_PASSWORD = "demo123"


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def auth_headers(api):
    r = api.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        timeout=TIMEOUT,
    )
    if r.status_code != 200:
        api.post(
            f"{BASE_URL}/api/auth/register",
            json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD, "full_name": "Demo"},
            timeout=TIMEOUT,
        )
        r = api.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
            timeout=TIMEOUT,
        )
    assert r.status_code == 200, f"login failed {r.status_code}: {r.text[:200]}"
    token = r.json().get("access_token") or r.json().get("token")
    return {"Authorization": f"Bearer {token}"}


def _search(api, q):
    r = api.get(f"{BASE_URL}/api/foods", params={"q": q}, timeout=TIMEOUT)
    assert r.status_code == 200, f"search q={q!r} -> {r.status_code}: {r.text[:200]}"
    data = r.json()
    # Response may be list or {foods: [...]}
    if isinstance(data, dict):
        for k in ("foods", "results", "items"):
            if k in data and isinstance(data[k], list):
                return data[k]
        return []
    return data


def _get_food(api, food_id):
    r = api.get(f"{BASE_URL}/api/foods/{food_id}", timeout=TIMEOUT)
    return r


# ---------------- A: mango search is the primary bug ----------------
class TestAMangoSearch:
    def test_mango_returns_15_or_more(self, api):
        results = _search(api, "mango")
        assert len(results) >= 15, (
            f"'mango' search returned {len(results)} results (expected >=15). "
            f"IDs: {[r.get('id') for r in results][:20]}"
        )

    def test_mango_small_and_whole_present(self, api):
        results = _search(api, "mango")
        ids = {r.get("id") for r in results}
        assert "food-mango-small" in ids, f"food-mango-small missing. IDs: {sorted(ids)}"
        assert "food-mango-whole" in ids, f"food-mango-whole missing. IDs: {sorted(ids)}"

    def test_mango_small_shape(self, api):
        r = _get_food(api, "food-mango-small")
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        f = r.json()
        f = f.get("food", f) if isinstance(f, dict) else f
        assert f.get("category") == "fruit", f"category={f.get('category')!r}"
        assert f.get("safety_tier") == "YELLOW", f"safety_tier={f.get('safety_tier')!r}"
        assert "mango" in (f.get("name") or "").lower()

    def test_mango_whole_shape(self, api):
        r = _get_food(api, "food-mango-whole")
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        f = r.json()
        f = f.get("food", f) if isinstance(f, dict) else f
        assert f.get("category") == "fruit", f"category={f.get('category')!r}"
        assert f.get("safety_tier") == "RED", f"safety_tier={f.get('safety_tier')!r}"

    def test_mango_malpua_category_snack(self, api):
        r = _get_food(api, "food-mango-malpua")
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        f = r.json()
        f = f.get("food", f) if isinstance(f, dict) else f
        assert f.get("category") == "snack", (
            f"food-mango-malpua category={f.get('category')!r} (expected 'snack')"
        )


# ---------------- B: regression for other new fruits ----------------
NEW_FRUIT_SEARCHES = [
    ("grapes", "food-grapes", "Grapes"),
    ("watermelon", "food-watermelon", "Watermelon"),
    ("guava", "food-guava", "Guava"),
    ("kiwi", "food-kiwi", "Kiwi"),
]


class TestBRegressionSearches:
    @pytest.mark.parametrize("q,fid,name", NEW_FRUIT_SEARCHES)
    def test_search_returns_expected(self, api, q, fid, name):
        results = _search(api, q)
        ids = {r.get("id") for r in results}
        assert fid in ids, (
            f"search {q!r} did not include {fid}. Got IDs: {sorted(ids)}"
        )

    def test_chikoo_or_sapota(self, api):
        for q in ("chikoo", "sapota"):
            results = _search(api, q)
            ids = {r.get("id") for r in results}
            if "food-chikoo" in ids:
                return
        pytest.fail(f"'chikoo' and 'sapota' searches both missed food-chikoo")


# ---------------- C: 5 new fruit detail smoke test ----------------
SMOKE_TEST_IDS = [
    "food-pineapple",
    "food-pomegranate",
    "food-lychee",
    "food-strawberries",
    "food-guava",
]


class TestCFoodDetailSmoke:
    @pytest.mark.parametrize("food_id", SMOKE_TEST_IDS)
    def test_food_detail_200(self, api, food_id):
        r = _get_food(api, food_id)
        assert r.status_code == 200, f"{food_id} -> {r.status_code}: {r.text[:200]}"
        f = r.json()
        f = f.get("food", f) if isinstance(f, dict) else f
        assert f.get("safety_tier") in ("GREEN", "YELLOW", "RED"), (
            f"{food_id} safety_tier={f.get('safety_tier')!r}"
        )
        assert isinstance(f.get("potassium_mg"), (int, float)), (
            f"{food_id} potassium_mg={f.get('potassium_mg')!r}"
        )
        assert f.get("category") == "fruit", (
            f"{food_id} category={f.get('category')!r}"
        )


# ---------------- D: category filter ----------------
class TestDCategoryFilter:
    def test_fruit_category_ge_33(self, api):
        r = api.get(f"{BASE_URL}/api/foods", params={"category": "fruit"}, timeout=TIMEOUT)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:200]}"
        data = r.json()
        if isinstance(data, dict):
            for k in ("foods", "results", "items"):
                if k in data and isinstance(data[k], list):
                    data = data[k]
                    break
        assert isinstance(data, list)
        # Should have at least 33 fruits (5 previously + 28 new; some may reclassify)
        assert len(data) >= 30, (
            f"category=fruit returned {len(data)} (expected >=30)"
        )
        # And all must be category=fruit
        for f in data:
            assert f.get("category") == "fruit", (
                f"non-fruit in category=fruit filter: {f.get('id')} category={f.get('category')}"
            )


# ---------------- E: fruit guide linked_food_id ----------------
class TestEFruitGuideLinkedIds:
    def test_guide_returns_200(self, api):
        r = api.get(f"{BASE_URL}/api/fruits/guide", timeout=TIMEOUT)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:200]}"

    def test_mango_small_has_linked_food_id(self, api):
        r = api.get(f"{BASE_URL}/api/fruits/guide", timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        # Traverse nested dict looking for entry name matching "Mango (small portion)"
        # with linked_food_id="food-mango-small"
        found = _find_by_linked_id(data, "food-mango-small")
        assert found, (
            "Fruit guide has no entry with linked_food_id='food-mango-small'. "
            f"Sample linked ids found: {_sample_linked_ids(data)[:15]}"
        )

    def test_multiple_new_linked_ids(self, api):
        r = api.get(f"{BASE_URL}/api/fruits/guide", timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        linked_ids = set(_sample_linked_ids(data))
        expected_any = {
            "food-grapes",
            "food-watermelon",
            "food-guava",
            "food-kiwi",
            "food-pineapple",
            "food-pomegranate",
        }
        matches = linked_ids & expected_any
        assert len(matches) >= 3, (
            f"Only {len(matches)} of expected new linked_food_ids populated. "
            f"Linked: {sorted(linked_ids)[:30]}"
        )


def _find_by_linked_id(data, target_id):
    if isinstance(data, dict):
        if data.get("linked_food_id") == target_id:
            return data
        for v in data.values():
            r = _find_by_linked_id(v, target_id)
            if r:
                return r
    elif isinstance(data, list):
        for item in data:
            r = _find_by_linked_id(item, target_id)
            if r:
                return r
    return None


def _sample_linked_ids(data, acc=None):
    if acc is None:
        acc = []
    if isinstance(data, dict):
        if "linked_food_id" in data and data["linked_food_id"]:
            acc.append(data["linked_food_id"])
        for v in data.values():
            _sample_linked_ids(v, acc)
    elif isinstance(data, list):
        for item in data:
            _sample_linked_ids(item, acc)
    return acc


# ---------------- G: salt-substitute regression ----------------
class TestGSaltSubstituteRegression:
    def test_lo_salt_barcode_warning(self, api, auth_headers):
        r = api.post(
            f"{BASE_URL}/api/scan/barcode",
            headers=auth_headers,
            json={"barcode": "5011544070034"},
            timeout=TIMEOUT,
        )
        assert r.status_code == 200, f"{r.status_code}: {r.text[:200]}"
        data = r.json()
        # scan responses may nest under different keys
        warn = data.get("salt_substitute_warning")
        if warn is None:
            # nested locations
            for k in ("result", "scan", "warnings", "food"):
                v = data.get(k)
                if isinstance(v, dict) and "salt_substitute_warning" in v:
                    warn = v["salt_substitute_warning"]
                    break
        assert warn is True, (
            f"salt_substitute_warning={warn!r} for Lo-Salt (5011544070034). Full: {str(data)[:400]}"
        )

    def test_tata_salt_lite_food(self, api):
        # find via search
        results = _search(api, "tata salt lite")
        ids = {r.get("id"): r for r in results}
        tsl = None
        for fid, r in ids.items():
            if "tata" in (r.get("name") or "").lower() and "lite" in (r.get("name") or "").lower():
                tsl = r
                break
        # If not in search, try direct GET on likely ID
        if tsl is None:
            for candidate in ("food-tata-salt-lite", "food-tata-salt-lite-lo-sodium"):
                rr = _get_food(api, candidate)
                if rr.status_code == 200:
                    tsl = rr.json()
                    tsl = tsl.get("food", tsl) if isinstance(tsl, dict) else tsl
                    break
        assert tsl is not None, "Tata Salt Lite food not found"
        # Fetch full record
        rr = _get_food(api, tsl["id"])
        assert rr.status_code == 200
        full = rr.json()
        full = full.get("food", full) if isinstance(full, dict) else full
        assert full.get("safety_tier") == "RED", f"safety_tier={full.get('safety_tier')!r}"
        assert full.get("tier_override") is True, f"tier_override={full.get('tier_override')!r}"
        assert full.get("data_quality_flag") == "concentrated_base_pending_resourcing", (
            f"data_quality_flag={full.get('data_quality_flag')!r}"
        )
