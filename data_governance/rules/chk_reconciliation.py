"""Category 17 — Count reconciliation checks (Info only)."""

from __future__ import annotations

import os

import pandas as pd

from data_governance.governance_config import INFO, AuditFinding, make_finding
from data_governance.rules._helpers import col, get_df, policy_set, s


def check_reconciliation(data: dict) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    ctx = data.get("_context") or {}

    mstr = get_df(data, "quikmstr", "quikmstr.csv")
    out_pols = policy_set(mstr) if mstr is not None else set()
    out_count = len(out_pols)

    # Resolve source policy set
    source_pols: set[str] | None = None
    if ctx.get("source_policy_count") is not None and ctx.get("source_policies"):
        source_pols = {s(x) for x in ctx["source_policies"] if s(x)}

    cw = get_df(data, "Master_Crosswalk", "master_crosswalk", "Master_Crosswalk.csv")
    if source_pols is None and cw is not None:
        src_col = col(cw, "SOURCE_POLICY", "SOURCE_KEY", "POLICY_NUMBER", "SRCPOLICY", "SOURCE")
        if src_col:
            source_pols = {s(v) for v in cw[src_col] if s(v)}

    source_df = get_df(data, "source_policies", "quikmstr_source")
    if source_pols is None and source_df is not None:
        pc = col(source_df, "POLICY_NUMBER", "MPOLICY", "POLICY")
        source_pols = {s(v) for v in source_df[pc] if s(v)} if pc else set()

    if source_pols is None:
        source_dir = ctx.get("source_dir") or ""
        src_path = os.path.join(source_dir, "quikmstr.csv") if source_dir else ""
        if src_path and os.path.isfile(src_path):
            try:
                sdf = pd.read_csv(src_path, dtype=str, low_memory=False)
                pc = col(sdf, "POLICY_NUMBER", "MPOLICY", "POLICY")
                source_pols = {s(v) for v in sdf[pc] if s(v)} if pc else set(range(len(sdf)))  # type: ignore
                if pc is None:
                    source_pols = {str(i) for i in range(len(sdf))}
            except Exception:
                source_pols = None

    src_cnt = ctx.get("source_policy_count")
    if src_cnt is None and source_pols is not None:
        src_cnt = len(source_pols)

    # RCN-001 — always Info
    if src_cnt is not None and mstr is not None:
        diff = int(src_cnt) - out_count
        findings.append(
            make_finding(
                rule_id="RCN-001",
                rule_category="Reconciliation",
                severity=INFO,
                source_file="quikmstr.csv",
                description="Source policy count vs quikmstr output count (review only).",
                reason=(
                    f"Source contained {src_cnt} policies. quikmstr "
                    f"output contains {out_count} records. Difference: {diff}. "
                    f"Review any variance to confirm expected exclusions."
                ),
                field_name="MPOLICY",
                expected=str(src_cnt),
                actual=str(out_count),
                affected_keys=["RCN-001"],
                sample_records=[{"src_cnt": src_cnt, "out_cnt": out_count, "diff": diff}],
                affected_count=abs(diff),
            )
        )

    # RCN-002 — row counts for major output files
    counts = {}
    for name in ("quikridr", "quikprmh", "quikclms", "quikclnt", "quikclid"):
        d = get_df(data, name, f"{name}.csv")
        if d is not None:
            counts[name] = len(d)
    if counts:
        findings.append(
            make_finding(
                rule_id="RCN-002",
                rule_category="Reconciliation",
                severity=INFO,
                source_file="(all)",
                description="Conversion summary — row counts for major output files.",
                reason=f"Output row counts: {counts}",
                field_name="",
                expected="",
                actual=str(counts),
                affected_keys=list(counts.keys()),
                sample_records=[counts],
                affected_count=0,
            )
        )

    # RCN-003 — dropped policies (source present, no quikmstr output)
    dropped: list[str] = []
    if cw is not None and mstr is not None:
        src_col = col(cw, "SOURCE_POLICY", "SOURCE_KEY", "POLICY_NUMBER", "SRCPOLICY", "SOURCE")
        tgt_col = col(cw, "MPOLICY", "TARGET_POLICY", "NEWPOLICY", "QLA_POLICY")
        if src_col and tgt_col:
            for _, row in cw.iterrows():
                src = s(row.get(src_col))
                tgt = s(row.get(tgt_col))
                if src and tgt and tgt not in out_pols:
                    dropped.append(src)
            dropped = sorted(set(dropped))
    elif source_pols is not None and mstr is not None:
        # Treat source_pols as expected output policy numbers when no crosswalk mapping
        dropped = sorted(source_pols - out_pols)

    if mstr is not None and (cw is not None or source_pols is not None):
        findings.append(
            make_finding(
                rule_id="RCN-003",
                rule_category="Reconciliation",
                severity=INFO,
                source_file="quikmstr.csv",
                description="Source policies with no quikmstr output (dropped).",
                reason=(
                    f"'{len(dropped)}' source policies have no corresponding "
                    f"quikmstr record. List available in sample_records."
                ),
                field_name="MPOLICY",
                expected="0 dropped",
                actual=str(len(dropped)),
                affected_keys=dropped[:500],
                sample_records=[{"policy": p} for p in dropped[:10]],
                affected_count=len(dropped),
            )
        )

    return findings
