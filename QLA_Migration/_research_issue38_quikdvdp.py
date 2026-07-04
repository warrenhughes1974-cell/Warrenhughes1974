"""
Issue #38 read-only research: quikdvdp MDEPOSIT vs PPBENTYP ACCUM_DIVIDENDS.
Run: python QLA_Migration/_research_issue38_quikdvdp.py
"""
from __future__ import annotations

import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "QLA_Migration", "Source")
OUT = os.path.join(ROOT, "QLA_Migration", "Output")
ISSUE = os.path.join(ROOT, "Issue_Log_Items", "Issue_38")


def parse_money(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(",", "").str.strip(), errors="coerce"
    ).fillna(0)


def main() -> int:
    pp_path = os.path.join(SRC, "PPBENTYP_BenefitType_Extract_20260530.csv")
    qd_path = os.path.join(OUT, "quikdvdp.csv")
    for p in (pp_path, qd_path):
        if not os.path.exists(p):
            print(f"MISSING: {p}")
            return 1

    pp = pd.read_csv(pp_path, encoding="latin1", dtype=str, low_memory=False)
    pp.columns = [c.strip().upper() for c in pp.columns]
    pp = pp[pp["BENEFIT_SEQ"].astype(str).str.strip().isin(["1", "01"])].copy()
    pp["ACC"] = parse_money(pp["ACCUM_DIVIDENDS"])

    qd = pd.read_csv(qd_path, dtype=str)
    qd.columns = [c.strip().upper() for c in qd.columns]
    qd["MDEP_OUT"] = parse_money(qd["MDEPOSIT"])

    print(f"PPBENTYP seq-1 rows: {len(pp)}")
    print(f"ACCUM_DIVIDENDS > 0: {(pp['ACC'] > 0).sum()}")
    print(f"quikdvdp rows: {len(qd)}")
    print(f"MDEPOSIT > 0 in output: {(qd['MDEP_OUT'] > 0).sum()}")
    print(
        "PACTG hardcoded file exists:",
        os.path.exists(os.path.join(SRC, "PACTG_Accounting_Extract20260427.csv")),
    )
    print(
        "PACTG current file exists:",
        os.path.exists(os.path.join(SRC, "PACTG_Accounting_Extract20260530.csv")),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
