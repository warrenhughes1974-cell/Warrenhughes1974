"""
Issue 21F — read-only risk simulation: LifePRO four-component premiums paid
vs current quikprmh totals; classify load candidates / exceptions / ISWL.

No production code changes. Run from repo root:

  python Issue_Log_Items/Issue_21/Issue_21F/_risk_review_issue21f_premium_adjustment.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
SRC = REPO / "QLA_Migration" / "Source"
OUT = REPO / "QLA_Migration" / "Output"
MAP = REPO / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"
EVID = Path(__file__).resolve().parent / "evidence"


def _norm(p) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", str(p or "").strip())


def _money(s) -> float:
    try:
        return float(str(s).replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def _status(r) -> str:
    if r["ISWL"]:
        return "ISWL_EXCLUDED"
    if not r["MPOLICY"]:
        return "NO_CROSSWALK"
    if r["LP_TOTAL"] <= 0 and r["HIST"] <= 0:
        return "NO_PREMIUM_DATA"
    if abs(r["ADJ"]) < 0.005:
        return "NO_GAP"
    if r["ADJ"] < 0:
        return "NEGATIVE_EXCEPTION"
    return "LOAD_CANDIDATE"


def main() -> None:
    EVID.mkdir(parents=True, exist_ok=True)
    pp_path = next(SRC.glob("PPBENTYP_BenefitType_Extract_*.csv"))
    pp = pd.read_csv(
        pp_path,
        encoding="latin1",
        low_memory=False,
        dtype=str,
        usecols=[
            "POLICY_NUMBER",
            "TYPE_CODE",
            "PREMIUMS_PAID",
            "PU_PREMIUMS_PAID",
            "SU_PREMIUMS_PAID",
            "SL_PREMIUMS_PAID",
        ],
    ).fillna("")
    pp["TC"] = pp["TYPE_CODE"].astype(str).str.strip().str.upper()
    pp["POL"] = pp["POLICY_NUMBER"].map(_norm)
    for c in ["PREMIUMS_PAID", "PU_PREMIUMS_PAID", "SU_PREMIUMS_PAID", "SL_PREMIUMS_PAID"]:
        pp[c] = pp[c].map(_money)

    iswl = set(pp.loc[pp["TC"] == "BF", "POL"])
    g = pp.groupby("POL", as_index=False).agg(
        {
            "PREMIUMS_PAID": "max",
            "PU_PREMIUMS_PAID": "max",
            "SU_PREMIUMS_PAID": "max",
            "SL_PREMIUMS_PAID": "max",
        }
    )
    g["LP_TOTAL"] = (
        g["PREMIUMS_PAID"]
        + g["PU_PREMIUMS_PAID"]
        + g["SU_PREMIUMS_PAID"]
        + g["SL_PREMIUMS_PAID"]
    )
    g["ISWL"] = g["POL"].isin(iswl)

    cw = pd.read_csv(MAP, dtype=str).fillna("")
    cw_map = dict(
        zip(cw["Old_Value"].map(_norm), cw["New_Value"].astype(str).str.strip())
    )
    g["MPOLICY"] = g["POL"].map(lambda p: cw_map.get(p, ""))

    prmh = pd.read_csv(OUT / "quikprmh.csv", dtype=str, low_memory=False).fillna("")
    prmh["PREMIUM"] = prmh["PREMIUM"].map(_money)
    hist = prmh.groupby(prmh["MPOLICY"].astype(str).str.strip())["PREMIUM"].sum()
    g["HIST"] = g["MPOLICY"].map(lambda m: float(hist.get(m, 0.0)) if m else 0.0)
    g["ADJ"] = (g["LP_TOTAL"] - g["HIST"]).round(2)
    g["HAS_HIST"] = g["MPOLICY"].isin(hist.index)
    g["STATUS"] = g.apply(_status, axis=1)

    cols = [
        "POL",
        "MPOLICY",
        "ISWL",
        "PREMIUMS_PAID",
        "PU_PREMIUMS_PAID",
        "SU_PREMIUMS_PAID",
        "SL_PREMIUMS_PAID",
        "LP_TOTAL",
        "HIST",
        "ADJ",
        "HAS_HIST",
        "STATUS",
    ]
    g[cols].to_csv(EVID / "issue21f_risk_adjustment_simulation.csv", index=False)
    cands = g[g["STATUS"] == "LOAD_CANDIDATE"]
    negs = g[g["STATUS"] == "NEGATIVE_EXCEPTION"]
    cands[cols].to_csv(EVID / "issue21f_risk_load_candidates.csv", index=False)
    negs[cols].to_csv(EVID / "issue21f_risk_negative_exceptions.csv", index=False)

    impact = {
        "ppbentyp_policies": int(len(g)),
        "iswl_excluded": int((g["STATUS"] == "ISWL_EXCLUDED").sum()),
        "load_candidates": int(len(cands)),
        "load_adj_sum": round(float(cands["ADJ"].sum()), 2) if len(cands) else 0.0,
        "load_adj_median": round(float(cands["ADJ"].median()), 2) if len(cands) else 0.0,
        "load_adj_max": round(float(cands["ADJ"].max()), 2) if len(cands) else 0.0,
        "negative_exceptions": int(len(negs)),
        "quikprmh_rows_today": int(len(prmh)),
        "projected_quikprmh_rows_after": int(len(prmh) + len(cands)),
        "golden_010310404C": g.loc[g["POL"] == "9010310404", cols]
        .head(1)
        .to_dict("records"),
        "status_counts": g["STATUS"].value_counts().to_dict(),
    }
    (EVID / "issue21f_risk_impact_summary.json").write_text(
        json.dumps(impact, indent=2), encoding="utf-8"
    )
    print(json.dumps(impact, indent=2))


if __name__ == "__main__":
    main()
