"""Standalone audit script for the seeded food catalog.

Runs the same reconciliation pipeline that server.py applies at startup, but
against the raw seed files only (does not touch MongoDB). Reports:
  * how many entries would be reclassified (old → new tier)
  * how many entries land in each bucket after Step 2 rescale
  * duplicates dropped in Step 6
  * remaining sanity ceiling violations (Step 7)
  * any portion_limit_text ↔ serving_disclaimer contradictions
  * count of tier_override rows that are legitimately exempt

Usage:
    python /app/backend/scripts/audit_seed.py           # human-readable
    python /app/backend/scripts/audit_seed.py --json    # machine-readable
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

# Make the parent directory (which contains reconciliation.py and the seed
# modules) importable when this file is executed directly.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

from reconciliation import reconcile_seed  # noqa: E402
from seed_data import SEED_FOODS  # noqa: E402
from seed_data_indb import SEED_FOODS_INDB  # noqa: E402


def build_report() -> dict:
    _, stats = reconcile_seed(SEED_FOODS, SEED_FOODS_INDB, logger=None)
    bucket_counts = Counter(bucket for _id, bucket in stats["rescaled"])
    return {
        "total_input": stats["total_input"],
        "curated_overrides": stats["curated_overrides"],
        "reclassified_count": len(stats["reclassified"]),
        "reclassified": stats["reclassified"][:50],  # sample
        "reclassified_by_direction": _direction_counts(stats["reclassified"]),
        "rescaled_by_bucket": dict(bucket_counts),
        "rescaled_total": len(stats["rescaled"]),
        "duplicates_dropped_count": len(stats["duplicates_dropped"]),
        "duplicates_dropped": stats["duplicates_dropped"],
        "sanity_violations_count": len(stats["sanity_violations"]),
        "sanity_violations": stats["sanity_violations"][:50],
        "portion_disclaimer_conflicts_count": len(stats["portion_disclaimer_conflicts"]),
        "portion_disclaimer_conflicts": stats["portion_disclaimer_conflicts"],
    }


def _direction_counts(reclassified: list[tuple]) -> dict[str, int]:
    order = {"GREEN": 0, "YELLOW": 1, "RED": 2}
    counts = {"upgraded_to_stricter": 0, "downgraded_to_safer": 0, "same_severity": 0}
    for _id, old, new in reclassified:
        try:
            o, n = order[old], order[new]
        except KeyError:
            counts["same_severity"] += 1
            continue
        if n > o:
            counts["upgraded_to_stricter"] += 1
        elif n < o:
            counts["downgraded_to_safer"] += 1
        else:
            counts["same_severity"] += 1
    return counts


def _human_report(report: dict) -> str:
    lines: list[str] = []
    lines.append("=" * 70)
    lines.append(" FOOD CATALOG RECONCILIATION AUDIT")
    lines.append("=" * 70)
    lines.append(f"Total entries inspected:              {report['total_input']}")
    lines.append(f"Curated tier overrides (kept as-is):  {report['curated_overrides']}")
    lines.append(f"Duplicates dropped:                    {report['duplicates_dropped_count']}")
    lines.append(f"Auto-rescaled (Step 2):                {report['rescaled_total']}")
    for bucket, n in sorted(report["rescaled_by_bucket"].items()):
        lines.append(f"    {bucket:<10s} {n}")
    lines.append(f"Reclassified (tier changed in Step 3): {report['reclassified_count']}")
    for direction, n in report["reclassified_by_direction"].items():
        lines.append(f"    {direction:<24s} {n}")
    lines.append(f"Sanity ceiling violations remaining:   {report['sanity_violations_count']}")
    if report["sanity_violations"]:
        lines.append("    Examples:")
        for _id, name, vios in report["sanity_violations"][:10]:
            lines.append(f"      {_id:<40s} {name[:35]:<35s}  {'; '.join(vios)}")
    lines.append(f"portion_limit_text ↔ disclaimer conflicts: {report['portion_disclaimer_conflicts_count']}")
    if report["duplicates_dropped"]:
        lines.append("\nDuplicates dropped (first-wins policy):")
        for dup_id, dup_name, kept_id in report["duplicates_dropped"]:
            lines.append(f"    {dup_id:<45s} '{dup_name}'  (kept {kept_id})")
    lines.append("=" * 70)
    if (
        report["sanity_violations_count"] == 0
        and report["portion_disclaimer_conflicts_count"] == 0
    ):
        lines.append(" AUDIT PASS: zero unexplained mismatches.")
    else:
        lines.append(" AUDIT FLAGS PRESENT — see counts above.")
    lines.append("=" * 70)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the seeded food catalog.")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--fail-on-flags",
        action="store_true",
        help="exit 1 if sanity violations or portion/disclaimer conflicts remain",
    )
    args = parser.parse_args()

    report = build_report()

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(_human_report(report))

    if args.fail_on_flags and (
        report["sanity_violations_count"] > 0
        or report["portion_disclaimer_conflicts_count"] > 0
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
