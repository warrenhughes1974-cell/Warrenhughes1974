"""
Issue #59 MSTATUS validation (v57.84).

Scoped client-policy fix only:
  - 6 Active+LP policies: MSTATUS 54 → 22
  - 010521213C (S+DP): MSTATUS 41 → 50

Hard guard: vs pre-v57.84 baseline, NO other MPOLICY may change MSTATUS.

Usage:
  python tools/validators/validate_issue59_mstatus.py
  python tools/validators/validate_issue59_mstatus.py --output-dir QLA_Migration/Output
  python tools/validators/validate_issue59_mstatus.py --simulate-only
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

SCRIPT_VERSION = "1.0"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
TEST_VALIDATION = DEFAULT_OUTPUT / "Test_Validation"
BASELINE = (
    PROJECT_ROOT
    / "Issue_Log_Items"
    / "Issue_59"
    / "evidence"
    / "quikmstr_pre_v5784_baseline.csv"
)
MVT = PROJECT_ROOT / "QLA_Migration" / "Mapping" / "Master_Value_Translation.csv"

# Exact QLA keys (normalized strip) allowed to change
ALLOWED_DELTAS = {
    "01122D991C": "22",
    "014FG8217C": "22",
    "016FG8217C": "22",
    "01ML8171C": "22",
    "01ML8250C": "22",
    "01ML8522C": "22",
    "010521213C": "50",
}

# Issue #49 preserve samples (must remain unchanged vs baseline)
ISSUE49_PRESERVE = ("018252C", "018253C", "01ML8007C", "018187C", "010380550C")


def _norm(v) -> str:
    s = str(v).strip() if v is not None else ""
    if s.endswith(".0"):
        s = s[:-2]
    if s.lower() in ("nan", "none"):
        return ""
    return s


def load_st() -> dict[str, str]:
    out: dict[str, str] = {}
    with MVT.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            k = _norm(row.get("Source_Code"))
            if k.startswith("ST_"):
                out[k] = _norm(row.get("QLA_Result"))
    return out


def load_mstatus(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return {_norm(r["MPOLICY"]): _norm(r["MSTATUS"]) for r in csv.DictReader(f)}


def simulate_scoped_keys() -> dict[str, str]:
    """Expected ST results for the 7 scoped composites."""
    st = load_st()
    return {
        "01122D991C": st["ST_A_"],
        "014FG8217C": st["ST_A_"],
        "016FG8217C": st["ST_A_"],
        "01ML8171C": st["ST_A_"],
        "01ML8250C": st["ST_A_"],
        "01ML8522C": st["ST_A_"],
        "010521213C": st["ST_S_DP"],
    }


def publish_test_validation(output_dir: Path) -> None:
    TEST_VALIDATION.mkdir(parents=True, exist_ok=True)
    for name in ("quikmstr.csv",):
        src = output_dir / name
        if src.exists():
            dst = TEST_VALIDATION / name
            dst.write_bytes(src.read_bytes())
            print(f"Published {dst}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Issue #59 MSTATUS scoped validation")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--simulate-only", action="store_true")
    ap.add_argument("--publish-test-validation", action="store_true")
    args = ap.parse_args()

    print(f"validate_issue59_mstatus.py {SCRIPT_VERSION}")
    errors: list[str] = []

    sim = simulate_scoped_keys()
    for pol, exp in ALLOWED_DELTAS.items():
        if sim.get(pol) != exp:
            errors.append(f"SIM translation mismatch {pol}: got {sim.get(pol)} expected {exp}")

    if args.simulate_only:
        if errors:
            print("FAIL (simulate)")
            for e in errors:
                print(" ", e)
            return 1
        print("PASS (simulate) — ST_A_=22 and ST_S_DP=50 for scoped keys")
        return 0

    mstr_path = args.output_dir / "quikmstr.csv"
    if not mstr_path.exists():
        print(f"FAIL — missing {mstr_path}")
        return 1
    if not BASELINE.exists():
        print(f"FAIL — missing baseline {BASELINE}")
        return 1

    current = load_mstatus(mstr_path)
    baseline = load_mstatus(BASELINE)

    # Trace expectations
    for pol, exp in ALLOWED_DELTAS.items():
        got = current.get(pol)
        if got != exp:
            errors.append(f"TRACE {pol}: MSTATUS={got!r} expected {exp!r}")

    # Hard guard: only allowed policies may differ from baseline
    unexpected: list[str] = []
    missing_baseline = 0
    for pol, before in baseline.items():
        after = current.get(pol)
        if after is None:
            missing_baseline += 1
            continue
        if after == before:
            continue
        if pol not in ALLOWED_DELTAS:
            unexpected.append(f"{pol}: {before} → {after}")
        else:
            if after != ALLOWED_DELTAS[pol]:
                errors.append(
                    f"ALLOWED delta wrong {pol}: {before} → {after} (want {ALLOWED_DELTAS[pol]})"
                )

    if unexpected:
        errors.append(f"UNEXPECTED MSTATUS changes ({len(unexpected)}):")
        for u in unexpected[:25]:
            errors.append(f"  {u}")
        if len(unexpected) > 25:
            errors.append(f"  ... +{len(unexpected) - 25} more")

    # Confirm each allowed policy actually changed from baseline as expected
    for pol, exp in ALLOWED_DELTAS.items():
        before = baseline.get(pol)
        after = current.get(pol)
        if before == after:
            errors.append(f"NO CHANGE vs baseline for required policy {pol} (still {after})")
        elif after != exp:
            errors.append(f"{pol} after={after} expected {exp} (baseline was {before})")

    # #49 samples unchanged vs baseline
    for pol in ISSUE49_PRESERVE:
        if pol in baseline and baseline[pol] != current.get(pol):
            errors.append(
                f"Issue #49 preserve broken {pol}: {baseline[pol]} → {current.get(pol)}"
            )

    if len(current) != len(baseline):
        # row count drift is a warning unless keys missing
        only_cur = set(current) - set(baseline)
        only_base = set(baseline) - set(current)
        if only_cur or only_base:
            errors.append(
                f"MPOLICY set drift: +{len(only_cur)} / -{len(only_base)} vs baseline"
            )

    if errors:
        print("FAIL")
        for e in errors:
            print(" ", e)
        return 1

    print("PASS")
    print(f"  Scoped traces OK ({len(ALLOWED_DELTAS)})")
    print("  No unexpected MSTATUS deltas vs pre-v57.84 baseline")
    print("  Issue #49 preserve samples unchanged")
    if args.publish_test_validation:
        publish_test_validation(args.output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
