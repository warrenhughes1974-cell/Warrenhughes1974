#!/usr/bin/env python3
"""Phase 22B — QLAdmin domain alignment analysis from Help PDF rules config."""

import argparse
import json
import logging
import os

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_ALIGNMENT = os.path.join(ROOT, "config", "qladmin_domain_alignment_rules.json")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase22_semantic_governance")
REPO_ROOT = os.path.normpath(os.path.join(ROOT, ".."))

logger = logging.getLogger("qladmin_domain_alignment")


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def run_alignment(config, output_dir, pseudo_count=0, policy_count=0):
    rows = []
    for item in config.get("rows", []):
        row = dict(item)
        row["production_dbf_flag"] = config.get("production_dbf_flag", "N")
        row["manual_reference"] = config.get("manual_path", "")
        row["observed_pseudo_claim_count"] = pseudo_count
        row["observed_affected_policy_count"] = policy_count
        rows.append(row)
    df = pd.DataFrame(rows)
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "qladmin_domain_alignment_analysis.csv")
    df.to_csv(out_path, index=False)
    logger.info("Wrote alignment analysis (%s rows) -> %s", len(df), out_path)
    return df, out_path


def main():
    parser = argparse.ArgumentParser(description="Phase 22B QLAdmin domain alignment analysis.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--config", default=DEFAULT_ALIGNMENT)
    parser.add_argument("--pseudo-count", type=int, default=0)
    parser.add_argument("--policy-count", type=int, default=0)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    config = load_json(args.config)
    pseudo_path = os.path.join(args.output, "semantic_pseudo_claim_population.csv")
    pseudo_count = args.pseudo_count
    policy_count = args.policy_count
    if os.path.isfile(pseudo_path):
        pdf = pd.read_csv(pseudo_path, dtype=str)
        pseudo_count = len(pdf)
        policy_count = pdf["policy_number"].nunique() if "policy_number" in pdf.columns else policy_count
    _, path = run_alignment(config, args.output, pseudo_count, policy_count)
    manual = os.path.join(REPO_ROOT, config.get("manual_path", ""))
    print(f"ALIGNMENT_ROWS: {len(config.get('rows', []))}")
    print(f"MANUAL_PATH: {manual}")
    print(f"ALIGNMENT_OUTPUT: {os.path.abspath(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
