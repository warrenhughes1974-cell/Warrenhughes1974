"""Issue #79 — remap quikclms.CLAIMSTAT to Policy-book conventions (SD-79)."""

from __future__ import annotations

import os
from typing import Any

import pandas as pd

FAMILY_PATTERN = (
    r"(DEATH_CLAIM|SURRENDER_CLAIM|DISBURSEMENT_CLAIM|PARTIAL_SURRENDER|MATURITY_CLAIM)"
)
LIFECYCLE_PATTERN = r"\|(SETTLED|FUNDED|PAID|PARTIAL|OPEN|UNKNOWN)\b"


def _strip(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if not text or text.lower() in ("nan", "none"):
        return ""
    return text


def _parse_family(memo: str) -> str:
    hit = pd.Series([memo]).str.extract(FAMILY_PATTERN, expand=False).iloc[0]
    return _strip(hit) or "OTHER"


def _parse_lifecycle(memo: str) -> str:
    hit = pd.Series([memo]).str.extract(LIFECYCLE_PATTERN, expand=False).iloc[0]
    return _strip(hit)


def proposed_claimstat(
    family: str,
    lifecycle: str,
    has_payment: bool,
    mpaid_n: float,
    current: str,
) -> tuple[str, str]:
    """Return (proposed CLAIMSTAT, reason_code) per SD-79."""
    if family in ("SURRENDER_CLAIM", "PARTIAL_SURRENDER", "DISBURSEMENT_CLAIM"):
        return "99", "FAMILY_SURRENDER_BUCKET"
    if family == "MATURITY_CLAIM":
        return "98", "FAMILY_MATURITY"
    if family == "DEATH_CLAIM":
        if has_payment or mpaid_n > 0 or lifecycle in ("SETTLED", "PAID", "FUNDED"):
            return "2", "DEATH_PAID_IN_FULL"
        return "1", "DEATH_OPEN"
    return current, "UNCHANGED_OTHER"


def remap_quikclms_claimstat(
    clms_df: pd.DataFrame,
    clmp_df: pd.DataFrame | None = None,
    payment_policies: set[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (updated quikclms, audit dataframe). Does not modify ORIGSTTUS or money fields."""
    clms = clms_df.copy().fillna("")
    if payment_policies is None:
        if clmp_df is None or clmp_df.empty:
            payment_policies = set()
        else:
            payment_policies = set(clmp_df["MPOLICY"].astype(str).str.strip())

    audit_rows: list[dict[str, Any]] = []
    new_stats: list[str] = []

    for _, row in clms.iterrows():
        memo = _strip(row.get("MEMOTEXT", ""))
        family = _parse_family(memo)
        lifecycle = _parse_lifecycle(memo)
        mpolicy = _strip(row.get("MPOLICY", ""))
        before = _strip(row.get("CLAIMSTAT", ""))
        mpaid_n = float(pd.to_numeric(row.get("MPAID", 0), errors="coerce") or 0)
        has_pay = mpolicy in payment_policies
        after, reason = proposed_claimstat(family, lifecycle, has_pay, mpaid_n, before)
        new_stats.append(after)
        if before != after:
            audit_rows.append(
                {
                    "mpolicy": mpolicy,
                    "mphase": _strip(row.get("MPHASE", "")),
                    "claimnum": _strip(row.get("CLAIMNUM", "")),
                    "family": family,
                    "lifecycle": lifecycle,
                    "before_claimstat": before,
                    "after_claimstat": after,
                    "reason": reason,
                    "has_payment": "Y" if has_pay else "N",
                    "mpaid": _strip(row.get("MPAID", "")),
                    "pddate": _strip(row.get("PDDATE", "")),
                    "origsttus": _strip(row.get("ORIGSTTUS", "")),
                }
            )

    clms["CLAIMSTAT"] = new_stats
    return clms, pd.DataFrame(audit_rows)


def write_remap_audit(audit_df: pd.DataFrame, reports_dir: str) -> str:
    os.makedirs(reports_dir, exist_ok=True)
    path = os.path.join(reports_dir, "issue79_claimstat_remap_audit.csv")
    audit_df.to_csv(path, index=False, encoding="utf-8")
    return path
