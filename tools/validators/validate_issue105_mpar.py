"""
Issue #105 — quikridr.MPAR must match product quikplan.PAR by MPLAN.

Issue #119 (2026-07-27): Paid-up addition coverages are never participating. When
QLAdmin adds a PA coverage it sets PAR/MPAR to 0 even if the base is participating.
Synthetic *PA codes have no quikplan row by design (#111); they must still carry
MPAR=0 (not inherit base participating).

Usage:
  python tools/validators/validate_issue105_mpar.py
  python tools/validators/validate_issue105_mpar.py --output-dir QLA_Migration/Output
  python tools/validators/validate_issue105_mpar.py --publish-test-validation
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_VERSION = "1.2"
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
TRACE_POLICIES = (
    "9010143726C",
    "9010148272C",
    "9010382520C",
    "9010391228C",
    "9010310404C",
)


def _n(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def _is_pua_code(mplan: str) -> bool:
    """PUA codes are synthesised as base_mplan[:4] + 'PA' by _apply_pua_rider_inheritance.

    Deliberately narrow: the genuine ...PUA plans that do exist in quikplan (121PUA, 165PUA,
    170PUA) end in 'UA', not 'PA', so they are unaffected.
    """
    return len(mplan) == 6 and mplan.upper().endswith("PA")


def _load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Issue #105/#119 quikridr MPAR")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--publish-test-validation",
        action="store_true",
        help="On PASS, copy quikridr.csv to Output/Test_Validation/",
    )
    args = parser.parse_args()

    ridr_path = args.output_dir / "quikridr.csv"
    plan_path = args.output_dir / "quikplan.csv"
    if not ridr_path.exists():
        print(f"FAIL: missing {ridr_path}")
        return 1
    if not plan_path.exists():
        print(f"FAIL: missing {plan_path}")
        return 1

    ridr = _load_csv(ridr_path)
    plan = _load_csv(plan_path)
    par_map = {_n(r.get("PLAN")): _n(r.get("PAR")) for r in plan if _n(r.get("PLAN"))}

    errors: list[str] = []
    mismatch_par1 = 0
    mismatch_par0 = 0
    mismatch_pua = 0
    invalid_mpar = 0
    expected_1 = 0
    expected_0 = 0
    pua_rows = 0
    orphan_nonpua = 0
    orphan_plans: Counter[str] = Counter()
    mpar_counts: Counter[str] = Counter()

    for i, row in enumerate(ridr, start=2):
        mplan = _n(row.get("MPLAN"))
        mpar = _n(row.get("MPAR"))
        mpolicy = _n(row.get("MPOLICY"))
        mpar_counts[mpar] += 1

        if mpar not in ("0", "1"):
            invalid_mpar += 1
            if invalid_mpar <= 5:
                errors.append(f"line {i}: invalid MPAR={mpar!r} MPLAN={mplan}")

        # Issue #119: PUA coverages always non-participating (checked before plan map).
        if _is_pua_code(mplan):
            pua_rows += 1
            expected_0 += 1
            if mpar != "0":
                mismatch_pua += 1
                if mismatch_pua <= 5:
                    errors.append(
                        f"line {i}: PUA {mplan} on {mpolicy} has MPAR={mpar!r} "
                        f"(Issue #119 expects 0)"
                    )
            continue

        if mplan not in par_map:
            orphan_nonpua += 1
            orphan_plans[mplan] += 1
            if orphan_nonpua <= 5:
                errors.append(
                    f"line {i}: MPLAN={mplan} has no quikplan row and is not a PUA code "
                    f"MPOLICY={mpolicy}"
                )
            continue

        plan_par = par_map[mplan]
        if plan_par == "1":
            expected_1 += 1
            if mpar != "1":
                mismatch_par1 += 1
                if mismatch_par1 <= 5:
                    errors.append(
                        f"line {i}: plan PAR=1 but MPAR={mpar!r} "
                        f"MPOLICY={mpolicy} MPLAN={mplan}"
                    )
        else:
            expected_0 += 1
            if mpar == "1":
                mismatch_par0 += 1
                if mismatch_par0 <= 5:
                    errors.append(
                        f"line {i}: plan PAR!=1 but MPAR=1 "
                        f"MPOLICY={mpolicy} MPLAN={mplan} PLAN_PAR={plan_par!r}"
                    )

    if mismatch_par1:
        errors.append(f"total plan-PAR=1 with MPAR!=1: {mismatch_par1}")
    if mismatch_par0:
        errors.append(f"total plan-PAR!=1 with MPAR=1: {mismatch_par0}")
    if mismatch_pua:
        errors.append(f"total PUA rows with MPAR!=0 (Issue #119): {mismatch_pua}")
    if invalid_mpar:
        errors.append(f"total invalid MPAR values: {invalid_mpar}")
    if orphan_nonpua:
        errors.append(
            f"total non-PUA rows with no quikplan row: {orphan_nonpua} "
            f"(plans: {dict(orphan_plans)})"
        )

    print(f"validate_issue105_mpar.py v{SCRIPT_VERSION}")
    print(f"output: {args.output_dir}")
    print(f"quikridr rows: {len(ridr)}")
    print(f"MPAR value counts: {dict(mpar_counts)}")
    print(f"non-PUA rows with plan PAR=1 (expect MPAR=1): {expected_1}")
    print(f"rows expecting MPAR=0 (non-par products + PUA): {expected_0}")
    print(f"PUA rows (Issue #119 expect MPAR=0): {pua_rows}")
    print(f"non-PUA rows with no quikplan row (must be 0): {orphan_nonpua}")
    print("trace:")
    for pol in TRACE_POLICIES:
        hits = [r for r in ridr if _n(r.get("MPOLICY")) == pol]
        if not hits:
            print(f"  {pol}: NOT FOUND")
            continue
        # Prefer a PUA phase when present (Issue #119), else phase 1.
        row = next((r for r in hits if _is_pua_code(_n(r.get("MPLAN")))), None)
        if row is None:
            row = next((r for r in hits if _n(r.get("MPHASE")) in ("1", "01")), hits[0])
        mplan = _n(row.get("MPLAN"))
        if _is_pua_code(mplan):
            via = "PUA expect MPAR=0 (#119)"
        elif mplan in par_map:
            via = f"planPAR={par_map[mplan]}"
        else:
            via = "planPAR=(no plan row)"
        print(
            f"  {pol} phase={_n(row.get('MPHASE'))} MPLAN={mplan} "
            f"MPAR={_n(row.get('MPAR'))} {via}"
        )

    if errors:
        print("FAIL")
        for e in errors[:25]:
            print(f"  - {e}")
        return 1

    print("PASS")
    if args.publish_test_validation:
        tv = args.output_dir / "Test_Validation"
        tv.mkdir(parents=True, exist_ok=True)
        dest = tv / "quikridr.csv"
        shutil.copy2(ridr_path, dest)
        manifest = tv / "manifest.txt"
        with manifest.open("a", encoding="utf-8") as f:
            f.write(
                f"{datetime.now().isoformat(timespec='seconds')} Issue_105_119 "
                f"published quikridr.csv ({len(ridr)} rows)\n"
            )
        print(f"Published {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
