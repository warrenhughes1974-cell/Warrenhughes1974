"""Issue 181 — 658/659 QuikTvs is one year earlier than the LifePRO year.

Fail-closed. With Store Means on, QLAdmin reads the prior year. These six
plans must keep the shifted grid or the reserve matches t-1 again.

The pre-shift rows live in
Issue_Log_Items/Issue_181/evidence/quiktvs_six_plans_before_shift.csv.
Every current cell must equal that file moved one year earlier, with the
final populated year repeated.
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TVS = ROOT / "QLA_Migration" / "Output" / "rates" / "QuikTvs.csv"
PLTV = ROOT / "QLA_Migration" / "Output" / "rates" / "QuikPlTv.csv"
BEFORE = (
    ROOT
    / "Issue_Log_Items"
    / "Issue_181"
    / "evidence"
    / "quiktvs_six_plans_before_shift.csv"
)

PLANS = ("1659C2", "1658C1", "1659CR", "1658CS", "1659CS", "1659SR")
EXPECTED_ROWS = 7644
EXPECTED_GRIDS = 1196

# Post-shift anchors. Year = CNTL * 10 + slot.
ANCHORS = (
    ("1659C2", "M", "PR", "44", {0: "2.00", 1: "17.00", 42: "764.00", 43: "776.00", 56: "978.00"}),
    ("1659C2", "M", "ST", "17", {0: "1.00", 1: "5.00", 82: "978.00", 83: "978.00"}),
    ("1658C1", "M", "PR", "24", {42: "205.00", 43: "211.00"}),
    ("1659CR", "F", "ST", "55", {41: "895.00", 42: "917.00"}),
    ("1658CS", "F", "ST", "38", {39: "332.00", 40: "342.00"}),
    ("1659CS", "M", "ST", "14", {39: "338.00", 40: "352.00"}),
    ("1659SR", "F", "ST", "51", {37: "763.99", 38: "779.75"}),
)


def _s(value: object) -> str:
    return str(value or "").strip()


def _load(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        return fields, list(reader)


def _grids(rows: list[dict[str, str]]) -> dict[tuple, dict[int, str]]:
    grouped: dict[tuple, dict[int, str]] = defaultdict(dict)
    for row in rows:
        if _s(row.get("PLAN")) not in PLANS:
            continue
        key = (
            _s(row.get("PLAN")),
            _s(row.get("GENDER")),
            _s(row.get("UWCLASS")),
            _s(row.get("AGE")),
            _s(row.get("BAND")),
            _s(row.get("ISSCNTRY")),
            _s(row.get("ISSUEST")),
            _s(row.get("EFFDATE")),
        )
        control = int(_s(row.get("CNTL")) or "0")
        for slot in range(10):
            value = _s(row.get(f"TV{slot}"))
            if value:
                grouped[key][control * 10 + slot] = value
    return grouped


def _shift(slots: dict[int, str]) -> dict[int, str]:
    last = max(slots)
    moved = {year: slots[year + 1] for year in range(last)}
    moved[last] = slots[last]
    return moved


def main() -> int:
    errors: list[str] = []
    if not TVS.is_file():
        print(f"FAIL: missing {TVS}")
        return 1
    if not BEFORE.is_file():
        print(f"FAIL: missing pre-shift baseline {BEFORE}")
        return 1

    _fields, current_rows = _load(TVS)
    _before_fields, before_rows = _load(BEFORE)
    current = _grids(current_rows)
    before = _grids(before_rows)
    scope_rows = sum(1 for row in current_rows if _s(row.get("PLAN")) in PLANS)
    if scope_rows != EXPECTED_ROWS:
        errors.append(f"in-scope rows {scope_rows}, expected {EXPECTED_ROWS}")
    if len(current) != EXPECTED_GRIDS:
        errors.append(f"grids {len(current)}, expected {EXPECTED_GRIDS}")
    if set(current) != set(before):
        errors.append(
            f"grid keys differ from the pre-shift file "
            f"(only current {len(set(current) - set(before))}, "
            f"only baseline {len(set(before) - set(current))})"
        )

    mismatches = 0
    for key, slots in before.items():
        expected = _shift(slots)
        got = current.get(key)
        if got != expected:
            mismatches += 1
            if mismatches <= 5:
                errors.append(f"grid {key} is not one year earlier")
    if mismatches > 5:
        errors.append(f"{mismatches} grids are not one year earlier")

    for plan, gender, uwclass, age, expect in ANCHORS:
        key = next(
            (
                item for item in current
                if item[0] == plan and item[1] == gender and item[2] == uwclass and item[3] == age
            ),
            None,
        )
        slots = current.get(key) if key else None
        if not slots:
            errors.append(f"missing anchor {plan} {gender} {uwclass} age {age}")
            continue
        for year, value in expect.items():
            if slots.get(year) != value:
                errors.append(
                    f"{plan} {gender} {uwclass} age {age} year {year} "
                    f"is {slots.get(year)!r}, expected {value}"
                )

    if PLTV.is_file():
        with PLTV.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                if _s(row.get("PLAN")) in PLANS and _s(row.get("STOREMEANS")).upper() not in {"N", "F", "FALSE", "0"}:
                    errors.append(
                        f"QuikPlTv STOREMEANS for {_s(row.get('PLAN'))} is "
                        f"{_s(row.get('STOREMEANS'))!r}; this issue must not turn it on"
                    )
                    break

    if errors:
        print("FAIL")
        for item in errors:
            print(f"  {item}")
        return 1
    print(
        f"PASS: {EXPECTED_ROWS} QuikTvs rows on {EXPECTED_GRIDS} grids "
        f"are one year earlier ({', '.join(PLANS)})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
