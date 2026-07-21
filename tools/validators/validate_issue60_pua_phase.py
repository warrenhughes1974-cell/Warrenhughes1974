"""
Issue #60 PUA phase validation (v57.85).

Chris plan / Track A:
  - PUA rows only (synthetic *PA MPLAN): MEFFDATE/MAGE/MPAYUP/MLASTANN align to base phase 1
  - MPHSTAT=41 when base MPHSTAT < 50
  - Non-PUA later-phase riders: MEFFDATE/MAGE unchanged vs pre-v57.85 baseline

Usage:
  python tools/validators/validate_issue60_pua_phase.py
  python tools/validators/validate_issue60_pua_phase.py --output-dir QLA_Migration/Output
  python tools/validators/validate_issue60_pua_phase.py --publish-test-validation
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_VERSION = "1.0"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
TEST_VALIDATION = DEFAULT_OUTPUT / "Test_Validation"
BASELINE = (
    PROJECT_ROOT
    / "Issue_Log_Items"
    / "Issue_60"
    / "evidence"
    / "quikridr_pre_v5785_baseline.csv"
)

GOLDEN = "010310404C"
MIXED_POLICY = "010150910C"  # PUA + ADB — other rider must not move


def _norm(v) -> str:
    s = str(v).strip() if v is not None else ""
    if s.endswith(".0"):
        s = s[:-2]
    if s.lower() in ("nan", "none"):
        return ""
    return s


def _status_int(raw: str) -> int:
    try:
        return int("".join(c for c in _norm(raw) if c.isdigit()) or "99")
    except ValueError:
        return 99


def is_pua_mplan(mplan: str) -> bool:
    p = _norm(mplan)
    return len(p) >= 6 and p.endswith("PA")


def load_ridrs(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def row_key(row: dict) -> tuple[str, str, str]:
    return (_norm(row.get("MPOLICY")), _norm(row.get("MPHASE")), _norm(row.get("MPLAN")))


def publish_test_validation(output_dir: Path) -> None:
    TEST_VALIDATION.mkdir(parents=True, exist_ok=True)
    src = output_dir / "quikridr.csv"
    if src.exists():
        dst = TEST_VALIDATION / "quikridr.csv"
        dst.write_bytes(src.read_bytes())
        print(f"Published {dst}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Issue #60 PUA phase validation")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--publish-test-validation", action="store_true")
    args = ap.parse_args()

    print(f"validate_issue60_pua_phase.py {SCRIPT_VERSION}")
    errors: list[str] = []

    ridr_path = args.output_dir / "quikridr.csv"
    if not ridr_path.exists():
        print(f"FAIL — missing {ridr_path}")
        return 1
    if not BASELINE.exists():
        print(f"FAIL — missing baseline {BASELINE}")
        return 1

    current = load_ridrs(ridr_path)
    baseline_rows = load_ridrs(BASELINE)
    baseline_by_key = {row_key(r): r for r in baseline_rows}
    current_by_key = {row_key(r): r for r in current}

    by_pol_cur: dict[str, list[dict]] = defaultdict(list)
    for r in current:
        by_pol_cur[_norm(r["MPOLICY"])].append(r)

    def base_of(pol: str) -> dict | None:
        for r in by_pol_cur.get(pol, []):
            if _norm(r.get("MPHASE")) in ("1", "01"):
                return r
        return None

    pua_rows = [r for r in current if is_pua_mplan(r.get("MPLAN", ""))]
    other_later = [
        r
        for r in current
        if not is_pua_mplan(r.get("MPLAN", ""))
        and _norm(r.get("MPHASE")) not in ("1", "01")
    ]

    # Golden trace
    golden_pua = next((r for r in pua_rows if _norm(r["MPOLICY"]) == GOLDEN), None)
    golden_base = base_of(GOLDEN)
    if not golden_pua or not golden_base:
        errors.append(f"TRACE missing golden policy {GOLDEN}")
    else:
        exp = {
            "MPHSTAT": "41",
            "MEFFDATE": _norm(golden_base.get("MEFFDATE")),
            "MAGE": _norm(golden_base.get("MAGE")),
            "MPAYUP": _norm(golden_base.get("MEFFDATE")),
            "MLASTANN": _norm(golden_base.get("MLASTANN")),
        }
        for f, v in exp.items():
            got = _norm(golden_pua.get(f))
            if got != v:
                errors.append(f"TRACE {GOLDEN} PUA {f}={got!r} expected {v!r}")

    # Mixed policy — ADB unchanged
    for r in current:
        if _norm(r["MPOLICY"]) != MIXED_POLICY:
            continue
        if _norm(r.get("MPLAN")) == "920ADB":
            bk = baseline_by_key.get(row_key(r))
            if not bk:
                errors.append(f"TRACE {MIXED_POLICY} ADB missing in baseline")
            else:
                for f in ("MEFFDATE", "MAGE", "MPHSTAT", "MPAYUP", "MLASTANN"):
                    if _norm(r.get(f)) != _norm(bk.get(f)):
                        errors.append(
                            f"TRACE {MIXED_POLICY} ADB {f} changed "
                            f"{_norm(bk.get(f))!r} -> {_norm(r.get(f))!r}"
                        )

    # Fleet PUA rules
    pua_violations = 0
    for r in pua_rows:
        pol = _norm(r["MPOLICY"])
        base = base_of(pol)
        if not base:
            errors.append(f"PUA {pol} ph={_norm(r.get('MPHASE'))}: no base phase")
            continue
        be = _norm(base.get("MEFFDATE"))
        ba = _norm(base.get("MAGE"))
        bl = _norm(base.get("MLASTANN"))
        if _norm(r.get("MEFFDATE")) != be:
            pua_violations += 1
            if pua_violations <= 5:
                errors.append(f"PUA {pol}: MEFFDATE != base")
        if _norm(r.get("MAGE")) != ba:
            pua_violations += 1
            if pua_violations <= 5:
                errors.append(f"PUA {pol}: MAGE != base")
        if _norm(r.get("MPAYUP")) != be:
            pua_violations += 1
            if pua_violations <= 5:
                errors.append(f"PUA {pol}: MPAYUP != base MEFFDATE")
        if bl and _norm(r.get("MLASTANN")) != bl:
            pua_violations += 1
            if pua_violations <= 5:
                errors.append(f"PUA {pol}: MLASTANN != base")
        bs = _status_int(base.get("MPHSTAT", ""))
        if bs < 50 and _norm(r.get("MPHSTAT")) != "41":
            pua_violations += 1
            if pua_violations <= 5:
                errors.append(f"PUA {pol}: expected MPHSTAT=41 (base active)")
        if bs >= 50 and _norm(r.get("MPHSTAT")) == "41":
            pua_violations += 1
            if pua_violations <= 5:
                errors.append(f"PUA {pol}: forced 41 on terminated base")

    if pua_violations > 5:
        errors.append(f"PUA fleet violations: {pua_violations} (first 5 listed)")

    # Hard guard: non-PUA later phases MEFFDATE/MAGE unchanged vs baseline
    other_deltas = 0
    for r in other_later:
        k = row_key(r)
        bk = baseline_by_key.get(k)
        if not bk:
            continue
        for f in ("MEFFDATE", "MAGE"):
            if _norm(r.get(f)) != _norm(bk.get(f)):
                other_deltas += 1
                if other_deltas <= 5:
                    errors.append(
                        f"NON-PUA delta {k} {f}: "
                        f"{_norm(bk.get(f))!r} -> {_norm(r.get(f))!r}"
                    )
    if other_deltas > 5:
        errors.append(f"Non-PUA rider date/age deltas: {other_deltas} (first 5 listed)")

    # Phase-1 base unchanged vs baseline
    phase1_deltas = 0
    for r in current:
        if _norm(r.get("MPHASE")) not in ("1", "01"):
            continue
        k = row_key(r)
        bk = baseline_by_key.get(k)
        if not bk:
            continue
        for f in ("MEFFDATE", "MAGE", "MPHSTAT", "MPAYUP", "MLASTANN", "MPREM"):
            if _norm(r.get(f)) != _norm(bk.get(f)):
                phase1_deltas += 1
                if phase1_deltas <= 3:
                    errors.append(f"PHASE1 delta {k} {f}")

    if phase1_deltas > 3:
        errors.append(f"Phase-1 field deltas vs baseline: {phase1_deltas}")

    print(f"PUA rows checked: {len(pua_rows)}")
    print(f"Other later-phase rows checked: {len(other_later)}")

    if errors:
        print("FAIL")
        for e in errors:
            print(" ", e)
        return 1

    print("PASS — Issue #60 Track A PUA phase rules; other riders unchanged")
    if args.publish_test_validation:
        publish_test_validation(args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
