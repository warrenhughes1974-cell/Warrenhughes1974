#!/usr/bin/env python3
"""
Phase 7A — Settlement chain intelligence engine (read-only).

Reconstructs funding/payout settlement lineage from Phase 4/6 outputs.
Does NOT modify app.py, Phase 4/6 outputs, or generate QUIKCLMS/QUIKCLMP DBFs.
"""

import argparse
import json
import logging
import os
import re
import shutil
from datetime import datetime

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_RULES = os.path.join(ROOT, "config", "settlement_chain_rules.json")
DEFAULT_BALANCING_RULES = os.path.join(ROOT, "config", "claim_family_balancing_rules.json")
PHASE4 = os.path.join(ROOT, "phase4_claim_event_reconstruction")
PHASE6 = os.path.join(ROOT, "phase6_family_balancing_intelligence")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase7_settlement_chain_intelligence")

logger = logging.getLogger("settlement_chain_engine")


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


def parse_date(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = re.sub(r"[^0-9]", "", str(value).strip())
    if len(s) != 8:
        return None
    try:
        return datetime.strptime(s, "%Y%m%d")
    except ValueError:
        return None


def date_str(value):
    d = parse_date(value)
    return d.strftime("%Y%m%d") if d else ""


def days_between(d1, d2):
    if not d1 or not d2:
        return None
    return abs((d2 - d1).days)


def codes_in_set(code, code_list):
    return format_tx_code(code) in {format_tx_code(c) for c in code_list}


def sum_events(events, code_list):
    if events.empty or not code_list:
        return 0.0
    mask = events["source_transaction_code"].apply(lambda c: codes_in_set(c, code_list))
    return round(float(events.loc[mask, "amount_parsed"].sum()), 2)


def filter_events(events, code_list):
    if events.empty or not code_list:
        return events.iloc[0:0]
    mask = events["source_transaction_code"].apply(lambda c: codes_in_set(c, code_list))
    return events.loc[mask]


def family_profile(rules, family):
    return rules.get("families", {}).get(family, {})


def all_code_buckets(profile):
    return {
        "funding": profile.get("funding_codes", []),
        "interest": profile.get("interest_codes", []),
        "offset": profile.get("offset_codes", []),
        "withholding": profile.get("withholding_codes", []),
        "payout": profile.get("payout_codes", []),
        "lifecycle_only": profile.get("lifecycle_only_codes", []),
    }


def prepare_lifecycle(lifecycle, rules):
    exclude = set(rules.get("exclude_lifecycle_event_types", ["CLAIM_SETTLEMENT"]))
    life = lifecycle.copy()
    life["source_transaction_code"] = life["source_transaction_code"].apply(format_tx_code)
    life["amount_parsed"] = life["trans_amount"].apply(parse_amount)
    life["effective_date_parsed"] = life["effective_date"].apply(parse_date)
    life = life[~life["lifecycle_event_type"].isin(exclude)]
    return life


def amount_aligned(funding_total, payout_total, rules):
    tol = rules.get("amount_alignment_tolerance", 100.0)
    ratio_tol = rules.get("amount_alignment_ratio_tolerance", 0.15)
    if funding_total <= 0 or payout_total <= 0:
        return payout_total > 0 and funding_total <= 0
    diff = abs(funding_total - payout_total)
    if diff <= tol:
        return True
    base = max(funding_total, payout_total)
    return (diff / base) <= ratio_tol


def score_confidence(chain_status, lag_days, family, profile, funding_total, payout_total,
                     rules, cross_claim=False, multi_payout=False):
    scoring = rules.get("confidence_scoring", {})
    if chain_status == "PAYOUT_ONLY" and family == "DISBURSEMENT_CLAIM":
        return "HIGH_CONFIDENCE", "Disbursement payout-only profile; semantic alignment confirmed"
    if chain_status == "IMMEDIATE_CHAIN" and amount_aligned(funding_total, payout_total, rules):
        return "HIGH_CONFIDENCE", "Same-day funding/payout with amount alignment"
    if chain_status == "MULTI_PAYOUT_CHAIN":
        return "MODERATE_CONFIDENCE", "Multiple payout events in settlement chain"
    if chain_status == "DELAYED_CHAIN":
        if cross_claim:
            return "INFERRED", f"Cross-claim delayed linkage within policy window (lag={lag_days}d)"
        return "MODERATE_CONFIDENCE", f"Delayed payout within {lag_days} day lag window"
    if chain_status == "FUNDED_NO_DISBURSEMENT":
        if profile.get("allow_delayed_disbursement"):
            return "INFERRED", "Funded-only chain; delayed disbursement allowed by family profile"
        return "LOW_CONFIDENCE", "Funding without observed payout linkage"
    if chain_status == "PARTIAL_CHAIN":
        return "MODERATE_CONFIDENCE", "Funding and payout linked but amounts diverge beyond tolerance"
    if chain_status == "ORPHAN_CHAIN":
        return "LOW_CONFIDENCE", "Insufficient semantic chain linkage"
    if chain_status == "PAYOUT_ONLY":
        return "MODERATE_CONFIDENCE", "Payout-only chain without in-group funding"
    return "INFERRED", "Rule-based default inference"


def classify_chain(events, profile, rules, header, cross_payout=None):
    buckets = all_code_buckets(profile)
    funding_ev = filter_events(events, buckets["funding"] + buckets["interest"])
    payout_ev = filter_events(events, buckets["payout"])
    offset_ev = filter_events(events, buckets["offset"])
    lifecycle_ev = filter_events(events, buckets["lifecycle_only"])

    funding_total = sum_events(events, buckets["funding"] + buckets["interest"])
    payout_total = sum_events(events, buckets["payout"])
    offset_total = sum_events(events, buckets["offset"])
    lifecycle_total = sum_events(events, buckets["lifecycle_only"])

    has_funding = funding_total > 0 or not funding_ev.empty
    has_payout = payout_total > 0 or not payout_ev.empty
    has_offset = offset_total > 0 or not offset_ev.empty
    has_lifecycle = lifecycle_total > 0 or not lifecycle_ev.empty

    payout_count = len(payout_ev)
    immediate_days = rules.get("immediate_settlement_days", 0)
    lag_window = rules.get("payout_lag_window_days", 14)

    first_d = parse_date(header.get("first_activity_date"))
    last_d = parse_date(header.get("latest_activity_date"))
    lag_days = days_between(first_d, last_d) if first_d and last_d else 0

    cross_payout_total = 0.0
    cross_lag = None
    if cross_payout:
        cross_payout_total = cross_payout.get("payout_total", 0.0)
        cross_lag = cross_payout.get("lag_days")

    effective_payout = payout_total + cross_payout_total
    effective_has_payout = has_payout or cross_payout_total > 0

    if payout_count >= rules.get("multi_payout_min_count", 2):
        status = "MULTI_PAYOUT_CHAIN"
    elif effective_has_payout and not has_funding and not has_offset:
        status = "PAYOUT_ONLY"
    elif (has_funding or has_offset) and not effective_has_payout:
        status = "FUNDED_NO_DISBURSEMENT"
    elif has_funding and effective_has_payout:
        effective_lag = cross_lag if cross_lag is not None else lag_days
        if effective_lag is not None and effective_lag <= immediate_days:
            status = "IMMEDIATE_CHAIN"
        elif effective_lag is not None and effective_lag <= lag_window:
            status = "DELAYED_CHAIN"
        else:
            status = "PARTIAL_CHAIN"
        if not amount_aligned(funding_total, effective_payout, rules):
            if status == "IMMEDIATE_CHAIN":
                status = "PARTIAL_CHAIN"
    elif has_lifecycle and not has_funding and not effective_has_payout:
        status = "ORPHAN_CHAIN"
    elif has_offset and not has_funding and not effective_has_payout:
        status = "FUNDED_NO_DISBURSEMENT"
    else:
        status = "ORPHAN_CHAIN"

    return {
        "chain_status": status,
        "funding_total": funding_total,
        "payout_total": payout_total,
        "effective_payout_total": round(effective_payout, 2),
        "offset_total": offset_total,
        "lifecycle_only_total": lifecycle_total,
        "funding_event_count": len(funding_ev),
        "payout_event_count": payout_count,
        "offset_event_count": len(offset_ev),
        "lifecycle_event_count": len(lifecycle_ev),
        "lag_days": lag_days if lag_days is not None else "",
        "cross_claim_lag_days": cross_lag if cross_lag is not None else "",
        "has_lifecycle_hub": "Y" if has_lifecycle else "N",
    }


def find_cross_claim_payout(claim_id, policy, header, policy_claims, policy_lifecycle, rules):
    if not rules.get("cross_claim_linkage_enabled", True):
        return None
    profile = family_profile(rules, header.get("claim_family", ""))
    if not profile.get("allow_delayed_disbursement"):
        return None

    buckets = all_code_buckets(profile)
    this_first = parse_date(header.get("first_activity_date"))
    if not this_first:
        return None

    window = rules.get("cross_claim_policy_window_days", 30)
    best = None

    for other_id, other_header in policy_claims.items():
        if other_id == claim_id:
            continue
        other_family = other_header.get("claim_family", "")
        other_profile = family_profile(rules, other_family)
        other_payout_codes = other_profile.get("payout_codes", [])
        if not other_payout_codes:
            continue
        other_events = policy_lifecycle[policy_lifecycle["reconstructed_claim_id"] == other_id]
        payout_ev = filter_events(other_events, other_payout_codes)
        if payout_ev.empty:
            continue
        other_dates = payout_ev["effective_date_parsed"].dropna()
        if other_dates.empty:
            continue
        payout_date = other_dates.min()
        lag = days_between(this_first, payout_date)
        if lag is None or lag > window:
            continue
        payout_total = sum_events(payout_ev, other_payout_codes)
        candidate = {
            "linked_claim_id": other_id,
            "linked_family": other_family,
            "payout_total": payout_total,
            "lag_days": lag,
            "payout_date": payout_date.strftime("%Y%m%d"),
        }
        if best is None or lag < best["lag_days"]:
            best = candidate
    return best


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def run_engine(headers, financials, lifecycle, revised_fin, payout_chain, balancing_rules_path,
               rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    life = prepare_lifecycle(lifecycle, rules)

    header_map = headers.set_index("reconstructed_claim_id").to_dict("index")
    fin_map = financials.set_index("reconstructed_claim_id").to_dict("index")
    rev_map = revised_fin.set_index("reconstructed_claim_id").to_dict("index") if not revised_fin.empty else {}
    pay_map = payout_chain.set_index("reconstructed_claim_id").to_dict("index") if not payout_chain.empty else {}

    policy_claims = {}
    for cid, h in header_map.items():
        policy = str(h.get("policy_number", "")).strip()
        policy_claims.setdefault(policy, {})[cid] = h

    summaries = []
    details = []
    delayed_rows = []
    orphan_rows = []
    multi_rows = []
    confidence_rows = []
    recommendations = []

    for claim_id in sorted(header_map.keys()):
        header = header_map[claim_id]
        family = header.get("claim_family", "")
        policy = str(header.get("policy_number", "")).strip()
        profile = family_profile(rules, family)
        events = life[life["reconstructed_claim_id"] == claim_id].sort_values(
            ["lifecycle_event_order"], ascending=True,
        )

        cross = find_cross_claim_payout(
            claim_id, policy, header,
            policy_claims.get(policy, {}),
            life[life["reconstructed_claim_id"].isin(policy_claims.get(policy, {}))],
            rules,
        )
        chain = classify_chain(events, profile, rules, header, cross)
        conf, conf_reason = score_confidence(
            chain["chain_status"],
            chain["lag_days"] if chain["lag_days"] != "" else cross.get("lag_days") if cross else None,
            family, profile,
            chain["funding_total"], chain["effective_payout_total"],
            rules,
            cross_claim=bool(cross),
            multi_payout=chain["chain_status"] == "MULTI_PAYOUT_CHAIN",
        )

        orig_fin = fin_map.get(claim_id, {})
        rev_fin = rev_map.get(claim_id, {})
        pay_info = pay_map.get(claim_id, {})

        chain_id = f"{claim_id}-SC"
        summaries.append({
            "reconstructed_claim_id": claim_id,
            "policy_number": policy,
            "claim_family": family,
            "settlement_chain_id": chain_id,
            "chain_status": chain["chain_status"],
            "confidence_level": conf,
            "confidence_rationale": conf_reason,
            "funding_total": chain["funding_total"],
            "payout_total": chain["payout_total"],
            "effective_payout_total": chain["effective_payout_total"],
            "offset_total": chain["offset_total"],
            "lifecycle_only_total": chain["lifecycle_only_total"],
            "lag_days": chain["lag_days"],
            "cross_claim_linked_id": cross.get("linked_claim_id", "") if cross else "",
            "cross_claim_lag_days": chain["cross_claim_lag_days"],
            "first_activity_date": header.get("first_activity_date", ""),
            "latest_activity_date": header.get("latest_activity_date", ""),
            "original_balancing_status": orig_fin.get("balancing_status", ""),
            "revised_balancing_status": rev_fin.get("revised_balancing_status", ""),
            "balancing_impact_observation": (
                "No change" if orig_fin.get("balancing_status") == rev_fin.get("revised_balancing_status")
                else f"{orig_fin.get('balancing_status', '')} -> {rev_fin.get('revised_balancing_status', '')}"
            ),
            "settlement_notes": profile.get("notes", ""),
        })

        for _, ev in events.iterrows():
            role = "FUNDING"
            code = ev["source_transaction_code"]
            buckets = all_code_buckets(profile)
            if codes_in_set(code, buckets["payout"]):
                role = "PAYOUT"
            elif codes_in_set(code, buckets["offset"]):
                role = "OFFSET"
            elif codes_in_set(code, buckets["lifecycle_only"]):
                role = "LIFECYCLE_ONLY"
            elif codes_in_set(code, buckets["withholding"]):
                role = "WITHHOLDING"
            elif codes_in_set(code, buckets["interest"]):
                role = "INTEREST"
            details.append({
                "reconstructed_claim_id": claim_id,
                "settlement_chain_id": chain_id,
                "chain_status": chain["chain_status"],
                "lifecycle_event_order": ev["lifecycle_event_order"],
                "lifecycle_event_type": ev["lifecycle_event_type"],
                "source_transaction_code": code,
                "effective_date": ev["effective_date"],
                "trans_amount": ev["trans_amount"],
                "chain_role": role,
                "lineage_notes": ev.get("lifecycle_notes", ""),
            })

        if chain["chain_status"] == "DELAYED_CHAIN" or cross:
            delayed_rows.append({
                "reconstructed_claim_id": claim_id,
                "policy_number": policy,
                "claim_family": family,
                "funding_codes": "|".join(sorted(set(
                    filter_events(events, all_code_buckets(profile)["funding"])["source_transaction_code"].tolist()
                ))),
                "payout_codes": "|".join(sorted(set(
                    filter_events(events, all_code_buckets(profile)["payout"])["source_transaction_code"].tolist()
                ))),
                "in_group_lag_days": chain["lag_days"],
                "cross_claim_linked_id": cross.get("linked_claim_id", "") if cross else "",
                "cross_claim_payout_total": cross.get("payout_total", "") if cross else "",
                "cross_claim_lag_days": cross.get("lag_days", "") if cross else "",
                "delayed_linkage_candidate": "Y",
                "linkage_basis": "CROSS_CLAIM" if cross else "IN_GROUP",
                "confidence_level": conf,
            })

        if chain["chain_status"] in {"ORPHAN_CHAIN", "FUNDED_NO_DISBURSEMENT"} and not cross:
            orphan_rows.append({
                "reconstructed_claim_id": claim_id,
                "policy_number": policy,
                "claim_family": family,
                "chain_status": chain["chain_status"],
                "funding_total": chain["funding_total"],
                "offset_total": chain["offset_total"],
                "payout_total": chain["payout_total"],
                "orphan_reason": (
                    "Funding/offset without payout linkage"
                    if chain["chain_status"] == "FUNDED_NO_DISBURSEMENT"
                    else "Insufficient chain components"
                ),
                "allow_delayed_disbursement": "Y" if profile.get("allow_delayed_disbursement") else "N",
                "confidence_level": conf,
            })

        if chain["chain_status"] == "MULTI_PAYOUT_CHAIN":
            multi_rows.append({
                "reconstructed_claim_id": claim_id,
                "policy_number": policy,
                "claim_family": family,
                "payout_event_count": chain["payout_event_count"],
                "payout_total": chain["payout_total"],
                "funding_total": chain["funding_total"],
                "staged_settlement_flag": "Y",
                "beneficiary_distribution_ready": "FUTURE",
                "confidence_level": conf,
                "notes": "Future-ready multi-payout analysis; no production DBF generation",
            })

        confidence_rows.append({
            "reconstructed_claim_id": claim_id,
            "claim_family": family,
            "chain_status": chain["chain_status"],
            "confidence_level": conf,
            "temporal_proximity_score": (
                "STRONG" if chain["lag_days"] == 0 or chain["lag_days"] == ""
                else ("MODERATE" if chain["lag_days"] != "" and int(chain["lag_days"]) <= rules.get("payout_lag_window_days", 14)
                      else "WEAK")
            ),
            "semantic_alignment_score": "STRONG" if family else "WEAK",
            "amount_alignment_score": (
                "STRONG" if amount_aligned(chain["funding_total"], chain["effective_payout_total"], rules)
                else "WEAK"
            ),
            "payout_linkage_quality": (
                "DIRECT" if chain["payout_total"] > 0
                else ("CROSS_CLAIM" if cross else "NONE")
            ),
            "confidence_rationale": conf_reason,
        })

    summary_df = pd.DataFrame(summaries).sort_values("reconstructed_claim_id").reset_index(drop=True)
    detail_df = pd.DataFrame(details).sort_values(
        ["reconstructed_claim_id", "lifecycle_event_order"],
    ).reset_index(drop=True)
    delayed_df = pd.DataFrame(delayed_rows).sort_values("reconstructed_claim_id").reset_index(drop=True) if delayed_rows else pd.DataFrame(columns=[
        "reconstructed_claim_id", "policy_number", "claim_family", "delayed_linkage_candidate",
    ])
    orphan_df = pd.DataFrame(orphan_rows).sort_values("reconstructed_claim_id").reset_index(drop=True) if orphan_rows else pd.DataFrame(columns=[
        "reconstructed_claim_id", "policy_number", "chain_status",
    ])
    multi_df = pd.DataFrame(multi_rows).sort_values("reconstructed_claim_id").reset_index(drop=True) if multi_rows else pd.DataFrame(columns=[
        "reconstructed_claim_id", "payout_event_count",
    ])
    confidence_df = pd.DataFrame(confidence_rows).sort_values("reconstructed_claim_id").reset_index(drop=True)

    # Recommendations from aggregates
    status_counts = summary_df["chain_status"].value_counts()
    for family, sub in summary_df.groupby("claim_family"):
        funded_no = int((sub["chain_status"] == "FUNDED_NO_DISBURSEMENT").sum())
        if funded_no > 0:
            recommendations.append({
                "claim_family": family,
                "observed_pattern": f"{funded_no} FUNDED_NO_DISBURSEMENT chains",
                "current_rule_issue": "Payout not in same reconstruction group",
                "recommended_adjustment": "Enable cross-claim delayed linkage within policy window",
                "expected_balancing_impact": "MEDIUM",
                "confidence_level": "HIGH" if family == "SURRENDER_CLAIM" else "MODERATE",
            })
    if int(status_counts.get("DELAYED_CHAIN", 0)) > 0:
        recommendations.append({
            "claim_family": "ALL",
            "observed_pattern": f"{int(status_counts.get('DELAYED_CHAIN', 0))} delayed in-group chains",
            "current_rule_issue": "Same-day assumption too strict",
            "recommended_adjustment": f"Use payout_lag_window_days={rules.get('payout_lag_window_days', 14)} for staged settlement",
            "expected_balancing_impact": "MEDIUM",
            "confidence_level": "HIGH",
        })
    if int(status_counts.get("MULTI_PAYOUT_CHAIN", 0)) > 0:
        recommendations.append({
            "claim_family": "DEATH_CLAIM",
            "observed_pattern": f"{int(status_counts.get('MULTI_PAYOUT_CHAIN', 0))} multi-payout chains",
            "current_rule_issue": "Single-payout assumption insufficient",
            "recommended_adjustment": "Stage beneficiary distribution linkage (future-ready)",
            "expected_balancing_impact": "LOW",
            "confidence_level": "MODERATE",
        })
    rec_df = pd.DataFrame(recommendations).drop_duplicates().sort_values(
        ["claim_family", "confidence_level"], ascending=[True, False],
    ).reset_index(drop=True) if recommendations else pd.DataFrame()

    reports = {
        "settlement_chain_summary.csv": summary_df,
        "settlement_chain_detail.csv": detail_df,
        "delayed_payout_detection.csv": delayed_df,
        "orphan_chain_analysis.csv": orphan_df,
        "multi_payout_chain_analysis.csv": multi_df,
        "chain_confidence_analysis.csv": confidence_df,
        "settlement_chain_recommendations.csv": rec_df,
    }

    rules_out = os.path.join(output_dir, "settlement_chain_rules.json")
    shutil.copy2(rules_path, rules_out)
    output_files = [rules_out]

    for name, frame in reports.items():
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        output_files.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    stats = {
        "total_chains": len(summary_df),
        "status_distribution": status_counts.to_dict(),
        "confidence_distribution": summary_df["confidence_level"].value_counts().to_dict(),
        "delayed_count": len(delayed_df),
        "orphan_count": len(orphan_df),
        "multi_payout_count": len(multi_df),
        "cross_claim_links": int((summary_df["cross_claim_linked_id"] != "").sum()),
    }

    summary_txt = os.path.join(output_dir, "settlement_chain_summary.txt")
    write_summary_txt(summary_txt, stats, rules, output_files, summary_df)
    output_files.append(summary_txt)
    logger.info("Wrote settlement_chain_summary.txt")

    return stats, output_files


def write_summary_txt(path, stats, rules, output_files, summary_df):
    lines = [
        "=== Settlement Chain Intelligence Summary (Phase 7A) ===",
        "",
        f"Total settlement chains analyzed: {stats['total_chains']}",
        "",
        "Chain-type distributions:",
    ]
    for status, count in sorted(stats["status_distribution"].items()):
        lines.append(f"  {status}: {count}")
    lines.extend([
        "",
        "Confidence distributions:",
    ])
    for level, count in sorted(stats["confidence_distribution"].items()):
        lines.append(f"  {level}: {count}")
    lines.extend([
        "",
        f"Delayed payout candidates: {stats['delayed_count']}",
        f"Orphan/funded-no-disbursement chains: {stats['orphan_count']}",
        f"Multi-payout chains: {stats['multi_payout_count']}",
        f"Cross-claim linkage matches: {stats['cross_claim_links']}",
        "",
        "Balancing impact observations:",
    ])
    for family, sub in summary_df.groupby("claim_family"):
        improved = int((sub["original_balancing_status"] != sub["revised_balancing_status"]).sum())
        lines.append(f"  {family}: {improved} claims with Phase 6 revised balancing divergence from original")
    lines.extend([
        "",
        "Family-specific chain behavior:",
    ])
    for family, sub in summary_df.groupby("claim_family"):
        top = sub["chain_status"].value_counts().idxmax()
        lines.append(f"  {family}: dominant status={top}")
    lines.extend([
        "",
        "Remaining major risks:",
        "  - Death claim benefit/payout amount mismatch persists in PARTIAL_CHAIN cases",
        "  - Surrender funded-only chains await cross-claim disbursement linkage",
        "  - Multi-beneficiary distribution remains future-ready only",
        "",
        "Recommended next-phase priorities:",
        "  - Apply cross-claim delayed linkage in reconstruction grouping (Phase 7B)",
        "  - Refine death claim clearing-to-payout pairing rules",
        "  - Stage beneficiary multi-payout linkage metadata",
        "",
        "Output files generated:",
    ])
    for f in output_files:
        lines.append(f"  - {f}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Phase 7A settlement chain intelligence engine.")
    parser.add_argument("--headers", default=os.path.join(PHASE4, "claim_candidate_header.csv"))
    parser.add_argument("--financials", default=os.path.join(PHASE4, "claim_candidate_financials.csv"))
    parser.add_argument("--lifecycle", default=os.path.join(PHASE4, "claim_candidate_lifecycle.csv"))
    parser.add_argument("--revised-financials", default=os.path.join(PHASE6, "revised_claim_financials.csv"))
    parser.add_argument("--payout-chain", default=os.path.join(PHASE6, "payout_chain_analysis.csv"))
    parser.add_argument("--balancing-rules", default=DEFAULT_BALANCING_RULES)
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
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
        ("Revised financials", args.revised_financials),
        ("Payout chain", args.payout_chain),
        ("Rules", args.rules),
    ):
        if not os.path.isfile(path):
            logger.error("%s not found: %s", label, path)
            return 1

    headers = load_csv(args.headers)
    financials = load_csv(args.financials)
    lifecycle = load_csv(args.lifecycle)
    revised_fin = load_csv(args.revised_financials)
    payout_chain = load_csv(args.payout_chain)

    try:
        stats, outputs = run_engine(
            headers, financials, lifecycle, revised_fin, payout_chain,
            args.balancing_rules, args.rules, args.output,
        )
        print(f"Settlement chain analysis complete. Chains: {stats['total_chains']}")
        print(f"Delayed candidates: {stats['delayed_count']}")
        print(f"Orphan chains: {stats['orphan_count']}")
        print(f"Output: {os.path.abspath(args.output)}")
        for p in outputs:
            print(f"  {p}")
        return 0
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
