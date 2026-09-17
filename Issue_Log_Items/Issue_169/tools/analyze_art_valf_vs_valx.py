"""ART book: LifePRO VALXLIFE vs QLAdmin QuikValf on the 6/30 test region.

Also reports whether the #169 5667AT net-premium rows are actually on the
region's QuikNps / QuikPlTv (the L14 ShareFile load may not have included them).
"""
from __future__ import annotations

import collections
import csv
import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "docs", "Valuation", "analysis"))

import quikvalf_dbf as QV  # noqa: E402
import valx_layout as VL  # noqa: E402
from dbfread import DBF

QDIR = r"Q:\CSO\CSO_Test_6_30_2026"
VALF = os.path.join(QDIR, "QuikValf.dbf")
NPS = os.path.join(QDIR, "QuikNps.dbf")
PLTV = os.path.join(QDIR, "QuikPlTv.dbf")
RIDR = os.path.join(QDIR, "quikridr.dbf")
TVS = os.path.join(QDIR, "QuikTvs.dbf")
OUT = os.path.join(ROOT, "Issue_Log_Items", "Issue_169", "evidence")

ART_PLANS = {"5667AT", "5646AT", "57ATCR", "9595WP", "967ADB", "9SLADB"}
TOL = 1.00


def is_art(plan: str) -> bool:
    p = (plan or "").strip().upper()
    return p in ART_PLANS or "ART" in p or p.endswith("AT")


def _int(v) -> int:
    try:
        return int(str(v or "").strip() or 0)
    except ValueError:
        return 0


def count_plan_dbf(path: str, plan: str, prefix: str | None = None) -> dict:
    by = collections.defaultdict(lambda: {"rows": 0, "nonzero": 0})
    if not os.path.isfile(path):
        return by
    for rec in DBF(path, load=True, char_decode_errors="replace"):
        if str(rec.get("PLAN") or "").strip() != plan:
            continue
        uw = str(rec.get("UWCLASS") or "").strip()
        by[uw]["rows"] += 1
        if prefix:
            for i in range(10):
                try:
                    if float(rec.get(f"{prefix}{i}") or 0) != 0:
                        by[uw]["nonzero"] += 1
                        break
                except (TypeError, ValueError):
                    pass
        else:
            by[uw]["nonzero"] += 1
    return by


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    lines: list[str] = []

    def out(msg: str = "") -> None:
        print(msg)
        lines.append(msg)

    out("=" * 108)
    out("ART RESERVE COMPARE — LifePRO VALXLIFE vs Q:\\CSO\\CSO_Test_6_30_2026 QuikValf")
    out(f"Generated: {datetime.now():%Y-%m-%d %H:%M}")
    out(f"QuikValf mtime: {datetime.fromtimestamp(os.path.getmtime(VALF))}")
    out(f"QuikNps  mtime: {datetime.fromtimestamp(os.path.getmtime(NPS))}")
    out(f"QuikPlTv mtime: {datetime.fromtimestamp(os.path.getmtime(PLTV))}")
    out(f"LifePRO: {VL.DEFAULT_EXTRACT}  mtime={datetime.fromtimestamp(os.path.getmtime(VL.DEFAULT_EXTRACT))}")
    out("=" * 108)

    out()
    out("A) Are the #169 5667AT net-premium rows on the TEST REGION?")
    nps = count_plan_dbf(NPS, "5667AT", "NP")
    pltv = count_plan_dbf(PLTV, "5667AT")
    tvs = count_plan_dbf(TVS, "5667AT", "TV")
    out(f"  QuikNps  5667AT by UWCLASS: {dict((k, v) for k, v in nps.items())}")
    out(f"  QuikPlTv 5667AT by UWCLASS: {dict((k, v) for k, v in pltv.items())}")
    out(f"  QuikTvs  5667AT by UWCLASS: {dict((k, v) for k, v in tvs.items())}")
    nps_rows = sum(v["rows"] for v in nps.values())
    nps_nz = sum(v["nonzero"] for v in nps.values())
    if nps_rows == 0:
        out("  VERDICT: 5667AT QuikNps is EMPTY on the test region — #169 grid was not loaded.")
    else:
        out(f"  VERDICT: 5667AT QuikNps has {nps_rows} rows, {nps_nz} with a nonzero cell.")

    # repo Output for contrast
    repo_nps = os.path.join(ROOT, "QLA_Migration", "Output", "rates", "QuikNps.csv")
    repo_ct = collections.Counter()
    if os.path.isfile(repo_nps):
        with open(repo_nps, encoding="utf-8-sig", newline="") as fh:
            for rec in csv.DictReader(fh):
                if (rec.get("PLAN") or "").strip() == "5667AT":
                    repo_ct[(rec.get("UWCLASS") or "").strip()] += 1
        out(f"  Repo Output/rates/QuikNps 5667AT: {dict(repo_ct)} total={sum(repo_ct.values())}")

    valf = QV.load(VALF)
    lifepro = {}
    for rec in VL.read_records():
        lifepro[(str(rec.get("POLICY_NUMBER") or "").strip(), _int(rec.get("BENEFIT_SEQ")))] = rec

    # Discover ART plans from valf + ridr
    ridr_plans = collections.Counter()
    for rec in DBF(RIDR, load=True, char_decode_errors="replace"):
        plan = str(rec.get("MPLAN") or "").strip()
        if is_art(plan):
            ridr_plans[(plan, str(rec.get("MUWCLASS") or "").strip())] += 1

    out()
    out("B) ART / *AT riders on quikridr in the test region")
    for (plan, uw), n in sorted(ridr_plans.items()):
        out(f"  {plan:<10} {uw or '(bl)':<4} riders={n}")

    rows = []
    stats = collections.defaultdict(lambda: {
        "n": 0, "qla_nz": 0, "lp_nz": 0, "match": 0,
        "qla0": 0, "qla": 0.0, "lp": 0.0,
    })
    for row in valf.valued:
        plan = QV.plan_code(row)
        if not is_art(plan):
            continue
        lp = lifepro.get((QV.lifepro_policy(row), QV.phase_of(row)))
        lp_rv = float(lp.get("RV_MEAN_RV") or 0) if lp else 0.0
        qla = QV.money(row, "MRESERVE")
        tabnet = QV.money(row, "MTABNET")
        rec = {
            "PLAN": plan,
            "MPOLICY": QV.policy_of(row),
            "PHASE": QV.phase_of(row),
            "MCLASS": QV.text(row, "MCLASS"),
            "MAGE": _int(row.get("MAGE")),
            "MDUR": _int(row.get("MDUR")),
            "MSEX": QV.text(row, "MSEX"),
            "MUNIT": QV.money(row, "MUNIT"),
            "MTABNET": tabnet,
            "MRESERVE": qla,
            "LP_RV_MEAN_RV": lp_rv,
            "DIFF": qla - lp_rv,
            "IN_VALX": "Y" if lp else "N",
            "MPLAN": QV.text(row, "MPLAN"),
        }
        rows.append(rec)
        s = stats[plan]
        s["n"] += 1
        s["qla"] += qla
        s["lp"] += lp_rv
        if qla:
            s["qla_nz"] += 1
        if lp_rv:
            s["lp_nz"] += 1
        if abs(qla - lp_rv) <= TOL:
            s["match"] += 1
        if qla == 0 and lp_rv:
            s["qla0"] += 1

    csv_path = os.path.join(OUT, f"art_policy_listing_{stamp}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["PLAN"])
        wr.writeheader()
        wr.writerows(sorted(rows, key=lambda r: (r["PLAN"], r["MPOLICY"], r["PHASE"])))

    out()
    out("C) QUIKVALF vs LIFEPRO by ART plan  ($1 tol)")
    out("-" * 108)
    out(
        f"{'PLAN':<10}{'ROWS':>5}{'QLA nz':>8}{'LP nz':>6}{'MATCH':>6}"
        f"{'QLA$0 LP>0':>12}{'QLA reserve':>14}{'LP reserve':>14}{'diff':>12}"
    )
    for plan, s in sorted(stats.items()):
        out(
            f"{plan:<10}{s['n']:>5}{s['qla_nz']:>8}{s['lp_nz']:>6}{s['match']:>6}"
            f"{s['qla0']:>12}{s['qla']:>14,.2f}{s['lp']:>14,.2f}{s['qla']-s['lp']:>12,.2f}"
        )

    # Named Issue 169 anchors
    anchors = {
        "9010800356C": 8239.00,
        "9010837136C": 6954.00,
        "9010816232C": 6312.50,
        "9010844919C": 4855.00,
        "9010777321C": 4285.00,
        "9010773561C": 3790.50,
        "9010768802C": 490.35,
        "9010764248C": 474.50,
        "9010764158C": 181.87,
        "9010886099C": None,  # zero units exception
    }
    out()
    out("D) Issue #169 named anchors on this morning's (or current) QuikValf")
    for row in valf.valued:
        pol = QV.policy_of(row)
        if pol not in anchors or QV.plan_code(row) != "5667AT":
            continue
        exp = anchors[pol]
        qla = QV.money(row, "MRESERVE")
        if exp is None:
            out(
                f"  {pol} phase={QV.phase_of(row)} units={QV.money(row,'MUNIT'):.2f} "
                f"MTABNET={QV.money(row,'MTABNET'):.2f} MRESERVE={qla:.2f}  (zero-units exception)"
            )
        else:
            ok = abs(qla - exp) <= TOL
            out(
                f"  {pol} units={QV.money(row,'MUNIT'):.2f} MRESERVE={qla:,.2f} "
                f"expected={exp:,.2f} MTABNET={QV.money(row,'MTABNET'):.2f}  {'PASS' if ok else 'FAIL'}"
            )

    zeros = [r for r in rows if r["MRESERVE"] == 0 and r["LP_RV_MEAN_RV"]]
    out()
    out(f"E) ART rows QLA $0 / LifePRO > 0: {len(zeros)}")
    byp = collections.Counter(r["PLAN"] for r in zeros)
    for plan, n in sorted(byp.items()):
        dollars = sum(r["LP_RV_MEAN_RV"] for r in zeros if r["PLAN"] == plan)
        out(f"  {plan}: {n} rows  LifePRO ${dollars:,.2f}")

    out()
    out(f"Full policy listing: {csv_path}")
    report = os.path.join(OUT, f"art_valf_vs_valx_{stamp}.txt")
    with open(report, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    out(f"Report: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
