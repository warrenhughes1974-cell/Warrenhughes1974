#!/usr/bin/env python3
"""
Phase 4 — Claim event reconstruction prototype (read-only).

Deterministic staging reconstruction from PACTG + semantic catalog + PRELSA.
Does NOT modify app.py or generate QUIKCLMS/QUIKCLMP DBF output.
"""

import argparse
import logging
import os
import re
import sys
from datetime import datetime

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
PHASE1_PROFILER_DIR = os.path.join(ROOT, "phase1_pactg_transaction_profiling", "profiler")
DEFAULT_CATALOG = os.path.join(
    ROOT, "phase2_semantic_catalog", "catalog", "Claims_Transaction_Code_Catalog.csv",
)
DEFAULT_REL_RULES = os.path.join(
    ROOT, "phase1_pactg_transaction_profiling", "relationship_resolution_recommendations.csv",
)

DATE_CLUSTER_DAYS = 60
BALANCE_TOLERANCE = 0.01
MINOR_VARIANCE = 100.0

FAMILY_GROUPS = {
    "DEATH_CLAIM": {
        "DEATH_BENEFIT", "DEATH_BENEFIT_INTEREST", "DEATH_CLAIM_CLEARING",
        "DEATH_CLAIM_PAYOUT", "DEATH_CLAIM_PRORATA_SURRENDER",
    },
    "SURRENDER_CLAIM": {
        "TOTAL_CASH", "PARTIAL_SURRENDER", "SURRENDER_CHARGE",
        "LOAN_PRINCIPAL_OFFSET", "LOAN_INTEREST_OFFSET",
    },
    "DISBURSEMENT_CLAIM": {
        "CASH_DISBURSEMENT", "CLAIM_CASH_DISBURSEMENT", "CLAIM_PAYMENT",
    },
    "TAX_CLAIM": {
        "FEDERAL_NON_WITHHOLDING", "FEDERAL_INTEREST_WITHHOLDING",
    },
}

LIFECYCLE_EVENT_BY_ROLE = {
    "BENEFIT_ESTABLISHMENT": "CLAIM_FUNDED",
    "INTEREST_ACCRUAL": "CLAIM_INTEREST",
    "OFFSET": "CLAIM_OFFSET",
    "TAX_TREATMENT": "CLAIM_WITHHOLDING",
    "PAYMENT_OUT": "CLAIM_PAYMENT",
    "CLEARING_HUB": "CLAIM_ESTABLISHED",
    "FEE_DEDUCTION": "CLAIM_OFFSET",
    "PAYOUT": "CLAIM_PAYMENT",
    "DISBURSEMENT": "CLAIM_PAYMENT",
    "BENEFIT_ADJUSTMENT": "CLAIM_FUNDED",
}

PAYEE_PRIORITY = ["PE", "B1", "B2", "TR", "CU", "PO", "AS", "IN"]

logger = logging.getLogger("claim_event_reconstructor")


# ---------------------------------------------------------------------------
# Import shared loaders
# ---------------------------------------------------------------------------

def _ensure_import_paths():
    for path in (ROOT, PHASE1_PROFILER_DIR):
        if path not in sys.path:
            sys.path.insert(0, path)


def import_helpers():
    _ensure_import_paths()
    from pactg_transaction_profiler import (  # noqa: WPS433
        load_pactg,
        norm_code,
        parse_effective_date,
    )
    from prelsa_relationship_profiler import (  # noqa: WPS433
        load_prelsa,
        strip_val,
        is_present,
        has_ssn,
        has_tin,
        entity_type,
    )
    return {
        "load_pactg": load_pactg,
        "norm_code": norm_code,
        "parse_effective_date": parse_effective_date,
        "load_prelsa": load_prelsa,
        "strip_val": strip_val,
        "is_present": is_present,
        "has_ssn": has_ssn,
        "has_tin": has_tin,
        "entity_type": entity_type,
    }


# ---------------------------------------------------------------------------
# Catalog / rules
# ---------------------------------------------------------------------------

def format_tx_code(code):
    digits = re.sub(r"[^0-9]", "", str(code))
    if not digits:
        return ""
    return str(int(digits)).zfill(4)


def load_catalog(path):
    df = pd.read_csv(path, dtype=str)
    df.columns = [c.strip().upper() for c in df.columns]
    catalog = {}
    for _, row in df.iterrows():
        key = format_tx_code(row["TRANSACTION_CODE"])
        if not key:
            continue
        catalog[key] = {
            "transaction_code": key,
            "known_description": strip_val_simple(row.get("KNOWN_DESCRIPTION", "")),
            "claim_relevant_flag": strip_val_simple(row.get("CLAIM_RELEVANT_FLAG", "")).upper(),
            "claim_family": strip_val_simple(row.get("CLAIM_FAMILY", "")),
            "financial_component": strip_val_simple(row.get("FINANCIAL_COMPONENT", "")),
            "lifecycle_role": strip_val_simple(row.get("LIFECYCLE_ROLE", "")),
            "payment_indicator": strip_val_simple(row.get("PAYMENT_INDICATOR", "")).upper(),
            "tax_indicator": strip_val_simple(row.get("TAX_INDICATOR", "")).upper(),
            "interest_indicator": strip_val_simple(row.get("INTEREST_INDICATOR", "")).upper(),
            "loan_offset_indicator": strip_val_simple(row.get("LOAN_OFFSET_INDICATOR", "")).upper(),
            "surrender_indicator": strip_val_simple(row.get("SURRENDER_INDICATOR", "")).upper(),
        }
    return catalog


def load_relationship_rules(path):
    df = pd.read_csv(path, dtype=str)
    df.columns = [c.strip().upper() for c in df.columns]
    rules = {}
    for _, row in df.iterrows():
        scenario = strip_val_simple(row.get("CLAIM_SCENARIO", ""))
        if scenario:
            rules[scenario] = row.to_dict()
    return rules


def strip_val_simple(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def super_family(claim_family):
    for group, members in FAMILY_GROUPS.items():
        if claim_family in members:
            return group
    return claim_family or "UNCLASSIFIED"


def scenario_for_group(group_family):
    return {
        "DEATH_CLAIM": "death_claim_payment",
        "SURRENDER_CLAIM": "surrender_payment",
        "DISBURSEMENT_CLAIM": "missing_payee_relationship",
        "TAX_CLAIM": "missing_payee_relationship",
    }.get(group_family, "missing_payee_relationship")


# ---------------------------------------------------------------------------
# Row annotation
# ---------------------------------------------------------------------------

def row_catalog_match(credit_code, debit_code, catalog, norm_code_fn):
    cc = norm_code_fn(credit_code)
    dc = norm_code_fn(debit_code)
    matches = []
    for code in (cc, dc):
        if not code:
            continue
        meta = catalog.get(format_tx_code(code))
        if meta and meta["claim_relevant_flag"] == "Y":
            matches.append((code, meta))
    if not matches:
        return None, None
    for code, meta in matches:
        if meta["financial_component"] != "CLEARING":
            return code, meta
    return matches[0][0], matches[0][1]


def annotate_claim_rows(pactg_df, catalog, helpers):
    norm_code_fn = helpers["norm_code"]
    rows = []
    for _, row in pactg_df.iterrows():
        code, meta = row_catalog_match(
            row.get("CREDIT_CODE", ""),
            row.get("DEBIT_CODE", ""),
            catalog,
            norm_code_fn,
        )
        if not meta:
            continue
        eff = row.get("effective_date_parsed")
        eff_str = eff.strftime("%Y%m%d") if pd.notna(eff) else strip_val_simple(row.get("EFFECTIVE_DATE", ""))
        amt = row.get("amount_parsed")
        rows.append({
            "policy_number": row["policy_norm"],
            "benefit_seq": strip_val_simple(row.get("BENEFIT_SEQ", "")) or "0",
            "effective_date": eff_str,
            "effective_date_parsed": eff,
            "credit_code": strip_val_simple(row.get("CREDIT_CODE", "")),
            "debit_code": strip_val_simple(row.get("DEBIT_CODE", "")),
            "trans_amount_raw": strip_val_simple(row.get("TRANS_AMOUNT", "")),
            "trans_amount": amt if amt is not None else 0.0,
            "distribution_code": strip_val_simple(row.get("DISTRIBUTION_CODE", "")),
            "payee_rela_code": strip_val_simple(row.get("PAYEE_RELA_CODE", "")),
            "payee_sequence": strip_val_simple(row.get("PAYEE_SEQUENCE", "")),
            "description": strip_val_simple(row.get("DESCRIPTION", "")),
            "source_row_number": row.get("source_row_number", ""),
            "primary_code": code,
            "transaction_code": format_tx_code(code),
            "claim_family": meta["claim_family"],
            "claim_subtype": meta["known_description"],
            "financial_component": meta["financial_component"],
            "lifecycle_role": meta["lifecycle_role"],
            "payment_indicator": meta["payment_indicator"],
            "tax_indicator": meta["tax_indicator"],
            "interest_indicator": meta["interest_indicator"],
            "loan_offset_indicator": meta["loan_offset_indicator"],
            "surrender_indicator": meta["surrender_indicator"],
            "group_family": super_family(meta["claim_family"]),
            "reversal_flag": "Y" if (amt is not None and amt < 0) else "N",
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(
        ["policy_number", "benefit_seq", "group_family", "effective_date", "source_row_number"],
        ascending=[True, True, True, True, True],
    ).reset_index(drop=True)


def assign_claim_clusters(claim_rows):
    if claim_rows.empty:
        claim_rows["cluster_id"] = []
        claim_rows["reconstructed_claim_id"] = []
        return claim_rows

    cluster_ids = []
    claim_ids = []
    current_key = None
    current_cluster = 0
    last_date = None

    for _, row in claim_rows.iterrows():
        key = (row["policy_number"], row["benefit_seq"], row["group_family"])
        eff = row["effective_date_parsed"]
        if key != current_key:
            current_key = key
            current_cluster = 0
            last_date = eff
        elif pd.notna(eff) and pd.notna(last_date):
            gap = abs((eff - last_date).days)
            if gap > DATE_CLUSTER_DAYS:
                current_cluster += 1
        elif key == current_key and current_cluster == 0 and last_date is None and pd.notna(eff):
            last_date = eff

        if pd.notna(eff):
            last_date = eff

        cluster_ids.append(current_cluster)
        policy = row["policy_number"]
        first_date = row["effective_date"] or "NODATE"
        rcid = f"RC-{policy}-{row['benefit_seq']}-{row['group_family']}-C{current_cluster}-{first_date}"
        claim_ids.append(rcid)

    claim_rows = claim_rows.copy()
    claim_rows["cluster_id"] = cluster_ids
    claim_rows["reconstructed_claim_id"] = claim_ids

    # Stabilize claim id using min date per cluster
    stable_ids = {}
    for (policy, benefit, group, cluster), sub in claim_rows.groupby(
        ["policy_number", "benefit_seq", "group_family", "cluster_id"], sort=True,
    ):
        dates = [d for d in sub["effective_date"].tolist() if d]
        first_date = min(dates) if dates else "NODATE"
        stable_ids[(policy, benefit, group, cluster)] = (
            f"RC-{policy}-{benefit}-{group}-C{cluster}-{first_date}"
        )
    claim_rows["reconstructed_claim_id"] = claim_rows.apply(
        lambda r: stable_ids[(r["policy_number"], r["benefit_seq"], r["group_family"], r["cluster_id"])],
        axis=1,
    )
    return claim_rows


# ---------------------------------------------------------------------------
# PRELSA index
# ---------------------------------------------------------------------------

def build_prelsa_index(prelsa_df, helpers):
    strip_val_fn = helpers["strip_val"]
    is_present_fn = helpers["is_present"]
    entity_type_fn = helpers["entity_type"]
    has_ssn_fn = helpers["has_ssn"]
    has_tin_fn = helpers["has_tin"]

    index = {}
    for _, row in prelsa_df.iterrows():
        policy = row["policy_norm"]
        if not policy:
            continue
        rel = strip_val_fn(row.get("RELATE_CODE", ""))
        name_id = strip_val_fn(row.get("NAME_ID", ""))
        entry = {
            "name_id": name_id,
            "relate_code": rel,
            "entity_type": entity_type_fn(row),
            "address_present": is_present_fn(row.get("ADDR_LINE_1")),
            "tax_id_present": has_ssn_fn(row) or has_tin_fn(row),
            "trust_indicator": rel in {"TR", "CU"},
        }
        index.setdefault(policy, []).append(entry)
    return index


def resolve_payee(policy, group_family, claim_sub, prelsa_index, rel_rules, helpers):
    strip_val_fn = helpers["strip_val"]
    relationships = prelsa_index.get(policy, [])
    scenario = scenario_for_group(group_family)
    rule = rel_rules.get(scenario, {})
    priority_str = strip_val_simple(rule.get("RECOMMENDED_PRIORITY_ORDER", ""))
    priority = [c.strip() for c in priority_str.split("|") if c.strip()] or PAYEE_PRIORITY

    pactg_rela = ""
    if not claim_sub.empty:
        rels = [strip_val_fn(v) for v in claim_sub["payee_rela_code"].tolist() if strip_val_fn(v)]
        pactg_rela = rels[0] if rels else ""

    method = "UNRESOLVED"
    fallback = ""
    name_id = ""
    relate = ""

    if pactg_rela:
        for entry in relationships:
            if entry["relate_code"] == pactg_rela:
                name_id = entry["name_id"]
                relate = entry["relate_code"]
                method = "PACTG_PAYEE_RELA_CODE"
                break
        if not name_id:
            method = "PACTG_RELA_UNMATCHED"

    if not name_id:
        for code in priority:
            candidates = [e for e in relationships if e["relate_code"] == code]
            if candidates:
                entry = candidates[0]
                name_id = entry["name_id"]
                relate = entry["relate_code"]
                method = "PRELSA_PRIORITY"
                fallback = "|".join(priority[:priority.index(code) + 1])
                break

    if not name_id and relationships:
        entry = relationships[0]
        name_id = entry["name_id"]
        relate = entry["relate_code"]
        method = "PRELSA_FIRST_AVAILABLE"
        fallback = "FIRST_AVAILABLE"

    selected = next((e for e in relationships if e["name_id"] == name_id), None)
    return {
        "likely_payee_name_id": name_id,
        "likely_payee_relationship": relate,
        "payee_resolution_method": method,
        "fallback_strategy_used": fallback or strip_val_simple(rule.get("FALLBACK_ORDER", "")),
        "address_available_flag": "Y" if selected and selected["address_present"] else "N",
        "tax_id_available_flag": "Y" if selected and selected["tax_id_present"] else "N",
        "trust_indicator": "Y" if selected and selected["trust_indicator"] else "N",
        "business_indicator": "Y" if selected and selected["entity_type"] == "BUSINESS" else "N",
    }


# ---------------------------------------------------------------------------
# Financials / lifecycle / confidence
# ---------------------------------------------------------------------------

def sum_component(sub, mask):
    if len(sub) == 0:
        return 0.0
    return round(float(sub.loc[mask, "trans_amount"].sum()), 2)


def build_financials(claim_id, sub):
    gross = sum_component(sub, sub["financial_component"] == "BENEFIT")
    interest = sum_component(
        sub,
        (sub["interest_indicator"] == "Y") | (sub["financial_component"] == "INTEREST"),
    )
    loan_prin = abs(sum_component(sub, sub["transaction_code"] == "0411"))
    loan_int = abs(sum_component(sub, sub["transaction_code"] == "0412"))
    surrender = abs(sum_component(sub, sub["transaction_code"] == "1020"))
    withholding = abs(sum_component(sub, sub["tax_indicator"] == "Y"))
    total_cash = sum_component(sub, sub["transaction_code"] == "0560")
    partial = sum_component(sub, sub["transaction_code"] == "0561")
    payments = sum_component(sub, sub["payment_indicator"] == "Y")

    net = round(
        gross + interest + total_cash + partial - loan_prin - loan_int - withholding - surrender,
        2,
    )
    raw_total = round(float(sub["trans_amount"].sum()), 2)
    diff = round(net - payments, 2)
    abs_diff = abs(diff)
    if abs_diff <= BALANCE_TOLERANCE:
        status = "BALANCED"
        fin_conf = "HIGH"
    elif abs_diff <= MINOR_VARIANCE:
        status = "MINOR_VARIANCE"
        fin_conf = "MEDIUM"
    else:
        status = "UNBALANCED"
        fin_conf = "LOW"

    return {
        "reconstructed_claim_id": claim_id,
        "gross_benefit_amount": gross,
        "interest_amount": interest,
        "loan_principal_offset": loan_prin,
        "loan_interest_offset": loan_int,
        "surrender_charge_amount": surrender,
        "withholding_amount": withholding,
        "total_cash_amount": total_cash,
        "partial_surrender_amount": partial,
        "reconstructed_net_payment": net,
        "raw_transaction_total": raw_total,
        "balancing_difference": diff,
        "balancing_status": status,
        "confidence_level": fin_conf,
    }


def infer_lifecycle_status(sub, reversal_flag):
    if reversal_flag == "Y":
        return "REVERSED"
    has_payment = (sub["payment_indicator"] == "Y").any()
    has_funded = (sub["financial_component"].isin({"BENEFIT", "SURRENDER", "CLEARING"})).any()
    if has_payment and has_funded:
        return "SETTLED"
    if has_payment:
        return "PAID"
    if has_funded:
        return "FUNDED"
    return "INFERRED"


def build_lifecycle_events(claim_id, sub):
    events = []
    order = 0
    for _, row in sub.sort_values(["effective_date", "source_row_number"]).iterrows():
        order += 1
        if row["reversal_flag"] == "Y":
            event_type = "CLAIM_REVERSAL"
        else:
            event_type = LIFECYCLE_EVENT_BY_ROLE.get(row["lifecycle_role"], "CLAIM_ESTABLISHED")
        events.append({
            "reconstructed_claim_id": claim_id,
            "lifecycle_event_order": order,
            "lifecycle_event_type": event_type,
            "source_transaction_code": row["transaction_code"],
            "effective_date": row["effective_date"],
            "trans_amount": row["trans_amount_raw"],
            "lifecycle_role": row["lifecycle_role"],
            "reversal_related_flag": row["reversal_flag"],
            "lifecycle_notes": row["claim_subtype"],
        })

    if events and events[-1]["lifecycle_event_type"] == "CLAIM_PAYMENT":
        order += 1
        last = events[-1]
        events.append({
            "reconstructed_claim_id": claim_id,
            "lifecycle_event_order": order,
            "lifecycle_event_type": "CLAIM_SETTLEMENT",
            "source_transaction_code": last["source_transaction_code"],
            "effective_date": last["effective_date"],
            "trans_amount": last["trans_amount"],
            "lifecycle_role": "SETTLEMENT",
            "reversal_related_flag": "N",
            "lifecycle_notes": "Inferred settlement after payment event",
        })
    return events


def score_header_confidence(financials, payee, reversal_flag, lifecycle_status):
    if payee["payee_resolution_method"] == "UNRESOLVED":
        return "LOW"
    if financials["balancing_status"] == "UNBALANCED":
        return "LOW"
    if reversal_flag == "Y":
        return "MEDIUM"
    if (
        financials["balancing_status"] == "BALANCED"
        and payee["payee_resolution_method"] in {"PACTG_PAYEE_RELA_CODE", "PRELSA_PRIORITY"}
        and lifecycle_status in {"SETTLED", "PAID"}
    ):
        return "HIGH"
    return "MEDIUM"


def collect_exceptions(claim_id, policy, sub, financials, payee, header_conf):
    exceptions = []
    codes = sorted(set(sub["transaction_code"].tolist()))

    if payee["payee_resolution_method"] in {"UNRESOLVED", "PACTG_RELA_UNMATCHED"}:
        exceptions.append({
            "reconstructed_claim_id": claim_id,
            "exception_type": "unresolved_payee",
            "severity": "HIGH",
            "policy_number": policy,
            "issue_description": "Unable to resolve payee from PACTG relationship code or PRELSA priority order",
            "impacted_transaction_codes": "|".join(codes),
            "recommended_manual_review": "Validate PRELSA payee/beneficiary roles and PACTG PAYEE_RELA_CODE",
        })

    if financials["balancing_status"] == "UNBALANCED":
        exceptions.append({
            "reconstructed_claim_id": claim_id,
            "exception_type": "unbalanced_financials",
            "severity": "HIGH",
            "policy_number": policy,
            "issue_description": f"Balancing difference {financials['balancing_difference']} exceeds tolerance",
            "impacted_transaction_codes": "|".join(codes),
            "recommended_manual_review": "Review component rollup vs payment transactions",
        })
    elif financials["balancing_status"] == "MINOR_VARIANCE":
        exceptions.append({
            "reconstructed_claim_id": claim_id,
            "exception_type": "unbalanced_financials",
            "severity": "MEDIUM",
            "policy_number": policy,
            "issue_description": f"Minor balancing variance {financials['balancing_difference']}",
            "impacted_transaction_codes": "|".join(codes),
            "recommended_manual_review": "Optional review of rounding/clearing rows",
        })

    if (sub["reversal_flag"] == "Y").any() and (sub["payment_indicator"] == "Y").any():
        exceptions.append({
            "reconstructed_claim_id": claim_id,
            "exception_type": "reversal_conflict",
            "severity": "MEDIUM",
            "policy_number": policy,
            "issue_description": "Claim contains both payment and reversal activity",
            "impacted_transaction_codes": "|".join(codes),
            "recommended_manual_review": "Isolate reversal rows before settlement",
        })

    payout_rows = sub[sub["payment_indicator"] == "Y"]
    if not payout_rows.empty and (payout_rows["distribution_code"] == "").all():
        exceptions.append({
            "reconstructed_claim_id": claim_id,
            "exception_type": "missing_distribution_code",
            "severity": "MEDIUM",
            "policy_number": policy,
            "issue_description": "Payment rows missing DISTRIBUTION_CODE",
            "impacted_transaction_codes": "|".join(codes),
            "recommended_manual_review": "Confirm distribution mapping for QUIKCLMP prototype",
        })

    if header_conf == "LOW":
        exceptions.append({
            "reconstructed_claim_id": claim_id,
            "exception_type": "low_confidence_reconstruction",
            "severity": "MEDIUM",
            "policy_number": policy,
            "issue_description": "Overall reconstruction confidence rated LOW",
            "impacted_transaction_codes": "|".join(codes),
            "recommended_manual_review": "Full manual reconstruction review recommended",
        })

    if "effective_date_parsed" in sub.columns:
        invalid_dates = sub[(sub["effective_date"] != "") & sub["effective_date_parsed"].isna()]
        if not invalid_dates.empty:
            exceptions.append({
                "reconstructed_claim_id": claim_id,
                "exception_type": "invalid_dates",
                "severity": "HIGH",
                "policy_number": policy,
                "issue_description": "One or more claim rows have invalid effective dates",
                "impacted_transaction_codes": "|".join(codes),
                "recommended_manual_review": "Correct or exclude invalid date rows",
            })

    return exceptions


# ---------------------------------------------------------------------------
# Main reconstruction
# ---------------------------------------------------------------------------

def reconstruct_claims(pactg_path, catalog_path, prelsa_path, rel_rules_path):
    helpers = import_helpers()
    catalog = load_catalog(catalog_path)
    rel_rules = load_relationship_rules(rel_rules_path)
    pactg_df, _ = helpers["load_pactg"](pactg_path)
    prelsa_df, _ = helpers["load_prelsa"](prelsa_path)
    prelsa_index = build_prelsa_index(prelsa_df, helpers)

    claim_rows = annotate_claim_rows(pactg_df, catalog, helpers)
    if claim_rows.empty:
        raise ValueError("No claim-relevant PACTG rows matched the semantic catalog")

    claim_rows = assign_claim_clusters(claim_rows)

    headers = []
    financials = []
    payees = []
    lifecycle = []
    exceptions = []

    for claim_id, sub in claim_rows.groupby("reconstructed_claim_id", sort=True):
        policy = sub.iloc[0]["policy_number"]
        benefit_seq = sub.iloc[0]["benefit_seq"]
        group_family = sub.iloc[0]["group_family"]
        claim_families = sorted(set(sub["claim_family"].tolist()))
        tx_codes = sorted(set(sub["transaction_code"].tolist()))
        dates = [d for d in sub["effective_date"].tolist() if d]
        first_date = min(dates) if dates else ""
        latest_date = max(dates) if dates else ""
        reversal_flag = "Y" if (sub["reversal_flag"] == "Y").any() else "N"

        fin = build_financials(claim_id, sub)
        payee = resolve_payee(policy, group_family, sub, prelsa_index, rel_rules, helpers)
        lifecycle_status = infer_lifecycle_status(sub, reversal_flag)
        header_conf = score_header_confidence(fin, payee, reversal_flag, lifecycle_status)

        # Multiple beneficiaries check
        rels = prelsa_index.get(policy, [])
        bens = [e for e in rels if e["relate_code"] in {"B1", "B2"}]
        if len(bens) > 2:
            exceptions.append({
                "reconstructed_claim_id": claim_id,
                "exception_type": "multiple_possible_beneficiaries",
                "severity": "MEDIUM",
                "policy_number": policy,
                "issue_description": f"{len(bens)} beneficiary relationships on policy",
                "impacted_transaction_codes": "|".join(tx_codes),
                "recommended_manual_review": "Confirm beneficiary allocation and payee selection",
            })

        overlap_roles = {}
        for e in rels:
            overlap_roles.setdefault(e["name_id"], set()).add(e["relate_code"])
        if any(len(v) > 2 for v in overlap_roles.values()):
            exceptions.append({
                "reconstructed_claim_id": claim_id,
                "exception_type": "ambiguous_relationship",
                "severity": "MEDIUM",
                "policy_number": policy,
                "issue_description": "Policy has NAME_IDs with multiple overlapping relationship roles",
                "impacted_transaction_codes": "|".join(tx_codes),
                "recommended_manual_review": "Review PRELSA overlap analysis before payee finalization",
            })

        headers.append({
            "reconstructed_claim_id": claim_id,
            "policy_number": policy,
            "benefit_seq": benefit_seq,
            "claim_family": group_family,
            "claim_subtype": "|".join(claim_families),
            "reconstructed_lifecycle_status": lifecycle_status,
            "first_activity_date": first_date,
            "latest_activity_date": latest_date,
            "claim_activity_row_count": len(sub),
            "claim_relevant_transaction_codes": "|".join(tx_codes),
            "possible_reversal_flag": reversal_flag,
            "confidence_level": header_conf,
            "reconstruction_notes": (
                f"Prototype grouping by policy/benefit_seq/{group_family} with "
                f"{DATE_CLUSTER_DAYS}-day date cluster window"
            ),
        })
        financials.append(fin)
        payees.append({
            "reconstructed_claim_id": claim_id,
            "policy_number": policy,
            **payee,
            "confidence_level": "HIGH" if payee["payee_resolution_method"] == "PACTG_PAYEE_RELA_CODE"
            else ("MEDIUM" if payee["likely_payee_name_id"] else "LOW"),
            "resolution_notes": scenario_for_group(group_family),
        })
        lifecycle.extend(build_lifecycle_events(claim_id, sub))
        exceptions.extend(collect_exceptions(claim_id, policy, sub, fin, payee, header_conf))

    header_df = pd.DataFrame(headers).sort_values("reconstructed_claim_id").reset_index(drop=True)
    financial_df = pd.DataFrame(financials).sort_values("reconstructed_claim_id").reset_index(drop=True)
    payee_df = pd.DataFrame(payees).sort_values("reconstructed_claim_id").reset_index(drop=True)
    lifecycle_df = pd.DataFrame(lifecycle).sort_values(
        ["reconstructed_claim_id", "lifecycle_event_order"],
    ).reset_index(drop=True)
    exception_df = pd.DataFrame(exceptions)
    if not exception_df.empty:
        exception_df = exception_df.sort_values(
            ["severity", "reconstructed_claim_id", "exception_type"],
            ascending=[True, True, True],
        ).reset_index(drop=True)

    summary_stats = {
        "total_claim_candidates": len(header_df),
        "claim_families_identified": "|".join(sorted(header_df["claim_family"].unique())),
        "policies_with_claims": int(header_df["policy_number"].nunique()),
        "balanced_count": int((financial_df["balancing_status"] == "BALANCED").sum()),
        "unbalanced_count": int((financial_df["balancing_status"] == "UNBALANCED").sum()),
        "reversal_candidates": int((header_df["possible_reversal_flag"] == "Y").sum()),
        "unresolved_payees": int((payee_df["payee_resolution_method"] == "UNRESOLVED").sum()),
        "trust_claims": int((payee_df["trust_indicator"] == "Y").sum()),
        "business_claims": int((payee_df["business_indicator"] == "Y").sum()),
        "lifecycle_statuses": "|".join(sorted(header_df["reconstructed_lifecycle_status"].unique())),
        "high_confidence": int((header_df["confidence_level"] == "HIGH").sum()),
        "medium_confidence": int((header_df["confidence_level"] == "MEDIUM").sum()),
        "low_confidence": int((header_df["confidence_level"] == "LOW").sum()),
    }
    return header_df, financial_df, payee_df, lifecycle_df, exception_df, summary_stats


def write_summary(path, summary_stats, output_files, inputs):
    lines = [
        "=== Claim Event Reconstruction Summary (Phase 4 Prototype) ===",
        f"PACTG input: {inputs['pactg']}",
        f"Catalog input: {inputs['catalog']}",
        f"PRELSA input: {inputs['prelsa']}",
        f"Relationship rules: {inputs['relationship_rules']}",
        "",
        f"Total reconstructed claim candidates: {summary_stats['total_claim_candidates']}",
        f"Claim families identified: {summary_stats['claim_families_identified']}",
        f"Policies with reconstructed claims: {summary_stats['policies_with_claims']}",
        f"Balanced candidates: {summary_stats['balanced_count']}",
        f"Unbalanced candidates: {summary_stats['unbalanced_count']}",
        f"Reversal candidates: {summary_stats['reversal_candidates']}",
        f"Unresolved payees: {summary_stats['unresolved_payees']}",
        f"Trust-related claim count: {summary_stats['trust_claims']}",
        f"Business payee claim count: {summary_stats['business_claims']}",
        f"Lifecycle statuses identified: {summary_stats['lifecycle_statuses']}",
        f"High confidence claim count: {summary_stats['high_confidence']}",
        f"Medium confidence claim count: {summary_stats['medium_confidence']}",
        f"Low confidence claim count: {summary_stats['low_confidence']}",
        "",
        "Output files generated:",
    ]
    for f in output_files:
        lines.append(f"  - {f}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def run_reconstructor(pactg_path, catalog_path, prelsa_path, rel_rules_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    results = reconstruct_claims(pactg_path, catalog_path, prelsa_path, rel_rules_path)
    header_df, financial_df, payee_df, lifecycle_df, exception_df, summary_stats = results

    outputs = {
        "claim_candidate_header.csv": header_df,
        "claim_candidate_financials.csv": financial_df,
        "claim_candidate_payees.csv": payee_df,
        "claim_candidate_lifecycle.csv": lifecycle_df,
        "claim_reconstruction_exceptions.csv": exception_df,
    }

    output_files = []
    for name, frame in outputs.items():
        out_path = os.path.join(output_dir, name)
        frame.to_csv(out_path, index=False, encoding="utf-8")
        output_files.append(out_path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    summary_path = os.path.join(output_dir, "claim_reconstruction_summary.txt")
    write_summary(
        summary_path,
        summary_stats,
        output_files + [summary_path],
        {
            "pactg": os.path.abspath(pactg_path),
            "catalog": os.path.abspath(catalog_path),
            "prelsa": os.path.abspath(prelsa_path),
            "relationship_rules": os.path.abspath(rel_rules_path),
        },
    )
    output_files.append(summary_path)
    logger.info("Wrote claim_reconstruction_summary.txt")
    return summary_stats, output_files


def main():
    parser = argparse.ArgumentParser(
        description="Phase 4 claim event reconstruction prototype (read-only).",
    )
    parser.add_argument("--pactg", required=True, help="PACTG accounting extract CSV")
    parser.add_argument("--catalog", default=DEFAULT_CATALOG, help="Claims transaction code catalog CSV")
    parser.add_argument("--prelsa", required=True, help="RelationshipNameAddress extract CSV")
    parser.add_argument(
        "--relationship-rules",
        default=DEFAULT_REL_RULES,
        help="relationship_resolution_recommendations.csv",
    )
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    for label, path in (
        ("PACTG", args.pactg),
        ("Catalog", args.catalog),
        ("PRELSA", args.prelsa),
        ("Relationship rules", args.relationship_rules),
    ):
        if not os.path.isfile(path):
            logger.error("%s file not found: %s", label, path)
            return 1

    try:
        stats, outputs = run_reconstructor(
            args.pactg, args.catalog, args.prelsa, args.relationship_rules, args.output,
        )
        print(f"Reconstruction complete. Claim candidates: {stats['total_claim_candidates']}")
        print(f"Policies: {stats['policies_with_claims']}")
        print(f"High/Medium/Low confidence: {stats['high_confidence']}/"
              f"{stats['medium_confidence']}/{stats['low_confidence']}")
        print(f"Output directory: {os.path.abspath(args.output)}")
        for p in outputs:
            print(f"  {p}")
        return 0
    except (ValueError, FileNotFoundError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
