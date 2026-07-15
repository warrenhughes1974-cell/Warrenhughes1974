"""
Issue #74 — quikplan VARDB: only former default `4` → `0`; keep structure codes 1/2/3.

Usage:
  python tools/validators/validate_issue74_vardb.py
  python tools/validators/validate_issue74_vardb.py --output-dir QLA_Migration/Output
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
EVIDENCE = PROJECT_ROOT / "Issue_Log_Items" / "Issue_74" / "evidence"
BASELINE_STRUCTURE = EVIDENCE / "issue74_risk_structure_plans_unchanged.csv"

SCRIPT_VERSION = "1.0"
EXPECTED_ROW_COUNT = 141
EXPECTED_ZERO_COUNT = 121
EXPECTED_STRUCTURE_COUNT = 20

TRACE_PLANS = {
    "920ADB": "0",
    "965ADB": "0",
    "130JEB": "3",
    "17CSI3": "2",
    "1659SR": "1",
    "A60MIR": "2",
}


def _n(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def _load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def _load_structure_baseline() -> dict[str, str]:
    if not BASELINE_STRUCTURE.is_file():
        return {}
    out: dict[str, str] = {}
    for row in _load_csv(BASELINE_STRUCTURE):
        plan = _n(row.get("PLAN"))
        vardb = _n(row.get("VARDB_before") or row.get("VARDB_after"))
        if plan and vardb:
            out[plan] = vardb
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Issue #74 quikplan VARDB 4→0 only")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Directory containing quikplan.csv",
    )
    args = parser.parse_args()

    plan_path = args.output_dir / "quikplan.csv"
    if not plan_path.exists():
        print(f"FAIL: missing {plan_path}")
        return 1

    rows = _load_csv(plan_path)
    errors: list[str] = []

    if len(rows) != EXPECTED_ROW_COUNT:
        errors.append(f"row count {len(rows)} != expected {EXPECTED_ROW_COUNT}")

    by_plan = {_n(r.get("PLAN")): r for r in rows}
    counts = Counter(_n(r.get("VARDB")) for r in rows)

    if counts.get("4", 0):
        errors.append(f"VARDB=4 residual: {counts.get('4', 0)} rows")

    zero_count = counts.get("0", 0)
    if zero_count != EXPECTED_ZERO_COUNT:
        errors.append(f"VARDB=0 count {zero_count} != expected {EXPECTED_ZERO_COUNT}")

    structure_count = sum(counts.get(v, 0) for v in ("1", "2", "3"))
    if structure_count != EXPECTED_STRUCTURE_COUNT:
        errors.append(
            f"structure VARDB 1/2/3 count {structure_count} != expected {EXPECTED_STRUCTURE_COUNT}"
        )

    baseline = _load_structure_baseline()
    if not baseline:
        errors.append(f"missing structure baseline: {BASELINE_STRUCTURE}")
    else:
        for plan, expected_vardb in sorted(baseline.items()):
            row = by_plan.get(plan)
            if not row:
                errors.append(f"structure plan missing from quikplan: {plan}")
                continue
            actual = _n(row.get("VARDB"))
            if actual != expected_vardb:
                errors.append(
                    f"{plan}: VARDB={actual!r}, expected unchanged {expected_vardb!r}"
                )

    for plan, expected_vardb in TRACE_PLANS.items():
        row = by_plan.get(plan)
        if not row:
            errors.append(f"trace plan missing: {plan}")
            continue
        actual = _n(row.get("VARDB"))
        if actual != expected_vardb:
            errors.append(f"{plan}: VARDB={actual!r}, expected {expected_vardb!r}")
        if _n(row.get("VARGP")) != "4":
            errors.append(f"{plan}: VARGP={row.get('VARGP')!r}, expected '4' unchanged")

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    summary_path = EVIDENCE / "issue74_validation_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        w.writerow(["script_version", SCRIPT_VERSION])
        w.writerow(["quikplan_rows", len(rows)])
        for k, v in sorted(counts.items()):
            w.writerow([f"VARDB_{k or 'BLANK'}", v])
        w.writerow(["vardb_4_residual", counts.get("4", 0)])
        w.writerow(["result", "PASS" if not errors else "FAIL"])

    print(f"Issue #74 VARDB validator v{SCRIPT_VERSION}")
    print(f"  quikplan rows: {len(rows)}")
    print(f"  VARDB distribution: {dict(counts)}")
    print(f"  structure baseline plans: {len(baseline)}")
    print(f"  trace plans: {len(TRACE_PLANS)}")

    if errors:
        print("FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
