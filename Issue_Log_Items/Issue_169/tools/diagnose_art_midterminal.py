"""Issue #169 -- why 5667AT (667 ART) still reserves $0 after the QuikNps fix.

Tests the mid-terminal reserve hypothesis against Output:

    reserve per unit = terminal reserve (QuikTvs) + 1/2 x net premium (QuikNps)

1L14SC is the control: Issue #168 proved LifePRO/QLAdmin hold 659.72 per unit at
F / age 62 / duration 24 (9011227604C, 15 units, $9,895.80). If our QuikTvs cell
at that address is 652.10 and QuikNps is ~15.2, then 652.10 + 15.2/2 = 659.7 and
the reserve QLAdmin reports is a mid-terminal, not a raw QuikTvs read.

5667AT is the subject: ART terminal reserves are legitimately .00, so its entire
reserve IS the half-net-premium term. If QLAdmin is not calculating mid-terminals
for this plan, every 5667AT policy reserves $0 no matter how correct QuikNps is.
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RATES = ROOT / "QLA_Migration" / "Output" / "rates"


def read(table):
    with (RATES / f"{table}.csv").open(encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def cells(row, pfx):
    return [row.get(f"{pfx}{i}", "") for i in range(10)]


def main() -> int:
    print("=" * 78)
    print("QuikPlTv valuation assumptions -- 1L14SC (reserves work) vs 5667AT ($0)")
    print("=" * 78)
    for r in read("QuikPlTv"):
        if r["PLAN"] in ("1L14SC", "5667AT"):
            print(
                "  {:6s} {}/{:2s} EFF={} MORT={:3s} RSVINT={:2s} RSVMETH={:2s} "
                "INTMETHTV={:2s} STOREMEANS={:2s} CALCMIDS={:2s}".format(
                    r["PLAN"], r["GENDER"], r["UWCLASS"], r["EFFDATE"],
                    r["MORT"], r["RSVINT"], r["RSVMETH"],
                    r["INTMETHTV"], r["STOREMEANS"], r["CALCMIDS"],
                )
            )

    print()
    print("=" * 78)
    print("CONTROL 1L14SC  F / AGE 62 / CNTL 02  (Issue #168 gold: dur 24 = 659.72)")
    print("=" * 78)
    tvs = [r for r in read("QuikTvs")
           if r["PLAN"] == "1L14SC" and r["GENDER"] == "F"
           and r["AGE"] == "62" and r["CNTL"] == "02" and r["UWCLASS"] == "NT"]
    nps = [r for r in read("QuikNps")
           if r["PLAN"] == "1L14SC" and r["GENDER"] == "F"
           and r["AGE"] == "62" and r["CNTL"] == "02" and r["UWCLASS"] == "NT"]
    for r in tvs:
        print("  QuikTvs TV0-9:", cells(r, "TV"))
    for r in nps:
        print("  QuikNps NP0-9:", cells(r, "NP"))
    if tvs and nps:
        tv = cells(tvs[0], "TV")
        np_ = cells(nps[0], "NP")
        print()
        print("  idx  QuikTvs      QuikNps    TV + NP/2   LifePRO gold")
        gold = {3: "636.23 (dur 23)", 4: "659.72 (dur 24)"}
        for i in range(10):
            try:
                t = float(tv[i] or 0)
                n = float(np_[i] or 0)
            except ValueError:
                continue
            print("   {:2d}  {:>9.2f}  {:>9.2f}  {:>9.2f}   {}".format(
                i, t, n, t + n / 2, gold.get(i, "")))

    print()
    print("=" * 78)
    print("SUBJECT 5667AT  M/PR / AGE 39 / CNTL 03  (LifePRO gold: dur 40 = $8,239 / 200u)")
    print("=" * 78)
    for eff in ("19000101", "19950101"):
        tv = [r for r in read("QuikTvs")
              if r["PLAN"] == "5667AT" and r["GENDER"] == "M" and r["AGE"] == "39"
              and r["CNTL"] == "03" and r["EFFDATE"] == eff]
        npr = [r for r in read("QuikNps")
               if r["PLAN"] == "5667AT" and r["GENDER"] == "M" and r["AGE"] == "39"
               and r["CNTL"] == "03" and r["UWCLASS"] == "PR" and r["EFFDATE"] == eff]
        print(f"  EFFDATE={eff}")
        print("    QuikTvs rows at this address:", len(tv),
              ([r["UWCLASS"] for r in tv] or "NONE"))
        for r in tv:
            print("      ", r["UWCLASS"], cells(r, "TV"))
        for r in npr:
            np_ = cells(r, "NP")
            print("       QuikNps M/PR:", np_)
            print("       NP9 =", np_[9], "-> half =",
                  round(float(np_[9] or 0) / 2, 3),
                  "x 200 units =", round(float(np_[9] or 0) / 2 * 200, 2))

    print()
    print("=" * 78)
    print("5667AT QuikTvs: are ANY cells non-zero?")
    print("=" * 78)
    total = nonzero_rows = 0
    for r in read("QuikTvs"):
        if r["PLAN"] != "5667AT":
            continue
        total += 1
        if any(v not in ("", ".00", "0.00") for v in cells(r, "TV")):
            nonzero_rows += 1
    print(f"  rows={total}  rows with any non-zero TV cell={nonzero_rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
