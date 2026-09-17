"""Issue #169 - fail-closed check that 667 ART reserves can be reached.

QLAdmin's mean reserve is 1/2 x ( terminal(t-1) + net premium + terminal(t) ),
terminal factors from QuikTvs and net premium from QuikNps. It will not pick the
net premium up unless a QuikTvs row exists at the policy's generation / gender /
class / issue age. 5667AT originally had a QuikTvs grid only at EFFDATE=19950101
and only for the ST classes, so 93 of 94 policies reserved $0.

Exits 1 if any of the following regress in full QLA_Migration/Output/:

  1. any 5667AT QuikNps address has no QuikTvs row at the same generation,
     gender and class  (the drop this catches: a rate rebatch that rebuilds
     QuikTvs from the PSUBSSEG manifest alone and loses the base generation)
  2. the 19000101 base generation is missing for either class or gender
  3. any 5667AT terminal factor is non-zero (would mean real reserve values
     were overwritten by the zero-terminal clone)
  4. the three walked anchor policies do not reproduce LifePRO to the cent

Slot convention is 0-based duration - 1, confirmed against the live 6/30 run:
9011136641C (M/ST, issue age 22, duration 31, 25 units) read net premium 7.86 at
CNTL=03 index 0 (slot 30) and QLAdmin reported MTABNET 196.50 / MRESERVE 98.25.
"""

from __future__ import annotations

import csv
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RATES = os.path.join(ROOT, "QLA_Migration", "Output", "rates")
PLAN = "5667AT"

# LifePRO 8/31 valuation, walked to the cent in Warren's 9/16 email.
# policy, gender, class, issue age, duration, units, LifePRO reserve
ANCHORS = [
    ("9010800356C", "M", "PR", "39", 40, 200.0, 8239.00),
    ("9010768802C", "F", "PR", "28", 41, 30.0, 490.35),
    ("9010764248C", "F", "PR", "22", 41, 50.0, 474.50),
]
# Proven live: the one policy QLAdmin already valued on this plan.
LIVE_PROOF = ("9011136641C", "M", "ST", "22", 31, 25.0, 98.25)

REQUIRED_KEYS = [(g, uw, eff)
                 for g in ("M", "F") for uw in ("PR", "ST")
                 for eff in ("19000101", "19950101")]


def load(table):
    path = os.path.join(RATES, f"{table}.csv")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return [r for r in csv.DictReader(fh) if r.get("PLAN") == PLAN]


def slots(rows, pfx):
    """(gender, uwclass, effdate, age) -> {0-based slot: value}."""
    out = defaultdict(dict)
    for r in rows:
        key = (r["GENDER"], r["UWCLASS"], r["EFFDATE"], r["AGE"])
        base = int(r["CNTL"]) * 10
        for i in range(10):
            raw = (r.get(f"{pfx}{i}") or "").strip()
            try:
                out[key][base + i] = float(raw or 0)
            except ValueError:
                out[key][base + i] = 0.0
    return out


def main() -> int:
    failures: list[str] = []
    tvs, nps = load("QuikTvs"), load("QuikNps")
    if tvs is None or nps is None:
        print("FAIL: QuikTvs.csv or QuikNps.csv missing from Output/rates")
        return 1
    if not nps:
        print(f"FAIL: no QuikNps rows for {PLAN} - the #169 net premium load is gone")
        return 1

    print(f"{PLAN}: QuikTvs rows={len(tvs)}  QuikNps rows={len(nps)}")

    # 1 + 2. address coverage and required generations
    tv_addr = {(r["GENDER"], r["UWCLASS"], r["EFFDATE"], r["AGE"], r["CNTL"]) for r in tvs}
    np_addr = {(r["GENDER"], r["UWCLASS"], r["EFFDATE"], r["AGE"], r["CNTL"]) for r in nps}
    uncovered = np_addr - tv_addr
    print(f"  net-premium addresses={len(np_addr)}  without a terminal-reserve row={len(uncovered)}")
    if uncovered:
        failures.append(
            f"{len(uncovered)} QuikNps addresses have no QuikTvs row, e.g. "
            f"{sorted(uncovered)[:3]}"
        )

    tv_keys = {(r["GENDER"], r["UWCLASS"], r["EFFDATE"]) for r in tvs if r["AGE"] != "00"}
    for key in REQUIRED_KEYS:
        if key not in tv_keys:
            failures.append(f"QuikTvs missing a real (non AGE=00) grid for {key}")
    print(f"  required gender/class/generation grids present: "
          f"{sum(1 for k in REQUIRED_KEYS if k in tv_keys)}/{len(REQUIRED_KEYS)}")

    # 3. terminal factors must stay zero for an annually renewable term
    non_zero = [
        r for r in tvs
        if any((r.get(f"TV{i}") or "").strip() not in ("", ".00") for i in range(10))
    ]
    print(f"  terminal factors non-zero rows={len(non_zero)} (expected 0)")
    if non_zero:
        failures.append(
            f"{len(non_zero)} {PLAN} QuikTvs rows carry a non-.00 terminal factor"
        )

    # 4. reproduce LifePRO on the walked anchors, plus the live-proven policy
    tv_s, np_s = slots(tvs, "TV"), slots(nps, "NP")
    print("\n  reserve walk  (mean = (term(t-1) + net premium + term(t)) / 2)")
    for pol, sex, cls, age, dur, units, expect in ANCHORS + [LIVE_PROOF]:
        slot = dur - 1
        ok_any = False
        for eff in ("19000101", "19950101"):
            k = (sex, cls, eff, age)
            if k not in np_s:
                continue
            p = np_s[k].get(slot, 0.0)
            a = tv_s.get(k, {}).get(slot - 1)
            b = tv_s.get(k, {}).get(slot)
            if a is None or b is None:
                print(f"    {pol} {sex}/{cls} @{eff}: NO terminal-reserve row at slot {slot}")
                continue
            got = (a + p + b) / 2 * units
            flag = "OK" if abs(got - expect) < 0.01 else "MISMATCH"
            print(f"    {pol} {sex}/{cls} @{eff} age {age} dur {dur}: "
                  f"term={a:.2f}/{b:.2f} np={p:.2f} -> {got:,.2f} "
                  f"(LifePRO {expect:,.2f}) {flag}")
            if flag == "OK":
                ok_any = True
        if not ok_any:
            failures.append(
                f"{pol} does not reproduce LifePRO {expect:,.2f} at any generation"
            )

    print()
    if failures:
        print("FAIL:")
        for f in failures:
            print(f"  {f}")
        return 1
    print("PASS: every 667 ART net premium has a reachable terminal-reserve row, "
          "terminals are zero, and all anchors reproduce LifePRO to the cent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
