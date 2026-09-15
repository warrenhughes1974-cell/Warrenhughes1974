"""Issue #168 independent review, part 2.

A) L05 / L01 / L07 policy-level detail. These three are the same LifePRO term
   family: their stored terminal-reserve (RV) grids are ALL ZERO in source, so the
   reserve is carried by the net premium. L07 matches LifePRO to ~$1; L05 matches
   5 of 9; L01 matches 0 of 124. This dumps the actual lookup cell each policy
   lands on so the discriminator is visible.

B) Book-wide test of whether QLAdmin falls back to the UWCLASS=00 default grid.
   Finds every plan where the emitted terminal-reserve rows sit only at UWCLASS=00
   while policies carry a non-00 class, and reports whether those policies valued.

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

TERM_FAMILY = ["5L0510", "9L05WP", "5L0110", "5L01MA", "5L075Y", "1L14SC"]


def load_grid(fn: str, prefix: str) -> dict:
    """(PLAN, AGE, GENDER, UWCLASS) -> {duration: value}"""
    grid: dict = collections.defaultdict(dict)
    path = os.path.join(RATES, fn)
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rd = csv.DictReader(fh)
        for row in rd:
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
                    grid[key][page * 10 + i] = float(raw)
                except ValueError:
                    pass
    return grid


def cell(grid: dict, plan: str, age: int, gender: str, uw: str, dur: int):
    """Return (value, key_used) trying exact class then the 00 default."""
    for candidate in (uw, "00", ""):
        key = (plan, age, gender, candidate)
        if key in grid:
            return grid[key].get(dur), candidate or "(blank)"
    return None, "NO ROW"


def part_a(valf, lifepro) -> None:
    tvs = load_grid("QuikTvs.csv", "TV")
    nps = load_grid("QuikNps.csv", "NP")

    print("=" * 128)
    print("A) TERM FAMILY POLICY DETAIL  (LifePRO RV grid is all zero for L01/L05/L07 -> reserve rides on net premium)")
    print("=" * 128)
    print(
        f"{'PLAN':<8}{'POLICY':<12}{'PH':>3}{'AGE':>4}{'DUR':>4}{'SX':>3}{'CLS':>4}"
        f"{'UNITS':>10}{'MTABNET':>10}{'MMEAN':>9}{'MRESERVE':>11}{'LP RV_MEAN':>12}"
        f"{'  NP cell(key)':<20}{'TV cell(key)':<18}"
    )
    print("-" * 128)
    for row in sorted(valf.valued, key=lambda r: (QV.plan_code(r), QV.policy_of(r))):
        plan = QV.plan_code(row)
        if plan not in TERM_FAMILY:
            continue
        age = int(row.get("MAGE") or 0)
        dur = int(row.get("MDUR") or 0)
        sex = QV.text(row, "MSEX")
        cls = QV.text(row, "MCLASS")
        lp = lifepro.get((QV.lifepro_policy(row), QV.phase_of(row)))
        lp_rv = 0.0
        if lp:
            try:
                lp_rv = float(lp.get("RV_MEAN_RV") or 0)
            except (TypeError, ValueError):
                lp_rv = 0.0
        npv, npk = cell(nps, plan, age, sex, cls, dur)
        tvv, tvk = cell(tvs, plan, age, sex, cls, dur)
        print(
            f"{plan:<8}{QV.policy_of(row):<12}{QV.phase_of(row):>3}{age:>4}{dur:>4}{sex:>3}{cls:>4}"
            f"{QV.money(row,'MUNIT'):>10.3f}{QV.money(row,'MTABNET'):>10.2f}"
            f"{QV.money(row,'MMEAN'):>9.2f}{QV.money(row,'MRESERVE'):>11.2f}{lp_rv:>12.2f}"
            f"  {str(npv):<8}{npk:<10}{str(tvv):<8}{tvk:<10}"
        )


def part_b(valf, lifepro) -> None:
    # policy classes per plan straight off QuikValf (MCLASS is what QLAdmin valued with)
    tv_classes = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    path = os.path.join(RATES, "QuikTvs.csv")
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            plan = (row.get("PLAN") or "").strip()
            uw = (row.get("UWCLASS") or "").strip()
            slot = tv_classes[plan][uw]
            slot[0] += 1
            for i in range(10):
                try:
                    if float(row.get(f"TV{i}") or 0) != 0.0:
                        slot[1] += 1
                        break
                except ValueError:
                    pass

    per_plan_class = collections.defaultdict(lambda: {"n": 0, "nz": 0, "qla": 0.0, "lp": 0.0})
    for row in valf.valued:
        plan = QV.plan_code(row)
        cls = QV.text(row, "MCLASS")
        lp = lifepro.get((QV.lifepro_policy(row), QV.phase_of(row)))
        lp_rv = 0.0
        if lp:
            try:
                lp_rv = float(lp.get("RV_MEAN_RV") or 0)
            except (TypeError, ValueError):
                lp_rv = 0.0
        s = per_plan_class[(plan, cls)]
        s["n"] += 1
        s["qla"] += QV.money(row, "MRESERVE")
        s["lp"] += lp_rv
        if QV.money(row, "MRESERVE"):
            s["nz"] += 1

    print()
    print("=" * 118)
    print("B) FALLBACK TEST - plans whose terminal-reserve grid sits ONLY at UWCLASS=00 (nonzero) while policies")
    print("   carry a non-00 class. If those policies valued, QLAdmin used the 00 default grid.")
    print("=" * 118)
    print(f"{'PLAN':<9}{'POL CLS':<9}{'ROWS':>6}{'QLA nz':>8}{'QLA reserve':>15}{'LP reserve':>15}{'ratio':>9}")
    print("-" * 118)
    hits = 0
    for (plan, cls), s in sorted(per_plan_class.items()):
        classes = tv_classes.get(plan)
        if not classes:
            continue
        if set(classes) != {"00"}:
            continue
        if classes["00"][1] == 0:  # 00 grid is all zero -> proves nothing
            continue
        if cls in ("00", ""):
            continue
        hits += 1
        ratio = (s["qla"] / s["lp"]) if s["lp"] else float("nan")
        print(
            f"{plan:<9}{cls:<9}{s['n']:>6}{s['nz']:>8}{s['qla']:>15,.2f}{s['lp']:>15,.2f}{ratio:>9.3f}"
        )
    if not hits:
        print("  (no qualifying plan found)")

    print()
    print("=" * 118)
    print("C) CONVERSE - plans whose grid has class rows but NOT the policy's class, and no 00 row")
    print("=" * 118)
    print(f"{'PLAN':<9}{'POL CLS':<9}{'GRID CLASSES':<24}{'ROWS':>6}{'QLA nz':>8}{'QLA reserve':>15}{'LP reserve':>15}")
    print("-" * 118)
    for (plan, cls), s in sorted(per_plan_class.items()):
        classes = tv_classes.get(plan)
        if not classes or cls in ("00", ""):
            continue
        if cls in classes or "00" in classes:
            continue
        grid_desc = ",".join(f"{k}:{v[0]}/{v[1]}" for k, v in sorted(classes.items()))
        print(
            f"{plan:<9}{cls:<9}{grid_desc:<24}{s['n']:>6}{s['nz']:>8}{s['qla']:>15,.2f}{s['lp']:>15,.2f}"
        )


def main() -> int:
    lifepro = {}
    for rec in VL.read_records():
        pol = str(rec.get("POLICY_NUMBER") or "").strip()
        seq = str(rec.get("BENEFIT_SEQ") or "").strip()
        try:
            seq_i = int(seq)
        except ValueError:
            seq_i = -1
        lifepro[(pol, seq_i)] = rec

    valf = QV.load()
    part_a(valf, lifepro)
    part_b(valf, lifepro)
    return 0


if __name__ == "__main__":
    sys.exit(main())
