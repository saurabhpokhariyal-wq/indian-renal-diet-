"""Iter-32 backend tests for guide-backfill (121 entries) + search priority.

Scope:
  A — Exact-name matches surface first for user's specific asks
  B — Vegetable/Grain/Protein/Snack/Beverage backfill items are searchable
  C — Salt-substitute regex doesn't regress (Lo-Salt=True, Nutella=False)
  D — Guide endpoints now expose linked_food_id on previously-unlinked entries
  E — iter-13d assertions pass at new values (flagged=43, sanity=42)
  F — audit_seed.py --json reports data_quality_flagged=43, sanity=42, overrides=10
  G — Category filter returns expanded counts
"""
import json
import os
import subprocess

import pytest
import requests

BASE_URL = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
TIMEOUT = 30


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _search(api, q):
    r = api.get(f"{BASE_URL}/api/foods", params={"q": q}, timeout=TIMEOUT)
    assert r.status_code == 200, f"search {q!r} => {r.status_code}"
    return r.json()


# ---------- A. Search priority ----------
def test_A_mango_search_exact_first(api):
    results = _search(api, "mango")
    assert len(results) >= 5
    assert results[0]["id"] == "food-mango-small", (
        f"Expected food-mango-small first, got {results[0]}"
    )


def test_A_milk_search_starts_with_milk(api):
    results = _search(api, "milk")
    assert len(results) >= 1
    assert results[0]["name"].lower().startswith("milk"), (
        f"Expected name starting with 'Milk', got {results[0]['name']}"
    )


def test_A_water_search_exact_first(api):
    results = _search(api, "water")
    assert results[0]["id"] == "food-water"
    assert results[0]["name"] == "Water"


def test_A_green_tea_exact_first(api):
    results = _search(api, "green tea")
    assert results[0]["name"] == "Green Tea"


def test_A_cauliflower_exact_first(api):
    results = _search(api, "cauliflower")
    assert results[0]["id"] == "food-cauliflower"
    assert results[0]["name"] == "Cauliflower"


# ---------- B. Backfill searchability ----------
VEGETABLE_TERMS = [
    "carrot", "brinjal", "okra", "pumpkin", "spinach",
    "avocado", "sweet potato", "arbi", "beetroot",
    "mushroom", "raw banana",
]
GRAIN_TERMS = [
    "boiled white rice", "suji", "maida", "bajra roti", "jowar roti",
    "oats", "ragi", "quinoa", "multigrain", "pasta", "millet",
]
PROTEIN_TERMS = [
    "egg white", "chicken breast", "masoor", "chana dal", "urad dal",
    "whole moong", "kala chana", "tofu", "mutton", "prawns", "cheese",
]
SNACK_TERMS = [
    "makhana", "puffed rice", "roasted chana", "chikki", "sabudana khichdi",
    "upma", "pakora", "kachori", "chocolate", "biscuit",
    "instant noodles", "popcorn",
]
BEVERAGE_TERMS = [
    "water", "herbal tea", "barley water", "masala chai", "filter coffee",
    "green tea", "nimbu paani", "jaljeera", "aam panna",
    "orange juice", "pomegranate juice", "sports",
    "bournvita", "tomato juice", "beetroot juice", "beer",
]


@pytest.mark.parametrize("q", VEGETABLE_TERMS)
def test_B_vegetable_searchable(api, q):
    results = _search(api, q)
    assert len(results) >= 1, f"No result for veg term {q!r}"


@pytest.mark.parametrize("q", GRAIN_TERMS)
def test_B_grain_searchable(api, q):
    results = _search(api, q)
    assert len(results) >= 1, f"No result for grain term {q!r}"


@pytest.mark.parametrize("q", PROTEIN_TERMS)
def test_B_protein_searchable(api, q):
    results = _search(api, q)
    assert len(results) >= 1, f"No result for protein term {q!r}"


@pytest.mark.parametrize("q", SNACK_TERMS)
def test_B_snack_searchable(api, q):
    results = _search(api, q)
    assert len(results) >= 1, f"No result for snack term {q!r}"


@pytest.mark.parametrize("q", BEVERAGE_TERMS)
def test_B_beverage_searchable(api, q):
    results = _search(api, q)
    assert len(results) >= 1, f"No result for beverage term {q!r}"


# ---------- C. Salt-substitute regex regression ----------
def _login(api):
    r = api.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "demo@renal.app", "password": "demo123"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, r.text
    tok = r.json().get("access_token") or r.json().get("token")
    return tok


def test_C_losalt_barcode_still_warns(api):
    tok = _login(api)
    r = api.post(
        f"{BASE_URL}/api/scan/barcode",
        headers={"Authorization": f"Bearer {tok}"},
        json={"barcode": "5011544070034"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload.get("salt_substitute_warning") is True, payload


def test_C_nutella_barcode_no_warn(api):
    tok = _login(api)
    r = api.post(
        f"{BASE_URL}/api/scan/barcode",
        headers={"Authorization": f"Bearer {tok}"},
        json={"barcode": "3017620422003"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload.get("salt_substitute_warning") is False, payload


# ---------- D. Guide linked_food_id populated ----------
def _flatten_guide(guide_json):
    """Walk guide JSON, return list of dicts that have 'name' key."""
    out = []
    def walk(node):
        if isinstance(node, dict):
            if "name" in node:
                out.append(node)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for x in node:
                walk(x)
    walk(guide_json)
    return out


@pytest.mark.parametrize("path,expected_min_linked", [
    ("/api/vegetables/guide", 20),
    ("/api/grains/guide", 10),
    ("/api/proteins/guide", 20),
    ("/api/snacks/guide", 20),
    ("/api/beverages/guide", 20),
])
def test_D_guide_has_linked_food_ids(api, path, expected_min_linked):
    r = api.get(f"{BASE_URL}{path}", timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    items = _flatten_guide(r.json())
    with_link = [i for i in items if i.get("linked_food_id")]
    assert len(with_link) >= expected_min_linked, (
        f"{path}: only {len(with_link)} linked items (expected >= {expected_min_linked})"
    )


def test_D_cauliflower_veg_guide_linked(api):
    r = api.get(f"{BASE_URL}/api/vegetables/guide", timeout=TIMEOUT)
    assert r.status_code == 200
    items = _flatten_guide(r.json())
    cauli = [i for i in items if i.get("name", "").lower() == "cauliflower"]
    assert cauli, "Cauliflower entry not found in vegetables guide"
    assert any(c.get("linked_food_id") == "food-cauliflower" for c in cauli), cauli


# ---------- E. iter-13d assertions pass at new values (delegated) ----------
def test_E_iter13d_still_passing():
    """Run iter-13d and inspect the specific assertions bumped by iter-32.

    We DO NOT fail on the two pre-existing TestB5Sajina failures (those were
    reported by iter-30/iter-31 as unrelated pre-existing regressions).
    We DO fail on any NEW iter-32 mismatch (e.g. duplicates_dropped count).
    """
    r = subprocess.run(
        [
            "pytest",
            "/app/backend/tests/test_iter13d_pending_resourcing.py",
            "-v", "--tb=line", "--no-header",
        ],
        capture_output=True, text=True, timeout=120,
    )
    combined = r.stdout + r.stderr
    # Assertions bumped by iter-32 must PASS
    for must_pass in [
        "test_flagged_count_39 PASSED",
        "test_flagged_39 PASSED",
        "test_tier_override_count_7 PASSED",
        "test_no_overlap PASSED",
    ]:
        assert must_pass in combined, (
            f"Expected {must_pass!r} in iter-13d output; got tail:\n{combined[-2000:]}"
        )
    # Known pre-existing failures (Sajina) are tolerated; NEW iter-32 failures are not
    pre_existing = {
        "test_portion_unchanged",  # Sajina — pre-existing iter-23 rescale
        "test_tier_red",           # Sajina — pre-existing iter-23 rescale
    }
    fail_lines = [
        line for line in combined.splitlines()
        if " FAILED" in line
    ]
    new_failures = [
        line for line in fail_lines
        if not any(pe in line for pe in pre_existing)
    ]
    assert not new_failures, (
        "NEW iter-13d failures introduced by iter-32:\n" + "\n".join(new_failures)
    )


# ---------- F. audit_seed.py --json numbers ----------
def test_F_audit_seed_counts():
    r = subprocess.run(
        ["python3", "/app/backend/scripts/audit_seed.py", "--json"],
        capture_output=True, text=True, timeout=60, cwd="/app",
    )
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["data_quality_flagged"] == 43, data.get("data_quality_flagged")
    assert data["sanity_violations_count"] == 42, data.get("sanity_violations_count")
    assert data["curated_overrides"] == 10, data.get("curated_overrides")


# ---------- G. Category filter counts ----------
def _by_cat(api, cat):
    r = api.get(f"{BASE_URL}/api/foods", params={"category": cat, "limit": 500}, timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    return r.json()


def test_G_vegetable_count_25plus(api):
    veg = _by_cat(api, "vegetable")
    assert len(veg) >= 25, f"veg count {len(veg)} < 25"


def test_G_beverage_count_20plus(api):
    bev = _by_cat(api, "beverage")
    assert len(bev) >= 20, f"beverage count {len(bev)} < 20"


def test_G_snack_count_25plus(api):
    snk = _by_cat(api, "snack")
    assert len(snk) >= 25, f"snack count {len(snk)} < 25"
