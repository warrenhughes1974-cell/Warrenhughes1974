"""Issue 176 — 9010715467C Preferred cash value rate is present.

Fail-closed. Exit 1 if plan 1659C2 male Preferred issue age 46 no longer
has the cash value that QLAdmin uses for this policy, or if the policy is
no longer Preferred on that plan. A rate rebuild that keeps only the
Standard cash-value key makes the policy screen calculate zero.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "QLA_Migration" / "Output"
RATES = OUT / "rates"

POLICY = "9010715467C"
PLAN = "1659C2"
# Duration 42 is CNTL 04, CV2. Duration 43 is CV3. 50 units x rate.
CV2 = 761.00
CV3 = 774.00


def _s(value: object) -> str:
    return str(value or "").strip()


def _num(value: object) -> float | None:
    text = _s(value).replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def main() -> int:
    errors: list[str] = []
    cvs_path = RATES / "QuikCvs.csv"
    plcv_path = RATES / "QuikPlCv.csv"
    plan_path = OUT / "quikplan.csv"
    ridr_path = OUT / "quikridr.csv"
    print("Issue #176 Preferred cash value")
    for path in (cvs_path, plcv_path, plan_path, ridr_path):
        if not path.is_file():
            print(f"FAIL: missing {path.name}")
            return 1

    hit = None
    with cvs_path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if (
                _s(row.get("PLAN")) == PLAN
                and _s(row.get("AGE")) == "46"
                and _s(row.get("CNTL")) == "04"
                and _s(row.get("GENDER")) == "M"
                and _s(row.get("UWCLASS")) == "PR"
                and _s(row.get("BAND")) == "00"
            ):
                hit = row
                break
    if hit is None:
        errors.append(f"{PLAN} male Preferred age 46 duration-control 04 cash value row is missing")
    else:
        cv2 = _num(hit.get("CV2"))
        cv3 = _num(hit.get("CV3"))
        if cv2 is None or abs(cv2 - CV2) > 0.001:
            errors.append(f"duration 42 cash value per unit is {hit.get('CV2')!r} expected {CV2:.2f}")
        if cv3 is None or abs(cv3 - CV3) > 0.001:
            errors.append(f"duration 43 cash value per unit is {hit.get('CV3')!r} expected {CV3:.2f}")

    plcv = False
    with plcv_path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if (
                _s(row.get("PLAN")) == PLAN
                and _s(row.get("GENDER")) == "M"
                and _s(row.get("UWCLASS")) == "PR"
                and _s(row.get("BAND")) == "00"
            ):
                plcv = True
                break
    if not plcv:
        errors.append(f"{PLAN} male Preferred cash value plan key is missing")

    with plan_path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if _s(row.get("PLAN")) == PLAN:
                if _s(row.get("UWVARYCV")).upper() != "N":
                    errors.append(f"{PLAN} UWVARYCV={row.get('UWVARYCV')!r} expected N")
                break
        else:
            errors.append(f"{PLAN} missing from quikplan")

    with ridr_path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if _s(row.get("MPOLICY")) == POLICY and _s(row.get("MPHASE")) == "1":
                if _s(row.get("MPLAN")) != PLAN:
                    errors.append(f"{POLICY} plan {_s(row.get('MPLAN'))!r} expected {PLAN}")
                if _s(row.get("MUWCLASS")) != "PR":
                    errors.append(f"{POLICY} underwriting {_s(row.get('MUWCLASS'))!r} expected PR")
                age = _s(row.get("MAGE"))
                if age not in ("46", "46.0"):
                    errors.append(f"{POLICY} issue age {age!r} expected 46")
                units = _num(row.get("MUNIT"))
                if units is None or abs(units - 50.0) > 0.001:
                    errors.append(f"{POLICY} units {row.get('MUNIT')!r} expected 50")
                break
        else:
            errors.append(f"{POLICY} phase 1 missing from quikridr")

    if errors:
        print("FAIL")
        for err in errors:
            print(f"  {err}")
        return 1
    print(
        f"PASS: {POLICY} {PLAN} male Preferred age 46 "
        f"duration 42={CV2:.2f} duration 43={CV3:.2f} per unit"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
