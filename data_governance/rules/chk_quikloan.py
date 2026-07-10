"""Category 14 — Loans (quikloan) checks."""

from __future__ import annotations

import os

import pandas as pd

from data_governance.governance_config import CRITICAL, HIGH, INFO, AuditFinding, make_finding
from data_governance.rules._helpers import col, get_df, policy_set, s, to_float


def check_quikloan(data: dict) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    ctx = data.get("_context") or {}
    df = get_df(data, "quikloan", "quikloan.csv")
    # Also accept staging candidates dataframe
    staging = get_df(data, "quikloan_staging", "quikloan_emit_candidates")

    check_df = df if df is not None else staging
    source_label = "quikloan.csv" if df is not None else "quikloan staging"

    if check_df is not None and not check_df.empty:
        mstr = get_df(data, "quikmstr", "quikmstr.csv")
        valid_pols = policy_set(mstr) if mstr is not None else None
        pol_c = col(check_df, "MPOLICY")
        date_c = col(check_df, "MLOANDATE")

        if pol_c:
            counts: dict[str, int] = {}
            for _, row in check_df.iterrows():
                p = s(row.get(pol_c))
                if p:
                    counts[p] = counts.get(p, 0) + 1
            for p, n in counts.items():
                if n > 1:
                    findings.append(
                        make_finding(
                            rule_id="LOAN-002",
                            rule_category="Loan",
                            severity=CRITICAL,
                            source_file=source_label,
                            description="No duplicate MPOLICY values in quikloan.",
                            reason=(
                                f"MPOLICY='{p}' appears {n} times in quikloan. "
                                f"Each policy may only have one loan master record."
                            ),
                            field_name="MPOLICY",
                            expected="unique",
                            actual=str(n),
                            affected_keys=[p],
                            affected_count=n,
                        )
                    )

        for _, row in check_df.iterrows():
            pol = s(row.get(pol_c)) if pol_c else ""
            if date_c and not s(row.get(date_c)):
                findings.append(
                    make_finding(
                        rule_id="LOAN-005",
                        rule_category="Loan",
                        severity=HIGH,
                        source_file=source_label,
                        description="MLOANDATE must be populated on every loan staging candidate.",
                        reason=(
                            f"quikloan staging record for MPOLICY='{pol}' "
                            f"has blank MLOANDATE. Loan date is required."
                        ),
                        field_name="MLOANDATE",
                        expected="populated",
                        actual="",
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )

    # RCN-004 — Info only
    ploan = get_df(data, "PLOAN", "ploan", "PLOAN.csv")
    src_cnt = None
    if ploan is not None:
        bal_c = col(ploan, "LOAN_BALANCE", "MLOANBAL", "BALANCE")
        pol_c = col(ploan, "POLICY_NUMBER", "MPOLICY", "POLICY")
        if pol_c and bal_c:
            seen = set()
            for _, row in ploan.iterrows():
                p = s(row.get(pol_c))
                bal = to_float(row.get(bal_c), 0) or 0
                if p and bal != 0:
                    seen.add(p)
            src_cnt = len(seen)
        else:
            src_cnt = len(ploan)

    stg_cnt = ctx.get("quikloan_candidate_count")
    if stg_cnt is None:
        if staging is not None:
            stg_cnt = len(policy_set(staging)) if col(staging, "MPOLICY") else len(staging)
        elif df is not None:
            stg_cnt = len(policy_set(df))
        else:
            # Try path from context
            stg_path = ctx.get("quikloan_staging_path") or ""
            if not stg_path:
                repo = ctx.get("repo_root") or ""
                candidate = os.path.join(
                    repo, "plan_analysis", "phase_l1_quikloan", "quikloan_emit_candidates.csv"
                )
                if os.path.isfile(candidate):
                    stg_path = candidate
            if stg_path and os.path.isfile(stg_path):
                try:
                    sdf = pd.read_csv(stg_path, dtype=str, low_memory=False)
                    stg_cnt = len(sdf)
                except Exception:
                    stg_cnt = None

    if src_cnt is not None and stg_cnt is not None:
        diff = int(src_cnt) - int(stg_cnt)
        findings.append(
            make_finding(
                rule_id="RCN-004",
                rule_category="Loan",
                severity=INFO,
                source_file="quikloan",
                description="PLOAN active count vs quikloan staging candidates (review only).",
                reason=(
                    f"PLOAN.csv contains {src_cnt} active loan "
                    f"records. quikloan staging has {stg_cnt} candidates. "
                    f"Difference: {diff}. Review to confirm expected variance."
                ),
                field_name="MPOLICY",
                expected=str(src_cnt),
                actual=str(stg_cnt),
                affected_keys=["RCN-004"],
                sample_records=[{"src_cnt": src_cnt, "stg_cnt": stg_cnt, "diff": diff}],
                affected_count=abs(diff),
            )
        )

    return findings
