"""Issue #79 — read-only CLAIMSTAT remap simulation (Policy-book rules). No production writes."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
EVID = ROOT / "Issue_Log_Items" / "Issue_79" / "evidence"
EVID.mkdir(parents=True, exist_ok=True)


def proposed(row: pd.Series) -> tuple[str, str]:
    fam = row["FAMILY"]
    life = row["LIFE"]
    haspay = bool(row["HAS_PAYMENT"]) or float(row["MPAID_N"]) > 0 or life in ("SETTLED", "PAID")
    if fam in ("SURRENDER_CLAIM", "PARTIAL_SURRENDER", "DISBURSEMENT_CLAIM"):
        return "99", "FAMILY_SURRENDER_BUCKET"
    if fam == "MATURITY_CLAIM":
        return "98", "FAMILY_MATURITY"
    if fam == "DEATH_CLAIM":
        if haspay or life in ("SETTLED", "PAID", "FUNDED"):
            if haspay or life in ("SETTLED", "PAID") or (
                life == "FUNDED" and (row["HAS_PAYMENT"] or float(row["MPAID_N"]) > 0)
            ):
                return "2", "DEATH_PAID_IN_FULL"
            if life == "FUNDED" and not row["HAS_PAYMENT"] and float(row["MPAID_N"]) <= 0:
                return "1", "DEATH_FUNDED_NO_PAY_KEEP_PENDING"
            return "2", "DEATH_CLOSED"
        return "1", "DEATH_OPEN"
    return str(row["CS"]), "UNCHANGED_OTHER"


def main() -> None:
    ours = pd.read_csv(
        ROOT / "QLA_Migration" / "Output" / "quikclms.csv", dtype=str, keep_default_na=False
    )
    pay = pd.read_csv(
        ROOT / "QLA_Migration" / "Output" / "quikclmp.csv", dtype=str, keep_default_na=False
    )
    has_pay = set(pay.MPOLICY.str.strip())
    ours["CS"] = ours.CLAIMSTAT.str.strip()
    ours["FAMILY"] = ours.MEMOTEXT.str.extract(
        r"(DEATH_CLAIM|SURRENDER_CLAIM|DISBURSEMENT_CLAIM|PARTIAL_SURRENDER|MATURITY_CLAIM)",
        expand=False,
    ).fillna("OTHER")
    ours["LIFE"] = ours.MEMOTEXT.str.extract(
        r"\|(SETTLED|FUNDED|PAID|PARTIAL|OPEN|UNKNOWN)\b", expand=False
    ).fillna("")
    ours["HAS_PAYMENT"] = ours.MPOLICY.str.strip().isin(has_pay)
    ours["MPAID_N"] = pd.to_numeric(ours.MPAID, errors="coerce").fillna(0)
    prop = ours.apply(lambda r: pd.Series(proposed(r), index=["PROPOSED", "REASON"]), axis=1)
    ours = pd.concat([ours, prop], axis=1)
    audit = ours[
        [
            "MPOLICY",
            "MPHASE",
            "CLAIMNUM",
            "FAMILY",
            "LIFE",
            "CS",
            "PROPOSED",
            "REASON",
            "HAS_PAYMENT",
            "MPAID",
            "PDDATE",
            "ORIGSTTUS",
        ]
    ].copy()
    audit.columns = [
        "mpolicy",
        "mphase",
        "claimnum",
        "family",
        "lifecycle",
        "before_claimstat",
        "after_claimstat",
        "reason",
        "has_payment",
        "mpaid",
        "pddate",
        "origsttus",
    ]
    out = EVID / "issue79_risk_claimstat_simulation.csv"
    audit.to_csv(out, index=False)
    print(f"Wrote {out} changes={int((ours.CS != ours.PROPOSED).sum())}")


if __name__ == "__main__":
    main()
