"""Category 12 — Premium history (quikprmh) checks."""

from __future__ import annotations

from data_governance.constants.valid_codes import LOAN_TRANSACTION_CODES
from data_governance.governance_config import CRITICAL, HIGH, AuditFinding, make_finding
from data_governance.rules._helpers import col, get_df, policy_set, s


def _is_loan_code(code: str) -> bool:
    if not code:
        return False
    candidates = {code, code.lstrip("0") or "0", code.zfill(4)}
    return bool(candidates & LOAN_TRANSACTION_CODES) or code in LOAN_TRANSACTION_CODES


def check_quikprmh(data: dict) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    df = get_df(data, "quikprmh", "quikprmh.csv")
    if df is None or df.empty:
        return findings

    mstr = get_df(data, "quikmstr", "quikmstr.csv")
    valid_pols = policy_set(mstr) if mstr is not None else None

    pol_c = col(df, "MPOLICY")
    date_c = col(df, "DATEPAID")
    code_c = col(df, "TRANSACTION_CODE", "TRANCODE", "MSOURCE", "TCODE")

    for _, row in df.iterrows():
        pol = s(row.get(pol_c)) if pol_c else ""

        if pol and valid_pols is not None and pol not in valid_pols:
            findings.append(
                make_finding(
                    rule_id="REF-002",
                    rule_category="Premium History",
                    severity=CRITICAL,
                    source_file="quikprmh.csv",
                    description="Every MPOLICY in quikprmh must exist in quikmstr.",
                    reason=(
                        f"quikprmh record for MPOLICY='{pol}' has no "
                        f"matching policy in quikmstr. Orphan premium history record."
                    ),
                    field_name="MPOLICY",
                    expected="policy in quikmstr",
                    actual=pol,
                    affected_keys=[pol],
                    affected_count=1,
                )
            )

        if date_c and not s(row.get(date_c)):
            findings.append(
                make_finding(
                    rule_id="PRM-010",
                    rule_category="Premium History",
                    severity=HIGH,
                    source_file="quikprmh.csv",
                    description="DATEPAID must be populated on every quikprmh row.",
                    reason=(
                        f"quikprmh MPOLICY='{pol}' row has blank DATEPAID. "
                        f"Payment date is required on all premium history records."
                    ),
                    field_name="DATEPAID",
                    expected="populated",
                    actual="",
                    affected_keys=[pol],
                    affected_count=1,
                )
            )

        if code_c:
            code = s(row.get(code_c))
            if _is_loan_code(code):
                findings.append(
                    make_finding(
                        rule_id="PRM-009",
                        rule_category="Premium History",
                        severity=CRITICAL,
                        source_file="quikprmh.csv",
                        description="Loan/borrowed-money codes must not appear in premium history.",
                        reason=(
                            f"quikprmh MPOLICY='{pol}' contains transaction "
                            f"code '{code}' which is a loan/borrowed-money code. These "
                            f"must not appear in premium history."
                        ),
                        field_name=code_c,
                        expected="non-loan code",
                        actual=code,
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )

    return findings
