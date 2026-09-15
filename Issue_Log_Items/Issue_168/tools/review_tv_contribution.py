"""Issue #168: does a UWCLASS=00 reserve grid actually get read for a non-00 policy?

On the four plans whose QuikTvs rows sit only at UWCLASS=00, the policies carry PR/ST
and they all valued. But they also all have a net premium, and for the term family
MRESERVE == MTABNET/2. So: if MRESERVE - MTABNET/2 == 0 the reserve came entirely
from the net premium and the 00 grid was never read -> "fall back to 00" stays
UNPROVEN, and the L14 fix must key rows at the policy's own class.

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
        f"{'PLAN':<8}{'POLICY':<13}{'CLS':<5}{'AGE':>4}{'DUR':>4}{'UNITS':>9}"
        f"{'MTABNET':>10}{'MMEAN':>9}{'MRESERVE':>10}{'MTABNET/2':>11}{'residual':>10}"
    )
    print("-" * 95)
    residual_nonzero = 0
    rows = 0
    for row in sorted(valf.valued, key=lambda r: (QV.plan_code(r), QV.policy_of(r))):
        plan = QV.plan_code(row)
        if plan not in TARGET:
            continue
        tabnet = QV.money(row, "MTABNET")
        res = QV.money(row, "MRESERVE")
        residual = res - tabnet / 2
        rows += 1
        if abs(residual) > 0.005:
            residual_nonzero += 1
        print(
            f"{plan:<8}{QV.policy_of(row):<13}{QV.text(row,'MCLASS'):<5}"
            f"{int(row.get('MAGE') or 0):>4}{int(row.get('MDUR') or 0):>4}"
            f"{QV.money(row,'MUNIT'):>9.2f}{tabnet:>10.2f}{QV.money(row,'MMEAN'):>9.2f}"
            f"{res:>10.2f}{tabnet/2:>11.2f}{residual:>10.2f}"
        )
    print()
    print(f"rows={rows}  rows where MRESERVE != MTABNET/2 (i.e. the TV grid contributed): {residual_nonzero}")
    if residual_nonzero == 0:
        print("VERDICT: reserve is entirely net-premium driven. UWCLASS=00 fallback NOT proven.")
    else:
        print("VERDICT: TV grid contributed for a non-00 policy -> QLAdmin does read the 00 default grid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
