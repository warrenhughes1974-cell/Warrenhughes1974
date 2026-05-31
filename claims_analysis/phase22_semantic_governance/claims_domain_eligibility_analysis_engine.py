#!/usr/bin/env python3
"""Phase 22C — Claim domain transaction eligibility analysis (LifePRO + QLAdmin authoritative)."""

import argparse
import logging
import os
from collections import Counter

import pandas as pd

from claim_domain_eligibility_utils import (
    DEFAULT_RULES,
    ROOT,
    load_csv,
    load_json,
    load_phase_artifacts,
    norm_code,
    parse_codes,
    strip_val,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT = os.path.join(ROOT, "phase22_semantic_governance")

logger = logging.getLogger("claims_domain_eligibility_analysis")


def phase4_family_for_code(code, hdr):
    code = norm_code(code)
    if hdr.empty:
        return ""
    counts = Counter()
    for _, row in hdr.iterrows():
        if code in parse_codes(row.get("claim_relevant_transaction_codes", "")):
            counts[strip_val(row.get("claim_family", ""))] += 1
    if not counts:
        return ""
    return counts.most_common(1)[0][0]


def uat_treatment(code, hdr, uat_ids, hold_ids):
    code = norm_code(code)
    if hdr.empty:
        return "NOT_OBSERVED"
    in_uat = 0
    held = 0
    for _, row in hdr.iterrows():
        cid = strip_val(row.get("reconstructed_claim_id", ""))
        if code not in parse_codes(row.get("claim_relevant_transaction_codes", "")):
            continue
        if uat_ids and cid in uat_ids:
            in_uat += 1
            if cid in hold_ids:
                held += 1
    if in_uat == 0:
        return "NOT_IN_UAT"
    if held == in_uat:
        return "SEMANTIC_GOVERNANCE_HOLD"
    if held:
        return "PARTIAL_HOLD"
    return "UAT_EMITTED"


def run_analysis(rules, output_dir, hold_ids=None):
    hold_ids = hold_ids or set()
    hdr, _, _, uat_ids = load_phase_artifacts()
    rows = []
    for item in rules.get("transactions", []):
        code = norm_code(item.get("transaction_code", ""))
        rows.append({
            "transaction_code": code,
            "lifepro_definition": item.get("lifepro_definition", ""),
            "accounting_category": item.get("accounting_category", ""),
            "lifepro_manual_section": item.get("lifepro_manual_section", ""),
            "current_claim_family_assignment": item.get("current_claim_family_assignment", ""),
            "current_phase4_family": phase4_family_for_code(code, hdr) or item.get("phase4_family", ""),
            "current_phase10_routing": item.get("phase10_routing", ""),
            "current_uat_treatment": uat_treatment(code, hdr, uat_ids, hold_ids),
            "likely_correct_qladmin_target_domain": item.get("qladmin_target_domain", ""),
            "claims_domain_eligible": item.get("claims_domain_eligible", ""),
            "rationale_from_documentation": item.get("rationale", ""),
            "recommended_governance_action": item.get("recommended_governance_action", ""),
            "production_dbf_flag": rules.get("production_dbf_flag", "N"),
            "rulebook_lineage": rules.get("rulebook_lineage", ""),
            "lifepro_manual_reference": rules["authoritative_references"][1]
            if len(rules.get("authoritative_references", [])) > 1 else "",
            "qladmin_manual_reference": rules["authoritative_references"][0]
            if rules.get("authoritative_references") else "",
        })
    df = pd.DataFrame(rows)
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "claims_domain_transaction_eligibility_analysis.csv")
    df.to_csv(out_path, index=False)
    logger.info("Wrote %s rows -> %s", len(df), out_path)
    return df, out_path


def main():
    parser = argparse.ArgumentParser(description="Claim domain transaction eligibility analysis.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    rules = load_json(args.rules)
    hold_path = os.path.join(args.output, "non_claim_accounting_activity_population.csv")
    hold_ids = set()
    if os.path.isfile(hold_path):
        hold_df = load_csv(hold_path)
        hold_ids = set(hold_df.get("reconstructed_claim_id", pd.Series(dtype=str)).astype(str))
    _, path = run_analysis(rules, args.output, hold_ids=hold_ids)
    print(f"ELIGIBILITY_ROWS: {len(pd.read_csv(path))}")
    print(f"ELIGIBILITY_OUTPUT: {os.path.abspath(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
