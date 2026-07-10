"""Category 18 — Global date sweep across all quik*.csv output files."""

from __future__ import annotations

from datetime import date

import pandas as pd

from data_governance.constants.valid_codes import DATE_COLUMNS
from data_governance.governance_config import HIGH, AuditFinding, make_finding
from data_governance.rules._helpers import col, date_out_of_range, max_allowed_date, parse_date, s


def check_global_dates(data: dict) -> list[AuditFinding]:
    """GDATE-001 — flag dates before 1900-01-01 or after today+12 months."""
    findings: list[AuditFinding] = []
    today = date.today()
    max_dt = max_allowed_date(today)
    date_cols_upper = {c.upper() for c in DATE_COLUMNS}

    for key, df in list(data.items()):
        if key.startswith("_") or df is None:
            continue
        if not isinstance(df, pd.DataFrame) or df.empty:
            continue
        # Only sweep quik* output-style frames
        key_l = str(key).lower()
        if not (key_l.startswith("quik") or key_l.endswith(".csv") and "quik" in key_l):
            # Still allow any loaded quik frame keyed without prefix edge cases
            if "quik" not in key_l:
                continue

        fname = key if key_l.endswith(".csv") else f"{key_l if key_l.endswith('.csv') else key}.csv"
        if not str(fname).lower().endswith(".csv"):
            fname = f"{fname}.csv"

        # Prefer known date columns; also try parse on name-hint columns
        candidate_cols = [
            c for c in df.columns
            if str(c).upper() in date_cols_upper
            or any(h in str(c).upper() for h in ("DATE", "DOB", "DT"))
        ]

        for c in candidate_cols:
            for idx, val in df[c].items():
                raw = s(val)
                if not raw:
                    continue
                d = parse_date(raw)
                if d is None:
                    # Non-parseable — skip silently (not necessarily a date column)
                    continue
                if not date_out_of_range(d, today):
                    continue
                pol_c = col(df, "MPOLICY", "PLAN", "MCLIENTID", "CLAIMNUM")
                key_val = s(df.loc[idx].get(pol_c)) if pol_c else str(idx)
                findings.append(
                    make_finding(
                        rule_id="GDATE-001",
                        rule_category="Global Dates",
                        severity=HIGH,
                        source_file=str(fname),
                        description="Dates must fall between 01/01/1900 and today plus 12 months.",
                        reason=(
                            f"File '{fname}' field '{c}' on record '{key_val}' "
                            f"has date '{raw}' which is outside the valid range "
                            f"01/01/1900 to {max_dt.isoformat()}. Review this date."
                        ),
                        field_name=str(c),
                        expected=f"1900-01-01 to {max_dt.isoformat()}",
                        actual=raw,
                        affected_keys=[key_val],
                        sample_records=[{"key": key_val, "field": str(c), "value": raw}],
                        affected_count=1,
                    )
                )

    return findings


# Back-compat alias used by earlier pipeline wiring
check_global_date_sweep = check_global_dates
