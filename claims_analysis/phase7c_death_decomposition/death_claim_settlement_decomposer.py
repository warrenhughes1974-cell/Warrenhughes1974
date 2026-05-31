#!/usr/bin/env python3
"""
Phase 7C — Death claim settlement decomposition engine (read-only).

Decomposes DEATH_CLAIM settlement layers and explains partial/multi-payout patterns.
Does NOT modify app.py, prior phase outputs, or generate QUIKCLMS/QUIKCLMP DBFs.
"""

import argparse
import json
import logging
import os
import re
import shutil
from collections import defaultdict

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_RULES = os.path.join(ROOT, "config", "death_claim_decomposition_rules.json")
DEFAULT_BALANCING_RULES = os.path.join(ROOT, "config", "claim_family_balancing_rules.json")
DEFAULT_SETTLEMENT_RULES = os.path.join(ROOT, "config", "settlement_chain_rules.json")
PHASE4 = os.path.join(ROOT, "phase4_claim_event_reconstruction")
PHASE6 = os.path.join(ROOT, "phase6_family_balancing_intelligence")
PHASE7A = os.path.join(ROOT, "phase7_settlement_chain_intelligence")
PHASE7B = os.path.join(ROOT, "phase7b_cross_claim_linkage")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase7c_death_claim_decomposition")

logger = logging.getLogger("death_claim_decomposer")


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


def format_tx_code(value):
    digits = re.sub(r"[^0-9]", "", str(value))
    if not digits:
        return ""
    return str(int(digits)).zfill(4)


def parse_amount(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0.0
    raw = str(value).strip().replace(",", "").replace("$", "")
    if not raw:
        return 0.0
    if raw.startswith("."):
        raw = "0" + raw
    if raw.startswith("-."):
        raw = "-0" + raw[1:]
    try:
        return float(raw)
    except ValueError:
        return 0.0


def sum_codes(events, codes):
    if events.empty or not codes:
        return 0.0
    allowed = {format_tx_code(c) for c in codes}
    mask = events["source_transaction_code"].apply(lambda c: format_tx_code(c) in allowed)
    return round(float(events.loc[mask, "amount_parsed"].sum()), 2)


def count_events(events, codes):
    if events.empty or not codes:
        return 0
    allowed = {format_tx_code(c) for c in codes}
    mask = events["source_transaction_code"].apply(lambda c: format_tx_code(c) in allowed)
    return int(mask.sum())


def present_codes(events, codes):
    return sorted({
        format_tx_code(c)
        for c in events["source_transaction_code"].tolist()
        if format_tx_code(c) in {format_tx_code(x) for x in codes}
    })


def layer_amounts(events, rules):
    layers = rules.get("layers", {})
    result = {}
    for key, cfg in layers.items():
        result[key] = sum_codes(events, cfg.get("codes", []))
    return result


def prepare_detail(detail, rules):
    df = detail.copy()
    df["source_transaction_code"] = df["source_transaction_code"].apply(format_tx_code)
    df["amount_parsed"] = df["trans_amount"].apply(parse_amount)
    exclude = set(rules.get("exclude_lifecycle_event_types", ["CLAIM_SETTLEMENT"]))
    if "lifecycle_event_type" in df.columns:
        df = df[~df["lifecycle_event_type"].isin(exclude)]
    return df


def expected_net(layer_totals):
    return round(
        layer_totals.get("funding", 0)
        + layer_totals.get("interest", 0)
        - layer_totals.get("offset", 0)
        - layer_totals.get("surrender_charge", 0)
        - layer_totals.get("withholding", 0),
        2,
    )


def residual_amount(expected, payout):
    return round(expected - payout, 2)


def is_balanced(diff, rules):
    return abs(diff) <= rules.get("balance_tolerance", 0.01)


def is_minor_variance(diff, rules):
    return abs(diff) <= rules.get("residual_tolerance", 100.0)


def detect_pattern(funding_count, payout_count):
    if funding_count == 0 and payout_count == 0:
        return "CLEARING_ONLY"
    if funding_count == 0 and payout_count > 0:
        return "PAYOUT_ONLY"
    if funding_count > 0 and payout_count == 0:
        return "FUNDING_ONLY"
    if funding_count == 1 and payout_count == 1:
        return "ONE_FUNDING_ONE_PAYOUT"
    if funding_count == 1 and payout_count > 1:
        return "ONE_FUNDING_MANY_PAYOUTS"
    if funding_count > 1 and payout_count == 1:
        return "MANY_FUNDING_ONE_PAYOUT"
    if funding_count > 1 and payout_count > 1:
        return "MANY_FUNDING_MANY_PAYOUTS"
    return "UNKNOWN"


def component_completeness(layer_totals, payout_count):
    core = ["funding", "payout"]
    optional = ["interest", "offset", "withholding"]
    score = 0.0
    total_weight = len(core) + len(optional)
    for key in core:
        if key == "payout" and payout_count > 0:
            score += 1
        elif layer_totals.get(key, 0) != 0:
            score += 1
    for key in optional:
        if layer_totals.get(key, 0) != 0:
            score += 1
        else:
            score += 0.5
    return round(score / total_weight, 2)


def classify_decomposition_status(
    layer_totals, payout_count, residual, clearing_total, chain_status,
    balancing_status, rules,
):
    gap_rules = rules.get("gap_explanation_rules", {})
    tol = rules.get("balance_tolerance", 0.01)
    abs_res = abs(residual)

    if clearing_total > 0 and layer_totals.get("funding", 0) == 0 and layer_totals.get("payout", 0) == 0:
        return "CLEARING_ONLY_DISTORTION"

    if payout_count >= rules.get("business_rules", {}).get("multi_payout_payee_analysis_threshold", 2):
        if not is_balanced(residual, rules):
            if abs_res > tol:
                return "NEEDS_PAYEE_DISTRIBUTION_ANALYSIS"

    if is_balanced(residual, rules) and balancing_status == "BALANCED":
        if payout_count <= 1:
            return "FULLY_DECOMPOSED"
        return "MULTI_PAYOUT_DECOMPOSED"

    offset = layer_totals.get("offset", 0)
    interest = layer_totals.get("interest", 0)
    withholding = layer_totals.get("withholding", 0)
    expected = expected_net(layer_totals)

    if offset > 0 and abs_res > 0:
        if abs(offset - abs_res) <= max(tol, abs_res * (1 - gap_rules.get("offset_explains_gap_threshold", 0.9))):
            return "OFFSET_EXPLAINS_GAP"
        if abs(expected + offset - layer_totals.get("payout", 0)) <= rules.get("residual_tolerance", 100.0):
            return "OFFSET_EXPLAINS_GAP"

    if interest > 0 and abs_res > 0:
        if abs(interest - abs_res) <= max(tol, abs_res * 0.15):
            return "INTEREST_EXPLAINS_GAP"

    if withholding > 0 and abs_res > 0:
        if abs(withholding - abs_res) <= max(tol, abs_res * 0.15):
            return "WITHHOLDING_EXPLAINS_GAP"

    if clearing_total > 0 and abs_res > 0:
        ratio = gap_rules.get("clearing_distortion_ratio", 0.5)
        if clearing_total >= abs_res * ratio and chain_status == "PARTIAL_CHAIN":
            return "CLEARING_ONLY_DISTORTION"

    if chain_status in {"PARTIAL_CHAIN", "FUNDED_NO_DISBURSEMENT"}:
        return "PARTIAL_DECOMPOSITION"

    if payout_count >= 2 and not is_balanced(residual, rules):
        return "MULTI_PAYOUT_DECOMPOSED"

    if abs_res > tol:
        return "RESIDUAL_REMAINS"

    return "PARTIAL_DECOMPOSITION"


def score_confidence(
    decomp_status, layer_totals, payout_count, residual, balancing_status,
    completeness, enhanced_group_linked, rules,
):
    scoring = rules.get("confidence_scoring", {})
    abs_res = abs(residual)

    if decomp_status == "FULLY_DECOMPOSED" and balancing_status == "BALANCED":
        return "HIGH_CONFIDENCE", "All core layers present; settlement fully decomposed and balanced"

    if decomp_status == "MULTI_PAYOUT_DECOMPOSED" and is_balanced(residual, rules):
        return "MODERATE_CONFIDENCE", "Multi-payout pattern decomposed with balanced residual"

    if decomp_status in {"OFFSET_EXPLAINS_GAP", "INTEREST_EXPLAINS_GAP", "WITHHOLDING_EXPLAINS_GAP"}:
        return "MODERATE_CONFIDENCE", f"Gap explained by {decomp_status.replace('_EXPLAINS_GAP', '').lower()} layer"

    if decomp_status == "CLEARING_ONLY_DISTORTION":
        return "INFERRED", "0038 clearing present; excluded from financial rollup but may affect chain perception"

    if decomp_status == "NEEDS_PAYEE_DISTRIBUTION_ANALYSIS":
        return "INFERRED", "Multi-payout split requires future payee distribution analysis"

    if completeness >= scoring.get("MODERATE_CONFIDENCE", {}).get("requires_component_completeness", 0.75):
        if enhanced_group_linked:
            return "MODERATE_CONFIDENCE", "Component completeness strong; Phase 7B enhanced group available"
        return "MODERATE_CONFIDENCE", "Component completeness adequate for partial decomposition"

    if abs_res > rules.get("residual_tolerance", 100.0) or layer_totals.get("funding", 0) == 0:
        return "LOW_CONFIDENCE", "Large residual or missing funding layer"

    return "INFERRED", "Rule-based default decomposition inference"


def gap_direction(residual):
    if abs(residual) <= 0.01:
        return "NONE"
    return "PAYOUT_SHORTFALL" if residual > 0 else "PAYOUT_EXCESS"


def is_focus_record(chain_status, chain_conf, balancing_status, rules):
    focus_statuses = set(rules.get("focus_chain_statuses", []))
    focus_conf = set(rules.get("focus_confidence_levels", []))
    if chain_status in focus_statuses:
        return "Y"
    if chain_conf in focus_conf:
        return "Y"
    if balancing_status not in {"BALANCED"}:
        return "Y"
    return "N"


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def run_engine(
    headers, financials, revised_fin, chain_summary, chain_detail,
    multi_payout, enhanced_groups, enhanced_balancing,
    balancing_rules_path, settlement_rules_path, rules_path, output_dir,
):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    balancing_rules = load_json(balancing_rules_path)
    death_profile = balancing_rules.get("families", {}).get("DEATH_CLAIM", {})

    detail = prepare_detail(chain_detail, rules)
    death_ids = set(
        headers.loc[headers["claim_family"] == "DEATH_CLAIM", "reconstructed_claim_id"].tolist()
    )
    detail = detail[detail["reconstructed_claim_id"].isin(death_ids)]

    header_map = headers.set_index("reconstructed_claim_id").to_dict("index")
    fin_map = financials.set_index("reconstructed_claim_id").to_dict("index")
    rev_map = revised_fin.set_index("reconstructed_claim_id").to_dict("index")
    chain_map = chain_summary.set_index("reconstructed_claim_id").to_dict("index")
    eg_map = enhanced_groups.set_index("reconstructed_claim_id").to_dict("index") if not enhanced_groups.empty else {}
    eb_map = enhanced_balancing.set_index("reconstructed_claim_id").to_dict("index") if not enhanced_balancing.empty else {}

    layer_defs = rules.get("layers", {})
    funding_codes = layer_defs.get("funding", {}).get("codes", [])
    payout_codes = layer_defs.get("payout", {}).get("codes", [])

    summaries = []
    component_rows = []
    multi_rows = []
    partial_rows = []
    residual_rows = []
    oiw_rows = []
    recommendations = []

    for claim_id in sorted(death_ids):
        header = header_map.get(claim_id, {})
        events = detail[detail["reconstructed_claim_id"] == claim_id].sort_values("lifecycle_event_order")
        chain = chain_map.get(claim_id, {})
        rev = rev_map.get(claim_id, {})
        orig = fin_map.get(claim_id, {})
        eg = eg_map.get(claim_id, {})
        eb = eb_map.get(claim_id, {})

        layers = layer_amounts(events, rules)
        funding_count = count_events(events, funding_codes)
        payout_count = count_events(events, payout_codes)
        pattern = detect_pattern(funding_count, payout_count)

        expected = expected_net(layers)
        payout_total = layers.get("payout", 0)
        residual = residual_amount(expected, payout_total)
        clearing_total = layers.get("clearing", 0)

        chain_status = chain.get("chain_status", "")
        chain_conf = chain.get("confidence_level", "")
        balancing_status = rev.get("revised_balancing_status", orig.get("balancing_status", ""))
        enhanced_status = eb.get("enhanced_balancing_status", balancing_status)
        enhanced_linked = eg.get("linked_target_claim_id", "") or eg.get("linked_source_claim_id", "")

        decomp_status = classify_decomposition_status(
            layers, payout_count, residual, clearing_total, chain_status,
            balancing_status, rules,
        )
        completeness = component_completeness(layers, payout_count)
        conf, conf_reason = score_confidence(
            decomp_status, layers, payout_count, residual, balancing_status,
            completeness, bool(enhanced_linked), rules,
        )
        focus_flag = is_focus_record(chain_status, chain_conf, balancing_status, rules)

        summaries.append({
            "reconstructed_claim_id": claim_id,
            "policy_number": header.get("policy_number", ""),
            "chain_status": chain_status,
            "decomposition_status": decomp_status,
            "settlement_pattern": pattern,
            "confidence_level": conf,
            "confidence_rationale": conf_reason,
            "focus_population_flag": focus_flag,
            "funding_total": layers.get("funding", 0),
            "interest_total": layers.get("interest", 0),
            "offset_total": layers.get("offset", 0),
            "withholding_total": layers.get("withholding", 0),
            "payout_total": payout_total,
            "clearing_total": clearing_total,
            "surrender_charge_total": layers.get("surrender_charge", 0),
            "expected_net_payment": expected,
            "residual_amount": residual,
            "gap_direction": gap_direction(residual),
            "funding_event_count": funding_count,
            "payout_event_count": payout_count,
            "component_completeness": completeness,
            "phase6_balancing_status": balancing_status,
            "phase7b_enhanced_balancing_status": enhanced_status,
            "enhanced_settlement_group_id": eg.get("enhanced_settlement_group_id", ""),
            "revised_balancing_difference": rev.get("revised_balancing_difference", ""),
            "decomposition_notes": death_profile.get("settlement_chain_guidance", ""),
        })

        for layer_key, cfg in layer_defs.items():
            codes = cfg.get("codes", [])
            layer_events = events[
                events["source_transaction_code"].apply(
                    lambda c: format_tx_code(c) in {format_tx_code(x) for x in codes}
                )
            ]
            component_rows.append({
                "reconstructed_claim_id": claim_id,
                "policy_number": header.get("policy_number", ""),
                "layer_name": layer_key,
                "layer_label": cfg.get("label", layer_key),
                "layer_codes": "|".join(codes),
                "layer_total": layers.get(layer_key, 0),
                "event_count": len(layer_events),
                "codes_present": "|".join(present_codes(events, codes)),
                "exclude_from_financial_rollup": "Y" if cfg.get("exclude_from_financial_rollup") else "N",
                "decomposition_status": decomp_status,
            })

        if payout_count >= 2 or chain_status == "MULTI_PAYOUT_CHAIN":
            payout_events = events[
                events["source_transaction_code"].apply(
                    lambda c: format_tx_code(c) in {format_tx_code(x) for x in payout_codes}
                )
            ]
            payout_by_code = payout_events.groupby("source_transaction_code")["amount_parsed"].sum().to_dict()
            multi_rows.append({
                "reconstructed_claim_id": claim_id,
                "policy_number": header.get("policy_number", ""),
                "payout_event_count": payout_count,
                "payout_total": payout_total,
                "funding_total": layers.get("funding", 0),
                "interest_total": layers.get("interest", 0),
                "offset_total": layers.get("offset", 0),
                "residual_amount": residual,
                "settlement_pattern": pattern,
                "decomposition_status": decomp_status,
                "staged_settlement_flag": "Y" if payout_count >= 2 else "N",
                "beneficiary_distribution_ready": "FUTURE",
                "payout_code_breakdown": "|".join(f"{k}:{round(v,2)}" for k, v in sorted(payout_by_code.items())),
                "confidence_level": conf,
                "notes": "Multi-payout may represent beneficiaries or staged payments; payee analysis not yet applied",
            })

        if chain_status == "PARTIAL_CHAIN" or decomp_status in {
            "PARTIAL_DECOMPOSITION", "RESIDUAL_REMAINS", "CLEARING_ONLY_DISTORTION",
        }:
            partial_rows.append({
                "reconstructed_claim_id": claim_id,
                "policy_number": header.get("policy_number", ""),
                "chain_status": chain_status,
                "decomposition_status": decomp_status,
                "funding_total": layers.get("funding", 0),
                "payout_total": payout_total,
                "clearing_total": clearing_total,
                "expected_net_payment": expected,
                "residual_amount": residual,
                "gap_direction": gap_direction(residual),
                "clearing_distortion_flag": "Y" if clearing_total > 0 and abs(residual) > 0 else "N",
                "confidence_level": conf,
                "partial_chain_notes": (
                    "0038 clearing excluded from rollup; gap may reflect benefit/payout pairing"
                    if clearing_total > 0 else "Funding/payout amounts diverge beyond tolerance"
                ),
            })

        if abs(residual) > rules.get("balance_tolerance", 0.01):
            unexplained = residual
            if layers.get("offset", 0) > 0 and decomp_status != "OFFSET_EXPLAINS_GAP":
                unexplained = round(residual + layers.get("offset", 0), 2)
            residual_rows.append({
                "reconstructed_claim_id": claim_id,
                "policy_number": header.get("policy_number", ""),
                "residual_amount": residual,
                "unexplained_residual": unexplained,
                "gap_direction": gap_direction(residual),
                "expected_net_payment": expected,
                "payout_total": payout_total,
                "clearing_total": clearing_total,
                "decomposition_status": decomp_status,
                "residual_explained_by": (
                    decomp_status.replace("_EXPLAINS_GAP", "").lower()
                    if "EXPLAINS_GAP" in decomp_status else "none"
                ),
                "confidence_level": conf,
            })

        if any(layers.get(k, 0) != 0 for k in ("offset", "interest", "withholding")):
            oiw_rows.append({
                "reconstructed_claim_id": claim_id,
                "policy_number": header.get("policy_number", ""),
                "offset_total": layers.get("offset", 0),
                "interest_total": layers.get("interest", 0),
                "withholding_total": layers.get("withholding", 0),
                "offset_codes": "|".join(present_codes(events, layer_defs.get("offset", {}).get("codes", []))),
                "interest_codes": "|".join(present_codes(events, layer_defs.get("interest", {}).get("codes", []))),
                "withholding_codes": "|".join(present_codes(events, layer_defs.get("withholding", {}).get("codes", []))),
                "residual_amount": residual,
                "offset_explains_gap": "Y" if decomp_status == "OFFSET_EXPLAINS_GAP" else "N",
                "interest_explains_gap": "Y" if decomp_status == "INTEREST_EXPLAINS_GAP" else "N",
                "withholding_explains_gap": "Y" if decomp_status == "WITHHOLDING_EXPLAINS_GAP" else "N",
                "decomposition_status": decomp_status,
            })

    summary_df = pd.DataFrame(summaries).sort_values("reconstructed_claim_id").reset_index(drop=True)
    component_df = pd.DataFrame(component_rows).sort_values(
        ["reconstructed_claim_id", "layer_name"],
    ).reset_index(drop=True)
    multi_df = pd.DataFrame(multi_rows).sort_values("reconstructed_claim_id").reset_index(drop=True) if multi_rows else pd.DataFrame()
    partial_df = pd.DataFrame(partial_rows).sort_values("reconstructed_claim_id").reset_index(drop=True) if partial_rows else pd.DataFrame()
    residual_df = pd.DataFrame(residual_rows).sort_values(
        "residual_amount", key=lambda s: s.apply(lambda x: abs(parse_amount(x))), ascending=False,
    ).reset_index(drop=True) if residual_rows else pd.DataFrame()
    oiw_df = pd.DataFrame(oiw_rows).sort_values("reconstructed_claim_id").reset_index(drop=True) if oiw_rows else pd.DataFrame()

    status_counts = summary_df["decomposition_status"].value_counts()
    if int(status_counts.get("NEEDS_PAYEE_DISTRIBUTION_ANALYSIS", 0)) > 0:
        recommendations.append({
            "observed_pattern": f"{int(status_counts.get('NEEDS_PAYEE_DISTRIBUTION_ANALYSIS', 0))} multi-payout death claims with unexplained residual",
            "root_cause": "Beneficiary or staged payment split not yet modeled",
            "recommended_action": "Integrate PRELSA payee distribution in Phase 8 (future-ready)",
            "expected_impact": "MEDIUM",
            "confidence_level": "MODERATE_CONFIDENCE",
        })
    if int(status_counts.get("CLEARING_ONLY_DISTORTION", 0)) > 0:
        recommendations.append({
            "observed_pattern": f"{int(status_counts.get('CLEARING_ONLY_DISTORTION', 0))} claims with 0038 clearing distortion signal",
            "root_cause": "0038 lifecycle hub inflates chain perception but is excluded from net rollup",
            "recommended_action": "Continue excluding 0038 from financial decomposition; use for lineage only",
            "expected_impact": "LOW",
            "confidence_level": "HIGH_CONFIDENCE",
        })
    if int(status_counts.get("RESIDUAL_REMAINS", 0)) > 0:
        recommendations.append({
            "observed_pattern": f"{int(status_counts.get('RESIDUAL_REMAINS', 0))} death claims with unexplained residual",
            "root_cause": "Benefit/payout pairing or missing optional components",
            "recommended_action": "Review largest residuals in death_claim_residual_analysis.csv",
            "expected_impact": "HIGH",
            "confidence_level": "MODERATE_CONFIDENCE",
        })
    if int(status_counts.get("PARTIAL_DECOMPOSITION", 0)) > 0:
        recommendations.append({
            "observed_pattern": f"{int(status_counts.get('PARTIAL_DECOMPOSITION', 0))} partial decompositions",
            "root_cause": "Incomplete funding/payout pairing within reconstruction group",
            "recommended_action": "Evaluate sibling DEATH_CLAIM groups on same policy for split funding/payout",
            "expected_impact": "MEDIUM",
            "confidence_level": "INFERRED",
        })

    rec_df = pd.DataFrame(recommendations).reset_index(drop=True) if recommendations else pd.DataFrame()

    residuals = summary_df["residual_amount"].apply(parse_amount)
    stats = {
        "total_death_claims": len(summary_df),
        "focus_population": int((summary_df["focus_population_flag"] == "Y").sum()),
        "fully_decomposed": int((summary_df["decomposition_status"] == "FULLY_DECOMPOSED").sum()),
        "multi_payout_decomposed": int((summary_df["decomposition_status"] == "MULTI_PAYOUT_DECOMPOSED").sum()),
        "partial_decomposition": int((summary_df["decomposition_status"] == "PARTIAL_DECOMPOSITION").sum()),
        "offset_explains_gap": int((summary_df["decomposition_status"] == "OFFSET_EXPLAINS_GAP").sum()),
        "interest_explains_gap": int((summary_df["decomposition_status"] == "INTEREST_EXPLAINS_GAP").sum()),
        "withholding_explains_gap": int((summary_df["decomposition_status"] == "WITHHOLDING_EXPLAINS_GAP").sum()),
        "residual_remains": int((summary_df["decomposition_status"] == "RESIDUAL_REMAINS").sum()),
        "clearing_distortion": int((summary_df["decomposition_status"] == "CLEARING_ONLY_DISTORTION").sum()),
        "needs_payee_analysis": int((summary_df["decomposition_status"] == "NEEDS_PAYEE_DISTRIBUTION_ANALYSIS").sum()),
        "avg_residual": round(float(residuals.abs().mean()), 2),
        "largest_residual": round(float(residuals.abs().max()), 2),
        "payout_count_distribution": summary_df["payout_event_count"].value_counts().to_dict(),
        "completeness_distribution": summary_df["component_completeness"].value_counts().sort_index().to_dict(),
        "confidence_distribution": summary_df["confidence_level"].value_counts().to_dict(),
        "status_distribution": status_counts.to_dict(),
        "pattern_distribution": summary_df["settlement_pattern"].value_counts().to_dict(),
    }

    reports = {
        "death_claim_decomposition_summary.csv": summary_df,
        "death_claim_component_layers.csv": component_df,
        "death_claim_multi_payout_analysis.csv": multi_df,
        "death_claim_partial_chain_analysis.csv": partial_df,
        "death_claim_residual_analysis.csv": residual_df,
        "death_claim_offset_interest_withholding_analysis.csv": oiw_df,
        "death_claim_decomposition_recommendations.csv": rec_df,
    }

    rules_out = os.path.join(output_dir, "death_claim_decomposition_rules.json")
    shutil.copy2(rules_path, rules_out)
    output_files = [rules_out]

    for name, frame in reports.items():
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        output_files.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_txt = os.path.join(output_dir, "death_claim_decomposition_summary.txt")
    write_summary_txt(summary_txt, stats, summary_df, output_files)
    output_files.append(summary_txt)
    logger.info("Wrote death_claim_decomposition_summary.txt")

    return stats, output_files


def write_summary_txt(path, stats, summary_df, output_files):
    lines = [
        "=== Death Claim Settlement Decomposition Summary (Phase 7C) ===",
        "",
        f"Total DEATH_CLAIM analyzed: {stats['total_death_claims']}",
        f"Focus population (partial/multi/unbalanced): {stats['focus_population']}",
        "",
        "Decomposition status distribution:",
    ]
    for status, count in sorted(stats.get("status_distribution", {}).items()):
        lines.append(f"  {status}: {count}")
    lines.extend([
        "",
        "Key metrics:",
        f"  Fully decomposed: {stats['fully_decomposed']}",
        f"  Multi-payout decomposed: {stats['multi_payout_decomposed']}",
        f"  Partial decompositions: {stats['partial_decomposition']}",
        f"  Offset-explained gaps: {stats['offset_explains_gap']}",
        f"  Interest-explained gaps: {stats['interest_explains_gap']}",
        f"  Withholding-explained gaps: {stats['withholding_explains_gap']}",
        f"  Residual remains: {stats['residual_remains']}",
        f"  Clearing-only distortion: {stats['clearing_distortion']}",
        f"  Needs payee distribution analysis: {stats['needs_payee_analysis']}",
        f"  Average |residual|: {stats['avg_residual']}",
        f"  Largest |residual|: {stats['largest_residual']}",
        "",
        "Settlement pattern distribution:",
    ])
    for pattern, count in sorted(stats.get("pattern_distribution", {}).items()):
        lines.append(f"  {pattern}: {count}")
    lines.extend([
        "",
        "Confidence distribution:",
    ])
    for level, count in sorted(stats.get("confidence_distribution", {}).items()):
        lines.append(f"  {level}: {count}")
    lines.extend([
        "",
        "Phase 6 balancing on death claims:",
    ])
    for status, count in summary_df["phase6_balancing_status"].value_counts().items():
        lines.append(f"  {status}: {count}")
    lines.extend([
        "",
        "Architectural notes:",
        "  - 0038 clearing excluded from financial rollup on all layers",
        "  - No Phase 4/6/7A/7B outputs modified",
        "  - No QUIKCLMS/QUIKCLMP generation",
        "",
        "Recommended next phase:",
        "  - Phase 8: PRELSA payee distribution linkage for NEEDS_PAYEE_DISTRIBUTION_ANALYSIS claims",
        "",
        "Output files generated:",
    ])
    for f in output_files:
        lines.append(f"  - {f}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Phase 7C death claim settlement decomposer.")
    parser.add_argument("--headers", default=os.path.join(PHASE4, "claim_candidate_header.csv"))
    parser.add_argument("--financials", default=os.path.join(PHASE4, "claim_candidate_financials.csv"))
    parser.add_argument("--revised-financials", default=os.path.join(PHASE6, "revised_claim_financials.csv"))
    parser.add_argument("--chain-summary", default=os.path.join(PHASE7A, "settlement_chain_summary.csv"))
    parser.add_argument("--chain-detail", default=os.path.join(PHASE7A, "settlement_chain_detail.csv"))
    parser.add_argument("--multi-payout", default=os.path.join(PHASE7A, "multi_payout_chain_analysis.csv"))
    parser.add_argument("--enhanced-groups", default=os.path.join(PHASE7B, "enhanced_settlement_groups.csv"))
    parser.add_argument("--enhanced-balancing", default=os.path.join(PHASE7B, "enhanced_balancing_impact.csv"))
    parser.add_argument("--balancing-rules", default=DEFAULT_BALANCING_RULES)
    parser.add_argument("--settlement-rules", default=DEFAULT_SETTLEMENT_RULES)
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    required = (
        ("Headers", args.headers),
        ("Financials", args.financials),
        ("Revised financials", args.revised_financials),
        ("Chain summary", args.chain_summary),
        ("Chain detail", args.chain_detail),
        ("Rules", args.rules),
        ("Balancing rules", args.balancing_rules),
    )
    for label, path in required:
        if not os.path.isfile(path):
            logger.error("%s not found: %s", label, path)
            return 1

    headers = load_csv(args.headers)
    financials = load_csv(args.financials)
    revised_fin = load_csv(args.revised_financials)
    chain_summary = load_csv(args.chain_summary)
    chain_detail = load_csv(args.chain_detail)
    multi_payout = load_csv(args.multi_payout) if os.path.isfile(args.multi_payout) else pd.DataFrame()
    enhanced_groups = load_csv(args.enhanced_groups) if os.path.isfile(args.enhanced_groups) else pd.DataFrame()
    enhanced_balancing = load_csv(args.enhanced_balancing) if os.path.isfile(args.enhanced_balancing) else pd.DataFrame()

    try:
        stats, outputs = run_engine(
            headers, financials, revised_fin, chain_summary, chain_detail,
            multi_payout, enhanced_groups, enhanced_balancing,
            args.balancing_rules, args.settlement_rules, args.rules, args.output,
        )
        print(f"Death claim decomposition complete. Claims: {stats['total_death_claims']}")
        print(f"Focus population: {stats['focus_population']}")
        print(f"Residual remains: {stats['residual_remains']}")
        print(f"Output: {os.path.abspath(args.output)}")
        for p in outputs:
            print(f"  {p}")
        return 0
    except (ValueError, FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
