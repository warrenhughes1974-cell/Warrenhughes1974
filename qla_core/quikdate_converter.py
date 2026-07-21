"""QuikDate governance defaults emit (DG-R-003 / Issue #86 / DG-QUIKDATE-001..006).

Writes a single-row quikdate.csv — full system-control rebuild:
- Date fields (except ESC_DATE) = prior_month_end(conversion_run_date)
- Non-date fields = locked screenshot defaults (Issue #86 D1-A/D2-A/D3-A)
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

# Issue #86 — screenshot / Data_Goverence non-date defaults (not crosswalk-sourced).
QUIKDATE_PME_DATE_FIELDS = frozenset(
    {
        "PROCDATE",
        "ANNDATE",
        "DIRBILL",
        "PACBILL",
        "GRPBILL",
        "APLBILL",
        "LOANBILL",
        "REINBILL",
        "CPNBILL",
        "CCBILL",
    }
)
QUIKDATE_DEFAULT_PDUEDAYS = 31
QUIKDATE_DEFAULT_VERSION = "5.318"
QUIKDATE_DEFAULT_UPDATENUM = 359
QUIKDATE_DEFAULT_ACHFILEID = 0
QUIKDATE_DEFAULT_ACHFILEID2 = "A"


def format_qla_date(value: date | None) -> str:
    """QLA CSV date format used by other converters (YYYYMMDD)."""
    if value is None:
        return ""
    return value.strftime("%Y%m%d")


def build_quikdate_governance_row(conversion_run_date: date | None = None) -> dict[str, Any]:
    """Build one QuikDate row — full rebuild per Issue #86 locked defaults.

    All date fields except ESC_DATE = prior_month_end(conversion_run_date).
    ESC_DATE blank; PDUEDAYS/VERSION/UPDATENUM/ACH* = screenshot defaults.
    Satisfies DG-QUIKDATE-001..006.
    """
    run_date = conversion_run_date or date.today()
    pme_s = format_qla_date(prior_month_end(run_date))
    row: dict[str, Any] = {field: "" for field in QUIKDATE_SCHEMA}
    for field in QUIKDATE_PME_DATE_FIELDS:
        row[field] = pme_s
    row["ESC_DATE"] = ""
    row["PDUEDAYS"] = QUIKDATE_DEFAULT_PDUEDAYS
    row["VERSION"] = QUIKDATE_DEFAULT_VERSION
    row["UPDATENUM"] = QUIKDATE_DEFAULT_UPDATENUM
    row["ACHFILEID"] = QUIKDATE_DEFAULT_ACHFILEID
    row["ACHFILEID2"] = QUIKDATE_DEFAULT_ACHFILEID2
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
        "PROCDATE": row["PROCDATE"],
        "PDUEDAYS": row["PDUEDAYS"],
        "VERSION": row["VERSION"],
        "UPDATENUM": row["UPDATENUM"],
        "ACHFILEID": row["ACHFILEID"],
        "ACHFILEID2": row["ACHFILEID2"],
        "ESC_DATE": row["ESC_DATE"],
        "emitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
