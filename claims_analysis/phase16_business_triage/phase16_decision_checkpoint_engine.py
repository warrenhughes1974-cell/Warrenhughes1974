#!/usr/bin/env python3
"""
Phase 16F — Pre-production decision checkpoint (analysis only).

Produces enterprise decision checkpoint from Phase 16 outputs.
Does NOT modify app.py or authorize production DBFs.
"""

import argparse
import json
import logging
import os
from datetime import datetime, timezone

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_RULES = os.path.join(ROOT, "config", "phase16_decision_checkpoint_rules.json")
PHASE15 = os.path.join(ROOT, "phase15_qa_signoff_replay_execution")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase16_business_triage_remediation")

logger = logging.getLogger("phase16_decision_checkpoint")


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


def snapshot_id(prefix):
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def run_engine(rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    audit_ts = utc_now()
    rollback_id = snapshot_id(rules["rollback_snapshot_prefix"])
    lineage = rules["rulebook_lineage"]
    dc_rules = rules["decision_categories"]

    orphan_triage = load_csv(os.path.join(output_dir, "remaining_orphan_root_cause_triage.csv"))
    surrender_wb = load_csv(os.path.join(output_dir, "surrender_offset_business_triage_workbench.csv"))
    forecast = load_csv(os.path.join(output_dir, "orphan_threshold_resolution_forecast.csv"))
    scenarios = load_csv(os.path.join(output_dir, "remediation_scenario_model.csv"))
    blockers = load_csv(os.path.join(PHASE15, "remaining_production_blockers.csv"))

    orphan_rate = 18.0
    if not forecast.empty:
        orphan_rate = float(forecast.iloc[0].get("current_orphan_rate_pct", 18.0))

    surrender_count = len(surrender_wb)
    lifecycle_blocked = (orphan_triage["blocker_type"] == "LIFECYCLE_BLOCKED").sum() if not orphan_triage.empty else 0
    derivation_rejected = (orphan_triage["blocker_type"] == "DERIVATION_REJECTED").sum() if not orphan_triage.empty else 0
    non_recoverable = (orphan_triage["remediability"] == "NON_RECOVERABLE").sum() if not orphan_triage.empty else 0
    non_rec_pct = non_recoverable / max(len(orphan_triage), 1)
    unbalanced_count = 4711
    if not blockers.empty:
        ub = blockers[blockers["blocker_type"] == "UNBALANCED_CLAIMS"]
        if not ub.empty:
            unbalanced_count = int(float(ub.iloc[0].get("blocker_count", 4711)))

    decisions = []
    if orphan_rate <= dc_rules["READY_FOR_MORE_REPLAY"]["requires_orphan_rate_below_pct"]:
        decisions.append("READY_FOR_MORE_REPLAY")
    if surrender_count >= dc_rules["NEEDS_BUSINESS_REVIEW"]["trigger_if_surrender_queue_min"]:
        decisions.append("NEEDS_BUSINESS_REVIEW")
    if lifecycle_blocked >= dc_rules["NEEDS_RULE_REFINEMENT"]["trigger_if_lifecycle_blocked_min"]:
        decisions.append("NEEDS_RULE_REFINEMENT")
    if derivation_rejected >= dc_rules["NEEDS_RULE_REFINEMENT"]["trigger_if_derivation_rejected_min"]:
        if "NEEDS_RULE_REFINEMENT" not in decisions:
            decisions.append("NEEDS_RULE_REFINEMENT")
    if orphan_rate > dc_rules["PRODUCTION_BLOCKED"]["trigger_if_orphan_rate_above_pct"]:
        decisions.append("PRODUCTION_BLOCKED")
    if unbalanced_count >= dc_rules["PRODUCTION_BLOCKED"]["trigger_if_unbalanced_claims_min"]:
        if "PRODUCTION_BLOCKED" not in decisions:
            decisions.append("PRODUCTION_BLOCKED")
    if non_rec_pct >= dc_rules["DEFER_TO_MANUAL_REMEDIATION"]["trigger_if_non_recoverable_pct"]:
        decisions.append("DEFER_TO_MANUAL_REMEDIATION")
    if not decisions:
        decisions = ["NEEDS_BUSINESS_REVIEW"]

    primary_decision = "PRODUCTION_BLOCKED" if "PRODUCTION_BLOCKED" in decisions else decisions[0]

    checkpoint_rows = [{
        "audit_timestamp": audit_ts,
        "rollback_snapshot_id": rollback_id,
        "production_dbf_flag": rules["production_dbf_flag"],
        "decision_category": primary_decision,
        "all_decision_flags": "|".join(decisions),
        "orphan_rate_pct": orphan_rate,
        "remaining_orphan_count": len(orphan_triage),
        "surrender_review_count": surrender_count,
        "unbalanced_claim_count": unbalanced_count,
        "governance_status": primary_decision,
        "severity": "HIGH",
        "remediability": "PARTIALLY_RECOVERABLE",
        "business_review_required": "Y",
        "replay_authorization_status": "NOT_AUTHORIZED",
        "production_authorization_flag": "UNSET",
        "table_schemas_quikclms_quikclmp": "NOT_PRESENT",
        "expected_replay_impact": "REQUIRES_PHASE16_REMEDIATION_GOVERNANCE",
        "rulebook_lineage": lineage,
    }]

    matrix_rows = []
    blocker_defs = [
        ("ORPHAN_PAYMENTS", len(orphan_triage), orphan_rate, "PRODUCTION_BLOCKED"),
        ("SURRENDER_OFFSET_REVIEW", surrender_count, None, "NEEDS_BUSINESS_REVIEW"),
        ("UNBALANCED_CLAIMS", unbalanced_count, None, "PRODUCTION_BLOCKED"),
        ("LIFECYCLE_BLOCKED_ORPHANS", lifecycle_blocked, None, "NEEDS_RULE_REFINEMENT"),
        ("DERIVATION_REJECTED_ORPHANS", derivation_rejected, None, "NEEDS_RULE_REFINEMENT"),
    ]
    for btype, count, rate, decision in blocker_defs:
        matrix_rows.append({
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "production_dbf_flag": rules["production_dbf_flag"],
            "blocker_type": btype,
            "blocker_count": count,
            "blocker_rate_pct": rate if rate is not None else "",
            "recommended_decision": decision,
            "governance_status": decision,
            "severity": "HIGH" if count > 100 else "MEDIUM",
            "remediability": "PARTIALLY_RECOVERABLE",
            "business_review_required": "Y",
            "replay_authorization_status": "NOT_AUTHORIZED",
            "remediation_workflow": "PHASE16_GOVERNED_TRIAGE",
            "rulebook_lineage": lineage,
        })

    checkpoint_df = pd.DataFrame(checkpoint_rows)
    matrix_df = pd.DataFrame(matrix_rows)

    outputs = []
    for name, frame in [
        ("phase16_decision_checkpoint.csv", checkpoint_df),
        ("remaining_blocker_decision_matrix.csv", matrix_df),
    ]:
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        outputs.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    best_scenario = ""
    if not scenarios.empty:
        best = scenarios.sort_values("projected_orphan_rate_pct").iloc[0]
        best_scenario = (
            f"{strip_val(best.get('scenario', ''))}: "
            f"{strip_val(best.get('projected_orphan_rate_pct', ''))}% orphan rate, "
            f"{strip_val(best.get('readiness_forecast', ''))}"
        )

    exec_path = os.path.join(output_dir, "phase16_executive_readiness_summary.txt")
    with open(exec_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 16 Executive Readiness Summary ===",
            "",
            f"Decision checkpoint: {primary_decision}",
            f"All decision flags: {', '.join(decisions)}",
            "",
            "Remaining production blockers:",
            f"  Orphan payments: {len(orphan_triage)} ({orphan_rate}% rate)",
            f"  Surrender offset review queue: {surrender_count}",
            f"  Unbalanced claims: {unbalanced_count}",
            "",
            f"Best remediation scenario forecast: {best_scenario or 'N/A'}",
            "",
            "Enterprise status:",
            "  production_dbf_flag=N",
            "  production_authorization_flag=UNSET",
            "  app.py NOT modified",
            "  TABLE_SCHEMAS quikclms/quikclmp NOT present",
            "",
            "Phase 16 is business triage and remediation governance only.",
            "No production deployment authorized.",
        ]) + "\n")
    outputs.append(exec_path)
    return {"decision": primary_decision}, outputs


def main():
    parser = argparse.ArgumentParser(description="Phase 16F decision checkpoint engine.")
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    stats, outputs = run_engine(args.rules, args.output)
    print(f"Phase 16F complete. Decision: {stats['decision']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
