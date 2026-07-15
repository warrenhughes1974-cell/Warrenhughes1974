"""
Issue #73 — quikmstr MISSCNTRY must be 0000 for all policies.

Usage:
  python tools/validators/validate_issue73_misscntry.py
  python tools/validators/validate_issue73_misscntry.py --output-dir QLA_Migration/Output
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
EVIDENCE = PROJECT_ROOT / "Issue_Log_Items" / "Issue_73" / "evidence"

SCRIPT_VERSION = "1.0"
EXPECTED_ROW_COUNT = 5083

TRACE_POLICIES = {
    "010143726C": "CA",
    "010148272C": "MO",
    "010148856C": "MO",
    "010149295C": "NE",
    "010157076C": "NE",
}


def _n(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def _load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Issue #73 MISSCNTRY=0000")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Directory containing quikmstr.csv",
    )
    args = parser.parse_args()

    mstr_path = args.output_dir / "quikmstr.csv"
    if not mstr_path.exists():
        print(f"FAIL: missing {mstr_path}")
        return 1

    rows = _load_csv(mstr_path)
    errors: list[str] = []

    if len(rows) != EXPECTED_ROW_COUNT:
        errors.append(f"row count {len(rows)} != expected {EXPECTED_ROW_COUNT}")

    bad = [(r.get("MPOLICY"), _n(r.get("MISSCNTRY"))) for r in rows if _n(r.get("MISSCNTRY")) != "0000"]
    if bad:
        errors.append(f"MISSCNTRY != 0000: {len(bad)} rows (first 5: {bad[:5]})")

    by_policy = {_n(r.get("MPOLICY")): r for r in rows}
    for pol, expected_state in TRACE_POLICIES.items():
        row = by_policy.get(pol)
        if not row:
            errors.append(f"trace policy missing: {pol}")
            continue
        if _n(row.get("MISSCNTRY")) != "0000":
            errors.append(f"{pol}: MISSCNTRY={row.get('MISSCNTRY')!r}, expected 0000")
        if _n(row.get("MISSUEST")) != expected_state:
            errors.append(
                f"{pol}: MISSUEST={row.get('MISSUEST')!r}, expected {expected_state!r} (unchanged)"
            )

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    summary_path = EVIDENCE / "issue73_validation_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        w.writerow(["script_version", SCRIPT_VERSION])
        w.writerow(["quikmstr_rows", len(rows)])
        w.writerow(["misscntry_not_0000", len(bad)])
        w.writerow(["result", "PASS" if not errors else "FAIL"])

    print(f"Issue #73 MISSCNTRY validator v{SCRIPT_VERSION}")
    print(f"  quikmstr rows: {len(rows)}")
    print(f"  MISSCNTRY != 0000: {len(bad)}")
    print(f"  trace policies: {len(TRACE_POLICIES)}")

    if errors:
        print("FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
