#!/usr/bin/env python3
"""
Phase 16B — Surrender offset business triage workbench (no automated balancing).

Business-friendly classification of 4,287 surrender offset claims.
Does NOT modify stable engines or app.py.
"""

import argparse
import json
import logging
import os
from datetime import datetime, timezone

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_RULES = os.path.join(ROOT, "config", "surrender_offset_business_triage_rules.json")
PHASE14 = os.path.join(ROOT, "phase14_controlled_rule_refinement")
PHASE13 = os.path.join(ROOT, "phase13_controlled_enterprise_integration")
PHASE7B = os.path.join(ROOT, "phase7b_cross_claim_linkage")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase16_business_triage_remediation")

logger = logging.getLogger("surrender_offset_business_triage")


def load_csv(path):
    if not os.path.isfile(path):
        return pd.DataFrame()
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


def classify_workbench(row, rules, group_lookup):
    buckets = rules["workbench_buckets"]
    diff = abs(parse_amount(row.get("balancing_difference_abs", 0)))
    cid = strip_val(row.get("reconstructed_claim_id", ""))
    esg = strip_val(row.get("enhanced_settlement_group_id", ""))
    group = group_lookup.get(cid, {})
    member_count = int(float(group.get("group_member_count", "1") or 1))
    linked = strip_val(row.get("cross_claim_linkage_present", "")) == "Y" or strip_val(group.get("linkage_status", "")) in {
        "ACCEPTED", "LINKED", "ENHANCED_GROUP", "CROSS_CLAIM_LINKED",
    }

    if diff >= float(buckets["LARGE_RESIDUAL_FAMILY"]["min_abs_difference"]):
        meta = buckets["LARGE_RESIDUAL_FAMILY"]
        bucket = "LARGE_RESIDUAL_FAMILY"
    elif linked:
        meta = buckets["CROSS_CLAIM_DEPENDENCY_GROUP"]
        bucket = "CROSS_CLAIM_DEPENDENCY_GROUP"
    elif diff <= float(buckets["OFFSET_ONLY_CYCLE"]["max_abs_difference"]):
        meta = buckets["OFFSET_ONLY_CYCLE"]
        bucket = "OFFSET_ONLY_CYCLE"
    elif member_count >= int(buckets["DUPLICATE_OFFSET_LOOP_CANDIDATE"]["min_group_member_count"]):
        meta = buckets["DUPLICATE_OFFSET_LOOP_CANDIDATE"]
        bucket = "DUPLICATE_OFFSET_LOOP_CANDIDATE"
    else:
        meta = buckets["STANDARD_LARGE_OFFSET"]
        bucket = "STANDARD_LARGE_OFFSET"

    future_replay = "Y" if bucket in rules["future_replay_eligible_categories"] else "N"
    return bucket, meta, future_replay, member_count


def run_engine(surrender_queue, enhanced_groups, balancing_patterns, rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    audit_ts = utc_now()
    rollback_id = snapshot_id(rules["rollback_snapshot_prefix"])
    lineage = rules["rulebook_lineage"]

    group_lookup = {}
    if not enhanced_groups.empty:
        for _, g in enhanced_groups.iterrows():
            cid = strip_val(g.get("reconstructed_claim_id", ""))
            group_lookup[cid] = g.to_dict()

    source = surrender_queue.copy()
    if source.empty and not balancing_patterns.empty:
        source = balancing_patterns[balancing_patterns["failure_pattern"] == "SURRENDER_OFFSET_CYCLE"].copy()

    workbench_rows = []
    dependency_groups = {}
    for _, row in source.iterrows():
        bucket, meta, future_replay, member_count = classify_workbench(row.to_dict(), rules, group_lookup)
        cid = strip_val(row.get("reconstructed_claim_id", ""))
        esg = strip_val(row.get("enhanced_settlement_group_id", "")) or strip_val(group_lookup.get(cid, {}).get("enhanced_settlement_group_id", ""))
        record = {
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "production_dbf_flag": rules["production_dbf_flag"],
            "parent_claim_id": cid,
            "reconstructed_claim_id": cid,
            "derivation_candidate_id": strip_val(row.get("derivation_candidate_id", "")),
            "enhanced_settlement_group_id": esg,
            "claim_family": "SURRENDER_CLAIM",
            "blocker_type": "SURRENDER_OFFSET_BLOCKED",
            "workbench_bucket": bucket,
            "balancing_difference_abs": parse_amount(row.get("balancing_difference_abs", 0)),
            "group_member_count": member_count,
            "governance_status": meta["governance_status"],
            "severity": meta["severity"],
            "remediability": meta["remediability"],
            "business_review_required": "Y",
            "replay_authorization_status": "NOT_AUTHORIZED",
            "future_controlled_replay_eligible": future_replay,
            "remediation_workflow": "SURRENDER_OFFSET_BUSINESS_REVIEW",
            "expected_replay_impact": "INDIRECT_ORPHAN_REDUCTION_IF_PARENT_ACCEPTED",
            "review_priority": meta["review_priority"],
            "rulebook_lineage": lineage,
        }
        workbench_rows.append(record)
        gkey = esg or cid
        dependency_groups.setdefault(gkey, []).append(record)

    workbench_df = pd.DataFrame(workbench_rows)
    if not workbench_df.empty:
        workbench_df = workbench_df.sort_values(["review_priority", "balancing_difference_abs"], ascending=[True, False])

    dep_rows = []
    for gkey, members in dependency_groups.items():
        dep_rows.append({
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "production_dbf_flag": rules["production_dbf_flag"],
            "dependency_group_key": gkey,
            "enhanced_settlement_group_id": gkey if gkey.startswith("ESG-") else "",
            "member_claim_count": len(members),
            "total_residual_abs": round(sum(m["balancing_difference_abs"] for m in members), 2),
            "cross_claim_dependency": "Y" if any(m["workbench_bucket"] == "CROSS_CLAIM_DEPENDENCY_GROUP" for m in members) else "N",
            "governance_status": "BUSINESS_REVIEW_REQUIRED",
            "severity": "HIGH" if len(members) > 1 else "MEDIUM",
            "remediability": "PARTIALLY_RECOVERABLE",
            "business_review_required": "Y",
            "rulebook_lineage": lineage,
        })
    dep_df = pd.DataFrame(dep_rows)
    if not dep_df.empty:
        dep_df = dep_df.sort_values("total_residual_abs", ascending=False)

    priority_df = workbench_df.copy()
    if not priority_df.empty:
        priority_df["review_queue_rank"] = range(1, len(priority_df) + 1)

    outputs = []
    for name, frame in [
        ("surrender_offset_business_triage_workbench.csv", workbench_df),
        ("surrender_offset_dependency_groups.csv", dep_df),
        ("surrender_offset_review_priority_queue.csv", priority_df),
    ]:
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        outputs.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_path = os.path.join(output_dir, "surrender_offset_triage_summary.txt")
    bucket_counts = workbench_df["workbench_bucket"].value_counts().to_dict() if not workbench_df.empty else {}
    bucket_lines = [f"  {k}: {v}" for k, v in bucket_counts.items()] or ["  (none)"]
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 16B Surrender Offset Business Triage Workbench ===",
            "",
            f"Rollback snapshot: {rollback_id}",
            f"Surrender offset claims classified: {len(workbench_df)}",
            f"Dependency groups: {len(dep_df)}",
            "",
            "Workbench bucket distribution:",
            *bucket_lines,
            "",
            "Business triage only. No automated balancing.",
            "production_dbf_flag=N",
        ]) + "\n")
    outputs.append(summary_path)
    return {"classified": len(workbench_df)}, outputs


def main():
    parser = argparse.ArgumentParser(description="Phase 16B surrender offset business triage workbench.")
    parser.add_argument("--surrender-queue", default=os.path.join(PHASE14, "surrender_offset_business_review_queue.csv"))
    parser.add_argument("--enhanced-groups", default=os.path.join(PHASE7B, "enhanced_settlement_groups.csv"))
    parser.add_argument("--balancing-patterns", default=os.path.join(PHASE13, "balancing_failure_pattern_analysis.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    stats, outputs = run_engine(
        load_csv(args.surrender_queue),
        load_csv(args.enhanced_groups),
        load_csv(args.balancing_patterns),
        args.rules,
        args.output,
    )
    print(f"Phase 16B complete. Classified: {stats['classified']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
