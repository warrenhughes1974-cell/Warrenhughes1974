#!/usr/bin/env python3
"""
Phase 10A — QUIKCLMP rulebook derivation design engine (read-only).

Derives QUIKCLMP field candidates from Phase 9 canonical staging layers.
Does NOT generate production QUIKCLMP DBFs or modify app.py / prior phase outputs.
"""

import argparse
import json
import logging
import os
import re
import shutil
import sys

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
CONFIG_DIR = os.path.join(ROOT, "config")
if CONFIG_DIR not in sys.path:
    sys.path.insert(0, CONFIG_DIR)
from resolve_claims_source_paths import resolve_prelsa_path

DEFAULT_RULES = os.path.join(ROOT, "config", "quikclmp_derivation_rules.json")
DEFAULT_PRELSA = resolve_prelsa_path()
PHASE4 = os.path.join(ROOT, "phase4_claim_event_reconstruction")
PHASE6 = os.path.join(ROOT, "phase6_family_balancing_intelligence")
PHASE9 = os.path.join(ROOT, "phase9_quikclmp_canonical_staging")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase10a_quikclmp_derivation_design")

logger = logging.getLogger("quikclmp_derivation")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0.0
    raw = str(value).strip().replace(",", "").replace("$", "")
    if not raw:
        return 0.0
    try:
        return float(raw)
    except ValueError:
        return 0.0


def confidence_rank(level):
    order = {"HIGH_CONFIDENCE": 4, "MODERATE_CONFIDENCE": 3, "INFERRED": 2, "LOW_CONFIDENCE": 1}
    return order.get(level, 0)


def is_dash_only(value):
    s = strip_val(value)
    return bool(s) and set(s.replace(" ", "")) == {"-"}


def is_present(value):
    s = strip_val(value)
    return bool(s) and s.lower() not in {"nan", "none"}


def load_prelsa_names(path):
    logger.info("Reading PRELSA for payee enrichment: %s", path)
    df = pd.read_csv(path, encoding="latin1", dtype=str, low_memory=False, on_bad_lines="skip")
    df.columns = [str(c).strip().upper() for c in df.columns]
    sep = df.apply(lambda r: is_dash_only(r.get("POLICY_NUMBER")) or is_dash_only(r.get("NAME_ID")), axis=1)
    df = df[~sep].copy()
    lookup = {}
    for _, row in df.iterrows():
        name_id = strip_val(row.get("NAME_ID", ""))
        if not name_id:
            continue
        first = strip_val(row.get("INDIVIDUAL_FIRST", ""))
        last = strip_val(row.get("INDIVIDUAL_LAST", ""))
        business = strip_val(row.get("NAME_BUSINESS", ""))
        if business:
            display = business[:50]
        else:
            display = " ".join(p for p in [first, last] if p).strip()[:50]
        tin = strip_val(row.get("SOC_SEC_NUMBER", "")) or strip_val(row.get("BUSINESS_TAX_CODE", ""))
        lookup[name_id] = {
            "name_display": display,
            "tax_id": tin[:9] if tin else "",
            "addr_line_1": strip_val(row.get("ADDR_LINE_1", ""))[:25],
            "city": strip_val(row.get("CITY", ""))[:50],
            "state": strip_val(row.get("STATE", ""))[:2],
            "zip": strip_val(row.get("ZIP", ""))[:5],
        }
    logger.info("PRELSA name lookup entries: %s", len(lookup))
    return lookup


def resolve_source(source_key, payment, payee, beneficiary, residual, prelsa, revised, financials):
    if source_key == "constant":
        return ""
    if source_key.startswith("prelsa."):
        field = source_key.split(".", 1)[1]
        name_id = strip_val(payee.get("payee_name_id", ""))
        return prelsa.get(name_id, {}).get(field, "")
    if source_key.startswith("revised_claim_financials."):
        field = source_key.split(".", 1)[1]
        claim_id = payment.get("reconstructed_claim_id", "")
        fin = financials.get(claim_id, {})
        rev = revised.get(claim_id, {})
        if field == "withholding":
            return fin.get("withholding_amount", "")
        if field == "interest":
            return fin.get("interest_amount", "")
        return rev.get(field, "")
    if source_key.startswith("canonical_claim_residual_stage."):
        field = source_key.split(".", 1)[1]
        return residual.get(field, "")
    if "." in source_key:
        table, field = source_key.split(".", 1)
        if table == "canonical_claim_payment_stage":
            return payment.get(field, "")
        if table == "canonical_claim_payee_stage":
            return payee.get(field, "")
        if table == "canonical_claim_beneficiary_stage":
            return beneficiary.get(field, "")
    return ""


def derive_field(field_name, cfg, payment, payee, beneficiary, residual, prelsa, revised, financials, rules):
    source = cfg.get("source", "")
    dtype = cfg.get("derivation_type", "DIRECT")
    value = resolve_source(source, payment, payee, beneficiary, residual, prelsa, revised, financials)

    if not value and cfg.get("fallback_source"):
        fb = cfg.get("fallback_source", "")
        if "payee_name_id" in fb:
            value = strip_val(payee.get("payee_name_id", ""))

    if field_name == "MPHASE" and cfg.get("constant_value"):
        value = cfg.get("constant_value", rules.get("default_mphase", "1"))

    if field_name == "MTRUSTEE":
        value = "Y" if strip_val(payee.get("trustee_indicator", "")) in cfg.get("true_values", ["Y"]) else "N"

    rationale = f"{dtype} from {source}"
    conf = payment.get("confidence_level", "INFERRED")

    if dtype == "HIERARCHICAL" and not value and payee.get("fallback_indicator") == "Y":
        rationale = f"Hierarchical fallback for {field_name}; relationship={payee.get('relationship_code', '')}"
        conf = "LOW_CONFIDENCE" if conf != "LOW_CONFIDENCE" else conf

    if dtype == "RESIDUAL" and not value:
        rationale = "No residual on claim; field left blank"
    elif dtype == "RESIDUAL" and value:
        rationale = f"Residual amount preserved from canonical residual stage"

    if field_name == "MPAYNAME" and not value:
        rationale = "Payee name unresolved; PRELSA lookup missing"

    return strip_val(value), rationale, conf


def derivation_status(payment, payee, rules):
    canonical = payment.get("canonical_status", "")
    status_map = rules.get("derivation_status_rules", {})
    base = status_map.get(canonical, "DIRECT_DERIVATION")

    if payee.get("fallback_indicator") == "Y":
        return "FALLBACK_DERIVATION"
    if base == "TRUSTEE_DERIVATION":
        return "TRUSTEE_DERIVATION"
    if base == "INFERRED_DERIVATION":
        return "INFERRED_DERIVATION"
    if base == "HIERARCHICAL_DERIVATION":
        if payment.get("future_rulebook_ready") == "Y":
            return "RULEBOOK_READY"
        return "HIERARCHICAL_DERIVATION"
    if payment.get("future_rulebook_ready") == "Y":
        return "RULEBOOK_READY"
    conf = payment.get("confidence_level", "INFERRED")
    gating = rules.get("confidence_gating", {})
    if conf in gating.get("manual_review_confidence", []):
        return "NEEDS_MANUAL_REVIEW"
    if base in gating.get("manual_review_statuses", []):
        return "NEEDS_MANUAL_REVIEW"
    return base


def gate_confidence(payment, payee, field_conf, rules):
    gating = rules.get("confidence_gating", {})
    min_rb = gating.get("rulebook_ready_minimum", "MODERATE_CONFIDENCE")
    payment_conf = payment.get("confidence_level", "INFERRED")
    overall = payment_conf if confidence_rank(payment_conf) <= confidence_rank(field_conf) else field_conf
    rulebook_ready = "Y" if confidence_rank(overall) >= confidence_rank(min_rb) else "N"
    manual_review = "Y" if overall in gating.get("manual_review_confidence", []) else "N"
    if not strip_val(payee.get("payee_name_id", "")) and rules.get("validation_rules", {}).get("flag_missing_payname"):
        manual_review = "Y"
    return overall, rulebook_ready, manual_review


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def run_engine(payment_stage, payee_stage, beneficiary_stage, residual_stage,
               staging_confidence, revised_fin, financials, prelsa_lookup, rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    field_rules = rules.get("field_derivations", {})

    payee_map = payee_stage.set_index("canonical_payment_stage_id").to_dict("index")
    ben_map = beneficiary_stage.set_index("canonical_payment_stage_id").to_dict("index") if not beneficiary_stage.empty else {}
    residual_map = residual_stage.set_index("reconstructed_claim_id").to_dict("index") if not residual_stage.empty else {}
    rev_map = revised_fin.set_index("reconstructed_claim_id").to_dict("index") if not revised_fin.empty else {}
    fin_map = financials.set_index("reconstructed_claim_id").to_dict("index") if not financials.empty else {}

    candidates = []
    field_rows = []
    payment_type_rows = []
    payee_rows = []
    residual_rows = []
    gating_rows = []
    validation_rows = []
    recommendations = []

    for _, pay in payment_stage.sort_values(["reconstructed_claim_id", "payment_sequence"]).iterrows():
        cps_id = pay["canonical_payment_stage_id"]
        claim_id = pay["reconstructed_claim_id"]
        payee = payee_map.get(cps_id, {})
        ben = ben_map.get(cps_id, {})
        residual = residual_map.get(claim_id, {})

        derived = {}
        field_confidences = []
        for field_name, cfg in field_rules.items():
            val, rationale, fconf = derive_field(
                field_name, cfg, pay.to_dict(), payee, ben, residual,
                prelsa_lookup, rev_map, fin_map, rules,
            )
            derived[field_name] = val
            field_confidences.append(fconf)
            field_rows.append({
                "canonical_payment_stage_id": cps_id,
                "reconstructed_claim_id": claim_id,
                "target_table": rules.get("target_table", "QUIKCLMP.DBF"),
                "target_field": field_name,
                "derived_value": val,
                "derivation_source": cfg.get("source", ""),
                "derivation_type": cfg.get("derivation_type", "DIRECT"),
                "derivation_rationale": rationale,
                "derivation_confidence": fconf,
                "layout_type": cfg.get("layout_type", ""),
                "layout_length": cfg.get("layout_length", ""),
            })

        dstatus = derivation_status(pay.to_dict(), payee, rules)
        min_conf = min(field_confidences, key=confidence_rank) if field_confidences else "INFERRED"
        overall_conf, rb_ready, manual = gate_confidence(pay.to_dict(), payee, min_conf, rules)

        if dstatus == "RULEBOOK_READY" and rb_ready == "N":
            dstatus = "NEEDS_MANUAL_REVIEW"

        pay_type = pay.get("payment_type", "")
        pt_map = rules.get("payment_type_mapping", {}).get(pay_type, {})
        payment_type_rows.append({
            "canonical_payment_stage_id": cps_id,
            "reconstructed_claim_id": claim_id,
            "canonical_payment_type": pay_type,
            "payout_code": pay.get("payout_code", ""),
            "quikclmp_paytype_candidate": pt_map.get("quikclmp_paytype", "UNKNOWN"),
            "mhdpmt_default_candidate": pt_map.get("mhdpmt_default", ""),
            "derivation_status": dstatus,
        })

        payee_rows.append({
            "canonical_payment_stage_id": cps_id,
            "reconstructed_claim_id": claim_id,
            "payee_name_id": payee.get("payee_name_id", ""),
            "relationship_code": derived.get("MRELATION", payee.get("relationship_code", "")),
            "mpayname_candidate": derived.get("MPAYNAME", ""),
            "mtin_candidate": derived.get("MTIN", ""),
            "mtrustee_candidate": derived.get("MTRUSTEE", "N"),
            "payee_role": payee.get("payee_role", ""),
            "derivation_status": dstatus,
            "derivation_rationale": payee.get("assignment_basis", ""),
            "derivation_confidence": overall_conf,
        })

        if residual:
            residual_rows.append({
                "reconstructed_claim_id": claim_id,
                "canonical_payment_stage_id": cps_id,
                "mresidual_candidate": derived.get("MRESIDUAL", ""),
                "residual_type": residual.get("residual_type", ""),
                "residual_reason": residual.get("residual_reason", ""),
                "balancing_status": residual.get("balancing_status", ""),
                "derivation_status": "RESIDUAL_PENDING" if parse_amount(residual.get("residual_amount", 0)) != 0 else dstatus,
                "derivation_confidence": overall_conf,
            })

        gating_rows.append({
            "canonical_payment_stage_id": cps_id,
            "reconstructed_claim_id": claim_id,
            "derivation_status": dstatus,
            "confidence_level": overall_conf,
            "future_rulebook_ready": rb_ready,
            "manual_review_required": manual,
            "canonical_status": pay.get("canonical_status", ""),
            "payee_distribution_status": pay.get("payee_distribution_status", ""),
            "gating_rationale": (
                "Passes confidence gate" if rb_ready == "Y" else "Below rulebook-ready confidence threshold or missing payee data"
            ),
        })

        val_issues = []
        vr = rules.get("validation_rules", {})
        if vr.get("require_mpolicy") and not derived.get("MPOLICY"):
            val_issues.append("MISSING_MPOLICY")
        if vr.get("require_mamount") and not derived.get("MAMOUNT"):
            val_issues.append("MISSING_MAMOUNT")
        if vr.get("flag_missing_payname") and not derived.get("MPAYNAME"):
            val_issues.append("MISSING_MPAYNAME")
        if vr.get("flag_low_confidence") and overall_conf in {"LOW_CONFIDENCE", "INFERRED"}:
            val_issues.append("LOW_CONFIDENCE")

        validation_rows.append({
            "canonical_payment_stage_id": cps_id,
            "reconstructed_claim_id": claim_id,
            "derivation_status": dstatus,
            "validation_result": "PASS" if not val_issues else "REVIEW",
            "validation_issues": "|".join(val_issues),
            "rulebook_ready": rb_ready,
            "derivation_confidence": overall_conf,
        })

        candidates.append({
            "derivation_candidate_id": f"QDC-{cps_id}",
            "canonical_payment_stage_id": cps_id,
            "canonical_payee_stage_id": payee.get("canonical_payee_stage_id", ""),
            "reconstructed_claim_id": claim_id,
            "policy_number": pay.get("policy_number", ""),
            "enhanced_settlement_group_id": pay.get("enhanced_settlement_group_id", ""),
            "derivation_status": dstatus,
            "derivation_confidence": overall_conf,
            "future_rulebook_ready": rb_ready,
            "manual_review_required": manual,
            "production_dbf_flag": "N",
            "derivation_lineage": pay.get("derivation_lineage", ""),
            **derived,
        })

    cand_df = pd.DataFrame(candidates).sort_values("derivation_candidate_id").reset_index(drop=True)
    field_df = pd.DataFrame(field_rows).sort_values(["canonical_payment_stage_id", "target_field"]).reset_index(drop=True)
    pt_df = pd.DataFrame(payment_type_rows).sort_values("canonical_payment_stage_id").reset_index(drop=True)
    payee_df = pd.DataFrame(payee_rows).sort_values("canonical_payment_stage_id").reset_index(drop=True)
    residual_df = pd.DataFrame(residual_rows).sort_values("reconstructed_claim_id").reset_index(drop=True) if residual_rows else pd.DataFrame()
    gating_df = pd.DataFrame(gating_rows).sort_values("canonical_payment_stage_id").reset_index(drop=True)
    val_df = pd.DataFrame(validation_rows).sort_values("canonical_payment_stage_id").reset_index(drop=True)

    stats = {
        "total_derivation_candidates": len(cand_df),
        "direct_derivations": int((cand_df["derivation_status"] == "DIRECT_DERIVATION").sum()),
        "hierarchical_derivations": int((cand_df["derivation_status"] == "HIERARCHICAL_DERIVATION").sum()),
        "trustee_derivations": int((cand_df["derivation_status"] == "TRUSTEE_DERIVATION").sum()),
        "inferred_derivations": int((cand_df["derivation_status"] == "INFERRED_DERIVATION").sum()),
        "fallback_derivations": int((cand_df["derivation_status"] == "FALLBACK_DERIVATION").sum()),
        "rulebook_ready": int((cand_df["future_rulebook_ready"] == "Y").sum()),
        "manual_review": int((cand_df["manual_review_required"] == "Y").sum()),
        "status_distribution": cand_df["derivation_status"].value_counts().to_dict(),
        "confidence_distribution": cand_df["derivation_confidence"].value_counts().to_dict(),
        "residual_aware": len(residual_df),
        "validation_pass": int((val_df["validation_result"] == "PASS").sum()),
        "validation_review": int((val_df["validation_result"] == "REVIEW").sum()),
    }

    if stats["manual_review"] > 0:
        recommendations.append({
            "observed_pattern": f"{stats['manual_review']} derivation candidates require manual review",
            "root_cause": "Low confidence, inferred distribution, or missing PRELSA payee name",
            "recommended_action": "Review quikclmp_confidence_gating_analysis.csv before Phase 10B",
            "expected_impact": "MEDIUM",
            "confidence_level": "MODERATE_CONFIDENCE",
        })
    if stats["rulebook_ready"] > 0:
        recommendations.append({
            "observed_pattern": f"{stats['rulebook_ready']} rulebook-ready QUIKCLMP derivation candidates",
            "root_cause": "Canonical staging with confidence-gated field derivation",
            "recommended_action": "Proceed to Phase 10B QUIKCLMS derivation design",
            "expected_impact": "HIGH",
            "confidence_level": "HIGH_CONFIDENCE",
        })
    if stats["validation_review"] > 0:
        recommendations.append({
            "observed_pattern": f"{stats['validation_review']} candidates flagged for validation review",
            "root_cause": "Missing payname or low confidence per validation rules",
            "recommended_action": "Use quikclmp_derivation_validation.csv for QA/UAT triage",
            "expected_impact": "MEDIUM",
            "confidence_level": "MODERATE_CONFIDENCE",
        })

    rec_df = pd.DataFrame(recommendations).reset_index(drop=True) if recommendations else pd.DataFrame()

    reports = {
        "quikclmp_derivation_candidates.csv": cand_df,
        "quikclmp_field_derivation_analysis.csv": field_df,
        "quikclmp_payment_type_mapping_analysis.csv": pt_df,
        "quikclmp_payee_derivation_analysis.csv": payee_df,
        "quikclmp_residual_derivation_analysis.csv": residual_df,
        "quikclmp_confidence_gating_analysis.csv": gating_df,
        "quikclmp_derivation_validation.csv": val_df,
        "quikclmp_derivation_recommendations.csv": rec_df,
    }

    rules_out = os.path.join(output_dir, "quikclmp_derivation_rules.json")
    shutil.copy2(rules_path, rules_out)
    output_files = [rules_out]

    for name, frame in reports.items():
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        output_files.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_txt = os.path.join(output_dir, "quikclmp_derivation_summary.txt")
    write_summary_txt(summary_txt, stats, output_files)
    output_files.append(summary_txt)
    logger.info("Wrote quikclmp_derivation_summary.txt")

    return stats, output_files


def write_summary_txt(path, stats, output_files):
    lines = [
        "=== QUIKCLMP Rulebook Derivation Design Summary (Phase 10A) ===",
        "",
        f"Total derivation candidates: {stats['total_derivation_candidates']}",
        "",
        "Derivation status distribution:",
    ]
    for status, count in sorted(stats.get("status_distribution", {}).items()):
        lines.append(f"  {status}: {count}")
    lines.extend([
        "",
        "Key metrics:",
        f"  Direct derivations: {stats['direct_derivations']}",
        f"  Hierarchical derivations: {stats['hierarchical_derivations']}",
        f"  Trustee derivations: {stats['trustee_derivations']}",
        f"  Inferred derivations: {stats['inferred_derivations']}",
        f"  Fallback derivations: {stats['fallback_derivations']}",
        f"  Rulebook-ready rows: {stats['rulebook_ready']}",
        f"  Manual review candidates: {stats['manual_review']}",
        f"  Residual-aware derivations: {stats['residual_aware']}",
        f"  Validation PASS: {stats['validation_pass']}",
        f"  Validation REVIEW: {stats['validation_review']}",
        "",
        "Confidence distribution:",
    ])
    for level, count in sorted(stats.get("confidence_distribution", {}).items()):
        lines.append(f"  {level}: {count}")
    lines.extend([
        "",
        "Architectural notes:",
        "  - First actual QUIKCLMP target derivation phase; production_dbf_flag=N on all rows",
        "  - Field derivations driven by quikclmp_derivation_rules.json",
        "  - Layout reference used for design only; no DBF generation",
        "",
        "Recommended next phase:",
        "  - Phase 10B: QUIKCLMS rulebook derivation design",
        "",
        "Output files generated:",
    ])
    for f in output_files:
        lines.append(f"  - {f}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Phase 10A QUIKCLMP rulebook derivation engine.")
    parser.add_argument("--payment-stage", default=os.path.join(PHASE9, "canonical_claim_payment_stage.csv"))
    parser.add_argument("--payee-stage", default=os.path.join(PHASE9, "canonical_claim_payee_stage.csv"))
    parser.add_argument("--beneficiary-stage", default=os.path.join(PHASE9, "canonical_claim_beneficiary_stage.csv"))
    parser.add_argument("--residual-stage", default=os.path.join(PHASE9, "canonical_claim_residual_stage.csv"))
    parser.add_argument("--staging-confidence", default=os.path.join(PHASE9, "canonical_staging_confidence_analysis.csv"))
    parser.add_argument("--revised-financials", default=os.path.join(PHASE6, "revised_claim_financials.csv"))
    parser.add_argument("--financials", default=os.path.join(PHASE4, "claim_candidate_financials.csv"))
    parser.add_argument("--prelsa", default=DEFAULT_PRELSA)
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")

    for label, path in (
        ("Payment stage", args.payment_stage),
        ("Payee stage", args.payee_stage),
        ("Rules", args.rules),
    ):
        if not os.path.isfile(path):
            logger.error("%s not found: %s", label, path)
            return 1

    payment_stage = load_csv(args.payment_stage)
    payee_stage = load_csv(args.payee_stage)
    beneficiary_stage = load_csv(args.beneficiary_stage) if os.path.isfile(args.beneficiary_stage) else pd.DataFrame()
    residual_stage = load_csv(args.residual_stage) if os.path.isfile(args.residual_stage) else pd.DataFrame()
    staging_confidence = load_csv(args.staging_confidence) if os.path.isfile(args.staging_confidence) else pd.DataFrame()
    revised_fin = load_csv(args.revised_financials) if os.path.isfile(args.revised_financials) else pd.DataFrame()
    financials = load_csv(args.financials) if os.path.isfile(args.financials) else pd.DataFrame()
    prelsa_lookup = load_prelsa_names(args.prelsa) if os.path.isfile(args.prelsa) else {}

    try:
        stats, outputs = run_engine(
            payment_stage, payee_stage, beneficiary_stage, residual_stage,
            staging_confidence, revised_fin, financials, prelsa_lookup, args.rules, args.output,
        )
        print(f"QUIKCLMP derivation design complete. Candidates: {stats['total_derivation_candidates']}")
        print(f"Rulebook ready: {stats['rulebook_ready']}")
        print(f"Manual review: {stats['manual_review']}")
        print(f"Output: {os.path.abspath(args.output)}")
        for p in outputs:
            print(f"  {p}")
        return 0
    except (ValueError, FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
