"""
Issue #38 read-only risk simulation: quikdvdp MDEPOSIT / MINTYTD / MINTDATE.
Run: python QLA_Migration/_risk_review_issue38_quikdvdp.py
"""
from __future__ import annotations

import os
import sys
from datetime import datetime

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "QLA_Migration", "Source")
OUT = os.path.join(ROOT, "QLA_Migration", "Output")
ISSUE = os.path.join(ROOT, "Issue_Log_Items", "Issue_38")


def norm(s) -> str:
    return str(s).strip().replace(".0", "")


def parse_money(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(",", "").str.strip(), errors="coerce"
    ).fillna(0)


def build_641_cache(cw_map: dict) -> dict:
    path = os.path.join(SRC, "PACTG_Accounting_Extract20260530.csv")
    if not os.path.exists(path):
        return {}
    tx = pd.read_csv(path, encoding="latin1", dtype=str, low_memory=False, on_bad_lines="skip")
    tx.columns = [c.replace("\ufeff", "").strip().upper() for c in tx.columns]
    current_year = str(datetime.now().year)
    cache: dict = {}
    for _, row in tx.iterrows():
        raw = norm(row.get("POLICY_NUMBER", row.get("POLN", "")))
        if not raw:
            continue
        pol = norm(cw_map.get(raw, raw))
        cc = norm(row.get("CREDIT_CODE", ""))
        dc = norm(row.get("DEBIT_CODE", ""))
        trcd = norm(row.get("TRCD", ""))
        if not trcd:
            if cc in ("641", "0641"):
                trcd = cc
            elif dc in ("641", "0641"):
                trcd = dc
        if trcd not in ("641", "0641"):
            continue
        amt = float(parse_money(pd.Series([row.get("TRANS_AMOUNT", 0)])).iloc[0])
        dt = str(row.get("EFFECTIVE_DATE", "")).strip()
        if pol not in cache:
            cache[pol] = {"MINTYTD": 0.0, "MINTDATE": ""}
        if current_year in dt:
            cache[pol]["MINTYTD"] += amt
        if dt > cache[pol]["MINTDATE"]:
            cache[pol]["MINTDATE"] = dt
    return cache


def main() -> int:
    cw = pd.read_csv(os.path.join(ROOT, "QLA_Migration", "Mapping", "Master_Crosswalk.csv"), dtype=str)
    cw.columns = [c.strip().upper() for c in cw.columns]
    cw_map = dict(zip(cw["OLD_VALUE"].apply(norm), cw["NEW_VALUE"].apply(norm)))

    pp = pd.read_csv(
        os.path.join(SRC, "PPBENTYP_BenefitType_Extract_20260530.csv"),
        encoding="latin1",
        dtype=str,
        low_memory=False,
    )
    pp.columns = [c.strip().upper() for c in pp.columns]
    pp = pp[pp["BENEFIT_SEQ"].astype(str).str.strip().isin(["1", "01"])].copy()
    pp["MPOLICY"] = pp["POLICY_NUMBER"].apply(norm).map(cw_map)
    acc_map = pp.set_index("MPOLICY")["ACCUM_DIVIDENDS"].pipe(parse_money).to_dict()

    qd = pd.read_csv(os.path.join(OUT, "quikdvdp.csv"), dtype=str)
    qd.columns = [c.strip().upper() for c in qd.columns]
    cache = build_641_cache(cw_map)

    sim = qd.copy()
    sim["MDEP_BEFORE"] = parse_money(sim["MDEPOSIT"])
    sim["MDEP_AFTER"] = sim["MPOLICY"].map(acc_map).fillna(0)
    sim["MINTYTD_AFTER"] = sim["MPOLICY"].map(lambda p: cache.get(p, {}).get("MINTYTD", 0.0))
    sim["MINTDATE_AFTER"] = sim["MPOLICY"].map(lambda p: cache.get(p, {}).get("MINTDATE", ""))

    os.makedirs(ISSUE, exist_ok=True)
    out_path = os.path.join(ISSUE, "Issue_38_Risk_Simulation.csv")
    sim.to_csv(out_path, index=False)

    mdep_chg = ((sim["MDEP_AFTER"] - sim["MDEP_BEFORE"]).abs() > 0.01).sum()
    print(f"quikdvdp rows: {len(sim)}")
    print(f"MDEPOSIT changes: {mdep_chg}")
    print(f"MDEPOSIT > 0 after: {(sim['MDEP_AFTER'] > 0).sum()}")
    print(f"Output: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
