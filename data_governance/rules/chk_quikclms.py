"""Category 13 — Claims (quikclms / quikclmp) checks."""

from __future__ import annotations

from data_governance.constants.valid_codes import (
    GOVERNANCE_METADATA_COLUMNS,
    LOAN_TRANSACTION_CODES,
)
from data_governance.governance_config import CRITICAL, AuditFinding, make_finding
from data_governance.rules._helpers import col, get_df, policy_set, s


def _is_loan_code(code: str) -> bool:
    if not code:
        return False
    candidates = {code, code.lstrip("0") or "0", code.zfill(4)}
    return bool(candidates & LOAN_TRANSACTION_CODES) or code in LOAN_TRANSACTION_CODES


def check_quikclms(data: dict) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    clms = get_df(data, "quikclms", "quikclms.csv")
    clmp = get_df(data, "quikclmp", "quikclmp.csv")
    mstr = get_df(data, "quikmstr", "quikmstr.csv")
    valid_pols = policy_set(mstr) if mstr is not None else None

    if clms is not None and not clms.empty:
        pol_c = col(clms, "MPOLICY")
        claim_c = col(clms, "CLAIMNUM")

        if claim_c:
            counts: dict[str, int] = {}
            for _, row in clms.iterrows():
                cn = s(row.get(claim_c))
                if cn:
                    counts[cn] = counts.get(cn, 0) + 1
            for cn, n in counts.items():
                if n > 1:
                    findings.append(
                        make_finding(
                            rule_id="DUP-008",
                            rule_category="Claims",
                            severity=CRITICAL,
                            source_file="quikclms.csv",
                            description="CLAIMNUM must be unique.",
                            reason=(
                                f"CLAIMNUM='{cn}' appears {n} times in quikclms. "
                                f"Claim numbers must be unique."
                            ),
                            field_name="CLAIMNUM",
                            expected="unique",
                            actual=str(n),
                            affected_keys=[cn],
                            affected_count=n,
                        )
                    )

        for _, row in clms.iterrows():
            pol = s(row.get(pol_c)) if pol_c else ""
            clm = s(row.get(claim_c)) if claim_c else ""
            if pol and valid_pols is not None and pol not in valid_pols:
                reason = (
                    f"quikclms CLAIMNUM='{clm}' references "
                    f"MPOLICY='{pol}' which does not exist in quikmstr. "
                    f"Orphan claim record."
                )
                # Implement once; report under both REF-003 and CLM-001
                for rule_id in ("REF-003", "CLM-001"):
                    findings.append(
                        make_finding(
                            rule_id=rule_id,
                            rule_category="Claims",
                            severity=CRITICAL,
                            source_file="quikclms.csv",
                            description="Every MPOLICY in quikclms must exist in quikmstr.",
                            reason=reason,
                            field_name="MPOLICY",
                            expected="policy in quikmstr",
                            actual=pol,
                            affected_keys=[pol],
                            affected_count=1,
                        )
                    )

        for fname, frame in (("quikclms.csv", clms), ("quikclmp.csv", clmp)):
            if frame is None:
                continue
            leak = [
                c for c in frame.columns
                if str(c).lower() in {x.lower() for x in GOVERNANCE_METADATA_COLUMNS}
            ]
            for col_name in leak:
                findings.append(
                    make_finding(
                        rule_id="CLM-011",
                        rule_category="Claims",
                        severity=CRITICAL,
                        source_file=fname,
                        description="Governance metadata columns must not appear in claims output.",
                        reason=(
                            f"{fname.replace('.csv', '')} output contains governance metadata "
                            f"column '{col_name}'. Internal audit columns must be stripped "
                            f"before output is written."
                        ),
                        field_name=str(col_name),
                        expected="no governance columns",
                        actual=str(col_name),
                        affected_keys=[str(col_name)],
                        affected_count=1,
                    )
                )

    # CLM-006
    pactg = get_df(data, "PACTG", "pactg", "PACTG_Accounting_Extract")
    if pactg is not None and clms is not None and not clms.empty:
        claim_pols = policy_set(clms)
        tcol = col(pactg, "TRANSACTION_CODE", "TRANCODE", "TCODE")
        pcol = col(pactg, "POLICY_NUMBER", "MPOLICY", "POLICY")
        if tcol and pcol:
            by_pol: dict[str, set[str]] = {}
            for _, row in pactg.iterrows():
                p = s(row.get(pcol))
                c = s(row.get(tcol))
                if p:
                    by_pol.setdefault(p, set()).add(c)
            for p, codes in by_pol.items():
                if p not in claim_pols or not codes:
                    continue
                if all(_is_loan_code(c) for c in codes):
                    findings.append(
                        make_finding(
                            rule_id="CLM-006",
                            rule_category="Claims",
                            severity=CRITICAL,
                            source_file="quikclms.csv",
                            description="Borrowed-money-only PACTG activity must not emit as claims.",
                            reason=(
                                f"quikclms MPOLICY='{p}' has only "
                                f"borrowed-money-only activity in PACTG source data. "
                                f"This policy should not appear in claims output."
                            ),
                            field_name="MPOLICY",
                            expected="claim-eligible activity",
                            actual=str(sorted(codes)),
                            affected_keys=[p],
                            affected_count=1,
                        )
                    )

    return findings
