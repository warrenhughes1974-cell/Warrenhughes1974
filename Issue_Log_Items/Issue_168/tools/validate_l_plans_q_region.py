"""Comprehensive L-plan reserve validation against the 6/30 test region.

Reads (user-granted):
  Q:\\CSO\\CSO_Test_6_30_2026\\QuikValf.dbf
  Q:\\CSO\\CSO_Test_6_30_2026\\QuikTvs.dbf
  Q:\\CSO\\CSO_Test_6_30_2026\\QuikNps.dbf
  Q:\\CSO\\CSO_Test_6_30_2026\\quikridr.dbf

Compares valued QuikValf rows to docs/Valuation/VALXLIFE.TXT (6/30 LifePRO).
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
TVS = os.path.join(QDIR, "QuikTvs.dbf")
NPS = os.path.join(QDIR, "QuikNps.dbf")
RIDR = os.path.join(QDIR, "quikridr.dbf")
OUT_DIR = os.path.join(ROOT, "Issue_Log_Items", "Issue_168", "evidence")
TOL = 1.00  # dollar tolerance for "matches"


def is_l_plan(plan: str) -> bool:
    p = (plan or "").strip().upper()
    return "L0" in p[:4] or "L1" in p[:4]


def _int(value) -> int:
    try:
        return int(str(value or "").strip() or 0)
    except ValueError:
        return 0


def load_factor_dbf(path: str, prefix: str) -> dict:
    """(PLAN, UWCLASS) -> {rows, nonzero_rows} and (PLAN, UWCLASS, AGE, GENDER) set."""
    by = collections.defaultdict(lambda: {"rows": 0, "nonzero": 0})
    keys = collections.defaultdict(set)
    for rec in DBF(path, load=True, char_decode_errors="replace"):
        plan = str(rec.get("PLAN") or "").strip()
        if not is_l_plan(plan):
            continue
        uw = str(rec.get("UWCLASS") or "").strip()
        gender = str(rec.get("GENDER") or "").strip()
        age = _int(rec.get("AGE"))
        slot = by[(plan, uw)]
        slot["rows"] += 1
        nz = False
        for i in range(10):
            try:
                if float(rec.get(f"{prefix}{i}") or 0) != 0.0:
                    nz = True
                    break
            except (TypeError, ValueError):
                pass
        if nz:
            slot["nonzero"] += 1
        keys[(plan, uw)].add((age, gender))
    return by, keys


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    lines: list[str] = []

    def out(msg: str = "") -> None:
        print(msg)
        lines.append(msg)

    out("=" * 100)
    out("L-PLAN RESERVE VALIDATION — Q:\\CSO\\CSO_Test_6_30_2026")
    out(f"Generated: {datetime.now():%Y-%m-%d %H:%M}")
    out(f"QuikValf: {VALF}  mtime={datetime.fromtimestamp(os.path.getmtime(VALF))}")
    out(f"QuikTvs:  mtime={datetime.fromtimestamp(os.path.getmtime(TVS))}")
    out(f"QuikNps:  mtime={datetime.fromtimestamp(os.path.getmtime(NPS))}")
    out(f"LifePRO:  {VL.DEFAULT_EXTRACT}")
    out("=" * 100)

    tvs, tvs_keys = load_factor_dbf(TVS, "TV")
    nps, nps_keys = load_factor_dbf(NPS, "NP")

    # Rider classes in the test region
    ridr_cls = collections.Counter()
    for rec in DBF(RIDR, load=True, char_decode_errors="replace"):
        plan = str(rec.get("MPLAN") or "").strip()
        if not is_l_plan(plan):
            continue
        ridr_cls[(plan, str(rec.get("MUWCLASS") or "").strip())] += 1

    out()
    out("A) RATE TABLES ON THE TEST REGION — does each L plan have reserve / net-premium rows?")
    out("-" * 100)
    out(f"{'PLAN':<10}{'POLICIES (ridr class)':<36}{'QuikTvs class rows/nonzero':<40}{'QuikNps class rows/nonzero'}")
    rate_plans = sorted({p for p, _ in tvs} | {p for p, _ in nps} | {p for p, _ in ridr_cls})
    missing_tv = []
    missing_np = []
    for plan in rate_plans:
        pol = ", ".join(f"{uw or '(bl)'}={n}" for (p, uw), n in sorted(ridr_cls.items()) if p == plan) or "-"

        def fmt(agg):
            bits = []
            for (p, uw), v in sorted(agg.items()):
                if p != plan:
                    continue
                bits.append(f"{uw or '(bl)'}={v['rows']}/{v['nonzero']}")
            return ", ".join(bits) or "NONE"

        tv_s = fmt(tvs)
        np_s = fmt(nps)
        out(f"{plan:<10}{pol:<36}{tv_s:<40}{np_s}")
        pol_classes = {uw for (p, uw) in ridr_cls if p == plan and uw}
        tv_classes = {uw for (p, uw) in tvs if p == plan}
        np_classes = {uw for (p, uw) in nps if p == plan}
        # A class is covered if exact match OR a 00 default grid exists
        for uw in pol_classes:
            if uw not in tv_classes and "00" not in tv_classes:
                missing_tv.append((plan, uw))
            if uw not in np_classes and "00" not in np_classes:
                missing_np.append((plan, uw))

    out()
    out("A1) Policy classes with NO QuikTvs key (and no UWCLASS=00 fallback):")
    if missing_tv:
        for plan, uw in missing_tv:
            out(f"    FAIL  {plan}  class {uw}")
    else:
        out("    none")
    out("A2) Policy classes with NO QuikNps key (and no UWCLASS=00 fallback):")
    if missing_np:
        for plan, uw in missing_np:
            out(f"    FAIL  {plan}  class {uw}")
    else:
        out("    none")

    # ---- QuikValf vs LifePRO ------------------------------------------------
    valf = QV.load(VALF)
    lifepro = {}
    for rec in VL.read_records():
        pol = str(rec.get("POLICY_NUMBER") or "").strip()
        lifepro[(pol, _int(rec.get("BENEFIT_SEQ")))] = rec

    stats = collections.defaultdict(
        lambda: {
            "n": 0,
            "qla_nz": 0,
            "lp_nz": 0,
            "qla": 0.0,
            "lp": 0.0,
            "match": 0,
            "qla_zero_lp_nz": 0,
            "lp_zero_qla_nz": 0,
            "off": 0,
        }
    )
    zeros = []  # QLA 0, LifePRO nonzero
    mismatches = []
    l14_detail = []

    for row in valf.valued:
        plan = QV.plan_code(row)
        if not is_l_plan(plan):
            continue
        cls = QV.text(row, "MCLASS")
        qla = QV.money(row, "MRESERVE")
        tabnet = QV.money(row, "MTABNET")
        lp = lifepro.get((QV.lifepro_policy(row), QV.phase_of(row)))
        lp_rv = 0.0
        if lp:
            try:
                lp_rv = float(lp.get("RV_MEAN_RV") or 0)
            except (TypeError, ValueError):
                lp_rv = 0.0
        s = stats[(plan, cls)]
        s["n"] += 1
        s["qla"] += qla
        s["lp"] += lp_rv
        if qla:
            s["qla_nz"] += 1
        if lp_rv:
            s["lp_nz"] += 1
        diff = qla - lp_rv
        if abs(diff) <= TOL:
            s["match"] += 1
        elif qla == 0 and lp_rv:
            s["qla_zero_lp_nz"] += 1
            zeros.append((plan, cls, QV.policy_of(row), QV.phase_of(row), qla, lp_rv, tabnet))
        elif lp_rv == 0 and qla:
            s["lp_zero_qla_nz"] += 1
        else:
            s["off"] += 1
            mismatches.append((plan, cls, QV.policy_of(row), qla, lp_rv, diff))
        if plan == "1L14SC":
            l14_detail.append((cls, QV.policy_of(row), qla, lp_rv, tabnet, abs(diff) <= TOL))

    out()
    out("B) QUIKVALF vs LIFEPRO 6/30  (valued rows only, MRESERVE vs RV_MEAN_RV, $1 tol)")
    out("-" * 100)
    out(
        f"{'PLAN':<9}{'CLS':<5}{'ROWS':>5}{'QLA nz':>7}{'LP nz':>6}{'MATCH':>6}"
        f"{'QLA$0 LP>0':>12}{'QLA reserve':>14}{'LP reserve':>14}{'diff':>12}"
    )
    tot = collections.Counter()
    for key in sorted(stats):
        s = stats[key]
        plan, cls = key
        d = s["qla"] - s["lp"]
        out(
            f"{plan:<9}{cls or '(bl)':<5}{s['n']:>5}{s['qla_nz']:>7}{s['lp_nz']:>6}{s['match']:>6}"
            f"{s['qla_zero_lp_nz']:>12}{s['qla']:>14,.2f}{s['lp']:>14,.2f}{d:>12,.2f}"
        )
        tot["n"] += s["n"]
        tot["qla_nz"] += s["qla_nz"]
        tot["lp_nz"] += s["lp_nz"]
        tot["match"] += s["match"]
        tot["zero"] += s["qla_zero_lp_nz"]
        tot["qla"] += s["qla"]
        tot["lp"] += s["lp"]
    out("-" * 100)
    out(
        f"{'TOTAL':<9}{'':<5}{tot['n']:>5}{tot['qla_nz']:>7}{tot['lp_nz']:>6}{tot['match']:>6}"
        f"{tot['zero']:>12}{tot['qla']:>14,.2f}{tot['lp']:>14,.2f}{tot['qla']-tot['lp']:>12,.2f}"
    )

    out()
    out("C) L14 (1L14SC) — the #168 fix. PQ/PR/ST must no longer be $0.")
    out("-" * 100)
    l14_by = collections.defaultdict(lambda: [0, 0, 0.0, 0.0])
    for cls, pol, qla, lp_rv, tabnet, ok in l14_detail:
        b = l14_by[cls]
        b[0] += 1
        b[1] += 1 if ok else 0
        b[2] += qla
        b[3] += lp_rv
    for cls in ("NT", "PQ", "PR", "ST"):
        n, ok, qla, lp_rv = l14_by.get(cls, [0, 0, 0.0, 0.0])
        verdict = "PASS" if n and ok == n else ("FAIL" if n else "NO ROWS")
        out(f"  {cls}: rows={n} match={ok}  QLA={qla:,.2f}  LP={lp_rv:,.2f}  {verdict}")

    # Named traces
    want = {
        "9011227604C": 9895.80,
        "9011258186C": 9543.45,
        "9011226092C": 9895.80,
    }
    out()
    out("C1) Named L14 traces")
    for row in valf.valued:
        pol = QV.policy_of(row)
        if pol not in want:
            continue
        qla = QV.money(row, "MRESERVE")
        exp = want[pol]
        ok = abs(qla - exp) <= TOL
        out(f"  {pol} class={QV.text(row,'MCLASS')}  MRESERVE={qla:,.2f}  expected={exp:,.2f}  {'PASS' if ok else 'FAIL'}")

    out()
    out("D) ALL L-plan rows where QLAdmin reserve is $0 and LifePRO is not")
    out("-" * 100)
    zero_path = os.path.join(OUT_DIR, f"l_plan_qla_zero_vs_lifepro_{stamp}.csv")
    with open(zero_path, "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["PLAN", "MCLASS", "MPOLICY", "PHASE", "MRESERVE", "LP_RV_MEAN_RV", "MTABNET"])
        for rec in zeros:
            wr.writerow(rec)
    by_plan = collections.Counter((z[0], z[1]) for z in zeros)
    if not zeros:
        out("  none — every L-plan LifePRO reserve has a QLAdmin reserve")
    else:
        out(f"  {len(zeros)} rows  (detail: {zero_path})")
        for (plan, cls), n in sorted(by_plan.items()):
            dollars = sum(z[5] for z in zeros if z[0] == plan and z[1] == cls)
            out(f"    {plan} {cls}: {n} rows  LifePRO ${dollars:,.2f}")

    out()
    out("E) Valued but off by more than $1 (both sides nonzero)")
    out("-" * 100)
    if not mismatches:
        out("  none")
    else:
        byp = collections.defaultdict(lambda: [0, 0.0])
        for plan, cls, pol, qla, lp_rv, diff in mismatches:
            byp[(plan, cls)][0] += 1
            byp[(plan, cls)][1] += diff
        for (plan, cls), (n, d) in sorted(byp.items()):
            out(f"    {plan} {cls}: {n} rows  net diff ${d:,.2f}")
        out("    first 15:")
        for rec in mismatches[:15]:
            out(f"      {rec[0]} {rec[1]} {rec[2]}  QLA={rec[3]:,.2f}  LP={rec[4]:,.2f}  diff={rec[5]:,.2f}")

    out()
    out("F) VERDICT")
    out("-" * 100)
    l14_fail = any(
        (l14_by.get(c, [0, 0, 0, 0])[0] == 0) or (l14_by.get(c, [0, 0, 0, 0])[1] != l14_by.get(c, [0, 0, 0, 0])[0])
        for c in ("NT", "PQ", "PR", "ST")
        if l14_by.get(c, [0])[0]
    )
    # L14 classes that exist on ridr must all match
    l14_ok = True
    for cls in ("NT", "PQ", "PR", "ST"):
        n, ok, _q, _l = l14_by.get(cls, [0, 0, 0.0, 0.0])
        if n and ok != n:
            l14_ok = False
    still_zero_l14 = sum(1 for z in zeros if z[0] == "1L14SC")
    out(f"  L14 class-key fix (PQ/PR/ST now valued and matching): {'PASS' if l14_ok and still_zero_l14 == 0 else 'FAIL'}")
    out(f"  L-book QLA $0 with LifePRO reserve remaining: {len(zeros)} rows / ${sum(z[5] for z in zeros):,.2f}")
    out(f"  L-book match rate: {tot['match']}/{tot['n']} valued rows")
    out(f"  Rate-table class gaps (no TV key): {len(missing_tv)}")
    out(f"  Rate-table class gaps (no NP key): {len(missing_np)}")

    report = os.path.join(OUT_DIR, f"l_plan_validation_{stamp}.txt")
    with open(report, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    out()
    out(f"Report: {report}")
    return 0 if l14_ok and still_zero_l14 == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
