#!/usr/bin/env python3
"""
Phase 13A — Trustee payment recovery governance engine (analysis only).

Analyzes TRUSTEE_ROUTING rejected payments for controlled recovery classification.
Does NOT auto-approve trustee payments or modify stable derivation engines / app.py.
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
DEFAULT_RULES = os.path.join(ROOT, "config", "trustee_payment_recovery_rules.json")
PHASE8 = os.path.join(ROOT, "phase8_payee_distribution_intelligence")
PHASE9 = os.path.join(ROOT, "phase9_quikclmp_canonical_staging")
PHASE10A = os.path.join(ROOT, "phase10a_quikclmp_derivation_design")
PHASE11 = os.path.join(ROOT, "phase11_prototype_dbf_generation")
PHASE12 = os.path.join(ROOT, "phase12_qa_uat_hardening")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase13_controlled_enterprise_integration")

logger = logging.getLogger("trustee_recovery")


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


def classify_trustee_payment(row, rules, accepted_claim_ids):
    scenarios = rules["recovery_scenarios"]
    confidence = strip_val(row.get("derivation_confidence", ""))
    validation = strip_val(row.get("validation_result", ""))
    rulebook = strip_val(row.get("rulebook_ready", ""))
    payname = strip_val(row.get("mpayname", ""))
    trustee = strip_val(row.get("mtrustee", "")).upper()
    cid = strip_val(row.get("reconstructed_claim_id", ""))

    if cid not in accepted_claim_ids:
        meta = scenarios["TRUSTEE_PARENT_CLAIM_BLOCKED"]
        return {
            "recovery_scenario": "TRUSTEE_PARENT_CLAIM_BLOCKED",
            "primary_blocker": meta["primary_blocker"],
            "governance_status": meta["governance_status"],
            "remediability": meta["remediability"],
            "severity": meta["severity"],
            "recovery_rationale": "Parent claim not in prototype QUIKCLMS (UNBALANCED/rejected)",
        }

    if not payname:
        meta = scenarios["TRUSTEE_PAYEE_DATA_GAP"]
        return {
            "recovery_scenario": "TRUSTEE_PAYEE_DATA_GAP",
            "primary_blocker": meta["primary_blocker"],
            "governance_status": meta["governance_status"],
            "remediability": meta["remediability"],
            "severity": meta["severity"],
            "recovery_rationale": "Missing MPAYNAME on trustee-routed payment",
        }

    if confidence_rank(confidence) < confidence_rank("MODERATE_CONFIDENCE"):
        meta = scenarios["TRUSTEE_CONFIDENCE_GAP"]
        return {
            "recovery_scenario": "TRUSTEE_CONFIDENCE_GAP",
            "primary_blocker": meta["primary_blocker"],
            "governance_status": meta["governance_status"],
            "remediability": meta["remediability"],
            "severity": meta["severity"],
            "recovery_rationale": f"Confidence {confidence} below MODERATE_CONFIDENCE floor",
        }

    if validation == "PASS" and rulebook == "Y" and trustee in {"Y", "TRUE", "1"}:
        meta = scenarios["TRUSTEE_RULEBOOK_READY_ELIGIBLE"]
        return {
            "recovery_scenario": "TRUSTEE_RULEBOOK_READY_ELIGIBLE",
            "primary_blocker": meta["primary_blocker"],
            "governance_status": meta["governance_status"],
            "remediability": meta["remediability"],
            "severity": meta["severity"],
            "recovery_rationale": "Validation PASS + rulebook_ready=Y blocked only by TRUSTEE_DERIVATION status gating",
        }

    meta = scenarios["TRUSTEE_PAYEE_DATA_GAP"]
    return {
        "recovery_scenario": "TRUSTEE_PAYEE_DATA_GAP",
        "primary_blocker": "VALIDATION_GAP",
        "governance_status": meta["governance_status"],
        "remediability": meta["remediability"],
        "severity": meta["severity"],
        "recovery_rationale": f"validation={validation}; rulebook_ready={rulebook}; trustee={trustee}",
    }


def run_engine(rejected_payments, clmp_candidates, clmp_validation, payee_stage, crosswalk, rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    audit_ts = utc_now()

    trustee_rej = rejected_payments[rejected_payments["root_cause"] == "TRUSTEE_ROUTING"].copy()
    accepted_claims = set(crosswalk["reconstructed_claim_id"].tolist()) if not crosswalk.empty else set()

    cand_lookup = clmp_candidates.set_index("canonical_payment_stage_id").to_dict("index") if not clmp_candidates.empty else {}
    val_lookup = clmp_validation.set_index("canonical_payment_stage_id").to_dict("index") if not clmp_validation.empty else {}
    payee_lookup = payee_stage.set_index("canonical_payment_stage_id").to_dict("index") if not payee_stage.empty else {}

    analysis_rows = []
    candidate_rows = []

    for _, rej in trustee_rej.iterrows():
        stage_id = strip_val(rej.get("canonical_payment_stage_id", ""))
        cand = cand_lookup.get(stage_id, {})
        val = val_lookup.get(stage_id, {})
        payee = payee_lookup.get(stage_id, {})
        cid = strip_val(rej.get("reconstructed_claim_id", cand.get("reconstructed_claim_id", "")))

        enriched = rej.to_dict()
        for k, v in cand.items():
            if k not in enriched or not strip_val(enriched.get(k)):
                enriched[k] = v
        enriched.update({
            "validation_result": val.get("validation_result", ""),
            "rulebook_ready": val.get("rulebook_ready", ""),
            "validation_issues": val.get("validation_issues", ""),
            "mpayname": enriched.get("mpayname") or cand.get("mpayname", ""),
            "mtrustee": enriched.get("mtrustee") or cand.get("mtrustee", payee.get("trustee_indicator", "")),
            "mrelation": enriched.get("mrelation") or cand.get("mrelation", payee.get("relationship_code", "")),
            "mamount": enriched.get("mamount") or cand.get("mamount", ""),
            "derivation_status_source": cand.get("derivation_status", "TRUSTEE_DERIVATION"),
            "derivation_confidence": enriched.get("derivation_confidence") or cand.get("derivation_confidence", val.get("derivation_confidence", "")),
        })
        classification = classify_trustee_payment(enriched, rules, accepted_claims)

        record = {
            "audit_timestamp": audit_ts,
            "canonical_payment_stage_id": stage_id,
            "reconstructed_claim_id": cid,
            "derivation_candidate_id": strip_val(rej.get("derivation_candidate_id", "")),
            "enhanced_settlement_group_id": strip_val(cand.get("enhanced_settlement_group_id", "")),
            "derivation_status_source": enriched["derivation_status_source"],
            "derivation_confidence": strip_val(enriched.get("derivation_confidence", "")),
            "validation_result": enriched["validation_result"],
            "rulebook_ready": enriched["rulebook_ready"],
            "mtrustee": enriched["mtrustee"],
            "mrelation": enriched["mrelation"],
            "mpayname_present": "Y" if strip_val(enriched.get("mpayname", "")) else "N",
            "parent_in_prototype_quikclms": "Y" if cid in accepted_claims else "N",
            "production_dbf_flag": "N",
            **classification,
        }
        analysis_rows.append(record)

        if classification["recovery_scenario"] == "TRUSTEE_RULEBOOK_READY_ELIGIBLE":
            candidate_rows.append({
                **record,
                "recovery_candidate_status": "QA_REVIEW_CANDIDATE",
                "auto_approve": "N",
                "replay_safe": "Y",
                "lineage_source": "phase10a_quikclmp_derivation|phase13a_trustee_recovery",
            })

    analysis_df = pd.DataFrame(analysis_rows)
    candidate_df = pd.DataFrame(candidate_rows)

    recs = []
    for scenario, sub in analysis_df.groupby("recovery_scenario"):
        recs.append({
            "observed_pattern": f"{len(sub)} trustee payments classified as {scenario}",
            "root_cause": sub["primary_blocker"].mode().iloc[0] if not sub.empty else "",
            "recommended_rule_refinement": rules["rule_refinement_recommendations"].get(
                "derivation_status_gating" if scenario == "TRUSTEE_RULEBOOK_READY_ELIGIBLE" else "confidence_floor", "",
            ),
            "governance_status": sub["governance_status"].mode().iloc[0],
            "expected_recovery_impact": len(sub),
            "production_dbf_flag": "N",
        })
    rec_df = pd.DataFrame(recs)

    stats = {
        "total_trustee_payments": len(analysis_df),
        "recovery_candidates": len(candidate_df),
        "parent_blocked": len(analysis_df[analysis_df["recovery_scenario"] == "TRUSTEE_PARENT_CLAIM_BLOCKED"]) if not analysis_df.empty else 0,
        "rulebook_eligible": len(analysis_df[analysis_df["recovery_scenario"] == "TRUSTEE_RULEBOOK_READY_ELIGIBLE"]) if not analysis_df.empty else 0,
    }

    rules_out = os.path.join(output_dir, "trustee_payment_recovery_rules.json")
    shutil.copy2(rules_path, rules_out)
    outputs = [rules_out]

    for name, frame in [
        ("trustee_routing_recovery_analysis.csv", analysis_df),
        ("trustee_recovery_candidate_population.csv", candidate_df),
        ("trustee_rule_refinement_recommendations.csv", rec_df),
    ]:
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        outputs.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_path = os.path.join(output_dir, "trustee_recovery_governance_summary.txt")
    write_summary(summary_path, stats, outputs, analysis_df)
    outputs.append(summary_path)
    return stats, outputs


def write_summary(path, stats, outputs, analysis_df):
    lines = [
        "=== Phase 13A Trustee Payment Recovery Governance Summary ===",
        "",
        f"Total trustee-routing payments analyzed: {stats['total_trustee_payments']}",
        f"QA recovery candidates (not auto-approved): {stats['recovery_candidates']}",
        f"Rulebook-eligible (gating-only block): {stats['rulebook_eligible']}",
        f"Parent-claim-blocked: {stats['parent_blocked']}",
        "",
        "Recovery scenario distribution:",
    ]
    if not analysis_df.empty:
        for scenario, cnt in analysis_df["recovery_scenario"].value_counts().items():
            lines.append(f"  {scenario}: {cnt}")
    lines.extend([
        "",
        "Enterprise notes:",
        "  - No trustee payments auto-approved",
        "  - Primary recoverable population blocked by derivation_status gating only",
        "  - production_dbf_flag=N on all outputs",
        "",
        "Output files:",
    ])
    for f in outputs:
        lines.append(f"  - {f}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Phase 13A trustee payment recovery engine.")
    parser.add_argument("--rejected-payments", default=os.path.join(PHASE12, "rejected_payment_root_cause_analysis.csv"))
    parser.add_argument("--clmp-candidates", default=os.path.join(PHASE10A, "quikclmp_derivation_candidates.csv"))
    parser.add_argument("--clmp-validation", default=os.path.join(PHASE10A, "quikclmp_derivation_validation.csv"))
    parser.add_argument("--payee-stage", default=os.path.join(PHASE9, "canonical_claim_payee_stage.csv"))
    parser.add_argument("--crosswalk", default=os.path.join(PHASE11, "claimnum_crosswalk.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    for label, path in (("Rejected payments", args.rejected_payments), ("Rules", args.rules)):
        if not os.path.isfile(path):
            logger.error("%s not found: %s", label, path)
            return 1

    stats, outputs = run_engine(
        load_csv(args.rejected_payments),
        load_csv(args.clmp_candidates) if os.path.isfile(args.clmp_candidates) else pd.DataFrame(),
        load_csv(args.clmp_validation) if os.path.isfile(args.clmp_validation) else pd.DataFrame(),
        load_csv(args.payee_stage) if os.path.isfile(args.payee_stage) else pd.DataFrame(),
        load_csv(args.crosswalk) if os.path.isfile(args.crosswalk) else pd.DataFrame(),
        args.rules, args.output,
    )
    print(f"Trustee recovery analysis complete. Analyzed: {stats['total_trustee_payments']}")
    print(f"Recovery candidates: {stats['recovery_candidates']}")
    for p in outputs:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
