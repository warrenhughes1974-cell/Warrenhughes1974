#!/usr/bin/env python3
"""
Phase 14E — Controlled app.py authorization prep (planning only).

Extends Phase 13D integration plan with Phase 14 governance signoff gates.
Does NOT modify app.py.
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
DEFAULT_RULES = os.path.join(ROOT, "config", "app_authorization_prep_rules.json")
PHASE12 = os.path.join(ROOT, "phase12_qa_uat_hardening")
PHASE14 = os.path.join(ROOT, "phase14_controlled_rule_refinement")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase14_controlled_rule_refinement")

logger = logging.getLogger("app_authorization_prep")


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_engine(rules_path, output_dir, phase14_delta_path=None, readiness_path=None):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    audit_ts = utc_now()

    rows = []
    for idx, cp in enumerate(rules["authorization_checkpoints"], start=1):
        rows.append({
            "audit_timestamp": audit_ts,
            "sequence": idx,
            "checkpoint": cp,
            "authorization_required": "Y",
            "modify_app_py": "N",
            "production_dbf_flag": "N",
            "rollback_safe": "Y",
        })

    for table, plan in rules["schema_registration"].items():
        rows.append({
            "audit_timestamp": audit_ts,
            "sequence": 100 + len(rows),
            "checkpoint": f"schema_registration_{table}",
            "authorization_required": "Y",
            "detail": plan,
            "modify_app_py": "N",
            "production_dbf_flag": "N",
            "rollback_safe": "Y",
        })

    orphan_remaining = None
    if phase14_delta_path and os.path.isfile(phase14_delta_path):
        delta = pd.read_csv(phase14_delta_path)
        rem = delta[delta["metric"] == "projected_remaining_orphans"]
        if not rem.empty:
            orphan_remaining = float(rem.iloc[0]["value"])

    overall = "NOT_READY"
    if readiness_path and os.path.isfile(readiness_path):
        rdf = pd.read_csv(readiness_path)
        o = rdf[rdf["readiness_dimension"] == "OVERALL_PRODUCTION_READINESS"]
        if not o.empty:
            overall = str(o.iloc[0]["assessment"])

    rows.append({
        "audit_timestamp": audit_ts,
        "sequence": 999,
        "checkpoint": "overall_production_readiness",
        "authorization_required": "Y",
        "detail": overall,
        "projected_remaining_orphans": orphan_remaining if orphan_remaining is not None else "",
        "modify_app_py": "N",
        "production_dbf_flag": "N",
        "rollback_safe": "Y",
    })

    plan_df = pd.DataFrame(rows)
    rules_out = os.path.join(output_dir, "app_authorization_prep_rules.json")
    shutil.copy2(rules_path, rules_out)

    plan_csv = os.path.join(output_dir, "app_authorization_prep_analysis.csv")
    plan_df.to_csv(plan_csv, index=False, encoding="utf-8")

    summary_path = os.path.join(output_dir, "app_authorization_prep_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 14E Controlled app.py Authorization Prep Summary ===",
            "",
            f"Planning timestamp: {audit_ts}",
            f"Modify app.py: NO",
            f"Overall readiness: {overall}",
            f"Projected remaining orphans: {orphan_remaining if orphan_remaining is not None else 'pending 14D'}",
            "",
            "Integration wrapper:",
            f"  {rules['integration_wrapper']}",
            "",
            "Authorization checkpoints:",
            *[f"  {i}. {cp}" for i, cp in enumerate(rules['authorization_checkpoints'], 1)],
            "",
            "Output files:",
            f"  - {rules_out}",
            f"  - {plan_csv}",
            f"  - {summary_path}",
        ]) + "\n")

    logger.info("Wrote app authorization prep outputs")
    return {"readiness": overall}, [rules_out, plan_csv, summary_path]


def main():
    parser = argparse.ArgumentParser(description="Phase 14E app authorization prep engine.")
    parser.add_argument("--orphan-delta", default=os.path.join(PHASE14, "orphan_population_delta_analysis.csv"))
    parser.add_argument("--readiness", default=os.path.join(PHASE12, "production_readiness_assessment.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    stats, outputs = run_engine(args.rules, args.output, args.orphan_delta, args.readiness)
    print(f"Phase 14E complete. Readiness: {stats['readiness']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
