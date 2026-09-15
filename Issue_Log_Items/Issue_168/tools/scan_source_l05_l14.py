"""Scan the newest (8/31) LifePRO rate extracts for L05 / L14 rate data.

Issue #168 review: the earlier diagnosis used the April extracts
(plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv and
PAAGERAT_..._20260428.csv). New Era regenerated the rate extracts the night of
8/31, so this re-checks the question "does L05 have reserve data in source?"
against the 8/31 files.

Read-only. Writes nothing.
"""
from __future__ import annotations

import collections
import os
import sys

SRC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "QLA_Migration",
    "Source",
)

FILES = {
    "PDAGE_20260831": "PDAGE_AgeDuration_Rates_Extract_20260831.csv",
    "PAAGE_20260831": "PAAGE_AttainedAge_Rates_Extract_20260831.csv",
    "PAAGERAT_20260831": "PAAGERAT_AttainedAge_Rates_Extract_20260831.csv",
}

# COVERAGE_ID prefixes of interest (first field of every row)
PREFIXES = ("L0", "L1")

VALUE_COL = {"PDAGE_20260831": 7, "PAAGE_20260831": None, "PAAGERAT_20260831": 7}
UW_COL = {"PDAGE_20260831": 5, "PAAGE_20260831": 4, "PAAGERAT_20260831": 4}


def scan(label: str, path: str) -> None:
    rows = collections.Counter()
    nonzero = collections.Counter()
    uwcol = UW_COL[label]
    vcol = VALUE_COL[label]
    total = 0
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        fh.readline()  # header
        fh.readline()  # dashes
        for line in fh:
            if not line.startswith(PREFIXES):
                continue
            parts = line.split(",")
            if len(parts) <= uwcol:
                continue
            key = (parts[0].strip(), parts[1].strip(), parts[uwcol].strip())
            rows[key] += 1
            total += 1
            if vcol is not None and len(parts) > vcol:
                try:
                    if float(parts[vcol] or 0) != 0.0:
                        nonzero[key] += 1
                except ValueError:
                    pass

    print("=" * 62)
    print(f"{label}  ({total} L0*/L1* rows)")
    print("=" * 62)
    print(f"{'COVERAGE_ID':<14}{'TYPE':<6}{'UWCLS':<7}{'ROWS':>8}{'NONZERO':>9}")
    for key in sorted(rows):
        print(f"{key[0]:<14}{key[1]:<6}{key[2]:<7}{rows[key]:>8}{nonzero[key]:>9}")
    print()


def main() -> int:
    for label, fn in FILES.items():
        path = os.path.join(SRC, fn)
        if not os.path.isfile(path):
            print(f"MISSING: {path}")
            continue
        scan(label, path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
