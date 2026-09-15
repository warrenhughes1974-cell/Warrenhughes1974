"""Issue #168 independent review: are L05 / L14 reserves a key problem or a value problem?

Cross-tabs, for every L-family plan:
  * Output/rates/QuikTvs.csv  - terminal reserve factor rows by (PLAN, UWCLASS)
  * Output/rates/QuikNps.csv  - net premium factor rows by (PLAN, UWCLASS)
  * Output/quikridr.csv       - policy UW classes actually carried, by plan
  * QuikPlTv / QuikPlUw       - emitted key rows

Read-only.
"""
from __future__ import annotations

import collections
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RATES = os.path.join(ROOT, "QLA_Migration", "Output", "rates")
OUT = os.path.join(ROOT, "QLA_Migration", "Output")

# Plans of interest: the L-book, plus the L10 controls that are known to work.
INTEREST_PREFIX = ("1L", "5L", "9L", "10L", "0L", "L")


def is_l_plan(plan: str) -> bool:
    p = plan.strip().upper()
    return "L0" in p[:4] or "L1" in p[:4]


def scan_factor_table(fn: str, val_prefix: str) -> dict:
    path = os.path.join(RATES, fn)
    agg = collections.defaultdict(lambda: {"rows": 0, "nonzero": 0})
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rd = csv.DictReader(fh)
        vcols = [c for c in rd.fieldnames if c.startswith(val_prefix) and c[len(val_prefix):].isdigit()]
        for row in rd:
            plan = (row.get("PLAN") or "").strip()
            if not is_l_plan(plan):
                continue
            key = (plan, (row.get("UWCLASS") or "").strip(), (row.get("GENDER") or "").strip())
            slot = agg[key]
            slot["rows"] += 1
            for c in vcols:
                try:
                    if float(row.get(c) or 0) != 0.0:
                        slot["nonzero"] += 1
                        break
                except ValueError:
                    pass
    return agg


def scan_ridr() -> dict:
    path = os.path.join(OUT, "quikridr.csv")
    agg = collections.Counter()
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rd = csv.DictReader(fh)
        for row in rd:
            plan = (row.get("MPLAN") or "").strip()
            if not is_l_plan(plan):
                continue
            agg[(plan, (row.get("MUWCLASS") or "").strip())] += 1
    return agg


def scan_key_table(fn: str) -> dict:
    path = os.path.join(RATES, fn)
    if not os.path.isfile(path):
        return {}
    agg = collections.Counter()
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rd = csv.DictReader(fh)
        for row in rd:
            plan = (row.get("PLAN") or "").strip()
            if not is_l_plan(plan):
                continue
            agg[(plan, (row.get("UWCLASS") or "").strip())] += 1
    return agg


def main() -> int:
    tvs = scan_factor_table("QuikTvs.csv", "TV")
    nps = scan_factor_table("QuikNps.csv", "NP")
    cvs = scan_factor_table("QuikCvs.csv", "CV")
    ridr = scan_ridr()
    pltv = scan_key_table("QuikPlTv.csv")

    plans = sorted({k[0] for k in tvs} | {k[0] for k in nps} | {p for p, _ in ridr} | {k[0] for k in cvs})

    print("=" * 96)
    print("L-BOOK: emitted factor rows (UWCLASS / nonzero) vs policy classes actually carried")
    print("=" * 96)
    hdr = f"{'PLAN':<10}{'POLICIES (MUWCLASS)':<30}{'QuikTvs UWCLASS: rows/nonzero':<34}{'QuikNps UWCLASS: rows/nonzero'}"
    print(hdr)
    print("-" * 96)
    for plan in plans:
        pol = ", ".join(
            f"{uw or '(blank)'}={n}" for (p, uw), n in sorted(ridr.items()) if p == plan
        ) or "-"

        def fmt(agg):
            byuw = collections.defaultdict(lambda: [0, 0])
            for (p, uw, _g), v in agg.items():
                if p != plan:
                    continue
                byuw[uw][0] += v["rows"]
                byuw[uw][1] += v["nonzero"]
            if not byuw:
                return "NONE"
            return ", ".join(f"{uw or '(blank)'}={v[0]}/{v[1]}" for uw, v in sorted(byuw.items()))

        print(f"{plan:<10}{pol:<30}{fmt(tvs):<34}{fmt(nps)}")

    print()
    print("=" * 96)
    print("QuikPlTv key rows (PLAN, UWCLASS)")
    print("=" * 96)
    for (plan, uw), n in sorted(pltv.items()):
        print(f"  {plan:<10} UWCLASS={uw or '(blank)':<8} rows={n}")

    print()
    print("=" * 96)
    print("QuikCvs for the same plans")
    print("=" * 96)
    for plan in plans:
        byuw = collections.defaultdict(lambda: [0, 0])
        for (p, uw, _g), v in cvs.items():
            if p != plan:
                continue
            byuw[uw][0] += v["rows"]
            byuw[uw][1] += v["nonzero"]
        if byuw:
            print(f"  {plan:<10} " + ", ".join(f"{uw or '(blank)'}={v[0]}/{v[1]}" for uw, v in sorted(byuw.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
