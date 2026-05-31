#!/usr/bin/env python3
"""
Phase 7B — Cross-claim settlement linkage integration (read-only overlay).

Creates enhanced settlement grouping candidates from Phase 7A findings.
Does NOT modify app.py, Phase 4/6/7A outputs, or generate QUIKCLMS/QUIKCLMP DBFs.
"""

import argparse
import json
import logging
import os
import re
import shutil
from collections import defaultdict
from datetime import datetime

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_RULES = os.path.join(ROOT, "config", "cross_claim_linkage_rules.json")
DEFAULT_SETTLEMENT_RULES = os.path.join(ROOT, "config", "settlement_chain_rules.json")
DEFAULT_BALANCING_RULES = os.path.join(ROOT, "config", "claim_family_balancing_rules.json")
PHASE4 = os.path.join(ROOT, "phase4_claim_event_reconstruction")
PHASE6 = os.path.join(ROOT, "phase6_family_balancing_intelligence")
PHASE7A = os.path.join(ROOT, "phase7_settlement_chain_intelligence")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase7b_cross_claim_linkage")

logger = logging.getLogger("cross_claim_linkage_engine")

BALANCE_TOLERANCE = 0.01
MINOR_VARIANCE = 100.0


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


def days_between(d1, d2):
    if not d1 or not d2:
        return None
    return abs((d2 - d1).days)


def code_in_list(code, codes):
    return format_tx_code(code) in {format_tx_code(c) for c in codes}


def sum_code_amounts(sub, codes):
    if sub.empty or not codes:
        return 0.0
    allowed = {format_tx_code(c) for c in codes}
    mask = sub["source_transaction_code"].apply(lambda c: format_tx_code(c) in allowed)
    return round(float(sub.loc[mask, "amount_parsed"].sum()), 2)


def present_codes(sub, codes):
    return sorted({
        format_tx_code(c)
        for c in sub["source_transaction_code"].tolist()
        if code_in_list(c, codes)
    })


def amount_aligned(funding_total, payout_total, rules):
    tol = rules.get("amount_alignment_tolerance", 100.0)
    ratio_tol = rules.get("amount_alignment_ratio_tolerance", 0.15)
    if funding_total <= 0 and payout_total <= 0:
        return False
    if funding_total <= 0:
        return payout_total > 0
    if payout_total <= 0:
        return False
    diff = abs(funding_total - payout_total)
    if diff <= tol:
        return True
    base = max(funding_total, payout_total)
    return (diff / base) <= ratio_tol


def balancing_status(diff, rules):
    tol = rules.get("balance_tolerance", BALANCE_TOLERANCE)
    minor = rules.get("minor_variance_tolerance", MINOR_VARIANCE)
    ad = abs(diff)
    if ad <= tol:
        return "BALANCED"
    if ad <= minor:
        return "MINOR_VARIANCE"
    return "UNBALANCED"


def prepare_lifecycle(lifecycle, settlement_rules):
    exclude = set(settlement_rules.get("exclude_lifecycle_event_types", ["CLAIM_SETTLEMENT"]))
    life = lifecycle.copy()
    life["source_transaction_code"] = life["source_transaction_code"].apply(format_tx_code)
    life["amount_parsed"] = life["trans_amount"].apply(parse_amount)
    life["effective_date_parsed"] = life["effective_date"].apply(parse_date)
    life = life[~life["lifecycle_event_type"].isin(exclude)]
    return life


def family_profile(settlement_rules, family):
    return settlement_rules.get("families", {}).get(family, {})


def classify_amounts(sub, profile):
    return {
        "gross": sum_code_amounts(sub, profile.get("gross_component_codes", [])),
        "interest": sum_code_amounts(sub, profile.get("interest_component_codes", [])),
        "loan_offsets": sum_code_amounts(sub, profile.get("offset_component_codes", [])),
        "surrender_charge": sum_code_amounts(sub, profile.get("surrender_charge_codes", [])),
        "withholding": sum_code_amounts(sub, profile.get("withholding_component_codes", [])),
        "payout": sum_code_amounts(sub, profile.get("payout_component_codes", [])),
        "lifecycle_only": sum_code_amounts(sub, profile.get("lifecycle_only_codes", [])),
    }


def apply_family_formula(family, amounts, profile):
    if profile.get("payment_event_only"):
        net = amounts["payout"]
        return net, round(net - amounts["payout"], 2), amounts["payout"]

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


def compute_funding_total(events, settlement_profile):
    funding_codes = (
        settlement_profile.get("funding_codes", [])
        + settlement_profile.get("interest_codes", [])
    )
    return sum_code_amounts(events, funding_codes)


def compute_offset_total(events, settlement_profile):
    return sum_code_amounts(events, settlement_profile.get("offset_codes", []))


def has_gross_funding(events, settlement_profile):
    gross_codes = settlement_profile.get("funding_codes", [])
    return sum_code_amounts(events, gross_codes) > 0 or bool(present_codes(events, gross_codes))


def confidence_rank(level):
    order = {"HIGH_CONFIDENCE": 4, "MODERATE_CONFIDENCE": 3, "INFERRED": 2, "LOW_CONFIDENCE": 1}
    return order.get(level, 0)


def meets_acceptance_confidence(conf, rules):
    acceptance = rules.get("linkage_acceptance_rules", {})
    minimum = acceptance.get("minimum_acceptance_confidence", "MODERATE_CONFIDENCE")
    return confidence_rank(conf) >= confidence_rank(minimum)


def compute_payout_total(events, settlement_profile):
    return sum_code_amounts(events, settlement_profile.get("payout_codes", []))


def cross_family_allowed(rules, source_family, target_family):
    perms = rules.get("cross_family_permissions", {})
    source_cfg = perms.get(source_family, {})
    target_cfg = source_cfg.get(target_family, {})
    return bool(target_cfg.get("enabled", False))


def max_lag_for_pair(rules, source_family, target_family):
    perms = rules.get("cross_family_permissions", {})
    pair = perms.get(source_family, {}).get(target_family, {})
    if pair:
        return pair.get("max_lag_days", rules.get("max_linkage_distance_days", 30))
    return rules.get("max_linkage_distance_days", 30)


def score_linkage_confidence(lag_days, amount_ok, same_family, cross_family, rules):
    scoring = rules.get("confidence_scoring", {})
    if lag_days is not None and lag_days <= scoring.get("HIGH_CONFIDENCE", {}).get("max_lag_days", 3):
        if amount_ok and (same_family or not cross_family):
            return "HIGH_CONFIDENCE", "Same-policy linkage with strong temporal and amount alignment"
    if lag_days is not None and lag_days <= scoring.get("MODERATE_CONFIDENCE", {}).get("max_lag_days", 14):
        if amount_ok:
            fam_note = "cross-family" if cross_family else "same-family"
            return "MODERATE_CONFIDENCE", f"Delayed payout linkage within window ({fam_note}); amount aligned"
    if amount_ok and lag_days is not None and lag_days <= rules.get("cross_claim_window_days", 30):
        return "INFERRED", f"Cross-claim linkage within policy window (lag={lag_days}d)"
    return "LOW_CONFIDENCE", "Linkage candidate with weak temporal or amount alignment"


def linkage_status_for_pair(source_family, target_family, lag_days, accepted):
    if not accepted:
        return "REJECTED_LINKAGE"
    if source_family != target_family:
        return "CROSS_FAMILY_LINK"
    if lag_days and lag_days > 0:
        return "LINKED_DELAYED_PAYOUT"
    return "ENHANCED_GROUP"


def make_enhanced_group_id(policy, claim_ids):
    root = sorted(claim_ids)[0]
    return f"ESG-{policy}-{root}"


def union_find_groups(edges):
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for a, b in edges:
        union(a, b)

    groups = defaultdict(set)
    for node in parent:
        groups[find(node)].add(node)
    for a, b in edges:
        groups[find(a)].add(a)
        groups[find(b)].add(b)
    return groups


# ---------------------------------------------------------------------------
# Linkage evaluation
# ---------------------------------------------------------------------------

def evaluate_linkage_candidate(
    source_id, target_id, header_map, life, settlement_rules, linkage_rules,
    chain_summary_map, used_targets,
):
    source_h = header_map[source_id]
    target_h = header_map[target_id]
    source_family = source_h.get("claim_family", "")
    target_family = target_h.get("claim_family", "")
    policy = str(source_h.get("policy_number", "")).strip()

    if str(target_h.get("policy_number", "")).strip() != policy:
        return None, "REJECTED_LINKAGE", "LOW_CONFIDENCE", "Policy mismatch"

    exclusions = linkage_rules.get("linkage_exclusion_rules", {})
    if exclusions.get("reject_if_target_already_linked") and target_id in used_targets:
        return None, "REJECTED_LINKAGE", "LOW_CONFIDENCE", "Target claim already linked to another source"

    if not cross_family_allowed(linkage_rules, source_family, target_family):
        if source_family != target_family:
            return None, "REJECTED_LINKAGE", "LOW_CONFIDENCE", f"Cross-family linkage disabled: {source_family}->{target_family}"

    source_events = life[life["reconstructed_claim_id"] == source_id]
    target_events = life[life["reconstructed_claim_id"] == target_id]
    source_settle = family_profile(settlement_rules, source_family)
    target_settle = family_profile(settlement_rules, target_family)

    perms = linkage_rules.get("cross_family_permissions", {}).get(source_family, {}).get(target_family, {})
    funding_codes = perms.get("funding_codes_required") or (
        source_settle.get("funding_codes", []) + source_settle.get("offset_codes", [])
    )
    payout_codes = perms.get("payout_codes_required") or target_settle.get("payout_codes", [])

    gross_funding = compute_funding_total(source_events, source_settle)
    offset_total = compute_offset_total(source_events, source_settle)
    funding_total = gross_funding
    if funding_total <= 0 and offset_total > 0:
        funding_total = offset_total

    payout_total = compute_payout_total(target_events, target_settle)
    if payout_total <= 0:
        payout_total = compute_payout_total(target_events, {"payout_codes": payout_codes})

    min_funding = linkage_rules.get("min_funding_amount", 0.01)
    min_payout = linkage_rules.get("min_payout_amount", 0.01)
    if exclusions.get("reject_if_amount_below_minimum"):
        if funding_total < min_funding and payout_total < min_payout:
            return None, "REJECTED_LINKAGE", "LOW_CONFIDENCE", "Funding and payout below minimum thresholds"

    if exclusions.get("reject_if_no_semantic_codes"):
        src_codes = present_codes(source_events, funding_codes)
        tgt_codes = present_codes(target_events, payout_codes)
        if not src_codes and not compute_funding_total(source_events, source_settle):
            if source_family != target_family or not present_codes(source_events, source_settle.get("offset_codes", [])):
                return None, "REJECTED_LINKAGE", "LOW_CONFIDENCE", "No qualifying funding/offset codes on source"
        if not tgt_codes and payout_total <= 0:
            return None, "REJECTED_LINKAGE", "LOW_CONFIDENCE", "No qualifying payout codes on target"

    source_date = parse_date(source_h.get("first_activity_date"))
    target_date = parse_date(target_h.get("first_activity_date"))
    lag = days_between(source_date, target_date)
    max_lag = max_lag_for_pair(linkage_rules, source_family, target_family)
    if exclusions.get("reject_if_lag_exceeds_max_distance") and lag is not None and lag > max_lag:
        return None, "REJECTED_LINKAGE", "LOW_CONFIDENCE", f"Lag {lag}d exceeds max {max_lag}d for {source_family}->{target_family}"

    amt_ok = amount_aligned(gross_funding if gross_funding > 0 else funding_total, payout_total, linkage_rules)
    cross_fam = source_family != target_family
    conf, conf_reason = score_linkage_confidence(lag, amt_ok, not cross_fam, cross_fam, linkage_rules)

    chain_info = chain_summary_map.get(source_id, {})
    chain_status = chain_info.get("chain_status", "")
    acceptance = linkage_rules.get("linkage_acceptance_rules", {})
    pair_requires_amount = perms.get("require_amount_alignment", acceptance.get("require_amount_alignment_for_acceptance", True))

    accepted = True
    reject_reason = ""
    possible_match = False

    if exclusions.get("reject_if_no_semantic_codes") and cross_fam:
        if acceptance.get("reject_offset_only_to_unrelated_payout") and not has_gross_funding(source_events, source_settle):
            if offset_total > 0 and not amt_ok:
                accepted = False
                reject_reason = "Offset-only source rejected for unrelated cross-family payout"

    if accepted and pair_requires_amount and not amt_ok:
        if acceptance.get("mark_weak_candidates_as_possible_match"):
            accepted = False
            possible_match = True
            reject_reason = "Amount alignment required; candidate retained as POSSIBLE_MATCH"
        else:
            accepted = False
            reject_reason = "Amount alignment required for acceptance"

    if accepted and cross_fam and acceptance.get("reject_low_confidence_cross_family") and not meets_acceptance_confidence(conf, linkage_rules):
        accepted = False
        if acceptance.get("mark_weak_candidates_as_possible_match"):
            possible_match = True
            reject_reason = f"Cross-family confidence below minimum ({conf})"
        else:
            reject_reason = f"Cross-family confidence below minimum ({conf})"

    if accepted and funding_total <= 0 and payout_total <= 0:
        accepted = False
        reject_reason = "No fundable source amount and no payout amount"

    if possible_match and not accepted:
        return {
            "source_claim_id": source_id,
            "target_claim_id": target_id,
            "policy_number": policy,
            "source_family": source_family,
            "target_family": target_family,
            "funding_total": funding_total,
            "gross_funding_total": gross_funding,
            "offset_total": offset_total,
            "payout_total": payout_total,
            "lag_days": lag if lag is not None else "",
            "amount_aligned": "Y" if amt_ok else "N",
            "cross_family": "Y" if cross_fam else "N",
            "source_chain_status": chain_status,
            "linkage_basis": "PHASE7A_DELAYED" if chain_info.get("cross_claim_linked_id") == target_id else "POLICY_SCAN",
            "possible_match": "Y",
        }, "POSSIBLE_MATCH", conf, reject_reason

    status = linkage_status_for_pair(source_family, target_family, lag, accepted)
    if not accepted:
        return None, status, conf, reject_reason or conf_reason

    return {
        "source_claim_id": source_id,
        "target_claim_id": target_id,
        "policy_number": policy,
        "source_family": source_family,
        "target_family": target_family,
        "funding_total": funding_total,
        "gross_funding_total": gross_funding,
        "offset_total": offset_total,
        "payout_total": payout_total,
        "lag_days": lag if lag is not None else "",
        "amount_aligned": "Y" if amt_ok else "N",
        "cross_family": "Y" if cross_fam else "N",
        "source_chain_status": chain_status,
        "linkage_basis": "PHASE7A_DELAYED" if chain_info.get("cross_claim_linked_id") == target_id else "POLICY_SCAN",
        "possible_match": "N",
    }, status, conf, conf_reason


def find_policy_linkage_candidates(source_id, policy_claims, header_map, life, settlement_rules, linkage_rules, chain_summary_map, used_targets):
    source_h = header_map[source_id]
    source_family = source_h.get("claim_family", "")
    policy = str(source_h.get("policy_number", "")).strip()
    source_date = parse_date(source_h.get("first_activity_date"))

    candidates = []
    for target_id, target_h in policy_claims.get(policy, {}).items():
        if target_id == source_id:
            continue
        target_family = target_h.get("claim_family", "")
        if source_family == target_family:
            continue
        if not cross_family_allowed(linkage_rules, source_family, target_family):
            continue
        result, status, conf, reason = evaluate_linkage_candidate(
            source_id, target_id, header_map, life, settlement_rules, linkage_rules,
            chain_summary_map, used_targets,
        )
        if result:
            result["linkage_status"] = status
            result["confidence_level"] = conf
            result["linkage_rationale"] = reason
            candidates.append(result)
        elif status in {"REJECTED_LINKAGE", "POSSIBLE_MATCH"}:
            candidates.append({
                "source_claim_id": source_id,
                "target_claim_id": target_id,
                "policy_number": policy,
                "source_family": source_family,
                "target_family": target_family,
                "linkage_status": status,
                "confidence_level": conf,
                "linkage_rationale": reason,
                "lag_days": days_between(source_date, parse_date(target_h.get("first_activity_date"))) or "",
                "rejected": "Y",
            })

    candidates.sort(key=lambda c: (
        0 if c.get("linkage_status") not in {"REJECTED_LINKAGE", "POSSIBLE_MATCH"} else (
            1 if c.get("linkage_status") == "POSSIBLE_MATCH" else 2
        ),
        parse_amount(c.get("lag_days", 999)),
        -parse_amount(c.get("payout_total", 0)),
    ))
    return candidates


def compute_enhanced_balancing(claim_id, linked_payout, header_map, life, balancing_rules, linkage_rules):
    header = header_map[claim_id]
    family = header.get("claim_family", "")
    profile = balancing_rules.get("families", {}).get(family, {})
    sub = life[life["reconstructed_claim_id"] == claim_id]
    amounts = classify_amounts(sub, profile)
    enhanced_payout = round(amounts["payout"] + linked_payout, 2)
    amounts_enhanced = dict(amounts)
    amounts_enhanced["payout"] = enhanced_payout
    net, diff, _ = apply_family_formula(family, amounts_enhanced, profile)
    status = balancing_status(diff, linkage_rules)
    return {
        "enhanced_net_payment": net,
        "enhanced_balancing_difference": diff,
        "enhanced_balancing_status": status,
        "enhanced_payout_total": enhanced_payout,
        "in_group_payout": amounts["payout"],
        "linked_payout_added": linked_payout,
    }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def run_engine(
    headers, financials, lifecycle, revised_fin, chain_summary, delayed_detection,
    orphan_analysis, balancing_rules_path, settlement_rules_path, linkage_rules_path, output_dir,
):
    os.makedirs(output_dir, exist_ok=True)
    linkage_rules = load_json(linkage_rules_path)
    settlement_rules = load_json(settlement_rules_path)
    balancing_rules = load_json(balancing_rules_path)
    life = prepare_lifecycle(lifecycle, settlement_rules)

    header_map = headers.set_index("reconstructed_claim_id").to_dict("index")
    fin_map = financials.set_index("reconstructed_claim_id").to_dict("index")
    rev_map = revised_fin.set_index("reconstructed_claim_id").to_dict("index")
    chain_summary_map = chain_summary.set_index("reconstructed_claim_id").to_dict("index")

    policy_claims = defaultdict(dict)
    for cid, h in header_map.items():
        policy = str(h.get("policy_number", "")).strip()
        policy_claims[policy][cid] = h

    delayed_map = {}
    if not delayed_detection.empty and "reconstructed_claim_id" in delayed_detection.columns:
        for _, row in delayed_detection.iterrows():
            src = row["reconstructed_claim_id"]
            tgt = str(row.get("cross_claim_linked_id", "")).strip()
            if tgt:
                delayed_map[src] = tgt

    orphan_ids = set()
    if not orphan_analysis.empty and "reconstructed_claim_id" in orphan_analysis.columns:
        orphan_ids = set(orphan_analysis["reconstructed_claim_id"].tolist())

    linkage_candidates = []
    accepted_edges = []
    used_targets = set()
    rejected_rows = []

    eligible_sources = set()
    for cid, info in chain_summary_map.items():
        if info.get("chain_status") in linkage_rules.get("source_chain_statuses_eligible", []):
            eligible_sources.add(cid)
    eligible_sources |= orphan_ids
    eligible_sources |= set(delayed_map.keys())

    for source_id in sorted(eligible_sources):
        if source_id not in header_map:
            continue

        phase7a_target = delayed_map.get(source_id, "")
        best = None

        if phase7a_target and phase7a_target in header_map:
            result, status, conf, reason = evaluate_linkage_candidate(
                source_id, phase7a_target, header_map, life, settlement_rules, linkage_rules,
                chain_summary_map, used_targets,
            )
            if result:
                result["linkage_status"] = status
                result["confidence_level"] = conf
                result["linkage_rationale"] = reason
                result["linkage_basis"] = "PHASE7A_DELAYED"
                if status != "POSSIBLE_MATCH":
                    best = result
                else:
                    linkage_candidates.append(result)
            else:
                rejected_rows.append({
                    "source_claim_id": source_id,
                    "target_claim_id": phase7a_target,
                    "linkage_status": status,
                    "confidence_level": conf,
                    "linkage_rationale": reason,
                    "linkage_basis": "PHASE7A_DELAYED",
                })

        if not best:
            scan = find_policy_linkage_candidates(
                source_id, policy_claims, header_map, life, settlement_rules, linkage_rules,
                chain_summary_map, used_targets,
            )
            for cand in scan:
                if cand.get("linkage_status") == "POSSIBLE_MATCH":
                    linkage_candidates.append(cand)
                    continue
                if cand.get("linkage_status") != "REJECTED_LINKAGE":
                    best = cand
                    break
                rejected_rows.append(cand)

        if best and best.get("linkage_status") not in {"REJECTED_LINKAGE", "POSSIBLE_MATCH"}:
            tgt = best["target_claim_id"]
            if tgt not in used_targets or linkage_rules.get("multi_payout_association_enabled"):
                linkage_candidates.append(best)
                accepted_edges.append((source_id, tgt))
                used_targets.add(tgt)
        elif not best:
            linkage_candidates.append({
                "source_claim_id": source_id,
                "target_claim_id": "",
                "policy_number": str(header_map[source_id].get("policy_number", "")),
                "source_family": header_map[source_id].get("claim_family", ""),
                "target_family": "",
                "linkage_status": "RETAIN_ORIGINAL_GROUP",
                "confidence_level": "INFERRED",
                "linkage_rationale": "No acceptable cross-claim linkage candidate within policy window",
                "linkage_basis": "NONE",
            })

    for cid in sorted(header_map.keys()):
        if cid not in eligible_sources:
            chain_status = chain_summary_map.get(cid, {}).get("chain_status", "")
            linkage_candidates.append({
                "source_claim_id": cid,
                "target_claim_id": "",
                "policy_number": str(header_map[cid].get("policy_number", "")),
                "source_family": header_map[cid].get("claim_family", ""),
                "target_family": "",
                "linkage_status": "RETAIN_ORIGINAL_GROUP",
                "confidence_level": chain_summary_map.get(cid, {}).get("confidence_level", "INFERRED"),
                "linkage_rationale": f"Baseline chain status {chain_status}; no linkage refinement required",
                "linkage_basis": "BASELINE",
            })

    cand_df = pd.DataFrame(linkage_candidates)
    if cand_df.empty:
        cand_df = pd.DataFrame(columns=[
            "source_claim_id", "target_claim_id", "linkage_status", "confidence_level",
        ])
    else:
        cand_df = cand_df.drop_duplicates(subset=["source_claim_id", "target_claim_id"], keep="first")
        cand_df = cand_df.sort_values(["policy_number", "source_claim_id"]).reset_index(drop=True)

    accepted_df = cand_df[cand_df["linkage_status"].isin({
        "LINKED_DELAYED_PAYOUT", "CROSS_FAMILY_LINK", "ENHANCED_GROUP",
    })].copy()
    possible_df = cand_df[cand_df["linkage_status"] == "POSSIBLE_MATCH"].copy() if "linkage_status" in cand_df.columns else pd.DataFrame()

    group_map = {}
    if accepted_edges:
        groups = union_find_groups(accepted_edges)
        for _, members in groups.items():
            if len(members) < 1:
                continue
            policy = str(header_map[sorted(members)[0]].get("policy_number", ""))
            egid = make_enhanced_group_id(policy, members)
            for m in members:
                group_map[m] = egid

    enhanced_groups = []
    grouping_overlay = []
    linked_payout_by_source = defaultdict(float)

    for _, row in accepted_df.iterrows():
        src = row["source_claim_id"]
        if row.get("amount_aligned", "N") != "Y":
            continue
        linked_payout_by_source[src] += parse_amount(row.get("payout_total", 0))

    for cid in sorted(header_map.keys()):
        policy = str(header_map[cid].get("policy_number", ""))
        egid = group_map.get(cid, f"ESG-{policy}-{cid}-SOLO")
        is_linked = cid in group_map
        linked_to = ""
        linked_from = ""
        for _, row in accepted_df.iterrows():
            if row["source_claim_id"] == cid:
                linked_to = row.get("target_claim_id", "")
            if row.get("target_claim_id") == cid:
                linked_from = row.get("source_claim_id", "")

        overlay_status = "ENHANCED_GROUP" if is_linked else "RETAIN_ORIGINAL_GROUP"
        if cid in linked_payout_by_source and chain_summary_map.get(cid, {}).get("chain_status") in {
            "FUNDED_NO_DISBURSEMENT", "ORPHAN_CHAIN",
        }:
            overlay_status = "ORPHAN_REDUCED"

        enhanced_groups.append({
            "reconstructed_claim_id": cid,
            "policy_number": policy,
            "claim_family": header_map[cid].get("claim_family", ""),
            "original_group_id": cid,
            "enhanced_settlement_group_id": egid,
            "linkage_status": overlay_status,
            "linked_target_claim_id": linked_to,
            "linked_source_claim_id": linked_from,
            "group_member_count": len([m for m, g in group_map.items() if g == egid]) if is_linked else 1,
            "preserves_original_lineage": "Y",
        })

        grouping_overlay.append({
            "reconstructed_claim_id": cid,
            "policy_number": policy,
            "claim_family": header_map[cid].get("claim_family", ""),
            "original_reconstruction_group": cid,
            "enhanced_settlement_group_id": egid,
            "baseline_chain_status": chain_summary_map.get(cid, {}).get("chain_status", ""),
            "overlay_linkage_status": overlay_status,
            "cross_claim_linked_id": linked_to or linked_from,
            "linkage_rationale": (
                accepted_df[accepted_df["source_claim_id"] == cid]["linkage_rationale"].iloc[0]
                if cid in accepted_df["source_claim_id"].values else
                "Original reconstruction grouping retained"
            ),
        })

    enhanced_groups_df = pd.DataFrame(enhanced_groups).sort_values("reconstructed_claim_id").reset_index(drop=True)
    overlay_df = pd.DataFrame(grouping_overlay).sort_values("reconstructed_claim_id").reset_index(drop=True)

    cross_family_rows = []
    for _, row in accepted_df.iterrows():
        if row.get("cross_family") == "Y" or row.get("source_family") != row.get("target_family"):
            cross_family_rows.append({
                "source_claim_id": row["source_claim_id"],
                "target_claim_id": row["target_claim_id"],
                "policy_number": row.get("policy_number", ""),
                "source_family": row.get("source_family", ""),
                "target_family": row.get("target_family", ""),
                "funding_total": row.get("funding_total", ""),
                "payout_total": row.get("payout_total", ""),
                "lag_days": row.get("lag_days", ""),
                "amount_aligned": row.get("amount_aligned", ""),
                "linkage_status": row.get("linkage_status", ""),
                "confidence_level": row.get("confidence_level", ""),
                "linkage_rationale": row.get("linkage_rationale", ""),
            })
    cross_family_df = pd.DataFrame(cross_family_rows).sort_values(
        ["policy_number", "source_claim_id"],
    ).reset_index(drop=True) if cross_family_rows else pd.DataFrame(columns=[
        "source_claim_id", "target_claim_id", "source_family", "target_family",
    ])

    balancing_impact = []
    for cid in sorted(header_map.keys()):
        rev = rev_map.get(cid, {})
        orig = fin_map.get(cid, {})
        linked_payout = linked_payout_by_source.get(cid, 0.0)
        enhanced = compute_enhanced_balancing(
            cid, linked_payout, header_map, life, balancing_rules, linkage_rules,
        )
        baseline_status = rev.get("revised_balancing_status", orig.get("balancing_status", ""))
        enhanced_status = enhanced["enhanced_balancing_status"]
        impact = "No change"
        if baseline_status != enhanced_status:
            impact = f"{baseline_status} -> {enhanced_status}"
        balancing_impact.append({
            "reconstructed_claim_id": cid,
            "policy_number": str(header_map[cid].get("policy_number", "")),
            "claim_family": header_map[cid].get("claim_family", ""),
            "baseline_balancing_status": baseline_status,
            "enhanced_balancing_status": enhanced_status,
            "baseline_balancing_difference": rev.get("revised_balancing_difference", orig.get("balancing_difference", "")),
            "enhanced_balancing_difference": enhanced["enhanced_balancing_difference"],
            "linked_payout_added": enhanced["linked_payout_added"],
            "in_group_payout": enhanced["in_group_payout"],
            "enhanced_payout_total": enhanced["enhanced_payout_total"],
            "balancing_impact": impact,
            "cross_claim_linkage_applied": "Y" if linked_payout > 0 else "N",
        })

    balancing_df = pd.DataFrame(balancing_impact).sort_values("reconstructed_claim_id").reset_index(drop=True)

    confidence_rows = []
    for _, row in cand_df.iterrows():
        if row.get("linkage_status") == "RETAIN_ORIGINAL_GROUP" and row.get("linkage_basis") == "BASELINE":
            continue
        confidence_rows.append({
            "source_claim_id": row.get("source_claim_id", ""),
            "target_claim_id": row.get("target_claim_id", ""),
            "linkage_status": row.get("linkage_status", ""),
            "confidence_level": row.get("confidence_level", ""),
            "temporal_proximity": (
                "STRONG" if parse_amount(row.get("lag_days", 999)) <= 3
                else ("MODERATE" if parse_amount(row.get("lag_days", 999)) <= 14 else "WEAK")
            ),
            "semantic_compatibility": (
                "STRONG" if row.get("cross_family") == "N" or row.get("source_family") == row.get("target_family")
                else "CROSS_FAMILY"
            ),
            "amount_alignment": row.get("amount_aligned", "N"),
            "linkage_rationale": row.get("linkage_rationale", ""),
        })
    for rej in rejected_rows:
        confidence_rows.append({
            "source_claim_id": rej.get("source_claim_id", ""),
            "target_claim_id": rej.get("target_claim_id", ""),
            "linkage_status": "REJECTED_LINKAGE",
            "confidence_level": rej.get("confidence_level", "LOW_CONFIDENCE"),
            "temporal_proximity": "WEAK",
            "semantic_compatibility": "REJECTED",
            "amount_alignment": "N",
            "linkage_rationale": rej.get("linkage_rationale", ""),
        })
    confidence_df = pd.DataFrame(confidence_rows).drop_duplicates().sort_values(
        ["source_claim_id", "linkage_status"],
    ).reset_index(drop=True) if confidence_rows else pd.DataFrame()

    baseline_funded_no = int((chain_summary["chain_status"] == "FUNDED_NO_DISBURSEMENT").sum())
    baseline_orphan = len(orphan_analysis) if not orphan_analysis.empty else 0
    linked_sources = set(accepted_df["source_claim_id"].tolist())
    orphan_reduced = int(sum(
        1 for cid in linked_sources
        if chain_summary_map.get(cid, {}).get("chain_status") in {"FUNDED_NO_DISBURSEMENT", "ORPHAN_CHAIN"}
    ))

    baseline_balanced = int((revised_fin["revised_balancing_status"] == "BALANCED").sum())
    enhanced_balanced = int((balancing_df["enhanced_balancing_status"] == "BALANCED").sum())
    baseline_unbalanced = len(revised_fin) - baseline_balanced
    newly_balanced = int((
        (balancing_df["baseline_balancing_status"] != "BALANCED")
        & (balancing_df["enhanced_balancing_status"] == "BALANCED")
    ).sum())

    orphan_reduction = []
    for family, sub in chain_summary.groupby("claim_family"):
        fam_funded = int((sub["chain_status"] == "FUNDED_NO_DISBURSEMENT").sum())
        fam_linked = int(sum(
            1 for cid in linked_sources
            if cid in sub["reconstructed_claim_id"].values
            and chain_summary_map.get(cid, {}).get("chain_status") == "FUNDED_NO_DISBURSEMENT"
        ))
        fam_orphan = int(sum(1 for cid in orphan_ids if header_map.get(cid, {}).get("claim_family") == family))
        fam_orphan_reduced = int(sum(
            1 for cid in linked_sources
            if cid in orphan_ids and header_map.get(cid, {}).get("claim_family") == family
        ))
        bal_sub = balancing_df[balancing_df["claim_family"] == family]
        fam_new_bal = int((
            (bal_sub["baseline_balancing_status"] != "BALANCED")
            & (bal_sub["enhanced_balancing_status"] == "BALANCED")
        ).sum())
        orphan_reduction.append({
            "claim_family": family,
            "baseline_funded_no_disbursement": fam_funded,
            "linkage_accepted_count": fam_linked,
            "funded_no_disbursement_reduction_pct": round((fam_linked / fam_funded * 100) if fam_funded else 0, 2),
            "baseline_orphan_count": fam_orphan,
            "orphan_reduced_count": fam_orphan_reduced,
            "orphan_reduction_pct": round((fam_orphan_reduced / fam_orphan * 100) if fam_orphan else 0, 2),
            "baseline_balanced_count": int((bal_sub["baseline_balancing_status"] == "BALANCED").sum()),
            "enhanced_balanced_count": int((bal_sub["enhanced_balancing_status"] == "BALANCED").sum()),
            "balancing_improvement_count": fam_new_bal,
            "balancing_improvement_pct": round(
                (fam_new_bal / len(bal_sub) * 100) if len(bal_sub) else 0, 2,
            ),
        })

    orphan_reduction_df = pd.DataFrame(orphan_reduction).sort_values("claim_family").reset_index(drop=True)

    stats = {
        "total_claims": len(header_map),
        "linkage_candidates_evaluated": len(cand_df),
        "accepted_linkages": len(accepted_df),
        "possible_matches": len(possible_df),
        "rejected_linkages": len(rejected_rows),
        "cross_family_linkages": len(cross_family_df),
        "enhanced_groups": len(set(enhanced_groups_df["enhanced_settlement_group_id"])),
        "baseline_funded_no_disbursement": baseline_funded_no,
        "orphan_reduced_count": orphan_reduced,
        "baseline_balanced": baseline_balanced,
        "enhanced_balanced": enhanced_balanced,
        "newly_balanced": newly_balanced,
        "linkage_status_distribution": cand_df["linkage_status"].value_counts().to_dict() if "linkage_status" in cand_df.columns else {},
        "confidence_distribution": confidence_df["confidence_level"].value_counts().to_dict() if not confidence_df.empty else {},
    }

    reports = {
        "cross_claim_linkage_candidates.csv": cand_df,
        "enhanced_settlement_groups.csv": enhanced_groups_df,
        "grouping_overlay_analysis.csv": overlay_df,
        "orphan_reduction_analysis.csv": orphan_reduction_df,
        "cross_family_linkage_analysis.csv": cross_family_df,
        "enhanced_balancing_impact.csv": balancing_df,
        "linkage_confidence_analysis.csv": confidence_df,
    }

    rules_out = os.path.join(output_dir, "cross_claim_linkage_rules.json")
    shutil.copy2(linkage_rules_path, rules_out)
    output_files = [rules_out]

    for name, frame in reports.items():
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        output_files.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_txt = os.path.join(output_dir, "enhanced_grouping_summary.txt")
    write_summary_txt(summary_txt, stats, orphan_reduction_df, output_files, accepted_df)
    output_files.append(summary_txt)
    logger.info("Wrote enhanced_grouping_summary.txt")

    return stats, output_files


def write_summary_txt(path, stats, orphan_reduction_df, output_files, accepted_df):
    lines = [
        "=== Cross-Claim Settlement Linkage Summary (Phase 7B) ===",
        "",
        f"Total claims analyzed: {stats['total_claims']}",
        f"Linkage candidates evaluated: {stats['linkage_candidates_evaluated']}",
        f"Accepted linkages: {stats['accepted_linkages']}",
        f"Possible matches (not accepted): {stats['possible_matches']}",
        f"Rejected linkages: {stats['rejected_linkages']}",
        f"Cross-family linkages: {stats['cross_family_linkages']}",
        f"Enhanced settlement groups: {stats['enhanced_groups']}",
        "",
        "Linkage status distribution:",
    ]
    for status, count in sorted(stats.get("linkage_status_distribution", {}).items()):
        lines.append(f"  {status}: {count}")
    lines.extend([
        "",
        "Confidence distribution:",
    ])
    for level, count in sorted(stats.get("confidence_distribution", {}).items()):
        lines.append(f"  {level}: {count}")
    lines.extend([
        "",
        "Orphan / funded-no-disbursement impact:",
        f"  Baseline FUNDED_NO_DISBURSEMENT (Phase 7A): {stats['baseline_funded_no_disbursement']}",
        f"  Orphan-reduced via accepted linkage: {stats['orphan_reduced_count']}",
        "",
        "Balancing impact (Phase 6 baseline vs enhanced overlay):",
        f"  Baseline balanced (Phase 6): {stats['baseline_balanced']}",
        f"  Enhanced balanced (with linkage overlay): {stats['enhanced_balanced']}",
        f"  Newly balanced via linkage: {stats['newly_balanced']}",
        "",
        "Family-specific orphan reduction:",
    ])
    for _, row in orphan_reduction_df.iterrows():
        lines.append(
            f"  {row['claim_family']}: funded-no-disbursement reduction {row['funded_no_disbursement_reduction_pct']}% "
            f"({row['linkage_accepted_count']}/{row['baseline_funded_no_disbursement']}); "
            f"balancing +{row['balancing_improvement_count']} claims"
        )
    lines.extend([
        "",
        "Cross-family linkage observations:",
    ])
    if accepted_df.empty:
        lines.append("  No accepted cross-family linkages.")
    else:
        if "source_family" in accepted_df.columns:
            for pair, sub in accepted_df.groupby(["source_family", "target_family"]):
                lines.append(f"  {pair[0]} -> {pair[1]}: {len(sub)} accepted")
    lines.extend([
        "",
        "Architectural notes:",
        "  - Original reconstructed_claim_id preserved on all rows",
        "  - enhanced_settlement_group_id is overlay-only; Phase 4 outputs unchanged",
        "  - Enhanced balancing is side-by-side measurement only",
        "",
        "Output files generated:",
    ])
    for f in output_files:
        lines.append(f"  - {f}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Phase 7B cross-claim settlement linkage engine.")
    parser.add_argument("--headers", default=os.path.join(PHASE4, "claim_candidate_header.csv"))
    parser.add_argument("--financials", default=os.path.join(PHASE4, "claim_candidate_financials.csv"))
    parser.add_argument("--lifecycle", default=os.path.join(PHASE4, "claim_candidate_lifecycle.csv"))
    parser.add_argument("--revised-financials", default=os.path.join(PHASE6, "revised_claim_financials.csv"))
    parser.add_argument("--chain-summary", default=os.path.join(PHASE7A, "settlement_chain_summary.csv"))
    parser.add_argument("--delayed-detection", default=os.path.join(PHASE7A, "delayed_payout_detection.csv"))
    parser.add_argument("--orphan-analysis", default=os.path.join(PHASE7A, "orphan_chain_analysis.csv"))
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
        ("Lifecycle", args.lifecycle),
        ("Revised financials", args.revised_financials),
        ("Chain summary", args.chain_summary),
        ("Delayed detection", args.delayed_detection),
        ("Orphan analysis", args.orphan_analysis),
        ("Linkage rules", args.rules),
        ("Settlement rules", args.settlement_rules),
        ("Balancing rules", args.balancing_rules),
    )
    for label, path in required:
        if not os.path.isfile(path):
            logger.error("%s not found: %s", label, path)
            return 1

    headers = load_csv(args.headers)
    financials = load_csv(args.financials)
    lifecycle = load_csv(args.lifecycle)
    revised_fin = load_csv(args.revised_financials)
    chain_summary = load_csv(args.chain_summary)
    delayed_detection = load_csv(args.delayed_detection)
    orphan_analysis = load_csv(args.orphan_analysis)

    try:
        stats, outputs = run_engine(
            headers, financials, lifecycle, revised_fin, chain_summary,
            delayed_detection, orphan_analysis,
            args.balancing_rules, args.settlement_rules, args.rules, args.output,
        )
        print(f"Cross-claim linkage analysis complete. Claims: {stats['total_claims']}")
        print(f"Accepted linkages: {stats['accepted_linkages']}")
        print(f"Newly balanced via overlay: {stats['newly_balanced']}")
        print(f"Output: {os.path.abspath(args.output)}")
        for p in outputs:
            print(f"  {p}")
        return 0
    except (ValueError, FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
