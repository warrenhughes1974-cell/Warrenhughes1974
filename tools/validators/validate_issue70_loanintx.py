"""
Issue #70 — QuikPlan LOANINTX from PCOVR.LOAN_ADV_ARREARS (0/N→A, 1→R).

Usage:
  python tools/validators/validate_issue70_loanintx.py
  python tools/validators/validate_issue70_loanintx.py --output-dir QLA_Migration/Output
  python tools/validators/validate_issue70_loanintx.py --publish-test-validation
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_VERSION = "1.0"
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
DEFAULT_PCOVR = (
    PROJECT_ROOT / "QLA_Migration" / "Source" / "PCOVR_Coverage_Extract_20260630.csv"
)
DEFAULT_CROSSWALK = PROJECT_ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"

EXPECTED_ARREARS_PLANS = frozenset({"1SALOL", "1SALML", "1SALMI", "9SLADB"})
EXPECTED_A = 137
EXPECTED_R = 4
# Issue #142 (v59.04): seeded 9SUBLF plan carries LOANINTX=A; exclude it from
# the pre-142 count guard so the original book expectation stays intact.
ISSUE142_PLAN = "9SUBLF"
TRACE_PLANS = {
    "1SALOL": "R",
    "1SALML": "R",
    "1SALMI": "R",
    "9SLADB": "R",
    "1960PO": "A",
}


def _n(v: object) -> str:
    return ("" if v is None else str(v)).strip().upper()


def _load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def _codebook_loanintx(raw: str) -> str:
    v = _n(raw)
    if v in ("0", "N"):
        return "A"
    if v == "1":
        return "R"
    return "A"


def _product_plan_map(crosswalk_path: Path) -> dict[str, str]:
    """Master_Crosswalk Old_Value → New_Value (coverage/plan product map)."""
    if not crosswalk_path.is_file():
        return {}
    out: dict[str, str] = {}
    for row in _load_csv(crosswalk_path):
        src = _n(row.get("Old_Value") or row.get("OLD_VALUE"))
        tgt = _n(row.get("New_Value") or row.get("NEW_VALUE"))
        if not src or not tgt:
            vals = list(row.values())
            if len(vals) >= 2:
                src = _n(vals[0])
                tgt = _n(vals[1])
        if src and tgt:
            out[src] = tgt
    return out


def _load_pcovr_expected(pcovr_path: Path, cw: dict[str, str]) -> dict[str, str]:
    """COVERAGE_ID → expected LOANINTX via codebook + crosswalk PLAN."""
    expected: dict[str, str] = {}
    if not pcovr_path.is_file():
        return expected
    for row in _load_csv(pcovr_path):
        cov = _n(row.get("COVERAGE_ID"))
        if not cov or cov.startswith("---") or set(cov) <= {"-"}:
            continue
        plan = cw.get(cov, cov)
        expected[plan] = _codebook_loanintx(row.get("LOAN_ADV_ARREARS", ""))
    return expected


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Issue #70 QuikPlan LOANINTX")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--pcovr", type=Path, default=DEFAULT_PCOVR)
    ap.add_argument("--crosswalk", type=Path, default=DEFAULT_CROSSWALK)
    ap.add_argument(
        "--publish-test-validation",
        action="store_true",
        help="On PASS, copy quikplan.csv to Output/Test_Validation/",
    )
    args = ap.parse_args()

    plan_path = args.output_dir / "quikplan.csv"
    print(f"validate_issue70_loanintx.py v{SCRIPT_VERSION}")
    print(f"output: {args.output_dir}")

    if not plan_path.is_file():
        print(f"FAIL: missing {plan_path}")
        return 1

    rows = _load_csv(plan_path)
    errors: list[str] = []
    counts = Counter(
        _n(r.get("LOANINTX")) for r in rows if _n(r.get("PLAN")) != ISSUE142_PLAN
    )
    by_plan = {_n(r.get("PLAN")): _n(r.get("LOANINTX")) for r in rows if _n(r.get("PLAN"))}

    print(f"rows: {len(rows)}")
    print(f"LOANINTX counts: {dict(counts)}")

    invalid = {k: v for k, v in counts.items() if k not in ("A", "R")}
    if invalid:
        errors.append(f"invalid LOANINTX values: {invalid}")
    if counts.get("A", 0) != EXPECTED_A:
        errors.append(f"LOANINTX=A count {counts.get('A', 0)} != expected {EXPECTED_A}")
    if counts.get("R", 0) != EXPECTED_R:
        errors.append(f"LOANINTX=R count {counts.get('R', 0)} != expected {EXPECTED_R}")

    arrears = {p for p, x in by_plan.items() if x == "R"}
    if arrears != EXPECTED_ARREARS_PLANS:
        errors.append(
            f"arrears plan set {sorted(arrears)} != expected {sorted(EXPECTED_ARREARS_PLANS)}"
        )

    print("trace:")
    for plan, expect in TRACE_PLANS.items():
        got = by_plan.get(plan, "MISSING")
        ok = "OK" if got == expect else "FAIL"
        print(f"  {plan}: LOANINTX={got} expected={expect} [{ok}]")
        if got != expect:
            errors.append(f"trace {plan}: got {got!r} expected {expect!r}")

    # Source fidelity vs raw PCOVR (optional if extract present)
    if args.pcovr.is_file():
        cw = _product_plan_map(args.crosswalk)
        expected = _load_pcovr_expected(args.pcovr, cw)
        mismatch = 0
        for plan, got in by_plan.items():
            exp = expected.get(plan)
            if exp is None:
                continue
            if got != exp:
                mismatch += 1
                if mismatch <= 5:
                    errors.append(f"source fidelity {plan}: Output={got} PCOVR->{exp}")
        print(f"PCOVR fidelity mismatches (first pass): {mismatch}")
    else:
        print(f"WARN: PCOVR not found at {args.pcovr}; skipped source fidelity")

    # QuikLoan non-regression sample (if present)
    loan_path = args.output_dir / "quikloan.csv"
    if loan_path.is_file():
        loans = _load_csv(loan_path)
        sample = [
            r for r in loans if _n(r.get("MPOLICY")) in ("9010331768C", " 9010331768C".upper())
            or _n(r.get("MPOLICY")).endswith("010331768C")
        ]
        # Match padded or unpadded
        sample = [r for r in loans if "010331768" in _n(r.get("MPOLICY"))]
        if sample:
            mloanintx = _n(sample[0].get("MLOANINTX"))
            print(f"QuikLoan sample 9010331768*: MLOANINTX={mloanintx}")
            if mloanintx not in ("", "A"):
                errors.append(
                    f"QuikLoan sample MLOANINTX={mloanintx!r} expected A (non-SAL control)"
                )
        else:
            print("QuikLoan sample 9010331768*: NOT FOUND (skip)")
    else:
        print("WARN: quikloan.csv missing; skipped QuikLoan sample")

    if errors:
        print("FAIL")
        for e in errors[:20]:
            print(f"  - {e}")
        return 1

    print("PASS")
    if args.publish_test_validation:
        dest_dir = args.output_dir / "Test_Validation"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "quikplan.csv"
        shutil.copy2(plan_path, dest)
        print(f"published: {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
