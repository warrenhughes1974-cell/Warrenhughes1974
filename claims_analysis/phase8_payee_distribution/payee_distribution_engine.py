#!/usr/bin/env python3
"""
Phase 8 — PRELSA payee distribution and claim payment staging intelligence (read-only).

Links death claim payout decomposition to PRELSA relationship hierarchy.
Does NOT modify app.py, prior phase outputs, or generate QUIKCLMS/QUIKCLMP DBFs.
"""

import argparse
import json
import logging
import os
import re
import shutil
import sys
from collections import defaultdict

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
CONFIG_DIR = os.path.join(ROOT, "config")
if CONFIG_DIR not in sys.path:
    sys.path.insert(0, CONFIG_DIR)
from resolve_claims_source_paths import resolve_prelsa_path

DEFAULT_RULES = os.path.join(ROOT, "config", "payee_distribution_rules.json")
DEFAULT_RELATIONSHIP_SEMANTICS = os.path.join(ROOT, "config", "relationship_code_semantics.json")
DEFAULT_PRELSA = resolve_prelsa_path()
PHASE4 = os.path.join(ROOT, "phase4_claim_event_reconstruction")
PHASE7A = os.path.join(ROOT, "phase7_settlement_chain_intelligence")
PHASE7B = os.path.join(ROOT, "phase7b_cross_claim_linkage")
PHASE7C = os.path.join(ROOT, "phase7c_death_claim_decomposition")
PHASE3_OUTPUT = os.path.join(ROOT, "output")
DEFAULT_OUTPUT = os.path.join(ROOT, "phase8_payee_distribution_intelligence")

logger = logging.getLogger("payee_distribution_engine")


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


def is_dash_only(value):
    s = strip_val(value)
    return bool(s) and set(s.replace(" ", "")) == {"-"}


def is_present(value):
    s = strip_val(value)
    if not s or s.lower() in {"nan", "none"}:
        return False
    compact = s.replace(" ", "")
    if set(compact) == {"0"}:
        return False
    if compact in {"0000000000", "000000000", "00000000"}:
        return False
    return True


def is_separator_row(row):
    if is_dash_only(row.get("POLICY_NUMBER")) or is_dash_only(row.get("RELATE_CODE")):
        return True
    return is_dash_only(row.get("NAME_ID"))


def normalize_prelsa_columns(df):
    df = df.copy()
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df


def load_prelsa(path):
    logger.info("Reading PRELSA extract: %s", path)
    df = pd.read_csv(path, encoding="latin1", dtype=str, low_memory=False, on_bad_lines="skip")
    df = normalize_prelsa_columns(df)
    sep_mask = df.apply(is_separator_row, axis=1)
    df = df[~sep_mask].copy()
    df["policy_norm"] = df["POLICY_NUMBER"].apply(strip_val)
    df["name_id_norm"] = df["NAME_ID"].apply(strip_val)
    df["relate_code_norm"] = df["RELATE_CODE"].apply(strip_val)
    df["benefit_seq_norm"] = df["BENEFIT_SEQ_NUMBER"].apply(strip_val)
    df["has_address"] = df["ADDR_LINE_1"].apply(is_present) if "ADDR_LINE_1" in df.columns else False
    df["has_tax_id"] = df.apply(
        lambda r: is_present(r.get("SOC_SEC_NUMBER", "")) or is_present(r.get("BUSINESS_TAX_CODE", "")),
        axis=1,
    )
    logger.info("Loaded %s usable PRELSA rows", len(df))
    return df


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


def priority_order(rules, semantics):
    tiers = rules.get("relationship_priority_tiers", {})
    order = []
    for tier in ("primary", "secondary", "fallback"):
        order.extend(tiers.get(tier, []))
    role_meta = semantics.get("roles", {})
    return order, role_meta


def role_priority(code, order):
    code = strip_val(code)
    if code in order:
        return order.index(code)
    return 999


def build_policy_relationships(prelsa_df, order):
    by_policy = defaultdict(list)
    seen = defaultdict(set)
    for _, row in prelsa_df.iterrows():
        policy = row["policy_norm"]
        name_id = row["name_id_norm"]
        code = row["relate_code_norm"]
        if not policy or not name_id or not code:
            continue
        key = (name_id, code)
        if key in seen[policy]:
            continue
        seen[policy].add(key)
        by_policy[policy].append({
            "name_id": name_id,
            "relate_code": code,
            "benefit_seq": row.get("benefit_seq_norm", ""),
            "has_address": "Y" if row.get("has_address") else "N",
            "has_tax_id": "Y" if row.get("has_tax_id") else "N",
            "priority_rank": role_priority(code, order),
        })
    for policy in by_policy:
        by_policy[policy].sort(key=lambda r: (r["priority_rank"], r["relate_code"], r["name_id"]))
    return by_policy


def filter_roles(relationships, codes):
    allowed = {strip_val(c) for c in codes}
    return [r for r in relationships if r["relate_code"] in allowed]


def amounts_equal(amounts, tolerance):
    if not amounts:
        return False
    first = amounts[0]
    return all(abs(a - first) <= tolerance for a in amounts)


def detect_equal_split(payout_amounts, rules):
    tol = rules.get("equal_split_tolerance", 0.02)
    return amounts_equal(payout_amounts, tol)


def dedupe_candidates(candidates):
    seen = set()
    out = []
    for c in candidates:
        key = (c["name_id"], c["relate_code"])
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def classify_distribution(
    payout_events, relationships, claim_payee, rules, decomposition,
):
    payout_count = len(payout_events)
    if payout_count == 0:
        return "PAYEE_UNRESOLVED", "No payout events in claim chain", []

    primary = filter_roles(relationships, rules.get("relationship_priority_tiers", {}).get("primary", []))
    secondary = filter_roles(relationships, rules.get("relationship_priority_tiers", {}).get("secondary", []))
    fallback = filter_roles(relationships, rules.get("relationship_priority_tiers", {}).get("fallback", []))
    trustees = filter_roles(relationships, rules.get("trustee_codes", []))
    beneficiaries = filter_roles(relationships, rules.get("beneficiary_codes", []))
    explicit_pe = filter_roles(relationships, rules.get("explicit_payee_codes", []))

    payout_amounts = [e["amount"] for e in payout_events]
    equal_split = detect_equal_split(payout_amounts, rules)

    assignments = []
    status = "PAYEE_UNRESOLVED"
    rationale = "No deterministic payee assignment available"

    if rules.get("business_rules", {}).get("trustee_precedence_when_present") and trustees:
        if payout_count >= 1:
            manager = trustees[0]
            for i, ev in enumerate(payout_events):
                assignments.append({
                    "payout_sequence": i + 1,
                    "payout_amount": ev["amount"],
                    "payout_code": ev["code"],
                    "payout_date": ev["date"],
                    "assigned_name_id": manager["name_id"],
                    "assigned_relate_code": manager["relate_code"],
                    "assignment_basis": "TRUSTEE_PRECEDENCE",
                    "inferred_share_pct": "",
                })
            status = "TRUSTEE_MANAGED_DISTRIBUTION"
            rationale = f"Payout routed via trustee/custodian role ({manager['relate_code']})"
            return status, rationale, assignments

    if payout_count == 1:
        candidate = None
        basis = ""
        if explicit_pe:
            candidate = explicit_pe[0]
            basis = "EXPLICIT_PE"
        elif beneficiaries:
            candidate = beneficiaries[0]
            basis = "PRIMARY_BENEFICIARY"
        elif primary:
            candidate = primary[0]
            basis = "PRIMARY_TIER"
        elif fallback:
            candidate = fallback[0]
            status = "OWNER_FALLBACK" if candidate["relate_code"] == "PO" else "INSURED_FALLBACK"
            basis = "FALLBACK_ROLE"
        if candidate:
            assignments.append({
                "payout_sequence": 1,
                "payout_amount": payout_events[0]["amount"],
                "payout_code": payout_events[0]["code"],
                "payout_date": payout_events[0]["date"],
                "assigned_name_id": candidate["name_id"],
                "assigned_relate_code": candidate["relate_code"],
                "assignment_basis": basis,
                "inferred_share_pct": "100.00" if basis != "FALLBACK_ROLE" else "",
            })
            if status not in {"OWNER_FALLBACK", "INSURED_FALLBACK"}:
                status = "SINGLE_PAYEE_MATCH"
                rationale = f"Single payout matched to {candidate['relate_code']} ({basis})"
            else:
                rationale = f"Single payout fallback to {candidate['relate_code']}"
            return status, rationale, assignments

    if payout_count > 1:
        candidates = dedupe_candidates(primary or beneficiaries or explicit_pe)
        if len(candidates) >= payout_count:
            status = "MULTI_BENEFICIARY_SPLIT"
            rationale = f"{payout_count} payouts aligned to {len(candidates)} relationship candidates"
            for i, ev in enumerate(payout_events):
                cand = candidates[i]
                pct = ""
                if equal_split and rules.get("business_rules", {}).get("do_not_force_percentages_unless_equal_split"):
                    pct = f"{round(100.0 / payout_count, 2):.2f}"
                assignments.append({
                    "payout_sequence": i + 1,
                    "payout_amount": ev["amount"],
                    "payout_code": ev["code"],
                    "payout_date": ev["date"],
                    "assigned_name_id": cand["name_id"],
                    "assigned_relate_code": cand["relate_code"],
                    "assignment_basis": "MULTI_BENEFICIARY_ORDER",
                    "inferred_share_pct": pct,
                })
            return status, rationale, assignments

        if len(candidates) == 1 and payout_count > 1:
            cand = candidates[0]
            dates = sorted({e["date"] for e in payout_events})
            if len(dates) > 1 or payout_count > 1:
                status = "STAGED_PAYEE_DISTRIBUTION"
                rationale = f"Multiple payouts staged to single payee candidate ({cand['relate_code']})"
                for i, ev in enumerate(payout_events):
                    assignments.append({
                        "payout_sequence": i + 1,
                        "payout_amount": ev["amount"],
                        "payout_code": ev["code"],
                        "payout_date": ev["date"],
                        "assigned_name_id": cand["name_id"],
                        "assigned_relate_code": cand["relate_code"],
                        "assignment_basis": "STAGED_SINGLE_PAYEE",
                        "inferred_share_pct": "",
                    })
                return status, rationale, assignments

        if candidates and len(candidates) < payout_count:
            status = "BENEFICIARY_INFERRED"
            rationale = (
                f"{payout_count} payouts exceed {len(candidates)} named beneficiaries; "
                "sequential assignment by priority"
            )
            for i, ev in enumerate(payout_events):
                cand = candidates[i % len(candidates)]
                assignments.append({
                    "payout_sequence": i + 1,
                    "payout_amount": ev["amount"],
                    "payout_code": ev["code"],
                    "payout_date": ev["date"],
                    "assigned_name_id": cand["name_id"],
                    "assigned_relate_code": cand["relate_code"],
                    "assignment_basis": "INFERRED_CYCLIC",
                    "inferred_share_pct": "",
                })
            return status, rationale, assignments

    if claim_payee.get("likely_payee_name_id"):
        for i, ev in enumerate(payout_events):
            assignments.append({
                "payout_sequence": i + 1,
                "payout_amount": ev["amount"],
                "payout_code": ev["code"],
                "payout_date": ev["date"],
                "assigned_name_id": claim_payee.get("likely_payee_name_id", ""),
                "assigned_relate_code": claim_payee.get("likely_payee_relationship", ""),
                "assignment_basis": "PHASE4_CLAIM_PAYEE",
                "inferred_share_pct": "",
            })
        status = "BENEFICIARY_INFERRED"
        rationale = "Assigned from Phase 4 claim payee resolution fallback"
        return status, rationale, assignments

    if fallback:
        fb = fallback[0]
        for i, ev in enumerate(payout_events):
            assignments.append({
                "payout_sequence": i + 1,
                "payout_amount": ev["amount"],
                "payout_code": ev["code"],
                "payout_date": ev["date"],
                "assigned_name_id": fb["name_id"],
                "assigned_relate_code": fb["relate_code"],
                "assignment_basis": "FALLBACK_ONLY",
                "inferred_share_pct": "",
            })
        status = "OWNER_FALLBACK" if fb["relate_code"] == "PO" else "INSURED_FALLBACK"
        rationale = f"Fallback assignment to {fb['relate_code']} only"
        return status, rationale, assignments

    return status, rationale, assignments


def score_confidence(status, assignments, relationships, payout_count, rules):
    if status == "PAYEE_UNRESOLVED":
        return "LOW_CONFIDENCE", "No deterministic payee assignment available"

    if not assignments:
        return "LOW_CONFIDENCE", "No payee assignments generated"

    assigned_codes = {a["assigned_relate_code"] for a in assignments}
    rel_map = {r["name_id"]: r for r in relationships}
    has_addr = all(rel_map.get(a["assigned_name_id"], {}).get("has_address") == "Y" for a in assignments if a["assigned_name_id"] in rel_map)
    has_tax = all(rel_map.get(a["assigned_name_id"], {}).get("has_tax_id") == "Y" for a in assignments if a["assigned_name_id"] in rel_map)

    beneficiaries = filter_roles(relationships, rules.get("beneficiary_codes", []))
    explicit_pe = filter_roles(relationships, rules.get("explicit_payee_codes", []))

    if status == "SINGLE_PAYEE_MATCH" and has_addr and has_tax and (explicit_pe or beneficiaries):
        return "HIGH_CONFIDENCE", "Single payee match with address and tax ID completeness"

    if status == "MULTI_BENEFICIARY_SPLIT" and len(beneficiaries) >= payout_count and has_addr:
        return "HIGH_CONFIDENCE", "Payout count aligns with beneficiary count; address present"

    if status in {"MULTI_BENEFICIARY_SPLIT", "STAGED_PAYEE_DISTRIBUTION", "TRUSTEE_MANAGED_DISTRIBUTION"}:
        return "MODERATE_CONFIDENCE", f"{status} with relationship hierarchy support"

    if status == "BENEFICIARY_INFERRED":
        return "INFERRED", "Payee inferred from relationship priority or Phase 4 resolution"

    if status in {"OWNER_FALLBACK", "INSURED_FALLBACK"}:
        return "LOW_CONFIDENCE", "Fallback role used; primary beneficiary/payee not confirmed"

    return "INFERRED", "Rule-based default payee distribution inference"


def is_focus_record(decomposition, rules):
    focus_statuses = set(rules.get("focus_decomposition_statuses", []))
    focus_patterns = set(rules.get("focus_settlement_patterns", []))
    if decomposition.get("decomposition_status", "") in focus_statuses:
        return "Y"
    if decomposition.get("settlement_pattern", "") in focus_patterns:
        return "Y"
    if parse_amount(decomposition.get("payout_event_count", 0)) >= 2:
        return "Y"
    return "N"


def extract_payout_events(detail_sub, rules):
    payout_codes = {format_tx_code(c) for c in rules.get("payout_codes", [])}
    exclude = set(rules.get("exclude_lifecycle_event_types", ["CLAIM_SETTLEMENT"]))
    events = []
    for _, row in detail_sub.sort_values("lifecycle_event_order").iterrows():
        if row.get("lifecycle_event_type", "") in exclude:
            continue
        code = format_tx_code(row.get("source_transaction_code", ""))
        role = strip_val(row.get("chain_role", "")).upper()
        if code in payout_codes or role == "PAYOUT":
            events.append({
                "order": row.get("lifecycle_event_order", ""),
                "code": code,
                "amount": parse_amount(row.get("trans_amount", 0)),
                "date": strip_val(row.get("effective_date", "")),
            })
    return events


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def run_engine(
    headers, payees, chain_detail, decomposition, multi_payout, enhanced_groups,
    prelsa_df, relationship_hierarchy, rules_path, semantics_path, output_dir,
):
    os.makedirs(output_dir, exist_ok=True)
    rules = load_json(rules_path)
    semantics = load_json(semantics_path)
    order, _role_meta = priority_order(rules, semantics)
    policy_rels = build_policy_relationships(prelsa_df, order)

    header_map = headers.set_index("reconstructed_claim_id").to_dict("index")
    payee_map = payees.set_index("reconstructed_claim_id").to_dict("index")
    decomp_map = decomposition.set_index("reconstructed_claim_id").to_dict("index")
    eg_map = enhanced_groups.set_index("reconstructed_claim_id").to_dict("index") if not enhanced_groups.empty else {}
    hier_map = relationship_hierarchy.set_index("policy_number").to_dict("index") if not relationship_hierarchy.empty else {}

    death_ids = sorted(
        headers.loc[headers["claim_family"] == "DEATH_CLAIM", "reconstructed_claim_id"].tolist()
    )
    detail = chain_detail.copy()
    detail["source_transaction_code"] = detail["source_transaction_code"].apply(format_tx_code)

    summaries = []
    detail_rows = []
    beneficiary_rows = []
    multi_ben_rows = []
    trustee_rows = []
    unresolved_rows = []
    staging_rows = []
    confidence_rows = []
    recommendations = []

    prefixes = rules.get("staging_prefixes", {})

    for claim_id in death_ids:
        header = header_map.get(claim_id, {})
        policy = str(header.get("policy_number", "")).strip()
        decomp = decomp_map.get(claim_id, {})
        claim_payee = payee_map.get(claim_id, {})
        eg = eg_map.get(claim_id, {})
        hier = hier_map.get(policy, {})

        relationships = policy_rels.get(policy, [])
        detail_sub = detail[detail["reconstructed_claim_id"] == claim_id]
        payout_events = extract_payout_events(detail_sub, rules)

        status, rationale, assignments = classify_distribution(
            payout_events, relationships, claim_payee, rules, decomp,
        )
        conf, conf_reason = score_confidence(
            status, assignments, relationships, len(payout_events), rules,
        )
        focus_flag = is_focus_record(decomp, rules)

        beneficiaries = filter_roles(relationships, rules.get("beneficiary_codes", []))
        primary_candidates = dedupe_candidates(filter_roles(
            relationships, rules.get("relationship_priority_tiers", {}).get("primary", []),
        ))
        trustees = filter_roles(relationships, rules.get("trustee_codes", []))
        payout_total = round(sum(e["amount"] for e in payout_events), 2)

        summaries.append({
            "reconstructed_claim_id": claim_id,
            "policy_number": policy,
            "enhanced_settlement_group_id": eg.get("enhanced_settlement_group_id", ""),
            "decomposition_status": decomp.get("decomposition_status", ""),
            "settlement_pattern": decomp.get("settlement_pattern", ""),
            "payee_distribution_status": status,
            "confidence_level": conf,
            "confidence_rationale": conf_reason,
            "focus_population_flag": focus_flag,
            "payout_event_count": len(payout_events),
            "payout_total": payout_total,
            "beneficiary_candidate_count": len(primary_candidates),
            "named_beneficiary_count": len(beneficiaries),
            "trustee_candidate_count": len(trustees),
            "relationship_candidate_count": len(relationships),
            "phase4_payee_name_id": claim_payee.get("likely_payee_name_id", ""),
            "phase4_payee_relate_code": claim_payee.get("likely_payee_relationship", ""),
            "distribution_rationale": rationale,
            "payout_beneficiary_alignment": (
                "ALIGNED" if len(primary_candidates) >= len(payout_events) and len(payout_events) > 0
                else ("PARTIAL" if primary_candidates else "NONE")
            ),
        })

        for asn in assignments:
            detail_rows.append({
                "reconstructed_claim_id": claim_id,
                "policy_number": policy,
                "payee_distribution_status": status,
                "payout_sequence": asn["payout_sequence"],
                "payout_code": asn["payout_code"],
                "payout_date": asn["payout_date"],
                "payout_amount": asn["payout_amount"],
                "assigned_name_id": asn["assigned_name_id"],
                "assigned_relate_code": asn["assigned_relate_code"],
                "assignment_basis": asn["assignment_basis"],
                "inferred_share_pct": asn["inferred_share_pct"],
                "confidence_level": conf,
            })

            staging_rows.append({
                "reconstructed_claim_id": claim_id,
                "policy_number": policy,
                "enhanced_settlement_group_id": eg.get("enhanced_settlement_group_id", ""),
                "payment_event_stage_candidate_id": f"{prefixes.get('payment_event', 'PESC')}-{claim_id}-P{asn['payout_sequence']}",
                "payee_distribution_candidate_id": f"{prefixes.get('payee_distribution', 'PDC')}-{claim_id}-P{asn['payout_sequence']}",
                "beneficiary_distribution_candidate_id": f"{prefixes.get('beneficiary_distribution', 'BDC')}-{claim_id}-P{asn['payout_sequence']}",
                "payout_sequence": asn["payout_sequence"],
                "payout_amount": asn["payout_amount"],
                "assigned_name_id": asn["assigned_name_id"],
                "assigned_relate_code": asn["assigned_relate_code"],
                "payee_distribution_status": status,
                "staging_readiness": "FUTURE_READY",
                "production_dbf_flag": "N",
                "confidence_level": conf,
            })

        if beneficiaries:
            for b in beneficiaries:
                beneficiary_rows.append({
                    "reconstructed_claim_id": claim_id,
                    "policy_number": policy,
                    "name_id": b["name_id"],
                    "relate_code": b["relate_code"],
                    "benefit_seq": b["benefit_seq"],
                    "priority_rank": b["priority_rank"],
                    "has_address": b["has_address"],
                    "has_tax_id": b["has_tax_id"],
                    "payout_event_count": len(payout_events),
                    "payee_distribution_status": status,
                })

        if status == "MULTI_BENEFICIARY_SPLIT" or len(payout_events) >= 2:
            multi_ben_rows.append({
                "reconstructed_claim_id": claim_id,
                "policy_number": policy,
                "payout_event_count": len(payout_events),
                "beneficiary_candidate_count": len(primary_candidates),
                "payout_total": payout_total,
                "equal_split_detected": "Y" if detect_equal_split([e["amount"] for e in payout_events], rules) else "N",
                "payee_distribution_status": status,
                "confidence_level": conf,
                "assignment_summary": "|".join(
                    f"{a['payout_sequence']}:{a['assigned_relate_code']}:{a['assigned_name_id']}"
                    for a in assignments
                ),
            })

        if status == "TRUSTEE_MANAGED_DISTRIBUTION" or trustees:
            for t in trustees:
                trustee_rows.append({
                    "reconstructed_claim_id": claim_id,
                    "policy_number": policy,
                    "trustee_name_id": t["name_id"],
                    "trustee_relate_code": t["relate_code"],
                    "payout_event_count": len(payout_events),
                    "payout_total": payout_total,
                    "trustee_managed_flag": "Y" if status == "TRUSTEE_MANAGED_DISTRIBUTION" else "N",
                    "payee_distribution_status": status,
                    "confidence_level": conf,
                })

        if status == "PAYEE_UNRESOLVED" or not assignments:
            unresolved_rows.append({
                "reconstructed_claim_id": claim_id,
                "policy_number": policy,
                "decomposition_status": decomp.get("decomposition_status", ""),
                "payout_event_count": len(payout_events),
                "beneficiary_candidate_count": len(primary_candidates),
                "relationship_candidate_count": len(relationships),
                "phase4_payee_name_id": claim_payee.get("likely_payee_name_id", ""),
                "unresolved_reason": rationale,
                "confidence_level": conf,
            })

        confidence_rows.append({
            "reconstructed_claim_id": claim_id,
            "policy_number": policy,
            "payee_distribution_status": status,
            "confidence_level": conf,
            "relationship_code_quality": (
                "STRONG" if beneficiaries or filter_roles(relationships, rules.get("explicit_payee_codes", []))
                else ("FALLBACK" if status in {"OWNER_FALLBACK", "INSURED_FALLBACK"} else "WEAK")
            ),
            "payout_count_alignment": (
                "MATCH" if len(primary_candidates) >= len(payout_events) and len(payout_events) > 0
                else "MISMATCH"
            ),
            "address_completeness": hier.get("possible_conflict_flag", claim_payee.get("address_available_flag", "")),
            "tax_id_completeness": claim_payee.get("tax_id_available_flag", ""),
            "confidence_rationale": conf_reason,
        })

    summary_df = pd.DataFrame(summaries).sort_values("reconstructed_claim_id").reset_index(drop=True)
    detail_df = pd.DataFrame(detail_rows).sort_values(
        ["reconstructed_claim_id", "payout_sequence"],
    ).reset_index(drop=True) if detail_rows else pd.DataFrame()
    beneficiary_df = pd.DataFrame(beneficiary_rows).sort_values(
        ["reconstructed_claim_id", "priority_rank"],
    ).reset_index(drop=True) if beneficiary_rows else pd.DataFrame()
    multi_ben_df = pd.DataFrame(multi_ben_rows).sort_values("reconstructed_claim_id").reset_index(drop=True) if multi_ben_rows else pd.DataFrame()
    trustee_df = pd.DataFrame(trustee_rows).sort_values("reconstructed_claim_id").reset_index(drop=True) if trustee_rows else pd.DataFrame()
    unresolved_df = pd.DataFrame(unresolved_rows).sort_values("reconstructed_claim_id").reset_index(drop=True) if unresolved_rows else pd.DataFrame()
    staging_df = pd.DataFrame(staging_rows).sort_values(
        ["reconstructed_claim_id", "payout_sequence"],
    ).reset_index(drop=True) if staging_rows else pd.DataFrame()
    confidence_df = pd.DataFrame(confidence_rows).sort_values("reconstructed_claim_id").reset_index(drop=True)

    with_payout = summary_df[summary_df["payout_event_count"].apply(parse_amount) > 0]
    aligned = with_payout[with_payout["payout_beneficiary_alignment"] == "ALIGNED"]

    if int((summary_df["payee_distribution_status"] == "PAYEE_UNRESOLVED").sum()) > 0:
        recommendations.append({
            "observed_pattern": f"{int((summary_df['payee_distribution_status'] == 'PAYEE_UNRESOLVED').sum())} unresolved payee distributions",
            "root_cause": "Missing PRELSA beneficiaries or zero payout events in reconstruction group",
            "recommended_action": "Review unresolved_payee_analysis.csv; validate PRELSA completeness per policy",
            "expected_impact": "MEDIUM",
            "confidence_level": "MODERATE_CONFIDENCE",
        })
    if int((summary_df["payee_distribution_status"] == "MULTI_BENEFICIARY_SPLIT").sum()) > 0:
        recommendations.append({
            "observed_pattern": f"{int((summary_df['payee_distribution_status'] == 'MULTI_BENEFICIARY_SPLIT').sum())} multi-beneficiary splits detected",
            "root_cause": "Payout count aligns with PRELSA beneficiary hierarchy",
            "recommended_action": "Use payment_payee_staging_candidates.csv for future QUIKCLMP derivation",
            "expected_impact": "HIGH",
            "confidence_level": "HIGH_CONFIDENCE",
        })
    if int((summary_df["payee_distribution_status"] == "BENEFICIARY_INFERRED").sum()) > 0:
        recommendations.append({
            "observed_pattern": f"{int((summary_df['payee_distribution_status'] == 'BENEFICIARY_INFERRED').sum())} inferred beneficiary distributions",
            "root_cause": "Payout count exceeds named beneficiary count",
            "recommended_action": "Manual validation before production payee assignment",
            "expected_impact": "MEDIUM",
            "confidence_level": "INFERRED",
        })

    rec_df = pd.DataFrame(recommendations).reset_index(drop=True) if recommendations else pd.DataFrame()

    stats = {
        "total_death_claims": len(summary_df),
        "focus_population": int((summary_df["focus_population_flag"] == "Y").sum()),
        "payout_chains_analyzed": len(with_payout),
        "beneficiary_linked_payouts": int((summary_df["payee_distribution_status"].isin({
            "SINGLE_PAYEE_MATCH", "MULTI_BENEFICIARY_SPLIT", "TRUSTEE_MANAGED_DISTRIBUTION",
        })).sum()),
        "inferred_distributions": int((summary_df["payee_distribution_status"] == "BENEFICIARY_INFERRED").sum()),
        "unresolved_payouts": int((summary_df["payee_distribution_status"] == "PAYEE_UNRESOLVED").sum()),
        "trustee_managed": int((summary_df["payee_distribution_status"] == "TRUSTEE_MANAGED_DISTRIBUTION").sum()),
        "staged_payouts": int((summary_df["payee_distribution_status"] == "STAGED_PAYEE_DISTRIBUTION").sum()),
        "multi_beneficiary": int((summary_df["payee_distribution_status"] == "MULTI_BENEFICIARY_SPLIT").sum()),
        "payout_beneficiary_alignment_pct": round(
            (len(aligned) / len(with_payout) * 100) if len(with_payout) else 0, 2,
        ),
        "status_distribution": summary_df["payee_distribution_status"].value_counts().to_dict(),
        "confidence_distribution": summary_df["confidence_level"].value_counts().to_dict(),
        "staging_candidates": len(staging_df),
    }

    reports = {
        "payee_distribution_summary.csv": summary_df,
        "payee_distribution_detail.csv": detail_df,
        "beneficiary_distribution_analysis.csv": beneficiary_df,
        "multi_beneficiary_split_analysis.csv": multi_ben_df,
        "trustee_custodian_distribution_analysis.csv": trustee_df,
        "unresolved_payee_analysis.csv": unresolved_df,
        "payment_payee_staging_candidates.csv": staging_df,
        "payee_distribution_confidence_analysis.csv": confidence_df,
        "payee_distribution_recommendations.csv": rec_df,
    }

    rules_out = os.path.join(output_dir, "payee_distribution_rules.json")
    shutil.copy2(rules_path, rules_out)
    output_files = [rules_out]

    for name, frame in reports.items():
        path = os.path.join(output_dir, name)
        frame.to_csv(path, index=False, encoding="utf-8")
        output_files.append(path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_txt = os.path.join(output_dir, "payee_distribution_summary.txt")
    write_summary_txt(summary_txt, stats, summary_df, output_files)
    output_files.append(summary_txt)
    logger.info("Wrote payee_distribution_summary.txt")

    return stats, output_files


def write_summary_txt(path, stats, summary_df, output_files):
    lines = [
        "=== PRELSA Payee Distribution Intelligence Summary (Phase 8) ===",
        "",
        f"Total DEATH_CLAIM analyzed: {stats['total_death_claims']}",
        f"Focus population: {stats['focus_population']}",
        f"Payout chains analyzed: {stats['payout_chains_analyzed']}",
        "",
        "Payee distribution status distribution:",
    ]
    for status, count in sorted(stats.get("status_distribution", {}).items()):
        lines.append(f"  {status}: {count}")
    lines.extend([
        "",
        "Key metrics:",
        f"  Beneficiary-linked payouts: {stats['beneficiary_linked_payouts']}",
        f"  Inferred distributions: {stats['inferred_distributions']}",
        f"  Unresolved payouts: {stats['unresolved_payouts']}",
        f"  Trustee-managed payouts: {stats['trustee_managed']}",
        f"  Staged payouts: {stats['staged_payouts']}",
        f"  Multi-beneficiary distributions: {stats['multi_beneficiary']}",
        f"  Payout-to-beneficiary alignment: {stats['payout_beneficiary_alignment_pct']}%",
        f"  Payment/payee staging candidates: {stats['staging_candidates']}",
        "",
        "Confidence distribution:",
    ])
    for level, count in sorted(stats.get("confidence_distribution", {}).items()):
        lines.append(f"  {level}: {count}")
    lines.extend([
        "",
        "Architectural notes:",
        "  - Staging candidates are future-ready only; no QUIKCLMP/QUIKCLMS generation",
        "  - Original reconstructed_claim_id and enhanced_settlement_group_id preserved",
        "  - No prior phase outputs modified",
        "",
        "Recommended next phase:",
        "  - Phase 9: Canonical QUIKCLMP staging derivation from payment_payee_staging_candidates",
        "",
        "Output files generated:",
    ])
    for f in output_files:
        lines.append(f"  - {f}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Phase 8 PRELSA payee distribution engine.")
    parser.add_argument("--headers", default=os.path.join(PHASE4, "claim_candidate_header.csv"))
    parser.add_argument("--payees", default=os.path.join(PHASE4, "claim_candidate_payees.csv"))
    parser.add_argument("--chain-detail", default=os.path.join(PHASE7A, "settlement_chain_detail.csv"))
    parser.add_argument("--decomposition", default=os.path.join(PHASE7C, "death_claim_decomposition_summary.csv"))
    parser.add_argument("--multi-payout", default=os.path.join(PHASE7C, "death_claim_multi_payout_analysis.csv"))
    parser.add_argument("--enhanced-groups", default=os.path.join(PHASE7B, "enhanced_settlement_groups.csv"))
    parser.add_argument("--prelsa", default=DEFAULT_PRELSA)
    parser.add_argument("--relationship-hierarchy", default=os.path.join(PHASE3_OUTPUT, "relationship_hierarchy_analysis.csv"))
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--semantics", default=DEFAULT_RELATIONSHIP_SEMANTICS)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    required = (
        ("Headers", args.headers),
        ("Payees", args.payees),
        ("Chain detail", args.chain_detail),
        ("Decomposition", args.decomposition),
        ("PRELSA", args.prelsa),
        ("Rules", args.rules),
        ("Semantics", args.semantics),
    )
    for label, path in required:
        if not os.path.isfile(path):
            logger.error("%s not found: %s", label, path)
            return 1

    headers = load_csv(args.headers)
    payees = load_csv(args.payees)
    chain_detail = load_csv(args.chain_detail)
    decomposition = load_csv(args.decomposition)
    multi_payout = load_csv(args.multi_payout) if os.path.isfile(args.multi_payout) else pd.DataFrame()
    enhanced_groups = load_csv(args.enhanced_groups) if os.path.isfile(args.enhanced_groups) else pd.DataFrame()
    prelsa_df = load_prelsa(args.prelsa)
    relationship_hierarchy = (
        load_csv(args.relationship_hierarchy)
        if os.path.isfile(args.relationship_hierarchy) else pd.DataFrame()
    )

    try:
        stats, outputs = run_engine(
            headers, payees, chain_detail, decomposition, multi_payout, enhanced_groups,
            prelsa_df, relationship_hierarchy, args.rules, args.semantics, args.output,
        )
        print(f"Payee distribution analysis complete. Death claims: {stats['total_death_claims']}")
        print(f"Staging candidates: {stats['staging_candidates']}")
        print(f"Unresolved: {stats['unresolved_payouts']}")
        print(f"Output: {os.path.abspath(args.output)}")
        for p in outputs:
            print(f"  {p}")
        return 0
    except (ValueError, FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
