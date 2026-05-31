#!/usr/bin/env python3
"""
Phase 14A — Trustee authorized gate refinement & QA-reviewed rerun analysis.

Applies isolated trustee gating overlay without modifying Phase 10A/11 engines.
Does NOT auto-approve trustee payments or modify app.py.
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
DEFAULT_RULES = os.path.join(ROOT, "config", "trustee_gate_refinement_rules.json")
PHASE10A = os.path.join(ROOT, "phase10a_quikclmp_derivation_design")
PHASE11 = os.path.join(ROOT, "phase11_prototype_dbf_generation")
PHASE13 = os.path.join(ROOT, "phase13_controlled_enterprise_integration")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase14_controlled_rule_refinement")

logger = logging.getLogger("trustee_authorized_rerun")


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


def confidence_rank(level):
    order = {"HIGH_CONFIDENCE": 4, "MODERATE_CONFIDENCE": 3, "INFERRED": 2, "LOW_CONFIDENCE": 1}
    return order.get(strip_val(level).upper(), 0)


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def snapshot_id(prefix):
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def baseline_gate(row):
    status = strip_val(row.get("derivation_status", ""))
    return status == "RULEBOOK_READY", f"derivation_status={status}"


def refined_trustee_gate(row, rules):
    cfg = rules["refined_payment_gating"]
    flags = rules["governance_flags"]
    status = strip_val(row.get("derivation_status", ""))
    validation = strip_val(row.get("validation_result", ""))
    rulebook = strip_val(row.get("rulebook_ready", ""))
    confidence = strip_val(row.get("derivation_confidence", ""))

    if status not in cfg["trustee_allowed_derivation_statuses"]:
        return False, f"derivation_status={status}", "BASELINE_REJECT"
    if validation != cfg["require_validation_result"]:
        return False, f"validation_result={validation}", "VALIDATION_REJECT"
    if rulebook != cfg["require_rulebook_ready"]:
        return False, f"rulebook_ready={rulebook}", "RULEBOOK_REJECT"
    if confidence_rank(confidence) < confidence_rank(cfg["minimum_confidence"]):
        return False, f"confidence={confidence}", "CONFIDENCE_REJECT"
    if cfg.get("require_parent_in_prototype_quikclms") and strip_val(row.get("parent_in_prototype_quikclms", "")) != "Y":
        return False, "parent_not_in_prototype", "PARENT_REJECT"
    if cfg.get("require_mpayname_present") and strip_val(row.get("mpayname_present", "")) != "Y":
        return False, "missing_payname", "PAYNAME_REJECT"
    if cfg.get("require_mtrustee") and strip_val(row.get("mtrustee", "")).upper() not in {"Y", "TRUE", "1"}:
        return False, "trustee_indicator_missing", "TRUSTEE_REJECT"
    return True, "trustee_qa_gate_pass", rules.get("governance_status", "QA_REVIEW_REQUIRED")


def run_engine(trustee_candidates, clmp_candidates, clmp_validation, phase11_audit, rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    audit_ts = utc_now()
    rollback_id = snapshot_id(rules["rollback_snapshot_prefix"])

    cand_lookup = clmp_candidates.set_index("canonical_payment_stage_id").to_dict("index") if not clmp_candidates.empty else {}
    val_lookup = clmp_validation.set_index("canonical_payment_stage_id").to_dict("index") if not clmp_validation.empty else {}

    baseline_rejected = phase11_audit[
        (phase11_audit["record_type"] == "PAYMENT") & (phase11_audit["generation_status"] == "REJECTED")
    ] if not phase11_audit.empty else pd.DataFrame()

    gate_results = []
    qa_population = []
    diff_rows = []

    source = trustee_candidates if not trustee_candidates.empty else pd.DataFrame()
    for _, row in source.iterrows():
        stage_id = strip_val(row.get("canonical_payment_stage_id", ""))
        enriched = row.to_dict()
        cand = cand_lookup.get(stage_id, {})
        val = val_lookup.get(stage_id, {})
        for src in (cand, val):
            for k, v in src.items():
                if k not in enriched or not strip_val(enriched.get(k)):
                    enriched[k] = v
        enriched["derivation_status"] = enriched.get("derivation_status") or cand.get("derivation_status", "TRUSTEE_DERIVATION")

        base_ok, base_reason = baseline_gate(enriched)
        ref_ok, ref_reason, gov = refined_trustee_gate(enriched, rules)

        record = {
            "audit_timestamp": audit_ts,
            "rollback_snapshot_id": rollback_id,
            "canonical_payment_stage_id": stage_id,
            "reconstructed_claim_id": strip_val(enriched.get("reconstructed_claim_id", "")),
            "derivation_candidate_id": strip_val(enriched.get("derivation_candidate_id", "")),
            "enhanced_settlement_group_id": strip_val(enriched.get("enhanced_settlement_group_id", "")),
            "derivation_status": strip_val(enriched.get("derivation_status", "")),
            "derivation_confidence": strip_val(enriched.get("derivation_confidence", "")),
            "baseline_gate_result": "PASS" if base_ok else "REJECT",
            "baseline_gate_reason": base_reason,
            "refined_gate_result": "PASS" if ref_ok else "REJECT",
            "refined_gate_reason": ref_reason,
            "trustee_recovery_eligible": rules["governance_flags"]["trustee_recovery_eligible"] if ref_ok else "N",
            "qa_review_required": rules["governance_flags"]["qa_review_required"] if ref_ok else "Y",
            "auto_approved": "N",
            "production_authorized": "N",
            "governance_status": gov if ref_ok else "PRODUCTION_BLOCKED",
            "severity": rules["severity"],
            "remediability": rules["remediability"],
            "replay_authorization_status": "AUTHORIZED_QA_RERUN" if ref_ok else "NOT_AUTHORIZED",
            "recovery_rationale": strip_val(enriched.get("recovery_rationale", ref_reason)),
            "lineage_source": "phase13a_trustee_recovery|phase14a_gate_refinement",
            "production_dbf_flag": "N",
        }
        gate_results.append(record)
        diff_rows.append({
            **record,
            "gate_delta": "REFINED_PASS" if (not base_ok and ref_ok) else ("UNCHANGED" if base_ok == ref_ok else "STILL_REJECT"),
        })
        if ref_ok:
            qa_population.append({**record, "qa_review_population_status": "QA_REVIEW_CANDIDATE"})

    gate_df = pd.DataFrame(gate_results)
    qa_df = pd.DataFrame(qa_population)
    diff_df = pd.DataFrame(diff_rows)

    stats = {
        "analyzed": len(gate_df),
        "refined_pass": len(qa_df),
        "baseline_only_pass": len(gate_df[gate_df["baseline_gate_result"] == "PASS"]) if not gate_df.empty else 0,
        "gate_delta_pass": len(diff_df[diff_df["gate_delta"] == "REFINED_PASS"]) if not diff_df.empty else 0,
    }

    rules_out = os.path.join(output_dir, "trustee_gate_refinement_rules.json")
    shutil.copy2(rules_path, rules_out)
    outputs = [rules_out]

    for name, frame in [
        ("trustee_refined_gate_results.csv", gate_df),
        ("trustee_qa_review_population.csv", qa_df),
        ("trustee_rulebook_gate_diff_analysis.csv", diff_df),
    ]:
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        outputs.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_path = os.path.join(output_dir, "trustee_authorized_rerun_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "=== Phase 14A Trustee Authorized Rerun Summary ===",
            "",
            f"Rollback snapshot: {rollback_id}",
            f"Trustee payments analyzed: {stats['analyzed']}",
            f"Refined gate PASS (QA subset): {stats['refined_pass']}",
            f"Gate delta (baseline reject -> refined pass): {stats['gate_delta_pass']}",
            "",
            "Controls: trustee_recovery_eligible=Y, qa_review_required=Y, auto_approved=N",
            "Stable Phase 10A/11 engines NOT modified",
            "production_dbf_flag=N",
            "",
            "Output files:",
            *[f"  - {p}" for p in outputs],
            f"  - {summary_path}",
        ]) + "\n")
    outputs.append(summary_path)
    return stats, outputs


def main():
    parser = argparse.ArgumentParser(description="Phase 14A trustee authorized rerun engine.")
    parser.add_argument("--trustee-candidates", default=os.path.join(PHASE13, "trustee_recovery_candidate_population.csv"))
    parser.add_argument("--clmp-candidates", default=os.path.join(PHASE10A, "quikclmp_derivation_candidates.csv"))
    parser.add_argument("--clmp-validation", default=os.path.join(PHASE10A, "quikclmp_derivation_validation.csv"))
    parser.add_argument("--phase11-audit", default=os.path.join(PHASE11, "prototype_dbf_generation_audit.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    if not os.path.isfile(args.rules):
        logger.error("Rules not found: %s", args.rules)
        return 1

    stats, outputs = run_engine(
        load_csv(args.trustee_candidates) if os.path.isfile(args.trustee_candidates) else pd.DataFrame(),
        load_csv(args.clmp_candidates) if os.path.isfile(args.clmp_candidates) else pd.DataFrame(),
        load_csv(args.clmp_validation) if os.path.isfile(args.clmp_validation) else pd.DataFrame(),
        load_csv(args.phase11_audit) if os.path.isfile(args.phase11_audit) else pd.DataFrame(),
        args.rules, args.output,
    )
    print(f"Phase 14A complete. QA subset: {stats['refined_pass']}/{stats['analyzed']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
