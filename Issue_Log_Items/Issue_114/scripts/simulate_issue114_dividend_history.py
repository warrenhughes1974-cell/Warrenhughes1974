"""
Issue #114 — Risk-stage simulation (READ-ONLY).

Models the proposed two-layer dividend history emit without writing to
QLA_Migration/Output/. Produces the population counts used in
Issue_114_Risk_Review_Report.md.

  Layer A  PACTG dividend election codes 514/515/516/517/518 -> quikbenh MBENTYP 1-5
  Layer B  one plug row per policy for (PPBENTYP.DIVIDENDS_CREDITED - Layer A sum)

Writes only to Issue_Log_Items/Issue_114/evidence/.
"""

from __future__ import annotations

import csv
import os
import sys
from collections import defaultdict

import pandas as pd

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, REPO)

from qla_core.normalize_utils import format_qladmin_mpolicy  # noqa: E402

PACTG = os.path.join(REPO, "QLA_Migration", "Source", "PACTG_Accounting_Extract20260630.csv")
PPBENTYP = os.path.join(REPO, "QLA_Migration", "Source", "PPBENTYP_BenefitType_Extract_20260630.csv")
BENH = os.path.join(REPO, "QLA_Migration", "Output", "quikbenh.csv")
EVIDENCE = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "evidence"))

# LifePRO dividend election code -> QLAdmin Policy Benefit Type Code
CODE_TO_MBENTYP = {"515": "1", "516": "2", "514": "3", "517": "4", "518": "5"}
# LifePRO dividend option -> QLAdmin benefit type (plug rows). 6 = Reduce Loan: no QLAdmin type.
OPTION_TO_MBENTYP = {"1": "1", "2": "2", "3": "3", "4": "4", "5": "5"}
PLUG_DATE = "20171231"
PRESERVE_TYPES = {"8", "10", "11", "12"}

csv.field_size_limit(10 ** 7)


def code(v: str) -> str:
    s = "".join(ch for ch in str(v).strip() if ch.isdigit())
    return s.lstrip("0") or "0"


def money(v) -> float:
    s = str(v or "").strip().replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def scan_pactg():
    """Layer A: dividend election transactions, keyed by MPOLICY."""
    rows = []
    stats = defaultdict(int)
    with open(PACTG, newline="", encoding="latin-1") as fh:
        rdr = csv.reader(fh)
        head = [c.strip() for c in next(rdr)]
        ix = {n: head.index(n) for n in
              ["CREDIT_CODE", "DEBIT_CODE", "POLICY_NUMBER", "TRANS_AMOUNT",
               "EFFECTIVE_DATE", "DATE_REVERSED"]}
        for r in rdr:
            if len(r) < len(head):
                continue
            pol = r[ix["POLICY_NUMBER"]].strip()
            if not pol or pol.startswith("---"):
                continue
            cr, db = code(r[ix["CREDIT_CODE"]]), code(r[ix["DEBIT_CODE"]])
            hit = db if db in CODE_TO_MBENTYP else (cr if cr in CODE_TO_MBENTYP else None)
            if hit is None:
                continue
            stats["election_rows"] += 1
            if (r[ix["DATE_REVERSED"]].strip().lstrip("0") or "") not in ("", "0"):
                stats["reversed_excluded"] += 1
                continue
            eff = r[ix["EFFECTIVE_DATE"]].strip()
            amt = abs(money(r[ix["TRANS_AMOUNT"]]))
            mp = format_qladmin_mpolicy(pol)
            if not mp:
                stats["no_crosswalk"] += 1
                continue
            if amt <= 0 or len(eff) < 8 or not eff.isdigit():
                stats["bad_amount_or_date"] += 1
                continue
            rows.append({"MPOLICY": mp, "MBENTYP": CODE_TO_MBENTYP[hit],
                         "MDATE": eff, "MBEN": f"{amt:.2f}", "_SRC": hit, "_POL": pol})
            stats["emitted"] += 1
    return rows, stats


def load_lifetime():
    """Layer B target: PPBENTYP BA-row DIVIDENDS_CREDITED + dividend option, by MPOLICY."""
    df = pd.read_csv(PPBENTYP, dtype=str, low_memory=False, encoding="latin-1").fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    df = df[~df["POLICY_NUMBER"].str.contains("---", na=False)]
    df["POLICY_NUMBER"] = df["POLICY_NUMBER"].str.strip()
    df["TC"] = df["TYPE_CODE"].str.strip().str.upper()

    out, or_rows = {}, {}
    for pol, g in df.groupby("POLICY_NUMBER"):
        if not pol:
            continue
        mp = format_qladmin_mpolicy(pol)
        if not mp:
            continue
        ba = g[g["TC"] == "BA"]
        total = sum(money(v) for v in ba["DIVIDENDS_CREDITED"])
        opt = (ba["DIVIDEND"].iloc[0].strip() if len(ba) else "")
        oram = sum(money(v) for v in g.loc[g["TC"] == "OR", "DIVIDENDS_CREDITED"])
        if total > 0:
            out[mp] = {"POL": pol, "LIFETIME": total, "OPTION": opt}
        if oram > 0:
            or_rows[mp] = oram
    return out, or_rows


def main():
    os.makedirs(EVIDENCE, exist_ok=True)

    layer_a, stats = scan_pactg()
    lifetime, or_rows = load_lifetime()

    a_sum = defaultdict(float)
    a_cnt = defaultdict(int)
    for r in layer_a:
        a_sum[r["MPOLICY"]] += float(r["MBEN"])
        a_cnt[r["MBENTYP"]] += 1

    plug_rows, exceptions = [], []
    b_cnt = defaultdict(int)
    b_amt = defaultdict(float)
    for mp, rec in sorted(lifetime.items()):
        gap = round(rec["LIFETIME"] - a_sum.get(mp, 0.0), 2)
        opt = rec["OPTION"]
        mbentyp = OPTION_TO_MBENTYP.get(opt)
        if gap <= 0.005:
            exceptions.append({**rec, "MPOLICY": mp, "GAP": gap,
                               "REASON": "NEGATIVE_OR_ZERO_GAP"})
            continue
        if mbentyp is None:
            exceptions.append({**rec, "MPOLICY": mp, "GAP": gap,
                               "REASON": f"UNMAPPED_OPTION_{opt or 'BLANK'}"})
            continue
        plug_rows.append({"MPOLICY": mp, "MBENTYP": mbentyp, "MDATE": PLUG_DATE,
                          "MBEN": f"{gap:.2f}"})
        b_cnt[mbentyp] += 1
        b_amt[mbentyp] += gap

    benh = pd.read_csv(BENH, dtype=str, low_memory=False).fillna("")
    before = benh["MBENTYP"].str.strip().value_counts().to_dict()

    print("=" * 74)
    print("ISSUE #114 — DIVIDEND HISTORY EMIT SIMULATION (read-only)")
    print("=" * 74)
    print("\nLayer A — PACTG dividend election transactions")
    for k, v in sorted(stats.items()):
        print(f"  {k:<24} {v:>10,}")
    print(f"  {'layer_a_dollars':<24} {sum(a_sum.values()):>13,.2f}")
    print(f"  {'layer_a_policies':<24} {len(a_sum):>10,}")

    print("\n  rows by MBENTYP:")
    for t in sorted(a_cnt, key=int):
        print(f"    type {t}: {a_cnt[t]:>6,} rows")

    print("\nLayer B — conversion adjustment plug rows")
    print(f"  target policies (lifetime > 0) : {len(lifetime):>6,}")
    print(f"  plug rows emitted              : {len(plug_rows):>6,}")
    print(f"  plug dollars                   : {sum(b_amt.values()):>13,.2f}")
    print(f"  exceptions (no row emitted)    : {len(exceptions):>6,}")
    for t in sorted(b_cnt, key=int):
        print(f"    type {t}: {b_cnt[t]:>6,} rows  ${b_amt[t]:>13,.2f}")

    ex_by = defaultdict(lambda: [0, 0.0])
    for e in exceptions:
        ex_by[e["REASON"]][0] += 1
        ex_by[e["REASON"]][1] += e["LIFETIME"]
    print("\n  exception breakdown:")
    for k, (n, amt) in sorted(ex_by.items()):
        print(f"    {k:<26} {n:>4} policies  ${amt:>12,.2f}")
    print(f"    {'OR_ROW_DOLLARS_EXCLUDED':<26} {len(or_rows):>4} policies  "
          f"${sum(or_rows.values()):>12,.2f}")

    print("\nquikbenh impact")
    print(f"  rows before                    : {len(benh):>6,}")
    print(f"  rows after                     : {len(benh) + len(layer_a) + len(plug_rows):>6,}")
    print("  preserved types (must not change):")
    for t in sorted(PRESERVE_TYPES, key=int):
        print(f"    type {t}: {before.get(t, 0):>6,} rows  (unchanged)")
    existing_div = sum(before.get(t, 0) for t in ("1", "2", "3", "4", "5"))
    print(f"  existing MBENTYP 1-5 to be replaced: {existing_div:,}")

    tot = sum(a_sum.values()) + sum(b_amt.values())
    target = sum(r["LIFETIME"] for r in lifetime.values())
    print("\nReconciliation")
    print(f"  LifePRO lifetime target        : {target:>13,.2f}")
    print(f"  Layer A + Layer B emitted      : {tot:>13,.2f}")
    print(f"  variance (exceptions withheld) : {target - tot:>13,.2f}")

    pd.DataFrame(layer_a).to_csv(
        os.path.join(EVIDENCE, "issue114_layer_a_transactions.csv"), index=False)
    pd.DataFrame(plug_rows).to_csv(
        os.path.join(EVIDENCE, "issue114_layer_b_plug_rows.csv"), index=False)
    pd.DataFrame(exceptions).to_csv(
        os.path.join(EVIDENCE, "issue114_exceptions.csv"), index=False)
    print(f"\nEvidence written to {EVIDENCE}")


if __name__ == "__main__":
    main()
