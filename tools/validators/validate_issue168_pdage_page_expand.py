"""Fail-closed check that L05 net premium year 32 is loaded from the PDAGE page.

LifePRO duration 32 for L05 10Y, issue age 28, female, class S is 15.59
(page 4, VALUE2). QuikNps stores net premium one year earlier than the
LifePRO year, so year 32 is CNTL 03, NP1. The old load parked each page's
first value on the page number, which put 15.59 on CNTL 00 NP3.

Usage:
  python tools/validators/validate_issue168_pdage_page_expand.py

Exit 1 when the expanded cell or the matching terminal-reserve row is missing.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RATES = ROOT / "QLA_Migration" / "Output" / "rates"

PLAN = "5L0510"
AGE = "28"
GENDER = "F"
UWCLASS = "ST"
EFFDATE = "19000101"


def _rows(name):
    path = RATES / name
    if not path.is_file():
        print(f"FAIL: missing {path}")
        return None
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return [
            row for row in csv.DictReader(fh)
            if (row.get("PLAN") or "").strip() == PLAN
            and (row.get("AGE") or "").strip() == AGE
            and (row.get("GENDER") or "").strip() == GENDER
            and (row.get("UWCLASS") or "").strip() == UWCLASS
            and (row.get("EFFDATE") or "").strip() == EFFDATE
        ]


def _cell(rows, cntl, field):
    for row in rows:
        if (row.get("CNTL") or "").strip() == cntl:
            return (row.get(field) or "").strip()
    return None


def main() -> int:
    failures = []
    nps = _rows("QuikNps.csv")
    tvs = _rows("QuikTvs.csv")
    if nps is None or tvs is None:
        return 1
    checks = (
        ("00", "NP0", "1.38", "year 1"),
        ("00", "NP1", "1.44", "year 2"),
        ("03", "NP1", "15.59", "year 32"),
    )
    for cntl, field, expected, label in checks:
        got = _cell(nps, cntl, field)
        if got != expected:
            failures.append(
                f"QuikNps {PLAN} age {AGE} {GENDER}/{UWCLASS} CNTL {cntl} {field} "
                f"is {got!r}, expected {expected} ({label})"
            )
    collapsed = _cell(nps, "00", "NP1")
    if collapsed == "3.87":
        failures.append(
            "QuikNps still has the collapsed page load (CNTL 00 NP1 is 3.87, page 2's first value)"
        )
    if not tvs:
        failures.append(
            f"QuikTvs has no {PLAN} age {AGE} {GENDER}/{UWCLASS} {EFFDATE} row, "
            "so Admin will ignore the net premium"
        )
    if failures:
        print("FAIL")
        for item in failures:
            print(f"  {item}")
        return 1
    print(
        f"PASS: {PLAN} age {AGE} {GENDER}/{UWCLASS} year 32 is 15.59 "
        f"and a QuikTvs row exists ({len(tvs)} row(s))"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
