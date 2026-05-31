#!/usr/bin/env python3
"""
Phase 15A — Trustee QA sign-off execution engine (simulation only).

Executes controlled QA sign-off workflow for trustee recovery candidates.
Does NOT auto-approve or modify stable engines / app.py.
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
DEFAULT_RULES = os.path.join(ROOT, "config", "trustee_signoff_workflow_rules.json")
PHASE14 = os.path.join(ROOT, "phase14_controlled_rule_refinement")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase15_qa_signoff_replay_execution")

logger = logging.getLogger("trustee_qa_signoff")


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


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def snapshot_id(prefix):
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def run_engine(trustee_qa_pop, rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    audit_ts = utc_now()
    rollback_id = snapshot_id(rules["rollback_snapshot_prefix"])
    controls = rules["signoff_controls"]
    sim = rules["simulated_reviewer"]

    package_rows = []
    signoff_rows = []
    audit_rows = []

    for _, row in trustee_qa_pop.iterrows():
        base = {
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "canonical_payment_stage_id": strip_val(row.get("canonical_payment_stage_id", "")),
            "reconstructed_claim_id": strip_val(row.get("reconstructed_claim_id", "")),
            "derivation_candidate_id": strip_val(row.get("derivation_candidate_id", "")),
            "enhanced_settlement_group_id": strip_val(row.get("enhanced_settlement_group_id", "")),
            "derivation_confidence": strip_val(row.get("derivation_confidence", "")),
            "trustee_recovery_eligible": controls["trustee_recovery_eligible"],
            "qa_review_required": controls["qa_review_required"],
            "auto_approved": controls["auto_approved"],
            "production_authorized": controls["production_authorized"],
            "production_dbf_flag": "N",
            "lineage_source": "phase14a_trustee_qa|phase15a_signoff",
        }
        package_rows.append({
            **base,
            "review_package_status": "READY_FOR_QA",
            "governance_status": strip_val(row.get("governance_status", "QA_REVIEW_REQUIRED")),
            "replay_authorization_status": strip_val(row.get("replay_authorization_status", "")),
            "recovery_rationale": strip_val(row.get("recovery_rationale", "")),
        })
        signoff_rows.append({
            **base,
            "qa_review_status": sim["signoff_status"] if sim.get("enabled") else "PENDING",
            "reviewer_id": sim.get("reviewer_id", "QA_SIMULATION"),
            "signoff_result": "SIMULATED_PASS" if sim.get("enabled") else "PENDING",
            "governance_status": rules["governance_status_after_signoff"],
            "replay_authorization_status": "AUTHORIZED_FOR_PHASE15_REPLAY" if sim.get("enabled") else "NOT_AUTHORIZED",
            "signoff_notes": sim.get("notes", ""),
        })
        audit_rows.append({
            **base,
            "audit_event": "TRUSTEE_QA_SIGNOFF_SIMULATION",
            "qa_review_status": sim["signoff_status"],
            "governance_status": rules["governance_status_after_signoff"],
            "confidence_elevated": "N",
        })

    package_df = pd.DataFrame(package_rows)
    signoff_df = pd.DataFrame(signoff_rows)
    audit_df = pd.DataFrame(audit_rows)

    rules_out = os.path.join(output_dir, "trustee_signoff_workflow_rules.json")
    shutil.copy2(rules_path, rules_out)
    outputs = [rules_out]

    for name, frame in [
        ("trustee_qa_signoff_review_package.csv", package_df),
        ("trustee_qa_signoff_results.csv", signoff_df),
        ("trustee_governance_audit_log.csv", audit_df),
    ]:
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        outputs.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_path = os.path.join(output_dir, "trustee_signoff_execution_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 15A Trustee QA Sign-off Execution Summary ===",
            "",
            f"Rollback snapshot: {rollback_id}",
            f"Trustee QA packages: {len(package_df)}",
            f"Simulated sign-offs: {len(signoff_df)}",
            "",
            "Controls preserved: auto_approved=N, production_authorized=N, confidence_elevated=N",
            "Stable Phase 10A/11 engines NOT modified",
            "production_dbf_flag=N",
            "",
            "Output files:",
            *[f"  - {p}" for p in outputs],
            f"  - {summary_path}",
        ]) + "\n")
    outputs.append(summary_path)
    return {"signed_off": len(signoff_df)}, outputs


def main():
    parser = argparse.ArgumentParser(description="Phase 15A trustee QA sign-off engine.")
    parser.add_argument("--trustee-qa", default=os.path.join(PHASE14, "trustee_qa_review_population.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    if not os.path.isfile(args.trustee_qa):
        logger.error("Trustee QA population not found: %s", args.trustee_qa)
        return 1

    stats, outputs = run_engine(load_csv(args.trustee_qa), args.rules, args.output)
    print(f"Phase 15A complete. Sign-off packages: {stats['signed_off']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
