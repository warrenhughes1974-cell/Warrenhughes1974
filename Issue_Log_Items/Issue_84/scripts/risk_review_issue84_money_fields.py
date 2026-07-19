"""Issue #84 Risk — quantify quikclms money recon + component gaps (read-only)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[3]
OUT = BASE / "QLA_Migration" / "Output"
EVID = Path(__file__).resolve().parents[1] / "evidence"
EVID.mkdir(parents=True, exist_ok=True)

MONEY = [
    "MPAID",
    "MFACE",
    "DIVIDENDS",
    "LOAN",
    "NETDB",
    "PREMIUM",
    "SUSPENSE",
    "MINTRATE",
    "MINTAMT",
    "ADJUST",
]
TRACES = ["010360289C", "010391359C", "010150740C"]


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").fillna(0.0)


def main() -> int:
    clms = pd.read_csv(OUT / "quikclms.csv", dtype=str, keep_default_na=False)
    clmp = pd.read_csv(OUT / "quikclmp.csv", dtype=str, keep_default_na=False)
    i78 = pd.read_csv(
        BASE / "QLA_Migration" / "Reports" / "issue78_quikclmp_recovery_audit.csv",
        dtype=str,
        keep_default_na=False,
    )

    for f in MONEY:
        clms[f + "_n"] = _num(clms[f])

    pay = (
        clmp.assign(MAMOUNT_n=_num(clmp["MAMOUNT"]))
        .groupby(clmp["MPOLICY"].str.strip(), as_index=False)
        .agg(payee_sum=("MAMOUNT_n", "sum"), payee_rows=("MAMOUNT_n", "count"))
    )
    clms["MPOLICY_k"] = clms["MPOLICY"].str.strip()
    m = clms.merge(pay, left_on="MPOLICY_k", right_on="MPOLICY", how="left", suffixes=("", "_p"))
    m["payee_sum"] = m["payee_sum"].fillna(0.0)
    m["payee_rows"] = m["payee_rows"].fillna(0).astype(int)
    m["mpaid_payee_delta"] = (m["MPAID_n"] - m["payee_sum"]).round(2)
    m["has_payee"] = m["payee_rows"] > 0
    m["pddate_blank"] = m["PDDATE"].astype(str).str.strip().eq("")

    # Recon classes
    mismatch = m[m["has_payee"] & (m["mpaid_payee_delta"].abs() > 0.01)]
    header_zero_payee = m[m["has_payee"] & (m["MPAID_n"].abs() <= 0.01) & (m["payee_sum"] > 0.01)]
    header_zero_pddate = m[m["has_payee"] & m["pddate_blank"] & (m["payee_sum"] > 0.01)]

    # #78 recovered with header delta
    i78["header_mpaid_n"] = _num(i78["header_mpaid"])
    i78["payout_n"] = _num(i78["payout_amount"])
    i78["delta_n"] = _num(i78["header_mpaid_delta"])
    i78_backfill = i78[(i78["header_mpaid_n"].abs() <= 0.01) & (i78["payout_n"] > 0.01)]

    pop = {f: int((clms[f + "_n"] != 0).sum()) for f in MONEY}

    rows = []
    for _, r in m.iterrows():
        rows.append(
            {
                "mpolicy": r["MPOLICY_k"],
                "claimstat": str(r.get("CLAIMSTAT", "")).strip(),
                "mpaid": r["MPAID_n"],
                "mface": r["MFACE_n"],
                "dividends": r["DIVIDENDS_n"],
                "loan": r["LOAN_n"],
                "netdb": r["NETDB_n"],
                "premium": r["PREMIUM_n"],
                "suspense": r["SUSPENSE_n"],
                "mintrate": r["MINTRATE_n"],
                "mintamt": r["MINTAMT_n"],
                "adjust": r["ADJUST_n"],
                "pddate_blank": "Y" if r["pddate_blank"] else "N",
                "payee_rows": r["payee_rows"],
                "payee_sum": round(float(r["payee_sum"]), 2),
                "mpaid_payee_delta": float(r["mpaid_payee_delta"]),
                "recon_class": (
                    "HEADER_ZERO_HAS_PAYEE"
                    if (r["has_payee"] and abs(r["MPAID_n"]) <= 0.01 and r["payee_sum"] > 0.01)
                    else (
                        "MISMATCH"
                        if (r["has_payee"] and abs(r["mpaid_payee_delta"]) > 0.01)
                        else ("MATCH" if r["has_payee"] else "NO_PAYEE")
                    )
                ),
            }
        )
    audit = pd.DataFrame(rows)
    out_path = EVID / "issue84_risk_money_recon_simulation.csv"
    # Keep full recon detail but also a compact summary file for mismatches
    audit.to_csv(out_path, index=False)
    mismatch_path = EVID / "issue84_risk_money_mismatches.csv"
    audit[audit["recon_class"].isin(["MISMATCH", "HEADER_ZERO_HAS_PAYEE"])].to_csv(
        mismatch_path, index=False
    )

    print("=== Issue #84 Risk quantification ===")
    print(f"quikclms rows: {len(clms)}")
    print(f"quikclmp rows: {len(clmp)}")
    print(f"headers with >=1 payee: {(m.has_payee).sum()}")
    print(f"MPAID vs payee MISMATCH (>0.01): {len(mismatch)}")
    print(f"HEADER_ZERO_HAS_PAYEE: {len(header_zero_payee)}")
    print(f"has payee + blank PDDATE: {len(header_zero_pddate)}")
    print(f"#78 recovered with header MPAID~0: {len(i78_backfill)}")
    print(f"#78 sum payout where header 0: {i78_backfill['payout_n'].sum():.2f}")
    print("nonzero population:", pop)
    print(f"abs mismatch $ sum: {mismatch['mpaid_payee_delta'].abs().sum():.2f}")
    print(f"wrote {out_path}")
    print(f"wrote {mismatch_path}")

    print("\n=== TRACE ===")
    for p in TRACES:
        t = audit[audit.mpolicy == p]
        print(t.to_string(index=False) if len(t) else f"{p}: missing")

    # Family hint from memo
    print("\n=== MISMATCH by CLAIMSTAT ===")
    print(mismatch.CLAIMSTAT.astype(str).str.strip().value_counts().to_dict())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
