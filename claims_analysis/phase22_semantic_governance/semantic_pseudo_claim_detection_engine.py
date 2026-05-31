#!/usr/bin/env python3
"""Phase 22A — Semantic pseudo-claim detection (delegates to claim-domain eligibility model)."""

import argparse
import logging
import os
import shutil

import pandas as pd

from claim_domain_eligibility_utils import DEFAULT_RULES, ROOT, load_json
from non_claim_accounting_activity_engine import detect_non_claim_accounting

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT = os.path.join(ROOT, "phase22_semantic_governance")

logger = logging.getLogger("semantic_pseudo_claim_detection")


def detect_pseudo_claims(rules, output_dir):
    """Detect non-claim accounting activity misclassified as claims (expanded Phase 22C model)."""
    primary_path = os.path.join(output_dir, "non_claim_accounting_activity_population.csv")
    if os.path.isfile(primary_path):
        detected = pd.read_csv(primary_path, dtype=str).to_dict("records")
    else:
        detected, primary_path = detect_non_claim_accounting(rules, output_dir)
    legacy_path = os.path.join(output_dir, "semantic_pseudo_claim_population.csv")
    shutil.copy2(primary_path, legacy_path)
    logger.info(
        "Legacy alias semantic_pseudo_claim_population.csv (%s rows) from non-claim accounting population",
        len(detected),
    )
    return detected, legacy_path


def main():
    parser = argparse.ArgumentParser(description="Phase 22A pseudo-claim detection (claim-domain eligibility).")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    rules = load_json(args.rules)
    detected, path = detect_pseudo_claims(rules, args.output)
    print(f"PSEUDO_CLAIM_COUNT: {len(detected)}")
    print(f"PSEUDO_CLAIM_OUTPUT: {os.path.abspath(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
