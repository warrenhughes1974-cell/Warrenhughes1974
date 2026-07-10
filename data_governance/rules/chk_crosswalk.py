"""Category 3 — Crosswalk mapping integrity."""

from __future__ import annotations

from data_governance.governance_config import CRITICAL, AuditFinding, make_finding
from data_governance.rules._helpers import col, get_df, s


def check_crosswalk(data: dict) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    df = get_df(data, "Master_Crosswalk", "master_crosswalk", "Master_Crosswalk.csv")
    if df is None or df.empty:
        return findings

    src_col = col(df, "SOURCE_POLICY", "SOURCE_KEY", "POLICY_NUMBER", "SRCPOLICY", "OLDPOLICY", "SOURCE")
    tgt_col = col(df, "MPOLICY", "TARGET_POLICY", "NEWPOLICY", "QLA_POLICY")
    if not src_col or not tgt_col:
        findings.append(
            make_finding(
                rule_id="CW-001",
                rule_category="Crosswalk",
                severity=CRITICAL,
                source_file="Master_Crosswalk.csv",
                description="Crosswalk must have identifiable source and MPOLICY columns.",
                reason=(
                    "Master_Crosswalk.csv does not have recognizable source-policy and "
                    "MPOLICY columns; crosswalk integrity cannot be verified."
                ),
                field_name="",
                expected="SOURCE + MPOLICY columns",
                actual=str(list(df.columns)[:10]),
                affected_keys=["Master_Crosswalk.csv"],
                affected_count=1,
            )
        )
        return findings

    # CW-001 — one source -> many MPOLICY
    src_to_tgts: dict[str, set[str]] = {}
    for _, row in df.iterrows():
        src = s(row.get(src_col))
        tgt = s(row.get(tgt_col))
        if not src or not tgt:
            continue
        src_to_tgts.setdefault(src, set()).add(tgt)

    for src, tgts in src_to_tgts.items():
        if len(tgts) > 1:
            tgt_list = sorted(tgts)
            findings.append(
                make_finding(
                    rule_id="CW-001",
                    rule_category="Crosswalk",
                    severity=CRITICAL,
                    source_file="Master_Crosswalk.csv",
                    description="Each source policy must map to exactly one MPOLICY.",
                    reason=(
                        f"Source policy '{src}' maps to {len(tgts)} different MPOLICY "
                        f"values: {tgt_list}. Each source policy must map to exactly "
                        f"one output policy number."
                    ),
                    field_name="MPOLICY",
                    expected="1 MPOLICY",
                    actual=str(tgt_list),
                    affected_keys=[src] + tgt_list,
                    affected_count=len(tgts),
                )
            )

    # CW-002 — many source -> one MPOLICY
    tgt_to_srcs: dict[str, set[str]] = {}
    for _, row in df.iterrows():
        src = s(row.get(src_col))
        tgt = s(row.get(tgt_col))
        if not src or not tgt:
            continue
        tgt_to_srcs.setdefault(tgt, set()).add(src)

    for mpol, srcs in tgt_to_srcs.items():
        if len(srcs) > 1:
            src_list = sorted(srcs)
            findings.append(
                make_finding(
                    rule_id="CW-002",
                    rule_category="Crosswalk",
                    severity=CRITICAL,
                    source_file="Master_Crosswalk.csv",
                    description="Each MPOLICY must come from exactly one source policy.",
                    reason=(
                        f"MPOLICY '{mpol}' is mapped to by {len(srcs)} source policies: "
                        f"{src_list}. Each output policy number must come from exactly "
                        f"one source policy."
                    ),
                    field_name="MPOLICY",
                    expected="1 source policy",
                    actual=str(src_list),
                    affected_keys=[mpol] + src_list,
                    affected_count=len(srcs),
                )
            )

    return findings
