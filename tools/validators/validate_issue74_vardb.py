"""
Issue #74 — quikplan VARDB: no `4` residual; structure codes follow the rate grid.

Issue A7 (Warren approved 2026-08-09) moved VARDB authority from the rulebook
literal to the emitted QuikDbs grid, so the fixed 121/20 split and the frozen
structure baseline are only used when Output/rates is unavailable.

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
sys.path.insert(0, str(PROJECT_ROOT))

from qla_core.attained_age_grid_fill import load_manifest  # noqa: E402
from qla_core.quikplan_rate_variation_flags import (  # noqa: E402
    CODE_ATTAINED_AGE,
    CODE_LEVEL,
    CODE_NOT_ON_FILE,
    classify_factor_grid,
    scan_factor_grid,
)

DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
EVIDENCE = PROJECT_ROOT / "Issue_Log_Items" / "Issue_74" / "evidence"
BASELINE_STRUCTURE = EVIDENCE / "issue74_risk_structure_plans_unchanged.csv"

SCRIPT_VERSION = "1.1"
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


def _expected_vardb_from_rates(output_dir: Path) -> dict[str, str]:
    """Issue A7: VARDB each plan should carry given its emitted QuikDbs grid."""
    rates_dir = output_dir / "rates"
    if not rates_dir.is_dir():
        return {}
    shapes = scan_factor_grid(str(rates_dir), "QuikDbs", "DB")
    if not shapes:
        return {}
    # Issue #140: an attained-age grid on the slot axis reads as policy-year by shape,
    # so its membership comes from the emit manifest.
    slot_plans = load_manifest(str(PROJECT_ROOT)).get("QuikDbs", set())
    expected: dict[str, str] = {}
    for plan, shape in shapes.items():
        if plan in slot_plans and shape is not None and shape.real_rows:
            expected[plan] = CODE_ATTAINED_AGE
            continue
        code = classify_factor_grid(shape)
        # No DB grid means level death benefit off INITVAL, which is Issue #74's 0.
        expected[plan] = CODE_LEVEL if code == CODE_NOT_ON_FILE else code
    return expected


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

    grid_expected = _expected_vardb_from_rates(args.output_dir)
    baseline = _load_structure_baseline()

    if grid_expected:
        authority = "QuikDbs grid (Issue A7)"
        for plan in sorted(by_plan):
            actual = _n(by_plan[plan].get("VARDB"))
            expected_vardb = grid_expected.get(plan, CODE_LEVEL)
            if actual != expected_vardb:
                errors.append(
                    f"{plan}: VARDB={actual!r}, expected {expected_vardb!r} from QuikDbs grid"
                )
    else:
        authority = "frozen Issue #74 baseline (no Output/rates)"
        zero_count = counts.get("0", 0)
        if zero_count != EXPECTED_ZERO_COUNT:
            errors.append(f"VARDB=0 count {zero_count} != expected {EXPECTED_ZERO_COUNT}")

        structure_count = sum(counts.get(v, 0) for v in ("1", "2", "3"))
        if structure_count != EXPECTED_STRUCTURE_COUNT:
            errors.append(
                f"structure VARDB 1/2/3 count {structure_count} != expected {EXPECTED_STRUCTURE_COUNT}"
            )

        if not baseline:
            errors.append(f"missing structure baseline: {BASELINE_STRUCTURE}")
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
    print(f"  VARDB authority: {authority}")
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
