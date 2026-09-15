"""Issue #168 independent review: does QLAdmin require an exact UWCLASS match on the
terminal-reserve grid, or does it fall back to the UWCLASS=00 default key?

The answer decides the SHAPE of the L14 fix:
  * exact-match required  -> replicate the one real NT grid onto PQ/ST/PR
  * falls back to 00      -> emit the one real grid at UWCLASS=00 (far smaller, and
                             consistent with UWVARYTV=N)

Natural experiment already in the data: 9L01WP and 5L0110 carry policies in PR/ST
but their QuikTvs rows sit only at UWCLASS=00. 9L01WP's 00 rows are NON-ZERO, so if
those policies value correctly in QuikValf, QLAdmin fell back to 00.

Also reports, per L plan, LifePRO RV_MEAN_RV vs QLAdmin MRESERVE so the L05 term
family can be separated into "legitimately zero" and "reserve carried by net premium".

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

OUT = os.path.join(ROOT, "QLA_Migration", "Output")

TARGET_PLANS = {
    "5L0510", "9L05WP",           # L05
    "1L14SC",                     # L14
    "5L0110", "5L01MA", "9L01WP",  # L01 - same term family as L05
    "5L075Y",                     # L07 - same term family
    "1L1095", "1L10OD", "1L10SO", "1L10SR",  # L10 controls (known working)
    "1L15GD", "1L16GD", "1L17SP", "10L171", "10L172",
}


def _int(value) -> int:
    text = str(value or "").strip()
    try:
        return int(text)
    except ValueError:
        return -1


def load_ridr_class() -> dict:
    """policy(+phase) -> (plan, uwclass) from quikridr."""
    by_policy = {}
    path = os.path.join(OUT, "quikridr.csv")
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            plan = (row.get("MPLAN") or "").strip()
            if plan not in TARGET_PLANS:
                continue
            pol = (row.get("MPOLICY") or "").strip()
            by_policy[(pol, _int(row.get("MPHASE")))] = (
                plan,
                (row.get("MUWCLASS") or "").strip(),
            )
    return by_policy


def main() -> int:
    ridr = load_ridr_class()
    print(f"quikridr rows on target plans: {len(ridr)}")

    # ---- LifePRO side -------------------------------------------------------
    lifepro = {}
    for rec in VL.read_records():
        pol = str(rec.get("POLICY_NUMBER") or "").strip()
        lifepro[(pol, _int(rec.get("BENEFIT_SEQ")))] = rec

    # ---- QLAdmin side -------------------------------------------------------
    valf = QV.load()
    rows = valf.valued

    stats = collections.defaultdict(
        lambda: {"n": 0, "qla_nz": 0, "lp_nz": 0, "qla_sum": 0.0, "lp_sum": 0.0, "tabnet_nz": 0}
    )

    for row in rows:
        plan = QV.plan_code(row)
        if plan not in TARGET_PLANS:
            continue
        pol = QV.lifepro_policy(row)
        phase = QV.phase_of(row)
        uw = ridr.get((QV.policy_of(row), phase), (plan, "?"))[1]
        res = QV.money(row, "MRESERVE")
        tabnet = QV.money(row, "MTABNET")

        lp = lifepro.get((pol, phase))
        lp_res = 0.0
        if lp:
            try:
                lp_res = float(lp.get("RV_MEAN_RV") or 0)
            except (TypeError, ValueError):
                lp_res = 0.0

        s = stats[(plan, uw)]
        s["n"] += 1
        s["qla_sum"] += res
        s["lp_sum"] += lp_res
        if res:
            s["qla_nz"] += 1
        if lp_res:
            s["lp_nz"] += 1
        if tabnet:
            s["tabnet_nz"] += 1

    print()
    print("=" * 104)
    print("QLAdmin QuikValf vs LifePRO VALXLIFE, by plan x policy UW class")
    print("=" * 104)
    print(
        f"{'PLAN':<9}{'UW':<5}{'ROWS':>6}{'QLA nz':>8}{'LP nz':>7}{'TABNET nz':>11}"
        f"{'QLA reserve':>16}{'LP reserve':>16}{'diff':>14}"
    )
    print("-" * 104)
    for (plan, uw) in sorted(stats):
        s = stats[(plan, uw)]
        print(
            f"{plan:<9}{uw or '(bl)':<5}{s['n']:>6}{s['qla_nz']:>8}{s['lp_nz']:>7}"
            f"{s['tabnet_nz']:>11}{s['qla_sum']:>16,.2f}{s['lp_sum']:>16,.2f}"
            f"{s['qla_sum'] - s['lp_sum']:>14,.2f}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
