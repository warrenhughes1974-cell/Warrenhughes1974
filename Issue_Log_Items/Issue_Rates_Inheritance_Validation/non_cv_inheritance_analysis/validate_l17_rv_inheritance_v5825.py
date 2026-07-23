"""Validate Eric 2026-07-22 Track 1: L17 children QuikTvs == 1L17SP; SAL unchanged."""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
UINT = ROOT / "QLA_Migration" / "Output" / "rates" / "QuikTvs.csv"

EXPECTED = {
    "1SALOL": 508,
    "1SALMI": 508,
    "1SALML": 508,
    "1L17SP": 38,
    "10L171": 38,
    "10L172": 38,
    "117JPO": 38,
    "17MJPO": 38,
}
HOLD_UNCHANGED_MIN = {
    "5L0110": 1,
    "5L0510": 1,
    "5L075Y": 1,
}
HOLD_ZERO = {"5667AT"}


def plan_fp(rows, plan):
    keys = ["AGE", "CNTL", "GENDER", "UWCLASS", "BAND", "TV0", "TV1", "TV2", "TV3", "TV4"]
    out = []
    for r in rows:
        if (r.get("PLAN") or "").strip() != plan:
            continue
        out.append(tuple((r.get(k) or "").strip() for k in keys))
    return sorted(out)


def main() -> int:
    rows = list(csv.DictReader(UINT.open(encoding="utf-8-sig")))
    counts = Counter((r.get("PLAN") or "").strip() for r in rows)
    fails = []
    for plan, n in EXPECTED.items():
        got = counts.get(plan, 0)
        if got != n:
            fails.append(f"{plan}: expected {n} got {got}")
    parent = plan_fp(rows, "1L17SP")
    for child in ("10L171", "10L172", "117JPO", "17MJPO"):
        if plan_fp(rows, child) != parent:
            fails.append(f"{child}: grid != 1L17SP")
    for plan, mn in HOLD_UNCHANGED_MIN.items():
        if counts.get(plan, 0) < mn:
            fails.append(f"{plan}: expected >= {mn} (hold track)")
    for plan in HOLD_ZERO:
        if counts.get(plan, 0) != 0:
            fails.append(f"{plan}: expected 0 while actuarial pending, got {counts.get(plan)}")
    if fails:
        print("FAIL")
        for f in fails:
            print(" ", f)
        return 1
    print("PASS — L17 children QuikTvs match 1L17SP; SAL OK; L01/L05/L07/667 ART hold")
    for plan, n in EXPECTED.items():
        print(f"  {plan}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
