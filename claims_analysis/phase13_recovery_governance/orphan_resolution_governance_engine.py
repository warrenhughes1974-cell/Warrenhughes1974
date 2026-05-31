#!/usr/bin/env python3
"""
Phase 13C — Orphan resolution governance engine (analysis only).

Defines orphan quarantine and parent-claim remediation workflows.
Does NOT suppress orphans or modify stable engines / app.py.
"""

import argparse
import json
import logging
import os
import shutil
from datetime import datetime, timezone

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_RULES = os.path.join(ROOT, "config", "orphan_resolution_governance_rules.json")
PHASE12 = os.path.join(ROOT, "phase12_qa_uat_hardening")
PHASE13 = os.path.join(ROOT, "phase13_controlled_enterprise_integration")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase13_controlled_enterprise_integration")

logger = logging.getLogger("orphan_governance")


def load_csv(path):
    df = pd.read_csv(path, dtype=str)
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def strip_val(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def parse_amount(value):
    raw = strip_val(value).replace(",", "").replace("$", "")
    if not raw:
        return 0.0
    try:
        return float(raw)
    except ValueError:
        return 0.0


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def assign_workflow(row, rules, balancing_lookup):
    workflows = rules["resolution_workflows"]
    cid = strip_val(row.get("reconstructed_claim_id", ""))
    parent = balancing_lookup.get(cid, {})
    parent_remed = strip_val(row.get("remediability", parent.get("remediability", "PARTIALLY_RECOVERABLE")))

    if parent_remed in workflows["PARENT_CLAIM_REMEDIATION"]["parent_remediability"]:
        meta = workflows["PARENT_CLAIM_REMEDIATION"]
        workflow = "PARENT_CLAIM_REMEDIATION"
    elif parent_remed == "NON_RECOVERABLE":
        meta = workflows["ORPHAN_QUARANTINE"]
        workflow = "ORPHAN_QUARANTINE"
    else:
        meta = workflows["PRODUCTION_EXCLUDE_POLICY"]
        workflow = "PRODUCTION_EXCLUDE_POLICY"

    return {
        "resolution_workflow": workflow,
        "governance_status": meta["governance_status"],
        "severity": meta["severity"],
        "recommended_action": meta["recommended_action"],
        "orphan_recoverability": "Y" if workflow == "PARENT_CLAIM_REMEDIATION" else "N",
    }


def run_engine(orphan_gov, rejected_claims, balancing_patterns, rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    audit_ts = utc_now()

    balancing_lookup = {}
    if not balancing_patterns.empty and "reconstructed_claim_id" in balancing_patterns.columns:
        balancing_lookup = balancing_patterns.set_index("reconstructed_claim_id").to_dict("index")

    rejected_lookup = {}
    if not rejected_claims.empty:
        rejected_lookup = rejected_claims.set_index("reconstructed_claim_id").to_dict("index")

    workflow_rows = []
    quarantine_rows = []

    for _, row in orphan_gov.iterrows():
        cid = strip_val(row.get("reconstructed_claim_id", ""))
        parent = rejected_lookup.get(cid, {})
        bal = balancing_lookup.get(cid, {})
        merged = {**row.to_dict(), **parent, **bal}
        wf = assign_workflow(merged, rules, balancing_lookup)
        record = {
            "audit_timestamp": audit_ts,
            "reconstructed_claim_id": cid,
            "canonical_payment_stage_id": strip_val(row.get("canonical_payment_stage_id", "")),
            "derivation_candidate_id": strip_val(row.get("derivation_candidate_id", "")),
            "mpolicy": strip_val(row.get("mpolicy", "")),
            "mseq": strip_val(row.get("mseq", "")),
            "mamount": parse_amount(row.get("mamount", 0)),
            "orphan_issue": strip_val(row.get("orphan_issue", "")),
            "parent_claim_root_cause": strip_val(row.get("parent_claim_root_cause", "")),
            "parent_failure_pattern": strip_val(bal.get("failure_pattern", "")),
            "parent_replay_eligible": strip_val(bal.get("replay_simulation_eligible", "N")),
            "production_dbf_flag": "N",
            **wf,
        }
        workflow_rows.append(record)
        if wf["resolution_workflow"] in {"ORPHAN_QUARANTINE", "PRODUCTION_EXCLUDE_POLICY"}:
            quarantine_rows.append({
                **record,
                "quarantine_status": "QUARANTINED",
                "quarantine_rationale": wf["recommended_action"],
                "lineage_source": "phase12_orphan_governance|phase13c_orphan_resolution",
            })

    workflow_df = pd.DataFrame(workflow_rows)
    quarantine_df = pd.DataFrame(quarantine_rows)

    recoverable = len(workflow_df[workflow_df["orphan_recoverability"] == "Y"]) if not workflow_df.empty else 0
    total = len(workflow_df)
    stats = {
        "total_orphans": total,
        "recoverable": recoverable,
        "recoverable_pct": round(100.0 * recoverable / max(total, 1), 2),
        "quarantine_count": len(quarantine_df),
    }

    rules_out = os.path.join(output_dir, "orphan_resolution_governance_rules.json")
    shutil.copy2(rules_path, rules_out)
    outputs = [rules_out]

    for name, frame in [
        ("orphan_resolution_workflow_analysis.csv", workflow_df),
        ("orphan_quarantine_candidates.csv", quarantine_df),
    ]:
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        outputs.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_path = os.path.join(output_dir, "orphan_recovery_governance_summary.txt")
    write_summary(summary_path, stats, outputs, workflow_df)
    outputs.append(summary_path)
    return stats, outputs


def write_summary(path, stats, outputs, workflow_df):
    lines = [
        "=== Phase 13C Orphan Resolution Governance Summary ===",
        "",
        f"Orphan payments analyzed: {stats['total_orphans']}",
        f"Recoverable via parent remediation: {stats['recoverable']} ({stats['recoverable_pct']}%)",
        f"Quarantine candidates: {stats['quarantine_count']}",
        "",
        "Workflow distribution:",
    ]
    if not workflow_df.empty:
        for wf, cnt in workflow_df["resolution_workflow"].value_counts().items():
            lines.append(f"  {wf}: {cnt}")
    lines.extend([
        "",
        "Enterprise notes:",
        "  - Orphans not suppressed",
        "  - production_dbf_flag=N on all outputs",
        "",
        "Output files:",
    ])
    for f in outputs:
        lines.append(f"  - {f}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Phase 13C orphan resolution governance engine.")
    parser.add_argument("--orphan-governance", default=os.path.join(PHASE12, "orphan_payment_governance_analysis.csv"))
    parser.add_argument("--rejected-claims", default=os.path.join(PHASE12, "rejected_claim_root_cause_analysis.csv"))
    parser.add_argument("--balancing-patterns", default=os.path.join(PHASE13, "balancing_failure_pattern_analysis.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    if not os.path.isfile(args.orphan_governance):
        logger.error("Orphan governance not found: %s", args.orphan_governance)
        return 1

    balancing = load_csv(args.balancing_patterns) if os.path.isfile(args.balancing_patterns) else pd.DataFrame()
    stats, outputs = run_engine(
        load_csv(args.orphan_governance),
        load_csv(args.rejected_claims) if os.path.isfile(args.rejected_claims) else pd.DataFrame(),
        balancing,
        args.rules, args.output,
    )
    print(f"Orphan governance complete. Orphans: {stats['total_orphans']}")
    print(f"Recoverable: {stats['recoverable_pct']}%")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
