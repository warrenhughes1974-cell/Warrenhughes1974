"""Issue #168: is the residual in review_tv_contribution.py a real reserve-grid
contribution, or just MMEAN's 2-decimal rounding?

QuikValf stores MMEAN as N7.2. If, for every policy on a UWCLASS=00-only reserve
grid, MMEAN == round(MTABNET / (2 * units), 2) and MRESERVE == round(MMEAN * units, 2),
then the reserve is 100% net-premium driven, the 00 grid was never read, and
"QLAdmin falls back to UWCLASS=00" is NOT proven by this data.

Read-only.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "docs", "Valuation", "analysis"))

import quikvalf_dbf as QV  # noqa: E402

TARGET = {"9L01WP", "901ADB", "976659", "996ADB"}


def main() -> int:
    valf = QV.load()
    print(
        f"{'PLAN':<8}{'POLICY':<13}{'MTABNET':>9}{'UNITS':>8}{'MMEAN':>8}"
        f"{'pred MMEAN':>12}{'MRESERVE':>10}{'pred RES':>10}  match"
    )
    print("-" * 88)
    rows = explained = 0
    for row in sorted(valf.valued, key=lambda r: (QV.plan_code(r), QV.policy_of(r))):
        plan = QV.plan_code(row)
        if plan not in TARGET:
            continue
        tabnet = QV.money(row, "MTABNET")
        units = QV.money(row, "MUNIT")
        mean = QV.money(row, "MMEAN")
        res = QV.money(row, "MRESERVE")
        if not units:
            continue
        pred_mean = round(tabnet / (2 * units), 2)
        pred_res = round(pred_mean * units, 2)
        ok = abs(pred_mean - mean) < 0.005 and abs(pred_res - res) < 0.005
        rows += 1
        explained += 1 if ok else 0
        print(
            f"{plan:<8}{QV.policy_of(row):<13}{tabnet:>9.2f}{units:>8.2f}{mean:>8.2f}"
            f"{pred_mean:>12.2f}{res:>10.2f}{pred_res:>10.2f}  {'yes' if ok else 'NO'}"
        )
    print()
    print(f"rows={rows}  fully explained by net premium + MMEAN rounding: {explained}")
    if explained == rows:
        print(
            "VERDICT: reserve is 100% net-premium driven on all of these plans.\n"
            "         The UWCLASS=00 reserve grid was never read.\n"
            "         'QLAdmin falls back to UWCLASS=00' is NOT proven -> the L14 fix must\n"
            "         put rows at the classes the policies actually carry."
        )
    else:
        print("VERDICT: at least one policy shows a genuine reserve-grid contribution at the 00 key.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
