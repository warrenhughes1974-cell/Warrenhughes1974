"""Category 7 — QUIKACTG and QUIKCHRT checks."""

from __future__ import annotations

from data_governance.governance_config import ADVISORY, CRITICAL, HIGH, AuditFinding, make_finding
from data_governance.rules._helpers import col, company_codes, get_df, plan_codes, s


def check_quikactg_chrt(data: dict) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    actg = get_df(data, "quikactg", "quikactg.csv")
    chrt = get_df(data, "quikchrt", "quikchrt.csv")
    comp = get_df(data, "quikcomp", "quikcomp.csv")
    plan = get_df(data, "quikplan", "quikplan.csv")

    valid_comp = company_codes(comp)
    valid_plans = plan_codes(plan)

    # ACTG-001 / ACTG-002
    if actg is not None and not actg.empty:
        ccol = col(actg, "MCOMP", "COMP", "COMPANY")
        # Account number may be MPREM1ST or a dedicated account field; use MPLAN as chart key per schema
        # Spec: key is company + account number. Prefer MACCT / ACCOUNT / MPREM1ST as account proxy.
        acol = col(actg, "MACCT", "ACCOUNT", "ACCTNO", "MPREM1ST")
        pcol = col(actg, "MPLAN", "PLAN")

        if ccol and acol:
            seen: dict[tuple[str, str], int] = {}
            for _, row in actg.iterrows():
                c = s(row.get(ccol))
                a = s(row.get(acol))
                if not c and not a:
                    continue
                key = (c, a)
                seen[key] = seen.get(key, 0) + 1
            for (c, a), n in seen.items():
                if n > 1:
                    findings.append(
                        make_finding(
                            rule_id="ACTG-001",
                            rule_category="Accounting",
                            severity=CRITICAL,
                            source_file="quikactg.csv",
                            description="QUIKACTG key company+account must be unique.",
                            reason=f"QUIKACTG has duplicate record for company '{c}' + account '{a}'.",
                            field_name=f"{ccol}+{acol}",
                            expected="unique",
                            actual=str(n),
                            affected_keys=[f"{c}|{a}"],
                            affected_count=n,
                        )
                    )

        if ccol:
            for _, row in actg.iterrows():
                c = s(row.get(ccol))
                if c and valid_comp and c not in valid_comp:
                    findings.append(
                        make_finding(
                            rule_id="ACTG-002",
                            rule_category="Accounting",
                            severity=CRITICAL,
                            source_file="quikactg.csv",
                            description="QUIKACTG company code must exist in QUIKCOMP.",
                            reason=f"QUIKACTG company code '{c}' does not exist in QUIKCOMP.",
                            field_name=ccol,
                            expected="code in QUIKCOMP",
                            actual=c,
                            affected_keys=[c],
                            affected_count=1,
                        )
                    )

        # ACTG-005 MASTER plan all caps
        if pcol and ccol:
            for _, row in actg.iterrows():
                p = s(row.get(pcol))
                c = s(row.get(ccol))
                if p.upper() == "MASTER" or p == "MASTER":
                    if p != p.upper() or not p.isupper():
                        findings.append(
                            make_finding(
                                rule_id="ACTG-005",
                                rule_category="Accounting",
                                severity=HIGH,
                                source_file="quikactg.csv",
                                description="Default MASTER plan must be all caps.",
                                reason=(
                                    f"QUIKACTG default MASTER plan '{p}' for company '{c}' is not all caps."
                                ),
                                field_name=pcol,
                                expected="MASTER",
                                actual=p,
                                affected_keys=[c],
                                affected_count=1,
                            )
                        )
                # Also flag if plan looks like master but mixed case
                if p and p.upper() == "MASTER" and p != "MASTER":
                    pass  # already handled

        # ACTG-006 plan assignment
        if pcol and valid_plans:
            for _, row in actg.iterrows():
                p = s(row.get(pcol))
                c = s(row.get(ccol)) if ccol else ""
                if p and p.upper() != "MASTER" and p not in valid_plans:
                    findings.append(
                        make_finding(
                            rule_id="ACTG-006",
                            rule_category="Accounting",
                            severity=ADVISORY,
                            source_file="quikactg.csv",
                            description="Plan assignment must exist in QUIKPLAN when assigning by plan.",
                            reason=(
                                f"QUIKACTG plan assignment '{p}' for company '{c}' does not exist in QUIKPLAN."
                            ),
                            field_name=pcol,
                            expected="plan in QUIKPLAN",
                            actual=p,
                            affected_keys=[p],
                            affected_count=1,
                        )
                    )

    # ACTG-003 QUIKCHRT duplicates company+plan
    chrt_keys: set[tuple[str, str]] = set()
    if chrt is not None and not chrt.empty:
        ccol = col(chrt, "MCOMP", "COMP", "COMPANY")
        pcol = col(chrt, "MPLAN", "PLAN")
        if ccol and pcol:
            seen = {}
            for _, row in chrt.iterrows():
                c = s(row.get(ccol))
                p = s(row.get(pcol))
                key = (c, p)
                seen[key] = seen.get(key, 0) + 1
                chrt_keys.add(key)
            for (c, p), n in seen.items():
                if n > 1:
                    findings.append(
                        make_finding(
                            rule_id="ACTG-003",
                            rule_category="Accounting",
                            severity=CRITICAL,
                            source_file="quikchrt.csv",
                            description="QUIKCHRT key company+plan must be unique.",
                            reason=f"QUIKCHRT has duplicate record for company '{c}' + plan '{p}'.",
                            field_name=f"{ccol}+{pcol}",
                            expected="unique",
                            actual=str(n),
                            affected_keys=[f"{c}|{p}"],
                            affected_count=n,
                        )
                    )

    # ACTG-004 actg entries exist in chrt by company
    if actg is not None and chrt is not None and chrt_keys:
        ccol = col(actg, "MCOMP", "COMP", "COMPANY")
        pcol = col(actg, "MPLAN", "PLAN")
        acol = col(actg, "MACCT", "ACCOUNT", "ACCTNO", "MPREM1ST")
        if ccol and pcol:
            for _, row in actg.iterrows():
                c = s(row.get(ccol))
                p = s(row.get(pcol))
                a = s(row.get(acol)) if acol else p
                if c and (c, p) not in chrt_keys and (c, a) not in chrt_keys:
                    # Match by company presence in chrt
                    company_in_chrt = any(ck[0] == c for ck in chrt_keys)
                    if not company_in_chrt or (c, p) not in chrt_keys:
                        findings.append(
                            make_finding(
                                rule_id="ACTG-004",
                                rule_category="Accounting",
                                severity=CRITICAL,
                                source_file="quikactg.csv",
                                description="QUIKACTG entries must exist in QUIKCHRT by company.",
                                reason=(
                                    f"QUIKACTG account '{a}' for company '{c}' has no corresponding "
                                    f"record in QUIKCHRT."
                                ),
                                field_name=acol or pcol,
                                expected="record in QUIKCHRT",
                                actual=f"{c}|{a}",
                                affected_keys=[f"{c}|{a}"],
                                affected_count=1,
                            )
                        )

    return findings
