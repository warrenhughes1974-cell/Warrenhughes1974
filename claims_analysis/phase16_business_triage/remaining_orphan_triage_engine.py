#!/usr/bin/env python3
"""
Phase 16A — Remaining orphan root-cause triage (analysis only).

Classifies 374 post-Phase-15 orphan payments by parent blocker.
Does NOT auto-remediate, modify app.py, or generate production DBFs.
"""

import argparse
import json
import logging
import os
from datetime import datetime, timezone

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_RULES = os.path.join(ROOT, "config", "remaining_orphan_triage_rules.json")
PHASE15 = os.path.join(ROOT, "phase15_qa_signoff_replay_execution")
PHASE14 = os.path.join(ROOT, "phase14_controlled_rule_refinement")
PHASE13 = os.path.join(ROOT, "phase13_controlled_enterprise_integration")
PHASE10B = os.path.join(ROOT, "phase10b_quikclms_derivation_design")
PHASE7C = os.path.join(ROOT, "phase7c_death_claim_decomposition")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase16_business_triage_remediation")

logger = logging.getLogger("remaining_orphan_triage")

REMEDIABILITY_SCORE = {"RECOVERABLE": 3, "PARTIALLY_RECOVERABLE": 2, "NON_RECOVERABLE": 1}
SEVERITY_SCORE = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}


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


def build_lookup(df, key_col, value_cols):
    lookup = {}
    if df.empty or key_col not in df.columns:
        return lookup
    for _, row in df.iterrows():
        key = strip_val(row.get(key_col, ""))
        if not key:
            continue
        lookup[key] = {c: strip_val(row.get(c, "")) for c in value_cols}
    return lookup


def classify_parent_blocker(parent_id, surrender_ids, balancing, lifecycle, death, derivation, rules):
    blockers = rules["parent_blocker_types"]
    if parent_id in surrender_ids:
        btype = "SURRENDER_OFFSET_BLOCKED"
    elif parent_id in death and strip_val(death[parent_id].get("claim_family", "")) == "DEATH_CLAIM":
        decomp = strip_val(death[parent_id].get("decomposition_status", ""))
        chain = strip_val(death[parent_id].get("chain_status", ""))
        if decomp not in ("COMPLETE", "BALANCED") or chain in ("PARTIAL_CHAIN", "MULTI_PAYOUT_CHAIN"):
            btype = "DEATH_DECOMPOSITION_BLOCKED"
        elif parent_id in balancing and strip_val(balancing[parent_id].get("failure_pattern", "")) == "LIFECYCLE_EXCLUSION_GAP":
            btype = "LIFECYCLE_BLOCKED"
        elif parent_id in derivation and strip_val(derivation[parent_id].get("derivation_status", "")) == "NEEDS_MANUAL_REVIEW":
            btype = "DERIVATION_REJECTED"
        else:
            btype = "UNBALANCED_PARENT"
    elif parent_id in lifecycle:
        proj = strip_val(lifecycle[parent_id].get("projected_balancing_status", ""))
        if "UNBALANCED" in proj.upper():
            btype = "LIFECYCLE_BLOCKED"
        else:
            btype = "UNBALANCED_PARENT"
    elif parent_id in balancing:
        fp = strip_val(balancing[parent_id].get("failure_pattern", ""))
        if fp == "SURRENDER_OFFSET_CYCLE":
            btype = "SURRENDER_OFFSET_BLOCKED"
        elif fp == "LIFECYCLE_EXCLUSION_GAP":
            btype = "LIFECYCLE_BLOCKED"
        else:
            btype = "UNBALANCED_PARENT"
    elif parent_id in derivation:
        if strip_val(derivation[parent_id].get("future_rulebook_ready", "")) == "N":
            btype = "DERIVATION_REJECTED"
        else:
            btype = "UNBALANCED_PARENT"
    else:
        btype = "OTHER_GOVERNED_BLOCK"

    meta = blockers[btype]
    return btype, meta


def priority_score(amount, meta, rules):
    weights = rules["priority_weights"]
    sev = SEVERITY_SCORE.get(meta["severity"], 1) / 3.0
    rem = REMEDIABILITY_SCORE.get(meta["remediability"], 1) / 3.0
    amt = min(parse_amount(amount) / 10000.0, 1.0)
    return round(
        weights["payment_amount"] * amt
        + weights["blocker_severity"] * sev
        + weights["remediability"] * rem,
        4,
    )


def run_engine(orphans, surrender_queue, balancing, lifecycle, death, derivation, rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    audit_ts = utc_now()
    rollback_id = snapshot_id(rules["rollback_snapshot_prefix"])
    lineage = rules["rulebook_lineage"]

    remaining = orphans[orphans["is_orphan"] == "Y"].copy() if not orphans.empty else pd.DataFrame()
    surrender_ids = set()
    if not surrender_queue.empty and "reconstructed_claim_id" in surrender_queue.columns:
        surrender_ids = set(surrender_queue["reconstructed_claim_id"].map(strip_val))

    bal_lookup = build_lookup(
        balancing,
        "reconstructed_claim_id",
        ["failure_pattern", "root_cause", "claim_family", "revised_balancing_difference", "enhanced_settlement_group_id"],
    )
    life_lookup = build_lookup(
        lifecycle,
        "reconstructed_claim_id",
        ["projected_balancing_status", "projected_balancing_difference", "claim_family", "enhanced_settlement_group_id"],
    )
    death_lookup = build_lookup(
        death,
        "reconstructed_claim_id",
        ["decomposition_status", "chain_status", "claim_family", "enhanced_settlement_group_id"],
    )
    deriv_lookup = build_lookup(
        derivation,
        "reconstructed_claim_id",
        ["derivation_candidate_id", "claim_family", "derivation_status", "future_rulebook_ready", "mbalancingstatus", "enhanced_settlement_group_id"],
    )

    triage_rows = []
    blocker_rows = []
    for _, row in remaining.iterrows():
        parent_id = strip_val(row.get("reconstructed_claim_id", ""))
        blocker_type, meta = classify_parent_blocker(
            parent_id, surrender_ids, bal_lookup, life_lookup, death_lookup, deriv_lookup, rules,
        )
        deriv = deriv_lookup.get(parent_id, {})
        esg = strip_val(row.get("enhanced_settlement_group_id", "")) or strip_val(deriv.get("enhanced_settlement_group_id", ""))
        claim_family = strip_val(deriv.get("claim_family", "")) or strip_val(bal_lookup.get(parent_id, {}).get("claim_family", ""))
        prio = priority_score(row.get("mamount", 0), meta, rules)
        base = {
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "production_dbf_flag": rules["production_dbf_flag"],
            "parent_claim_id": parent_id,
            "reconstructed_claim_id": parent_id,
            "derivation_candidate_id": strip_val(row.get("derivation_candidate_id", "")) or strip_val(deriv.get("derivation_candidate_id", "")),
            "canonical_payment_stage_id": strip_val(row.get("canonical_payment_stage_id", "")),
            "enhanced_settlement_group_id": esg,
            "claim_family": claim_family,
            "mpolicy": strip_val(row.get("mpolicy", "")),
            "mseq": strip_val(row.get("mseq", "")),
            "mamount": parse_amount(row.get("mamount", 0)),
            "orphan_issue": strip_val(row.get("orphan_issues", "")),
            "blocker_type": blocker_type,
            "governance_status": meta["governance_status"],
            "severity": meta["severity"],
            "remediability": meta["remediability"],
            "business_review_required": meta["business_review_required"],
            "remediation_workflow": meta["remediation_workflow"],
            "replay_authorization_status": "NOT_AUTHORIZED",
            "expected_replay_impact": "ORPHAN_RESOLUTION_IF_PARENT_REMEDIATED",
            "rulebook_lineage": lineage,
        }
        triage_rows.append({**base, "priority_score": prio, "is_orphan": "Y"})
        blocker_rows.append({
            **base,
            "parent_blocker_detail": f"{blocker_type}|orphan={strip_val(row.get('orphan_issues', ''))}",
            "parent_balancing_status": strip_val(deriv.get("mbalancingstatus", "")),
            "parent_derivation_status": strip_val(deriv.get("derivation_status", "")),
        })

    triage_df = pd.DataFrame(triage_rows)
    blocker_df = pd.DataFrame(blocker_rows)
    if not triage_df.empty:
        triage_df = triage_df.sort_values("priority_score", ascending=False)
        queue_df = triage_df.copy()
        queue_df["review_queue_rank"] = range(1, len(queue_df) + 1)
    else:
        queue_df = pd.DataFrame()

    outputs = []
    for name, frame in [
        ("remaining_orphan_root_cause_triage.csv", triage_df),
        ("orphan_parent_blocker_analysis.csv", blocker_df),
        ("orphan_remediation_priority_queue.csv", queue_df),
    ]:
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        outputs.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_path = os.path.join(output_dir, "remaining_orphan_triage_summary.txt")
    blocker_counts = triage_df["blocker_type"].value_counts().to_dict() if not triage_df.empty else {}
    blocker_lines = [f"  {k}: {v}" for k, v in blocker_counts.items()] or ["  (none)"]
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 16A Remaining Orphan Root-Cause Triage ===",
            "",
            f"Rollback snapshot: {rollback_id}",
            f"Remaining orphan payments triaged: {len(triage_df)}",
            "",
            "Parent blocker distribution:",
            *blocker_lines,
            "",
            "Analysis only. No auto-remediation.",
            "production_dbf_flag=N",
            "app.py NOT modified",
        ]) + "\n")
    outputs.append(summary_path)
    return {"triaged": len(triage_df)}, outputs


def main():
    parser = argparse.ArgumentParser(description="Phase 16A remaining orphan triage engine.")
    parser.add_argument("--orphans", default=os.path.join(PHASE15, "phase15_replay_orphan_analysis.csv"))
    parser.add_argument("--surrender-queue", default=os.path.join(PHASE14, "surrender_offset_business_review_queue.csv"))
    parser.add_argument("--balancing", default=os.path.join(PHASE13, "balancing_failure_pattern_analysis.csv"))
    parser.add_argument("--lifecycle", default=os.path.join(PHASE14, "lifecycle_balancing_replay_results.csv"))
    parser.add_argument("--death", default=os.path.join(PHASE7C, "death_claim_decomposition_summary.csv"))
    parser.add_argument("--derivation", default=os.path.join(PHASE10B, "quikclms_derivation_candidates.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    stats, outputs = run_engine(
        load_csv(args.orphans),
        load_csv(args.surrender_queue),
        load_csv(args.balancing),
        load_csv(args.lifecycle),
        load_csv(args.death),
        load_csv(args.derivation),
        args.rules,
        args.output,
    )
    print(f"Phase 16A complete. Orphans triaged: {stats['triaged']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
