#!/usr/bin/env python3
"""
Phase 14B — Authorized lifecycle balancing replay analysis (no forced balancing).

Authorizes replay for LIFECYCLE_EXCLUSION_GAP claims and projects replay outcomes.
Does NOT modify stable Phase 6 balancing engines or app.py.
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
DEFAULT_RULES = os.path.join(ROOT, "config", "lifecycle_balancing_replay_rules.json")
PHASE6 = os.path.join(ROOT, "phase6_family_balancing_intelligence")
PHASE13 = os.path.join(ROOT, "phase13_controlled_enterprise_integration")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase14_controlled_rule_refinement")

logger = logging.getLogger("balancing_authorized_rerun")


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


def project_replay_outcome(row, rules):
    tol = float(rules["replay_authorization"]["projected_balance_tolerance"])
    diff = abs(parse_amount(row.get("balancing_difference_abs", row.get("revised_balancing_difference", 0))))
    lifecycle_excl = abs(parse_amount(row.get("lifecycle_only_excluded", 0)))
    projected_diff = round(max(0.0, diff - lifecycle_excl), 2)

    if projected_diff <= tol:
        return "PROJECTED_BALANCED", projected_diff, "Lifecycle exclusion replay aligns residual to tolerance"
    if projected_diff <= 100.0:
        return "PROJECTED_MINOR_VARIANCE", projected_diff, "Replay may reduce to minor variance; business review advised"
    return "PROJECTED_STILL_UNBALANCED", projected_diff, "Large residual remains after lifecycle replay projection; no forced correction"


def run_engine(balancing_patterns, revised_fin, rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    audit_ts = utc_now()
    rollback_id = snapshot_id(rules["rollback_snapshot_prefix"])

    pattern = rules["authorized_failure_pattern"]
    auth_pop = balancing_patterns[balancing_patterns["failure_pattern"] == pattern].copy()
    if auth_pop.empty:
        logger.warning("No claims found for pattern %s", pattern)

    merged = auth_pop.merge(revised_fin, on="reconstructed_claim_id", how="left", suffixes=("", "_rev"))
    if "lifecycle_only_excluded" not in merged.columns and "lifecycle_only_amount_excluded" in merged.columns:
        merged["lifecycle_only_excluded"] = merged["lifecycle_only_amount_excluded"]

    auth_rows = []
    replay_rows = []
    audit_rows = []

    for _, row in merged.iterrows():
        projected_status, projected_diff, rationale = project_replay_outcome(row.to_dict(), rules)
        auth_record = {
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "reconstructed_claim_id": strip_val(row.get("reconstructed_claim_id", "")),
            "derivation_candidate_id": strip_val(row.get("derivation_candidate_id", "")),
            "enhanced_settlement_group_id": strip_val(row.get("enhanced_settlement_group_id", "")),
            "claim_family": strip_val(row.get("claim_family", "")),
            "failure_pattern": pattern,
            "revised_balancing_difference": strip_val(row.get("revised_balancing_difference", "")),
            "lifecycle_only_excluded": parse_amount(row.get("lifecycle_only_excluded", 0)),
            "replay_authorization_status": "AUTHORIZED",
            "governance_status": rules["governance_status_default"],
            "severity": rules["severity_default"],
            "remediability": rules["remediability_default"],
            "recovery_rationale": "Authorized lifecycle exclusion replay; no forced balancing",
            "lineage_source": "phase13b_balancing_remediation|phase14b_authorized_replay",
            "production_dbf_flag": "N",
        }
        auth_rows.append(auth_record)
        replay_rows.append({
            **auth_record,
            "projected_balancing_status": projected_status,
            "projected_balancing_difference": projected_diff,
            "projection_rationale": rationale,
            "residual_preserved": "Y" if projected_diff > float(rules["replay_authorization"]["projected_balance_tolerance"]) else "N",
        })
        audit_rows.append({
            **auth_record,
            "audit_event": "REPLAY_AUTHORIZATION",
            "projected_outcome": projected_status,
            "deterministic_replay_safe": "Y",
        })

    auth_df = pd.DataFrame(auth_rows)
    replay_df = pd.DataFrame(replay_rows)
    audit_df = pd.DataFrame(audit_rows)

    stats = {
        "authorized": len(auth_df),
        "projected_balanced": len(replay_df[replay_df["projected_balancing_status"] == "PROJECTED_BALANCED"]) if not replay_df.empty else 0,
        "projected_still_unbalanced": len(replay_df[replay_df["projected_balancing_status"] == "PROJECTED_STILL_UNBALANCED"]) if not replay_df.empty else 0,
    }

    rules_out = os.path.join(output_dir, "lifecycle_balancing_replay_rules.json")
    shutil.copy2(rules_path, rules_out)
    outputs = [rules_out]

    for name, frame in [
        ("lifecycle_replay_authorization_population.csv", auth_df),
        ("lifecycle_balancing_replay_results.csv", replay_df),
        ("balancing_replay_governance_audit.csv", audit_df),
    ]:
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        outputs.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_path = os.path.join(output_dir, "balancing_authorized_rerun_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 14B Balancing Authorized Rerun Summary ===",
            "",
            f"Rollback snapshot: {rollback_id}",
            f"Authorized replay population: {stats['authorized']}",
            f"Projected BALANCED after replay: {stats['projected_balanced']}",
            f"Projected still UNBALANCED: {stats['projected_still_unbalanced']}",
            "",
            "No forced balancing applied. Phase 6 engine NOT modified.",
            "production_dbf_flag=N",
            "",
            "Output files:",
            *[f"  - {p}" for p in outputs],
            f"  - {summary_path}",
        ]) + "\n")
    outputs.append(summary_path)
    return stats, outputs


def main():
    parser = argparse.ArgumentParser(description="Phase 14B authorized balancing rerun engine.")
    parser.add_argument("--balancing-patterns", default=os.path.join(PHASE13, "balancing_failure_pattern_analysis.csv"))
    parser.add_argument("--revised-financials", default=os.path.join(PHASE6, "revised_claim_financials.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    stats, outputs = run_engine(
        load_csv(args.balancing_patterns),
        load_csv(args.revised_financials) if os.path.isfile(args.revised_financials) else pd.DataFrame(),
        args.rules, args.output,
    )
    print(f"Phase 14B complete. Authorized: {stats['authorized']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
