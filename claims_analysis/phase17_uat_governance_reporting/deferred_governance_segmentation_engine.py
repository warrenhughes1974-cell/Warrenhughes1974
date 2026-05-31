#!/usr/bin/env python3
"""
Phase 17B — Deferred governance population segmentation (analysis only).

Quarantines governance-hold and business-review populations for transparency.
Does NOT modify app.py or suppress deferred records.
"""

import argparse
import json
import logging
import os
from datetime import datetime, timezone

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_RULES = os.path.join(ROOT, "config", "deferred_governance_segmentation_rules.json")
PHASE15 = os.path.join(ROOT, "phase15_qa_signoff_replay_execution")
PHASE12 = os.path.join(ROOT, "phase12_qa_uat_hardening")
PHASE16 = os.path.join(ROOT, "phase16_business_triage_remediation")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase17_uat_governance_reporting")

logger = logging.getLogger("deferred_governance_segmentation")


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


def run_engine(clms, clmp, recon, orphans, rejected, surrender_wb, orphan_triage, rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    audit_ts = utc_now()
    rollback_id = snapshot_id(rules["rollback_snapshot_prefix"])
    cats = rules["deferred_categories"]
    lineage = rules["rulebook_lineage"]

    uat_ids = set()
    uat_path = os.path.join(output_dir, "_uat_claim_id_set.csv")
    if os.path.isfile(uat_path):
        uat_ids = set(load_csv(uat_path)["reconstructed_claim_id"].map(strip_val))

    recon_lookup = {}
    if not recon.empty:
        for _, r in recon.iterrows():
            recon_lookup[strip_val(r.get("reconstructed_claim_id", ""))] = strip_val(r.get("reconciliation_status", ""))

    orphan_lookup = {}
    if not orphan_triage.empty:
        for _, r in orphan_triage.iterrows():
            orphan_lookup[strip_val(r.get("derivation_candidate_id", ""))] = r.to_dict()

    surrender_ids = set(surrender_wb["reconstructed_claim_id"].map(strip_val)) if not surrender_wb.empty else set()
    rejected_lookup = {}
    if not rejected.empty:
        for _, r in rejected.iterrows():
            rejected_lookup[strip_val(r.get("reconstructed_claim_id", ""))] = r.to_dict()

    claim_rows = []
    for _, row in clms.iterrows():
        cid = strip_val(row.get("reconstructed_claim_id", ""))
        if cid in uat_ids:
            continue
        recon_status = recon_lookup.get(cid, "")
        if cid in surrender_ids:
            cat_key = "SURRENDER_REVIEW"
        elif cid in rejected_lookup:
            cat_key = "UNBALANCED_CLAIM"
        elif recon_status != "PASS":
            cat_key = "RECONCILIATION_FAIL"
        else:
            cat_key = "GOVERNANCE_HOLD"
        meta = cats[cat_key]
        claim_rows.append({
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "production_dbf_flag": rules["production_dbf_flag"],
            "record_type": "CLAIM",
            "reconstructed_claim_id": cid,
            "derivation_candidate_id": strip_val(row.get("derivation_candidate_id", "")),
            "prototype_claimnum": strip_val(row.get("prototype_claimnum", "")),
            "deferred_category": cat_key,
            "blocker_category": meta["blocker_category"],
            "governance_status": meta["governance_status"],
            "business_review_required": meta["business_review_required"],
            "replay_authorization_status": strip_val(row.get("replay_authorization_status", "")),
            "replay_eligibility": meta["replay_eligibility"],
            "reconciliation_status": recon_status,
            "orphan_impact": "POSSIBLE" if cid in set(orphans[orphans["is_orphan"] == "Y"]["reconstructed_claim_id"]) else "NONE",
            "reconciliation_impact": recon_status,
            "remediation_recommendation": "BUSINESS_REVIEW" if meta["business_review_required"] == "Y" else "RULE_REFINEMENT",
            "rulebook_lineage": lineage,
        })

    payment_rows = []
    orphan_set = orphans[orphans["is_orphan"] == "Y"] if not orphans.empty else pd.DataFrame()
    for _, row in orphan_set.iterrows():
        triage = orphan_lookup.get(strip_val(row.get("derivation_candidate_id", "")), {})
        meta = cats["ORPHAN_PAYMENT"]
        payment_rows.append({
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "production_dbf_flag": rules["production_dbf_flag"],
            "record_type": "PAYMENT",
            "reconstructed_claim_id": strip_val(row.get("reconstructed_claim_id", "")),
            "derivation_candidate_id": strip_val(row.get("derivation_candidate_id", "")),
            "canonical_payment_stage_id": strip_val(row.get("canonical_payment_stage_id", "")),
            "deferred_category": "ORPHAN_PAYMENT",
            "blocker_category": meta["blocker_category"],
            "governance_status": meta["governance_status"],
            "business_review_required": meta["business_review_required"],
            "replay_authorization_status": "NOT_AUTHORIZED",
            "replay_eligibility": meta["replay_eligibility"],
            "mamount": strip_val(row.get("mamount", "")),
            "orphan_issue": strip_val(row.get("orphan_issues", "")),
            "parent_blocker_type": strip_val(triage.get("blocker_type", "")),
            "orphan_impact": "HIGH",
            "reconciliation_impact": "FAIL",
            "remediation_recommendation": strip_val(triage.get("remediation_workflow", "PARENT_CLAIM_REMEDIATION")),
            "rulebook_lineage": lineage,
        })

    for _, row in clmp.iterrows():
        cid = strip_val(row.get("reconstructed_claim_id", ""))
        dcid = strip_val(row.get("derivation_candidate_id", ""))
        if cid in uat_ids:
            continue
        if not orphan_set.empty and dcid in set(orphan_set.get("derivation_candidate_id", pd.Series()).map(strip_val)):
            continue
        if cid in uat_ids:
            continue
        if recon_lookup.get(cid, "") == "PASS" and cid not in surrender_ids:
            continue
        meta = cats["GOVERNANCE_HOLD"]
        payment_rows.append({
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "production_dbf_flag": rules["production_dbf_flag"],
            "record_type": "PAYMENT",
            "reconstructed_claim_id": cid,
            "derivation_candidate_id": dcid,
            "canonical_payment_stage_id": strip_val(row.get("canonical_payment_stage_id", "")),
            "deferred_category": "GOVERNANCE_HOLD",
            "blocker_category": meta["blocker_category"],
            "governance_status": meta["governance_status"],
            "business_review_required": "Y",
            "replay_authorization_status": strip_val(row.get("replay_authorization_status", "")),
            "replay_eligibility": meta["replay_eligibility"],
            "mamount": strip_val(row.get("mamount", "")),
            "orphan_impact": "LOW",
            "reconciliation_impact": recon_lookup.get(cid, ""),
            "remediation_recommendation": "BUSINESS_REVIEW",
            "rulebook_lineage": lineage,
        })

    claims_df = pd.DataFrame(claim_rows)
    payments_df = pd.DataFrame(payment_rows)

    metrics = [
        {"metric": "deferred_claims", "value": len(claims_df)},
        {"metric": "deferred_payments", "value": len(payments_df)},
        {"metric": "orphan_payments_deferred", "value": len(orphan_set) if not orphan_set.empty else 0},
        {"metric": "surrender_review_deferred", "value": len(surrender_ids)},
        {"metric": "unbalanced_rejected_deferred", "value": len(rejected_lookup)},
    ]
    for m in metrics:
        m.update({"audit_timestamp": audit_ts, "production_dbf_flag": "N", "governance_status": "DEFERRED"})
    metrics_df = pd.DataFrame(metrics)

    outputs = []
    for name, frame in [
        ("deferred_governance_claims.csv", claims_df),
        ("deferred_governance_payments.csv", payments_df),
        ("governance_population_metrics.csv", metrics_df),
    ]:
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        outputs.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_path = os.path.join(output_dir, "governance_hold_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 17B Deferred Governance Population Summary ===",
            "",
            f"Rollback snapshot: {rollback_id}",
            f"Deferred claims: {len(claims_df)}",
            f"Deferred payments: {len(payments_df)}",
            "",
            "All deferred populations preserved for business review.",
            "No suppressions. production_dbf_flag=N",
        ]) + "\n")
    outputs.append(summary_path)
    return {"deferred_claims": len(claims_df), "deferred_payments": len(payments_df)}, outputs


def main():
    parser = argparse.ArgumentParser(description="Phase 17B deferred governance segmentation engine.")
    parser.add_argument("--clms", default=os.path.join(PHASE15, "phase15_replay_quikclms_results.csv"))
    parser.add_argument("--clmp", default=os.path.join(PHASE15, "phase15_replay_quikclmp_results.csv"))
    parser.add_argument("--recon", default=os.path.join(PHASE15, "phase15_replay_reconciliation.csv"))
    parser.add_argument("--orphans", default=os.path.join(PHASE15, "phase15_replay_orphan_analysis.csv"))
    parser.add_argument("--rejected", default=os.path.join(PHASE12, "rejected_claim_root_cause_analysis.csv"))
    parser.add_argument("--surrender-workbench", default=os.path.join(PHASE16, "surrender_offset_business_triage_workbench.csv"))
    parser.add_argument("--orphan-triage", default=os.path.join(PHASE16, "remaining_orphan_root_cause_triage.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    stats, outputs = run_engine(
        load_csv(args.clms), load_csv(args.clmp), load_csv(args.recon),
        load_csv(args.orphans), load_csv(args.rejected), load_csv(args.surrender_workbench),
        load_csv(args.orphan_triage), args.rules, args.output,
    )
    print(f"Phase 17B complete. Deferred claims: {stats['deferred_claims']}, payments: {stats['deferred_payments']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
