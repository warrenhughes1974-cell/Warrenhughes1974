"""
Issue #105 — quikridr.MPAR must match product quikplan.PAR by MPLAN.

Paid-up additions (Issue #111): QLAdmin does not create plans for PUA coverages, so a
synthesised PUA code such as 1708PA has no quikplan row by design and a direct lookup finds
nothing. v1.0 read that as "plan is not participating" and failed 493 rows. Those rows are
resolved through the policy's phase 1 base plan instead, which is the plan the PUA inherits
from. This is still a real comparison, not a skip — a PUA over a participating base must
carry MPAR=1 and a PUA over a non-par base must carry 0.

A plan code with no quikplan row that is *not* a PUA code remains an error: that would be a
genuine product-row orphan.

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
SCRIPT_VERSION = "1.1"
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
TRACE_POLICIES = (
    "9010143726C",
    "9010148272C",
    "9010382520C",
    "9010391228C",
)


def _n(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def _is_pua_code(mplan: str) -> bool:
    """PUA codes are synthesised as base_mplan[:4] + 'PA' by _apply_pua_rider_inheritance.

    Deliberately narrow: the genuine ...PUA plans that do exist in quikplan (121PUA, 165PUA,
    170PUA) end in 'UA', not 'PA', so they are unaffected. Callers check the direct quikplan
    lookup first, so a real plan ending in PA is never routed through here.
    """
    return len(mplan) == 6 and mplan.upper().endswith("PA")


def _base_plan_by_policy(ridr: list[dict]) -> dict[str, str]:
    """Phase 1 MPLAN per policy — the plan a PUA rider inherits its participation from."""
    base: dict[str, str] = {}
    for row in ridr:
        if _n(row.get("MPHASE")) in ("1", "01"):
            pol = _n(row.get("MPOLICY"))
            if pol:
                base[pol] = _n(row.get("MPLAN"))
    return base


def _load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Issue #105 quikridr MPAR")
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

    base_map = _base_plan_by_policy(ridr)

    errors: list[str] = []
    mismatch_par1 = 0
    mismatch_par0 = 0
    invalid_mpar = 0
    expected_1 = 0
    expected_0 = 0
    pua_resolved = 0
    pua_unresolved = 0
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

        if mplan in par_map:
            plan_par = par_map[mplan]
        elif _is_pua_code(mplan):
            # QLAdmin has no plan for a PUA; inherit participation from the base coverage.
            base = base_map.get(mpolicy, "")
            if base and base in par_map:
                plan_par = par_map[base]
                pua_resolved += 1
            else:
                pua_unresolved += 1
                if pua_unresolved <= 5:
                    errors.append(
                        f"line {i}: PUA {mplan} on {mpolicy} cannot resolve a base plan "
                        f"(phase 1 MPLAN={base or '(none)'!r})"
                    )
                continue
        else:
            orphan_nonpua += 1
            orphan_plans[mplan] += 1
            if orphan_nonpua <= 5:
                errors.append(
                    f"line {i}: MPLAN={mplan} has no quikplan row and is not a PUA code "
                    f"MPOLICY={mpolicy}"
                )
            continue

        if plan_par == "1":
            expected_1 += 1
            if mpar != "1":
                mismatch_par1 += 1
                if mismatch_par1 <= 5:
                    errors.append(
                        f"line {i}: plan PAR=1 but MPAR={mpar!r} "
                        f"MPOLICY={_n(row.get('MPOLICY'))} MPLAN={mplan}"
                    )
        else:
            expected_0 += 1
            if mpar == "1":
                mismatch_par0 += 1
                if mismatch_par0 <= 5:
                    errors.append(
                        f"line {i}: plan PAR!=1 but MPAR=1 "
                        f"MPOLICY={_n(row.get('MPOLICY'))} MPLAN={mplan} PLAN_PAR={plan_par!r}"
                    )

    if mismatch_par1:
        errors.append(f"total plan-PAR=1 with MPAR!=1: {mismatch_par1}")
    if mismatch_par0:
        errors.append(f"total plan-PAR!=1 with MPAR=1: {mismatch_par0}")
    if invalid_mpar:
        errors.append(f"total invalid MPAR values: {invalid_mpar}")
    if pua_unresolved:
        errors.append(f"total PUA rows with no resolvable base plan: {pua_unresolved}")
    if orphan_nonpua:
        errors.append(
            f"total non-PUA rows with no quikplan row: {orphan_nonpua} "
            f"(plans: {dict(orphan_plans)})"
        )

    print(f"validate_issue105_mpar.py v{SCRIPT_VERSION}")
    print(f"output: {args.output_dir}")
    print(f"quikridr rows: {len(ridr)}")
    print(f"MPAR value counts: {dict(mpar_counts)}")
    print(f"rows with plan PAR=1 (expect MPAR=1): {expected_1}")
    print(f"rows with plan PAR!=1 (expect MPAR=0): {expected_0}")
    print(f"PUA rows resolved via phase-1 base plan (Issue #111): {pua_resolved}")
    print(f"non-PUA rows with no quikplan row (must be 0): {orphan_nonpua}")
    print("trace (prefer MPHASE=1):")
    for pol in TRACE_POLICIES:
        hits = [r for r in ridr if _n(r.get("MPOLICY")) == pol]
        if not hits:
            print(f"  {pol}: NOT FOUND")
            continue
        row = next((r for r in hits if _n(r.get("MPHASE")) in ("1", "01")), hits[0])
        mplan = _n(row.get("MPLAN"))
        if mplan in par_map:
            via = f"planPAR={par_map[mplan]}"
        elif _is_pua_code(mplan):
            base = base_map.get(pol, "")
            via = f"planPAR={par_map.get(base, '')} via base {base or '(none)'}"
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
                f"{datetime.now().isoformat(timespec='seconds')} Issue_105 "
                f"published quikridr.csv ({len(ridr)} rows)\n"
            )
        print(f"Published {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
