"""Issue #169 -- pin down the two remaining facts about the 5667AT $0 reserve.

Live 6/30 evidence: 9011136641C (M/ST, issue 19960224, age 22, dur 31, 25 units)
is the ONLY 667 ART policy QLAdmin valued -- MTABNET 196.50, MRESERVE 98.25.
196.50 / 25 units = 7.86 net premium per unit, and 196.50 / 2 = 98.25.

1. Which grid slot holds 7.86? That tells us the duration convention the live
   engine actually used, independent of any assumption.
2. How much of the QuikTvs grid each gender/class really covers -- the ST classes
   look fully populated while PR is an 11-row stub, which would explain why the
   other post-1995 policy (9011121183C, F/PR) still reserves $0.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RATES = ROOT / "QLA_Migration" / "Output" / "rates"


def load(table):
    with (RATES / f"{table}.csv").open(encoding="utf-8-sig") as fh:
        return [r for r in csv.DictReader(fh) if r["PLAN"] == "5667AT"]


def main() -> int:
    nps, tvs = load("QuikNps"), load("QuikTvs")

    print("=" * 78)
    print("1. Where does net premium 7.86 sit for M/ST issue age 22?")
    print("   (live engine read it for duration 31)")
    print("=" * 78)
    for r in sorted((x for x in nps if x["GENDER"] == "M" and x["UWCLASS"] == "ST"
                     and x["AGE"] == "22"), key=lambda x: (x["EFFDATE"], x["CNTL"])):
        base = int(r["CNTL"]) * 10
        for i in range(10):
            v = (r.get(f"NP{i}") or "").strip()
            if v == "7.86":
                print(f"   EFF={r['EFFDATE']} CNTL={r['CNTL']} index={i}"
                      f"  -> 0-based slot {base + i}")
                print(f"      duration 31 means slot = duration - 1"
                      if base + i == 30 else
                      f"      duration 31 means slot = duration"
                      if base + i == 31 else
                      f"      unexpected slot {base + i}")

    print()
    print("=" * 78)
    print("2. QuikTvs coverage for 5667AT by gender/class")
    print("=" * 78)
    counts, ages, effs = Counter(), {}, {}
    for r in tvs:
        k = (r["GENDER"], r["UWCLASS"])
        counts[k] += 1
        ages.setdefault(k, set()).add(r["AGE"])
        effs.setdefault(k, set()).add(r["EFFDATE"])
    for k in sorted(counts):
        a = sorted(ages[k])
        shown = a if len(a) <= 14 else a[:8] + ["..."] + a[-3:]
        print(f"   {k[0]}/{k[1]:<2} rows={counts[k]:<5} distinct AGE={len(a):<3}"
              f" EFFDATE={sorted(effs[k])}")
        print(f"        ages: {shown}")

    print()
    print("   Valued policy address -- QuikTvs M/ST AGE=22 CNTL=03:")
    hit = [r for r in tvs if r["GENDER"] == "M" and r["UWCLASS"] == "ST"
           and r["AGE"] == "22" and r["CNTL"] == "03"]
    for r in hit:
        print(f"     PRESENT EFF={r['EFFDATE']} "
              f"TV={[(r.get(f'TV{i}') or '').strip() for i in range(10)]}")
    if not hit:
        print("     ABSENT")

    print()
    print("   Zero policy address -- QuikTvs F/PR (9011121183C, F/PR, issue 19951025):")
    fpr = [r for r in tvs if r["GENDER"] == "F" and r["UWCLASS"] == "PR"]
    print(f"     total F/PR rows = {len(fpr)}")
    for r in sorted(fpr, key=lambda x: (x["AGE"], x["CNTL"])):
        print(f"       AGE={r['AGE']} CNTL={r['CNTL']} EFF={r['EFFDATE']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
