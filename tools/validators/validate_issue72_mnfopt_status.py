"""
Issue #72 — quikmstr MNFOPT vs ETI/RPU status.

Robert 2026-07-25 reversed the original rule. MNFOPT must carry the **source** election from
PPBENTYP; the converter must no longer force it from MSTATUS. Any disagreement between the
election and the policy status is reported for source review instead of being overwritten.

Rules:
  1. MNFOPT is NOT forced. Every NFO policy whose election disagrees with its status must
     appear in Reports/nfo_election_status_mismatch.csv, and the report must agree exactly
     with what was emitted (no silently forced rows, no phantom rows).
  2. MNFOPT domain is 0-3.
  3. MNFOPT > 0 -> phase-1 plan is life with CV (QuikPlCv key or VARDB != 0).
  4. Client trace policies carry their specified source election.

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
DEFAULT_REPORTS = PROJECT_ROOT / "QLA_Migration" / "Reports"
MISMATCH_REPORT = "nfo_election_status_mismatch.csv"
EVIDENCE = PROJECT_ROOT / "Issue_Log_Items" / "Issue_72" / "evidence" / "issue72_nfo_life_cv_validation.csv"

SCRIPT_VERSION = "2.0"
EXPECTED_ROW_COUNT = 5083

# Client trace policies (recorded in the pre-Issue-#2 10-char form; matched via _canon).
# Expected values are the SOURCE election, not a status-derived one.
CONTROLS = {
    "010367131C": ("22", "2"),
    "010148272C": ("22", "2"),
    "010143726C": ("22", "2"),
    "011221309C": ("53", "1"),
    "010392763C": ("53", "3"),
}


def _n(v: object) -> str:
    return ("" if v is None else str(v)).strip()


def _canon(v: object) -> str:
    """Policy identity that matches across the Issue #2 key change (see #108F)."""
    s = _n(v).upper()
    if s.endswith("C"):
        s = s[:-1]
    if s.startswith("9"):
        s = s[1:]
    return s


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
    return mplan in cv_plans or _n(pl.get("VARDB")) not in ("", "0")


def _validate_nfo_life_cv(output_dir: Path, mstr_rows: list[dict], errors: list[str]) -> tuple[int, int]:
    ridr_path = output_dir / "quikridr.csv"
    plan_path = output_dir / "quikplan.csv"
    plcv_path = output_dir / "rates" / "QuikPlCv.csv"
    for p in (ridr_path, plan_path, plcv_path):
        if not p.exists():
            errors.append(f"life-with-CV check: missing {p.name}")
            return 0, 0

    plans = {_n(r.get("PLAN")): r for r in _load_csv(plan_path) if _n(r.get("PLAN"))}
    cv_plans = {_n(r.get("PLAN")) for r in _load_csv(plcv_path) if _n(r.get("PLAN"))}
    phase1 = {
        _canon(r.get("MPOLICY")): r
        for r in _load_csv(ridr_path)
        if _n(r.get("MPHASE")) == "1"
    }

    checked = 0
    fails: list[dict] = []
    for r in mstr_rows:
        if _to_int(r.get("MNFOPT")) <= 0:
            continue
        checked += 1
        pol = _n(r.get("MPOLICY"))
        p1 = phase1.get(_canon(pol))
        if not p1:
            fails.append({"MPOLICY": pol, "MNFOPT": _n(r.get("MNFOPT")), "MPLAN": "",
                          "RESULT": "FAIL", "REASON": "no phase-1 quikridr row"})
            continue
        mplan = _n(p1.get("MPLAN"))
        if not _is_life_with_cv(mplan, plans, cv_plans):
            pl = plans.get(mplan, {})
            fails.append({
                "MPOLICY": pol, "MNFOPT": _n(r.get("MNFOPT")), "MPLAN": mplan,
                "RESULT": "FAIL",
                "REASON": (f"not life-with-CV (PRODUCT={_n(pl.get('PRODUCT'))} "
                           f"VARDB={_n(pl.get('VARDB'))} QuikPlCv={mplan in cv_plans})"),
            })

    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    with EVIDENCE.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["MPOLICY", "MNFOPT", "MPLAN", "RESULT", "REASON"])
        w.writeheader()
        w.writerows(fails or [{
            "MPOLICY": "(fleet)", "MNFOPT": "", "MPLAN": "", "RESULT": "PASS",
            "REASON": f"all {checked} MNFOPT>0 policies have life-with-CV phase-1 plan",
        }])

    for row in fails[:5]:
        errors.append(f"NFO>0 not life-with-CV: {row['MPOLICY']} plan={row['MPLAN']} {row['REASON']}")
    if len(fails) > 5:
        errors.append(f"NFO>0 life-with-CV failures: {len(fails)} total (see {EVIDENCE.name})")

    return checked, len(fails)


def _validate_no_force(rows: list[dict], reports_dir: Path, errors: list[str]) -> tuple[int, int]:
    """The emitted mismatches and the exception report must agree exactly."""
    expected_by_status = {"44": "2", "45": "3"}
    emitted: dict[str, tuple[str, str]] = {}
    for r in rows:
        st = _n(r.get("MSTATUS"))
        want = expected_by_status.get(st)
        if want is None:
            continue
        got = _n(r.get("MNFOPT"))
        if got != want:
            emitted[_canon(r.get("MPOLICY"))] = (st, got)

    report_path = reports_dir / MISMATCH_REPORT
    if not report_path.exists():
        errors.append(
            f"missing {MISMATCH_REPORT} — the Issue #72 downgrade requires the exception "
            "report to be written every batch (header even when empty)"
        )
        return len(emitted), 0

    reported = {_canon(r.get("MPOLICY")): r for r in _load_csv(report_path)}

    missing = set(emitted) - set(reported)
    phantom = set(reported) - set(emitted)
    if missing:
        errors.append(
            f"{len(missing)} policies disagree with their status but are absent from "
            f"{MISMATCH_REPORT} (e.g. {sorted(missing)[0]})"
        )
    if phantom:
        errors.append(
            f"{len(phantom)} policies in {MISMATCH_REPORT} do not disagree in the output "
            f"(e.g. {sorted(phantom)[0]}) — report is stale"
        )

    for pol, row in reported.items():
        if pol not in emitted:
            continue
        st, got = emitted[pol]
        if _n(row.get("MSTATUS")) != st or _n(row.get("MNFOPT_EMITTED")) != got:
            errors.append(
                f"{_n(row.get('MPOLICY'))}: report says {_n(row.get('MSTATUS'))}/"
                f"{_n(row.get('MNFOPT_EMITTED'))}, output has {st}/{got}"
            )
            break

    return len(emitted), len(reported)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS)
    args = ap.parse_args()
    mstr_path = args.output_dir / "quikmstr.csv"
    if not mstr_path.exists():
        print(f"FAIL: missing {mstr_path}")
        return 1

    rows = _load_csv(mstr_path)
    errors: list[str] = []

    if len(rows) != EXPECTED_ROW_COUNT:
        errors.append(f"row count {len(rows)} != expected {EXPECTED_ROW_COUNT}")

    bad_domain = [r for r in rows if _n(r.get("MNFOPT")) not in ("", "0", "1", "2", "3")]
    if bad_domain:
        errors.append(
            f"MNFOPT outside 0-3 on {len(bad_domain)} policies "
            f"(e.g. {_n(bad_domain[0].get('MPOLICY'))}={_n(bad_domain[0].get('MNFOPT'))})"
        )

    mismatches, reported = _validate_no_force(rows, args.reports_dir, errors)

    by_pol = {_canon(r.get("MPOLICY")): r for r in rows}
    for pol, (exp_st, exp_nfo) in CONTROLS.items():
        r = by_pol.get(_canon(pol))
        if not r:
            errors.append(f"missing control {pol}")
            continue
        if _n(r.get("MSTATUS")) != exp_st or _n(r.get("MNFOPT")) != exp_nfo:
            errors.append(
                f"control {pol}: expected {exp_st}/{exp_nfo} got "
                f"{_n(r.get('MSTATUS'))}/{_n(r.get('MNFOPT'))}"
            )

    nfo_cv_checked, nfo_cv_fails = _validate_nfo_life_cv(args.output_dir, rows, errors)

    print(f"validate_issue72_mnfopt_status v{SCRIPT_VERSION} (report-only; force removed v58.33)")
    print(f"  rows={len(rows)}")
    print(f"  election/status disagreements: emitted={mismatches} reported={reported}")
    print(f"  NFO>0 life-with-CV: checked={nfo_cv_checked} fail={nfo_cv_fails}")

    if errors:
        print("FAIL:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
