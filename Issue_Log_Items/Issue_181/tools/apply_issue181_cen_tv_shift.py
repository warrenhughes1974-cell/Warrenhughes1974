"""Issue 181 — move 658/659 QuikTvs factors one year earlier.

With Store Means on, QLAdmin multiplies units by the factor one year before
the policy year. LifePRO uses the factor for the current year. Moving each
populated factor one year earlier makes those two agree. Warren approved
this on 2026-09-30, including the Issue 106 exception for these plans only.

Plans: 1659C2, 1658C1, 1659CR, 1658CS, 1659CS, 1659SR.
The last populated year is repeated in place. No year is added past the grid.
Every other plan is left byte-identical.

Idempotent. A second run prints SKIP when the 1659C2 male Preferred age-44
grid is already shifted.
"""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TVS = ROOT / "QLA_Migration" / "Output" / "rates" / "QuikTvs.csv"
ARCHIVE = ROOT / "QLA_Migration" / "Archive" / "issue181_pre_shift" / "QuikTvs.csv"
BEFORE = (
    ROOT
    / "Issue_Log_Items"
    / "Issue_181"
    / "evidence"
    / "quiktvs_six_plans_before_shift.csv"
)

PLANS = ("1659C2", "1658C1", "1659CR", "1658CS", "1659CS", "1659SR")
# 1659C2 male Preferred issue age 44. Distinguishes the original grid from
# a shifted grid, including a second accidental shift.
GOLD_PLAN = ("1659C2", "M", "PR", "44", "00", "0000", "00", "19000101")
GOLD_BEFORE = {0: ".00", 42: "751.00", 43: "764.00", 56: "978.00"}
GOLD_AFTER = {0: "2.00", 1: "17.00", 42: "764.00", 43: "776.00", 56: "978.00"}


def _shift(slots: dict[int, str]) -> dict[int, str]:
    last = max(slots)
    moved = {year: slots[year + 1] for year in range(last)}
    moved[last] = slots[last]
    return moved


def _grid_key(fields: list[str], idx: dict[str, int]) -> tuple[str, ...]:
    return tuple(fields[idx[name]].strip() for name in (
        "PLAN", "GENDER", "UWCLASS", "AGE", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE",
    ))


def _slots(rows: list[tuple[int, list[str]]], idx: dict[str, int]) -> dict[int, str]:
    found: dict[int, str] = {}
    for _line_no, fields in rows:
        control = int(fields[idx["CNTL"]].strip())
        for slot in range(10):
            value = fields[idx[f"TV{slot}"]].strip()
            if value:
                found[control * 10 + slot] = value
    return found


def _gold_state(slots: dict[int, str]) -> str:
    if all(slots.get(year) == value for year, value in GOLD_BEFORE.items()):
        return "before"
    if all(slots.get(year) == value for year, value in GOLD_AFTER.items()):
        return "after"
    return "unknown"


def main() -> int:
    if not TVS.is_file():
        print(f"FAIL: missing {TVS}")
        return 1
    raw = TVS.read_bytes()
    if b'"' in raw:
        print("FAIL: QuikTvs contains quotes; refusing to rewrite by field")
        return 1
    newline = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8")
    trailing = text.endswith(newline)
    lines = text.split(newline)
    if trailing:
        lines = lines[:-1]
    if not lines:
        print("FAIL: QuikTvs is empty")
        return 1

    header = lines[0].split(",")
    idx = {name: header.index(name) for name in (
        "PLAN", "AGE", "CNTL", "GENDER", "UWCLASS", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE",
        *(f"TV{slot}" for slot in range(10)),
    )}
    plan_at = idx["PLAN"]

    grouped: dict[tuple[str, ...], list[tuple[int, list[str]]]] = {}
    scope_lines = 0
    for line_no, line in enumerate(lines):
        if line_no == 0 or not line:
            continue
        fields = line.split(",")
        if fields[plan_at].strip() not in PLANS:
            continue
        scope_lines += 1
        grouped.setdefault(_grid_key(fields, idx), []).append((line_no, fields))

    gold_rows = grouped.get(GOLD_PLAN)
    if not gold_rows:
        print("FAIL: missing 1659C2 male Preferred age 44 grid")
        return 1
    state = _gold_state(_slots(gold_rows, idx))
    if state == "after":
        print(
            f"SKIP: 658/659 QuikTvs already shifted "
            f"({scope_lines} rows, {len(grouped)} grids)"
        )
        return 0
    if state != "before":
        print("FAIL: 1659C2 male Preferred age 44 grid is neither original nor shifted")
        return 1

    for key, rows in grouped.items():
        slots = _slots(rows, idx)
        if not slots or set(slots) != set(range(max(slots) + 1)):
            print(f"FAIL: gap in grid {key}")
            return 1

    if not ARCHIVE.is_file():
        ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(TVS, ARCHIVE)
    if not BEFORE.is_file():
        BEFORE.parent.mkdir(parents=True, exist_ok=True)
        before_lines = [lines[0]]
        for line_no, line in enumerate(lines):
            if line_no == 0 or not line:
                continue
            if line.split(",", 1)[0].strip() in PLANS:
                before_lines.append(line)
        BEFORE.write_bytes((newline.join(before_lines) + newline).encode("utf-8"))

    changed_cells = 0
    for rows in grouped.values():
        moved = _shift(_slots(rows, idx))
        for line_no, fields in rows:
            control = int(fields[idx["CNTL"]].strip())
            for slot in range(10):
                year = control * 10 + slot
                if year not in moved:
                    continue
                column = idx[f"TV{slot}"]
                if fields[column] != moved[year]:
                    fields[column] = moved[year]
                    changed_cells += 1
            lines[line_no] = ",".join(fields)

    # Re-check that lines outside the six plans were not rebuilt.
    original = text.split(newline)
    if trailing:
        original = original[:-1]
    for line_no, line in enumerate(lines):
        if line_no == 0:
            continue
        plan = line.split(",", 1)[0].strip() if line else ""
        if plan not in PLANS and line != original[line_no]:
            print(f"FAIL: out-of-scope line {line_no + 1} changed")
            return 1

    payload = newline.join(lines)
    if trailing:
        payload += newline
    TVS.write_bytes(payload.encode("utf-8"))
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(
        f"APPLIED: shifted {scope_lines} rows, {len(grouped)} grids, "
        f"{changed_cells} cells ({stamp})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
