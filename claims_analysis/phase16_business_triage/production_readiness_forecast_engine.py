#!/usr/bin/env python3
"""
Phase 16D — Production readiness threshold forecasting (analysis only).

Forecasts remediation volume needed for production-readiness thresholds.
Does NOT modify app.py or generate production DBFs.
"""

import argparse
import json
import logging
import os
from datetime import datetime, timezone

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_RULES = os.path.join(ROOT, "config", "production_readiness_forecast_rules.json")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase16_business_triage_remediation")

logger = logging.getLogger("production_readiness_forecast")


def load_csv(path):
    if not os.path.isfile(path):
        return pd.DataFrame()
    df = pd.read_csv(path, dtype=str)
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def snapshot_id(prefix):
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def run_engine(parent_impact, orphan_triage, surrender_workbench, rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    audit_ts = utc_now()
    rollback_id = snapshot_id(rules["rollback_snapshot_prefix"])
    lineage = rules["rulebook_lineage"]
    baseline = rules["baseline_metrics"]
    thresholds = rules["thresholds"]

    total_payments = int(baseline["phase15_quikclmp_row_count"])
    current_orphans = int(baseline["phase15_orphan_count"])
    max_orphans_at_threshold = int(total_payments * thresholds["orphan_payment_rate_max_pct"] / 100.0)
    orphans_to_resolve = max(current_orphans - max_orphans_at_threshold, 0)

    parent_count = len(parent_impact) if not parent_impact.empty else 0
    avg_orphans_per_parent = (
        parent_impact["orphan_payment_count"].astype(float).mean() if not parent_impact.empty else 1.0
    )
    parents_needed = int(round(orphans_to_resolve / max(avg_orphans_per_parent, 1.0)))

    threshold_rows = [
        {
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "production_dbf_flag": rules["production_dbf_flag"],
            "metric": "ORPHAN_PAYMENT_RATE",
            "current_value": baseline["phase15_orphan_rate_pct"],
            "threshold_value": thresholds["orphan_payment_rate_max_pct"],
            "gap_to_threshold": round(baseline["phase15_orphan_rate_pct"] - thresholds["orphan_payment_rate_max_pct"], 2),
            "governance_status": "PRODUCTION_BLOCKED",
            "severity": "HIGH",
            "remediability": "PARTIALLY_RECOVERABLE",
            "business_review_required": "Y",
            "rulebook_lineage": lineage,
        },
        {
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "production_dbf_flag": rules["production_dbf_flag"],
            "metric": "RECONCILIATION_PASS_RATE",
            "current_value": baseline["phase15_reconciliation_pass_rate_pct"],
            "threshold_value": thresholds["reconciliation_pass_rate_min_pct"],
            "gap_to_threshold": round(baseline["phase15_reconciliation_pass_rate_pct"] - thresholds["reconciliation_pass_rate_min_pct"], 2),
            "governance_status": "READY",
            "severity": "LOW",
            "remediability": "RECOVERABLE",
            "business_review_required": "N",
            "rulebook_lineage": lineage,
        },
        {
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "production_dbf_flag": rules["production_dbf_flag"],
            "metric": "SURRENDER_REVIEW_QUEUE",
            "current_value": baseline["phase15_surrender_review_count"],
            "threshold_value": thresholds["surrender_review_queue_max"],
            "gap_to_threshold": baseline["phase15_surrender_review_count"],
            "governance_status": "BUSINESS_REVIEW_REQUIRED",
            "severity": "HIGH",
            "remediability": "PARTIALLY_RECOVERABLE",
            "business_review_required": "Y",
            "rulebook_lineage": lineage,
        },
    ]
    threshold_df = pd.DataFrame(threshold_rows)

    orphan_forecast_df = pd.DataFrame([{
        "audit_timestamp": audit_ts,
        "rollback_snapshot_id": rollback_id,
        "production_dbf_flag": rules["production_dbf_flag"],
        "total_quikclmp_payments": total_payments,
        "current_orphan_count": current_orphans,
        "current_orphan_rate_pct": baseline["phase15_orphan_rate_pct"],
        "target_orphan_rate_pct": thresholds["orphan_payment_rate_max_pct"],
        "max_orphans_at_threshold": max_orphans_at_threshold,
        "orphans_must_resolve": orphans_to_resolve,
        "parent_claims_estimated_for_resolution": parents_needed,
        "governance_status": "PRODUCTION_BLOCKED",
        "severity": "HIGH",
        "remediability": "PARTIALLY_RECOVERABLE",
        "business_review_required": "Y",
        "expected_replay_impact": f"ORPHAN_RATE_TARGET_IF_{orphans_to_resolve}_RESOLVED",
        "rulebook_lineage": lineage,
    }])

    scenario_rows = []
    blocker_filter_map = {}
    if not orphan_triage.empty:
        for bt in orphan_triage["blocker_type"].unique():
            blocker_filter_map[str(bt)] = orphan_triage[orphan_triage["blocker_type"] == bt]

    for scenario_name, params in rules["remediation_scenarios"].items():
        fraction = float(params["parent_remediation_fraction"])
        resolve_rate = float(params["orphans_resolved_per_parent"])
        lift = float(params["reconciliation_lift_per_100_orphans"])

        eligible_parents = parent_impact
        filter_types = params.get("filter_blocker_types", [])
        if filter_types and not parent_impact.empty:
            eligible_parents = parent_impact[parent_impact["blocker_type"].isin(filter_types)]

        remediated_parents = int(round(len(eligible_parents) * fraction))
        if not eligible_parents.empty and remediated_parents > 0:
            top = eligible_parents.sort_values("remediation_priority_score", ascending=False).head(remediated_parents)
            projected_orphans = int(round(top["orphan_payment_count"].astype(float).sum() * resolve_rate))
        else:
            projected_orphans = 0

        remaining_orphans = max(current_orphans - projected_orphans, 0)
        projected_orphan_rate = round(100.0 * remaining_orphans / max(total_payments, 1), 2)
        recon_lift = round(projected_orphans / 100.0 * lift, 2)
        projected_recon = min(
            baseline["phase15_reconciliation_pass_rate_pct"] + recon_lift,
            100.0,
        )
        surrender_remaining = max(
            int(baseline["phase15_surrender_review_count"]) - int(remediated_parents * 0.1),
            0,
        )
        readiness = "NOT_READY"
        if projected_orphan_rate <= thresholds["orphan_payment_rate_max_pct"] and surrender_remaining == 0:
            readiness = "READY"
        elif projected_orphan_rate <= thresholds["orphan_payment_rate_max_pct"]:
            readiness = "NEAR_READY"

        scenario_rows.append({
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "production_dbf_flag": rules["production_dbf_flag"],
            "scenario": scenario_name,
            "parent_claims_remediated": remediated_parents,
            "projected_orphans_resolved": projected_orphans,
            "projected_remaining_orphans": remaining_orphans,
            "projected_orphan_rate_pct": projected_orphan_rate,
            "projected_reconciliation_pass_rate_pct": projected_recon,
            "projected_surrender_review_remaining": surrender_remaining,
            "readiness_forecast": readiness,
            "governance_status": "FORECAST_ANALYZED",
            "severity": "MEDIUM",
            "remediability": "PARTIALLY_RECOVERABLE",
            "business_review_required": "Y" if surrender_remaining > 0 else "N",
            "replay_authorization_status": "NOT_AUTHORIZED",
            "expected_replay_impact": f"ORPHAN_DELTA=-{projected_orphans}",
            "rulebook_lineage": lineage,
        })

    scenario_df = pd.DataFrame(scenario_rows)
    production_forecast_df = threshold_df.copy()

    outputs = []
    for name, frame in [
        ("production_threshold_forecast.csv", production_forecast_df),
        ("orphan_threshold_resolution_forecast.csv", orphan_forecast_df),
        ("remediation_scenario_model.csv", scenario_df),
    ]:
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        outputs.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_path = os.path.join(output_dir, "phase16_readiness_forecast_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 16D Production Readiness Threshold Forecast ===",
            "",
            f"Rollback snapshot: {rollback_id}",
            f"Current orphan count: {current_orphans} ({baseline['phase15_orphan_rate_pct']}%)",
            f"Orphans to resolve for <=5% rate: {orphans_to_resolve}",
            f"Estimated parent claims needed: {parents_needed}",
            f"Scenarios modeled: {len(scenario_df)}",
            "",
            "Forecast only. No auto-remediation.",
            "production_dbf_flag=N",
        ]) + "\n")
    outputs.append(summary_path)
    return {"orphans_to_resolve": orphans_to_resolve, "scenarios": len(scenario_df)}, outputs


def main():
    parser = argparse.ArgumentParser(description="Phase 16D production readiness forecast engine.")
    parser.add_argument("--parent-impact", default=os.path.join(DEFAULT_OUTPUT, "parent_claim_remediation_impact_analysis.csv"))
    parser.add_argument("--orphan-triage", default=os.path.join(DEFAULT_OUTPUT, "remaining_orphan_root_cause_triage.csv"))
    parser.add_argument("--surrender-workbench", default=os.path.join(DEFAULT_OUTPUT, "surrender_offset_business_triage_workbench.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    stats, outputs = run_engine(
        load_csv(args.parent_impact),
        load_csv(args.orphan_triage),
        load_csv(args.surrender_workbench),
        args.rules,
        args.output,
    )
    print(f"Phase 16D complete. Orphans to resolve: {stats['orphans_to_resolve']}, scenarios: {stats['scenarios']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
