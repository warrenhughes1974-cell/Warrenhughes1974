"""Issue #169 -- prove QLAdmin's mean-reserve formula, then show why 5667AT is $0.

QLAdmin Help (via Issue #80 code map) for QuikPlTv:
    STOREMEANS = False -> QuikTvs holds TERMINAL factors
    CALCMIDS   = False -> engine calculates MEAN reserves

Classic statutory mean reserve per unit:
    mean(t) = 1/2 * ( terminal(t-1) + net level premium + terminal(t) )

Leg 1 (control): reproduce Issue #168's verified L14 golds 636.23 and 659.72
                 from our own QuikTvs + QuikNps cells.
Leg 2 (subject): apply the same formula to 5667AT, where terminal factors are
                 legitimately .00 for an annually renewable term, so the whole
                 reserve is 1/2 x net premium.
Leg 3 (defect):  show which EFFDATE generations and class keys 5667AT actually
                 has in QuikTvs vs QuikNps, and compare that alignment to every
                 other plan in the fleet.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RATES = ROOT / "QLA_Migration" / "Output" / "rates"


def read(table):
    with (RATES / f"{table}.csv").open(encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def cell(row, pfx, i):
    try:
        return float((row.get(f"{pfx}{i}") or "").strip() or 0)
    except ValueError:
        return 0.0


def grid(rows, pfx):
    """(plan, gender, uwclass, effdate) -> {duration_slot_index: value} keyed AGE/CNTL."""
    out = {}
    for r in rows:
        key = (r["PLAN"], r["GENDER"], r["UWCLASS"], r["EFFDATE"], r["AGE"])
        d = out.setdefault(key, {})
        base = int(r["CNTL"]) * 10
        for i in range(10):
            d[base + i] = cell(r, pfx, i)
    return out


def main() -> int:
    tvs, nps = read("QuikTvs"), read("QuikNps")
    tv_g, np_g = grid(tvs, "TV"), grid(nps, "NP")

    print("=" * 84)
    print("LEG 1 -- CONTROL: reproduce Issue #168's verified L14 reserves")
    print("  gold: F / issue age 62 / per-unit 636.23 and 659.72 (9011227604C 15u = 9,895.80)")
    print("=" * 84)
    k = ("1L14SC", "F", "NT", "19000101", "62")
    tv, np_ = tv_g.get(k, {}), np_g.get(k, {})
    p = np_.get(20, 0.0)
    print(f"  net level premium (QuikNps, flat) = {p}")
    print(f"  {'slot':>5}{'term(t-1)':>11}{'term(t)':>10}{'mean = (a+P+b)/2':>19}   gold")
    for slot in range(21, 27):
        a, b = tv.get(slot - 1, 0.0), tv.get(slot, 0.0)
        mean = (a + p + b) / 2
        gold = ""
        if abs(mean - 636.23) < 0.005:
            gold = "<== 636.23 MATCH"
        elif abs(mean - 659.72) < 0.005:
            gold = "<== 659.72 MATCH"
        print(f"  {slot:>5}{a:>11.2f}{b:>10.2f}{mean:>19.2f}   {gold}")

    print()
    print("=" * 84)
    print("LEG 2 -- SUBJECT: same formula on 5667AT (667 ART), terminal factors .00")
    print("=" * 84)
    anchors = [
        ("9010800356C", "M", "PR", "39", 40, 200, 8239.00),
        ("9010768802C", "F", "PR", "28", 41, 30, 490.35),
        ("9010764248C", "F", "PR", "22", 41, 50, 474.50),
    ]
    for pol, sex, cls, age, dur, units, lp in anchors:
        for eff in ("19000101", "19950101"):
            kt = ("5667AT", sex, cls, eff, age)
            tv, np_ = tv_g.get(kt, {}), np_g.get(kt, {})
            a, b = tv.get(dur - 1, 0.0), tv.get(dur, 0.0)
            p = np_.get(dur, 0.0)
            mean = (a + p + b) / 2
            print(f"  {pol} {sex}/{cls} age {age} dur {dur} EFF={eff}")
            print(f"    QuikTvs rows present: {'YES' if tv else 'NONE'};"
                  f" term(t-1)={a:.2f} term(t)={b:.2f}")
            print(f"    QuikNps net premium = {p:.2f}"
                  f" -> mean/unit = {mean:.4f} x {units}u = {mean * units:,.2f}"
                  f"   LifePRO = {lp:,.2f}"
                  f"   {'MATCH' if abs(mean * units - lp) < 0.01 else ''}")

    print()
    print("=" * 84)
    print("LEG 3 -- DEFECT: QuikTvs vs QuikNps generation/class alignment")
    print("=" * 84)
    tv_keys = defaultdict(set)
    np_keys = defaultdict(set)
    for r in tvs:
        tv_keys[r["PLAN"]].add((r["GENDER"], r["UWCLASS"], r["EFFDATE"]))
    for r in nps:
        np_keys[r["PLAN"]].add((r["GENDER"], r["UWCLASS"], r["EFFDATE"]))

    print("  5667AT QuikTvs keys:", sorted(tv_keys["5667AT"]))
    print("  5667AT QuikNps keys:", sorted(np_keys["5667AT"]))
    print("  QuikNps keys with NO matching QuikTvs key:",
          sorted(np_keys["5667AT"] - tv_keys["5667AT"]))

    print()
    print("  Fleet: plans where a QuikNps key has no matching QuikTvs key")
    print(f"  {'PLAN':<9}{'Nps keys':>9}{'Tvs keys':>9}{'unmatched':>11}")
    offenders = 0
    for plan in sorted(np_keys):
        missing = np_keys[plan] - tv_keys.get(plan, set())
        if missing:
            offenders += 1
            mark = "  <-- 667 ART" if plan == "5667AT" else ""
            print(f"  {plan:<9}{len(np_keys[plan]):>9}{len(tv_keys.get(plan, set())):>9}"
                  f"{len(missing):>11}{mark}")
    print(f"  plans with a net-premium key that has no terminal-reserve key: {offenders}"
          f" of {len(np_keys)}")

    # AGE/CNTL footprint comparison for the subject
    print()
    print("  5667AT AGE footprint")
    tv_ages = {r["AGE"] for r in tvs if r["PLAN"] == "5667AT"}
    np_ages = {r["AGE"] for r in nps if r["PLAN"] == "5667AT"}
    print(f"    QuikTvs distinct AGE = {len(tv_ages)}  range {min(tv_ages)}..{max(tv_ages)}")
    print(f"    QuikNps distinct AGE = {len(np_ages)}  range {min(np_ages)}..{max(np_ages)}")
    print(f"    ages in Nps but not Tvs = {len(np_ages - tv_ages)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
