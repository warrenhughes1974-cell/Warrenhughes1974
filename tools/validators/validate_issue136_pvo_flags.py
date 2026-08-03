#!/usr/bin/env python3
"""Issue #136 — QuikPlan PVO flags: real-rate-only Band/State/DV/DB.

Usage:
  python tools/validators/validate_issue136_pvo_flags.py
  python tools/validators/validate_issue136_pvo_flags.py --output-dir QLA_Migration/Output
  python tools/validators/validate_issue136_pvo_flags.py --publish-test-validation
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

VARY_SUFFIXES = ("GP", "DB", "CV", "TV", "DV")
BD_FIELDS = [f"BDVARY{s}" for s in VARY_SUFFIXES]
ST_FIELDS = [f"STVARY{s}" for s in VARY_SUFFIXES]
DV_FIELDS = [f"{d}DV" for d in ("GDVARY", "UWVARY", "BDVARY", "STVARY")]
DB_FIELDS = [f"{d}DB" for d in ("GDVARY", "UWVARY", "BDVARY", "STVARY")]

GOLD_1658C1 = {
    "BDVARYGP": "N",
    "BDVARYDB": "N",
    "BDVARYCV": "N",
    "BDVARYTV": "N",
    "BDVARYDV": "N",
    "STVARYGP": "N",
    "STVARYDB": "N",
    "STVARYCV": "N",
    "STVARYTV": "N",
    "STVARYDV": "N",
    "GDVARYDV": "N",
    "UWVARYDV": "N",
    "GDVARYDB": "N",
    "UWVARYDB": "N",
    "GDVARYGP": "Y",
    "UWVARYGP": "Y",
}


def _u(v: object) -> str:
    return ("" if v is None else str(v)).strip().upper()


def _count_factor_plans(rates: Path, table: str) -> set[str]:
    path = rates / f"{table}.csv"
    if not path.is_file():
        for p in rates.glob("*.csv"):
            if p.stem.lower() == table.lower():
                path = p
                break
        else:
            return set()
    plans: set[str] = set()
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            plan = (row.get("PLAN") or "").strip().upper()
            if plan:
                plans.add(plan)
    return plans


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Issue #136 PVO flags")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument(
        "--publish-test-validation",
        action="store_true",
        help="On PASS, copy quikplan.csv to Output/Test_Validation/",
    )
    args = ap.parse_args()

    plan_path = args.output_dir / "quikplan.csv"
    rates = args.output_dir / "rates"
    print(f"validate_issue136_pvo_flags.py {SCRIPT_VERSION}")
    print(f"output: {args.output_dir}")
    if not plan_path.is_file():
        print("FAIL: missing quikplan.csv")
        return 2

    with plan_path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    print(f"rows: {len(rows)}")

    errors: list[str] = []
    bd_y = st_y = 0
    gold = None
    for row in rows:
        plan = (row.get("PLAN") or "").strip().upper()
        if any(_u(row.get(f)) == "Y" for f in BD_FIELDS):
            bd_y += 1
        if any(_u(row.get(f)) == "Y" for f in ST_FIELDS):
            st_y += 1
        if plan == "1658C1":
            gold = row

    if gold is None:
        errors.append("1658C1 missing from quikplan")
    else:
        for fld, exp in GOLD_1658C1.items():
            got = _u(gold.get(fld))
            if got != exp:
                errors.append(f"1658C1 {fld}: expected {exp}, got {got or '(blank)'}")

    if bd_y != 0:
        errors.append(f"fleet BDVARY*=Y plans={bd_y} (expected 0)")
    if st_y != 0:
        errors.append(f"fleet STVARY*=Y plans={st_y} (expected 0)")

    dvs = _count_factor_plans(rates, "QuikDvs")
    dbs = _count_factor_plans(rates, "QuikDbs")
    for row in rows:
        plan = (row.get("PLAN") or "").strip().upper()
        if plan not in dvs:
            for f in DV_FIELDS:
                if _u(row.get(f)) == "Y":
                    errors.append(f"{plan}: {f}=Y but no QuikDvs factors")
        if plan not in dbs:
            for f in DB_FIELDS:
                if _u(row.get(f)) == "Y":
                    errors.append(f"{plan}: {f}=Y but no QuikDbs factors")

    # Cap error spam
    if len(errors) > 25:
        shown = errors[:25]
        shown.append(f"... +{len(errors) - 25} more")
        errors = shown

    print(f"fleet BDVARY Y plans: {bd_y}")
    print(f"fleet STVARY Y plans: {st_y}")
    print(f"QuikDvs factor plans: {len(dvs)}")
    print(f"QuikDbs factor plans: {len(dbs)}")
    if gold:
        print(
            "1658C1:",
            f"PLANVALOPT={_u(gold.get('PLANVALOPT'))}",
            f"GDVARYGP={_u(gold.get('GDVARYGP'))}",
            f"UWVARYGP={_u(gold.get('UWVARYGP'))}",
            f"BDVARYGP={_u(gold.get('BDVARYGP'))}",
            f"STVARYGP={_u(gold.get('STVARYGP'))}",
            f"GDVARYDV={_u(gold.get('GDVARYDV'))}",
        )

    if errors:
        print("FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS")
    if args.publish_test_validation:
        dest = args.output_dir / "Test_Validation"
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(plan_path, dest / "quikplan.csv")
        print(f"published {dest / 'quikplan.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
