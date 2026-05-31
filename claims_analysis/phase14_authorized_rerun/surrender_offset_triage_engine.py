#!/usr/bin/env python3
"""
Phase 14C — Surrender offset cycle business triage (no automated remediation).

Classifies SURRENDER_OFFSET_CYCLE claims for business review.
Does NOT modify stable engines or app.py.
"""

import argparse
import json
import logging
import os
import shutil
from datetime import datetime, timezone

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_RULES = os.path.join(ROOT, "config", "surrender_offset_review_rules.json")
PHASE7B = os.path.join(ROOT, "phase7b_cross_claim_linkage")
PHASE13 = os.path.join(ROOT, "phase13_controlled_enterprise_integration")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase14_controlled_rule_refinement")

logger = logging.getLogger("surrender_offset_triage")


def load_csv(path):
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


def parse_amount(value):
    raw = strip_val(value).replace(",", "").replace("$", "")
    if not raw:
        return 0.0
    try:
        return float(raw)
    except ValueError:
        return 0.0


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def snapshot_id(prefix):
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def classify_surrender(row, rules, linkage_lookup):
    cats = rules["triage_categories"]
    diff = abs(parse_amount(row.get("balancing_difference_abs", row.get("revised_balancing_difference", 0))))
    esg = strip_val(row.get("enhanced_settlement_group_id", ""))
    cid = strip_val(row.get("reconstructed_claim_id", ""))
    linked = linkage_lookup.get(cid, False)

    if diff <= float(cats["OFFSET_ONLY_BALANCED_CYCLE"]["max_abs_difference"]):
        meta = cats["OFFSET_ONLY_BALANCED_CYCLE"]
        category = "OFFSET_ONLY_BALANCED_CYCLE"
    elif linked or (esg and "LINK" in esg.upper()):
        meta = cats["CROSS_CLAIM_DEPENDENT"]
        category = "CROSS_CLAIM_DEPENDENT"
    elif diff >= float(cats["LARGE_OFFSET_RESIDUAL"]["min_abs_difference"]):
        meta = cats["LARGE_OFFSET_RESIDUAL"]
        category = "LARGE_OFFSET_RESIDUAL"
    else:
        meta = cats["LARGE_OFFSET_RESIDUAL"]
        category = "LARGE_OFFSET_RESIDUAL"

    return {
        "triage_category": category,
        "governance_status": meta["governance_status"],
        "severity": meta["severity"],
        "remediability": meta["remediability"],
        "cross_claim_linkage_present": "Y" if linked else "N",
    }


def run_engine(balancing_patterns, enhanced_groups, rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    audit_ts = utc_now()
    rollback_id = snapshot_id(rules["rollback_snapshot_prefix"])

    target = rules["target_failure_pattern"]
    pop = balancing_patterns[balancing_patterns["failure_pattern"] == target].copy()

    linkage_lookup = {}
    if not enhanced_groups.empty and "reconstructed_claim_id" in enhanced_groups.columns:
        cross_statuses = {"ACCEPTED", "LINKED", "ENHANCED_GROUP", "CROSS_CLAIM_LINKED"}
        for _, g in enhanced_groups.iterrows():
            cid = strip_val(g.get("reconstructed_claim_id", ""))
            status = strip_val(g.get("linkage_status", "")).upper()
            linked = strip_val(g.get("linked_target_claim_id", "")) or strip_val(g.get("linked_source_claim_id", ""))
            linkage_lookup[cid] = status in cross_statuses and bool(linked)

    pattern_rows = []
    review_rows = []
    for _, row in pop.iterrows():
        triage = classify_surrender(row.to_dict(), rules, linkage_lookup)
        record = {
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "reconstructed_claim_id": strip_val(row.get("reconstructed_claim_id", "")),
            "derivation_candidate_id": strip_val(row.get("derivation_candidate_id", "")),
            "enhanced_settlement_group_id": strip_val(row.get("enhanced_settlement_group_id", "")),
            "balancing_difference_abs": parse_amount(row.get("balancing_difference_abs", 0)),
            "applied_balancing_profile": strip_val(row.get("applied_balancing_profile", "")),
            "balancing_notes": strip_val(row.get("balancing_notes", "")),
            "replay_authorization_status": "NOT_AUTHORIZED",
            "recovery_rationale": "Business triage only; no automated balancing",
            "lineage_source": "phase13b_balancing_remediation|phase14c_surrender_triage",
            "production_dbf_flag": "N",
            **triage,
        }
        pattern_rows.append(record)
        review_rows.append({
            **record,
            "business_review_queue_status": rules["business_review_queue_status"],
            "automated_remediation": "N",
        })

    pattern_df = pd.DataFrame(pattern_rows)
    review_df = pd.DataFrame(review_rows)

    rules_out = os.path.join(output_dir, "surrender_offset_review_rules.json")
    shutil.copy2(rules_path, rules_out)
    outputs = [rules_out]

    for name, frame in [
        ("surrender_offset_cycle_pattern_analysis.csv", pattern_df),
        ("surrender_offset_business_review_queue.csv", review_df),
    ]:
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        outputs.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_path = os.path.join(output_dir, "surrender_offset_governance_summary.txt")
    triage_lines = []
    if not pattern_df.empty:
        for k, v in pattern_df["triage_category"].value_counts().items():
            triage_lines.append(f"  {k}: {v}")
    else:
        triage_lines.append("  (none)")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 14C Surrender Offset Triage Summary ===",
            "",
            f"Rollback snapshot: {rollback_id}",
            f"SURRENDER_OFFSET_CYCLE claims triaged: {len(pattern_df)}",
            "",
            "Triage category distribution:",
            *triage_lines,
            "",
            "Business triage only. No automated remediation.",
            "production_dbf_flag=N",
            "",
            "Output files:",
            *[f"  - {p}" for p in outputs],
            f"  - {summary_path}",
        ]) + "\n")
    outputs.append(summary_path)
    return {"triaged": len(pattern_df)}, outputs


def main():
    parser = argparse.ArgumentParser(description="Phase 14C surrender offset triage engine.")
    parser.add_argument("--balancing-patterns", default=os.path.join(PHASE13, "balancing_failure_pattern_analysis.csv"))
    parser.add_argument("--enhanced-groups", default=os.path.join(PHASE7B, "enhanced_settlement_groups.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    stats, outputs = run_engine(
        load_csv(args.balancing_patterns),
        load_csv(args.enhanced_groups) if os.path.isfile(args.enhanced_groups) else pd.DataFrame(),
        args.rules, args.output,
    )
    print(f"Phase 14C complete. Triaged: {stats['triaged']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
