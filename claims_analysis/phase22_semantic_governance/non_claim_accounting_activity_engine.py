#!/usr/bin/env python3
"""Phase 22C — Non-claim accounting activity detection (expanded governance hold population)."""

import argparse
import logging
import os
from datetime import datetime

import pandas as pd

from claim_domain_eligibility_utils import (
    DEFAULT_RULES,
    ROOT,
    build_reason_codes,
    load_json,
    load_phase_artifacts,
    p10_index,
    resolve_tx_codes,
    row_financials,
    should_hold_non_claim_accounting,
    strip_val,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT = os.path.join(ROOT, "phase22_semantic_governance")

logger = logging.getLogger("non_claim_accounting_activity")


def parse_yyyymmdd(value):
    s = strip_val(value)
    if not s or len(s) != 8:
        return None
    try:
        return datetime.strptime(s, "%Y%m%d")
    except ValueError:
        return None


def policy_annual_recurrence(dates, min_claims=3, min_days=330, max_days=400, ratio=0.6):
    parsed = sorted(d for d in (parse_yyyymmdd(x) for x in dates) if d)
    if len(parsed) < min_claims:
        return False
    gaps = [(parsed[i] - parsed[i - 1]).days for i in range(1, len(parsed))]
    if not gaps:
        return False
    hits = sum(1 for g in gaps if min_days <= g <= max_days)
    return (hits / len(gaps)) >= ratio


def detect_non_claim_accounting(rules, output_dir):
    hdr, life, p10, uat_ids = load_phase_artifacts()
    if hdr.empty:
        raise ValueError("claim_candidate_header.csv missing or empty")
    p10_idx = p10_index(p10)
    policy_dates = {}
    detected = []

    for _, row in hdr.iterrows():
        cid = strip_val(row.get("reconstructed_claim_id", ""))
        if not cid:
            continue
        tx_codes = resolve_tx_codes(row, life, cid)
        if not should_hold_non_claim_accounting(row, tx_codes, rules, uat_ids):
            continue

        p10_row = p10_idx.get(cid)
        if p10_row is None:
            p10_row = {}
        fin = row_financials(p10_row)
        policy = strip_val(row.get("policy_number", ""))
        first_date = strip_val(row.get("first_activity_date", ""))
        policy_dates.setdefault(policy, []).append(first_date)

        detected.append({
            "reconstructed_claim_id": cid,
            "derivation_candidate_id": strip_val(
                p10_row.get("derivation_candidate_id", f"QDC-{cid}")
            ),
            "policy_number": policy,
            "claim_family": strip_val(row.get("claim_family", "")),
            "lifecycle_status": strip_val(row.get("reconstructed_lifecycle_status", "")),
            "claim_subtype": strip_val(row.get("claim_subtype", "")),
            "first_activity_date": first_date,
            "transaction_codes": "|".join(sorted(tx_codes)),
            "activity_class": "LOAN_ACCOUNTING_ACTIVITY",
            "mpaid": fin["mpaid"],
            "mface": fin["mface"],
            "netdb": fin["netdb"],
            "mintamt": fin["mintamt"],
            "annual_recurrence_flag": "N",
            "reason_excluded": build_reason_codes(tx_codes, rules),
            "pattern_id": "NON_CLAIM_ACCOUNTING_ONLY",
            "hold_category": rules.get("hold_category", "SEMANTIC_PSEUDO_CLAIM"),
            "governance_status": rules.get("governance_status", "SEMANTIC_GOVERNANCE_HOLD"),
            "production_dbf_flag": rules.get("production_dbf_flag", "N"),
            "exclude_from_uat_emit": "Y",
            "exclude_from_uat_dbf": "Y",
            "rulebook_lineage": rules.get("rulebook_lineage", ""),
        })

    annual_policies = set()
    if rules.get("enable_annual_cadence_check", True):
        min_claims = int(rules.get("annual_cadence_min_claims_per_policy", 3))
        min_days = int(rules.get("annual_cadence_min_days", 330))
        max_days = int(rules.get("annual_cadence_max_days", 400))
        ratio = float(rules.get("annual_cadence_match_ratio", 0.6))
        for policy, dates in policy_dates.items():
            if policy_annual_recurrence(dates, min_claims, min_days, max_days, ratio):
                annual_policies.add(policy)

    for item in detected:
        if item["policy_number"] in annual_policies:
            item["annual_recurrence_flag"] = "Y"
            tx = set(item["transaction_codes"].split("|"))
            item["reason_excluded"] = build_reason_codes(tx, rules, annual_flag=True)

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "non_claim_accounting_activity_population.csv")
    pd.DataFrame(detected).to_csv(out_path, index=False)
    logger.info("Detected %s non-claim accounting rows -> %s", len(detected), out_path)
    return detected, out_path


def main():
    parser = argparse.ArgumentParser(description="Non-claim accounting activity detection.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    rules = load_json(args.rules)
    detected, path = detect_non_claim_accounting(rules, args.output)
    print(f"NON_CLAIM_ACCOUNTING_COUNT: {len(detected)}")
    print(f"NON_CLAIM_ACCOUNTING_OUTPUT: {os.path.abspath(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
