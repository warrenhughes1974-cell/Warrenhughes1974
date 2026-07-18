"""QuikDate governance defaults emit (DG-R-003 / DG-QUIKDATE-001..006).

Writes a single-row quikdate.csv with prior-month-end bill dates and ACH defaults.
Uses the same prior_month_end definition as data_governance (shared import).
"""

from __future__ import annotations

import os
from datetime import date, datetime
from typing import Any

import pandas as pd

from data_governance.data_access.normalization import prior_month_end

# Live QUIKDATE.dbf field order (Q:\CSO region schema verification).
QUIKDATE_SCHEMA = [
    "PROCDATE",
    "ESC_DATE",
    "ANNDATE",
    "DIRBILL",
    "PDUEDAYS",
    "PACBILL",
    "GRPBILL",
    "APLBILL",
    "LOANBILL",
    "REINBILL",
    "CPNBILL",
    "VERSION",
    "UPDATENUM",
    "CCBILL",
    "ACHFILEID",
    "ACHFILEID2",
]


def format_qla_date(value: date | None) -> str:
    """QLA CSV date format used by other converters (YYYYMMDD)."""
    if value is None:
        return ""
    return value.strftime("%Y%m%d")


def build_quikdate_governance_row(conversion_run_date: date | None = None) -> dict[str, Any]:
    """Build one QuikDate row satisfying DG-QUIKDATE-001..006.

    PACBILL/DIRBILL/REINBILL = prior_month_end(conversion_run_date).
    ACHFILEID=0, ACHFILEID2=A, ESC_DATE blank.
    Other schema fields left blank (no invented business values).
    """
    run_date = conversion_run_date or date.today()
    pme = prior_month_end(run_date)
    pme_s = format_qla_date(pme)
    row = {field: "" for field in QUIKDATE_SCHEMA}
    row["PACBILL"] = pme_s
    row["DIRBILL"] = pme_s
    row["REINBILL"] = pme_s
    row["ACHFILEID"] = 0
    row["ACHFILEID2"] = "A"
    row["ESC_DATE"] = ""
    return row


def emit_quikdate_csv(
    output_dir: str,
    conversion_run_date: date | None = None,
) -> dict[str, Any]:
    """Write quikdate.csv to output_dir. Returns path/stats dict."""
    run_date = conversion_run_date or date.today()
    row = build_quikdate_governance_row(run_date)
    df = pd.DataFrame([row], columns=QUIKDATE_SCHEMA)
    out_path = os.path.normpath(os.path.join(output_dir, "quikdate.csv"))
    os.makedirs(output_dir, exist_ok=True)
    df.to_csv(out_path, index=False)
    return {
        "path": out_path,
        "row_count": 1,
        "conversion_run_date": run_date.isoformat(),
        "prior_month_end": prior_month_end(run_date).isoformat(),
        "PACBILL": row["PACBILL"],
        "DIRBILL": row["DIRBILL"],
        "REINBILL": row["REINBILL"],
        "ACHFILEID": row["ACHFILEID"],
        "ACHFILEID2": row["ACHFILEID2"],
        "ESC_DATE": row["ESC_DATE"],
        "emitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
