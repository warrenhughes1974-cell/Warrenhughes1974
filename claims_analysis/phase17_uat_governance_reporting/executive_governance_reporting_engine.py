#!/usr/bin/env python3
"""
Phase 17E — Executive/UAT governance reporting dashboards.

Business-consumable KPI and trend reports for UAT preparation.
Does NOT modify app.py or authorize production.
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

logger = logging.getLogger("executive_governance_reporting")


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


def run_engine(uat_metrics, gov_metrics, exclusion_catalog, phase16_forecast, phase16_decision, rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    audit_ts = utc_now()
    rollback_id = f"{rules['rollback_snapshot_prefix']}-EXEC-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    baseline = rules["baseline_metrics"]

    def metric_val(df, name, default=0):
        if df.empty:
            return default
        row = df[df["metric"] == name]
        if row.empty:
            return default
        return float(row.iloc[0].get("value", default))

    uat_clms = int(metric_val(uat_metrics, "uat_candidate_quikclms"))
    uat_clmp = int(metric_val(uat_metrics, "uat_candidate_quikclmp"))
    deferred_claims = int(metric_val(gov_metrics, "deferred_claims"))
    deferred_payments = int(metric_val(gov_metrics, "deferred_payments"))
    total_processed = int(baseline["phase15_quikclms_count"])

    dashboard_rows = [
        {"kpi": "total_claims_processed", "value": total_processed, "unit": "claims"},
        {"kpi": "uat_candidate_claims", "value": uat_clms, "unit": "claims"},
        {"kpi": "deferred_governance_claims", "value": deferred_claims, "unit": "claims"},
        {"kpi": "uat_candidate_payments", "value": uat_clmp, "unit": "payments"},
        {"kpi": "deferred_governance_payments", "value": deferred_payments, "unit": "payments"},
        {"kpi": "orphan_count_phase15", "value": baseline["phase15_orphan_count"], "unit": "payments"},
        {"kpi": "orphan_count_phase11", "value": baseline["phase11_orphan_count"], "unit": "payments"},
        {"kpi": "orphan_reduction", "value": baseline["phase11_orphan_count"] - baseline["phase15_orphan_count"], "unit": "payments"},
        {"kpi": "reconciliation_pass_rate_phase15_pct", "value": baseline["phase15_recon_pass_rate_pct"], "unit": "percent"},
        {"kpi": "reconciliation_improvement_pct", "value": round(baseline["phase15_recon_pass_rate_pct"] - baseline["phase11_recon_pass_rate_pct"], 2), "unit": "percent"},
        {"kpi": "go_live_target", "value": rules["go_live_target_date"], "unit": "date"},
        {"kpi": "production_dbf_flag", "value": "N", "unit": "flag"},
    ]
    for r in dashboard_rows:
        r.update({
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "production_dbf_flag": "N",
            "governance_status": "UAT_REPORTING",
            "business_review_required": "N",
        })
    dashboard_df = pd.DataFrame(dashboard_rows)

    kpi_rows = []
    if not exclusion_catalog.empty:
        for _, row in exclusion_catalog.iterrows():
            kpi_rows.append({
                "audit_timestamp": audit_ts,
                "production_dbf_flag": "N",
                "kpi_name": f"blocker_{strip_val(row.get('blocker_category', '')).lower()}",
                "kpi_value": strip_val(row.get("exception_count", "")),
                "kpi_description": strip_val(row.get("business_explanation", "")),
                "governance_status": strip_val(row.get("governance_status", "")),
                "business_review_required": "Y",
            })
    kpi_df = pd.DataFrame(kpi_rows)

    trend_rows = [
        {
            "audit_timestamp": audit_ts,
            "production_dbf_flag": "N",
            "trend_metric": "orphan_payments",
            "phase11_value": baseline["phase11_orphan_count"],
            "phase15_value": baseline["phase15_orphan_count"],
            "delta": baseline["phase11_orphan_count"] - baseline["phase15_orphan_count"],
            "trend_direction": "IMPROVING",
        },
        {
            "audit_timestamp": audit_ts,
            "production_dbf_flag": "N",
            "trend_metric": "reconciliation_pass_rate",
            "phase11_value": baseline["phase11_recon_pass_rate_pct"],
            "phase15_value": baseline["phase15_recon_pass_rate_pct"],
            "delta": round(baseline["phase15_recon_pass_rate_pct"] - baseline["phase11_recon_pass_rate_pct"], 2),
            "trend_direction": "IMPROVING",
        },
        {
            "audit_timestamp": audit_ts,
            "production_dbf_flag": "N",
            "trend_metric": "quikclms_rows",
            "phase11_value": baseline["phase11_quikclms_count"],
            "phase15_value": baseline["phase15_quikclms_count"],
            "delta": baseline["phase15_quikclms_count"] - baseline["phase11_quikclms_count"],
            "trend_direction": "IMPROVING",
        },
    ]
    if not phase16_forecast.empty and "orphans_must_resolve" in phase16_forecast.columns:
        trend_rows.append({
            "audit_timestamp": audit_ts,
            "production_dbf_flag": "N",
            "trend_metric": "orphans_to_production_threshold",
            "phase11_value": "",
            "phase15_value": strip_val(phase16_forecast.iloc[0].get("orphans_must_resolve", "")),
            "delta": "",
            "trend_direction": "PENDING_REMEDIATION",
        })
    trend_df = pd.DataFrame(trend_rows)

    decision = "PRODUCTION_BLOCKED"
    if not phase16_decision.empty:
        decision = strip_val(phase16_decision.iloc[0].get("decision_category", decision))

    outputs = []
    for name, frame in [
        ("executive_uat_dashboard.csv", dashboard_df),
        ("governance_kpi_summary.csv", kpi_df),
        ("blocker_trend_analysis.csv", trend_df),
    ]:
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        outputs.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    exec_path = os.path.join(output_dir, "phase17_executive_summary.txt")
    with open(exec_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 17E Executive UAT Governance Summary ===",
            "",
            f"Go-live target: {rules['go_live_target_date']}",
            f"Total claims processed (Phase 15 replay): {total_processed}",
            f"UAT candidate claims: {uat_clms}",
            f"Deferred governance claims: {deferred_claims}",
            f"UAT candidate payments: {uat_clmp}",
            f"Deferred governance payments: {deferred_payments}",
            "",
            "Replay recovery improvements:",
            f"  Orphans: {baseline['phase11_orphan_count']} -> {baseline['phase15_orphan_count']} "
            f"({baseline['phase11_orphan_count'] - baseline['phase15_orphan_count']} resolved)",
            f"  Reconciliation: {baseline['phase11_recon_pass_rate_pct']}% -> {baseline['phase15_recon_pass_rate_pct']}%",
            "",
            f"Phase 16 decision checkpoint: {decision}",
            "",
            "UAT preparation reporting only. production_dbf_flag=N",
            "No production DBFs. app.py NOT modified.",
        ]) + "\n")
    outputs.append(exec_path)
    return {"uat_claims": uat_clms}, outputs


def strip_val(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def main():
    parser = argparse.ArgumentParser(description="Phase 17E executive governance reporting engine.")
    parser.add_argument("--uat-metrics", default=os.path.join(DEFAULT_OUTPUT, "uat_candidate_metrics.csv"))
    parser.add_argument("--gov-metrics", default=os.path.join(DEFAULT_OUTPUT, "governance_population_metrics.csv"))
    parser.add_argument("--exclusion-catalog", default=os.path.join(DEFAULT_OUTPUT, "governance_exception_catalog.csv"))
    parser.add_argument("--phase16-forecast", default=os.path.join(PHASE16, "orphan_threshold_resolution_forecast.csv"))
    parser.add_argument("--phase16-decision", default=os.path.join(PHASE16, "phase16_decision_checkpoint.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    stats, outputs = run_engine(
        load_csv(args.uat_metrics), load_csv(args.gov_metrics),
        load_csv(args.exclusion_catalog), load_csv(args.phase16_forecast),
        load_csv(args.phase16_decision), args.rules, args.output,
    )
    print(f"Phase 17E complete. UAT claims in dashboard: {stats['uat_claims']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
