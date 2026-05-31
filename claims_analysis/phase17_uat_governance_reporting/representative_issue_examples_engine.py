#!/usr/bin/env python3
"""
Phase 17D — Representative issue examples for business review.

Generates categorized before/after examples from replay and governance outputs.
Does NOT modify stable engines or app.py.
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
PHASE15 = os.path.join(ROOT, "phase15_qa_signoff_replay_execution")
PHASE14 = os.path.join(ROOT, "phase14_controlled_rule_refinement")
PHASE16 = os.path.join(ROOT, "phase16_business_triage_remediation")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase17_uat_governance_reporting")

logger = logging.getLogger("representative_issue_examples")


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


def sample_df(df, n):
    if df.empty:
        return df
    return df.head(n)


def example_row(category, before, after, why, included, remediation, governance, audit_ts, rollback_id, rules, extra=None):
    row = {
        "audit_timestamp": audit_ts,
        "rollback_snapshot_id": rollback_id,
        "production_dbf_flag": rules["production_dbf_flag"],
        "example_category": category,
        "before_status": before,
        "after_status": after,
        "why_issue_occurred": why,
        "why_included_or_excluded": included,
        "remediation_path": remediation,
        "governance_reasoning": governance,
        "business_review_required": "Y" if "excluded" in included.lower() or "deferred" in included.lower() else "N",
        "replay_eligibility": extra.get("replay_eligibility", "") if extra else "",
        "reconstructed_claim_id": extra.get("reconstructed_claim_id", "") if extra else "",
        "derivation_candidate_id": extra.get("derivation_candidate_id", "") if extra else "",
        "rulebook_lineage": rules["rulebook_lineage"],
    }
    return row


def run_engine(orphan_triage, surrender_wb, trustee_signoff, lifecycle_replay, rejected, uat_clms, rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    audit_ts = utc_now()
    rollback_id = f"{rules['rollback_snapshot_prefix']}-EXAMPLES-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    sizes = rules["example_sample_sizes"]

    examples = []
    for _, row in sample_df(orphan_triage, sizes["orphan_examples"]).iterrows():
        examples.append(example_row(
            "ORPHAN_EXAMPLE",
            "Payment exists without accepted claim header (orphan)",
            "Still orphan after Phase 15 replay",
            f"Parent claim blocked: {strip_val(row.get('blocker_type', ''))}",
            "Excluded from UAT candidate population",
            strip_val(row.get("remediation_workflow", "Parent claim remediation")),
            strip_val(row.get("governance_status", "")),
            audit_ts, rollback_id, rules, row.to_dict(),
        ))

    for _, row in sample_df(surrender_wb, sizes["surrender_examples"]).iterrows():
        examples.append(example_row(
            "SURRENDER_OFFSET_EXAMPLE",
            "Surrender claim with large offset/residual",
            "Held in business review queue",
            f"Workbench bucket: {strip_val(row.get('workbench_bucket', ''))}",
            "Deferred from UAT; surrender review required",
            "Surrender offset business review",
            strip_val(row.get("governance_status", "")),
            audit_ts, rollback_id, rules, row.to_dict(),
        ))

    for _, row in sample_df(trustee_signoff, sizes["trustee_replay_examples"]).iterrows():
        examples.append(example_row(
            "TRUSTEE_REPLAY_EXAMPLE",
            "Trustee routing payment blocked from baseline prototype",
            "Trustee QA overlay replay accepted in Phase 15",
            "Trustee derivation required QA sign-off simulation",
            "Included in UAT if parent claim UAT-cleared",
            "Trustee QA review and authorized replay",
            strip_val(row.get("governance_status", "")),
            audit_ts, rollback_id, rules, row.to_dict(),
        ))

    for _, row in sample_df(lifecycle_replay, sizes["lifecycle_replay_examples"]).iterrows():
        examples.append(example_row(
            "LIFECYCLE_REPLAY_EXAMPLE",
            "Claim unbalanced due to lifecycle exclusion gap",
            strip_val(row.get("projected_balancing_status", "PROJECTED")),
            strip_val(row.get("projection_rationale", "Lifecycle exclusion handling")),
            "Included in UAT if reconciliation PASS after replay overlay",
            "Authorized lifecycle replay (no forced balancing)",
            strip_val(row.get("governance_status", "")),
            audit_ts, rollback_id, rules, row.to_dict(),
        ))

    for _, row in sample_df(rejected, sizes["unresolved_balancing_examples"]).iterrows():
        examples.append(example_row(
            "UNRESOLVED_BALANCING_EXAMPLE",
            strip_val(row.get("balancing_status", "UNBALANCED")),
            "Still rejected from prototype generation",
            strip_val(row.get("rejection_rationale", "Balancing validation failed")),
            "Excluded from UAT candidate population",
            strip_val(row.get("recommended_remediation", "Balancing review")),
            strip_val(row.get("governance_status", "")),
            audit_ts, rollback_id, rules, row.to_dict(),
        ))

    examples_df = pd.DataFrame(examples)

    success_rows = []
    phase15_clms = load_csv(os.path.join(PHASE15, "phase15_replay_quikclms_results.csv"))
    lifecycle_source = phase15_clms[phase15_clms["replay_source"] == "LIFECYCLE_REPLAY_OVERLAY"] if not phase15_clms.empty else pd.DataFrame()
    uat_ids = set(uat_clms["reconstructed_claim_id"].map(strip_val)) if not uat_clms.empty else set()
    for _, row in sample_df(lifecycle_source, sizes["replay_success_examples"]).iterrows():
        cid = strip_val(row.get("reconstructed_claim_id", ""))
        included = "Included in UAT candidate population" if cid in uat_ids else "Recovered by replay but deferred from UAT pending additional governance"
        success_rows.append(example_row(
            "REPLAY_SUCCESS_EXAMPLE",
            "Previously lifecycle-blocked / unbalanced",
            "Lifecycle replay overlay applied in Phase 15",
            "Lifecycle replay overlay recovered claim without forced balancing",
            included,
            "Continue governed replay if additional claims qualify",
            "REPLAY_RECOVERED",
            audit_ts, rollback_id, rules, row.to_dict(),
        ))
    success_df = pd.DataFrame(success_rows)

    unresolved_df = examples_df[
        examples_df["example_category"].isin([
            "ORPHAN_EXAMPLE", "SURRENDER_OFFSET_EXAMPLE", "UNRESOLVED_BALANCING_EXAMPLE",
        ])
    ].copy()

    outputs = []
    for name, frame in [
        ("representative_issue_examples.csv", examples_df),
        ("replay_success_examples.csv", success_df),
        ("unresolved_issue_examples.csv", unresolved_df),
    ]:
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        outputs.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_path = os.path.join(output_dir, "business_example_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 17D Representative Issue Examples Summary ===",
            "",
            f"Total examples: {len(examples_df)}",
            f"Replay success examples: {len(success_df)}",
            f"Unresolved issue examples: {len(unresolved_df)}",
            "",
            "Examples prepared for business/UAT review.",
            "production_dbf_flag=N",
        ]) + "\n")
    outputs.append(summary_path)
    return {"examples": len(examples_df)}, outputs


def main():
    parser = argparse.ArgumentParser(description="Phase 17D representative issue examples engine.")
    parser.add_argument("--orphan-triage", default=os.path.join(PHASE16, "remaining_orphan_root_cause_triage.csv"))
    parser.add_argument("--surrender-workbench", default=os.path.join(PHASE16, "surrender_offset_business_triage_workbench.csv"))
    parser.add_argument("--trustee-signoff", default=os.path.join(PHASE15, "trustee_qa_signoff_results.csv"))
    parser.add_argument("--lifecycle-replay", default=os.path.join(PHASE14, "lifecycle_balancing_replay_results.csv"))
    parser.add_argument("--rejected", default=os.path.join(ROOT, "phase12_qa_uat_hardening", "rejected_claim_root_cause_analysis.csv"))
    parser.add_argument("--uat-clms", default=os.path.join(DEFAULT_OUTPUT, "uat_candidate_quikclms.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    stats, outputs = run_engine(
        load_csv(args.orphan_triage), load_csv(args.surrender_workbench),
        load_csv(args.trustee_signoff), load_csv(args.lifecycle_replay),
        load_csv(args.rejected), load_csv(args.uat_clms),
        args.rules, args.output,
    )
    print(f"Phase 17D complete. Examples: {stats['examples']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
