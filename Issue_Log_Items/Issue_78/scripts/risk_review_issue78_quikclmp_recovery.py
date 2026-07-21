"""
Issue #78 — read-only Risk simulation: missing quikclmp recovery candidates.
Does NOT modify Output or production mapping.
Writes: Issue_Log_Items/Issue_78/evidence/issue78_risk_recovery_simulation.csv
"""
from __future__ import annotations

import collections
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
EVID = ROOT / "Issue_Log_Items" / "Issue_78" / "evidence"
EVID.mkdir(parents=True, exist_ok=True)

PAYOUT = {"90", "92", "94", "567", "1900", "0090", "0092", "0094", "0567"}


def main() -> None:
    s = pd.read_csv(ROOT / "QLA_Migration" / "Output" / "quikclms.csv", dtype=str, keep_default_na=False)
    p = pd.read_csv(ROOT / "QLA_Migration" / "Output" / "quikclmp.csv", dtype=str, keep_default_na=False)
    missing = set(s.MPOLICY.str.strip()) - set(p.MPOLICY.str.strip())
    missing_lp = {("9" + m[:-1]): m for m in missing if m.endswith("C")}
    hdr = s.copy()
    hdr["POL"] = hdr.MPOLICY.str.strip()
    hdr = hdr.drop_duplicates("POL").set_index("POL")

    pactg = ROOT / "QLA_Migration" / "Source" / "PACTG_Accounting_Extract20260630.csv"
    h0 = pd.read_csv(pactg, encoding="latin1", dtype=str, nrows=0)
    colmap = {c.strip(): c for c in h0.columns}
    want = [
        "POLICY_NUMBER",
        "CREDIT_CODE",
        "DEBIT_CODE",
        "TRANS_AMOUNT",
        "EFFECTIVE_DATE",
        "REVERSAL_CODE",
        "CONTROL_NUMBER",
    ]
    usecols = [colmap[w] for w in want]
    rows = []
    for chunk in pd.read_csv(pactg, encoding="latin1", dtype=str, usecols=usecols, chunksize=300000):
        chunk.columns = [c.strip() for c in chunk.columns]
        chunk["POL"] = chunk.POLICY_NUMBER.str.strip()
        m = chunk[chunk.POL.isin(missing_lp)]
        m = m[
            (m.CREDIT_CODE.str.strip().isin(PAYOUT))
            | (m.DEBIT_CODE.str.strip().isin(PAYOUT))
        ]
        m = m[~m.REVERSAL_CODE.astype(str).str.strip().isin(["Y", "R", "V"])]
        rows.append(m)
    pay = pd.concat(rows) if rows else pd.DataFrame()
    pay["AMT"] = pd.to_numeric(pay.TRANS_AMOUNT.astype(str).str.strip(), errors="coerce").fillna(0)

    rel = pd.read_csv(
        ROOT / "QLA_Migration" / "Source" / "RelationshipNameAddress_Extract_20260630.csv",
        encoding="latin1",
        dtype=str,
        engine="python",
        on_bad_lines="skip",
    )
    rel.columns = [c.strip() for c in rel.columns]
    rel["POL"] = rel.POLICY_NUMBER.astype(str).str.strip()
    rel = rel[rel.POL.isin(missing_lp)]
    rel["RC"] = rel.RELATE_CODE.astype(str).str.strip()
    pe = rel[rel.RC == "PE"]
    pe_cnt = pe.groupby("POL")["NAME_ID"].nunique()
    b1 = set(rel[rel.RC == "B1"].POL)
    b2 = set(rel[rel.RC == "B2"].POL)
    ins = set(rel[rel.RC.isin(["IN", "INSD"])].POL)
    pay_cnt = pay.groupby("POL").size()

    audit = []
    for pol in sorted(set(pay.POL)):
        qla = missing_lp[pol]
        n_pe = int(pe_cnt.get(pol, 0))
        n_pay = int(pay_cnt.get(pol, 0))
        if n_pe == 1:
            t, src, note = 1, "PE_SINGLE", ""
        elif n_pe >= 2:
            t = 2
            if n_pay == n_pe:
                src, note = "PE_MULTI_PAIR_OK", "PAIR_OK"
            else:
                src, note = "PE_MULTI_PRIMARY_PE_ALL", "PRIMARY_PE_ALL"
        elif pol in b1:
            t, src, note = 3, "B1", ""
        elif pol in b2:
            t, src, note = 3, "B2", ""
        elif pol in ins:
            t, src, note = 3, "ESTATE_IN", ""
        else:
            t, src, note = 3, "ESTATE_UNKNOWN", ""
        cs = str(hdr.loc[qla, "CLAIMSTAT"]).strip() if qla in hdr.index else "?"
        mpaid = str(hdr.loc[qla, "MPAID"]).strip() if qla in hdr.index else ""
        audit.append(
            {
                "mpolicy": qla,
                "lifepro": pol,
                "tier": t,
                "payout_rows": n_pay,
                "pe_count": n_pe,
                "payout_amount": round(float(pay.loc[pay.POL == pol, "AMT"].sum()), 2),
                "claimstat": cs,
                "header_mpaid": mpaid,
                "payee_source": src,
                "pair_note": note,
            }
        )

    out = EVID / "issue78_risk_recovery_simulation.csv"
    pd.DataFrame(audit).to_csv(out, index=False)
    print(f"Wrote {out} ({len(audit)} policies)")


if __name__ == "__main__":
    main()
