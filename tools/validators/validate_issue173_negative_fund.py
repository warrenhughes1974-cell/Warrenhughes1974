"""Issue 173 — negative LifePRO fund stays on the last QuikIswl row.

Fail-closed. Exit 1 if a later history rebuild stores those ending
balances as 0.00 again. Does not require QLA_VALUATION_DATE.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "QLA_Migration" / "Output" / "QuikIswl.csv"

# Last history row on the 2026-06-30 package.
GOLDS = {
    "9010779727C": -172395.45,
    "9010737619C": -718363.35,
    "9010735781C": -121065.25,
    "9010713704C": 45551.94,
}
MIN_NEGATIVE_POLICIES = 247


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
    print("Issue #173 negative ISWL fund")
    if not OUT.is_file():
        print("FAIL: missing QuikIswl.csv")
        return 1

    last: dict[str, dict[str, str]] = {}
    with OUT.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            policy = _s(row.get("MPOLICY"))
            if policy:
                last[policy] = row

    errors: list[str] = []
    negative = 0
    for policy, row in last.items():
        account = _num(row.get("MACCTBAL"))
        cash = _num(row.get("MCASHVAL"))
        if account is None or account >= -0.005:
            continue
        negative += 1
        if cash is None or abs(cash - account) > 0.011:
            errors.append(
                f"{policy} last cash value {row.get('MCASHVAL')!r} "
                f"does not match account {row.get('MACCTBAL')!r}"
            )

    if negative < MIN_NEGATIVE_POLICIES:
        errors.append(
            f"{negative} policies end with a negative account, "
            f"expected at least {MIN_NEGATIVE_POLICIES}"
        )

    for policy, expected in GOLDS.items():
        row = last.get(policy)
        if row is None:
            errors.append(f"{policy} missing from QuikIswl")
            continue
        account = _num(row.get("MACCTBAL"))
        cash = _num(row.get("MCASHVAL"))
        if account is None or abs(account - expected) > 0.011:
            errors.append(
                f"{policy} account {row.get('MACCTBAL')!r} expected {expected:.2f}"
            )
        if cash is None or abs(cash - expected) > 0.011:
            errors.append(
                f"{policy} cash value {row.get('MCASHVAL')!r} expected {expected:.2f}"
            )

    if errors:
        print("FAIL")
        for err in errors[:25]:
            print(f"  {err}")
        return 1
    print(
        f"PASS: {negative} policies end negative; "
        f"9010779727C=-172395.45; 9010713704C=45551.94"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
