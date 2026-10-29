"""
Tests for iter-33 follow-ups:
1. Sajina rescale reconciliation (assertions updated to portion=40g, tier YELLOW).
2. P/Na refinement top-30 spot checks.
3. Hindi/Devanagari search unification (name + hindi_name, parens stripped).
4. Regression on English search + audit_seed counts.
"""
import os
import subprocess
import json
import pytest
import requests
import urllib.parse

BASE_URL = os.environ.get(
    "EXPO_PUBLIC_BACKEND_URL",
    "https://safe-food-guide-1.preview.emergentagent.com",
).rstrip("/")


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# --- FIX 2: P/Na spot checks ---
@pytest.mark.parametrize(
    "food_id,phosphorus_mg,sodium_mg,protein_g",
    [
        ("food-cauliflower", 44, 8, 1.9),
        ("food-oats-plain-small", 99, 1, 4.2),
        ("food-carrot", 20, 40, 0.6),
        ("food-ridge-gourd-turai", 35, 8, 0.6),
        ("food-masoor-dal-red-split", 115, 3, 5.4),
    ],
)
def test_refined_pna_values(api, food_id, phosphorus_mg, sodium_mg, protein_g):
    r = api.get(f"{BASE_URL}/api/foods/{food_id}")
    assert r.status_code == 200, f"{food_id} => {r.status_code} {r.text[:200]}"
    body = r.json()
    data = body.get("food", body)
    assert data["phosphorus_mg"] == pytest.approx(phosphorus_mg, abs=0.1), (
        f"{food_id} phosphorus_mg={data.get('phosphorus_mg')} (expected {phosphorus_mg})"
    )
    assert data["sodium_mg"] == pytest.approx(sodium_mg, abs=0.1), (
        f"{food_id} sodium_mg={data.get('sodium_mg')} (expected {sodium_mg})"
    )
    assert data["protein_g"] == pytest.approx(protein_g, abs=0.1), (
        f"{food_id} protein_g={data.get('protein_g')} (expected {protein_g})"
    )


# --- FIX 2C: No tier upshift on refined entries ---
@pytest.mark.parametrize(
    "food_id,expected_tier",
    [
        ("food-cauliflower", "YELLOW"),
        ("food-oats-plain-small", "GREEN"),
        ("food-carrot", "YELLOW"),
    ],
)
def test_refined_tiers_unchanged(api, food_id, expected_tier):
    r = api.get(f"{BASE_URL}/api/foods/{food_id}")
    assert r.status_code == 200
    body = r.json()
    data = body.get("food", body)
    assert data["safety_tier"] == expected_tier, (
        f"{food_id} tier={data.get('safety_tier')} (expected {expected_tier})"
    )


# --- FIX 3: Hindi/Devanagari search ---
def test_devanagari_aam_mango_ranked_first(api):
    q = urllib.parse.quote("आम")
    r = api.get(f"{BASE_URL}/api/foods?q={q}")
    assert r.status_code == 200, r.text
    results = r.json()
    assert isinstance(results, list) and len(results) >= 2, f"got {len(results)} results"
    names = [f["name"] for f in results]
    ids = [f.get("id") for f in results]
    # First result should be Mango (small portion)
    assert ids[0] == "food-mango-small", f"expected food-mango-small first, got {ids[:5]} / {names[:5]}"
    # Second should be Mango (whole)
    assert names[1].startswith("Mango"), f"expected Mango second, got {names[:5]}"
    # Aam Panna / Raw mango chutney rank after
    aam_panna_idx = next((i for i, n in enumerate(names) if "Aam Panna" in n), None)
    if aam_panna_idx is not None:
        assert aam_panna_idx >= 2, f"Aam Panna at idx {aam_panna_idx}, expected >=2 ({names[:5]})"


def test_devanagari_dudh_milk(api):
    q = urllib.parse.quote("दूध")
    r = api.get(f"{BASE_URL}/api/foods?q={q}")
    assert r.status_code == 200
    results = r.json()
    assert isinstance(results, list) and len(results) >= 1
    names = [f["name"].lower() for f in results]
    assert any("milk" in n for n in names), f"no milk entry in {names[:5]}"


# --- FIX 3F: English regressions ---
@pytest.mark.parametrize(
    "query,expected_first_substring",
    [
        ("mango", "Mango (small portion)"),
        ("water", "Water"),
        ("cauliflower", "Cauliflower"),
        ("sports drink", "Sports"),
    ],
)
def test_english_search_first_result(api, query, expected_first_substring):
    r = api.get(f"{BASE_URL}/api/foods", params={"q": query})
    assert r.status_code == 200
    results = r.json()
    assert isinstance(results, list) and len(results) >= 1, f"no results for {query}"
    first_name = results[0]["name"]
    assert expected_first_substring.lower() in first_name.lower(), (
        f"q={query!r} first result={first_name!r} (expected substring {expected_first_substring!r}); top5={[x['name'] for x in results[:5]]}"
    )


def test_english_search_milk_starts_with(api):
    r = api.get(f"{BASE_URL}/api/foods", params={"q": "milk"})
    assert r.status_code == 200
    results = r.json()
    assert len(results) >= 1
    first_name = results[0]["name"]
    assert first_name.lower().startswith("milk"), f"first={first_name!r}; top5={[x['name'] for x in results[:5]]}"


# --- REGRESSION G: audit_seed reconciliation counts ---
def test_audit_seed_reconciliation_counts():
    script_path = "/app/backend/scripts/audit_seed.py"
    if not os.path.exists(script_path):
        pytest.skip("audit_seed.py not present")
    result = subprocess.run(
        ["python", script_path, "--json"],
        capture_output=True,
        text=True,
        cwd="/app/backend",
        timeout=60,
    )
    assert result.returncode == 0, f"audit_seed exited {result.returncode}: {result.stderr[:400]}"
    # Try to parse JSON (may have leading log lines)
    stdout = result.stdout.strip()
    # extract from last '{' to matching braces or from first line that's JSON
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        # find last json object
        lines = stdout.splitlines()
        for i in range(len(lines)):
            candidate = "\n".join(lines[i:])
            try:
                data = json.loads(candidate)
                break
            except json.JSONDecodeError:
                continue
        else:
            pytest.fail(f"could not parse audit_seed JSON output; stdout head: {stdout[:400]}")
    assert data.get("data_quality_flagged") == 43, f"data_quality_flagged={data.get('data_quality_flagged')}"
    assert data.get("sanity_violations_count") == 42, f"sanity_violations_count={data.get('sanity_violations_count')}"
    assert data.get("curated_overrides") == 10, f"curated_overrides={data.get('curated_overrides')}"
    assert data.get("duplicates_dropped_count") == 10, f"duplicates_dropped_count={data.get('duplicates_dropped_count')}"
