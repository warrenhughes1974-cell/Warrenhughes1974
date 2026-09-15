"""Issue #168: exact scope of an L14 (1L14SC) class-key fix.

Counts the rows that exist at UWCLASS=NT in every rate table the L14 reserve
touches, plus the key/lookup tables, so the fix can be sized precisely.

Also re-tests the 976659 'NO' rows from review_tv_contribution_rounding.py under
commercial (half-up) rounding instead of Python's banker's rounding.

Read-only.
"""
from __future__ import annotations

import collections
import csv
import decimal
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "docs", "Valuation", "analysis"))

import quikvalf_dbf as QV  # noqa: E402

RATES = os.path.join(ROOT, "QLA_Migration", "Output", "rates")
PLAN = "1L14SC"


def half_up(value: float, places: int = 2) -> float:
    return float(
        decimal.Decimal(repr(value)).quantize(
            decimal.Decimal("1." + "0" * places), rounding=decimal.ROUND_HALF_UP
        )
    )


def count_by_class(fn: str) -> collections.Counter:
    path = os.path.join(RATES, fn)
    agg = collections.Counter()
    if not os.path.isfile(path):
        return agg
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rd = csv.DictReader(fh)
        if "UWCLASS" not in (rd.fieldnames or []):
            return agg
        for row in rd:
            if (row.get("PLAN") or "").strip() != PLAN:
                continue
            agg[(row.get("UWCLASS") or "").strip()] += 1
    return agg


def main() -> int:
    print(f"=== {PLAN} rows per table, by UWCLASS (current 9/13 package) ===")
    tables = [
        "QuikTvs.csv", "QuikNps.csv", "QuikCvs.csv", "QuikNff.csv", "QuikDbs.csv",
        "QuikGps.csv", "QuikDvs.csv", "QuikPlTv.csv", "QuikPlCv.csv", "QuikPlDb.csv",
        "QuikPlGp.csv", "QuikPlDv.csv", "QuikPlUw.csv", "QuikPlSt.csv", "QuikPlNb.csv",
    ]
    add_total = 0
    for fn in tables:
        agg = count_by_class(fn)
        if not agg:
            print(f"  {fn:<15} (no {PLAN} rows / no UWCLASS column)")
            continue
        desc = ", ".join(f"{k or '(blank)'}={v}" for k, v in sorted(agg.items()))
        nt = agg.get("NT", 0)
        missing = [c for c in ("PQ", "PR", "ST") if c not in agg]
        note = ""
        if nt and missing:
            add = nt * len(missing)
            add_total += add
            note = f"  -> needs {', '.join(missing)}: +{add} rows"
        print(f"  {fn:<15} {desc}{note}")
    print(f"\n  total rows a PQ/PR/ST replication would add: {add_total}")

    # QuikPlUw valid class list for the plan
    print(f"\n=== QuikPlUw entries for {PLAN} ===")
    with open(os.path.join(RATES, "QuikPlUw.csv"), encoding="utf-8-sig", newline="") as fh:
        found = [r for r in csv.DictReader(fh) if (r.get("PLAN") or "").strip() == PLAN]
    for r in found:
        print("  ", r)
    if not found:
        print("   (none)")

    # policy classes actually carried, from QuikValf
    valf = QV.load()
    pol = collections.Counter(
        QV.text(r, "MCLASS") for r in valf.valued if QV.plan_code(r) == PLAN
    )
    print(f"\n=== {PLAN} valued policies by MCLASS (QuikValf 9/2 run) ===")
    for cls, n in sorted(pol.items()):
        print(f"   {cls or '(blank)'}: {n}")

    # rounding re-test
    print("\n=== 976659 residuals under commercial (half-up) rounding ===")
    bad = 0
    total = 0
    for row in valf.valued:
        if QV.plan_code(row) not in {"9L01WP", "901ADB", "976659", "996ADB"}:
            continue
        units = QV.money(row, "MUNIT")
        if not units:
            continue
        total += 1
        pred_mean = half_up(QV.money(row, "MTABNET") / (2 * units))
        pred_res = half_up(pred_mean * units)
        if abs(pred_mean - QV.money(row, "MMEAN")) > 0.005 or abs(pred_res - QV.money(row, "MRESERVE")) > 0.005:
            bad += 1
            print(
                f"   unexplained: {QV.plan_code(row)} {QV.policy_of(row)} "
                f"MMEAN={QV.money(row,'MMEAN')} pred={pred_mean} "
                f"MRESERVE={QV.money(row,'MRESERVE')} pred={pred_res}"
            )
    print(f"   rows={total}  unexplained by (net premium / 2) with half-up rounding: {bad}")
    if bad == 0:
        print(
            "   VERDICT: every one of these policies is 100% net-premium driven.\n"
            "            The UWCLASS=00 reserve grid was never read -> 'fall back to 00'\n"
            "            is NOT supported. L14 rows must be keyed to the policy's own class."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
