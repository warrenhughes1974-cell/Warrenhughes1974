#!/usr/bin/env python3
"""Phase 22C — QuikLoan candidate population (analysis only — no conversion)."""

import argparse
import logging
import os

import pandas as pd

from claim_domain_eligibility_utils import DEFAULT_RULES, ROOT, load_json

DEFAULT_OUTPUT = os.path.join(ROOT, "phase22_semantic_governance")
logger = logging.getLogger("quikloan_candidate_population")


def build_quikloan_candidates(rules, output_dir):
    src = os.path.join(output_dir, "non_claim_accounting_activity_population.csv")
    if not os.path.isfile(src):
        raise FileNotFoundError(f"Missing non-claim population: {src}")
    df = pd.read_csv(src, dtype=str).fillna("")
    rows = []
    for _, row in df.iterrows():
        tx = row.get("transaction_codes", "")
        target_fields = []
        if "0412" in tx or "0451" in tx:
            target_fields.extend(["MLOANACCR", "MLOANBAL", "MLOANINT"])
        if "0411" in tx:
            target_fields.append("MLOANPRIN")
        if not target_fields:
            target_fields = ["MLOANBAL", "MLOANACCR"]
        rows.append({
            "reconstructed_claim_id": row.get("reconstructed_claim_id", ""),
            "derivation_candidate_id": row.get("derivation_candidate_id", ""),
            "policy_number": row.get("policy_number", ""),
            "transaction_codes": tx,
            "current_misroute": "QUIKCLMS (SURRENDER_CLAIM / CLAIMSTAT=99)",
            "recommended_qladmin_domain": "QuikLoan + Loan History",
            "recommended_quikloan_fields": "|".join(sorted(set(target_fields))),
            "mintamt_misinterpretation": row.get("mintamt", ""),
            "mapping_status": "CANDIDATE_ONLY_NOT_CONVERTED",
            "conversion_phase": "FUTURE_QUIKLOAN_WORKSTREAM",
            "governance_status": row.get("governance_status", ""),
            "production_dbf_flag": rules.get("production_dbf_flag", "N"),
            "rulebook_lineage": rules.get("rulebook_lineage", ""),
            "qladmin_manual_reference": "docs/claims_conversion_reference/QLAdmin_Help.pdf p.74-75,827-828",
            "lifepro_manual_reference": "LifePRO Accounting Transactions (4).pdf p.5 (04xx Borrowed Money)",
        })
    out_df = pd.DataFrame(rows)
    out_path = os.path.join(output_dir, "quikloan_candidate_population.csv")
    out_df.to_csv(out_path, index=False)
    logger.info("QuikLoan candidates: %s -> %s", len(out_df), out_path)
    return out_df, out_path


def main():
    parser = argparse.ArgumentParser(description="QuikLoan candidate population (analysis only).")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    rules = load_json(args.rules)
    df, path = build_quikloan_candidates(rules, args.output)
    print(f"QUIKLOAN_CANDIDATE_COUNT: {len(df)}")
    print(f"QUIKLOAN_CANDIDATE_OUTPUT: {os.path.abspath(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
