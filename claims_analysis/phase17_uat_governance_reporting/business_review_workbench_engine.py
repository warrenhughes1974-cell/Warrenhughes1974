#!/usr/bin/env python3
"""
Phase 17F — Business review workbench preparation.

Prioritized review queues for surrender, orphan, and high-impact decisions.
Does NOT auto-approve or modify app.py.
"""

import argparse
import json
import logging
import os
from datetime import datetime, timezone

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_RULES = os.path.join(ROOT, "config", "phase17_governance_reporting_rules.json")
PHASE16 = os.path.join(ROOT, "phase16_business_triage_remediation")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase17_uat_governance_reporting")

logger = logging.getLogger("business_review_workbench")


def load_csv(path):
    if not os.path.isfile(path):
        return pd.DataFrame()
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


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def enrich_workbench(df, queue_type, audit_ts, rollback_id, rules):
    rows = []
    for rank, (_, row) in enumerate(df.iterrows(), start=1):
        rows.append({
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "production_dbf_flag": rules["production_dbf_flag"],
            "workbench_queue": queue_type,
            "review_queue_rank": rank,
            "reconstructed_claim_id": strip_val(row.get("reconstructed_claim_id", "")),
            "derivation_candidate_id": strip_val(row.get("derivation_candidate_id", "")),
            "claim_family": strip_val(row.get("claim_family", "")),
            "blocker_category": strip_val(row.get("blocker_category", row.get("blocker_type", row.get("workbench_bucket", "")))),
            "governance_status": strip_val(row.get("governance_status", "")),
            "severity": strip_val(row.get("severity", "")),
            "remediability": strip_val(row.get("remediability", "")),
            "business_review_required": "Y",
            "replay_authorization_status": strip_val(row.get("replay_authorization_status", "NOT_AUTHORIZED")),
            "replay_eligibility": strip_val(row.get("replay_eligibility", row.get("future_controlled_replay_eligible", ""))),
            "remediation_recommendation": strip_val(row.get("remediation_workflow", row.get("remediation_recommendation", "BUSINESS_REVIEW"))),
            "business_explanation": strip_val(row.get("business_explanation", "Pending business decision")),
            "orphan_impact": strip_val(row.get("orphan_impact", "")),
            "reconciliation_impact": strip_val(row.get("reconciliation_impact", "")),
            "priority_score": strip_val(row.get("priority_score", row.get("remediation_priority_score", row.get("review_priority", "")))),
            "rulebook_lineage": rules["rulebook_lineage"],
        })
    return pd.DataFrame(rows)


def run_engine(surrender_wb, orphan_queue, high_value, deferred_claims, rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    audit_ts = utc_now()
    rollback_id = f"{rules['rollback_snapshot_prefix']}-WORKBENCH-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    limits = rules["workbench_queue_limits"]

    surrender_sorted = surrender_wb.sort_values(
        ["review_priority", "balancing_difference_abs"], ascending=[True, False],
    ).head(limits["surrender_review"]) if not surrender_wb.empty else pd.DataFrame()

    orphan_sorted = orphan_queue.sort_values("priority_score", ascending=False).head(limits["orphan_review"]) if not orphan_queue.empty else pd.DataFrame()

    high_sorted = high_value.sort_values("remediation_priority_score", ascending=False).head(limits["high_priority_decisions"]) if not high_value.empty else pd.DataFrame()

    surrender_df = enrich_workbench(surrender_sorted, "SURRENDER_OFFSET_REVIEW", audit_ts, rollback_id, rules)
    orphan_df = enrich_workbench(orphan_sorted, "ORPHAN_REVIEW", audit_ts, rollback_id, rules)
    high_df = enrich_workbench(high_sorted, "HIGH_IMPACT_REMEDIATION", audit_ts, rollback_id, rules)

    decision_rows = []
    for source, label in ((surrender_df, "SURRENDER"), (orphan_df, "ORPHAN"), (high_df, "HIGH_IMPACT")):
        for _, row in source.head(20).iterrows():
            decision_rows.append({
                **row.to_dict(),
                "decision_type": label,
                "pending_business_decision": f"Review {label.lower()} item for UAT/deferred disposition",
                "decision_deadline_context": f"Go-live target: {rules['go_live_target_date']}",
            })
    decisions_df = pd.DataFrame(decision_rows)

    hold_df = enrich_workbench(
        deferred_claims.head(100) if not deferred_claims.empty else pd.DataFrame(),
        "GOVERNANCE_HOLD", audit_ts, rollback_id, rules,
    )

    outputs = []
    for name, frame in [
        ("surrender_review_workbench.csv", surrender_df),
        ("orphan_review_workbench.csv", orphan_df),
        ("high_priority_business_decisions.csv", decisions_df),
    ]:
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        outputs.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    if not hold_df.empty:
        hold_path = os.path.join(output_dir, "_governance_hold_workbench.csv")
        hold_df.to_csv(hold_path, index=False, encoding="utf-8")

    summary_path = os.path.join(output_dir, "business_review_workbench_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 17F Business Review Workbench Summary ===",
            "",
            f"Surrender review queue: {len(surrender_df)}",
            f"Orphan review queue: {len(orphan_df)}",
            f"High-priority business decisions: {len(decisions_df)}",
            f"Governance-hold workbench (internal): {len(hold_df)}",
            "",
            f"Go-live target: {rules['go_live_target_date']}",
            "Review queues for business/UAT stakeholders only.",
            "production_dbf_flag=N",
        ]) + "\n")
    outputs.append(summary_path)
    return {
        "surrender": len(surrender_df),
        "orphan": len(orphan_df),
        "decisions": len(decisions_df),
    }, outputs


def main():
    parser = argparse.ArgumentParser(description="Phase 17F business review workbench engine.")
    parser.add_argument("--surrender-workbench", default=os.path.join(PHASE16, "surrender_offset_business_triage_workbench.csv"))
    parser.add_argument("--orphan-queue", default=os.path.join(PHASE16, "orphan_remediation_priority_queue.csv"))
    parser.add_argument("--high-value", default=os.path.join(PHASE16, "high_value_remediation_queue.csv"))
    parser.add_argument("--deferred-claims", default=os.path.join(DEFAULT_OUTPUT, "deferred_governance_claims.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    stats, outputs = run_engine(
        load_csv(args.surrender_workbench), load_csv(args.orphan_queue),
        load_csv(args.high_value), load_csv(args.deferred_claims),
        args.rules, args.output,
    )
    print(f"Phase 17F complete. Workbench queues: surrender={stats['surrender']}, orphan={stats['orphan']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
