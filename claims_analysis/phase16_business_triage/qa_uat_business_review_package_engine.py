#!/usr/bin/env python3
"""
Phase 16E — QA/UAT business review package generator.

Produces business-consumable review packages from Phase 16A-D outputs.
Analysis only. Does NOT modify app.py.
"""

import argparse
import logging
import os
from datetime import datetime, timezone

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_OUTPUT = os.path.join(ROOT, "phase16_business_triage_remediation")

logger = logging.getLogger("qa_uat_business_review")


def load_csv(path):
    if not os.path.isfile(path):
        return pd.DataFrame()
    df = pd.read_csv(path, dtype=str)
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def strip_val(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def business_summary_orphan(row):
    blocker = strip_val(row.get("blocker_type", ""))
    amount = strip_val(row.get("mamount", ""))
    return (
        f"Orphan payment ${amount} blocked because parent claim is {blocker.replace('_', ' ').lower()}. "
        f"Recommended workflow: {strip_val(row.get('remediation_workflow', ''))}."
    )


def business_summary_surrender(row):
    bucket = strip_val(row.get("workbench_bucket", ""))
    diff = strip_val(row.get("balancing_difference_abs", ""))
    return (
        f"Surrender claim with ${diff} residual classified as {bucket.replace('_', ' ').lower()}. "
        f"Requires business review before any controlled replay."
    )


def business_summary_parent(row):
    count = strip_val(row.get("orphan_payment_count", ""))
    amount = strip_val(row.get("orphan_payment_amount", ""))
    return (
        f"Parent claim drives {count} orphan payment(s) totaling ${amount}. "
        f"Remediating this parent is a high-value target for orphan reduction."
    )


def run_engine(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    audit_ts = utc_now()

    orphan_triage = load_csv(os.path.join(output_dir, "remaining_orphan_root_cause_triage.csv"))
    surrender_wb = load_csv(os.path.join(output_dir, "surrender_offset_business_triage_workbench.csv"))
    parent_candidates = load_csv(os.path.join(output_dir, "parent_claim_remediation_candidates.csv"))
    forecast = load_csv(os.path.join(output_dir, "orphan_threshold_resolution_forecast.csv"))
    scenarios = load_csv(os.path.join(output_dir, "remediation_scenario_model.csv"))

    orphan_pkg = []
    for _, row in orphan_triage.head(500).iterrows():
        orphan_pkg.append({
            "audit_timestamp": audit_ts,
            "production_dbf_flag": "N",
            "package_type": "REMAINING_ORPHAN_REVIEW",
            "parent_claim_id": strip_val(row.get("parent_claim_id", "")),
            "reconstructed_claim_id": strip_val(row.get("reconstructed_claim_id", "")),
            "derivation_candidate_id": strip_val(row.get("derivation_candidate_id", "")),
            "claim_family": strip_val(row.get("claim_family", "")),
            "blocker_type": strip_val(row.get("blocker_type", "")),
            "orphan_payment_amount": strip_val(row.get("mamount", "")),
            "governance_status": strip_val(row.get("governance_status", "")),
            "severity": strip_val(row.get("severity", "")),
            "remediability": strip_val(row.get("remediability", "")),
            "business_review_required": strip_val(row.get("business_review_required", "")),
            "remediation_workflow": strip_val(row.get("remediation_workflow", "")),
            "business_summary": business_summary_orphan(row),
            "rulebook_lineage": "phase16e_qa_uat_orphan_package",
        })

    surrender_pkg = []
    for _, row in surrender_wb.head(500).iterrows():
        surrender_pkg.append({
            "audit_timestamp": audit_ts,
            "production_dbf_flag": "N",
            "package_type": "SURRENDER_OFFSET_REVIEW",
            "parent_claim_id": strip_val(row.get("parent_claim_id", "")),
            "reconstructed_claim_id": strip_val(row.get("reconstructed_claim_id", "")),
            "workbench_bucket": strip_val(row.get("workbench_bucket", "")),
            "balancing_difference_abs": strip_val(row.get("balancing_difference_abs", "")),
            "governance_status": strip_val(row.get("governance_status", "")),
            "severity": strip_val(row.get("severity", "")),
            "remediability": strip_val(row.get("remediability", "")),
            "business_review_required": "Y",
            "future_controlled_replay_eligible": strip_val(row.get("future_controlled_replay_eligible", "")),
            "business_summary": business_summary_surrender(row),
            "rulebook_lineage": "phase16e_qa_uat_surrender_package",
        })

    parent_pkg = []
    for _, row in parent_candidates.head(200).iterrows():
        parent_pkg.append({
            "audit_timestamp": audit_ts,
            "production_dbf_flag": "N",
            "package_type": "PARENT_REMEDIATION_REVIEW",
            "parent_claim_id": strip_val(row.get("parent_claim_id", "")),
            "reconstructed_claim_id": strip_val(row.get("reconstructed_claim_id", "")),
            "orphan_payment_count": strip_val(row.get("orphan_payment_count", "")),
            "orphan_payment_amount": strip_val(row.get("orphan_payment_amount", "")),
            "blocker_type": strip_val(row.get("blocker_type", "")),
            "remediation_priority_score": strip_val(row.get("remediation_priority_score", "")),
            "expected_replay_impact": strip_val(row.get("expected_replay_impact", "")),
            "governance_status": strip_val(row.get("governance_status", "")),
            "severity": strip_val(row.get("severity", "")),
            "remediability": strip_val(row.get("remediability", "")),
            "business_review_required": strip_val(row.get("business_review_required", "")),
            "business_summary": business_summary_parent(row),
            "rulebook_lineage": "phase16e_qa_uat_parent_package",
        })

    orphan_df = pd.DataFrame(orphan_pkg)
    surrender_df = pd.DataFrame(surrender_pkg)
    parent_df = pd.DataFrame(parent_pkg)

    outputs = []
    for name, frame in [
        ("qa_uat_remaining_orphan_review_package.csv", orphan_df),
        ("qa_uat_surrender_offset_review_package.csv", surrender_df),
        ("qa_uat_parent_remediation_review_package.csv", parent_df),
    ]:
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        outputs.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    orphans_to_resolve = ""
    if not forecast.empty:
        orphans_to_resolve = strip_val(forecast.iloc[0].get("orphans_must_resolve", ""))
    best_scenario = ""
    if not scenarios.empty:
        best = scenarios.sort_values("projected_orphan_rate_pct").iloc[0]
        best_scenario = f"{strip_val(best.get('scenario', ''))} -> {strip_val(best.get('projected_orphan_rate_pct', ''))}% orphan rate"

    summary_path = os.path.join(output_dir, "qa_uat_phase16_business_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 16E QA/UAT Business Review Package Summary ===",
            "",
            f"Generated: {audit_ts}",
            "",
            "Business review packages:",
            f"  Remaining orphan review rows: {len(orphan_df)} (top priority sample)",
            f"  Surrender offset review rows: {len(surrender_df)} (top priority sample)",
            f"  Parent remediation review rows: {len(parent_df)} (top priority sample)",
            "",
            "Production readiness context:",
            f"  Orphans to resolve for 5% threshold: {orphans_to_resolve}",
            f"  Best forecast scenario: {best_scenario or 'N/A'}",
            "",
            "These packages are for QA/UAT and stakeholder sign-off.",
            "No auto-remediation. production_dbf_flag=N",
        ]) + "\n")
    outputs.append(summary_path)
    return {"packages": len(orphan_df) + len(surrender_df) + len(parent_df)}, outputs


def main():
    parser = argparse.ArgumentParser(description="Phase 16E QA/UAT business review package engine.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    stats, outputs = run_engine(args.output)
    print(f"Phase 16E complete. Package rows: {stats['packages']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
