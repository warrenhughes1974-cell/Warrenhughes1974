#!/usr/bin/env python3
"""
Phase 16C — Parent-claim remediation prioritization (analysis only).

Identifies high-value parent claims whose remediation reduces orphan population.
Does NOT auto-remediate or modify app.py.
"""

import argparse
import json
import logging
import os
from datetime import datetime, timezone

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_RULES = os.path.join(ROOT, "config", "parent_claim_remediation_rules.json")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase16_business_triage_remediation")

logger = logging.getLogger("parent_claim_remediation")


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


def complexity_score(blocker_type):
    mapping = {
        "SURRENDER_OFFSET_BLOCKED": 0.9,
        "DEATH_DECOMPOSITION_BLOCKED": 0.8,
        "DERIVATION_REJECTED": 0.7,
        "LIFECYCLE_BLOCKED": 0.4,
        "UNBALANCED_PARENT": 0.6,
        "OTHER_GOVERNED_BLOCK": 0.5,
    }
    return mapping.get(blocker_type, 0.5)


def run_engine(orphan_triage, rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    audit_ts = utc_now()
    rollback_id = snapshot_id(rules["rollback_snapshot_prefix"])
    lineage = rules["rulebook_lineage"]
    weights = rules["priority_weights"]
    rem_scores = rules["remediability_scores"]
    sev_scores = rules["severity_scores"]

    if orphan_triage.empty:
        orphan_triage = pd.DataFrame()

    parent_groups = {}
    for _, row in orphan_triage.iterrows():
        pid = strip_val(row.get("parent_claim_id", row.get("reconstructed_claim_id", "")))
        if not pid:
            continue
        parent_groups.setdefault(pid, []).append(row.to_dict())

    candidate_rows = []
    impact_rows = []
    for pid, payments in parent_groups.items():
        orphan_count = len(payments)
        orphan_amount = sum(parse_amount(p.get("mamount", 0)) for p in payments)
        first = payments[0]
        blocker = strip_val(first.get("blocker_type", ""))
        remediability = strip_val(first.get("remediability", ""))
        severity = strip_val(first.get("severity", ""))
        rem_score = rem_scores.get(remediability, 0.2)
        sev_score = sev_scores.get(severity, 0.3)
        biz_complex = complexity_score(blocker)
        priority = round(
            weights["orphan_payment_count"] * min(orphan_count / 10.0, 1.0)
            + weights["orphan_payment_amount"] * min(orphan_amount / 50000.0, 1.0)
            + weights["remediability_score"] * rem_score
            + weights["blocker_severity"] * sev_score
            + weights["business_review_complexity"] * (1.0 - biz_complex),
            4,
        )
        expected_orphans_resolved = int(round(orphan_count * rem_score))
        record = {
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "production_dbf_flag": rules["production_dbf_flag"],
            "parent_claim_id": pid,
            "reconstructed_claim_id": pid,
            "derivation_candidate_id": strip_val(first.get("derivation_candidate_id", "")),
            "enhanced_settlement_group_id": strip_val(first.get("enhanced_settlement_group_id", "")),
            "claim_family": strip_val(first.get("claim_family", "")),
            "blocker_type": blocker,
            "orphan_payment_count": orphan_count,
            "orphan_payment_amount": round(orphan_amount, 2),
            "governance_status": strip_val(first.get("governance_status", "")),
            "severity": severity,
            "remediability": remediability,
            "business_review_required": strip_val(first.get("business_review_required", "")),
            "remediation_workflow": strip_val(first.get("remediation_workflow", "")),
            "replay_authorization_status": "NOT_AUTHORIZED",
            "expected_replay_impact": f"PROJECTED_ORPHANS_RESOLVED={expected_orphans_resolved}",
            "remediation_priority_score": priority,
            "rulebook_lineage": lineage,
        }
        candidate_rows.append(record)
        impact_rows.append({
            **record,
            "projected_orphans_resolved": expected_orphans_resolved,
            "projected_orphan_amount_resolved": round(orphan_amount * rem_score, 2),
            "blocker_severity_score": sev_score,
            "business_review_complexity": round(biz_complex, 2),
        })

    candidates_df = pd.DataFrame(candidate_rows)
    impact_df = pd.DataFrame(impact_rows)
    if not candidates_df.empty:
        candidates_df = candidates_df.sort_values("remediation_priority_score", ascending=False)
        threshold = candidates_df["remediation_priority_score"].quantile(rules["high_value_threshold_percentile"])
        high_value = candidates_df[candidates_df["remediation_priority_score"] >= threshold].copy()
        high_value["high_value_queue_rank"] = range(1, len(high_value) + 1)
    else:
        high_value = pd.DataFrame()

    outputs = []
    for name, frame in [
        ("parent_claim_remediation_candidates.csv", candidates_df),
        ("parent_claim_remediation_impact_analysis.csv", impact_df),
        ("high_value_remediation_queue.csv", high_value),
    ]:
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        outputs.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_path = os.path.join(output_dir, "parent_claim_remediation_summary.txt")
    total_orphans = int(candidates_df["orphan_payment_count"].sum()) if not candidates_df.empty else 0
    projected = int(impact_df["projected_orphans_resolved"].sum()) if not impact_df.empty else 0
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 16C Parent-Claim Remediation Prioritization ===",
            "",
            f"Rollback snapshot: {rollback_id}",
            f"Parent claims with orphan payments: {len(candidates_df)}",
            f"Total orphan payments attached: {total_orphans}",
            f"Projected orphans resolved if remediated: {projected}",
            f"High-value remediation queue: {len(high_value)}",
            "",
            "Prioritization only. No auto-remediation.",
            "production_dbf_flag=N",
        ]) + "\n")
    outputs.append(summary_path)
    return {"parents": len(candidates_df), "projected_resolved": projected}, outputs


def main():
    parser = argparse.ArgumentParser(description="Phase 16C parent claim remediation prioritization.")
    parser.add_argument(
        "--orphan-triage",
        default=os.path.join(DEFAULT_OUTPUT, "remaining_orphan_root_cause_triage.csv"),
    )
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    stats, outputs = run_engine(load_csv(args.orphan_triage), args.rules, args.output)
    print(f"Phase 16C complete. Parents: {stats['parents']}, projected resolved: {stats['projected_resolved']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
