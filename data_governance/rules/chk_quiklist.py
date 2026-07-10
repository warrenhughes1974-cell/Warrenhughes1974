"""Category 8 — QUIKLIST group/list table checks."""

from __future__ import annotations

from data_governance.governance_config import ADVISORY, CRITICAL, AuditFinding, make_finding
from data_governance.rules._helpers import col, company_codes, get_df, s

LIST_DEFAULTS = {
    "MSORT": "N",
    "MLAPSEL": "0",
    "MLASPEH": "0",
    "MSTATUS": "A",
    "MBILLDAY": "0",
    "MBILLMODE": "0",
}


def check_quiklist(data: dict) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    df = get_df(data, "quiklist", "quiklist.csv")
    if df is None or df.empty:
        return findings

    comp = get_df(data, "quikcomp", "quikcomp.csv")
    valid_comp = company_codes(comp)

    grp_c = col(df, "MGROUP", "GROUP", "GROUPNO", "MGRP", "GNUMBER")
    comp_c = col(df, "MCOMP", "COMP", "COMPANY")
    bill_c = col(df, "MBILLNAME", "BILLNAME")

    if grp_c:
        counts: dict[str, int] = {}
        for _, row in df.iterrows():
            g = s(row.get(grp_c))
            if g:
                counts[g] = counts.get(g, 0) + 1
        for g, n in counts.items():
            if n > 1:
                findings.append(
                    make_finding(
                        rule_id="LIST-001",
                        rule_category="List",
                        severity=CRITICAL,
                        source_file="quiklist.csv",
                        description="Group numbers must be unique.",
                        reason=(
                            f"QUIKLIST group number '{g}' appears {n} times. "
                            f"Group numbers must be unique."
                        ),
                        field_name=grp_c,
                        expected="unique",
                        actual=str(n),
                        affected_keys=[g],
                        affected_count=n,
                    )
                )

    for _, row in df.iterrows():
        g = s(row.get(grp_c)) if grp_c else ""

        if comp_c:
            c = s(row.get(comp_c))
            if c and valid_comp and c not in valid_comp:
                findings.append(
                    make_finding(
                        rule_id="LIST-002",
                        rule_category="List",
                        severity=CRITICAL,
                        source_file="quiklist.csv",
                        description="QUIKLIST company code must exist in QUIKCOMP.",
                        reason=(
                            f"QUIKLIST group '{g}' has company code '{c}' not found in QUIKCOMP."
                        ),
                        field_name=comp_c,
                        expected="code in QUIKCOMP",
                        actual=c,
                        affected_keys=[g or c],
                        affected_count=1,
                    )
                )

        if bill_c and not s(row.get(bill_c)):
            findings.append(
                make_finding(
                    rule_id="LIST-003",
                    rule_category="List",
                    severity=CRITICAL,
                    source_file="quiklist.csv",
                    description="MBILLNAME must be populated for every group.",
                    reason=f"QUIKLIST group '{g}' has no MBILLNAME. This field is required.",
                    field_name="MBILLNAME",
                    expected="populated",
                    actual="",
                    affected_keys=[g],
                    affected_count=1,
                )
            )

        for field, default in LIST_DEFAULTS.items():
            fcol = col(df, field)
            if not fcol:
                continue
            actual = s(row.get(fcol))
            # Normalize numeric defaults
            if actual != default and not (default == "0" and actual in ("0", "0.0")):
                findings.append(
                    make_finding(
                        rule_id="LIST-004",
                        rule_category="List",
                        severity=ADVISORY,
                        source_file="quiklist.csv",
                        description="QUIKLIST default field values.",
                        reason=(
                            f"QUIKLIST group '{g}' field '{field}' = '{actual}', "
                            f"expected default '{default}'."
                        ),
                        field_name=field,
                        expected=default,
                        actual=actual,
                        affected_keys=[g],
                        affected_count=1,
                    )
                )

    return findings
