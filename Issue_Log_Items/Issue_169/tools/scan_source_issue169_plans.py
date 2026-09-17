"""Issue #169 discovery: does the newest (8/31) LifePRO rate extract carry any
TYPE_CODE='RV' (terminal reserve) rows for the plans Jill named?

    960 LP85-M  -> QL 196085  (base plan, LifePRO PLAN_ID "960")
    SAL ADB     -> QL 9SLADB  (ADB rider under SAL ML, LifePRO PLAN_ID "SLADB"/"SAL ADB")
    619 SPS PU  -> QL 7619PU  (base plan, LifePRO PLAN_ID "619")
    1595 (667 ART) -> QL 9595WP (WP rider, LifePRO PLAN_ID "1595"); base 667 ART -> QL 5667AT (PLAN_ID "667")
    1596 LO1    -> QL 901ADB (ADB rider under 1596/L01, LifePRO PLAN_ID "1596")

COVERAGE_ID is a fixed 11-char field: 4-5 digit sequence number + space + LifePRO
PLAN_ID. We split on whitespace and match the PLAN_ID token exactly (not prefix),
so "960MI" does not falsely match "960".

Read-only. Writes nothing but prints a report.
"""
from __future__ import annotations

import collections
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SRC = os.path.join(ROOT, "QLA_Migration", "Source")

FILES = {
    "PDAGE_20260831": (
        "PDAGE_AgeDuration_Rates_Extract_20260831.csv",
        {"cov": 0, "type": 1, "uw": 5, "dur": 6, "val1": 7},
    ),
    "PAAGE_20260831": (
        "PAAGE_AttainedAge_Rates_Extract_20260831.csv",
        {"cov": 0, "type": 1, "uw": 4, "dur": None, "val1": 7},
    ),
    "PAAGERAT_20260831": (
        "PAAGERAT_AttainedAge_Rates_Extract_20260831.csv",
        {"cov": 0, "type": 1, "uw": 4, "dur": None, "val1": 7},
    ),
}

# LifePRO PLAN_ID tokens of interest (exact match on the token AFTER the leading
# sequence number in COVERAGE_ID), plus the two-token form "SAL ADB".
PLAN_IDS = {"960", "619", "667", "1595", "1596"}
TWO_TOKEN_PLAN_IDS = {("SAL", "ADB")}


def plan_id_of(cov_field: str) -> tuple[str, ...]:
    toks = cov_field.split()
    return tuple(toks[1:]) if len(toks) > 1 else tuple(toks)


def scan(label: str, path: str, cols: dict) -> None:
    rows_by_key = collections.Counter()
    nonzero_by_key = collections.Counter()
    type_totals = collections.Counter()
    total = 0
    matched = 0
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        fh.readline()  # header
        fh.readline()  # dashes
        for line in fh:
            total += 1
            cov = line[: cols["val1"]].split(",", 1)[0]
            pid = plan_id_of(cov)
            hit = False
            if len(pid) == 1 and pid[0] in PLAN_IDS:
                hit = True
                pid_disp = pid[0]
            elif len(pid) >= 2 and (pid[0], pid[1]) in TWO_TOKEN_PLAN_IDS:
                hit = True
                pid_disp = "SAL ADB"
            elif len(pid) == 1 and pid[0].upper() in {"SALADB", "SLADB"}:
                hit = True
                pid_disp = pid[0]
            else:
                continue
            matched += 1
            parts = line.split(",")
            type_code = parts[cols["type"]].strip() if len(parts) > cols["type"] else "?"
            uw = parts[cols["uw"]].strip() if cols["uw"] is not None and len(parts) > cols["uw"] else "?"
            dur = (
                parts[cols["dur"]].strip()
                if cols["dur"] is not None and len(parts) > cols["dur"]
                else ""
            )
            key = (pid_disp, type_code, uw)
            rows_by_key[key] += 1
            type_totals[(pid_disp, type_code)] += 1
            try:
                v1 = float(parts[cols["val1"]].strip() or 0)
            except (ValueError, IndexError):
                v1 = 0.0
            if v1 != 0.0:
                nonzero_by_key[key] += 1

    print("=" * 78)
    print(f"{label}  ({total:,} total rows scanned, {matched} matched our plan IDs)")
    print("=" * 78)
    if not rows_by_key:
        print("  NO ROWS MATCHED any of:", sorted(PLAN_IDS), "or SAL ADB")
    else:
        print(f"{'PLAN_ID':<10}{'TYPE':<6}{'UWCLS':<7}{'ROWS':>7}{'NONZERO V1':>12}")
        for key in sorted(rows_by_key):
            print(
                f"{key[0]:<10}{key[1]:<6}{key[2]:<7}{rows_by_key[key]:>7}"
                f"{nonzero_by_key[key]:>12}"
            )
    print()
    print("  TYPE_CODE presence summary (plan_id, type_code) -> row count:")
    for key in sorted(type_totals):
        print(f"    {key} -> {type_totals[key]}")
    print()


def main() -> int:
    for label, (fn, cols) in FILES.items():
        path = os.path.join(SRC, fn)
        if not os.path.isfile(path):
            print(f"MISSING: {path}")
            continue
        scan(label, path, cols)
    return 0


if __name__ == "__main__":
    sys.exit(main())
