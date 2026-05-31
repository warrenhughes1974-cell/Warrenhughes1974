#!/usr/bin/env python3
"""
Phase 15B — Authorized Phase 11 replay execution engine (governance overlay wrapper).

Executes first controlled prototype regeneration without modifying stable Phase 11 engine.
Does NOT deploy production DBFs or modify app.py.
"""

import argparse
import json
import logging
import os
import shutil
import sys
from datetime import datetime, timezone

import pandas as pd

_PHASE11_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "phase11_prototype_generation")
)
if _PHASE11_DIR not in sys.path:
    sys.path.insert(0, _PHASE11_DIR)

from quikplan_prototype_dbf_generator import (
    analyze_orphans,
    build_claimnum_crosswalk,
    confidence_rank,
    gate_candidates,
    load_csv,
    load_json,
    map_row_to_dbf_values,
    normalize_merged_columns,
    parse_amount,
    passes_gating,
    run_reconciliation,
    strip_val,
    validate_required_fields,
    write_dbf,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_REPLAY_RULES = os.path.join(ROOT, "config", "replay_execution_rules.json")
DEFAULT_PROTO_RULES = os.path.join(ROOT, "config", "prototype_dbf_generation_rules.json")
PHASE10A = os.path.join(ROOT, "phase10a_quikclmp_derivation_design")
PHASE10B = os.path.join(ROOT, "phase10b_quikclms_derivation_design")
PHASE11 = os.path.join(ROOT, "phase11_prototype_dbf_generation")
PHASE14 = os.path.join(ROOT, "phase14_controlled_rule_refinement")
PHASE15A = os.path.join(ROOT, "phase15_qa_signoff_replay_execution")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase15_qa_signoff_replay_execution")

logger = logging.getLogger("authorized_phase11_rerun")


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def snapshot_id(prefix):
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def merge_gate_records(baseline_df, overlay_records, id_field):
    frames = []
    if not baseline_df.empty:
        b = baseline_df.copy()
        if "replay_source" not in b.columns:
            b["replay_source"] = "BASELINE"
        if "replay_authorization_status" not in b.columns:
            b["replay_authorization_status"] = "BASELINE_RULEBOOK_READY"
        frames.append(b)
    if overlay_records:
        frames.append(pd.DataFrame(overlay_records))
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    return combined.drop_duplicates(subset=[id_field], keep="first")


def run_engine(
    clmp_candidates, clmp_validation, clms_candidates, clms_validation,
    trustee_signoff, lifecycle_replay, replay_rules_path, proto_rules_path, output_dir,
):
    os.makedirs(output_dir, exist_ok=True)
    replay_rules = load_json(replay_rules_path)
    proto_rules = load_json(proto_rules_path)
    audit_ts = utc_now()
    rollback_id = snapshot_id(replay_rules["rollback_snapshot_prefix"])

    baseline_claims, rejected_claims = gate_candidates(
        clms_candidates, clms_validation, "reconstructed_claim_id", proto_rules,
    )
    baseline_payments, rejected_payments = gate_candidates(
        clmp_candidates, clmp_validation, "canonical_payment_stage_id", proto_rules,
    )

    lifecycle_ids = set()
    if not lifecycle_replay.empty:
        allowed = replay_rules["claim_gating_overlay"]["lifecycle_projected_statuses"]
        lifecycle_ids = set(
            lifecycle_replay[lifecycle_replay["projected_balancing_status"].isin(allowed)]["reconstructed_claim_id"]
        )

    clms_merged = clms_candidates.merge(clms_validation, on="reconstructed_claim_id", suffixes=("_cand", "_val"))
    clms_merged = normalize_merged_columns(clms_merged)
    lifecycle_overlay = []
    for _, row in clms_merged.iterrows():
        cid = strip_val(row.get("reconstructed_claim_id", ""))
        if cid not in lifecycle_ids:
            continue
        lifecycle_overlay.append({
            **row.to_dict(),
            "replay_source": "LIFECYCLE_REPLAY_OVERLAY",
            "replay_authorization_status": "AUTHORIZED_LIFECYCLE_REPLAY",
            "governance_status": replay_rules["claim_gating_overlay"]["lifecycle_governance_status"],
            "production_dbf_flag": "N",
        })

    signed_stage_ids = set()
    if not trustee_signoff.empty:
        req = replay_rules["payment_gating_overlay"]["require_trustee_signoff_status"]
        signed = trustee_signoff[trustee_signoff["qa_review_status"] == req]
        signed_stage_ids = set(signed["canonical_payment_stage_id"].tolist())

    clmp_merged = clmp_candidates.merge(clmp_validation, on="canonical_payment_stage_id", suffixes=("_cand", "_val"))
    clmp_merged = normalize_merged_columns(clmp_merged)
    trustee_overlay = []
    for _, row in clmp_merged.iterrows():
        stage_id = strip_val(row.get("canonical_payment_stage_id", ""))
        if stage_id not in signed_stage_ids:
            continue
        status = strip_val(row.get("derivation_status", ""))
        if status not in replay_rules["payment_gating_overlay"]["trustee_allowed_derivation_statuses"]:
            continue
        trustee_overlay.append({
            **row.to_dict(),
            "replay_source": "TRUSTEE_QA_OVERLAY",
            "replay_authorization_status": "AUTHORIZED_TRUSTEE_REPLAY",
            "governance_status": replay_rules["payment_gating_overlay"]["trustee_governance_status"],
            "production_dbf_flag": "N",
        })

    accepted_claims = merge_gate_records(baseline_claims, lifecycle_overlay, "reconstructed_claim_id")
    accepted_payments = merge_gate_records(baseline_payments, trustee_overlay, "canonical_payment_stage_id")

    clms_layout = proto_rules["quikclms_layout"]
    clmp_layout = proto_rules["quikclmp_layout"]
    clms_mapping = proto_rules["quikclms_field_mapping"]
    clmp_mapping = proto_rules["quikclmp_field_mapping"]

    crosswalk_df, claimnum_lookup = build_claimnum_crosswalk(accepted_claims, proto_rules)
    crosswalk_path = os.path.join(output_dir, "phase15_claimnum_crosswalk.csv")
    crosswalk_df.to_csv(crosswalk_path, index=False, encoding="utf-8")

    clms_results = []
    clms_dbf_rows = []
    for _, row in accepted_claims.iterrows():
        row_dict = row.to_dict() if isinstance(row, dict) else row.to_dict()
        cid = strip_val(row_dict.get("reconstructed_claim_id", ""))
        row_dict["prototype_claimnum"] = claimnum_lookup.get(cid, "")
        dbf_vals = map_row_to_dbf_values(row_dict, clms_layout, clms_mapping, proto_rules, claimnum_lookup)
        issues = validate_required_fields(dbf_vals, clms_layout, proto_rules.get("required_quikclms_fields", []))
        if issues:
            continue
        clms_dbf_rows.append(dbf_vals)
        mpaid_idx = next(i for i, f in enumerate(clms_layout) if f["field"] == "MPAID")
        clms_results.append({
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "reconstructed_claim_id": cid,
            "prototype_claimnum": row_dict["prototype_claimnum"],
            "derivation_candidate_id": strip_val(row_dict.get("derivation_candidate_id", "")),
            "replay_source": strip_val(row_dict.get("replay_source", "BASELINE")),
            "replay_authorization_status": strip_val(row_dict.get("replay_authorization_status", "BASELINE_RULEBOOK_READY")),
            "governance_status": strip_val(row_dict.get("governance_status", "AUTO_APPROVED")),
            "generation_status": "ACCEPTED",
            "production_dbf_flag": "N",
            "mpaid": dbf_vals[mpaid_idx],
        })

    clmp_results = []
    clmp_dbf_rows = []
    for _, row in accepted_payments.iterrows():
        row_dict = row.to_dict()
        cid = strip_val(row_dict.get("reconstructed_claim_id", ""))
        row_dict["prototype_claimnum"] = claimnum_lookup.get(cid, "")
        dbf_vals = map_row_to_dbf_values(row_dict, clmp_layout, clmp_mapping, proto_rules)
        issues = validate_required_fields(dbf_vals, clmp_layout, proto_rules.get("required_quikclmp_fields", []))
        if issues:
            continue
        clmp_dbf_rows.append(dbf_vals)
        mamount_idx = next(i for i, f in enumerate(clmp_layout) if f["field"] == "MAMOUNT")
        clmp_results.append({
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "reconstructed_claim_id": cid,
            "canonical_payment_stage_id": strip_val(row_dict.get("canonical_payment_stage_id", "")),
            "prototype_claimnum": row_dict["prototype_claimnum"],
            "derivation_candidate_id": strip_val(row_dict.get("derivation_candidate_id", "")),
            "replay_source": strip_val(row_dict.get("replay_source", "BASELINE")),
            "replay_authorization_status": strip_val(row_dict.get("replay_authorization_status", "BASELINE_RULEBOOK_READY")),
            "governance_status": strip_val(row_dict.get("governance_status", "AUTO_APPROVED")),
            "generation_status": "ACCEPTED",
            "production_dbf_flag": "N",
            "mamount": dbf_vals[mamount_idx],
        })

    clms_name = replay_rules["output_dbf_names"]["quikclms"]
    clmp_name = replay_rules["output_dbf_names"]["quikclmp"]
    clms_path = os.path.join(output_dir, clms_name)
    clmp_path = os.path.join(output_dir, clmp_name)
    clms_count = write_dbf(clms_path, clms_layout, clms_dbf_rows)
    clmp_count = write_dbf(clmp_path, clmp_layout, clmp_dbf_rows)
    logger.info("Wrote %s (%s rows)", clms_name, clms_count)
    logger.info("Wrote %s (%s rows)", clmp_name, clmp_count)

    recon_claim_rows = []
    for res, dbf_vals in zip(clms_results, clms_dbf_rows):
        cid = res["reconstructed_claim_id"]
        match = accepted_claims[accepted_claims["reconstructed_claim_id"] == cid]
        if match.empty:
            continue
        r = match.iloc[0].to_dict()
        r["prototype_claimnum"] = res["prototype_claimnum"]
        r["mpaid_dbf"] = res["mpaid"]
        r["mpaycount"] = r.get("mpaycount", "0")
        r["mnetamt"] = r.get("mnetamt", r.get("netdb", "0"))
        r["mresidual"] = r.get("mresidual", "0")
        r["claim_family"] = r.get("claim_family", "")
        recon_claim_rows.append(r)
    recon_claim_df = pd.DataFrame(recon_claim_rows)

    recon_pay_rows = []
    for res, dbf_vals in zip(clmp_results, clmp_dbf_rows):
        stage_id = res["canonical_payment_stage_id"]
        match = accepted_payments[accepted_payments["canonical_payment_stage_id"] == stage_id]
        if match.empty:
            continue
        r = match.iloc[0].to_dict()
        r["prototype_claimnum"] = res["prototype_claimnum"]
        r["mamount_dbf"] = res["mamount"]
        recon_pay_rows.append(r)
    recon_pay_df = pd.DataFrame(recon_pay_rows)

    recon_df = run_reconciliation(recon_claim_df, recon_pay_df, crosswalk_df, proto_rules)
    orphan_df = analyze_orphans(recon_claim_df, recon_pay_df, crosswalk_df)

    baseline_recon = load_csv(os.path.join(PHASE11, "prototype_claim_payment_reconciliation.csv"))
    baseline_orphans = load_csv(os.path.join(PHASE11, "prototype_orphan_analysis.csv"))
    baseline_orphan_count = (baseline_orphans["is_orphan"] == "Y").sum() if not baseline_orphans.empty else 0
    replay_orphan_count = (orphan_df["is_orphan"] == "Y").sum() if not orphan_df.empty else 0
    baseline_pass = (baseline_recon["reconciliation_status"] == "PASS").sum() if not baseline_recon.empty else 0
    replay_pass = (recon_df["reconciliation_status"] == "PASS").sum() if not recon_df.empty else 0

    delta_rows = [{
        "metric": "quikclms_row_count",
        "baseline_phase11": 5182,
        "phase15_replay": clms_count,
        "delta": clms_count - 5182,
        "rollback_snapshot_id": rollback_id,
        "production_dbf_flag": "N",
    }, {
        "metric": "quikclmp_row_count",
        "baseline_phase11": 1910,
        "phase15_replay": clmp_count,
        "delta": clmp_count - 1910,
        "rollback_snapshot_id": rollback_id,
        "production_dbf_flag": "N",
    }, {
        "metric": "lifecycle_overlay_claims",
        "baseline_phase11": 0,
        "phase15_replay": len(lifecycle_overlay),
        "delta": len(lifecycle_overlay),
        "rollback_snapshot_id": rollback_id,
        "production_dbf_flag": "N",
    }, {
        "metric": "trustee_overlay_payments",
        "baseline_phase11": 0,
        "phase15_replay": len(trustee_overlay),
        "delta": len(trustee_overlay),
        "rollback_snapshot_id": rollback_id,
        "production_dbf_flag": "N",
    }, {
        "metric": "orphan_count",
        "baseline_phase11": int(baseline_orphan_count),
        "phase15_replay": int(replay_orphan_count),
        "delta": int(replay_orphan_count - baseline_orphan_count),
        "rollback_snapshot_id": rollback_id,
        "production_dbf_flag": "N",
    }, {
        "metric": "reconciliation_pass_count",
        "baseline_phase11": int(baseline_pass),
        "phase15_replay": int(replay_pass),
        "delta": int(replay_pass - baseline_pass),
        "rollback_snapshot_id": rollback_id,
        "production_dbf_flag": "N",
    }]
    delta_df = pd.DataFrame(delta_rows)

    clms_df = pd.DataFrame(clms_results)
    clmp_df = pd.DataFrame(clmp_results)

    rules_out = os.path.join(output_dir, "replay_execution_rules.json")
    shutil.copy2(replay_rules_path, rules_out)
    outputs = [rules_out, clms_path, clmp_path, crosswalk_path]

    for name, frame in [
        ("phase15_replay_quikclms_results.csv", clms_df),
        ("phase15_replay_quikclmp_results.csv", clmp_df),
        ("phase15_reconciliation_delta_analysis.csv", delta_df),
    ]:
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        outputs.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    recon_path = os.path.join(output_dir, "phase15_replay_reconciliation.csv")
    recon_df.to_csv(recon_path, index=False, encoding="utf-8")
    orphan_path = os.path.join(output_dir, "phase15_replay_orphan_analysis.csv")
    orphan_df.to_csv(orphan_path, index=False, encoding="utf-8")
    outputs.extend([recon_path, orphan_path])

    gov_summary = os.path.join(output_dir, "phase15_governance_delta_summary.txt")
    replay_summary = os.path.join(output_dir, "phase15_authorized_replay_summary.txt")
    summary_text = "\n".join([
        "=== Phase 15B Authorized Phase 11 Replay Summary ===",
        "",
        f"Rollback snapshot: {rollback_id}",
        f"QUIKCLMS replay rows: {clms_count} (baseline 5182, +{clms_count - 5182})",
        f"QUIKCLMP replay rows: {clmp_count} (baseline 1910, +{clmp_count - 1910})",
        f"Lifecycle overlay claims authorized: {len(lifecycle_overlay)}",
        f"Trustee overlay payments signed-off: {len(trustee_overlay)}",
        f"Orphans: {replay_orphan_count} (baseline {baseline_orphan_count}, delta {replay_orphan_count - baseline_orphan_count})",
        f"Reconciliation PASS: {replay_pass} (baseline {baseline_pass})",
        "",
        "Stable Phase 11 engine NOT modified — overlay wrapper only",
        "production_dbf_flag=N",
    ])
    with open(gov_summary, "w", encoding="utf-8") as fh:
        fh.write(summary_text + "\n")
    with open(replay_summary, "w", encoding="utf-8") as fh:
        fh.write(summary_text + "\n")
    outputs.extend([gov_summary, replay_summary])

    stats = {
        "clms_count": clms_count,
        "clmp_count": clmp_count,
        "lifecycle_overlay": len(lifecycle_overlay),
        "trustee_overlay": len(trustee_overlay),
        "orphan_delta": int(replay_orphan_count - baseline_orphan_count),
        "rollback_id": rollback_id,
    }
    return stats, outputs


def main():
    parser = argparse.ArgumentParser(description="Phase 15B authorized Phase 11 replay engine.")
    parser.add_argument("--clmp-candidates", default=os.path.join(PHASE10A, "quikclmp_derivation_candidates.csv"))
    parser.add_argument("--clmp-validation", default=os.path.join(PHASE10A, "quikclmp_derivation_validation.csv"))
    parser.add_argument("--clms-candidates", default=os.path.join(PHASE10B, "quikclms_derivation_candidates.csv"))
    parser.add_argument("--clms-validation", default=os.path.join(PHASE10B, "quikclms_derivation_validation.csv"))
    parser.add_argument("--trustee-signoff", default=os.path.join(PHASE15A, "trustee_qa_signoff_results.csv"))
    parser.add_argument("--lifecycle-replay", default=os.path.join(PHASE14, "lifecycle_balancing_replay_results.csv"))
    parser.add_argument("--replay-rules", default=DEFAULT_REPLAY_RULES)
    parser.add_argument("--proto-rules", default=DEFAULT_PROTO_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")

    stats, outputs = run_engine(
        load_csv(args.clmp_candidates),
        load_csv(args.clmp_validation),
        load_csv(args.clms_candidates),
        load_csv(args.clms_validation),
        load_csv(args.trustee_signoff) if os.path.isfile(args.trustee_signoff) else pd.DataFrame(),
        load_csv(args.lifecycle_replay) if os.path.isfile(args.lifecycle_replay) else pd.DataFrame(),
        args.replay_rules, args.proto_rules, args.output,
    )
    print(f"Phase 15B complete. QUIKCLMS={stats['clms_count']} QUIKCLMP={stats['clmp_count']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
