"""Issue #84 Track A — backfill quikclms MPAID/PDDATE from claim-keyed quikclmp payees."""

from __future__ import annotations

import os
from typing import Any

import pandas as pd

RULE_ID = "Issue-84-Track-A"
MPAID_TOLERANCE = 0.01


def _strip(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if not text or text.lower() in ("nan", "none"):
        return ""
    return text


def _money(value: Any) -> float:
    try:
        return float(str(value).replace(",", "").strip() or 0)
    except (TypeError, ValueError):
        return 0.0


def _money_str(value: float) -> str:
    return f"{float(value):.2f}"


def _is_blank_mpaid(value: Any) -> bool:
    return abs(_money(value)) <= MPAID_TOLERANCE


def _normalize_date_yyyymmdd(value: Any) -> str:
    text = _strip(value)
    if not text:
        return ""
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 8:
        return digits[:8]
    return ""


def _claim_key(mpolicy: Any, mphase: Any) -> tuple[str, str]:
    return _strip(mpolicy), _strip(mphase)


def _build_payee_aggregates(clmp_df: pd.DataFrame) -> dict[tuple[str, str], dict[str, Any]]:
    if clmp_df is None or clmp_df.empty:
        return {}

    clmp = clmp_df.copy().fillna("")
    if "MPOLICY" not in clmp.columns:
        return {}

    phase_col = "MPHASE" if "MPHASE" in clmp.columns else None
    aggregates: dict[tuple[str, str], dict[str, Any]] = {}

    for _, row in clmp.iterrows():
        key = _claim_key(row.get("MPOLICY", ""), row.get("MPHASE", "") if phase_col else "")
        amount = _money(row.get("MAMOUNT", 0))
        pay_date = _normalize_date_yyyymmdd(row.get("MPMTDATE", ""))
        if not pay_date:
            pay_date = _normalize_date_yyyymmdd(row.get("MCHKDATE", ""))

        bucket = aggregates.setdefault(
            key,
            {"payee_sum": 0.0, "payee_rows": 0, "payee_dates": []},
        )
        bucket["payee_sum"] += amount
        bucket["payee_rows"] += 1
        if pay_date:
            bucket["payee_dates"].append(pay_date)

    for bucket in aggregates.values():
        dates = sorted(set(bucket.pop("payee_dates", [])))
        bucket["payee_pddate"] = dates[-1] if dates else ""
        bucket["payee_sum"] = round(float(bucket["payee_sum"]), 2)

    return aggregates


def backfill_quikclms_headers_from_payees(
    clms_df: pd.DataFrame,
    clmp_df: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """When MPAID is blank/zero and claim-keyed payees exist, backfill header MPAID/PDDATE."""
    clms = clms_df.copy().fillna("")
    payees = _build_payee_aggregates(clmp_df if clmp_df is not None else pd.DataFrame())
    audit_rows: list[dict[str, Any]] = []

    for idx, row in clms.iterrows():
        key = _claim_key(row.get("MPOLICY", ""), row.get("MPHASE", ""))
        pay = payees.get(key)
        if not pay or pay["payee_rows"] <= 0 or pay["payee_sum"] <= MPAID_TOLERANCE:
            continue
        if not _is_blank_mpaid(row.get("MPAID", "")):
            continue

        before_mpaid = _strip(row.get("MPAID", ""))
        before_pddate = _strip(row.get("PDDATE", ""))
        after_mpaid = _money_str(pay["payee_sum"])
        after_pddate = before_pddate or pay.get("payee_pddate", "")

        clms.at[idx, "MPAID"] = after_mpaid
        if not before_pddate and after_pddate:
            clms.at[idx, "PDDATE"] = after_pddate

        audit_rows.append(
            {
                "table": "QuikClms",
                "mpolicy": key[0],
                "mphase": key[1],
                "claimnum": _strip(row.get("CLAIMNUM", "")),
                "claimstat": _strip(row.get("CLAIMSTAT", "")),
                "field": "MPAID" + (",PDDATE" if not before_pddate and after_pddate else ""),
                "before_mpaid": before_mpaid,
                "after_mpaid": after_mpaid,
                "before_pddate": before_pddate,
                "after_pddate": _strip(clms.at[idx, "PDDATE"]) if "PDDATE" in clms.columns else "",
                "payee_sum": after_mpaid,
                "payee_rows": pay["payee_rows"],
                "payee_pddate_source": pay.get("payee_pddate", ""),
                "reason": "Header MPAID blank with live payee rows; backfilled from claim-keyed payee sum",
                "rule_id": RULE_ID,
            }
        )

    return clms, pd.DataFrame(audit_rows)


def write_money_field_audit(audit_df: pd.DataFrame, reports_dir: str) -> str:
    os.makedirs(reports_dir, exist_ok=True)
    path = os.path.join(reports_dir, "issue84_money_field_audit.csv")
    audit_df.to_csv(path, index=False, encoding="utf-8")
    return path
