"""Fail-closed check that CEN/ISWL net premiums stay at the issue-year rate.

QLAdmin adds the stored net premium between anniversary cash values. Later
10-year pages must use LifePRO duration 1, not the climbed rate at the start
of that page. Warren 2026-09-22.

Anchors:
  1658C1 age 37 M PR — every page is 4.00 (the closed year-1 rate).
  1659CR age 51 F ST — every page is 18.00, including year 36 (CNTL 03).

Exit 1 when a later page still carries the climbed rate (49, 640, 813, ...).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NPS = ROOT / "QLA_Migration" / "Output" / "rates" / "QuikNps.csv"

ANCHORS = (
    {
        "plan": "1658C1",
        "age": "37",
        "gender": "M",
        "uwclass": "PR",
        "effdate": "19000101",
        "rate": 4.0,
        "pages": ("00", "01", "03"),
    },
    {
        "plan": "1659CR",
        "age": "51",
        "gender": "F",
        "uwclass": "ST",
        "effdate": "19000101",
        "rate": 18.0,
        "pages": ("00", "03", "04"),
    },
)


def _matches(row, anchor):
    return (
        (row.get("PLAN") or "").strip() == anchor["plan"]
        and (row.get("AGE") or "").strip() == anchor["age"]
        and (row.get("GENDER") or "").strip() == anchor["gender"]
        and (row.get("UWCLASS") or "").strip() == anchor["uwclass"]
        and (row.get("EFFDATE") or "").strip() == anchor["effdate"]
    )


def main() -> int:
    if not NPS.is_file():
        print(f"FAIL: missing {NPS}")
        return 1
    with NPS.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))

    failures = []
    for anchor in ANCHORS:
        found = {}
        for row in rows:
            if not _matches(row, anchor):
                continue
            cntl = (row.get("CNTL") or "").strip()
            found[cntl] = row
        for page in anchor["pages"]:
            row = found.get(page)
            if row is None:
                failures.append(
                    f"{anchor['plan']} age {anchor['age']} {anchor['gender']}/"
                    f"{anchor['uwclass']} missing CNTL {page}"
                )
                continue
            for col in range(10):
                raw = (row.get(f"NP{col}") or "").strip()
                try:
                    value = float(raw) if raw else None
                except ValueError:
                    value = None
                if value is None or abs(value - anchor["rate"]) > 0.001:
                    failures.append(
                        f"{anchor['plan']} CNTL {page} NP{col}={raw or '(blank)'} "
                        f"expected {anchor['rate']:.2f}"
                    )
                    break

    if failures:
        print("FAIL: CEN net premium left the issue-year rate")
        for line in failures:
            print(f"  {line}")
        return 1
    print(
        "PASS: 1658C1 age 37 M/PR is 4.00 on later pages and "
        "1659CR age 51 F/ST is 18.00 through year 36"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
