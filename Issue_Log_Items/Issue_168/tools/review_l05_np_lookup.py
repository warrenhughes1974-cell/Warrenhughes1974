"""Issue #168 independent review, part 3.

1) Why does MTABNET land for 5 of 9 L05 policies and not the other 4?
   Dumps the full QuikNps duration strip for the exact (age, gender, class) each
   L05 / L01 policy reads, next to what QLAdmin actually stored in MTABNET.

2) Airtight version of the UWCLASS=00 fallback proof: plans whose reserve grid sits
   only at UWCLASS=00 AND which have no usable net premium, yet still valued -> the
   reserve can only have come from the 00 grid.

3) What LifePRO itself reports for net premium on the L05 policies that QLAdmin
   zeroed, to separate "LifePRO has no net premium" from "QLAdmin missed the lookup".

Read-only.
"""
from __future__ import annotations

import collections
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "docs", "Valuation", "analysis"))

import quikvalf_dbf as QV  # noqa: E402
import valx_layout as VL  # noqa: E402

RATES = os.path.join(ROOT, "QLA_Migration", "Output", "rates")
L05_L01 = {"5L0510", "5L0110", "5L01MA", "5L075Y"}


def load_strips(fn: str, prefix: str) -> dict:
    strips: dict = collections.defaultdict(dict)
    with open(os.path.join(RATES, fn), encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            plan = (row.get("PLAN") or "").strip()
            try:
                age = int((row.get("AGE") or "0").strip() or 0)
                page = int((row.get("CNTL") or "0").strip() or 0)
            except ValueError:
                continue
            key = (plan, age, (row.get("GENDER") or "").strip(), (row.get("UWCLASS") or "").strip())
            for i in range(10):
                raw = (row.get(f"{prefix}{i}") or "").strip()
                if raw == "":
                    continue
                try:
                    strips[key][page * 10 + i] = float(raw)
                except ValueError:
                    pass
    return strips


def main() -> int:
    nps = load_strips("QuikNps.csv", "NP")
    tvs = load_strips("QuikTvs.csv", "TV")

    valf = QV.load()

    lifepro = {}
    for rec in VL.read_records():
        try:
            seq = int(str(rec.get("BENEFIT_SEQ") or "").strip())
        except ValueError:
            seq = -1
        lifepro[(str(rec.get("POLICY_NUMBER") or "").strip(), seq)] = rec

    # VALX net-premium-ish fields
    cand = [f.name for f in VL.FIELDS if "NET" in f.name or "PREM" in f.name]
    print("VALXLIFE fields mentioning NET/PREM:", cand)
    print()

    print("=" * 120)
    print("1) L05 / L01 net-premium lookup: QuikNps duration strip vs what QLAdmin stored")
    print("=" * 120)
    for row in sorted(valf.valued, key=lambda r: (QV.plan_code(r), int(r.get("MDUR") or 0))):
        plan = QV.plan_code(row)
        if plan not in L05_L01:
            continue
        age = int(row.get("MAGE") or 0)
        dur = int(row.get("MDUR") or 0)
        sex = QV.text(row, "MSEX")
        cls = QV.text(row, "MCLASS")
        units = QV.money(row, "MUNIT")
        tabnet = QV.money(row, "MTABNET")
        strip = nps.get((plan, age, sex, cls), {})
        nonzero = sorted(d for d, v in strip.items() if v)
        span = f"{nonzero[0]}-{nonzero[-1]}" if nonzero else "none"
        lp = lifepro.get((QV.lifepro_policy(row), QV.phase_of(row)))
        lp_bits = ""
        if lp:
            lp_bits = " ".join(f"{c}={lp.get(c)}" for c in cand if lp.get(c) not in (None, 0, "", "0"))
        implied = (tabnet / units) if units else 0.0
        print(
            f"{plan} {QV.policy_of(row):<12} age={age:<3} dur={dur:<3} {sex} {cls:<3} "
            f"units={units:<8.2f} MTABNET={tabnet:<9.2f} (per unit {implied:>7.2f})  "
            f"NP nonzero durs={span:<10} NP[dur]={strip.get(dur)} NP[dur-1]={strip.get(dur-1)}"
        )
        if lp_bits:
            print(f"      LifePRO: {lp_bits}")

    print()
    print("=" * 120)
    print("2) Airtight fallback proof: reserve grid only at UWCLASS=00, policy class != 00, MTABNET == 0")
    print("   -> a nonzero MRESERVE can only have come from the UWCLASS=00 grid.")
    print("=" * 120)
    tv_classes = collections.defaultdict(set)
    tv_nonzero = collections.defaultdict(bool)
    for (plan, _age, _g, uw), strip in tvs.items():
        tv_classes[plan].add(uw)
        if any(strip.values()):
            tv_nonzero[(plan, uw)] = True

    print(f"{'PLAN':<9}{'POLICY':<13}{'CLS':<5}{'MTABNET':>10}{'MRESERVE':>11}{'LP RV':>11}  verdict")
    print("-" * 120)
    proofs = 0
    for row in valf.valued:
        plan = QV.plan_code(row)
        cls = QV.text(row, "MCLASS")
        if tv_classes.get(plan) != {"00"} or cls in ("00", ""):
            continue
        if not tv_nonzero.get((plan, "00")):
            continue
        tabnet = QV.money(row, "MTABNET")
        res = QV.money(row, "MRESERVE")
        if tabnet != 0 or res == 0:
            continue
        lp = lifepro.get((QV.lifepro_policy(row), QV.phase_of(row)))
        lp_rv = 0.0
        if lp:
            try:
                lp_rv = float(lp.get("RV_MEAN_RV") or 0)
            except (TypeError, ValueError):
                lp_rv = 0.0
        proofs += 1
        print(
            f"{plan:<9}{QV.policy_of(row):<13}{cls:<5}{tabnet:>10.2f}{res:>11.2f}{lp_rv:>11.2f}"
            f"  valued off the 00 grid"
        )
    print(f"\n  qualifying proof policies: {proofs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
