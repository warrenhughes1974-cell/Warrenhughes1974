"""Issue L14 — QuikCvs duration placement for plan 1L14SC.

REVISED 2026-08-13 (Warren-approved closed-row override): the identity freeze
(extract label = QL Dur) was replaced by PDAGE native-year truth. Gold is now
the LifePRO PDAGE native grid, confirmed by Eric's screenshots in
'Rates of Identified Issues - 8.13.26.xlsx':
  F/69: native first year 2 -> unchanged: Dur2=14.73, Dur3=52.91, Dur31=1000
  F/45: native first year 3 -> Dur3=8.37, terminal 1000 at Dur55
  M/54: native first year 3 -> Dur3=20.94, 538.30 at Dur24, terminal 1000 at
        Dur46 (Eric screen: LifePRO shows 538.30 at Dur 024, 1000 at 046)

Fails if F/69 slips (+/-1) or if F/45 / M/54 revert to the old identity
placement (first value one year early, terminal short of attained age 100).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUIKCVS = ROOT / "QLA_Migration" / "Output" / "rates" / "QuikCvs.csv"
EVIDENCE = (
    ROOT / "Issue_Log_Items" / "Issue_L14" / "evidence" / "issue_l14_quikcvs_duration_validation.csv"
)

PLAN = "1L14SC"
# Issue #118 retired NS from the underwriting domain; these L14 CV rows are NT.
UWCLASS = "NT"

ANCHORS = (
    ("F69_dur2", "F", 69, 2, "14.73"),
    ("F69_dur3", "F", 69, 3, "52.91"),
    ("F69_dur31_terminal", "F", 69, 31, "1000.00"),
    ("F45_dur3", "F", 45, 3, "8.37"),
    ("F45_dur55_terminal", "F", 45, 55, "1000.00"),
    ("M54_dur3", "M", 54, 3, "20.94"),
    ("M54_dur24", "M", 54, 24, "538.30"),
    ("M54_dur46_terminal", "M", 54, 46, "1000.00"),
)


def _norm_num(value: str) -> str:
    s = (value or "").strip()
    if not s:
        return ""
    try:
        return f"{float(s):.2f}"
    except ValueError:
        return s


def _age_match(raw: str, age: int) -> bool:
    s = (raw or "").strip()
    if not s:
        return False
    try:
        return int(s) == age
    except ValueError:
        return s.lstrip("0") == str(age) or s == str(age)


def _load_grid(gender: str, age: int) -> dict[int, str]:
    grid: dict[int, str] = {}
    with QUIKCVS.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("PLAN") or "").strip() != PLAN:
                continue
            if (row.get("GENDER") or "").strip() != gender:
                continue
            if (row.get("UWCLASS") or "").strip() != UWCLASS:
                continue
            if not _age_match(row.get("AGE") or "", age):
                continue
            try:
                cntl = int((row.get("CNTL") or "").strip() or "0")
            except ValueError:
                continue
            for col in range(10):
                dur = cntl * 10 + col
                grid[dur] = (row.get(f"CV{col}") or "").strip()
    return grid


def main() -> int:
    if not QUIKCVS.is_file():
        print(f"FAIL: missing {QUIKCVS}")
        return 1

    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    with EVIDENCE.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "check",
                "plan",
                "gender",
                "issue_age",
                "duration",
                "expected",
                "actual",
                "result",
            ],
        )
        w.writeheader()
        cache: dict[tuple[str, int], dict[int, str]] = {}
        for check, gender, age, duration, expected in ANCHORS:
            key = (gender, age)
            if key not in cache:
                cache[key] = _load_grid(gender, age)
            grid = cache[key]
            actual = grid.get(duration, "")
            ok = _norm_num(actual) == _norm_num(expected)
            if not ok:
                failures.append(
                    f"{check}: duration {duration} expected {expected} got {actual or '(blank)'}"
                )
            # Explicit anti-regression: F69 must NOT still have 14.73 at Dur3 as the "first" nonzero
            if check == "F69_dur2" and _norm_num(grid.get(3, "")) == "14.73" and not ok:
                failures.append("F69 still late-shifted (14.73 at Dur3)")
            w.writerow(
                {
                    "check": check,
                    "plan": PLAN,
                    "gender": gender,
                    "issue_age": age,
                    "duration": duration,
                    "expected": expected,
                    "actual": actual,
                    "result": "PASS" if ok else "FAIL",
                }
            )

    if failures:
        print("FAIL: Issue L14 QuikCvs duration")
        for line in failures:
            print(" ", line)
        return 1

    print(
        "PASS: Issue L14 QuikCvs duration (PDAGE native, rev 2026-08-13) — "
        "1L14SC F/69 Dur2=14.73 Dur31=1000; F/45 Dur3=8.37 Dur55=1000; "
        "M/54 Dur3=20.94 Dur24=538.30 Dur46=1000"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
