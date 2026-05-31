#!/usr/bin/env python3
"""Phase 22A — Semantic governance hold population builder."""

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

logger = logging.getLogger("semantic_governance_hold")


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_hold_population(rules, output_dir):
    primary_path = os.path.join(output_dir, "non_claim_accounting_activity_population.csv")
    pseudo_path = os.path.join(output_dir, "semantic_pseudo_claim_population.csv")
    source_path = primary_path if os.path.isfile(primary_path) else pseudo_path
    if not os.path.isfile(source_path):
        raise FileNotFoundError(f"Missing detection output: {source_path}")
    df = pd.read_csv(source_path, dtype=str).fillna("")
    hold_category = rules.get("hold_category", "SEMANTIC_PSEUDO_CLAIM")
    audit_ts = utc_now()
    rows = []
    for _, row in df.iterrows():
        rows.append({
            "audit_timestamp": audit_ts,
            "hold_category": hold_category,
            "governance_status": rules.get("governance_status", "SEMANTIC_GOVERNANCE_HOLD"),
            "record_type": "QUIKCLMS",
            "reconstructed_claim_id": row.get("reconstructed_claim_id", ""),
            "derivation_candidate_id": row.get("derivation_candidate_id", ""),
            "policy_number": row.get("policy_number", ""),
            "claim_family": row.get("claim_family", ""),
            "lifecycle_status": row.get("lifecycle_status", ""),
            "reason_excluded": row.get("reason_excluded", ""),
            "activity_class": row.get("activity_class", "LOAN_ACCOUNTING_ACTIVITY"),
            "transaction_codes": row.get("transaction_codes", ""),
            "mintamt": row.get("mintamt", ""),
            "annual_recurrence_flag": row.get("annual_recurrence_flag", ""),
            "production_dbf_flag": rules.get("production_dbf_flag", "N"),
            "exclude_from_uat_emit": "Y" if rules.get("exclude_from_uat_emit") else "N",
            "exclude_from_uat_dbf": "Y" if rules.get("exclude_from_uat_dbf") else "N",
            "business_review_required": "Y",
            "business_explanation": (
                "Non-claim loan accounting activity (LifePRO 04xx Borrowed Money) misclassified as "
                "SURRENDER_CLAIM/QUIKCLMS. LifePRO defines 0412=Loan Interest Capitalized and "
                "0451=Unearned Interest Income — not death/surrender claims. QLAdmin assigns loan "
                "activity to QuikLoan/Loan History, not QUIKCLMS Death Claims."
            ),
            "remediation_recommendation": (
                "Business review required. Future target: QuikLoan/MLOANACCR — not auto-converted in Phase 22."
            ),
            "rulebook_lineage": rules.get("rulebook_lineage", ""),
        })
    hold_df = pd.DataFrame(rows)
    hold_path = os.path.join(output_dir, "semantic_governance_hold_population.csv")
    hold_df.to_csv(hold_path, index=False)

    patterns_path = os.path.join(output_dir, "loan_interest_pseudo_claim_patterns.csv")
    group_cols = ["transaction_codes"]
    if "activity_class" in df.columns:
        group_cols = ["activity_class", "transaction_codes"]
    elif "pattern_id" in df.columns:
        group_cols = ["pattern_id", "transaction_codes"]
    pattern_summary = (
        df.groupby(group_cols, dropna=False)
        .agg(claim_count=("reconstructed_claim_id", "count"), policy_count=("policy_number", "nunique"))
        .reset_index()
    )
    pattern_summary.to_csv(patterns_path, index=False)

    conflicts_path = os.path.join(output_dir, "active_policy_surrender_conflicts.csv")
    if "annual_recurrence_flag" in df.columns:
        conflicts = df[df["annual_recurrence_flag"].astype(str).str.upper() == "Y"].copy()
    else:
        conflicts = df.iloc[0:0].copy()
    if conflicts.empty:
        conflicts = df.copy()
    conflicts["conflict_type"] = "ACTIVE_POLICY_RECURRING_SURRENDER_CLAIMSTAT_99"
    conflicts.to_csv(conflicts_path, index=False)

    logger.info("Hold population: %s rows -> %s", len(hold_df), hold_path)
    return hold_df, hold_path


def main():
    parser = argparse.ArgumentParser(description="Phase 22A semantic governance hold builder.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    rules = load_json(args.rules)
    hold_df, path = build_hold_population(rules, args.output)
    print(f"HOLD_COUNT: {len(hold_df)}")
    print(f"HOLD_OUTPUT: {os.path.abspath(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
