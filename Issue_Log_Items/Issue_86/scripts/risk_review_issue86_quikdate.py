"""Read-only Issue #86 risk simulation: current QuikDate emit vs locked full rebuild.

Does not modify production converters or Output.
"""

from __future__ import annotations

import csv
import os
from datetime import date
from typing import Any

from data_governance.data_access.normalization import prior_month_end
from qla_core.quikdate_converter import QUIKDATE_SCHEMA, build_quikdate_governance_row, format_qla_date

ISSUE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
EVIDENCE_DIR = os.path.join(ISSUE_DIR, "evidence")

DATE_FIELDS = {
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


def build_proposed_row(run_date: date) -> dict[str, Any]:
    """Locked D1-A / D2-A / D3-A full rebuild row."""
    pme_s = format_qla_date(prior_month_end(run_date))
    row: dict[str, Any] = {field: "" for field in QUIKDATE_SCHEMA}
    for field in DATE_FIELDS:
        row[field] = pme_s
    row["ESC_DATE"] = ""
    row["PDUEDAYS"] = 31
    row["VERSION"] = "5.318"
    row["UPDATENUM"] = 359
    row["ACHFILEID"] = 0
    row["ACHFILEID2"] = "A"
    return row


def main(run_date: date | None = None) -> str:
    run = run_date or date.today()
    current = build_quikdate_governance_row(run)
    proposed = build_proposed_row(run)
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    out_path = os.path.join(EVIDENCE_DIR, "issue86_risk_before_after.csv")
    changed = 0
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "field",
                "current_emit",
                "proposed_D1A_D2A_D3A",
                "changes",
                "notes",
            ]
        )
        for field in QUIKDATE_SCHEMA:
            c = current[field]
            p = proposed[field]
            ch = "Y" if str(c) != str(p) else "N"
            if ch == "Y":
                changed += 1
            note = ""
            if field in ("PACBILL", "DIRBILL", "REINBILL", "ACHFILEID", "ACHFILEID2", "ESC_DATE"):
                note = "unchanged vs DG-R-003 partial emit"
            elif field in DATE_FIELDS:
                note = "fill blank date with PME"
            else:
                note = "screenshot non-date default"
            w.writerow([field, c, p, ch, note])
    print(f"run_date={run.isoformat()} prior_month_end={prior_month_end(run).isoformat()}")
    print(f"fields_changed={changed} of {len(QUIKDATE_SCHEMA)}")
    print(f"wrote {out_path}")
    return out_path


if __name__ == "__main__":
    main(date(2026, 7, 19))
