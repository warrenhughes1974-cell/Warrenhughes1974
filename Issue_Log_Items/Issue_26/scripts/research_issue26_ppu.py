"""Issue #26 research helper — Premium Per Unit trace (read-only)."""
from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[3]
SRC = BASE / "QLA_Migration" / "Source"
OUT = BASE / "QLA_Migration" / "Output"
CW = BASE / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"

TRACE = [
    {"qla": "010310404C", "lifepro": "9010310404", "exp_lifepro_ppu": 13.20, "reported_qla": 18.10},
    {"qla": "010331768C", "lifepro": "9010331768", "exp_lifepro_ppu": 10.96, "reported_qla": 174.40},
    {"qla": "010367131C", "lifepro": "9010367131", "exp_lifepro_ppu": 9.12, "reported_qla": 31.20},
]


def main() -> None:
    ppben = pd.read_csv(SRC / "PPBEN_PolicyBenefit_Extract_20260530.csv", dtype=str, encoding="latin1")
    ppben.columns = [c.strip().upper() for c in ppben.columns]
    ppolc = pd.read_csv(SRC / "PPOLC_PolicyMaster_Extract_20260530.csv", dtype=str, encoding="latin1")
    ppolc.columns = [c.strip().upper() for c in ppolc.columns]
    ridr = pd.read_csv(OUT / "quikridr.csv", dtype=str, encoding="latin1")
    ridr.columns = [c.strip().upper() for c in ridr.columns]
    mstr = pd.read_csv(OUT / "quikmstr.csv", dtype=str, encoding="latin1")
    mstr.columns = [c.strip().upper() for c in mstr.columns]

    ppben["POLICY_NUMBER"] = ppben["POLICY_NUMBER"].astype(str).str.strip()
    ppben1 = ppben[ppben["BENEFIT_SEQ"].astype(str).str.strip().isin(["1", "01"])].copy()

    cw = pd.read_csv(CW, dtype=str, header=None, names=["LP", "QLA"])
    cw["LP"] = cw["LP"].str.strip()
    cw["QLA"] = cw["QLA"].str.strip()

    merged = ppben1.merge(cw, left_on="POLICY_NUMBER", right_on="LP", how="left")
    merged = merged.merge(
        ridr[ridr["MPHASE"].astype(str).str.strip().isin(["1", "01"])],
        left_on="QLA",
        right_on="MPOLICY",
        how="left",
        suffixes=("_SRC", "_OUT"),
    )

    num_cols = [
        "ANN_PREM_PER_UNIT", "MODE_PREMIUM", "VALUE_PER_UNIT", "NUMBER_OF_UNITS",
        "BENEFIT_FEE", "MVPU", "MPREM", "MUNIT",
    ]
    for c in num_cols:
        if c in merged.columns:
            merged[c] = pd.to_numeric(merged[c].astype(str).str.strip(), errors="coerce")

    merged["calc_ann_from_ppu"] = merged["ANN_PREM_PER_UNIT"] * merged["NUMBER_OF_UNITS"]
    merged["calc_ann_with_fee"] = merged["calc_ann_from_ppu"] + merged["BENEFIT_FEE"]
    merged["mprem_per_unit"] = merged["MODE_PREMIUM"] / merged["NUMBER_OF_UNITS"]
    merged["mprem_matches_reported"] = False

    for t in TRACE:
        m = merged[merged["QLA"] == t["qla"]]
        if len(m):
            merged.loc[m.index, "mprem_matches_reported"] = (
                (m["MPREM"] - t["reported_qla"]).abs() < 0.01
            ).values[0]

    print("=== FLEET (phase 1) ===")
    print("rows joined:", len(merged))
    print("MPREM == source MODE_PREMIUM:", int(((merged["MPREM"] - merged["MODE_PREMIUM"]).abs() < 0.01).sum()))
    print("MVPU == source VALUE_PER_UNIT:", int(((merged["MVPU"] - merged["VALUE_PER_UNIT"]).abs() < 0.01).sum()))
    print("MVPU == ANN_PREM_PER_UNIT:", int(((merged["MVPU"] - merged["ANN_PREM_PER_UNIT"]).abs() < 0.01).sum()))
    print(
        "ANN_PREM_PER_UNIT != MPREM (Issue #26 pattern):",
        int((merged["ANN_PREM_PER_UNIT"] - merged["MPREM"]).abs().gt(0.01).sum()),
        f"({100*(merged['ANN_PREM_PER_UNIT'] - merged['MPREM']).abs().gt(0.01).mean():.1f}%)",
    )

    print("\n=== TRACE POLICIES ===")
    for t in TRACE:
        row = merged[merged["QLA"] == t["qla"]].iloc[0]
        print(f"\n{t['qla']} (LifePRO {t['lifepro']})")
        print(f"  LifePRO ANN_PREM_PER_UNIT (expected PPU): {row['ANN_PREM_PER_UNIT']}")
        print(f"  LifePRO MODE_PREMIUM: {row['MODE_PREMIUM']}")
        print(f"  LifePRO VALUE_PER_UNIT (face): {row['VALUE_PER_UNIT']}")
        print(f"  LifePRO NUMBER_OF_UNITS: {row['NUMBER_OF_UNITS']}")
        print(f"  LifePRO BENEFIT_FEE: {row['BENEFIT_FEE']}")
        print(f"  Emitted quikridr MVPU: {row['MVPU']}")
        print(f"  Emitted quikridr MPREM: {row['MPREM']}")
        print(f"  Client reported QLAdmin: {t['reported_qla']} (matches MPREM: {t['reported_qla'] == row['MPREM']})")
        print(f"  ANN_PPU * units + fee: {row['calc_ann_with_fee']}")
        print(f"  MPREM/units (modal per unit): {row['mprem_per_unit']:.4f}")


if __name__ == "__main__":
    main()
