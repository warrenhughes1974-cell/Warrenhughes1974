"""Identify the one 1L14SC NT row that missed the $1 tolerance."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "docs", "Valuation", "analysis"))
import quikvalf_dbf as QV  # noqa: E402
import valx_layout as VL  # noqa: E402

VALF = r"Q:\CSO\CSO_Test_6_30_2026\QuikValf.dbf"


def _int(value) -> int:
    try:
        return int(str(value or "").strip() or 0)
    except ValueError:
        return 0


def main() -> int:
    lifepro = {}
    for rec in VL.read_records():
        lifepro[(str(rec.get("POLICY_NUMBER") or "").strip(), _int(rec.get("BENEFIT_SEQ")))] = rec
    valf = QV.load(VALF)
    print(f"{'POLICY':<14}{'CLS':<4}{'AGE':>4}{'DUR':>4}{'UNITS':>8}{'MRESERVE':>12}{'LP':>12}{'DIFF':>10}{'PREFIX'}")
    for row in valf.valued:
        if QV.plan_code(row) != "1L14SC":
            continue
        lp = lifepro.get((QV.lifepro_policy(row), QV.phase_of(row)))
        lp_rv = float(lp.get("RV_MEAN_RV") or 0) if lp else 0.0
        qla = QV.money(row, "MRESERVE")
        if abs(qla - lp_rv) <= 1:
            continue
        print(
            f"{QV.policy_of(row):<14}{QV.text(row,'MCLASS'):<4}"
            f"{_int(row.get('MAGE')):>4}{_int(row.get('MDUR')):>4}"
            f"{QV.money(row,'MUNIT'):>8.2f}{qla:>12.2f}{lp_rv:>12.2f}{qla-lp_rv:>10.2f}"
            f"  mplan={QV.text(row,'MPLAN')} prefix={QV.plan_prefix(row)}"
        )
    print("\n1L17SP vs LifePRO presence:")
    for row in valf.valued:
        if QV.plan_code(row) != "1L17SP":
            continue
        key = (QV.lifepro_policy(row), QV.phase_of(row))
        lp = lifepro.get(key)
        print(
            f"  {QV.policy_of(row)} phase={QV.phase_of(row)} QLA={QV.money(row,'MRESERVE'):.2f} "
            f"in_VALX={'Y' if lp else 'N'} LP={float(lp.get('RV_MEAN_RV') or 0) if lp else None}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
