#!/usr/bin/env python3
"""
Phase 14D — Orphan resolution authorized rerun analysis.

Measures projected orphan reduction after Phase 14A/14B authorized replays.
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
DEFAULT_RULES = os.path.join(ROOT, "config", "orphan_authorized_rerun_rules.json")
PHASE11 = os.path.join(ROOT, "phase11_prototype_dbf_generation")
PHASE13 = os.path.join(ROOT, "phase13_controlled_enterprise_integration")
PHASE14 = os.path.join(ROOT, "phase14_controlled_rule_refinement")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase14_controlled_rule_refinement")

logger = logging.getLogger("orphan_authorized_rerun")


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


def run_engine(baseline_orphans, lifecycle_replay, trustee_qa, crosswalk, rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    audit_ts = utc_now()
    rollback_id = snapshot_id(rules["rollback_snapshot_prefix"])

    accepted_claims = set(crosswalk["reconstructed_claim_id"].tolist()) if not crosswalk.empty else set()

    projected_new_claims = set()
    if not lifecycle_replay.empty:
        projected = lifecycle_replay[
            lifecycle_replay["projected_balancing_status"].isin(["PROJECTED_BALANCED", "PROJECTED_MINOR_VARIANCE"])
        ]
        projected_new_claims = set(projected["reconstructed_claim_id"].tolist())

    combined_accepted = accepted_claims | projected_new_claims

    rerun_rows = []
    for _, row in baseline_orphans.iterrows():
        cid = strip_val(row.get("reconstructed_claim_id", ""))
        resolved = cid in combined_accepted
        rerun_rows.append({
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "reconstructed_claim_id": cid,
            "canonical_payment_stage_id": strip_val(row.get("canonical_payment_stage_id", "")),
            "orphan_issue": strip_val(row.get("orphan_issue", "")),
            "baseline_orphan_status": "ORPHAN",
            "rerun_orphan_status": "RESOLVED" if resolved else "ORPHAN",
            "resolution_driver": "LIFECYCLE_REPLAY_PARENT_ACCEPTED" if cid in projected_new_claims else (
                "ALREADY_IN_PROTOTYPE" if cid in accepted_claims else "PARENT_STILL_REJECTED"
            ),
            "governance_status": "SAFE_TO_REPROCESS" if resolved else "PRODUCTION_BLOCKED",
            "severity": "HIGH" if not resolved else "MEDIUM",
            "remediability": "RECOVERABLE" if resolved else "PARTIALLY_RECOVERABLE",
            "replay_authorization_status": "RERUN_ANALYZED",
            "recovery_rationale": "Orphan preserved in audit; projected resolution from authorized replay",
            "lineage_source": "phase11_orphan|phase14d_authorized_rerun",
            "production_dbf_flag": "N",
        })

    rerun_df = pd.DataFrame(rerun_rows)
    baseline_count = len(baseline_orphans)
    post_resolved = len(rerun_df[rerun_df["rerun_orphan_status"] == "RESOLVED"]) if not rerun_df.empty else 0
    post_orphan = baseline_count - post_resolved

    delta_rows = [{
        "metric": "baseline_orphan_count",
        "value": baseline_count,
        "rollback_snapshot_id": rollback_id,
        "production_dbf_flag": "N",
    }, {
        "metric": "projected_resolved_orphans",
        "value": post_resolved,
        "rollback_snapshot_id": rollback_id,
        "production_dbf_flag": "N",
    }, {
        "metric": "projected_remaining_orphans",
        "value": post_orphan,
        "rollback_snapshot_id": rollback_id,
        "production_dbf_flag": "N",
    }, {
        "metric": "orphan_reduction_pct",
        "value": round(100.0 * post_resolved / max(baseline_count, 1), 2),
        "rollback_snapshot_id": rollback_id,
        "production_dbf_flag": "N",
    }, {
        "metric": "trustee_qa_payments_authorized",
        "value": len(trustee_qa) if not trustee_qa.empty else 0,
        "rollback_snapshot_id": rollback_id,
        "production_dbf_flag": "N",
    }, {
        "metric": "lifecycle_replay_authorized_claims",
        "value": len(lifecycle_replay) if not lifecycle_replay.empty else 0,
        "rollback_snapshot_id": rollback_id,
        "production_dbf_flag": "N",
    }]

    delta_df = pd.DataFrame(delta_rows)

    rules_out = os.path.join(output_dir, "orphan_authorized_rerun_rules.json")
    shutil.copy2(rules_path, rules_out)
    outputs = [rules_out]

    for name, frame in [
        ("orphan_resolution_rerun_results.csv", rerun_df),
        ("orphan_population_delta_analysis.csv", delta_df),
    ]:
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        outputs.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_path = os.path.join(output_dir, "orphan_recovery_rerun_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 14D Orphan Authorized Rerun Summary ===",
            "",
            f"Rollback snapshot: {rollback_id}",
            f"Baseline orphans: {baseline_count}",
            f"Projected resolved: {post_resolved}",
            f"Projected remaining: {post_orphan}",
            f"Reduction: {round(100.0 * post_resolved / max(baseline_count, 1), 2)}%",
            "",
            "Orphans NOT suppressed. Unresolved orphans remain visible.",
            "production_dbf_flag=N",
            "",
            "Output files:",
            *[f"  - {p}" for p in outputs],
            f"  - {summary_path}",
        ]) + "\n")
    outputs.append(summary_path)
    return {"baseline": baseline_count, "resolved": post_resolved, "remaining": post_orphan}, outputs


def main():
    parser = argparse.ArgumentParser(description="Phase 14D orphan authorized rerun engine.")
    parser.add_argument("--baseline-orphans", default=os.path.join(PHASE13, "orphan_resolution_workflow_analysis.csv"))
    parser.add_argument("--lifecycle-replay", default=os.path.join(PHASE14, "lifecycle_balancing_replay_results.csv"))
    parser.add_argument("--trustee-qa", default=os.path.join(PHASE14, "trustee_qa_review_population.csv"))
    parser.add_argument("--crosswalk", default=os.path.join(PHASE11, "claimnum_crosswalk.csv"))
    parser.add_argument("--rules", default=os.path.join(ROOT, "config", "orphan_authorized_rerun_rules.json"))
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    stats, outputs = run_engine(
        load_csv(args.baseline_orphans) if os.path.isfile(args.baseline_orphans) else pd.DataFrame(),
        load_csv(args.lifecycle_replay) if os.path.isfile(args.lifecycle_replay) else pd.DataFrame(),
        load_csv(args.trustee_qa) if os.path.isfile(args.trustee_qa) else pd.DataFrame(),
        load_csv(args.crosswalk) if os.path.isfile(args.crosswalk) else pd.DataFrame(),
        args.rules, args.output,
    )
    print(f"Phase 14D complete. Baseline orphans: {stats['baseline']}, projected resolved: {stats['resolved']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
