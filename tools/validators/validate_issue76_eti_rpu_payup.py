"""
Issue #76 — quikridr phase-1 MPAYUP/MLASTANN for ETI/RPU (MSTATUS 44/45).

Rules:
  1. Phase-1 only when quikmstr.MSTATUS in {44, 45}
  2. MPAYUP = quikmstr.MPAIDTO
  3. MLASTANN = completed years from MPAYUP to the batch valuation date, measured to the
     NFO anniversary (Issue #108B). The pre-v58.32 rule subtracted calendar years against
     the system clock, which ran a year high whenever the anniversary had not yet occurred
     and made the value drift between reruns of the same batch.
  4. Non-candidates and phase-2+ PUA rows unchanged

Candidate count is active-cut / source-aware. The midyear frozen count (400) is not a
hard GAP; when no same-cut count baseline exists the validator WARNs and still proves
payup / MLASTANN behavior.

Valuation date resolves the same way app.py does: QLA_VALUATION_DATE (YYYYMMDD) if set,
otherwise today. Pass --valuation-date to override when checking an older package.

Usage:
  python tools/validators/validate_issue76_eti_rpu_payup.py
  python tools/validators/validate_issue76_eti_rpu_payup.py --valuation-date 20251231
  python tools/validators/validate_issue76_eti_rpu_payup.py --publish-test-validation
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
TEST_VAL = DEFAULT_OUTPUT / "Test_Validation"
EVIDENCE_DIR = PROJECT_ROOT / "Issue_Log_Items" / "Issue_76" / "evidence"
EVIDENCE = EVIDENCE_DIR / "issue76_validation_summary.csv"

SCRIPT_VERSION = "2.1"
MIDYEAR_CANDIDATE_COUNT = 400  # informational only; not a hard GAP on later cuts

# Issue #2 (v58.29): MPOLICY is source POLICY_NUMBER + "C" at width 11. Traces below are
# recorded in the original 10-char form, so all lookups go through _canon.
SAMPLE = "010407670C"
ACTIVE_CONTROL = "010367131C"


def _n(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def _canon(v: object) -> str:
    """Policy identity that matches across the Issue #2 key change.

    Issue #25 emitted the source number with the leading 9 stripped; Issue #2 emits it
    whole. Dropping a trailing C and a single leading 9 makes both forms comparable.
    """
    s = _n(v).upper()
    if s.endswith("C"):
        s = s[:-1]
    if s.startswith("9"):
        s = s[1:]
    return s


def _ymd(v: object) -> str:
    digits = "".join(c for c in _n(v) if c.isdigit())
    return digits[:8] if len(digits) >= 8 else ""


def _as_date(ymd: str) -> date | None:
    if len(ymd) != 8:
        return None
    try:
        return date(int(ymd[:4]), int(ymd[4:6]), int(ymd[6:8]))
    except ValueError:
        return None


def _expected_mlastann(paidto: str, val: date) -> str:
    nfo = _as_date(paidto)
    if not nfo:
        return ""
    dur = val.year - nfo.year - ((val.month, val.day) < (nfo.month, nfo.day))
    return str(dur if dur >= 0 else 0)


def _resolve_valuation_date(explicit: str | None) -> tuple[date, str]:
    raw = explicit or os.environ.get("QLA_VALUATION_DATE", "").strip()
    if raw:
        digits = "".join(c for c in raw if c.isdigit())
        d = _as_date(digits)
        if d:
            return d, f"QLA_VALUATION_DATE={digits}"
    return datetime.now().date(), "system date"


def _load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def _same_cut_candidate_expectation(val: date) -> tuple[int | None, str]:
    """Optional same-cut expected count file in Issue_76/evidence/."""
    vymd = val.strftime("%Y%m%d")
    for name in (
        f"issue76_expected_candidates_{vymd}.txt",
        "issue76_expected_candidates_active_cut.txt",
    ):
        path = EVIDENCE_DIR / name
        if not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
        if not raw:
            continue
        digits = "".join(c for c in raw[0] if c.isdigit())
        if digits:
            return int(digits), path.name
    return None, ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--valuation-date", default=None, help="YYYYMMDD")
    ap.add_argument("--publish-test-validation", action="store_true")
    args = ap.parse_args()

    mstr_path = args.output_dir / "quikmstr.csv"
    ridr_path = args.output_dir / "quikridr.csv"
    for p in (mstr_path, ridr_path):
        if not p.exists():
            print(f"FAIL: missing {p}")
            return 1

    mstr = {_canon(r.get("MPOLICY")): r for r in _load_csv(mstr_path)}
    ridr = _load_csv(ridr_path)
    val_date, val_src = _resolve_valuation_date(args.valuation_date)
    errors: list[str] = []
    warnings: list[str] = []
    rows_out: list[dict] = []

    cand = 0
    payup_bad = mlast_bad = 0
    for r in ridr:
        pol = _canon(r.get("MPOLICY"))
        if _n(r.get("MPHASE")) != "1":
            continue
        m = mstr.get(pol)
        if not m:
            continue
        st = _n(m.get("MSTATUS"))
        if st not in ("44", "45"):
            continue
        cand += 1
        paidto = _ymd(m.get("MPAIDTO"))
        payup = _ymd(r.get("MPAYUP"))
        mlast = _n(r.get("MLASTANN"))
        exp_mlast = _expected_mlastann(paidto, val_date)
        ok_pay = payup == paidto
        ok_mlast = mlast == exp_mlast
        if not ok_pay:
            payup_bad += 1
            if payup_bad <= 3:
                errors.append(f"MPAYUP!=MPAIDTO: {_n(r.get('MPOLICY'))} payup={payup} paidto={paidto}")
        if not ok_mlast:
            mlast_bad += 1
            if mlast_bad <= 3:
                errors.append(
                    f"MLASTANN mismatch: {_n(r.get('MPOLICY'))} got {mlast} expected {exp_mlast} "
                    f"(paidto={paidto} val={val_date:%Y%m%d})"
                )
        rows_out.append({
            "MPOLICY": _n(r.get("MPOLICY")),
            "MSTATUS": st,
            "MPAIDTO": paidto,
            "MPAYUP": payup,
            "MLASTANN": mlast,
            "EXPECTED_MLASTANN": exp_mlast,
            "PAYUP_OK": "Y" if ok_pay else "N",
            "MLAST_OK": "Y" if ok_mlast else "N",
        })

    if cand < 1:
        errors.append("no ETI/RPU phase-1 candidates in active cut")
    else:
        exp_count, exp_src = _same_cut_candidate_expectation(val_date)
        if exp_count is not None:
            if cand != exp_count:
                errors.append(
                    f"candidate count {cand} != same-cut expected {exp_count} ({exp_src})"
                )
            else:
                print(f"OK: candidate count {cand} matches same-cut baseline {exp_src}")
        else:
            warnings.append(
                f"no same-cut candidate-count baseline; active-cut candidates={cand} "
                f"(midyear frozen {MIDYEAR_CANDIDATE_COUNT} not required)"
            )

    # Trace: phase-1 pay-up moves to paid-to; the phase-2 PUA row keeps base MEFFDATE.
    sample_rows = [r for r in ridr if _canon(r.get("MPOLICY")) == _canon(SAMPLE)]
    if not sample_rows:
        errors.append(f"missing sample {SAMPLE}")
    else:
        p1 = next((r for r in sample_rows if _n(r.get("MPHASE")) == "1"), None)
        p2 = next((r for r in sample_rows if _n(r.get("MPHASE")) == "2"), None)
        if p1:
            if _ymd(p1.get("MPAYUP")) != "20121001":
                errors.append(f"{SAMPLE} phase1 MPAYUP expected 20121001 got {_ymd(p1.get('MPAYUP'))}")
            exp = _expected_mlastann("20121001", val_date)
            if _n(p1.get("MLASTANN")) != exp:
                errors.append(f"{SAMPLE} phase1 MLASTANN expected {exp} got {_n(p1.get('MLASTANN'))}")
        if p2 and _ymd(p2.get("MPAYUP")) != _ymd(p2.get("MEFFDATE")):
            errors.append(
                f"{SAMPLE} phase2 PUA MPAYUP expected MEFFDATE {_ymd(p2.get('MEFFDATE'))} "
                f"got {_ymd(p2.get('MPAYUP'))}"
            )

    # Control: an active policy must not receive the ETI/RPU pay-up override.
    ac = mstr.get(_canon(ACTIVE_CONTROL))
    if not ac:
        errors.append(f"missing active control {ACTIVE_CONTROL}")
    elif _n(ac.get("MSTATUS")) in ("44", "45"):
        errors.append(f"active control {ACTIVE_CONTROL} is NFO ({_n(ac.get('MSTATUS'))}) — pick another")
    else:
        p1 = next(
            (r for r in ridr
             if _canon(r.get("MPOLICY")) == _canon(ACTIVE_CONTROL) and _n(r.get("MPHASE")) == "1"),
            None,
        )
        if p1 and _ymd(p1.get("MPAYUP")) == _ymd(ac.get("MPAIDTO")) != "":
            errors.append(
                f"active control {ACTIVE_CONTROL}: MPAYUP equals MPAIDTO — "
                "Issue #76 override leaked onto a non-NFO policy"
            )

    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    with EVIDENCE.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()) if rows_out else ["MPOLICY"])
        w.writeheader()
        w.writerows(rows_out)

    if payup_bad or mlast_bad:
        errors.append(f"violations: payup={payup_bad} mlastann={mlast_bad}")

    print(f"validate_issue76_eti_rpu_payup v{SCRIPT_VERSION}")
    print(f"  valuation date: {val_date:%Y-%m-%d} ({val_src})")
    print(f"  candidates={cand} payup_fail={payup_bad} mlast_fail={mlast_bad}")
    for wmsg in warnings:
        print(f"WARN: {wmsg}")

    if errors:
        print("FAIL:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS")
    if args.publish_test_validation:
        TEST_VAL.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ridr_path, TEST_VAL / "quikridr.csv")
        print(f"Published: {TEST_VAL / 'quikridr.csv'}")
    if warnings:
        print("CLASS_A_WARN: no same-cut candidate-count baseline (exit 2)")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
