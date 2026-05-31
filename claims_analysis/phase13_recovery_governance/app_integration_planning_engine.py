#!/usr/bin/env python3
"""
Phase 13D — Controlled app.py integration planning engine (planning only).

Produces rollback-safe integration plan without modifying app.py.
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
DEFAULT_RULES = os.path.join(ROOT, "config", "app_integration_planning_rules.json")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase13_controlled_enterprise_integration")

logger = logging.getLogger("app_integration_planning")


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_engine(rules_path, output_dir, readiness_path=None):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    audit_ts = utc_now()

    checkpoint_rows = []
    for idx, cp in enumerate(rules["governance_checkpoints"], start=1):
        checkpoint_rows.append({
            "sequence": idx,
            "checkpoint": cp,
            "required_before_production": "Y",
            "rollback_safe": "Y",
            "audit_timestamp": audit_ts,
            "production_dbf_flag": "N",
        })

    rollback_rows = []
    for item in rules["rollback_controls"]:
        rollback_rows.append({
            "rollback_control": item,
            "implementation": "snapshot_before_integration",
            "audit_timestamp": audit_ts,
            "production_dbf_flag": "N",
        })

    insertion = rules["insertion_strategy"]
    planning_rows = [
        {
            "planning_area": "INSERTION_PATTERN",
            "detail": insertion["pattern"],
            "avoid": "|".join(insertion["avoid"]),
            "preferred": "|".join(insertion["preferred"]),
            "modify_app_py": rules["app_py_observations"]["modify_app_py"],
            "production_dbf_flag": "N",
        },
        {
            "planning_area": "TABLE_SCHEMA_GAP",
            "detail": rules["app_py_observations"]["current_state"],
            "avoid": "inline_schema_hack",
            "preferred": "add_quikclms_quikclmp_to_TABLE_SCHEMAS_with_isolated_pipeline",
            "modify_app_py": False,
            "production_dbf_flag": "N",
        },
        {
            "planning_area": "PIPELINE_SEQUENCE",
            "detail": "phase4->phase6->phase8->phase9->phase10->phase11->phase12->phase13->authorized_dbf",
            "avoid": "skip_governance_phases",
            "preferred": "deterministic_replay_runner",
            "modify_app_py": False,
            "production_dbf_flag": "N",
        },
    ]

    overall_readiness = "NOT_READY"
    if readiness_path and os.path.isfile(readiness_path):
        rdf = pd.read_csv(readiness_path)
        overall = rdf[rdf["readiness_dimension"] == "OVERALL_PRODUCTION_READINESS"]
        if not overall.empty:
            overall_readiness = str(overall.iloc[0]["assessment"])

    planning_rows.append({
        "planning_area": "PRODUCTION_READINESS_GATE",
        "detail": f"Current overall readiness: {overall_readiness}",
        "avoid": "production_dbf_without_signoff",
        "preferred": "explicit_production_dbf_authorization_flag",
        "modify_app_py": False,
        "production_dbf_flag": "N",
    })

    checkpoint_df = pd.DataFrame(checkpoint_rows)
    rollback_df = pd.DataFrame(rollback_rows)
    planning_df = pd.DataFrame(planning_rows)

    rules_out = os.path.join(output_dir, "app_integration_planning_rules.json")
    shutil.copy2(rules_path, rules_out)

    plan_csv = os.path.join(output_dir, "app_integration_planning_analysis.csv")
    pd.concat([planning_df, checkpoint_df.rename(columns={"checkpoint": "detail"})], ignore_index=True).to_csv(
        plan_csv, index=False, encoding="utf-8",
    )

    summary_path = os.path.join(output_dir, "app_integration_planning_summary.txt")
    lines = [
        "=== Phase 13D Controlled app.py Integration Planning Summary ===",
        "",
        f"Planning timestamp: {audit_ts}",
        f"Current production readiness: {overall_readiness}",
        f"Modify app.py in this phase: NO",
        "",
        "Governance checkpoints:",
    ]
    for row in checkpoint_rows:
        lines.append(f"  {row['sequence']}. {row['checkpoint']}")
    lines.extend(["", "Rollback controls:"])
    for row in rollback_rows:
        lines.append(f"  - {row['rollback_control']}")
    lines.extend([
        "",
        "Insertion strategy:",
        f"  Pattern: {insertion['pattern']}",
        f"  Preferred: {', '.join(insertion['preferred'])}",
        f"  Avoid: {', '.join(insertion['avoid'])}",
        "",
        "app.py observation:",
        f"  {rules['app_py_observations']['current_state']}",
        "",
        "Output files:",
        f"  - {rules_out}",
        f"  - {plan_csv}",
        f"  - {summary_path}",
    ])
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    logger.info("Wrote app integration planning outputs")
    return {"overall_readiness": overall_readiness}, [rules_out, plan_csv, summary_path]


def main():
    parser = argparse.ArgumentParser(description="Phase 13D app.py integration planning engine.")
    parser.add_argument("--readiness", default=os.path.join(ROOT, "phase12_qa_uat_hardening", "production_readiness_assessment.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    if not os.path.isfile(args.rules):
        logger.error("Rules not found: %s", args.rules)
        return 1

    stats, outputs = run_engine(args.rules, args.output, args.readiness)
    print(f"Integration planning complete. Readiness: {stats['overall_readiness']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
