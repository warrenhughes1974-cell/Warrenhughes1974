#!/usr/bin/env python3
"""
Phase 17A — UAT candidate segmentation (CSV only, no production DBFs).

Separates governance-cleared UAT-safe populations from deferred populations.
Does NOT modify app.py or stable engines.
"""

import argparse
import json
import logging
import os
from datetime import datetime, timezone

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_RULES = os.path.join(ROOT, "config", "uat_candidate_segmentation_rules.json")
PHASE15 = os.path.join(ROOT, "phase15_qa_signoff_replay_execution")
PHASE12 = os.path.join(ROOT, "phase12_qa_uat_hardening")
PHASE16 = os.path.join(ROOT, "phase16_business_triage_remediation")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase17_uat_governance_reporting")

logger = logging.getLogger("uat_candidate_segmentation")


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


def run_engine(clms, clmp, recon, orphans, rejected, surrender_wb, rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    audit_ts = utc_now()
    rollback_id = snapshot_id(rules["rollback_snapshot_prefix"])
    criteria = rules["uat_inclusion_criteria"]
    lineage = rules["rulebook_lineage"]

    orphan_parents = set()
    if not orphans.empty:
        orphan_parents = set(
            orphans[orphans["is_orphan"] == "Y"]["reconstructed_claim_id"].map(strip_val)
        )

    surrender_ids = set()
    if not surrender_wb.empty:
        surrender_ids = set(surrender_wb["reconstructed_claim_id"].map(strip_val))

    rejected_ids = set()
    if not rejected.empty:
        rejected_ids = set(rejected["reconstructed_claim_id"].map(strip_val))

    recon_lookup = {}
    if not recon.empty:
        for _, r in recon.iterrows():
            recon_lookup[strip_val(r.get("reconstructed_claim_id", ""))] = strip_val(r.get("reconciliation_status", ""))

    uat_claim_ids = set()
    deferred_claim_ids = set()
    for _, row in clms.iterrows():
        cid = strip_val(row.get("reconstructed_claim_id", ""))
        if not cid:
            continue
        recon_status = recon_lookup.get(cid, "")
        gen_status = strip_val(row.get("generation_status", ""))
        excluded = (
            gen_status != criteria["require_generation_status"]
            or recon_status != criteria["require_reconciliation_status"]
            or cid in orphan_parents
            or (criteria["exclude_surrender_review_parents"] and cid in surrender_ids)
            or (criteria["exclude_unbalanced_rejected_parents"] and cid in rejected_ids)
        )
        if excluded:
            deferred_claim_ids.add(cid)
        else:
            uat_claim_ids.add(cid)

    uat_clms_rows = []
    for _, row in clms.iterrows():
        cid = strip_val(row.get("reconstructed_claim_id", ""))
        if cid not in uat_claim_ids:
            continue
        replay_source = strip_val(row.get("replay_source", "BASELINE"))
        segment_tag = rules["uat_segment_tags"].get(replay_source, "governance_cleared")
        uat_clms_rows.append({
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "production_dbf_flag": rules["production_dbf_flag"],
            "record_type": "QUIKCLMS",
            "reconstructed_claim_id": cid,
            "prototype_claimnum": strip_val(row.get("prototype_claimnum", "")),
            "derivation_candidate_id": strip_val(row.get("derivation_candidate_id", "")),
            "replay_source": replay_source,
            "uat_segment": segment_tag,
            "governance_status": "UAT_CLEARED",
            "business_review_required": "N",
            "replay_authorization_status": strip_val(row.get("replay_authorization_status", "")),
            "reconciliation_status": recon_lookup.get(cid, ""),
            "generation_status": strip_val(row.get("generation_status", "")),
            "blocker_category": "NONE",
            "business_explanation": "Claim passed reconciliation and governance checks; cleared for UAT candidate testing.",
            "orphan_impact": "NONE",
            "reconciliation_impact": "PASS",
            "replay_eligibility": "UAT_READY",
            "remediation_recommendation": "NONE",
            "rulebook_lineage": lineage,
        })

    uat_clmp_rows = []
    for _, row in clmp.iterrows():
        cid = strip_val(row.get("reconstructed_claim_id", ""))
        is_orphan = strip_val(row.get("is_orphan", "")) == "Y" if "is_orphan" in row else False
        if not orphans.empty and not is_orphan:
            match = orphans[
                (orphans["derivation_candidate_id"] == strip_val(row.get("derivation_candidate_id", "")))
                & (orphans["is_orphan"] == "Y")
            ]
            is_orphan = len(match) > 0
        if is_orphan or cid not in uat_claim_ids:
            continue
        replay_source = strip_val(row.get("replay_source", "BASELINE"))
        segment_tag = rules["uat_segment_tags"].get(replay_source, "governance_cleared")
        uat_clmp_rows.append({
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "production_dbf_flag": rules["production_dbf_flag"],
            "record_type": "QUIKCLMP",
            "reconstructed_claim_id": cid,
            "canonical_payment_stage_id": strip_val(row.get("canonical_payment_stage_id", "")),
            "derivation_candidate_id": strip_val(row.get("derivation_candidate_id", "")),
            "prototype_claimnum": strip_val(row.get("prototype_claimnum", "")),
            "replay_source": replay_source,
            "uat_segment": segment_tag,
            "governance_status": "UAT_CLEARED",
            "business_review_required": "N",
            "replay_authorization_status": strip_val(row.get("replay_authorization_status", "")),
            "generation_status": strip_val(row.get("generation_status", "")),
            "mamount": strip_val(row.get("mamount", "")),
            "blocker_category": "NONE",
            "business_explanation": "Payment linked to UAT-cleared claim; available for UAT testing.",
            "orphan_impact": "NONE",
            "reconciliation_impact": "PASS",
            "replay_eligibility": "UAT_READY",
            "remediation_recommendation": "NONE",
            "rulebook_lineage": lineage,
        })

    uat_clms_df = pd.DataFrame(uat_clms_rows)
    uat_clmp_df = pd.DataFrame(uat_clmp_rows)

    metrics_rows = [
        {"metric": "total_quikclms_replay", "value": len(clms), "population": "PHASE15_REPLAY"},
        {"metric": "uat_candidate_quikclms", "value": len(uat_clms_df), "population": "UAT_CLEARED"},
        {"metric": "deferred_quikclms", "value": len(clms) - len(uat_clms_df), "population": "DEFERRED"},
        {"metric": "total_quikclmp_replay", "value": len(clmp), "population": "PHASE15_REPLAY"},
        {"metric": "uat_candidate_quikclmp", "value": len(uat_clmp_df), "population": "UAT_CLEARED"},
        {"metric": "deferred_quikclmp", "value": len(clmp) - len(uat_clmp_df), "population": "DEFERRED"},
        {"metric": "orphan_payments_excluded", "value": len(orphan_parents), "population": "DEFERRED"},
        {"metric": "lifecycle_replay_uat_claims", "value": (uat_clms_df["replay_source"] == "LIFECYCLE_REPLAY_OVERLAY").sum() if not uat_clms_df.empty else 0, "population": "UAT_CLEARED"},
        {"metric": "trustee_qa_uat_payments", "value": (uat_clmp_df["replay_source"] == "TRUSTEE_QA_OVERLAY").sum() if not uat_clmp_df.empty else 0, "population": "UAT_CLEARED"},
    ]
    for m in metrics_rows:
        m.update({
            "audit_timestamp": audit_ts,
            "production_dbf_flag": rules["production_dbf_flag"],
            "governance_status": "UAT_SEGMENTATION",
        })
    metrics_df = pd.DataFrame(metrics_rows)

    outputs = []
    for name, frame in [
        ("uat_candidate_quikclms.csv", uat_clms_df),
        ("uat_candidate_quikclmp.csv", uat_clmp_df),
        ("uat_candidate_metrics.csv", metrics_df),
    ]:
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        outputs.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_path = os.path.join(output_dir, "uat_candidate_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 17A UAT Candidate Segmentation Summary ===",
            "",
            f"Rollback snapshot: {rollback_id}",
            f"UAT candidate QUIKCLMS: {len(uat_clms_df)}",
            f"UAT candidate QUIKCLMP: {len(uat_clmp_df)}",
            f"Deferred from UAT (claims): {len(clms) - len(uat_clms_df)}",
            "",
            "UAT inclusion: reconciliation PASS, no orphan payments, not surrender-hold, not rejected-unbalanced.",
            "CSV outputs only. production_dbf_flag=N",
            "No production DBFs generated.",
        ]) + "\n")
    outputs.append(summary_path)

    # Persist claim sets for downstream engines
    pd.DataFrame({"reconstructed_claim_id": list(uat_claim_ids)}).to_csv(
        os.path.join(output_dir, "_uat_claim_id_set.csv"), index=False,
    )
    pd.DataFrame({"reconstructed_claim_id": list(deferred_claim_ids)}).to_csv(
        os.path.join(output_dir, "_deferred_claim_id_set.csv"), index=False,
    )
    return {"uat_clms": len(uat_clms_df), "uat_clmp": len(uat_clmp_df)}, outputs


def main():
    parser = argparse.ArgumentParser(description="Phase 17A UAT candidate segmentation engine.")
    parser.add_argument("--clms", default=os.path.join(PHASE15, "phase15_replay_quikclms_results.csv"))
    parser.add_argument("--clmp", default=os.path.join(PHASE15, "phase15_replay_quikclmp_results.csv"))
    parser.add_argument("--recon", default=os.path.join(PHASE15, "phase15_replay_reconciliation.csv"))
    parser.add_argument("--orphans", default=os.path.join(PHASE15, "phase15_replay_orphan_analysis.csv"))
    parser.add_argument("--rejected", default=os.path.join(PHASE12, "rejected_claim_root_cause_analysis.csv"))
    parser.add_argument("--surrender-workbench", default=os.path.join(PHASE16, "surrender_offset_business_triage_workbench.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    stats, outputs = run_engine(
        load_csv(args.clms), load_csv(args.clmp), load_csv(args.recon),
        load_csv(args.orphans), load_csv(args.rejected), load_csv(args.surrender_workbench),
        args.rules, args.output,
    )
    print(f"Phase 17A complete. UAT CLMS: {stats['uat_clms']}, UAT CLMP: {stats['uat_clmp']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
