#!/usr/bin/env python3
"""Phase 22 — Semantic business review workbench builder."""

import argparse
import json
import logging
import os
from datetime import datetime, timezone

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_RULES = os.path.join(ROOT, "config", "semantic_governance_rules.json")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase22_semantic_governance")

logger = logging.getLogger("semantic_business_review_workbench")


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_workbench(rules, output_dir):
    pseudo_path = os.path.join(output_dir, "semantic_pseudo_claim_population.csv")
    hold_path = os.path.join(output_dir, "semantic_governance_hold_population.csv")
    if not os.path.isfile(pseudo_path):
        raise FileNotFoundError(pseudo_path)
    pseudo = pd.read_csv(pseudo_path, dtype=str).fillna("")
    hold = pd.read_csv(hold_path, dtype=str).fillna("") if os.path.isfile(hold_path) else pd.DataFrame()

    audit_ts = utc_now()
    rows = []
    policy_counts = pseudo.groupby("policy_number").size().to_dict() if "policy_number" in pseudo.columns else {}
    for _, row in pseudo.iterrows():
        pol = row.get("policy_number", "")
        rows.append({
            "audit_timestamp": audit_ts,
            "workbench_category": "SEMANTIC_PSEUDO_CLAIM_REVIEW",
            "reconstructed_claim_id": row.get("reconstructed_claim_id", ""),
            "derivation_candidate_id": row.get("derivation_candidate_id", ""),
            "policy_number": pol,
            "example_qla_policy": "",
            "claim_family": row.get("claim_family", ""),
            "lifecycle_status": row.get("lifecycle_status", ""),
            "first_activity_date": row.get("first_activity_date", ""),
            "mintamt": row.get("mintamt", ""),
            "transaction_codes": row.get("transaction_codes", ""),
            "annual_recurrence_flag": row.get("annual_recurrence_flag", ""),
            "policy_pseudo_claim_count": policy_counts.get(pol, 1),
            "reason_excluded": row.get("reason_excluded", ""),
            "review_priority": "HIGH" if row.get("annual_recurrence_flag") == "Y" else "MEDIUM",
            "recommended_business_decision": "EXCLUDE_FROM_UAT_CLAIMS_PENDING_QUIKLOAN_DESIGN",
            "qladmin_target_domain": "QuikLoan (MLOANACCR/MLOANBAL) + Loan History",
            "production_dbf_flag": rules.get("production_dbf_flag", "N"),
            "governance_status": rules.get("governance_status", "SEMANTIC_GOVERNANCE_HOLD"),
            "rulebook_lineage": rules.get("rulebook_lineage", ""),
        })

    wb = pd.DataFrame(rows)
    out_path = os.path.join(output_dir, "semantic_business_review_workbench.csv")
    wb.to_csv(out_path, index=False)
    logger.info("Workbench rows: %s -> %s", len(wb), out_path)
    return wb, out_path


def main():
    parser = argparse.ArgumentParser(description="Phase 22 semantic business review workbench.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    rules = load_json(args.rules)
    wb, path = build_workbench(rules, args.output)
    print(f"WORKBENCH_ROWS: {len(wb)}")
    print(f"WORKBENCH_OUTPUT: {os.path.abspath(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
