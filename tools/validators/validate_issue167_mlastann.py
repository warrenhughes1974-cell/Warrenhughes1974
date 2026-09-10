"""
Issue #167 — quikridr.MLASTANN anniversary-accurate vs QLA_VALUATION_DATE.

Rules:
  1. Non-ETI/RPU rows: MLASTANN = completed years from MEFFDATE to valuation date
     (year minus year, minus 1 if anniversary month/day has not occurred).
  2. ETI/RPU phase 1 (quikmstr.MSTATUS 44/45): keep Issue #76/#108B paid-to math.
  3. Gold 9010397528C must be 54 on an 8/31/2026 valuation.

Usage:
  python tools/validators/validate_issue167_mlastann.py
  python tools/validators/validate_issue167_mlastann.py --valuation-date 20260831
  python tools/validators/validate_issue167_mlastann.py --publish-test-validation
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
SCRIPT_VERSION = "1.0"

GOLD = "9010397528C"
CONTROL_JULY = "9010367704C"
CONTROL_APRIL = "9010412641C"
ETI_TRACE = "9010149295C"
ETI_TRACE2 = "9010374099C"


def _n(v: object) -> str:
    return ("" if v is None else str(v)).strip()


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


def _ann_mlastann(issue_ymd: str, val: date) -> str:
    issue = _as_date(issue_ymd)
    if not issue or issue > val:
        return ""
    dur = val.year - issue.year - ((val.month, val.day) < (issue.month, issue.day))
    return str(dur) if dur >= 0 else ""


def _nfo_mlastann(paidto: str, val: date) -> str:
    nfo = _as_date(paidto)
    if not nfo:
        return ""
    dur = val.year - nfo.year - ((val.month, val.day) < (nfo.month, nfo.day))
    return str(dur if dur >= 0 else 0)


def _resolve_valuation_date(explicit: str | None) -> tuple[date, str]:
    try:
        from qla_core.valuation_date import resolve_valuation_date_yyyymmdd

        ymd, src = resolve_valuation_date_yyyymmdd(
            source_dir=PROJECT_ROOT / "QLA_Migration" / "Source",
            explicit=explicit,
        )
        d = _as_date(ymd)
        if d:
            return d, src
    except Exception:
        pass
    raw = explicit or os.environ.get("QLA_VALUATION_DATE", "").strip()
    if raw:
        digits = "".join(c for c in raw if c.isdigit())
        d = _as_date(digits)
        if d:
            return d, f"QLA_VALUATION_DATE={digits}"
    return datetime.now().date(), "system date"


def _load(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--valuation-date", default=None)
    ap.add_argument("--publish-test-validation", action="store_true")
    args = ap.parse_args()

    ridr_path = args.output_dir / "quikridr.csv"
    mstr_path = args.output_dir / "quikmstr.csv"
    for p in (ridr_path, mstr_path):
        if not p.exists():
            print(f"FAIL: missing {p}")
            return 1

    ridr = _load(ridr_path)
    mstr = {_n(r.get("MPOLICY")): r for r in _load(mstr_path)}
    val, val_src = _resolve_valuation_date(args.valuation_date)
    errors: list[str] = []

    nfo_ok = 0
    ann_bad = 0
    ann_ok = 0
    for r in ridr:
        pol = _n(r.get("MPOLICY"))
        phase = _n(r.get("MPHASE"))
        got = _n(r.get("MLASTANN"))
        m = mstr.get(pol) or {}
        st = _n(m.get("MSTATUS"))
        if phase == "1" and st in ("44", "45"):
            # Issue #76 overlay owns these values. This cut already has known
            # paid-to anniversary drift (#76 mlast_fail); #167 must not rewrite them.
            nfo_ok += 1
            continue
        exp = _ann_mlastann(_ymd(r.get("MEFFDATE")), val)
        ann_ok += 1
        if got != exp:
            ann_bad += 1
            if ann_bad <= 5:
                errors.append(
                    f"{pol} ph{phase} MLASTANN={got} expected {exp} (meff={_ymd(r.get('MEFFDATE'))})"
                )

    traces = [
        (GOLD, "1", _ann_mlastann("19710901", val)),
        (GOLD, "2", _ann_mlastann("19710901", val)),
        (CONTROL_JULY, "1", _ann_mlastann("19700701", val)),
        (CONTROL_APRIL, "1", _ann_mlastann("19720401", val)),
    ]
    print(f"validate_issue167_mlastann v{SCRIPT_VERSION}")
    print(f"  valuation: {val:%Y%m%d} ({val_src})")
    print(f"  rows={len(ridr)} anniversary_checked={ann_ok} nfo_phase1={nfo_ok}")
    print("  traces:")
    for pol, phase, exp in traces:
        hits = [r for r in ridr if _n(r.get("MPOLICY")) == pol and _n(r.get("MPHASE")) == phase]
        if not hits:
            errors.append(f"missing trace {pol} phase {phase}")
            print(f"    {pol} ph{phase}: MISSING")
            continue
        got = _n(hits[0].get("MLASTANN"))
        ok = "PASS" if got == exp else "FAIL"
        print(f"    {pol} ph{phase} MLASTANN={got} expected {exp} {ok}")
        if got != exp:
            errors.append(f"trace {pol} ph{phase} MLASTANN={got} expected {exp}")

    for pol in (ETI_TRACE, ETI_TRACE2):
        hits = [r for r in ridr if _n(r.get("MPOLICY")) == pol and _n(r.get("MPHASE")) == "1"]
        m = mstr.get(pol) or {}
        if not hits:
            errors.append(f"missing ETI trace {pol}")
            continue
        exp = _nfo_mlastann(_ymd(m.get("MPAIDTO")), val)
        got = _n(hits[0].get("MLASTANN"))
        ok = "PASS" if got == exp else "FAIL"
        print(f"    {pol} ph1 NFO MLASTANN={got} expected {exp} {ok}")
        if got != exp:
            errors.append(f"ETI trace {pol} MLASTANN={got} expected {exp}")

    if val == date(2026, 8, 31):
        gold = next(
            (r for r in ridr if _n(r.get("MPOLICY")) == GOLD and _n(r.get("MPHASE")) == "1"),
            None,
        )
        if gold and _n(gold.get("MLASTANN")) != "54":
            errors.append(f"{GOLD} phase1 must be 54 on 20260831, got {_n(gold.get('MLASTANN'))}")

    if ann_bad:
        errors.append(f"anniversary mismatches={ann_bad}")
    if ann_ok < 1:
        errors.append("no anniversary-checked rows")
    if nfo_ok < 1:
        errors.append("no ETI/RPU phase-1 rows found to leave on #76 overlay")

    if errors:
        print("FAIL:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS")
    if args.publish_test_validation:
        tv = args.output_dir / "Test_Validation"
        tv.mkdir(parents=True, exist_ok=True)
        dest = tv / "quikridr.csv"
        shutil.copy2(ridr_path, dest)
        with (tv / "manifest.txt").open("a", encoding="utf-8") as f:
            f.write(
                f"{datetime.now().isoformat(timespec='seconds')} Issue_167 "
                f"published quikridr.csv ({len(ridr)} rows)\n"
            )
        print(f"Published {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
