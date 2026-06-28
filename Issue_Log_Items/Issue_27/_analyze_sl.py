"""Issue 27 — SL benefit type impact analysis (planning only)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "QLA_Migration" / "Source" / "PPBEN_PolicyBenefit_Extract_20260530.csv"
OUT = ROOT / "QLA_Migration" / "Output"
CW = ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"


def read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def strip(val) -> str:
    return str(val).strip()


def amount_insured(units: str, vpu: str) -> float:
    try:
        u = float(strip(units) or "0")
        v = float(strip(vpu) or "0")
        return round(u * v, 2)
    except ValueError:
        return 0.0


def main() -> None:
    ppben = read_csv(SRC)
    ridr = read_csv(OUT / "quikridr.csv")
    cw = read_csv(CW)
    lp_to_qla = {strip(k): strip(v) for k, v in zip(cw.iloc[:, 0], cw.iloc[:, 1])}

    ppben["_BT"] = ppben["BENEFIT_TYPE"].astype(str).str.strip().str.upper()
    ppben["_SEQ"] = ppben["BENEFIT_SEQ"].astype(str).str.strip()
    ppben["_LP"] = ppben["POLICY_NUMBER"].astype(str).str.strip()
    ppben["_QLA"] = ppben["_LP"].map(lp_to_qla).fillna("")
    ppben["_AMT"] = ppben.apply(
        lambda r: amount_insured(r.get("NUMBER_OF_UNITS", ""), r.get("VALUE_PER_UNIT", "")),
        axis=1,
    )

    sl = ppben[ppben["_BT"] == "SL"].copy()
    print(f"Total SL rows in PPBEN: {len(sl)}")
    print(f"Policies with SL: {sl['_LP'].nunique()}")

    # Base benefit (seq 1) per policy with SL
    base = ppben[ppben["_SEQ"] == "1"][["_LP", "_QLA", "_AMT", "PLAN_CODE", "NUMBER_OF_UNITS", "VALUE_PER_UNIT"]].rename(
        columns={"_AMT": "BASE_AMT", "PLAN_CODE": "BASE_PLAN"}
    )
    sl_m = sl.merge(base, on="_LP", how="left")

    sl_m["_DUP_AMT"] = (sl_m["_AMT"] > 0) & (sl_m["BASE_AMT"] > 0) & (
        abs(sl_m["_AMT"] - sl_m["BASE_AMT"]) < 0.02
    )
    sl_m["_SL_HAS_AMT"] = sl_m["_AMT"] > 0
    sl_m["_SL_HAS_PREM"] = sl_m.apply(
        lambda r: float(strip(r.get("MODE_PREMIUM", "0") or "0") or 0) > 0
        or float(strip(r.get("ANN_PREM_PER_UNIT", "0") or "0") or 0) > 0,
        axis=1,
    )

    print(f"SL rows with amount insured > 0: {sl_m['_SL_HAS_AMT'].sum()}")
    print(f"SL rows duplicating base face amount: {sl_m['_DUP_AMT'].sum()}")
    print(f"Policies with duplicate SL face: {sl_m.loc[sl_m['_DUP_AMT'], '_LP'].nunique()}")
    print(f"SL rows with premium > 0: {sl_m['_SL_HAS_PREM'].sum()}")

    # quikridr phases for SL policies
    ridr["_POL"] = ridr["MPOLICY"].astype(str).str.strip()
    sl_qla = set(sl_m["_QLA"].dropna()) - {""}
    ridr_sl = ridr[ridr["_POL"].isin(sl_qla)]
    print(f"quikridr rows for SL policies: {len(ridr_sl)}")

    # Trace 010448806C
    lp = "9010448806"
    print("\n=== TRACE 010448806C ===")
    for _, r in ppben[ppben["_LP"] == lp].sort_values("_SEQ").iterrows():
        print(
            f"SEQ={r['_SEQ']} TYPE={r['_BT']} PLAN={strip(r.get('PLAN_CODE',''))} "
            f"UNITS={strip(r.get('NUMBER_OF_UNITS',''))} VPU={strip(r.get('VALUE_PER_UNIT',''))} "
            f"AMT={r['_AMT']} MODE_PREM={strip(r.get('MODE_PREMIUM',''))} ANN_PPU={strip(r.get('ANN_PREM_PER_UNIT',''))}"
        )
    qla = "010448806C"
    print("\nquikridr:")
    cols = ["MPHASE", "MPLAN", "MPHSTAT", "MUNIT", "MVPU", "MPREM", "MPAR", "MEFFDATE", "MUWCLASS", "MRIDRID"]
    print(ridr[ridr["_POL"] == qla][cols].to_string(index=False))

    # Export impact CSV
    out_dir = Path(__file__).resolve().parent
    sl_m.to_csv(out_dir / "Issue_27_SL_Impact_Population.csv", index=False)
    summary = {
        "total_sl_rows": int(len(sl)),
        "policies_with_sl": int(sl["_LP"].nunique()),
        "sl_rows_with_amount": int(sl_m["_SL_HAS_AMT"].sum()),
        "sl_rows_dup_base_amount": int(sl_m["_DUP_AMT"].sum()),
        "policies_dup_base_amount": int(sl_m.loc[sl_m["_DUP_AMT"], "_LP"].nunique()),
        "sl_rows_with_premium": int(sl_m["_SL_HAS_PREM"].sum()),
    }
    (out_dir / "Issue_27_SL_Impact_Summary.json").write_text(json.dumps(summary, indent=2))
    print("\nSummary:", summary)


if __name__ == "__main__":
    main()
