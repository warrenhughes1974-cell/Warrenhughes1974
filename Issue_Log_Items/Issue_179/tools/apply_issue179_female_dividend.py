"""Issue 179 — copy the male dividend scale onto the female key.

Plans 221END, 196065, and 1960OL have a female dividend key and no female
LifePRO scale. QLAdmin looks up by the sex on the policy, so the female key
needs the same factors as the male key. Warren approved that copy 2026-09-30.

Idempotent. If every male row already has a matching female row, the file
is left untouched.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DVS = ROOT / "QLA_Migration" / "Output" / "rates" / "QuikDvs.csv"
PLANS = ("221END", "196065", "1960OL")
DV_COLS = tuple(f"DV{i}" for i in range(10))
SEG = ("AGE", "CNTL", "UWCLASS", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE")


def _s(value: object) -> str:
    return str(value or "").strip()


def _seg(row: dict) -> tuple:
    return tuple(_s(row.get(col)) for col in SEG)


def _factors(row: dict) -> tuple:
    return tuple(_s(row.get(col)) for col in DV_COLS)


def main() -> int:
    if not DVS.is_file():
        print(f"FAIL: missing {DVS}")
        return 1
    with DVS.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    if not fields:
        print("FAIL: QuikDvs has no header")
        return 1

    male: dict[str, dict[tuple, dict]] = {plan: {} for plan in PLANS}
    female: dict[str, dict[tuple, tuple]] = {plan: {} for plan in PLANS}
    for row in rows:
        plan = _s(row.get("PLAN"))
        if plan not in male:
            continue
        gender = _s(row.get("GENDER"))
        key = _seg(row)
        if gender == "M":
            male[plan][key] = row
        elif gender == "F":
            female[plan][key] = _factors(row)

    missing_male = [plan for plan in PLANS if not male[plan]]
    if missing_male:
        print("FAIL: no male dividend rows for " + ", ".join(missing_male))
        return 1

    already = True
    for plan in PLANS:
        if set(female[plan]) != set(male[plan]):
            already = False
            break
        for key, src in male[plan].items():
            if female[plan].get(key) != _factors(src):
                already = False
                break
        if not already:
            break
    if already:
        counts = ", ".join(f"{plan} {len(male[plan])}" for plan in PLANS)
        print(f"SKIP: female dividend rows already match male ({counts})")
        return 0

    out = []
    i = 0
    added = {plan: 0 for plan in PLANS}
    while i < len(rows):
        plan = _s(rows[i].get("PLAN"))
        gender = _s(rows[i].get("GENDER"))
        if plan in male and gender == "M":
            block = []
            while i < len(rows) and _s(rows[i].get("PLAN")) == plan and _s(rows[i].get("GENDER")) == "M":
                block.append(rows[i])
                i += 1
            out.extend(block)
            for src in block:
                copy = dict(src)
                copy["GENDER"] = "F"
                out.append(copy)
                added[plan] += 1
            continue
        if plan in male and gender == "F":
            i += 1
            continue
        out.append(rows[i])
        i += 1

    with DVS.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(out)
    print(
        "APPLIED: female dividend rows copied from male ("
        + ", ".join(f"{plan} {added[plan]}" for plan in PLANS)
        + ")"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
