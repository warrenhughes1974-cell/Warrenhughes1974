#!/usr/bin/env python3
"""
Phase 9 — Canonical QUIKCLMP staging derivation engine (read-only).

Transforms Phase 8 payment/payee staging candidates into canonical staging structures.
Does NOT generate production QUIKCLMP DBFs or modify app.py / prior phase outputs.
"""

import argparse
import json
import logging
import os
import re
import shutil

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_RULES = os.path.join(ROOT, "config", "quikclmp_canonical_rules.json")
DEFAULT_RELATIONSHIP_SEMANTICS = os.path.join(ROOT, "config", "relationship_code_semantics.json")
PHASE6 = os.path.join(ROOT, "phase6_family_balancing_intelligence")
PHASE7B = os.path.join(ROOT, "phase7b_cross_claim_linkage")
PHASE7C = os.path.join(ROOT, "phase7c_death_claim_decomposition")
PHASE8 = os.path.join(ROOT, "phase8_payee_distribution_intelligence")
PHASE3_OUTPUT = os.path.join(ROOT, "output")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase9_quikclmp_canonical_staging")

logger = logging.getLogger("quikclmp_canonical_staging")


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


def format_tx_code(value):
    digits = re.sub(r"[^0-9]", "", str(value))
    if not digits:
        return ""
    return str(int(digits)).zfill(4)


def confidence_rank(level):
    order = {"HIGH_CONFIDENCE": 4, "MODERATE_CONFIDENCE": 3, "INFERRED": 2, "LOW_CONFIDENCE": 1}
    return order.get(level, 0)


def payout_category(code, rules):
    mapping = rules.get("payout_code_categories", {})
    cfg = mapping.get(format_tx_code(code), {})
    return (
        cfg.get("payment_type", "UNKNOWN_PAYOUT"),
        cfg.get("payment_category", "UNKNOWN"),
        cfg.get("payment_family", rules.get("claim_family_default", "DEATH_CLAIM")),
    )


def payee_role_meta(relate_code, rules):
    mapping = rules.get("payee_role_mapping", {})
    return mapping.get(strip_code(relate_code), {
        "payee_role": "UNKNOWN",
        "beneficiary_indicator": "N",
        "trustee_indicator": "N",
        "fallback_indicator": "N",
    })


def strip_code(value):
    return str(value).strip().upper() if value is not None else ""


def status_mapping(payee_status, rules):
    return rules.get("distribution_status_mapping", {}).get(
        payee_status,
        {"canonical_status": "PAYMENT_STAGED", "settlement_status": "STAGED"},
    )


def distribution_type(assignment_basis, rules):
    return rules.get("beneficiary_distribution_types", {}).get(
        assignment_basis, assignment_basis or "UNKNOWN",
    )


def is_rulebook_ready(canonical_status, confidence, has_payee, rules):
    cfg = rules.get("rulebook_readiness", {})
    min_conf = cfg.get("minimum_confidence", "MODERATE_CONFIDENCE")
    if confidence_rank(confidence) < confidence_rank(min_conf):
        return "N"
    if cfg.get("requires_payee_assigned") and not has_payee:
        return "N"
    if canonical_status in cfg.get("exclude_statuses", []):
        if canonical_status == "INFERRED_DISTRIBUTION" and cfg.get("allow_inferred_with_equal_split"):
            return "PARTIAL"
        return "N"
    return "Y"


def residual_type(gap_direction, rules):
    mapping = rules.get("residual_type_mapping", {})
    key = gap_direction if gap_direction in mapping else "UNRESOLVED"
    return mapping.get(key, "UNRESOLVED_PAYEE_RESIDUAL")


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def run_engine(
    staging, detail, beneficiary_analysis, multi_split, confidence_analysis,
    decomp_summary, component_layers, enhanced_groups, revised_fin,
    relationship_hierarchy, rules_path, output_dir,
):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    prefixes = rules.get("staging_id_prefixes", {})

    detail_map = {}
    if not detail.empty:
        for _, row in detail.iterrows():
            key = (row["reconstructed_claim_id"], str(row.get("payout_sequence", "")))
            detail_map[key] = row.to_dict()

    summary_map = {}
    payee_summary = load_csv(os.path.join(PHASE8, "payee_distribution_summary.csv"))
    for _, row in payee_summary.iterrows():
        summary_map[row["reconstructed_claim_id"]] = row.to_dict()

    decomp_map = decomp_summary.set_index("reconstructed_claim_id").to_dict("index")
    rev_map = revised_fin.set_index("reconstructed_claim_id").to_dict("index") if not revised_fin.empty else {}
    conf_map = confidence_analysis.set_index("reconstructed_claim_id").to_dict("index") if not confidence_analysis.empty else {}
    multi_map = multi_split.set_index("reconstructed_claim_id").to_dict("index") if not multi_split.empty else {}

    payment_rows = []
    payee_rows = []
    beneficiary_rows = []
    residual_rows = []
    sequence_rows = []
    role_rows = []
    ben_dist_rows = []
    confidence_rows = []
    recommendations = []

    staged_claims = set()

    for _, st in staging.sort_values(["reconstructed_claim_id", "payout_sequence"]).iterrows():
        claim_id = st["reconstructed_claim_id"]
        seq = str(st.get("payout_sequence", "1"))
        key = (claim_id, seq)
        det = detail_map.get(key, {})
        summ = summary_map.get(claim_id, {})
        decomp = decomp_map.get(claim_id, {})
        multi = multi_map.get(claim_id, {})

        payee_status = st.get("payee_distribution_status", "")
        status_cfg = status_mapping(payee_status, rules)
        canonical_status = status_cfg.get("canonical_status", "PAYMENT_STAGED")
        settlement_status = status_cfg.get("settlement_status", "STAGED")

        payout_code = format_tx_code(det.get("payout_code", "0094"))
        pay_type, pay_category, pay_family = payout_category(payout_code, rules)
        confidence = st.get("confidence_level", summ.get("confidence_level", "INFERRED"))

        cps_id = f"{prefixes.get('payment', 'CPS')}-{claim_id}-P{seq}"
        lineage = "|".join(filter(None, [
            claim_id,
            st.get("enhanced_settlement_group_id", ""),
            st.get("payment_event_stage_candidate_id", ""),
        ]))

        rulebook_ready = is_rulebook_ready(
            canonical_status,
            confidence,
            bool(strip_code(st.get("assigned_name_id", ""))),
            rules,
        )
        if rulebook_ready == "PARTIAL":
            canonical_status = "INFERRED_DISTRIBUTION"

        payment_rows.append({
            "canonical_payment_stage_id": cps_id,
            "reconstructed_claim_id": claim_id,
            "policy_number": st.get("policy_number", ""),
            "enhanced_settlement_group_id": st.get("enhanced_settlement_group_id", ""),
            "payment_sequence": seq,
            "payment_amount": round(parse_amount(st.get("payout_amount", 0)), 2),
            "payment_type": pay_type,
            "payment_category": pay_category,
            "payment_family": pay_family,
            "payout_code": payout_code,
            "payout_date": det.get("payout_date", ""),
            "settlement_status": settlement_status,
            "canonical_status": canonical_status,
            "confidence_level": confidence,
            "payee_distribution_status": payee_status,
            "decomposition_status": decomp.get("decomposition_status", ""),
            "derivation_lineage": lineage,
            "source_payment_event_stage_candidate_id": st.get("payment_event_stage_candidate_id", ""),
            "future_rulebook_ready": rulebook_ready,
            "production_dbf_flag": "N",
        })

        relate = strip_code(st.get("assigned_relate_code", ""))
        role_meta = payee_role_meta(relate, rules)
        cpys_id = f"{prefixes.get('payee', 'CPYS')}-{claim_id}-P{seq}"

        payee_rows.append({
            "canonical_payee_stage_id": cpys_id,
            "canonical_payment_stage_id": cps_id,
            "reconstructed_claim_id": claim_id,
            "policy_number": st.get("policy_number", ""),
            "payee_name_id": st.get("assigned_name_id", ""),
            "relationship_code": relate,
            "payee_role": role_meta.get("payee_role", "UNKNOWN"),
            "payee_confidence": confidence,
            "trustee_indicator": role_meta.get("trustee_indicator", "N"),
            "beneficiary_indicator": role_meta.get("beneficiary_indicator", "N"),
            "fallback_indicator": role_meta.get("fallback_indicator", "N"),
            "assignment_basis": det.get("assignment_basis", ""),
            "canonical_status": "PAYEE_STAGED" if relate else "RESIDUAL_PENDING",
            "derivation_lineage": f"{cps_id}|{st.get('payee_distribution_candidate_id', '')}",
            "source_payee_distribution_candidate_id": st.get("payee_distribution_candidate_id", ""),
            "production_dbf_flag": "N",
        })

        is_beneficiary = (
            role_meta.get("beneficiary_indicator") == "Y"
            or relate in rules.get("beneficiary_codes", [])
            or payee_status in {"MULTI_BENEFICIARY_SPLIT", "BENEFICIARY_INFERRED"}
        )
        if is_beneficiary and strip_code(st.get("assigned_name_id", "")):
            equal_split = multi.get("equal_split_detected", "N")
            inferred = "Y" if payee_status == "BENEFICIARY_INFERRED" else "N"
            cbs_id = f"{prefixes.get('beneficiary', 'CBS')}-{claim_id}-P{seq}"
            beneficiary_rows.append({
                "canonical_beneficiary_stage_id": cbs_id,
                "canonical_payment_stage_id": cps_id,
                "reconstructed_claim_id": claim_id,
                "policy_number": st.get("policy_number", ""),
                "beneficiary_name_id": st.get("assigned_name_id", ""),
                "relationship_code": relate,
                "distribution_type": distribution_type(det.get("assignment_basis", ""), rules),
                "equal_split_indicator": equal_split,
                "inferred_distribution_indicator": inferred,
                "beneficiary_sequence": seq,
                "inferred_share_pct": det.get("inferred_share_pct", ""),
                "canonical_status": "BENEFICIARY_STAGED",
                "derivation_lineage": f"{cps_id}|{st.get('beneficiary_distribution_candidate_id', '')}",
                "source_beneficiary_distribution_candidate_id": st.get("beneficiary_distribution_candidate_id", ""),
                "production_dbf_flag": "N",
            })

        sequence_rows.append({
            "reconstructed_claim_id": claim_id,
            "canonical_payment_stage_id": cps_id,
            "payment_sequence": seq,
            "payout_date": det.get("payout_date", ""),
            "payment_amount": round(parse_amount(st.get("payout_amount", 0)), 2),
            "sequencing_basis": "PAYOUT_EVENT_ORDER",
            "staged_payout_flag": "Y" if parse_amount(summ.get("payout_event_count", 0)) > 1 else "N",
            "canonical_status": canonical_status,
        })

        role_rows.append({
            "reconstructed_claim_id": claim_id,
            "canonical_payee_stage_id": cpys_id,
            "relationship_code": relate,
            "payee_role": role_meta.get("payee_role", "UNKNOWN"),
            "trustee_indicator": role_meta.get("trustee_indicator", "N"),
            "beneficiary_indicator": role_meta.get("beneficiary_indicator", "N"),
            "fallback_indicator": role_meta.get("fallback_indicator", "N"),
            "payee_distribution_status": payee_status,
            "confidence_level": confidence,
        })

        if payee_status in {"MULTI_BENEFICIARY_SPLIT", "TRUSTEE_MANAGED_DISTRIBUTION", "BENEFICIARY_INFERRED"}:
            ben_dist_rows.append({
                "reconstructed_claim_id": claim_id,
                "canonical_payment_stage_id": cps_id,
                "payment_sequence": seq,
                "distribution_type": distribution_type(det.get("assignment_basis", ""), rules),
                "payee_distribution_status": payee_status,
                "equal_split_detected": multi.get("equal_split_detected", "N"),
                "beneficiary_name_id": st.get("assigned_name_id", ""),
                "relationship_code": relate,
                "confidence_level": confidence,
            })

        confidence_rows.append({
            "reconstructed_claim_id": claim_id,
            "canonical_payment_stage_id": cps_id,
            "canonical_status": canonical_status,
            "confidence_level": confidence,
            "payee_distribution_status": payee_status,
            "future_rulebook_ready": rulebook_ready,
            "relationship_code_quality": conf_map.get(claim_id, {}).get("relationship_code_quality", ""),
            "payout_count_alignment": conf_map.get(claim_id, {}).get("payout_count_alignment", ""),
            "confidence_rationale": summ.get("confidence_rationale", ""),
        })

        staged_claims.add(claim_id)

    for claim_id, decomp in decomp_map.items():
        residual_amt = parse_amount(decomp.get("residual_amount", 0))
        gap = decomp.get("gap_direction", "")
        payee_status = summary_map.get(claim_id, {}).get("payee_distribution_status", "")
        rev = rev_map.get(claim_id, {})
        balancing = rev.get("revised_balancing_status", "")

        needs_residual = (
            abs(residual_amt) > 0.01
            or payee_status == "PAYEE_UNRESOLVED"
            or claim_id not in staged_claims
        )
        if not needs_residual:
            continue

        rtype = residual_type(gap if payee_status != "PAYEE_UNRESOLVED" else "UNRESOLVED", rules)
        reason = decomp.get("decomposition_status", "")
        if payee_status == "PAYEE_UNRESOLVED":
            reason = "UNRESOLVED_PAYEE;" + reason

        crs_id = f"{prefixes.get('residual', 'CRS')}-{claim_id}"
        residual_rows.append({
            "canonical_residual_stage_id": crs_id,
            "reconstructed_claim_id": claim_id,
            "policy_number": decomp.get("policy_number", ""),
            "enhanced_settlement_group_id": decomp.get("enhanced_settlement_group_id", ""),
            "residual_type": rtype,
            "residual_amount": round(residual_amt, 2),
            "residual_reason": reason,
            "gap_direction": gap,
            "decomposition_status": decomp.get("decomposition_status", ""),
            "balancing_status": balancing,
            "payee_distribution_status": payee_status,
            "canonical_status": "RESIDUAL_PENDING",
            "confidence_level": summary_map.get(claim_id, {}).get("confidence_level", "LOW_CONFIDENCE"),
            "derivation_lineage": claim_id,
            "production_dbf_flag": "N",
        })

    payment_df = pd.DataFrame(payment_rows).sort_values(
        ["reconstructed_claim_id", "payment_sequence"],
    ).reset_index(drop=True) if payment_rows else pd.DataFrame()
    payee_df = pd.DataFrame(payee_rows).sort_values(
        ["reconstructed_claim_id", "canonical_payment_stage_id"],
    ).reset_index(drop=True) if payee_rows else pd.DataFrame()
    beneficiary_df = pd.DataFrame(beneficiary_rows).sort_values(
        ["reconstructed_claim_id", "beneficiary_sequence"],
    ).reset_index(drop=True) if beneficiary_rows else pd.DataFrame()
    residual_df = pd.DataFrame(residual_rows).sort_values(
        "reconstructed_claim_id",
    ).reset_index(drop=True) if residual_rows else pd.DataFrame()
    sequence_df = pd.DataFrame(sequence_rows).sort_values(
        ["reconstructed_claim_id", "payment_sequence"],
    ).reset_index(drop=True) if sequence_rows else pd.DataFrame()
    role_df = pd.DataFrame(role_rows).sort_values(
        "reconstructed_claim_id",
    ).reset_index(drop=True) if role_rows else pd.DataFrame()
    ben_dist_df = pd.DataFrame(ben_dist_rows).sort_values(
        ["reconstructed_claim_id", "payment_sequence"],
    ).reset_index(drop=True) if ben_dist_rows else pd.DataFrame()
    confidence_df = pd.DataFrame(confidence_rows).sort_values(
        "canonical_payment_stage_id",
    ).reset_index(drop=True) if confidence_rows else pd.DataFrame()

    rb_ready = int((payment_df["future_rulebook_ready"] == "Y").sum()) if not payment_df.empty else 0
    rulebook_ready_rows = int(
        ((payment_df["future_rulebook_ready"] == "Y") & (payment_df["confidence_level"] == "HIGH_CONFIDENCE")).sum()
    ) if not payment_df.empty else 0
    if rb_ready > 0:
        recommendations.append({
            "observed_pattern": f"{rb_ready} canonical payment stages marked FUTURE_RULEBOOK_READY",
            "root_cause": "High-confidence payee linkage with normalized staging lineage",
            "recommended_action": "Proceed to Phase 10 rulebook field derivation design",
            "expected_impact": "HIGH",
            "confidence_level": "HIGH_CONFIDENCE",
        })
    if len(residual_df) > 0:
        recommendations.append({
            "observed_pattern": f"{len(residual_df)} residual staging records",
            "root_cause": "Balancing/decomposition gaps or unresolved payee distributions",
            "recommended_action": "Review canonical_claim_residual_stage.csv before production derivation",
            "expected_impact": "MEDIUM",
            "confidence_level": "MODERATE_CONFIDENCE",
        })
    if not payment_df.empty:
        multi_count = int((payment_df["canonical_status"] == "MULTI_PAYEE_STAGED").sum())
        if multi_count > 0:
            recommendations.append({
                "observed_pattern": f"{multi_count} multi-payee staged payment rows",
                "root_cause": "Multi-beneficiary death claim payout decomposition",
                "recommended_action": "Use canonical_claim_beneficiary_stage.csv for QUIKCLMP derivation",
                "expected_impact": "HIGH",
                "confidence_level": "HIGH_CONFIDENCE",
            })

    rec_df = pd.DataFrame(recommendations).reset_index(drop=True) if recommendations else pd.DataFrame()

    stats = {
        "total_payment_stages": len(payment_df),
        "total_payee_stages": len(payee_df),
        "total_beneficiary_stages": len(beneficiary_df),
        "total_residual_stages": len(residual_df),
        "multi_payee_stages": int((payment_df["canonical_status"] == "MULTI_PAYEE_STAGED").sum()) if not payment_df.empty else 0,
        "trustee_managed": int((payment_df["canonical_status"] == "TRUSTEE_ROUTED").sum()) if not payment_df.empty else 0,
        "inferred_distributions": int((payment_df["canonical_status"] == "INFERRED_DISTRIBUTION").sum()) if not payment_df.empty else 0,
        "future_rulebook_ready": rb_ready,
        "future_rulebook_ready_high_confidence": rulebook_ready_rows,
        "unresolved_residuals": int((residual_df["payee_distribution_status"] == "PAYEE_UNRESOLVED").sum()) if not residual_df.empty else 0,
        "payment_sequence_distribution": sequence_df["payment_sequence"].value_counts().to_dict() if not sequence_df.empty else {},
        "canonical_status_distribution": payment_df["canonical_status"].value_counts().to_dict() if not payment_df.empty else {},
        "confidence_distribution": payment_df["confidence_level"].value_counts().to_dict() if not payment_df.empty else {},
        "unique_claims_staged": payment_df["reconstructed_claim_id"].nunique() if not payment_df.empty else 0,
    }

    reports = {
        "canonical_claim_payment_stage.csv": payment_df,
        "canonical_claim_payee_stage.csv": payee_df,
        "canonical_claim_beneficiary_stage.csv": beneficiary_df,
        "canonical_claim_residual_stage.csv": residual_df,
        "canonical_payment_sequence_analysis.csv": sequence_df,
        "canonical_payee_role_analysis.csv": role_df,
        "canonical_beneficiary_distribution_analysis.csv": ben_dist_df,
        "canonical_staging_confidence_analysis.csv": confidence_df,
        "canonical_staging_recommendations.csv": rec_df,
    }

    rules_out = os.path.join(output_dir, "quikclmp_canonical_rules.json")
    shutil.copy2(rules_path, rules_out)
    output_files = [rules_out]

    for name, frame in reports.items():
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        output_files.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_txt = os.path.join(output_dir, "canonical_staging_summary.txt")
    write_summary_txt(summary_txt, stats, output_files)
    output_files.append(summary_txt)
    logger.info("Wrote canonical_staging_summary.txt")

    return stats, output_files


def write_summary_txt(path, stats, output_files):
    lines = [
        "=== Canonical QUIKCLMP Staging Summary (Phase 9) ===",
        "",
        f"Canonical payment stages: {stats['total_payment_stages']}",
        f"Canonical payee stages: {stats['total_payee_stages']}",
        f"Canonical beneficiary stages: {stats['total_beneficiary_stages']}",
        f"Canonical residual stages: {stats['total_residual_stages']}",
        f"Unique claims with payment staging: {stats['unique_claims_staged']}",
        "",
        "Canonical status distribution (payment):",
    ]
    for status, count in sorted(stats.get("canonical_status_distribution", {}).items()):
        lines.append(f"  {status}: {count}")
    lines.extend([
        "",
        "Key metrics:",
        f"  Multi-payee staged rows: {stats['multi_payee_stages']}",
        f"  Trustee-managed stages: {stats['trustee_managed']}",
        f"  Inferred distributions: {stats['inferred_distributions']}",
        f"  Future rulebook ready: {stats['future_rulebook_ready']}",
        f"  Unresolved residual stages: {stats['unresolved_residuals']}",
        "",
        "Confidence distribution:",
    ])
    for level, count in sorted(stats.get("confidence_distribution", {}).items()):
        lines.append(f"  {level}: {count}")
    lines.extend([
        "",
        "Architectural notes:",
        "  - Canonical staging only; no production QUIKCLMP DBF generation",
        "  - All rows preserve reconstructed_claim_id and enhanced_settlement_group_id lineage",
        "  - production_dbf_flag=N on all staging outputs",
        "",
        "Recommended next phase:",
        "  - Phase 10: Actual QUIKCLMP rulebook derivation design",
        "",
        "Output files generated:",
    ])
    for f in output_files:
        lines.append(f"  - {f}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Phase 9 canonical QUIKCLMP staging engine.")
    parser.add_argument("--staging", default=os.path.join(PHASE8, "payment_payee_staging_candidates.csv"))
    parser.add_argument("--detail", default=os.path.join(PHASE8, "payee_distribution_detail.csv"))
    parser.add_argument("--beneficiary-analysis", default=os.path.join(PHASE8, "beneficiary_distribution_analysis.csv"))
    parser.add_argument("--multi-split", default=os.path.join(PHASE8, "multi_beneficiary_split_analysis.csv"))
    parser.add_argument("--confidence", default=os.path.join(PHASE8, "payee_distribution_confidence_analysis.csv"))
    parser.add_argument("--decomposition", default=os.path.join(PHASE7C, "death_claim_decomposition_summary.csv"))
    parser.add_argument("--component-layers", default=os.path.join(PHASE7C, "death_claim_component_layers.csv"))
    parser.add_argument("--enhanced-groups", default=os.path.join(PHASE7B, "enhanced_settlement_groups.csv"))
    parser.add_argument("--revised-financials", default=os.path.join(PHASE6, "revised_claim_financials.csv"))
    parser.add_argument("--relationship-hierarchy", default=os.path.join(PHASE3_OUTPUT, "relationship_hierarchy_analysis.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    required = (
        ("Staging candidates", args.staging),
        ("Payee detail", args.detail),
        ("Decomposition", args.decomposition),
        ("Rules", args.rules),
    )
    for label, path in required:
        if not os.path.isfile(path):
            logger.error("%s not found: %s", label, path)
            return 1

    staging = load_csv(args.staging)
    detail = load_csv(args.detail)
    beneficiary_analysis = load_csv(args.beneficiary_analysis) if os.path.isfile(args.beneficiary_analysis) else pd.DataFrame()
    multi_split = load_csv(args.multi_split) if os.path.isfile(args.multi_split) else pd.DataFrame()
    confidence_analysis = load_csv(args.confidence) if os.path.isfile(args.confidence) else pd.DataFrame()
    decomp_summary = load_csv(args.decomposition)
    component_layers = load_csv(args.component_layers) if os.path.isfile(args.component_layers) else pd.DataFrame()
    enhanced_groups = load_csv(args.enhanced_groups) if os.path.isfile(args.enhanced_groups) else pd.DataFrame()
    revised_fin = load_csv(args.revised_financials) if os.path.isfile(args.revised_financials) else pd.DataFrame()
    relationship_hierarchy = (
        load_csv(args.relationship_hierarchy)
        if os.path.isfile(args.relationship_hierarchy) else pd.DataFrame()
    )

    try:
        stats, outputs = run_engine(
            staging, detail, beneficiary_analysis, multi_split, confidence_analysis,
            decomp_summary, component_layers, enhanced_groups, revised_fin,
            relationship_hierarchy, args.rules, args.output,
        )
        print(f"Canonical staging derivation complete. Payment stages: {stats['total_payment_stages']}")
        print(f"Future rulebook ready: {stats['future_rulebook_ready']}")
        print(f"Residual stages: {stats['total_residual_stages']}")
        print(f"Output: {os.path.abspath(args.output)}")
        for p in outputs:
            print(f"  {p}")
        return 0
    except (ValueError, FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
