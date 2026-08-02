"""Issue #135 Phase A — force quikclms.MINTAMT = 0.00 on emit.

Client lock: interest is not needed on converted claims; paid amount stays in
MPAID / quikclmp. Does not alter MPAID, MAMOUNT, LOAN, DTOFDEATH, or eligibility.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

ZERO_MINTAMT = "0.00"


def force_mintamt_zero_row(qla_row: dict) -> dict:
    """Return a copy of a quikclms row dict with MINTAMT forced to 0.00."""
    out = dict(qla_row)
    out["MINTAMT"] = ZERO_MINTAMT
    return out


def apply_issue135_mintamt_zero(
    clms_df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Force every quikclms.MINTAMT to 0.00.

    Returns (updated_clms, stats).
    """
    stats: dict[str, Any] = {
        "rows_seen": 0,
        "rows_updated": 0,
        "nonzero_before": 0,
        "reason": "",
    }
    if clms_df is None or clms_df.empty:
        stats["reason"] = "empty_quikclms"
        return clms_df if clms_df is not None else pd.DataFrame(), stats
    if "MINTAMT" not in clms_df.columns:
        stats["reason"] = "missing_mintamt_column"
        return clms_df, stats

    clms = clms_df.copy().fillna("")
    stats["rows_seen"] = int(len(clms))
    before = pd.to_numeric(clms["MINTAMT"], errors="coerce").fillna(0.0)
    nonzero_mask = before.abs() > 0.00001
    stats["nonzero_before"] = int(nonzero_mask.sum())
    already_zero = clms["MINTAMT"].astype(str).str.strip() == ZERO_MINTAMT
    update_mask = ~already_zero
    stats["rows_updated"] = int(update_mask.sum())
    clms.loc[:, "MINTAMT"] = ZERO_MINTAMT
    if stats["rows_updated"] <= 0 and stats["nonzero_before"] <= 0:
        stats["reason"] = "already_zero"
    return clms, stats
