"""Issue 175 — L15 and L16 reserve category 13, L17 BASE reserve category 12.

Fail-closed. Exit 1 if a seq-1 policy on those coverages is still the LifePRO
letter L, or if the engine map is missing. Other product types stay as-is.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "QLA_Migration" / "Output"
SRC = ROOT / "QLA_Migration" / "Source"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qla_core.quikspec_resrvcat import (  # noqa: E402
    ISSUE175_RESERVE_CATEGORY,
    load_ppben_seq1_plans,
    reserve_category,
)

GOLD = {
    "9011210337C": {"RESRVCAT": "13", "VANISH": "F", "RESSTATE": "KY", "SOR_POL": "9011210337"},
    "9011216680C": {"RESRVCAT": "13", "VANISH": "F", "RESSTATE": "IN", "SOR_POL": "9011216680"},
    "9011217014C": {"RESRVCAT": "12", "VANISH": "F", "RESSTATE": "LA", "SOR_POL": "9011217014"},
}
PLAN_PRODUCT = {"1L15GD": "13", "1L16GD": "13", "1L17SP": "12"}


def _s(value: object) -> str:
    return str(value or "").strip()


def _unit_checks() -> list[str]:
    errors: list[str] = []
    expected = {"L15": "13", "L16": "13", "L17 BASE": "12"}
    if ISSUE175_RESERVE_CATEGORY != expected:
        errors.append(f"map is {ISSUE175_RESERVE_CATEGORY!r}")
    if reserve_category("L15", "L") != "13":
        errors.append("L15 did not map to 13")
    if reserve_category("L16", "L") != "13":
        errors.append("L16 did not map to 13")
    if reserve_category("L17 BASE", "L") != "12":
        errors.append("L17 BASE did not map to 12")
    if reserve_category("DISCHO25", "L") != "L":
        errors.append("discount coverage L was remapped")
    if reserve_category("221END", "03") != "03":
        errors.append("ordinary product type 03 was remapped")
    return errors


def main() -> int:
    errors = _unit_checks()
    spec_path = OUT / "quikspec.csv"
    plan_path = OUT / "quikplan.csv"
    print("Issue #175 reserve category validator")
    if not spec_path.is_file() or not plan_path.is_file():
        print("FAIL: missing quikspec or quikplan")
        return 1

    spec: dict[str, dict[str, str]] = {}
    with spec_path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            spec[_s(row.get("MPOLICY"))] = {k: _s(v) for k, v in row.items()}

    seq1 = load_ppben_seq1_plans(str(SRC))
    checked = {code: 0 for code in ISSUE175_RESERVE_CATEGORY}
    for policy, row in spec.items():
        coverage = seq1.get(policy, "")
        if coverage not in ISSUE175_RESERVE_CATEGORY:
            continue
        checked[coverage] += 1
        expected = ISSUE175_RESERVE_CATEGORY[coverage]
        if row.get("RESRVCAT") != expected:
            errors.append(
                f"{policy} coverage {coverage} RESRVCAT={row.get('RESRVCAT')!r} expected {expected}"
            )

    if sum(checked.values()) == 0:
        errors.append("no L15, L16, or L17 BASE policies in Output")

    for policy, fields in GOLD.items():
        row = spec.get(policy)
        if row is None:
            errors.append(f"missing gold {policy}")
            continue
        for field, expected in fields.items():
            if row.get(field) != expected:
                errors.append(f"{policy} {field}={row.get(field)!r} expected {expected}")

    with plan_path.open(newline="", encoding="utf-8-sig") as handle:
        plans = {_s(row.get("PLAN")): _s(row.get("PRODUCT")) for row in csv.DictReader(handle)}
    for plan, expected in PLAN_PRODUCT.items():
        got = plans.get(plan)
        if got != expected:
            errors.append(f"quikplan {plan} PRODUCT={got!r} expected {expected}")

    print(
        "checked "
        + " ".join(f"{code}={count}" for code, count in checked.items())
    )
    if errors:
        print(f"FAIL: {len(errors)}")
        for item in errors[:30]:
            print(f"  {item}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
