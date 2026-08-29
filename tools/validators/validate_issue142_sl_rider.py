#!/usr/bin/env python3
"""Issue #142 — Active SL riders emit as 9SUBLF with VPU=0.

Usage:
  python tools/validators/validate_issue142_sl_rider.py
  python tools/validators/validate_issue142_sl_rider.py --output-dir QLA_Migration/Output
  python tools/validators/validate_issue142_sl_rider.py --publish-test-validation
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
SCRIPT_VERSION = "1.0"

ISSUE142_PLAN = "9SUBLF"
MIN_RIDR_ROWS = 22

ACTIVE_POLICIES = [
    "9010398471C",
    "9010440631C",
    "9010448806C",
    "9010451453C",
    "9010459814C",
    "9010466978C",
    "9010469666C",
    "9010495122C",
    "9010497264C",
    "9010511795C",
    "9010556634C",
    "9010782078C",
    "9010784732C",
    "9010796912C",
    "9010803776C",
    "9010819774C",
    "9010886099C",
    "9010987095C",
    "9011185537C",
    "9011193243C",
    "9011201237C",
    "9011203457C",
]

# Red-font policies: source ANN_PREM_PER_UNIT / NUMBER_OF_UNITS
RED_GOLD = {
    "9010469666C": (10.0, 2.5),
    "9010497264C": (5.0, 5.03),
    "9010886099C": (100.0, 26.34),
    "9010987095C": (25.0, 0.1952),
    "9011185537C": (25.0, 4.96),
    "9011193243C": (5.0, 22.22),
    "9011201237C": (25.0, 11.935),
    "9011203457C": (15.0, 3.28),
}

OUTLIER_ZERO_PREM = "9010782078C"


def _f(v: object) -> float:
    try:
        return float(str(v or "").replace(",", "").strip() or 0)
    except (ValueError, TypeError):
        return 0.0


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Issue #142 SL rider 9SUBLF")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument(
        "--publish-test-validation",
        action="store_true",
        help="On PASS, copy quikplan.csv and quikridr.csv to Output/Test_Validation/",
    )
    args = ap.parse_args()

    plan_path = args.output_dir / "quikplan.csv"
    ridr_path = args.output_dir / "quikridr.csv"
    print(f"validate_issue142_sl_rider.py {SCRIPT_VERSION}")
    print(f"output: {args.output_dir}")
    if not plan_path.is_file():
        print("FAIL: missing quikplan.csv")
        return 2
    if not ridr_path.is_file():
        print("FAIL: missing quikridr.csv")
        return 2

    with plan_path.open(encoding="latin1", newline="") as f:
        plans = list(csv.DictReader(f))
    with ridr_path.open(encoding="latin1", newline="") as f:
        riders = list(csv.DictReader(f))

    errors: list[str] = []
    sublf_plans = [r for r in plans if (r.get("PLAN") or "").strip().upper() == ISSUE142_PLAN]
    if len(sublf_plans) != 1:
        errors.append(f"quikplan 9SUBLF rows={len(sublf_plans)} (expected 1)")
    else:
        par = (sublf_plans[0].get("PAR") or "").strip()
        if par != "0":
            errors.append(f"quikplan 9SUBLF PAR={par or '(blank)'} (expected 0)")

    sublf = [
        r
        for r in riders
        if (r.get("MPLAN") or "").strip().upper() == ISSUE142_PLAN
    ]
    print(f"quikridr 9SUBLF rows: {len(sublf)}")
    if len(sublf) < MIN_RIDR_ROWS:
        errors.append(f"quikridr 9SUBLF count={len(sublf)} (floor {MIN_RIDR_ROWS})")

    nonzero_vpu = [r for r in sublf if _f(r.get("MVPU")) != 0.0]
    if nonzero_vpu:
        sample = (nonzero_vpu[0].get("MPOLICY") or "").strip()
        errors.append(f"{len(nonzero_vpu)} 9SUBLF rows have MVPU!=0 (e.g. {sample})")

    by_pol = {(r.get("MPOLICY") or "").strip(): r for r in sublf}
    missing = [p for p in ACTIVE_POLICIES if p not in by_pol]
    if missing:
        errors.append(f"missing 9SUBLF phase on {len(missing)} policies: {', '.join(missing[:5])}")

    for pol, (units, prem) in RED_GOLD.items():
        row = by_pol.get(pol)
        if not row:
            continue
        got_u = _f(row.get("MUNIT"))
        got_p = _f(row.get("MPREM"))
        if abs(got_u - units) > 0.0001:
            errors.append(f"{pol} MUNIT={got_u} expected {units}")
        if abs(got_p - prem) > 0.0001:
            errors.append(f"{pol} MPREM={got_p} expected {prem}")

    outlier = by_pol.get(OUTLIER_ZERO_PREM)
    if outlier and _f(outlier.get("MPREM")) != 0.0:
        errors.append(f"{OUTLIER_ZERO_PREM} MPREM={outlier.get('MPREM')} (expected 0)")

    if errors:
        print("FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS")
    print("  quikplan 9SUBLF PAR=0")
    print(f"  quikridr 9SUBLF rows={len(sublf)} all MVPU=0")
    print(f"  22 active anchors present; 8 red golds match; {OUTLIER_ZERO_PREM} MPREM=0")
    if args.publish_test_validation:
        dest = args.output_dir / "Test_Validation"
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(plan_path, dest / "quikplan.csv")
        shutil.copy2(ridr_path, dest / "quikridr.csv")
        print(f"published {dest / 'quikplan.csv'}")
        print(f"published {dest / 'quikridr.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
