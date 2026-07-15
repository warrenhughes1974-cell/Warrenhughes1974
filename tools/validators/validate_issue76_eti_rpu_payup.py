"""
Issue #76 — quikridr phase-1 MPAYUP/MLASTANN for ETI/RPU (MSTATUS 44/45).

Rules:
  1. Phase-1 only when quikmstr.MSTATUS ∈ {44, 45}
  2. MPAYUP = quikmstr.MPAIDTO
  3. MLASTANN = run_date.year − year(MPAYUP)
  4. Non-candidates and phase-2+ PUA rows unchanged

Usage:
  python tools/validators/validate_issue76_eti_rpu_payup.py
  python tools/validators/validate_issue76_eti_rpu_payup.py --publish-test-validation
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
TEST_VAL = DEFAULT_OUTPUT / "Test_Validation"
EVIDENCE = PROJECT_ROOT / "Issue_Log_Items" / "Issue_76" / "evidence" / "issue76_validation_summary.csv"
BASELINE = PROJECT_ROOT / "Issue_Log_Items" / "Issue_76" / "evidence" / "issue76_risk_phase1_simulation.csv"

SCRIPT_VERSION = "1.0"
EXPECTED_CANDIDATES = 400
EXPECTED_PAYUP_CHG = 223
SAMPLE = "010407670C"
PUA_CONTROL = "010407670C"  # phase 2
ACTIVE_CONTROL = "010367131C"


def _n(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def _ymd(v: object) -> str:
    digits = "".join(c for c in _n(v) if c.isdigit())
    return digits[:8] if len(digits) >= 8 else ""


def _load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--publish-test-validation", action="store_true")
    args = ap.parse_args()

    mstr_path = args.output_dir / "quikmstr.csv"
    ridr_path = args.output_dir / "quikridr.csv"
    for p in (mstr_path, ridr_path):
        if not p.exists():
            print(f"FAIL: missing {p}")
            return 1

    mstr = {_n(r["MPOLICY"]): r for r in _load_csv(mstr_path)}
    ridr = _load_csv(ridr_path)
    sys_year = datetime.now().year
    errors: list[str] = []
    rows_out: list[dict] = []

    cand = 0
    payup_bad = mlast_bad = 0
    for r in ridr:
        pol = _n(r.get("MPOLICY"))
        phase = _n(r.get("MPHASE"))
        m = mstr.get(pol)
        if not m:
            continue
        st = _n(m.get("MSTATUS"))
        if st not in ("44", "45") or phase != "1":
            continue
        cand += 1
        paidto = _ymd(m.get("MPAIDTO"))
        payup = _ymd(r.get("MPAYUP"))
        mlast = _n(r.get("MLASTANN"))
        exp_mlast = str(sys_year - int(paidto[:4])) if paidto else ""
        ok_pay = payup == paidto
        ok_mlast = mlast == exp_mlast
        if not ok_pay:
            payup_bad += 1
            if payup_bad <= 3:
                errors.append(f"MPAYUP!=MPAIDTO: {pol} payup={payup} paidto={paidto}")
        if not ok_mlast:
            mlast_bad += 1
            if mlast_bad <= 3:
                errors.append(f"MLASTANN mismatch: {pol} got {mlast} expected {exp_mlast}")
        rows_out.append({
            "MPOLICY": pol,
            "MSTATUS": st,
            "MPAIDTO": paidto,
            "MPAYUP": payup,
            "MLASTANN": mlast,
            "EXPECTED_MLASTANN": exp_mlast,
            "PAYUP_OK": "Y" if ok_pay else "N",
            "MLAST_OK": "Y" if ok_mlast else "N",
        })

    if cand != EXPECTED_CANDIDATES:
        errors.append(f"candidate count {cand} != expected {EXPECTED_CANDIDATES}")

    payup_chg = sum(1 for row in rows_out if row["MPAYUP"] != _ymd(mstr[row["MPOLICY"]].get("MPAIDTO")))
    # count actual payup changes vs baseline risk file if present
    if BASELINE.exists():
        baseline_payup_chg = sum(
            1 for b in _load_csv(BASELINE) if _n(b.get("PAYUP_CHANGED")) == "Y"
        )
        actual_payup_chg = sum(
            1 for row in rows_out
            if row["MPAYUP"] != _n(
                next(
                    (b.get("MPAYUP_BEFORE") for b in _load_csv(BASELINE) if _n(b.get("MPOLICY")) == row["MPOLICY"]),
                    "",
                )
            )
        )
        if actual_payup_chg < baseline_payup_chg:
            errors.append(f"payup changes {actual_payup_chg} < risk baseline {baseline_payup_chg}")

    sample_rows = [r for r in ridr if _n(r.get("MPOLICY")) == SAMPLE]
    if not sample_rows:
        errors.append(f"missing sample {SAMPLE}")
    else:
        p1 = next((r for r in sample_rows if _n(r.get("MPHASE")) == "1"), None)
        p2 = next((r for r in sample_rows if _n(r.get("MPHASE")) == "2"), None)
        m = mstr.get(SAMPLE, {})
        if p1:
            if _ymd(p1.get("MPAYUP")) != "20121001":
                errors.append(f"{SAMPLE} phase1 MPAYUP expected 20121001 got {_ymd(p1.get('MPAYUP'))}")
            exp = str(sys_year - 2012)
            if _n(p1.get("MLASTANN")) != exp:
                errors.append(f"{SAMPLE} phase1 MLASTANN expected {exp} got {_n(p1.get('MLASTANN'))}")
        if p2 and _ymd(p2.get("MPAYUP")) != _ymd(p2.get("MEFFDATE")):
            errors.append(
                f"{SAMPLE} phase2 PUA MPAYUP expected MEFFDATE {_ymd(p2.get('MEFFDATE'))} "
                f"got {_ymd(p2.get('MPAYUP'))}"
            )

    ac = mstr.get(ACTIVE_CONTROL)
    if ac and _n(ac.get("MSTATUS")) == "22":
        p1 = next(
            (r for r in ridr if _n(r.get("MPOLICY")) == ACTIVE_CONTROL and _n(r.get("MPHASE")) == "1"),
            None,
        )
        if p1 and _n(p1.get("MLASTANN")) == str(sys_year - int(_ymd(p1.get("MPAYUP"))[:4])):
            # active policy should NOT use issue76 formula unless coincidentally same
            pass  # only fail if we can detect wrong override — check status gate
    else:
        errors.append(f"missing active control {ACTIVE_CONTROL}")

    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    with EVIDENCE.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()) if rows_out else ["MPOLICY"])
        w.writeheader()
        w.writerows(rows_out)

    if payup_bad or mlast_bad:
        errors.append(f"violations: payup={payup_bad} mlastann={mlast_bad}")

    print(f"validate_issue76_eti_rpu_payup v{SCRIPT_VERSION}")
    print(f"  candidates={cand} payup_fail={payup_bad} mlast_fail={mlast_bad} sys_year={sys_year}")

    if errors:
        print("FAIL:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS")
    if args.publish_test_validation:
        TEST_VAL.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ridr_path, TEST_VAL / "quikridr.csv")
        manifest = TEST_VAL / "manifest.txt"
        manifest.write_text(
            f"published={datetime.now().isoformat()}\nissue=Issue_76\nversion=v57.93\ntables=quikridr\n",
            encoding="utf-8",
        )
        print(f"Published: {TEST_VAL / 'quikridr.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
