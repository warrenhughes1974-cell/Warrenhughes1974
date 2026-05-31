#!/usr/bin/env python3
"""
Phase 6 — Claim family balancing rule engine (read-only validation).

Applies configurable family-specific balancing rules to Phase 4 reconstruction
outputs. Does NOT modify app.py or generate QUIKCLMS/QUIKCLMP output.
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
DEFAULT_RULES = os.path.join(ROOT, "config", "claim_family_balancing_rules.json")
DEFAULT_PHASE4 = os.path.join(ROOT, "phase4_claim_event_reconstruction")

BALANCE_TOLERANCE = 0.01
MINOR_VARIANCE = 100.0
EXCLUDED_LIFECYCLE_EVENTS = {"CLAIM_SETTLEMENT"}

logger = logging.getLogger("claim_family_balancing")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_csv(path):
    df = pd.read_csv(path, dtype=str)
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def load_rules(path):
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
    if not raw or set(raw.replace("-", "").replace(".", "")) == set():
        return 0.0
    if raw.startswith("."):
        raw = "0" + raw
    if raw.startswith("-."):
        raw = "-0" + raw[1:]
    try:
        return float(raw)
    except ValueError:
        return 0.0


def balancing_status(diff):
    ad = abs(diff)
    if ad <= BALANCE_TOLERANCE:
        return "BALANCED"
    if ad <= MINOR_VARIANCE:
        return "MINOR_VARIANCE"
    return "UNBALANCED"


def code_in_list(code, codes):
    return format_tx_code(code) in {format_tx_code(c) for c in codes}


def sum_code_amounts(sub, codes):
    if sub.empty or not codes:
        return 0.0
    allowed = {format_tx_code(c) for c in codes}
    mask = sub["source_transaction_code"].apply(lambda c: format_tx_code(c) in allowed)
    return round(float(sub.loc[mask, "amount_parsed"].sum()), 2)


def present_codes(sub, codes):
    found = sorted({
        format_tx_code(c)
        for c in sub["source_transaction_code"].tolist()
        if code_in_list(c, codes)
    })
    return found


def classify_amounts(sub, profile):
    lifecycle_only = sum_code_amounts(sub, profile.get("lifecycle_only_codes", []))
    excluded = sum_code_amounts(sub, profile.get("excluded_from_net_rollup_codes", []))
    gross = sum_code_amounts(sub, profile.get("gross_component_codes", []))
    interest = sum_code_amounts(sub, profile.get("interest_component_codes", []))
    loan_total = sum_code_amounts(sub, profile.get("offset_component_codes", []))
    surrender = sum_code_amounts(sub, profile.get("surrender_charge_codes", []))
    withholding = sum_code_amounts(sub, profile.get("withholding_component_codes", []))
    payout = sum_code_amounts(sub, profile.get("payout_component_codes", []))
    return {
        "gross": gross,
        "interest": interest,
        "loan_offsets": loan_total,
        "loan_principal": sum_code_amounts(sub, ["0411"]),
        "loan_interest": sum_code_amounts(sub, ["0412"]),
        "surrender_charge": surrender,
        "withholding": withholding,
        "payout": payout,
        "lifecycle_only": lifecycle_only,
        "excluded_from_net": excluded,
    }


def apply_family_formula(family, amounts, profile):
    if profile.get("payment_event_only"):
        net = amounts["payout"]
        return net, 0.0, amounts["payout"]

    net = round(
        amounts["gross"]
        + amounts["interest"]
        - amounts["loan_offsets"]
        - amounts["surrender_charge"]
        - amounts["withholding"],
        2,
    )

    if profile.get("offset_only_chain_net_zero"):
        has_gross = amounts["gross"] != 0
        has_payout = amounts["payout"] != 0
        has_offset = amounts["loan_offsets"] != 0 or amounts["surrender_charge"] != 0
        if has_offset and not has_gross and not has_payout:
            net = 0.0

    diff = round(net - amounts["payout"], 2)
    return net, diff, amounts["payout"]


def prepare_lifecycle(lifecycle):
    life = lifecycle.copy()
    life["source_transaction_code"] = life["source_transaction_code"].apply(format_tx_code)
    life["amount_parsed"] = life["trans_amount"].apply(parse_amount)
    life = life[~life["lifecycle_event_type"].isin(EXCLUDED_LIFECYCLE_EVENTS)]
    return life


# ---------------------------------------------------------------------------
# Per-claim processing
# ---------------------------------------------------------------------------

def process_claim(claim_id, header, original_fin, life_sub, profile, family):
    amounts = classify_amounts(life_sub, profile)
    net, diff, payout = apply_family_formula(family, amounts, profile)
    status = balancing_status(diff)

    optional = profile.get("optional_components", [])
    codes_present = set(life_sub["source_transaction_code"].tolist())
    optional_present = [format_tx_code(c) for c in optional if format_tx_code(c) in codes_present]
    optional_missing = [format_tx_code(c) for c in optional if format_tx_code(c) not in codes_present]

    excluded_codes = present_codes(life_sub, profile.get("excluded_from_net_rollup_codes", []))
    lifecycle_codes = present_codes(life_sub, profile.get("lifecycle_only_codes", []))

    conf = "HIGH" if status == "BALANCED" else ("MEDIUM" if status == "MINOR_VARIANCE" else "LOW")
    notes = []
    if amounts["lifecycle_only"] > 0:
        notes.append(f"Excluded lifecycle-only amount {amounts['lifecycle_only']}")
    if profile.get("payment_event_only"):
        notes.append("Payment-event-only profile applied")
    if optional_missing and not profile.get("payment_event_only"):
        notes.append("Optional components absent (not forced)")

    revised = {
        "reconstructed_claim_id": claim_id,
        "claim_family": family,
        "revised_net_payment": net,
        "revised_balancing_difference": diff,
        "revised_balancing_status": status,
        "applied_balancing_profile": family,
        "lifecycle_only_amount_excluded": amounts["lifecycle_only"],
        "excluded_transaction_codes": "|".join(excluded_codes or lifecycle_codes),
        "optional_components_missing": "|".join(optional_missing),
        "balancing_confidence": conf,
        "balancing_notes": "; ".join(notes) if notes else profile.get("confidence_notes", ""),
        "original_balancing_difference": round(parse_amount(original_fin.get("balancing_difference", 0)), 2),
        "original_balancing_status": original_fin.get("balancing_status", ""),
    }
    return revised, amounts, optional, optional_present, optional_missing, payout


# ---------------------------------------------------------------------------
# Report builders
# ---------------------------------------------------------------------------

def build_validation_results(revised_df, original_fin):
    rows = []
    for family, sub in revised_df.groupby("claim_family", sort=True):
        orig = original_fin[original_fin["reconstructed_claim_id"].isin(sub["reconstructed_claim_id"])]
        orig_bal = int((orig["balancing_status"].str.upper() == "BALANCED").sum())
        rev_bal = int((sub["revised_balancing_status"] == "BALANCED").sum())
        gap_before = orig["balancing_difference"].apply(parse_amount).abs()
        gap_after = sub["revised_balancing_difference"].abs()
        improvement = rev_bal - orig_bal
        rows.append({
            "claim_family": family,
            "original_balanced_count": orig_bal,
            "revised_balanced_count": rev_bal,
            "balancing_improvement": improvement,
            "avg_gap_before": round(float(gap_before.mean()), 2),
            "avg_gap_after": round(float(gap_after.mean()), 2),
            "largest_gap_before": round(float(gap_before.max()), 2),
            "largest_gap_after": round(float(gap_after.max()), 2),
            "major_improvement_flag": "Y" if improvement >= 10 else "N",
        })
    return pd.DataFrame(rows).sort_values("claim_family").reset_index(drop=True)


def build_lifecycle_only_analysis(revised_rows, life_prepared, rules):
    rows = []
    for item in revised_rows:
        claim_id = item["reconstructed_claim_id"]
        family = item["claim_family"]
        profile = rules["families"].get(family, {})
        sub = life_prepared[life_prepared["reconstructed_claim_id"] == claim_id]
        lc_codes = present_codes(sub, profile.get("lifecycle_only_codes", []))
        lc_amount = item["lifecycle_only_amount_excluded"]
        rows.append({
            "reconstructed_claim_id": claim_id,
            "lifecycle_only_codes": "|".join(lc_codes),
            "lifecycle_only_amount": lc_amount,
            "excluded_from_net_flag": "Y" if lc_amount > 0 else "N",
            "lifecycle_role_impact": "CLEARING_HUB" if "0038" in lc_codes else "",
            "settlement_chain_impact": (
                "Hub linkage preserved; excluded from net rollup"
                if lc_amount > 0 else "No lifecycle-only codes"
            ),
        })
    return pd.DataFrame(rows).sort_values("reconstructed_claim_id").reset_index(drop=True)


def build_payout_chain_analysis(revised_rows, life_prepared, rules):
    rows = []
    for item in revised_rows:
        claim_id = item["reconstructed_claim_id"]
        family = item["claim_family"]
        profile = rules["families"].get(family, {})
        sub = life_prepared[life_prepared["reconstructed_claim_id"] == claim_id]
        payout_codes = present_codes(sub, profile.get("payout_component_codes", []))
        payout_total = sum_code_amounts(sub, profile.get("payout_component_codes", []))
        gross = present_codes(sub, profile.get("gross_component_codes", []))
        offsets = present_codes(sub, profile.get("offset_component_codes", []))
        interest = present_codes(sub, profile.get("interest_component_codes", []))
        diff = item["revised_balancing_difference"]
        status = item["revised_balancing_status"]
        conf = "HIGH" if status == "BALANCED" else "LOW"
        if profile.get("payment_event_only") and payout_total > 0:
            conf = "HIGH"
        rows.append({
            "reconstructed_claim_id": claim_id,
            "payout_codes_detected": "|".join(payout_codes),
            "payout_total": payout_total,
            "linked_gross_components": "|".join(gross),
            "linked_offset_components": "|".join(offsets),
            "linked_interest_components": "|".join(interest),
            "chain_balancing_status": status,
            "payout_chain_confidence": conf,
        })
    return pd.DataFrame(rows).sort_values("reconstructed_claim_id").reset_index(drop=True)


def build_optional_component_analysis(revised_rows, rules):
    rows = []
    for item in revised_rows:
        family = item["claim_family"]
        profile = rules["families"].get(family, {})
        optional = [format_tx_code(c) for c in profile.get("optional_components", [])]
        missing = [c for c in item.get("optional_components_missing", "").split("|") if c]
        present = [c for c in optional if c not in missing]
        wh_codes = {format_tx_code(c) for c in profile.get("withholding_component_codes", [])}
        wh_required = "N"
        impact = "NONE" if item["revised_balancing_status"] == "BALANCED" else "POTENTIAL"
        rows.append({
            "reconstructed_claim_id": item["reconstructed_claim_id"],
            "optional_components_expected": "|".join(optional),
            "optional_components_present": "|".join(present),
            "optional_components_missing": "|".join(missing),
            "balancing_impact": impact,
            "withholding_required_flag": wh_required,
        })
    return pd.DataFrame(rows).sort_values("reconstructed_claim_id").reset_index(drop=True)


def build_rule_recommendations(validation_df, revised_df, rules):
    recs = []
    for _, row in validation_df.iterrows():
        family = row["claim_family"]
        profile = rules["families"].get(family, {})
        if row["balancing_improvement"] <= 0 and row["revised_balanced_count"] < row["original_balanced_count"]:
            recs.append({
                "claim_family": family,
                "observed_pattern": "Rule application did not improve balancing counts",
                "current_rule_issue": "Profile may need pairing logic refinement",
                "recommended_adjustment": "Review settlement pairing and signed amount handling",
                "expected_balancing_impact": "MEDIUM",
                "confidence_level": "LOW",
            })
        elif row["balancing_improvement"] > 0:
            recs.append({
                "claim_family": family,
                "observed_pattern": f"Improved {row['balancing_improvement']} balanced claims",
                "current_rule_issue": "Generic Phase 4 formula insufficient",
                "recommended_adjustment": f"Adopt {family} profile in future reconstruction pass",
                "expected_balancing_impact": "HIGH",
                "confidence_level": "HIGH",
            })

    death_sub = revised_df[revised_df["claim_family"] == "DEATH_CLAIM"]
    if not death_sub.empty:
        lc_excluded = (death_sub["lifecycle_only_amount_excluded"] > 0).sum()
        recs.append({
            "claim_family": "DEATH_CLAIM",
            "observed_pattern": f"{lc_excluded} claims with 0038 lifecycle-only amounts excluded",
            "current_rule_issue": "Clearing hub inflates generic raw totals",
            "recommended_adjustment": "Keep 0038 lifecycle-only exclusion in net rollup",
            "expected_balancing_impact": "HIGH",
            "confidence_level": "HIGH",
        })

    disb = validation_df[validation_df["claim_family"] == "DISBURSEMENT_CLAIM"]
    if not disb.empty and int(disb.iloc[0]["revised_balanced_count"]) > 0:
        recs.append({
            "claim_family": "DISBURSEMENT_CLAIM",
            "observed_pattern": "Payment-event-only profile balances disbursement chains",
            "current_rule_issue": "Gross benefit required incorrectly in Phase 4",
            "recommended_adjustment": "Treat DISBURSEMENT_CLAIM as payout-only event chains",
            "expected_balancing_impact": "HIGH",
            "confidence_level": "HIGH",
        })

    surr_unbal = revised_df[
        (revised_df["claim_family"] == "SURRENDER_CLAIM")
        & (revised_df["revised_balancing_status"] != "BALANCED")
    ]
    if len(surr_unbal) > 0:
        recs.append({
            "claim_family": "SURRENDER_CLAIM",
            "observed_pattern": f"{len(surr_unbal)} surrender claims remain unbalanced after rules",
            "current_rule_issue": "Missing linked disbursement (0090) on funded-only chains",
            "recommended_adjustment": "Add delayed payout detection or separate funded vs disbursed chains",
            "expected_balancing_impact": "MEDIUM",
            "confidence_level": "MEDIUM",
        })

    if not recs:
        recs.append({
            "claim_family": "ALL",
            "observed_pattern": "No major patterns",
            "current_rule_issue": "none",
            "recommended_adjustment": "Continue monitoring",
            "expected_balancing_impact": "LOW",
            "confidence_level": "LOW",
        })

    return pd.DataFrame(recs).drop_duplicates().sort_values(
        ["claim_family", "confidence_level"],
        ascending=[True, False],
    ).reset_index(drop=True)


def write_summary(path, validation_df, revised_df, stats, output_files):
    lines = [
        "=== Family Balancing Rule Validation Summary (Phase 6) ===",
        "",
        "Balancing improvement by family:",
    ]
    for _, r in validation_df.iterrows():
        lines.append(
            f"  {r['claim_family']}: {r['original_balanced_count']} -> {r['revised_balanced_count']} "
            f"(+{r['balancing_improvement']})"
        )
    lines.extend([
        "",
        f"Total balanced before: {stats['balanced_before']}",
        f"Total balanced after: {stats['balanced_after']}",
        f"Total improvement: {stats['total_improvement']}",
        f"Largest avg gap reduction: {stats['largest_avg_gap_reduction']}",
        "",
        f"Lifecycle-only impact: {stats['lifecycle_only_claims']} claims with excluded hub amounts",
        f"Payout chain findings: {stats['payout_chain_balanced']} payout chains balanced under rules",
        f"Optional withholding observations: not forced when codes absent",
        "",
        "Remaining major balancing risks:",
    ])
    for risk in stats.get("risks", []):
        lines.append(f"  - {risk}")
    lines.extend([
        "",
        "Recommended next-phase priorities:",
    ])
    for p in stats.get("priorities", []):
        lines.append(f"  - {p}")
    lines.extend(["", "Output files generated:"])
    for f in output_files:
        lines.append(f"  - {f}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_engine(headers_path, financials_path, lifecycle_path, rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_rules(rules_path)
    global BALANCE_TOLERANCE  # noqa: PLW0603
    BALANCE_TOLERANCE = rules.get("balance_tolerance", BALANCE_TOLERANCE)

    headers = load_csv(headers_path)
    financials = load_csv(financials_path)
    lifecycle = load_csv(lifecycle_path)
    life_prepared = prepare_lifecycle(lifecycle)

    orig_map = financials.set_index("reconstructed_claim_id").to_dict("index")
    revised_rows = []
    amounts_cache = {}

    for claim_id, header in headers.groupby("reconstructed_claim_id", sort=True):
        h = header.iloc[0]
        family = h["claim_family"]
        profile = rules["families"].get(family)
        if not profile:
            logger.warning("No profile for family %s claim %s", family, claim_id)
            continue
        life_sub = life_prepared[life_prepared["reconstructed_claim_id"] == claim_id]
        orig = orig_map.get(claim_id, {})
        revised, amounts, optional, opt_present, opt_missing, payout = process_claim(
            claim_id, h, orig, life_sub, profile, family,
        )
        revised["optional_components_missing"] = "|".join(opt_missing)
        revised_rows.append(revised)
        amounts_cache[claim_id] = amounts

    revised_df = pd.DataFrame(revised_rows).sort_values("reconstructed_claim_id").reset_index(drop=True)

    validation_df = build_validation_results(revised_df, financials)
    lifecycle_df = build_lifecycle_only_analysis(revised_rows, life_prepared, rules)
    payout_df = build_payout_chain_analysis(revised_rows, life_prepared, rules)
    optional_df = build_optional_component_analysis(revised_rows, rules)
    recommendations_df = build_rule_recommendations(validation_df, revised_df, rules)

    rules_out = os.path.join(output_dir, "claim_family_balancing_rules.json")
    shutil.copy2(rules_path, rules_out)

    reports = {
        "family_balancing_validation_results.csv": validation_df,
        "revised_claim_financials.csv": revised_df[[
            "reconstructed_claim_id", "claim_family", "revised_net_payment",
            "revised_balancing_difference", "revised_balancing_status",
            "applied_balancing_profile", "lifecycle_only_amount_excluded",
            "excluded_transaction_codes", "optional_components_missing",
            "balancing_confidence", "balancing_notes",
        ]],
        "lifecycle_only_transaction_analysis.csv": lifecycle_df,
        "payout_chain_analysis.csv": payout_df,
        "optional_component_analysis.csv": optional_df,
        "balancing_rule_recommendations.csv": recommendations_df,
    }

    output_files = [rules_out]
    for name, frame in reports.items():
        out_path = os.path.join(output_dir, name)
        frame.to_csv(out_path, index=False, encoding="utf-8")
        output_files.append(out_path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    orig_bal = int((financials["balancing_status"].str.upper() == "BALANCED").sum())
    rev_bal = int((revised_df["revised_balancing_status"] == "BALANCED").sum())
    avg_before = financials["balancing_difference"].apply(parse_amount).abs().mean()
    avg_after = revised_df["revised_balancing_difference"].abs().mean()

    stats = {
        "balanced_before": orig_bal,
        "balanced_after": rev_bal,
        "total_improvement": rev_bal - orig_bal,
        "largest_avg_gap_reduction": round(float(avg_before - avg_after), 2),
        "lifecycle_only_claims": int((revised_df["lifecycle_only_amount_excluded"] > 0).sum()),
        "payout_chain_balanced": int((payout_df["chain_balancing_status"] == "BALANCED").sum()),
        "risks": [
            "Death claims with benefit/payout mismatch remain after clearing exclusion",
            "Surrender funded-only chains without 0090 disbursement",
            "Withholding codes largely unobserved (optional, not forced)",
        ],
        "priorities": recommendations_df.head(5)["recommended_adjustment"].tolist(),
    }

    summary_path = os.path.join(output_dir, "family_balancing_summary.txt")
    write_summary(summary_path, validation_df, revised_df, stats, output_files + [summary_path])
    output_files.append(summary_path)
    logger.info("Wrote family_balancing_summary.txt")

    return stats, output_files


def main():
    parser = argparse.ArgumentParser(
        description="Phase 6 family-specific claim balancing rule engine (read-only validation).",
    )
    parser.add_argument(
        "--headers",
        default=os.path.join(DEFAULT_PHASE4, "claim_candidate_header.csv"),
    )
    parser.add_argument(
        "--financials",
        default=os.path.join(DEFAULT_PHASE4, "claim_candidate_financials.csv"),
    )
    parser.add_argument(
        "--lifecycle",
        default=os.path.join(DEFAULT_PHASE4, "claim_candidate_lifecycle.csv"),
    )
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", required=True)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    for label, path in (
        ("Headers", args.headers),
        ("Financials", args.financials),
        ("Lifecycle", args.lifecycle),
        ("Rules", args.rules),
    ):
        if not os.path.isfile(path):
            logger.error("%s file not found: %s", label, path)
            return 1

    try:
        stats, outputs = run_engine(
            args.headers, args.financials, args.lifecycle, args.rules, args.output,
        )
        print(f"Balancing validation complete. Before: {stats['balanced_before']} balanced")
        print(f"After: {stats['balanced_after']} balanced (+{stats['total_improvement']})")
        print(f"Output directory: {os.path.abspath(args.output)}")
        for p in outputs:
            print(f"  {p}")
        return 0
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
