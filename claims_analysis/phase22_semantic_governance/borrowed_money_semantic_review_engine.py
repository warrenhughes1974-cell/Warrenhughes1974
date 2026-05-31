#!/usr/bin/env python3
"""Phase 22C — 04xx Borrowed Money semantic review (LifePRO authoritative)."""

import argparse
import logging
import os

import pandas as pd

from claim_domain_eligibility_utils import (
    DEFAULT_RULES,
    ROOT,
    borrowed_code_set,
    load_json,
    load_phase_artifacts,
    norm_code,
    parse_codes,
    strip_val,
)

DEFAULT_OUTPUT = os.path.join(ROOT, "phase22_semantic_governance")
logger = logging.getLogger("borrowed_money_semantic_review")


def run_review(rules, output_dir):
    hdr, _, _, uat_ids = load_phase_artifacts()
    borrowed = borrowed_code_set(rules)
    rows = []
    tx_catalog = {norm_code(t.get("transaction_code", "")): t for t in rules.get("transactions", [])}
    for code in sorted(borrowed):
        item = tx_catalog.get(code, {})
        obs = 0
        uat_obs = 0
        families = set()
        if not hdr.empty:
            for _, row in hdr.iterrows():
                tx = parse_codes(row.get("claim_relevant_transaction_codes", ""))
                if code not in tx:
                    continue
                obs += 1
                families.add(strip_val(row.get("claim_family", "")))
                cid = strip_val(row.get("reconstructed_claim_id", ""))
                if uat_ids and cid in uat_ids:
                    uat_obs += 1
        rows.append({
            "transaction_code": code,
            "lifepro_definition": item.get("lifepro_definition", ""),
            "accounting_category": "04xx Borrowed Money",
            "lifepro_manual_section": item.get("lifepro_manual_section", "LifePRO Accounting Transactions p.5"),
            "observed_phase4_claim_count": obs,
            "observed_uat_claim_count": uat_obs,
            "observed_phase4_families": "|".join(sorted(f for f in families if f)),
            "current_conversion_route": item.get("phase10_routing", item.get("current_claim_family_assignment", "")),
            "qladmin_target_domain": item.get("qladmin_target_domain", "QuikLoan + Loan History"),
            "should_enter_quikclms": "N",
            "claims_domain_eligible": "N",
            "rationale_from_documentation": item.get(
                "rationale",
                "LifePRO 04xx Borrowed Money — loan accounting, not death/surrender claims.",
            ),
            "recommended_governance_action": item.get(
                "recommended_governance_action",
                "NEVER route to QUIKCLMS without claim payout/benefit evidence",
            ),
            "production_dbf_flag": rules.get("production_dbf_flag", "N"),
            "rulebook_lineage": rules.get("rulebook_lineage", ""),
        })
    df = pd.DataFrame(rows)
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "borrowed_money_semantic_review.csv")
    df.to_csv(out_path, index=False)
    logger.info("Wrote borrowed money review (%s codes) -> %s", len(df), out_path)
    return df, out_path


def main():
    parser = argparse.ArgumentParser(description="04xx Borrowed Money semantic review.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    rules = load_json(args.rules)
    df, path = run_review(rules, args.output)
    print(f"BORROWED_MONEY_ROWS: {len(df)}")
    print(f"BORROWED_MONEY_OUTPUT: {os.path.abspath(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
