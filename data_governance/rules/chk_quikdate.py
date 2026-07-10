"""Category 9 — QUIKDATE defaults."""

from __future__ import annotations

from data_governance.governance_config import ADVISORY, CRITICAL, AuditFinding, make_finding
from data_governance.rules._helpers import (
    col,
    get_df,
    last_day_previous_month,
    parse_date,
    s,
)

BILL_DATE_TYPES = (
    ("PACBILL", "PAC BILL", "PAC_BILL", "MPACBILL"),
    ("DIRBILL", "DIRECT BILL", "DIRECT_BILL", "MDIRBILL", "MDBILL"),
    ("REINBILL", "REINSURANCE BILL", "REINS_BILL", "MREINBILL", "MRBILL"),
)


def check_quikdate(data: dict) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    df = get_df(data, "quikdate", "quikdate.csv")
    expected = last_day_previous_month()

    if df is not None and not df.empty:
        row = df.iloc[0]
        for names in BILL_DATE_TYPES:
            fcol = col(df, *names)
            if not fcol:
                continue
            raw = s(row.get(fcol))
            d = parse_date(raw)
            label = names[0]
            if d != expected:
                findings.append(
                    make_finding(
                        rule_id="DATE-001",
                        rule_category="Date",
                        severity=CRITICAL,
                        source_file="quikdate.csv",
                        description="Bill dates must be last day of previous month.",
                        reason=(
                            f"QUIKDATE '{label}' date is '{raw}'. Expected last day of "
                            f"previous month: '{expected.isoformat()}'."
                        ),
                        field_name=fcol,
                        expected=expected.isoformat(),
                        actual=raw,
                        affected_keys=[label],
                        affected_count=1,
                    )
                )

        # DATE-002 defaults
        ach_c = col(df, "ACHFILEID")
        if ach_c:
            ach = s(row.get(ach_c))
            if ach not in ("0", "A"):
                findings.append(
                    make_finding(
                        rule_id="DATE-002",
                        rule_category="Date",
                        severity=ADVISORY,
                        source_file="quikdate.csv",
                        description="ACHFILEID default is 0 (numeric) or A (alpha).",
                        reason=(
                            f"QUIKDATE field 'ACHFILEID' = '{ach}', expected '0' or 'A'."
                        ),
                        field_name="ACHFILEID",
                        expected="0 or A",
                        actual=ach,
                        affected_keys=["ACHFILEID"],
                        affected_count=1,
                    )
                )
        esc_c = col(df, "ESCDATE")
        if esc_c and s(row.get(esc_c)):
            findings.append(
                make_finding(
                    rule_id="DATE-002",
                    rule_category="Date",
                    severity=ADVISORY,
                    source_file="quikdate.csv",
                    description="ESCDATE should be blank.",
                    reason=(
                        f"QUIKDATE field 'ESCDATE' = '{s(row.get(esc_c))}', expected ''."
                    ),
                    field_name="ESCDATE",
                    expected="",
                    actual=s(row.get(esc_c)),
                    affected_keys=["ESCDATE"],
                    affected_count=1,
                )
            )

    return findings


# Global date sweep lives in chk_dates.py (GDATE-001). Re-export for compatibility.
from data_governance.rules.chk_dates import check_global_date_sweep, check_global_dates  # noqa: E402
