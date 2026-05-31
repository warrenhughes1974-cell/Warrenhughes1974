#!/usr/bin/env python3
"""
Phase 17C — Business-facing exclusion logging (human-readable).

Documents every excluded/deferred claim and payment with business explanations.
Does NOT modify app.py or hide exclusions.
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
DEFAULT_OUTPUT = os.path.join(ROOT, "phase17_uat_governance_reporting")

logger = logging.getLogger("business_exclusion_logging")


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


def business_explain(blocker, templates):
    return templates.get(blocker, templates.get("GOVERNANCE_HOLD", "Record held for governance review."))


def remediation_text(row):
    rec = strip_val(row.get("remediation_recommendation", ""))
    workflow = strip_val(row.get("remediation_workflow", ""))
    if workflow:
        return workflow.replace("_", " ").title()
    if rec:
        return rec.replace("_", " ").title()
    return "Business review required before UAT inclusion."


def run_engine(deferred_claims, deferred_payments, rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    audit_ts = utc_now()
    rollback_id = f"{rules['rollback_snapshot_prefix']}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    templates = rules["business_explanation_templates"]
    lineage = rules["rulebook_lineage"]

    exclusion_rows = []
    for source, rtype in ((deferred_claims, "CLAIM"), (deferred_payments, "PAYMENT")):
        for _, row in source.iterrows():
            blocker = strip_val(row.get("blocker_category", row.get("deferred_category", "")))
            cat = strip_val(row.get("deferred_category", blocker))
            template_key = cat if cat in templates else blocker
            if template_key not in templates:
                template_key = "GOVERNANCE_HOLD" if rtype == "CLAIM" else "ORPHAN_PAYMENT"
            exclusion_rows.append({
                "audit_timestamp": audit_ts,
                "rollback_snapshot_id": rollback_id,
                "production_dbf_flag": rules["production_dbf_flag"],
                "record_type": rtype,
                "record_identifier": strip_val(row.get("derivation_candidate_id", "")) or strip_val(row.get("reconstructed_claim_id", "")),
                "reconstructed_claim_id": strip_val(row.get("reconstructed_claim_id", "")),
                "derivation_candidate_id": strip_val(row.get("derivation_candidate_id", "")),
                "governance_status": strip_val(row.get("governance_status", "")),
                "reason_excluded": cat,
                "blocker_category": blocker,
                "business_explanation": business_explain(template_key, templates),
                "remediation_recommendation": remediation_text(row),
                "replay_eligibility": strip_val(row.get("replay_eligibility", "")),
                "orphan_impact": strip_val(row.get("orphan_impact", "")),
                "reconciliation_impact": strip_val(row.get("reconciliation_impact", "")),
                "business_review_required": strip_val(row.get("business_review_required", "Y")),
                "replay_authorization_status": strip_val(row.get("replay_authorization_status", "")),
                "rulebook_lineage": lineage,
            })

    exclusion_df = pd.DataFrame(exclusion_rows)

    catalog_rows = []
    if not exclusion_df.empty:
        for blocker, grp in exclusion_df.groupby("blocker_category"):
            catalog_rows.append({
                "audit_timestamp": audit_ts,
                "production_dbf_flag": "N",
                "blocker_category": blocker,
                "exception_count": len(grp),
                "claim_count": (grp["record_type"] == "CLAIM").sum(),
                "payment_count": (grp["record_type"] == "PAYMENT").sum(),
                "business_explanation": business_explain(blocker, templates),
                "governance_status": grp["governance_status"].mode().iloc[0] if len(grp) else "",
                "business_review_required": "Y",
                "rulebook_lineage": lineage,
            })
    catalog_df = pd.DataFrame(catalog_rows)

    remediation_df = exclusion_df.copy()
    if not remediation_df.empty:
        remediation_df = remediation_df.sort_values("blocker_category")

    outputs = []
    for name, frame in [
        ("business_exclusion_log.csv", exclusion_df),
        ("governance_exception_catalog.csv", catalog_df),
        ("remediation_recommendation_log.csv", remediation_df),
    ]:
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        outputs.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_path = os.path.join(output_dir, "business_exclusion_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 17C Business Exclusion Log Summary ===",
            "",
            f"Total excluded records logged: {len(exclusion_df)}",
            f"Exception categories: {len(catalog_df)}",
            "",
            "All exclusions documented with business-readable explanations.",
            "production_dbf_flag=N",
        ]) + "\n")
    outputs.append(summary_path)
    return {"exclusions": len(exclusion_df)}, outputs


def main():
    parser = argparse.ArgumentParser(description="Phase 17C business exclusion logging engine.")
    parser.add_argument("--deferred-claims", default=os.path.join(DEFAULT_OUTPUT, "deferred_governance_claims.csv"))
    parser.add_argument("--deferred-payments", default=os.path.join(DEFAULT_OUTPUT, "deferred_governance_payments.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    stats, outputs = run_engine(load_csv(args.deferred_claims), load_csv(args.deferred_payments), args.rules, args.output)
    print(f"Phase 17C complete. Exclusions logged: {stats['exclusions']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
