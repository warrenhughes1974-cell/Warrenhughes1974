"""Issue 27 planning revision — validate SL suppression (read-only)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "QLA_Migration" / "Output"
ISSUE = Path(__file__).resolve().parent


def read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def ridr_amt(r) -> float:
    try:
        return round(float(r["MUNIT"] or 0) * float(r["MVPU"] or 0), 2)
    except ValueError:
        return 0.0


def main() -> None:
    pop = read_csv(ISSUE / "Issue_27_SL_Impact_Population.csv")
    prem = read_csv(ISSUE / "Issue_27_SL_Premium_Population.csv")
    ridr = read_csv(OUT / "quikridr.csv")
    mstr = read_csv(OUT / "quikmstr.csv")

    pop["_QLA"] = pop["_QLA"].astype(str).str.strip()
    pop["_SEQ"] = pop["_SEQ"].astype(str).str.strip()
    pop["_AMT"] = pop["_AMT"].astype(float)
    pop["BASE_AMT"] = pop["BASE_AMT"].astype(float)
    pop["_DUP_AMT"] = pop["_DUP_AMT"].map(lambda x: str(x).strip().lower() in ("true", "1", "yes"))

    sl_policies = sorted(pop["_QLA"].unique())
    sl_phases = {(r["_QLA"], r["_SEQ"]) for _, r in pop.iterrows()}

    ridr["_POL"] = ridr["MPOLICY"].str.strip()
    ridr["_PH"] = ridr["MPHASE"].str.strip()
    ridr_post = ridr[~ridr.apply(lambda r: (r["_POL"], r["_PH"]) in sl_phases, axis=1)].copy()

    # Duplicate face in quikridr after SL removal (same MPLAN + face)
    ridr_dup = []
    for pol in sl_policies:
        sub = ridr_post[ridr_post["_POL"] == pol]
        seen: dict[tuple[float, str], str] = {}
        for _, r in sub.iterrows():
            a = ridr_amt(r)
            if a <= 0:
                continue
            key = (a, str(r["MPLAN"]).strip())
            ph = str(r["MPHASE"]).strip()
            if key in seen:
                ridr_dup.append({"QLA": pol, "PH1": seen[key], "PH2": ph, "AMT": key[0], "MPLAN": key[1]})
            else:
                seen[key] = ph

    # SL was sole source of duplicate — count policies where _DUP_AMT true
    dup_policies = pop.loc[pop["_DUP_AMT"], "_QLA"].nunique()

    # SL unique face (not matching base)
    sl_unique = pop[(pop["_AMT"] > 0) & (~pop["_DUP_AMT"])][["_QLA", "_SEQ", "_AMT", "BASE_AMT", "SL_TABLE_CODE"]]

    # Premium: PPOLC from premium pop vs MMODEPREM
    mstr["_POL"] = mstr["MPOLICY"].str.strip()
    prem_match = prem_mismatch = 0
    for _, r in prem.iterrows():
        qla = str(r["QLA"]).strip()
        pp = float(r["PPOLC_MODE_PREM"])
        ms = mstr[mstr["_POL"] == qla]
        if ms.empty:
            continue
        mm = float(str(ms.iloc[0]["MMODEPREM"]).strip() or 0)
        if abs(pp - mm) <= 0.10:
            prem_match += 1
        else:
            prem_mismatch += 1

    # All 67 policies MMODEPREM present
    mstr_sl = mstr[mstr["_POL"].isin(sl_policies)]
    mstr_missing = len(sl_policies) - mstr_sl["_POL"].nunique()

    # Current SL phases in quikridr
    sl_in_ridr = int(ridr.apply(lambda r: (r["_POL"], r["_PH"]) in sl_phases, axis=1).sum())

    # MSPCODE blank on SL policy quikridr rows
    sl_ridr = ridr[ridr["_POL"].isin(sl_policies)]
    mspcode_blank = int((sl_ridr["MSPCODE"].str.strip() == "").sum())

    summary = {
        "sl_policies": len(sl_policies),
        "sl_rows": len(pop),
        "policies_with_sl_dup_face_before": int(dup_policies),
        "quikridr_dup_face_after_sl_removal": len(ridr_dup),
        "sl_unique_face_rows_not_dup_base": len(sl_unique),
        "sl_phases_current_quikridr": sl_in_ridr,
        "quikridr_rows_removed_on_suppression": sl_in_ridr,
        "premium_population_ppoc_vs_mmodeprem_match": prem_match,
        "premium_population_mismatch": prem_mismatch,
        "sl_policies_missing_quikmstr": mstr_missing,
        "quikridr_mspcode_blank_sl_policy_rows": f"{mspcode_blank}/{len(sl_ridr)}",
        "sl_table_code_in_conversion": False,
    }

    print(json.dumps(summary, indent=2))
    if ridr_dup:
        print("\nRemaining duplicates after SL removal:")
        for d in ridr_dup:
            print(d)
    if len(sl_unique):
        print(f"\nSL rows with unique face (not dup base): {len(sl_unique)}")
        print(sl_unique.head(10).to_string(index=False))

    (ISSUE / "Issue_27_SL_Suppression_Validation.json").write_text(json.dumps(summary, indent=2))
    if ridr_dup:
        pd.DataFrame(ridr_dup).to_csv(ISSUE / "Issue_27_Remaining_Dup_Face_After_SL.csv", index=False)
    if len(sl_unique):
        sl_unique.to_csv(ISSUE / "Issue_27_SL_Unique_Face_Policies.csv", index=False)


if __name__ == "__main__":
    main()
