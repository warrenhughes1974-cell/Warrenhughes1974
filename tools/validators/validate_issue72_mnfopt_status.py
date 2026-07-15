"""
Issue #72 — quikmstr MNFOPT validation for this batch.

Rules:
  1. MSTATUS 44 → MNFOPT 2; MSTATUS 45 → MNFOPT 3 (Robert)
  2. MNFOPT > 0 → phase-1 plan is life with CV (QuikPlCv key or VARDB ≠ 0)

Usage:
  python tools/validators/validate_issue72_mnfopt_status.py
  python tools/validators/validate_issue72_mnfopt_status.py --output-dir QLA_Migration/Output
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "QLA_Migration" / "Output"
BASELINE = PROJECT_ROOT / "Issue_Log_Items" / "Issue_72" / "evidence" / "issue72_risk_mnfopt_deltas.csv"
EVIDENCE = PROJECT_ROOT / "Issue_Log_Items" / "Issue_72" / "evidence" / "issue72_nfo_life_cv_validation.csv"

SCRIPT_VERSION = "1.1"
EXPECTED_ROW_COUNT = 5083
EXPECTED_FORCE_COUNT = 277

ROBERT_SAMPLE = "010407670C"
CONTROLS = {
    "010367131C": ("22", "2"),
    "010148272C": ("22", "2"),
    "010143726C": ("22", "2"),
    "011221309C": ("53", "1"),
    "010392763C": ("53", "3"),
}


def _n(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def _load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def _to_int(val: object) -> int:
    s = _n(val)
    if not s:
        return 0
    try:
        return int(float(s))
    except ValueError:
        return 0


def _is_life_with_cv(mplan: str, plans: dict[str, dict], cv_plans: set[str]) -> bool:
    pl = plans.get(mplan)
    if not pl:
        return False
    vardb = _n(pl.get("VARDB"))
    return mplan in cv_plans or vardb not in ("", "0")


def _validate_nfo_life_cv(output_dir: Path, mstr_rows: list[dict], errors: list[str]) -> tuple[int, int]:
    ridr_path = output_dir / "quikridr.csv"
    plan_path = output_dir / "quikplan.csv"
    plcv_path = output_dir / "rates" / "QuikPlCv.csv"
    for p in (ridr_path, plan_path, plcv_path):
        if not p.exists():
            errors.append(f"life-with-CV check: missing {p.name}")
            return 0, 0

    ridr = _load_csv(ridr_path)
    plans = {_n(r.get("PLAN")): r for r in _load_csv(plan_path) if _n(r.get("PLAN"))}
    cv_plans = {_n(r.get("PLAN")) for r in _load_csv(plcv_path) if _n(r.get("PLAN"))}
    phase1 = {
        _n(r.get("MPOLICY")): r
        for r in ridr
        if _n(r.get("MPHASE")) == "1"
    }

    checked = 0
    fails: list[dict] = []
    for r in mstr_rows:
        nfo = _to_int(r.get("MNFOPT"))
        if nfo <= 0:
            continue
        checked += 1
        pol = _n(r.get("MPOLICY"))
        p1 = phase1.get(pol)
        if not p1:
            fails.append({
                "MPOLICY": pol,
                "MNFOPT": str(nfo),
                "MPLAN": "",
                "RESULT": "FAIL",
                "REASON": "no phase-1 quikridr row",
            })
            continue
        mplan = _n(p1.get("MPLAN"))
        pl = plans.get(mplan, {})
        ok = _is_life_with_cv(mplan, plans, cv_plans)
        if not ok:
            fails.append({
                "MPOLICY": pol,
                "MNFOPT": str(nfo),
                "MPLAN": mplan,
                "RESULT": "FAIL",
                "REASON": (
                    f"not life-with-CV "
                    f"(PRODUCT={_n(pl.get('PRODUCT'))} VARDB={_n(pl.get('VARDB'))} "
                    f"QuikPlCv={mplan in cv_plans})"
                ),
            })

    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    with EVIDENCE.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["MPOLICY", "MNFOPT", "MPLAN", "RESULT", "REASON"],
        )
        w.writeheader()
        if fails:
            w.writerows(fails)
        else:
            w.writerow({
                "MPOLICY": "(fleet)",
                "MNFOPT": "",
                "MPLAN": "",
                "RESULT": "PASS",
                "REASON": f"all {checked} MNFOPT>0 policies have life-with-CV phase-1 plan",
            })

    if fails:
        for row in fails[:5]:
            errors.append(
                f"NFO>0 not life-with-CV: {row['MPOLICY']} plan={row['MPLAN']} {row['REASON']}"
            )
        if len(fails) > 5:
            errors.append(f"NFO>0 life-with-CV failures: {len(fails)} total (see {EVIDENCE.name})")

    return checked, len(fails)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args()
    mstr_path = args.output_dir / "quikmstr.csv"
    if not mstr_path.exists():
        print(f"FAIL: missing {mstr_path}")
        return 1

    rows = _load_csv(mstr_path)
    errors: list[str] = []

    if len(rows) != EXPECTED_ROW_COUNT:
        errors.append(f"row count {len(rows)} != expected {EXPECTED_ROW_COUNT}")

    bad44 = bad45 = 0
    for r in rows:
        st, nfo, pol = _n(r.get("MSTATUS")), _n(r.get("MNFOPT")), _n(r.get("MPOLICY"))
        if st == "44" and nfo != "2":
            bad44 += 1
            if bad44 <= 3:
                errors.append(f"status 44 MNFOPT!=2: {pol} got {nfo}")
        if st == "45" and nfo != "3":
            bad45 += 1
            if bad45 <= 3:
                errors.append(f"status 45 MNFOPT!=3: {pol} got {nfo}")

    if bad44 or bad45:
        errors.append(f"violations: status44={bad44} status45={bad45}")

    sample = next((r for r in rows if _n(r.get("MPOLICY")) == ROBERT_SAMPLE), None)
    if not sample:
        errors.append(f"missing sample {ROBERT_SAMPLE}")
    elif _n(sample.get("MSTATUS")) != "45" or _n(sample.get("MNFOPT")) != "3":
        errors.append(
            f"{ROBERT_SAMPLE}: expected 45/3 got {_n(sample.get('MSTATUS'))}/{_n(sample.get('MNFOPT'))}"
        )

    for pol, (exp_st, exp_nfo) in CONTROLS.items():
        r = next((x for x in rows if _n(x.get("MPOLICY")) == pol), None)
        if not r:
            errors.append(f"missing control {pol}")
            continue
        if _n(r.get("MSTATUS")) != exp_st or _n(r.get("MNFOPT")) != exp_nfo:
            errors.append(
                f"control {pol}: expected {exp_st}/{exp_nfo} got "
                f"{_n(r.get('MSTATUS'))}/{_n(r.get('MNFOPT'))}"
            )

    # Optional delta count vs risk baseline
    if BASELINE.exists():
        with BASELINE.open(newline="", encoding="utf-8") as f:
            baseline_n = sum(1 for _ in csv.DictReader(f))
        forced = 0
        with BASELINE.open(newline="", encoding="utf-8") as f:
            for b in csv.DictReader(f):
                pol = _n(b.get("MPOLICY"))
                r = next((x for x in rows if _n(x.get("MPOLICY")) == pol), None)
                if r and _n(r.get("MNFOPT")) == _n(b.get("MNFOPT_AFTER")):
                    forced += 1
        if forced != baseline_n:
            errors.append(f"baseline delta match {forced}/{baseline_n}")

    nfo_cv_checked, nfo_cv_fails = _validate_nfo_life_cv(args.output_dir, rows, errors)

    print(f"validate_issue72_mnfopt_status v{SCRIPT_VERSION}")
    print(f"  rows={len(rows)} bad44={bad44} bad45={bad45}")
    print(f"  NFO>0 life-with-CV: checked={nfo_cv_checked} fail={nfo_cv_fails}")
    if sample:
        print(f"  {ROBERT_SAMPLE}: MSTATUS={_n(sample.get('MSTATUS'))} MNFOPT={_n(sample.get('MNFOPT'))}")

    if errors:
        print("FAIL:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
