"""Shared enrichment helpers for the 6 curated food guides.

The guide dicts (fruit, vegetable, snack, beverage, protein, grain) store their
*source-of-truth* nutrient data in mg — the same convention as the main seed DB.
Two derived quantities are computed here at load time so the raw dicts never
need to be hand-maintained in two units:

  - potassium_meq : mg → mEq using K = 39.1 g/mol, valence 1.
  - high_sodium   : boolean flag when sodium_mg >= 400 (the same RED threshold
                    used by the main seed DB's sodium-tiering rule).

An additional book-keeping CSV is written at import time listing every entry
that is *missing* a sourced sodium value plus a manually-curated list of dishes
we have flagged for a future sourcing pass (Vada Pav, Momos, etc.). This mirrors
the `needs_manual_review.csv` pipeline used for the seed DB reconciliation pass.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

# ---------- Unit conversion (Potassium K+, valence 1, atomic mass 39.1 g/mol) ----------
K_MG_PER_MEQ = 39.1


def mg_to_meq_potassium(mg: float) -> float:
    """Convert potassium in mg to milliequivalents, rounded to 1 decimal."""
    if not isinstance(mg, (int, float)):
        return 0.0
    return round(mg / K_MG_PER_MEQ, 1)


# ---------- Sodium safety threshold (matches main seed DB's RED threshold) ----------
HIGH_SODIUM_THRESHOLD_MG = 400


def _is_high_sodium(sodium_mg: Optional[float]) -> bool:
    return (
        isinstance(sodium_mg, (int, float))
        and sodium_mg is not None
        and sodium_mg >= HIGH_SODIUM_THRESHOLD_MG
    )


# ---------- Enrichment ----------
def enrich_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of `entry` with derived fields injected.

    Always adds:
      - potassium_meq : rounded mEq of the entry's potassium_mg
      - sodium_mg     : None if unset (never guessed by this function)
      - high_sodium   : boolean flag; only True when sodium_mg >= 400
    """
    out = dict(entry)  # shallow copy — entries are flat dicts
    out.setdefault("sodium_mg", None)
    out["potassium_meq"] = mg_to_meq_potassium(float(out.get("potassium_mg", 0) or 0))
    out["high_sodium"] = _is_high_sodium(out.get("sodium_mg"))
    return out


def enrich_guide(guide: Dict[str, Any], entries_key: str) -> Dict[str, Any]:
    """Return an enriched copy of a full three-tier guide.

    `entries_key` is the field inside each tier holding the array
    (e.g. "fruits", "vegetables", "proteins", "snacks", "beverages", "grains").
    Non-entry keys such as `title` and `subtitle` are copied through unchanged.
    """
    result: Dict[str, Any] = {}
    for tier_key, tier_data in guide.items():
        if not isinstance(tier_data, dict) or entries_key not in tier_data:
            result[tier_key] = tier_data
            continue
        tier_copy = dict(tier_data)
        tier_copy[entries_key] = [enrich_entry(e) for e in tier_data[entries_key]]
        result[tier_key] = tier_copy
    return result


# ---------- Missing-sodium CSV writer ----------
# Dishes intentionally NOT added to any guide yet — flagged for a future
# sourcing pass. See the iteration prompt.
_FLAGGED_UNSOURCED: List[Dict[str, str]] = [
    {"name": "Vada Pav",         "reason": "meaningful sodium noted in sources but no consistent per-serving figure"},
    {"name": "Misal Pav",        "reason": "sodium heavy but no consistent per-serving figure"},
    {"name": "Sattu Sharbat",    "reason": "sodium content depends heavily on black salt used"},
    {"name": "Sol Kadhi",        "reason": "recipe-variable — needs an IFCT/USDA figure"},
    {"name": "Momos",            "reason": "filling + dipping sauce push sodium high but no citable per-serving number"},
    {"name": "Bhel Puri",        "reason": "chutneys make sodium recipe-dependent"},
    {"name": "Sev Puri",         "reason": "chutneys make sodium recipe-dependent"},
    {"name": "Tata Salt Lite (%KCl split)", "reason": "seed uses ~35% KCl / 65% NaCl (product marketing claim) but no manufacturer spec sheet cited — verify % against Tata Consumer Products FSSAI declaration and update potassium_mg/sodium_mg accordingly. See seed_data.py food-tata-saltlite."},
]


def collect_needs_sourcing(all_guides: Iterable[tuple[str, Dict[str, Any], str]]) -> List[Dict[str, str]]:
    """Walk every guide and return a list of rows for entries lacking sodium_mg.

    `all_guides` is an iterable of (guide_name, guide_dict, entries_key) triples.
    """
    rows: List[Dict[str, str]] = []
    for guide_name, guide, entries_key in all_guides:
        for tier_key, tier_data in guide.items():
            if not isinstance(tier_data, dict) or entries_key not in tier_data:
                continue
            for entry in tier_data[entries_key]:
                if entry.get("sodium_mg") is None:
                    rows.append({
                        "guide": guide_name,
                        "tier": tier_key,
                        "name": str(entry.get("name", "")),
                        "hindi": str(entry.get("hindi", "")),
                        "reason": "sodium_mg not yet sourced — do not guess; flag for real data",
                    })
    return rows


def write_needs_sourcing_csv(
    path: Path,
    missing_rows: List[Dict[str, str]],
) -> Path:
    """Write the guide_needs_sourcing.csv used by the QA / sourcing pipeline.

    Combines the flagged-not-yet-added dishes with the sodium-gap rows from
    the existing guides. Same convention as needs_manual_review.csv for the
    main seed DB.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["guide", "tier", "name", "hindi", "reason"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        # First: the manually-flagged dishes we chose NOT to add yet.
        for row in _FLAGGED_UNSOURCED:
            writer.writerow({
                "guide": "flagged-not-added",
                "tier": "n/a",
                "name": row["name"],
                "hindi": "",
                "reason": row["reason"],
            })
        # Then: every existing guide entry that still needs a sodium number.
        for row in missing_rows:
            writer.writerow(row)
    logger.info(
        "Wrote guide_needs_sourcing.csv with %d flagged + %d missing-sodium rows to %s",
        len(_FLAGGED_UNSOURCED),
        len(missing_rows),
        path,
    )
    return path
