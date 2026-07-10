"""Category 4 — QUIKCOMP company table checks."""

from __future__ import annotations

from data_governance.governance_config import CRITICAL, AuditFinding, make_finding
from data_governance.rules._helpers import col, get_df, s, finding_per_key


def check_quikcomp(data: dict) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    comp = get_df(data, "quikcomp", "quikcomp.csv")
    mstr = get_df(data, "quikmstr", "quikmstr.csv")
    agts = get_df(data, "quikagts", "quikagts.csv")

    valid_codes: set[str] = set()
    if comp is not None and not comp.empty:
        code_col = col(comp, "MCOMP", "COMP", "COMPANY", "COMPCODE", "CCOMP")
        if code_col:
            counts: dict[str, int] = {}
            for _, row in comp.iterrows():
                code = s(row.get(code_col))
                if not code:
                    continue
                counts[code] = counts.get(code, 0) + 1
            valid_codes = set(counts.keys())
            # COMP-001
            for code, n in counts.items():
                if n > 1:
                    findings.append(
                        make_finding(
                            rule_id="COMP-001",
                            rule_category="Company",
                            severity=CRITICAL,
                            source_file="quikcomp.csv",
                            description="Company codes must be unique in quikcomp.",
                            reason=(
                                f"Company code '{code}' appears {n} times in quikcomp. "
                                f"Company codes must be unique."
                            ),
                            field_name=code_col,
                            expected="unique",
                            actual=str(n),
                            affected_keys=[code],
                            affected_count=n,
                        )
                    )

    # COMP-002 — agent company codes
    if agts is not None and not agts.empty:
        agt_id = col(agts, "MAGENT", "AGENT", "MAGENTID")
        agt_comp = col(agts, "MCOMP", "COMP", "COMPANY")
        if agt_comp:
            items = []
            for _, row in agts.iterrows():
                code = s(row.get(agt_comp))
                aid = s(row.get(agt_id)) if agt_id else ""
                if code and code not in valid_codes:
                    items.append((
                        aid or code,
                        code,
                        f"Agent record '{aid}' has company code '{code}' which does not exist in quikcomp.",
                    ))
            findings.extend(
                finding_per_key(
                    "COMP-002", "Company", CRITICAL, "quikagts.csv",
                    "Every agent company code must exist in quikcomp.",
                    agt_comp, "code in quikcomp", items,
                )
            )

    # COMP-003 / COMP-004 — policy suffix and length
    if mstr is not None and not mstr.empty:
        pol_col = col(mstr, "MPOLICY")
        if pol_col:
            suffix_items = []
            length_items = []
            for _, row in mstr.iterrows():
                pol = s(row.get(pol_col))
                if not pol:
                    continue
                n = len(pol)
                if n < 9 or n > 10:
                    length_items.append((
                        pol,
                        str(n),
                        f"Policy '{pol}' is {n} characters long. Policy numbers must be between 9 and 10 characters.",
                    ))
                suffix = pol[-1]
                if valid_codes and suffix not in valid_codes:
                    # Also try matching as full company code if policies use multi-char suffix
                    # Spec: last character must exist as registered suffix in quikcomp
                    suffix_items.append((
                        pol,
                        suffix,
                        f"Policy '{pol}' ends with '{suffix}' which is not a registered suffix in quikcomp.",
                    ))
            findings.extend(
                finding_per_key(
                    "COMP-004", "Company", CRITICAL, "quikmstr.csv",
                    "Policy numbers must be 9 or 10 characters.",
                    "MPOLICY", "9 or 10 characters", length_items,
                )
            )
            findings.extend(
                finding_per_key(
                    "COMP-003", "Company", CRITICAL, "quikmstr.csv",
                    "Policy number last character must be a registered company suffix.",
                    "MPOLICY", "suffix in quikcomp", suffix_items,
                )
            )

    return findings
