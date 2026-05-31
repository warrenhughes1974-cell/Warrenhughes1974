#!/usr/bin/env python3
"""
Phase 13B — Balancing remediation workflow governance engine (analysis only).

Classifies UNBALANCED claim failure patterns and replay candidates.
Does NOT force balancing or modify stable engines / app.py.
"""

import argparse
import json
import logging
import os
import re
import shutil
from datetime import datetime, timezone

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_RULES = os.path.join(ROOT, "config", "balancing_remediation_rules.json")
PHASE4 = os.path.join(ROOT, "phase4_claim_event_reconstruction")
PHASE6 = os.path.join(ROOT, "phase6_family_balancing_intelligence")
PHASE12 = os.path.join(ROOT, "phase12_qa_uat_hardening")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase13_controlled_enterprise_integration")

logger = logging.getLogger("balancing_remediation")


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


def classify_balancing_failure(row, rules):
    patterns = rules["failure_patterns"]
    family = strip_val(row.get("claim_family", ""))
    notes = strip_val(row.get("balancing_notes", ""))
    diff = abs(parse_amount(row.get("revised_balancing_difference", 0)))
    lifecycle_excl = parse_amount(row.get("lifecycle_only_amount_excluded", 0))
    large_threshold = float(patterns["LARGE_RESIDUAL"]["min_abs_difference"])
    replay_threshold = float(rules.get("replay_diff_threshold", 100.0))

    if lifecycle_excl >= float(patterns["LIFECYCLE_EXCLUSION_GAP"]["min_lifecycle_excluded"]):
        meta = patterns["LIFECYCLE_EXCLUSION_GAP"]
        pattern = "LIFECYCLE_EXCLUSION_GAP"
    elif family in patterns["SURRENDER_OFFSET_CYCLE"]["families"]:
        meta = patterns["SURRENDER_OFFSET_CYCLE"]
        pattern = "SURRENDER_OFFSET_CYCLE"
    elif family in patterns["DEATH_DECOMPOSITION_GAP"]["families"]:
        meta = patterns["DEATH_DECOMPOSITION_GAP"]
        pattern = "DEATH_DECOMPOSITION_GAP"
    elif any(m in notes for m in patterns["OPTIONAL_COMPONENT_ABSENT"]["match_notes"]):
        meta = patterns["OPTIONAL_COMPONENT_ABSENT"]
        pattern = "OPTIONAL_COMPONENT_ABSENT"
    elif diff >= large_threshold:
        meta = patterns["LARGE_RESIDUAL"]
        pattern = "LARGE_RESIDUAL"
    else:
        meta = patterns["GENERAL_UNBALANCED"]
        pattern = "GENERAL_UNBALANCED"

    replay_eligible = (
        pattern in {"LIFECYCLE_EXCLUSION_GAP", "OPTIONAL_COMPONENT_ABSENT"}
        and diff <= replay_threshold
    )

    return {
        "failure_pattern": pattern,
        "severity": meta["severity"],
        "remediability": meta["remediability"],
        "governance_status": meta["governance_status"],
        "recommended_remediation": meta["recommended_action"],
        "replay_simulation_eligible": "Y" if replay_eligible else "N",
        "balancing_difference_abs": diff,
        "lifecycle_only_excluded": lifecycle_excl,
    }


def run_engine(rejected_claims, revised_fin, rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    audit_ts = utc_now()

    merged = rejected_claims.merge(revised_fin, on="reconstructed_claim_id", how="left", suffixes=("", "_rev"))
    if "claim_family" not in merged.columns or merged["claim_family"].fillna("").eq("").all():
        if "claim_family_rev" in merged.columns:
            merged["claim_family"] = merged["claim_family_rev"]

    pattern_rows = []
    replay_rows = []
    for _, row in merged.iterrows():
        classification = classify_balancing_failure(row.to_dict(), rules)
        record = {
            "audit_timestamp": audit_ts,
            "reconstructed_claim_id": strip_val(row.get("reconstructed_claim_id", "")),
            "derivation_candidate_id": strip_val(row.get("derivation_candidate_id", "")),
            "enhanced_settlement_group_id": strip_val(row.get("enhanced_settlement_group_id", "")),
            "claim_family": strip_val(row.get("claim_family", "")),
            "applied_balancing_profile": strip_val(row.get("applied_balancing_profile", "")),
            "revised_balancing_status": strip_val(row.get("revised_balancing_status", "")),
            "revised_balancing_difference": strip_val(row.get("revised_balancing_difference", "")),
            "balancing_confidence": strip_val(row.get("balancing_confidence", "")),
            "balancing_notes": strip_val(row.get("balancing_notes", "")),
            "excluded_transaction_codes": strip_val(row.get("excluded_transaction_codes", "")),
            "optional_components_missing": strip_val(row.get("optional_components_missing", "")),
            "root_cause": strip_val(row.get("root_cause", "UNBALANCED")),
            "production_dbf_flag": "N",
            **classification,
        }
        pattern_rows.append(record)
        if classification["replay_simulation_eligible"] == "Y":
            replay_rows.append({
                **record,
                "replay_candidate_status": "SAFE_TO_REPROCESS",
                "replay_rationale": "Deterministic balancing replay candidate; no forced correction",
                "lineage_source": "phase6_revised_claim_financials|phase13b_balancing_remediation",
            })

    pattern_df = pd.DataFrame(pattern_rows)
    replay_df = pd.DataFrame(replay_rows)

    recs = []
    for pattern, sub in pattern_df.groupby("failure_pattern"):
        recs.append({
            "failure_pattern": pattern,
            "claim_count": len(sub),
            "recommended_rule_refinement": sub["recommended_remediation"].iloc[0],
            "governance_status": sub["governance_status"].mode().iloc[0],
            "remediability": sub["remediability"].mode().iloc[0],
            "replay_candidate_count": len(sub[sub["replay_simulation_eligible"] == "Y"]),
            "production_dbf_flag": "N",
        })
    rec_df = pd.DataFrame(recs)

    stats = {
        "total_unbalanced": len(pattern_df),
        "replay_candidates": len(replay_df),
        "patterns": pattern_df["failure_pattern"].value_counts().to_dict() if not pattern_df.empty else {},
    }

    rules_out = os.path.join(output_dir, "balancing_remediation_rules.json")
    shutil.copy2(rules_path, rules_out)
    outputs = [rules_out]

    for name, frame in [
        ("balancing_failure_pattern_analysis.csv", pattern_df),
        ("balancing_replay_candidate_population.csv", replay_df),
        ("balancing_rule_refinement_recommendations.csv", rec_df),
    ]:
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        outputs.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_path = os.path.join(output_dir, "balancing_remediation_governance_summary.txt")
    write_summary(summary_path, stats, outputs, pattern_df)
    outputs.append(summary_path)
    return stats, outputs


def write_summary(path, stats, outputs, pattern_df):
    lines = [
        "=== Phase 13B Balancing Remediation Workflow Summary ===",
        "",
        f"UNBALANCED claims analyzed: {stats['total_unbalanced']}",
        f"Replay simulation candidates: {stats['replay_candidates']}",
        "",
        "Failure pattern distribution:",
    ]
    for pattern, cnt in sorted(stats.get("patterns", {}).items()):
        lines.append(f"  {pattern}: {cnt}")
    lines.extend([
        "",
        "Enterprise notes:",
        "  - No forced balancing applied",
        "  - Residual and lineage visibility preserved",
        "  - production_dbf_flag=N on all outputs",
        "",
        "Output files:",
    ])
    for f in outputs:
        lines.append(f"  - {f}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Phase 13B balancing remediation workflow engine.")
    parser.add_argument("--rejected-claims", default=os.path.join(PHASE12, "rejected_claim_root_cause_analysis.csv"))
    parser.add_argument("--revised-financials", default=os.path.join(PHASE6, "revised_claim_financials.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    for label, path in (("Rejected claims", args.rejected_claims), ("Rules", args.rules)):
        if not os.path.isfile(path):
            logger.error("%s not found: %s", label, path)
            return 1

    stats, outputs = run_engine(
        load_csv(args.rejected_claims),
        load_csv(args.revised_financials) if os.path.isfile(args.revised_financials) else pd.DataFrame(),
        args.rules, args.output,
    )
    print(f"Balancing remediation analysis complete. Claims: {stats['total_unbalanced']}")
    print(f"Replay candidates: {stats['replay_candidates']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
