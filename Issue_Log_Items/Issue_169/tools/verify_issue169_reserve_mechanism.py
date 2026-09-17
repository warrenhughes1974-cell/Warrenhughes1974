"""Issue #169 independent validation (Opus, 2026-09-15).

Tests the claims in the #169 Discovery/Planning/Risk documents against QLAdmin's
own valuation output and LifePRO's, rather than against the static rate tables.

Question the #169 plan never asked: for these plans, is the reserve driven by the
terminal-reserve grid (QuikTvs) at all, or by the net valuation premium (QuikNps
-> MTABNET)? Issue #168's independent review established that for 901ADB / 996ADB
the 00-keyed TV grid is never read and MRESERVE = MTABNET / 2. If that holds, a
QuikTvs class-replication fix on those plans changes nothing.

Read-only.
"""
from __future__ import annotations

import collections
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "docs", "Valuation", "analysis"))

import quikvalf_dbf as QV  # noqa: E402
import valx_layout as VL  # noqa: E402

TARGETS = {
    "196085": "960 LP85-M (base)",
    "7619PU": "619 SPS PU (base)",
    "5667AT": "667 ART (base)",
    "9595WP": "1595 WP rider",
    "901ADB": "1596 L01 ADB rider",
    "996ADB": "1596 bare ADB rider",
    "967ADB": "1596 667 ADB rider",
    "9SLADB": "SAL ADB rider",
}


def main() -> int:
    valf = QV.load()

    lifepro = {}
    for rec in VL.read_records():
        pol = str(rec.get("POLICY_NUMBER") or "").strip()
        seq = str(rec.get("BENEFIT_SEQ") or "").strip()
        try:
            seq_i = int(seq)
        except ValueError:
            seq_i = 0
        lifepro[(pol, seq_i)] = rec

    stats = collections.defaultdict(
        lambda: {
            "rows": 0,
            "qla_res_nz": 0,
            "tabnet_nz": 0,
            "qla_sum": 0.0,
            "lp_sum": 0.0,
            "lp_nz": 0,
            "halfnet_match": 0,
            "halfnet_tested": 0,
        }
    )

    for row in valf.valued:
        plan = QV.plan_code(row)
        if plan not in TARGETS:
            continue
        s = stats[plan]
        s["rows"] += 1
        res = QV.money(row, "MRESERVE")
        tabnet = QV.money(row, "MTABNET")
        s["qla_sum"] += res
        if res:
            s["qla_res_nz"] += 1
        if tabnet:
            s["tabnet_nz"] += 1
        # does MRESERVE == MTABNET / 2 (net-premium-driven reserve)?
        if res or tabnet:
            s["halfnet_tested"] += 1
            if abs(res - tabnet / 2.0) <= 0.02:
                s["halfnet_match"] += 1

        lp = lifepro.get((QV.lifepro_policy(row), QV.phase_of(row)))
        lp_res = 0.0
        if lp:
            try:
                lp_res = float(lp.get("RV_MEAN_RV") or 0)
            except (TypeError, ValueError):
                lp_res = 0.0
        s["lp_sum"] += lp_res
        if lp_res:
            s["lp_nz"] += 1

    print("=" * 118)
    print("QuikValf (9/2 run, 6/30/2026 valuation) vs LifePRO VALXLIFE — issue #169 plans")
    print("=" * 118)
    header = (
        f"{'PLAN':<8}{'WHAT':<24}{'ROWS':>5}{'QLA res nz':>11}{'MTABNET nz':>11}"
        f"{'LP res nz':>10}{'QLA total':>13}{'LP total':>13}{'res==net/2':>12}"
    )
    print(header)
    print("-" * 118)
    for plan in TARGETS:
        s = stats.get(plan)
        if not s:
            print(f"{plan:<8}{TARGETS[plan]:<24}{'-- no rows in QuikValf --':>60}")
            continue
        ratio = f"{s['halfnet_match']}/{s['halfnet_tested']}"
        print(
            f"{plan:<8}{TARGETS[plan]:<24}{s['rows']:>5}{s['qla_res_nz']:>11}"
            f"{s['tabnet_nz']:>11}{s['lp_nz']:>10}{s['qla_sum']:>13,.2f}"
            f"{s['lp_sum']:>13,.2f}{ratio:>12}"
        )
    print()
    print("res==net/2 = rows where MRESERVE equals MTABNET/2 within 2 cents")
    print("            (the signature of a net-premium-driven reserve, i.e. the TV grid is not read)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
