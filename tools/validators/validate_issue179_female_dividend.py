"""Issue 179 — female dividend scale matches the male scale.

Fail-closed. Exit 1 if 221END, 196065, or 1960OL loses the female QuikDvs
rows that were copied from the male scale. QLAdmin looks the dividend up by
the sex on the policy, so a blank female key leaves Next Div empty.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RATES = ROOT / "QLA_Migration" / "Output" / "rates"

# Male row floors on the 8/31 package. A later extract may add rows; it must
# not drop below these, and every male row must still have a female twin.
PLAN_FLOORS = {
    "221END": 236,
    "196065": 249,
    "1960OL": 345,
}
DV_COLS = tuple(f"DV{i}" for i in range(10))
SEG = ("AGE", "CNTL", "UWCLASS", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE")


def _s(value: object) -> str:
    return str(value or "").strip()


def _key(row: dict) -> tuple:
    return tuple(_s(row.get(col)) for col in SEG)


def _factors(row: dict) -> tuple:
    return tuple(_s(row.get(col)) for col in DV_COLS)


def main() -> int:
    errors: list[str] = []
    dvs_path = RATES / "QuikDvs.csv"
    key_path = RATES / "QuikPlDv.csv"
    print("Issue #179 female dividend scale")
    for path in (dvs_path, key_path):
        if not path.is_file():
            print(f"FAIL: missing {path}")
            return 1

    by_plan: dict[str, dict[str, dict]] = {plan: {"M": {}, "F": {}} for plan in PLAN_FLOORS}
    with dvs_path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            plan = _s(row.get("PLAN"))
            if plan not in PLAN_FLOORS:
                continue
            gender = _s(row.get("GENDER"))
            if gender not in ("M", "F"):
                errors.append(f"{plan} unexpected gender {gender!r}")
                continue
            key = _key(row)
            bucket = by_plan[plan][gender]
            if key in bucket:
                errors.append(f"{plan} {gender} duplicate key {key}")
            bucket[key] = _factors(row)

    for plan, floor in PLAN_FLOORS.items():
        male = by_plan[plan]["M"]
        female = by_plan[plan]["F"]
        if len(male) < floor:
            errors.append(f"{plan} male rows {len(male)} below {floor}")
        if len(female) != len(male):
            errors.append(f"{plan} female rows {len(female)} male rows {len(male)}")
        missing = [key for key in male if key not in female]
        extra = [key for key in female if key not in male]
        if missing:
            errors.append(f"{plan} female missing {len(missing)} male keys, first {missing[0]}")
        if extra:
            errors.append(f"{plan} female has {len(extra)} keys with no male row, first {extra[0]}")
        differ = [key for key in male if key in female and female[key] != male[key]]
        if differ:
            errors.append(f"{plan} female factors differ on {len(differ)} keys, first {differ[0]}")

    gold_key = ("19", "06", "00", "00", "0000", "00", "19000101")
    gold = by_plan["221END"]["F"].get(gold_key)
    if gold is None:
        errors.append("221END female age 19 duration 66 row is missing")
    elif gold[6] != "7.36":
        errors.append(f"221END female duration 66 factor is {gold[6]!r} expected 7.36")

    keys_found = {plan: set() for plan in PLAN_FLOORS}
    with key_path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            plan = _s(row.get("PLAN"))
            if plan in keys_found:
                keys_found[plan].add(_s(row.get("GENDER")))
    for plan, genders in keys_found.items():
        if "F" not in genders or "M" not in genders:
            errors.append(f"{plan} QuikPlDv genders {sorted(genders)} expected M and F")

    if errors:
        print("FAIL")
        for err in errors:
            print(f"  {err}")
        return 1
    print(
        "PASS: female dividend rows match male on "
        + ", ".join(f"{plan} {len(by_plan[plan]['F'])}" for plan in PLAN_FLOORS)
        + "; 221END age 19 duration 66 = 7.36"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
