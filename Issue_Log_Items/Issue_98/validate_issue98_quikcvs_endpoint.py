"""Issue #98 — CV endpoint / duration placement validator.

Validates Eric's `010398471C` / `17085M` M issue-age 14 anchors against the
full generated `QLA_Migration/Output/rates/QuikCvs.csv` package.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QUIKCVS = ROOT / "QLA_Migration" / "Output" / "rates" / "QuikCvs.csv"
EVIDENCE = ROOT / "Issue_Log_Items" / "Issue_98" / "evidence" / "issue98_quikcvs_endpoint_validation.csv"

PLAN = "17085M"
GENDER = "M"
ISSUE_AGE = 14

ANCHORS = (
    ("first_0.06", 3, "0.06"),
    ("neighbor_lo", 54, "674.69"),
    ("neighbor_hi", 55, "688.11"),
    ("year85", 85, "975.61"),
    ("year86_terminal", 86, "1000.00"),
)


def _norm_num(value: str) -> str:
    s = (value or "").strip()
    if not s:
        return ""
    try:
        return f"{float(s):.2f}"
    except ValueError:
        return s


def _load_grid() -> dict[int, str]:
    grid: dict[int, str] = {}
    with QUIKCVS.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("PLAN") or "").strip() != PLAN:
                continue
            if (row.get("GENDER") or "").strip() != GENDER:
                continue
            try:
                age = int((row.get("AGE") or "").strip())
                cntl = int((row.get("CNTL") or "").strip())
            except ValueError:
                continue
            if age != ISSUE_AGE:
                continue
            for col in range(10):
                dur = cntl * 10 + col
                grid[dur] = (row.get(f"CV{col}") or "").strip()
    return grid


def main() -> int:
    grid = _load_grid()
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    failures = []
    with EVIDENCE.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["check", "plan", "gender", "issue_age", "duration", "expected", "actual", "result"],
        )
        w.writeheader()
        for check, duration, expected in ANCHORS:
            actual = grid.get(duration, "")
            ok = _norm_num(actual) == _norm_num(expected)
            if not ok:
                failures.append(f"{check}: duration {duration} expected {expected} got {actual or '(blank)'}")
            w.writerow({
                "check": check,
                "plan": PLAN,
                "gender": GENDER,
                "issue_age": ISSUE_AGE,
                "duration": duration,
                "expected": expected,
                "actual": actual,
                "result": "PASS" if ok else "FAIL",
            })

    if failures:
        print("FAIL - Issue #98 QuikCvs endpoint")
        for failure in failures:
            print(f"  {failure}")
        print(f"Evidence: {EVIDENCE.relative_to(ROOT)}")
        return 1
    print("PASS - Issue #98 QuikCvs endpoint")
    print(f"Evidence: {EVIDENCE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
