#!/usr/bin/env python3
"""
Phase 10B — QUIKCLMS rulebook derivation design engine (read-only).

Derives QUIKCLMS claim-level field candidates from reconstructed claims and Phase 10A payments.
Does NOT generate production QUIKCLMS DBFs or modify app.py / prior phase outputs.
"""

import argparse
import json
import logging
import os
import shutil
from collections import defaultdict

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_RULES = os.path.join(ROOT, "config", "quikclms_derivation_rules.json")
PHASE4 = os.path.join(ROOT, "phase4_claim_event_reconstruction")
PHASE6 = os.path.join(ROOT, "phase6_family_balancing_intelligence")
PHASE7B = os.path.join(ROOT, "phase7b_cross_claim_linkage")
PHASE7C = os.path.join(ROOT, "phase7c_death_claim_decomposition")
PHASE9 = os.path.join(ROOT, "phase9_quikclmp_canonical_staging")
PHASE10A = os.path.join(ROOT, "phase10a_quikclmp_derivation_design")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase10b_quikclms_derivation_design")

logger = logging.getLogger("quikclms_derivation")


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
    order = {"HIGH_CONFIDENCE": 4, "MODERATE_CONFIDENCE": 3, "INFERRED": 2, "LOW_CONFIDENCE": 1,
             "HIGH": 4, "MEDIUM": 3, "LOW": 1}
    return order.get(str(level).upper(), 2)


def normalize_confidence(value):
    v = strip_val(value).upper()
    mapping = {"HIGH": "HIGH_CONFIDENCE", "MEDIUM": "MODERATE_CONFIDENCE", "LOW": "LOW_CONFIDENCE"}
    if v in mapping:
        return mapping[v]
    if v in {"HIGH_CONFIDENCE", "MODERATE_CONFIDENCE", "INFERRED", "LOW_CONFIDENCE"}:
        return v
    return "INFERRED"


def build_payment_aggregation(payment_stage, quikclmp_candidates, financials):
    agg = defaultdict(lambda: {
        "payment_count": 0,
        "total_payment_amount": 0.0,
        "max_payout_date": "",
        "rulebook_ready_payments": 0,
    })
    if not payment_stage.empty:
        for _, row in payment_stage.iterrows():
            cid = row["reconstructed_claim_id"]
            agg[cid]["payment_count"] += 1
            agg[cid]["total_payment_amount"] += parse_amount(row.get("payment_amount", 0))
            d = strip_val(row.get("payout_date", ""))
            if d and (not agg[cid]["max_payout_date"] or d > agg[cid]["max_payout_date"]):
                agg[cid]["max_payout_date"] = d
            if strip_val(row.get("future_rulebook_ready", "")) == "Y":
                agg[cid]["rulebook_ready_payments"] += 1
    if not quikclmp_candidates.empty:
        for cid, sub in quikclmp_candidates.groupby("reconstructed_claim_id"):
            if agg[cid]["payment_count"] == 0:
                agg[cid]["payment_count"] = len(sub)
                amt_col = "mamount" if "mamount" in sub.columns else "MAMOUNT"
                if amt_col in sub.columns:
                    agg[cid]["total_payment_amount"] = round(sub[amt_col].apply(parse_amount).sum(), 2)
    for _, row in financials.iterrows():
        cid = row["reconstructed_claim_id"]
        if agg[cid]["payment_count"] == 0:
            net = parse_amount(row.get("reconstructed_net_payment", 0))
            if net > 0:
                agg[cid]["total_payment_amount"] = net
                agg[cid]["payment_count"] = 1
    return agg


def derive_loan_total(fin):
    return round(
        parse_amount(fin.get("loan_principal_offset", 0))
        + parse_amount(fin.get("loan_interest_offset", 0)),
        2,
    )


def resolve_field(field_name, cfg, ctx, rules):
    source = cfg.get("source", "")
    dtype = cfg.get("derivation_type", "DIRECT")
    header = ctx["header"]
    fin = ctx["financial"]
    rev = ctx["revised"]
    decomp = ctx["decomposition"]
    pay_agg = ctx["payment_agg"]
    family = strip_val(header.get("claim_family", ""))
    lifecycle = strip_val(header.get("reconstructed_lifecycle_status", "UNKNOWN")).upper()

    family_filter = cfg.get("family_filter", [])
    if family_filter and family not in family_filter:
        return "", f"Not applicable for family {family}", "INFERRED"

    if field_name == "MPHASE":
        return rules.get("default_mphase", "1"), "Default phase constant", normalize_confidence(rev.get("balancing_confidence", "INFERRED"))

    if source == "claim_family_mapping.mclaimtype":
        val = rules.get("claim_family_mapping", {}).get(family, {}).get("mclaimtype", family)
        return val, f"Claim family mapping for {family}", normalize_confidence(rev.get("balancing_confidence", "INFERRED"))

    if source == "lifecycle_status_mapping.claimstat":
        lmap = rules.get("lifecycle_status_mapping", {}).get(lifecycle, {})
        val = lmap.get("claimstat", rules.get("claim_family_mapping", {}).get(family, {}).get("claimstat_default", "1"))
        return val, f"Lifecycle {lifecycle} mapped to CLAIMSTAT", normalize_confidence(rev.get("balancing_confidence", "INFERRED"))

    if source == "claim_candidate_header.reconstructed_lifecycle_status":
        lmap = rules.get("lifecycle_status_mapping", {}).get(lifecycle, {})
        val = lmap.get("mclaimstatus", lifecycle)
        return val, f"Lifecycle status from reconstruction header", normalize_confidence(rev.get("balancing_confidence", "INFERRED"))

    if source.startswith("payment_aggregation."):
        field = source.split(".", 1)[1]
        val = pay_agg.get(field, "")
        if field == "total_payment_amount":
            val = str(round(parse_amount(val), 2)) if val != "" else ""
        return strip_val(val), f"Aggregated from canonical payment stages", normalize_confidence(rev.get("balancing_confidence", "INFERRED"))

    if source == "derived.loan_total":
        val = derive_loan_total(fin)
        return str(val), "Sum of loan principal and interest offsets", normalize_confidence(rev.get("balancing_confidence", "INFERRED"))

    if source == "derived.lineage":
        parts = [ctx["claim_id"], ctx.get("enhanced_group", ""), family, lifecycle]
        return "|".join(p for p in parts if p), "Composite claim derivation lineage", normalize_confidence(rev.get("balancing_confidence", "INFERRED"))

    if source.startswith("claim_candidate_header."):
        val = header.get(source.split(".", 1)[1], "")
        if field_name in {"MSETTLEDATE", "PDDATE"} and cfg.get("requires_lifecycle"):
            if lifecycle not in [x.upper() for x in cfg.get("requires_lifecycle", [])]:
                return "", f"Settlement date requires lifecycle {cfg.get('requires_lifecycle')}", "INFERRED"
        return strip_val(val), f"Direct from header.{source.split('.', 1)[1]}", normalize_confidence(rev.get("balancing_confidence", "INFERRED"))

    if source.startswith("claim_candidate_financials."):
        val = fin.get(source.split(".", 1)[1], "")
        return strip_val(val) if val != "" else str(parse_amount(val)), f"Financial component from Phase 4", normalize_confidence(rev.get("balancing_confidence", "INFERRED"))

    if source.startswith("revised_claim_financials."):
        val = rev.get(source.split(".", 1)[1], "")
        return strip_val(val), f"Phase 6 revised balancing output", normalize_confidence(rev.get("balancing_confidence", "INFERRED"))

    if source.startswith("death_claim_decomposition."):
        val = decomp.get(source.split(".", 1)[1], "")
        if not val and dtype == "RESIDUAL":
            val = rev.get("revised_balancing_difference", "")
        return strip_val(val), f"Death decomposition layer reference", normalize_confidence(decomp.get("confidence_level", "INFERRED"))

    return "", f"No resolver for {source}", "LOW_CONFIDENCE"


def derivation_status(ctx, rules):
    rev = ctx["revised"]
    pay_agg = ctx["payment_agg"]
    decomp = ctx["decomposition"]
    balancing = strip_val(rev.get("revised_balancing_status", ""))
    conf = normalize_confidence(rev.get("balancing_confidence", "INFERRED"))

    if parse_amount(decomp.get("residual_amount", 0)) != 0 and balancing == "UNBALANCED":
        base = "RESIDUAL_PENDING"
    elif pay_agg.get("payment_count", 0) > 0:
        base = "AGGREGATED_PAYMENT_DERIVATION"
    elif strip_val(ctx["header"].get("reconstructed_lifecycle_status", "")):
        base = "LIFECYCLE_DERIVATION"
    else:
        base = "FINANCIAL_DERIVATION"

    if conf in rules.get("confidence_gating", {}).get("manual_review_confidence", []):
        return "NEEDS_MANUAL_REVIEW"
    if balancing in rules.get("confidence_gating", {}).get("manual_review_balancing", []) and conf == "LOW_CONFIDENCE":
        return "NEEDS_MANUAL_REVIEW"
    if conf in {"HIGH_CONFIDENCE", "MODERATE_CONFIDENCE"} and balancing in {"BALANCED", "MINOR_VARIANCE"}:
        return "RULEBOOK_READY"
    if pay_agg.get("rulebook_ready_payments", 0) > 0 and balancing != "UNBALANCED":
        return "RULEBOOK_READY"
    if base == "RESIDUAL_PENDING":
        return "RESIDUAL_PENDING"
    if decomp and not strip_val(decomp.get("decomposition_status", "")):
        return base
    if strip_val(decomp.get("decomposition_status", "")):
        return "INFERRED_DERIVATION" if conf == "INFERRED" else base
    return base


def gate_rulebook(status, conf, validation_issues, rules):
    min_conf = rules.get("confidence_gating", {}).get("rulebook_ready_minimum", "MODERATE_CONFIDENCE")
    if status == "NEEDS_MANUAL_REVIEW":
        return "N"
    if validation_issues:
        return "N"
    if status == "RULEBOOK_READY" and confidence_rank(conf) >= confidence_rank(min_conf):
        return "Y"
    if status in {"AGGREGATED_PAYMENT_DERIVATION", "LIFECYCLE_DERIVATION", "FINANCIAL_DERIVATION"}:
        if confidence_rank(conf) >= confidence_rank(min_conf):
            return "Y"
    return "N"


def run_engine(headers, financials, revised_fin, decomp_summary, enhanced_groups,
               payment_stage, quikclmp_candidates, rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    field_rules = rules.get("field_derivations", {})

    rev_map = revised_fin.set_index("reconstructed_claim_id").to_dict("index")
    fin_map = financials.set_index("reconstructed_claim_id").to_dict("index")
    decomp_map = decomp_summary.set_index("reconstructed_claim_id").to_dict("index") if not decomp_summary.empty else {}
    eg_map = enhanced_groups.set_index("reconstructed_claim_id").to_dict("index") if not enhanced_groups.empty else {}
    pay_agg_map = build_payment_aggregation(payment_stage, quikclmp_candidates, financials)

    candidates = []
    field_rows = []
    status_rows = []
    financial_rows = []
    payment_agg_rows = []
    residual_rows = []
    gating_rows = []
    validation_rows = []
    recommendations = []

    claim_ids = sorted(headers["reconstructed_claim_id"].tolist())

    for claim_id in claim_ids:
        header = headers.loc[headers["reconstructed_claim_id"] == claim_id].iloc[0].to_dict()
        fin = fin_map.get(claim_id, {})
        rev = rev_map.get(claim_id, {})
        decomp = decomp_map.get(claim_id, {})
        eg = eg_map.get(claim_id, {})
        pay_agg = pay_agg_map.get(claim_id, {
            "payment_count": 0, "total_payment_amount": 0.0, "max_payout_date": "", "rulebook_ready_payments": 0,
        })

        ctx = {
            "claim_id": claim_id,
            "header": header,
            "financial": fin,
            "revised": rev,
            "decomposition": decomp,
            "payment_agg": pay_agg,
            "enhanced_group": eg.get("enhanced_settlement_group_id", ""),
        }

        derived = {}
        field_confs = []
        for field_name, cfg in field_rules.items():
            val, rationale, fconf = resolve_field(field_name, cfg, ctx, rules)
            derived[field_name] = val
            field_confs.append(fconf)
            field_rows.append({
                "reconstructed_claim_id": claim_id,
                "target_table": rules.get("target_table", "QUIKCLMS.DBF"),
                "target_field": field_name,
                "derived_value": val,
                "derivation_source": cfg.get("source", ""),
                "derivation_type": cfg.get("derivation_type", "DIRECT"),
                "derivation_rationale": rationale,
                "derivation_confidence": fconf,
                "layout_type": cfg.get("layout_type", ""),
                "layout_length": cfg.get("layout_length", ""),
            })

        dstatus = derivation_status(ctx, rules)
        overall_conf = min(field_confs, key=confidence_rank) if field_confs else "INFERRED"
        overall_conf = normalize_confidence(rev.get("balancing_confidence", overall_conf))

        val_issues = []
        vr = rules.get("validation_rules", {})
        if vr.get("require_mpolicy") and not derived.get("MPOLICY"):
            val_issues.append("MISSING_MPOLICY")
        if vr.get("require_mclaimid") and not derived.get("MCLAIMID"):
            val_issues.append("MISSING_MCLAIMID")
        if vr.get("flag_unbalanced") and strip_val(rev.get("revised_balancing_status", "")) == "UNBALANCED":
            val_issues.append("UNBALANCED")
        lifecycle = strip_val(header.get("reconstructed_lifecycle_status", "")).upper()
        if vr.get("flag_missing_payment_when_settled") and lifecycle == "SETTLED" and pay_agg.get("payment_count", 0) == 0:
            val_issues.append("SETTLED_NO_PAYMENT")

        rb_ready = gate_rulebook(dstatus, overall_conf, val_issues, rules)
        manual = "Y" if dstatus == "NEEDS_MANUAL_REVIEW" or overall_conf in {"LOW_CONFIDENCE", "INFERRED"} and val_issues else "N"

        status_rows.append({
            "reconstructed_claim_id": claim_id,
            "policy_number": header.get("policy_number", ""),
            "claim_family": header.get("claim_family", ""),
            "reconstructed_lifecycle_status": header.get("reconstructed_lifecycle_status", ""),
            "mclaimstatus_candidate": derived.get("MCLAIMSTATUS", ""),
            "claimstat_candidate": derived.get("CLAIMSTAT", ""),
            "derivation_status": dstatus,
            "derivation_confidence": overall_conf,
        })

        financial_rows.append({
            "reconstructed_claim_id": claim_id,
            "claim_family": header.get("claim_family", ""),
            "mgrossamt_candidate": derived.get("MGROSSAMT", ""),
            "mnetamt_candidate": derived.get("MNETAMT", ""),
            "mpaid_candidate": derived.get("MPAID", ""),
            "mintamt_candidate": derived.get("MINTAMT", ""),
            "mfedtax_candidate": derived.get("MFEDTAX", ""),
            "mloan_candidate": derived.get("MLOAN", ""),
            "mbalancingstatus": derived.get("MBALANCINGSTATUS", ""),
            "revised_balancing_difference": rev.get("revised_balancing_difference", ""),
            "derivation_status": dstatus,
            "derivation_confidence": overall_conf,
        })

        payment_agg_rows.append({
            "reconstructed_claim_id": claim_id,
            "policy_number": header.get("policy_number", ""),
            "claim_family": header.get("claim_family", ""),
            "mpaycount_candidate": derived.get("MPAYCOUNT", pay_agg.get("payment_count", 0)),
            "mpaid_candidate": derived.get("MPAID", ""),
            "total_canonical_payments": pay_agg.get("payment_count", 0),
            "rulebook_ready_payments": pay_agg.get("rulebook_ready_payments", 0),
            "max_payout_date": pay_agg.get("max_payout_date", ""),
            "derivation_status": dstatus,
        })

        residual_amt = parse_amount(derived.get("MRESIDUAL", decomp.get("residual_amount", rev.get("revised_balancing_difference", 0))))
        if residual_amt != 0 or dstatus == "RESIDUAL_PENDING" or strip_val(rev.get("revised_balancing_status", "")) == "UNBALANCED":
            residual_rows.append({
                "reconstructed_claim_id": claim_id,
                "claim_family": header.get("claim_family", ""),
                "mresidual_candidate": derived.get("MRESIDUAL", ""),
                "decomposition_status": decomp.get("decomposition_status", ""),
                "balancing_status": rev.get("revised_balancing_status", ""),
                "residual_reason": decomp.get("decomposition_status", rev.get("balancing_notes", "")),
                "derivation_status": dstatus,
                "derivation_confidence": overall_conf,
            })

        gating_rows.append({
            "reconstructed_claim_id": claim_id,
            "derivation_status": dstatus,
            "derivation_confidence": overall_conf,
            "future_rulebook_ready": rb_ready,
            "manual_review_required": manual,
            "validation_issues": "|".join(val_issues),
            "gating_rationale": "Passes rulebook gate" if rb_ready == "Y" else "Review required",
        })

        validation_rows.append({
            "reconstructed_claim_id": claim_id,
            "claim_family": header.get("claim_family", ""),
            "derivation_status": dstatus,
            "validation_result": "PASS" if not val_issues else "REVIEW",
            "validation_issues": "|".join(val_issues),
            "rulebook_ready": rb_ready,
            "derivation_confidence": overall_conf,
        })

        candidates.append({
            "derivation_candidate_id": f"QDC-{claim_id}",
            "reconstructed_claim_id": claim_id,
            "policy_number": header.get("policy_number", ""),
            "enhanced_settlement_group_id": eg.get("enhanced_settlement_group_id", ""),
            "claim_family": header.get("claim_family", ""),
            "derivation_status": dstatus,
            "derivation_confidence": overall_conf,
            "future_rulebook_ready": rb_ready,
            "manual_review_required": manual,
            "production_dbf_flag": "N",
            **derived,
        })

    cand_df = pd.DataFrame(candidates).sort_values("reconstructed_claim_id").reset_index(drop=True)
    field_df = pd.DataFrame(field_rows).sort_values(["reconstructed_claim_id", "target_field"]).reset_index(drop=True)
    status_df = pd.DataFrame(status_rows).sort_values("reconstructed_claim_id").reset_index(drop=True)
    fin_df = pd.DataFrame(financial_rows).sort_values("reconstructed_claim_id").reset_index(drop=True)
    pay_df = pd.DataFrame(payment_agg_rows).sort_values("reconstructed_claim_id").reset_index(drop=True)
    residual_df = pd.DataFrame(residual_rows).sort_values("reconstructed_claim_id").reset_index(drop=True) if residual_rows else pd.DataFrame()
    gating_df = pd.DataFrame(gating_rows).sort_values("reconstructed_claim_id").reset_index(drop=True)
    val_df = pd.DataFrame(validation_rows).sort_values("reconstructed_claim_id").reset_index(drop=True)

    stats = {
        "total_claim_candidates": len(cand_df),
        "lifecycle_derivations": int((cand_df["derivation_status"] == "LIFECYCLE_DERIVATION").sum()),
        "financial_derivations": int((cand_df["derivation_status"] == "FINANCIAL_DERIVATION").sum()),
        "aggregated_payment": int((cand_df["derivation_status"] == "AGGREGATED_PAYMENT_DERIVATION").sum()),
        "residual_pending": int((cand_df["derivation_status"] == "RESIDUAL_PENDING").sum()),
        "inferred": int((cand_df["derivation_status"] == "INFERRED_DERIVATION").sum()),
        "rulebook_ready": int((cand_df["future_rulebook_ready"] == "Y").sum()),
        "manual_review": int((cand_df["manual_review_required"] == "Y").sum()),
        "residual_aware": len(residual_df),
        "status_distribution": cand_df["derivation_status"].value_counts().to_dict(),
        "confidence_distribution": cand_df["derivation_confidence"].value_counts().to_dict(),
        "family_distribution": cand_df["claim_family"].value_counts().to_dict(),
        "validation_pass": int((val_df["validation_result"] == "PASS").sum()),
        "validation_review": int((val_df["validation_result"] == "REVIEW").sum()),
    }

    if stats["rulebook_ready"] > 0:
        recommendations.append({
            "observed_pattern": f"{stats['rulebook_ready']} QUIKCLMS claim derivation candidates rulebook-ready",
            "root_cause": "Lifecycle + financial + payment aggregation lineage complete",
            "recommended_action": "Proceed to Phase 11 prototype DBF generation design",
            "expected_impact": "HIGH",
            "confidence_level": "HIGH_CONFIDENCE",
        })
    if stats["validation_review"] > 0:
        recommendations.append({
            "observed_pattern": f"{stats['validation_review']} claims flagged for validation review",
            "root_cause": "Unbalanced status or settled-without-payment detection",
            "recommended_action": "Review quikclms_derivation_validation.csv before prototype DBF",
            "expected_impact": "MEDIUM",
            "confidence_level": "MODERATE_CONFIDENCE",
        })
    if stats["residual_pending"] > 0:
        recommendations.append({
            "observed_pattern": f"{stats['residual_pending']} residual-pending claim derivations",
            "root_cause": "Death decomposition or balancing residuals remain",
            "recommended_action": "Cross-reference quikclms_residual_derivation_analysis.csv with Phase 7C",
            "expected_impact": "MEDIUM",
            "confidence_level": "INFERRED",
        })

    rec_df = pd.DataFrame(recommendations).reset_index(drop=True) if recommendations else pd.DataFrame()

    reports = {
        "quikclms_derivation_candidates.csv": cand_df,
        "quikclms_field_derivation_analysis.csv": field_df,
        "quikclms_claim_status_analysis.csv": status_df,
        "quikclms_financial_derivation_analysis.csv": fin_df,
        "quikclms_payment_aggregation_analysis.csv": pay_df,
        "quikclms_residual_derivation_analysis.csv": residual_df,
        "quikclms_confidence_gating_analysis.csv": gating_df,
        "quikclms_derivation_validation.csv": val_df,
        "quikclms_derivation_recommendations.csv": rec_df,
    }

    rules_out = os.path.join(output_dir, "quikclms_derivation_rules.json")
    shutil.copy2(rules_path, rules_out)
    output_files = [rules_out]

    for name, frame in reports.items():
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        output_files.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_txt = os.path.join(output_dir, "quikclms_derivation_summary.txt")
    write_summary_txt(summary_txt, stats, output_files)
    output_files.append(summary_txt)
    logger.info("Wrote quikclms_derivation_summary.txt")

    return stats, output_files


def write_summary_txt(path, stats, output_files):
    lines = [
        "=== QUIKCLMS Rulebook Derivation Design Summary (Phase 10B) ===",
        "",
        f"Total claim derivation candidates: {stats['total_claim_candidates']}",
        "",
        "Claim family distribution:",
    ]
    for fam, count in sorted(stats.get("family_distribution", {}).items()):
        lines.append(f"  {fam}: {count}")
    lines.extend([
        "",
        "Derivation status distribution:",
    ])
    for status, count in sorted(stats.get("status_distribution", {}).items()):
        lines.append(f"  {status}: {count}")
    lines.extend([
        "",
        "Key metrics:",
        f"  Lifecycle derivations: {stats['lifecycle_derivations']}",
        f"  Financial derivations: {stats['financial_derivations']}",
        f"  Aggregated payment derivations: {stats['aggregated_payment']}",
        f"  Residual pending: {stats['residual_pending']}",
        f"  Inferred derivations: {stats['inferred']}",
        f"  Rulebook-ready claims: {stats['rulebook_ready']}",
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
        "  - QUIKCLMS companion to Phase 10A QUIKCLMP derivation",
        "  - production_dbf_flag=N on all outputs",
        "  - JSON-driven field derivations",
        "",
        "Recommended next phase:",
        "  - Phase 11: Prototype DBF generation & QA/UAT reconciliation",
        "",
        "Output files generated:",
    ])
    for f in output_files:
        lines.append(f"  - {f}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Phase 10B QUIKCLMS rulebook derivation engine.")
    parser.add_argument("--headers", default=os.path.join(PHASE4, "claim_candidate_header.csv"))
    parser.add_argument("--financials", default=os.path.join(PHASE4, "claim_candidate_financials.csv"))
    parser.add_argument("--revised-financials", default=os.path.join(PHASE6, "revised_claim_financials.csv"))
    parser.add_argument("--decomposition", default=os.path.join(PHASE7C, "death_claim_decomposition_summary.csv"))
    parser.add_argument("--enhanced-groups", default=os.path.join(PHASE7B, "enhanced_settlement_groups.csv"))
    parser.add_argument("--payment-stage", default=os.path.join(PHASE9, "canonical_claim_payment_stage.csv"))
    parser.add_argument("--quikclmp-candidates", default=os.path.join(PHASE10A, "quikclmp_derivation_candidates.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")

    for label, path in (("Headers", args.headers), ("Financials", args.financials), ("Rules", args.rules)):
        if not os.path.isfile(path):
            logger.error("%s not found: %s", label, path)
            return 1

    headers = load_csv(args.headers)
    financials = load_csv(args.financials)
    revised_fin = load_csv(args.revised_financials) if os.path.isfile(args.revised_financials) else pd.DataFrame()
    decomp_summary = load_csv(args.decomposition) if os.path.isfile(args.decomposition) else pd.DataFrame()
    enhanced_groups = load_csv(args.enhanced_groups) if os.path.isfile(args.enhanced_groups) else pd.DataFrame()
    payment_stage = load_csv(args.payment_stage) if os.path.isfile(args.payment_stage) else pd.DataFrame()
    quikclmp_candidates = load_csv(args.quikclmp_candidates) if os.path.isfile(args.quikclmp_candidates) else pd.DataFrame()

    try:
        stats, outputs = run_engine(
            headers, financials, revised_fin, decomp_summary, enhanced_groups,
            payment_stage, quikclmp_candidates, args.rules, args.output,
        )
        print(f"QUIKCLMS derivation design complete. Claims: {stats['total_claim_candidates']}")
        print(f"Rulebook ready: {stats['rulebook_ready']}")
        print(f"Validation review: {stats['validation_review']}")
        print(f"Output: {os.path.abspath(args.output)}")
        for p in outputs:
            print(f"  {p}")
        return 0
    except (ValueError, FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
