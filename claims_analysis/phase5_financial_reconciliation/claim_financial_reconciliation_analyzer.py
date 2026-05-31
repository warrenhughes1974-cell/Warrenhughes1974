#!/usr/bin/env python3
"""
Phase 5 — Claim financial reconciliation analyzer (read-only).

Analyzes Phase 4 reconstruction balancing gaps, settlement chains, reversals,
and grouping quality. Does NOT modify app.py or generate QUIKCLMS/QUIKCLMP output.
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
DEFAULT_PHASE4_DIR = os.path.join(ROOT, "phase4_claim_event_reconstruction")

BALANCE_TOLERANCE = 0.01
MINOR_VARIANCE = 100.0
MAJOR_VARIANCE = 10000.0
GROUPING_WINDOW_PAD_DAYS = 7

EXPECTED_CODES = {
    "DEATH_CLAIM": {"0038", "0094", "0530", "0630", "0411", "0412", "0810", "0820"},
    "SURRENDER_CLAIM": {"0560", "0561", "1020", "0411", "0412", "0090"},
    "DISBURSEMENT_CLAIM": {"0090", "0567", "1900"},
    "TAX_CLAIM": {"0810", "0820"},
}

logger = logging.getLogger("claim_financial_reconciliation")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_header(name):
    return str(name).strip().upper()


def load_csv(path):
    df = pd.read_csv(path, dtype=str)
    df.columns = [normalize_header(c).lower() for c in df.columns]
    return df


def to_float(value, default=0.0):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return default


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


def format_tx_code(code):
    digits = re.sub(r"[^0-9]", "", str(code))
    if not digits:
        return ""
    return str(int(digits)).zfill(4)


def gap_category(abs_diff):
    if abs_diff <= BALANCE_TOLERANCE:
        return "BALANCED"
    if abs_diff <= MINOR_VARIANCE:
        return "MINOR_VARIANCE"
    if abs_diff <= MAJOR_VARIANCE:
        return "MAJOR_VARIANCE"
    return "EXTREME_VARIANCE"


def gap_percent(net, diff):
    base = abs(net) if abs(net) > BALANCE_TOLERANCE else abs(to_float(net, 1.0)) or 1.0
    return round(100.0 * abs(diff) / base, 4)


def import_pactg_helpers():
    for path in (ROOT, PHASE1_PROFILER_DIR):
        if path not in sys.path:
            sys.path.insert(0, path)
    from pactg_transaction_profiler import load_pactg, norm_code  # noqa: WPS433
    return load_pactg, norm_code


def load_catalog(path):
    df = load_csv(path)
    catalog = {}
    claim_codes = set()
    for _, row in df.iterrows():
        if str(row.get("claim_relevant_flag", "")).strip().upper() != "Y":
            continue
        key = format_tx_code(row.get("transaction_code", ""))
        if not key:
            continue
        catalog[key] = {
            "claim_family": str(row.get("claim_family", "")).strip(),
            "financial_component": str(row.get("financial_component", "")).strip(),
            "lifecycle_role": str(row.get("lifecycle_role", "")).strip(),
            "payment_indicator": str(row.get("payment_indicator", "")).strip().upper(),
        }
        claim_codes.add(key)
    return catalog, claim_codes


def annotate_pactg_claim_rows(pactg_df, catalog, claim_codes, norm_code_fn):
    rows = []
    for _, row in pactg_df.iterrows():
        cc = norm_code_fn(row.get("CREDIT_CODE", ""))
        dc = norm_code_fn(row.get("DEBIT_CODE", ""))
        matched = []
        for code in (cc, dc):
            key = format_tx_code(code)
            if key in claim_codes:
                matched.append(key)
        if not matched:
            continue
        amt = row.get("amount_parsed")
        eff = row.get("effective_date_parsed")
        rows.append({
            "policy_number": row["policy_norm"],
            "source_row_number": row.get("source_row_number", ""),
            "effective_date": eff.strftime("%Y%m%d") if pd.notna(eff) else "",
            "effective_date_parsed": eff,
            "trans_amount": amt if amt is not None else 0.0,
            "credit_code": format_tx_code(cc),
            "debit_code": format_tx_code(dc),
            "transaction_codes": "|".join(sorted(set(matched))),
            "primary_code": matched[0],
            "claim_family_meta": catalog.get(matched[0], {}).get("claim_family", ""),
            "financial_component": catalog.get(matched[0], {}).get("financial_component", ""),
            "payment_indicator": catalog.get(matched[0], {}).get("payment_indicator", ""),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Analysis builders
# ---------------------------------------------------------------------------

def infer_missing_components(header_row, fin_row, lifecycle_sub):
    missing = []
    family = header_row.get("claim_family", "")
    codes = set(str(header_row.get("claim_relevant_transaction_codes", "")).split("|"))
    expected = EXPECTED_CODES.get(family, set())
    for code in sorted(expected):
        if code not in codes:
            missing.append(code)

    if "0038" in codes and family == "DEATH_CLAIM":
        missing.append("CLEARING_HUB_DOUBLE_COUNT")
    if family == "DISBURSEMENT_CLAIM" and fin_row["gross_benefit_amount"] == 0:
        missing.append("PAYOUT_ONLY_ROLLUP")
    if header_row.get("reconstructed_lifecycle_status") == "SETTLED":
        events = set(lifecycle_sub["lifecycle_event_type"].tolist()) if not lifecycle_sub.empty else set()
        if "CLAIM_PAYMENT" not in events:
            missing.append("MISSING_PAYMENT_EVENT")
        if "CLAIM_FUNDED" not in events and family == "DEATH_CLAIM":
            missing.append("MISSING_FUNDING_EVENT")
    if fin_row["withholding_amount"] == 0 and family in {"DEATH_CLAIM", "SURRENDER_CLAIM"}:
        if "0810" not in codes and "0820" not in codes:
            missing.append("WITHHOLDING_NOT_OBSERVED")
    return "|".join(missing) if missing else ""


def infer_gap_notes(category, missing, grouping_issue, reversal_issue, family):
    notes = []
    if category == "BALANCED":
        notes.append("Components reconcile within tolerance")
    if "CLEARING_HUB_DOUBLE_COUNT" in missing:
        notes.append("0038 clearing hub amounts likely inflate raw_transaction_total")
    if "PAYOUT_ONLY_ROLLUP" in missing:
        notes.append("Disbursement-only chain lacks benefit component in net formula")
    if grouping_issue == "Y":
        notes.append("Review claim grouping window or benefit_seq partition")
    if reversal_issue == "Y":
        notes.append("Potential reversal/correction activity near claim window")
    if family == "DEATH_CLAIM" and category in {"MAJOR_VARIANCE", "EXTREME_VARIANCE"}:
        notes.append("Death claim settlement chain may require clearing-to-payout pairing")
    return "; ".join(notes) if notes else "No specific pattern identified"


def norm_code_from_row(df):
    from pactg_transaction_profiler import norm_code  # noqa: WPS433
    codes = []
    for _, r in df.iterrows():
        for col in ("credit_code_norm", "debit_code_norm"):
            if col in r.index and r[col]:
                codes.append(format_tx_code(r[col]))
        if "CREDIT_CODE" in r.index:
            codes.append(format_tx_code(norm_code(r.get("CREDIT_CODE", ""))))
        if "DEBIT_CODE" in r.index:
            codes.append(format_tx_code(norm_code(r.get("DEBIT_CODE", ""))))
    return [c for c in codes if c]


def build_balancing_gap_analysis(headers, financials, lifecycle, pactg_claim_rows):
    merged = headers.merge(financials, on="reconstructed_claim_id", how="inner")
    rows = []
    for _, row in merged.iterrows():
        claim_id = row["reconstructed_claim_id"]
        net = to_float(row["reconstructed_net_payment"])
        raw = to_float(row["raw_transaction_total"])
        diff = to_float(row["balancing_difference"])
        abs_diff = abs(diff)
        category = gap_category(abs_diff)
        life_sub = lifecycle[lifecycle["reconstructed_claim_id"] == claim_id]
        fin_dict = {
            "gross_benefit_amount": to_float(row["gross_benefit_amount"]),
            "withholding_amount": to_float(row["withholding_amount"]),
        }
        missing = infer_missing_components(row, fin_dict, life_sub)

        grouping_issue = "N"
        reversal_issue = "N"
        if row.get("claim_activity_row_count", "0") != str(len(life_sub)):
            grouping_issue = "Y"
        policy = str(row["policy_number"]).strip()
        first_d = parse_date(row.get("first_activity_date"))
        last_d = parse_date(row.get("latest_activity_date"))
        if first_d and last_d and pactg_claim_rows is not None and not pactg_claim_rows.empty:
            pad = pd.Timedelta(days=GROUPING_WINDOW_PAD_DAYS)
            window = pactg_claim_rows[
                (pactg_claim_rows["policy_number"] == policy)
                & pactg_claim_rows["effective_date_parsed"].notna()
                & (pactg_claim_rows["effective_date_parsed"] >= first_d - pad)
                & (pactg_claim_rows["effective_date_parsed"] <= last_d + pad)
            ]
            grouped_n = int(to_float(row.get("claim_activity_row_count", 0)))
            if len(window) > grouped_n:
                grouping_issue = "Y"
            if (window["trans_amount"] < 0).any():
                reversal_issue = "Y"

        conf = "HIGH" if category == "BALANCED" else ("MEDIUM" if category == "MINOR_VARIANCE" else "LOW")
        rows.append({
            "reconstructed_claim_id": claim_id,
            "policy_number": policy,
            "claim_family": row.get("claim_family", ""),
            "reconstructed_net_payment": round(net, 2),
            "raw_transaction_total": round(raw, 2),
            "balancing_difference": round(diff, 2),
            "balancing_gap_percent": gap_percent(net, diff),
            "balancing_gap_category": category,
            "likely_missing_components": missing,
            "likely_grouping_issue": grouping_issue,
            "likely_reversal_issue": reversal_issue,
            "confidence_level": conf,
            "reconciliation_notes": infer_gap_notes(
                category, missing, grouping_issue, reversal_issue, row.get("claim_family", ""),
            ),
        })
    out = pd.DataFrame(rows)
    return out.sort_values(
        ["balancing_gap_category", "reconstructed_claim_id"],
        ascending=[True, True],
    ).reset_index(drop=True)


def build_component_breakdown(financials, gap_df, headers):
    merged = financials.merge(
        gap_df[["reconstructed_claim_id", "likely_missing_components"]],
        on="reconstructed_claim_id",
        how="left",
    ).merge(
        headers[["reconstructed_claim_id", "claim_relevant_transaction_codes"]],
        on="reconstructed_claim_id",
        how="left",
    )
    rows = []
    for _, row in merged.iterrows():
        gross = to_float(row["gross_benefit_amount"])
        interest = to_float(row["interest_amount"])
        loan = to_float(row["loan_principal_offset"]) + to_float(row["loan_interest_offset"])
        withholding = to_float(row["withholding_amount"])
        surrender = to_float(row["surrender_charge_amount"])
        cash = to_float(row["total_cash_amount"])
        partial = to_float(row["partial_surrender_amount"])
        net = to_float(row["reconstructed_net_payment"])
        raw = to_float(row["raw_transaction_total"])
        diff = to_float(row["balancing_difference"])
        identified = gross + interest + cash + partial
        unidentified = round(raw - identified, 2)
        payments = round(net - diff, 2)

        suspected = ""
        codes = str(row.get("claim_relevant_transaction_codes", ""))
        if "0038" in codes:
            suspected = "0038 clearing rows may be unlinked from payout pairing"

        rows.append({
            "reconstructed_claim_id": row["reconstructed_claim_id"],
            "gross_benefit_amount": round(gross, 2),
            "interest_amount": round(interest, 2),
            "loan_offsets": round(loan, 2),
            "withholding_amount": round(withholding, 2),
            "surrender_charges": round(surrender, 2),
            "payout_amount": payments,
            "unidentified_amount": unidentified,
            "missing_component_candidates": str(row.get("likely_missing_components", "")),
            "suspected_unlinked_transactions": suspected,
            "balancing_status": row.get("balancing_status", ""),
        })
    return pd.DataFrame(rows).sort_values("reconstructed_claim_id").reset_index(drop=True)


def build_settlement_chain_analysis(headers, lifecycle):
    rows = []
    for claim_id, sub in lifecycle.groupby("reconstructed_claim_id", sort=True):
        header = headers[headers["reconstructed_claim_id"] == claim_id]
        if header.empty:
            continue
        h = header.iloc[0]
        dates = [parse_date(d) for d in sub["effective_date"].tolist() if parse_date(d)]
        first_d = min(dates) if dates else None
        last_d = max(dates) if dates else None
        duration = (last_d - first_d).days if first_d and last_d else 0
        events = set(sub["lifecycle_event_type"].tolist())
        payout = "Y" if "CLAIM_PAYMENT" in events else "N"
        offset = "Y" if "CLAIM_OFFSET" in events else "N"
        withholding = "Y" if "CLAIM_WITHHOLDING" in events else "N"
        interest = "Y" if "CLAIM_INTEREST" in events else "N"

        if payout == "Y" and ("CLAIM_FUNDED" in events or h["claim_family"] == "DISBURSEMENT_CLAIM"):
            status = "COMPLETE"
            conf = "HIGH"
        elif payout == "N" and h["reconstructed_lifecycle_status"] in {"FUNDED", "INFERRED"}:
            status = "INCOMPLETE"
            conf = "MEDIUM"
        elif payout == "Y":
            status = "PARTIAL"
            conf = "MEDIUM"
        else:
            status = "INDETERMINATE"
            conf = "LOW"

        rows.append({
            "reconstructed_claim_id": claim_id,
            "settlement_chain_id": f"{claim_id}-SC1",
            "lifecycle_event_count": len(sub),
            "first_activity_date": h.get("first_activity_date", ""),
            "last_activity_date": h.get("latest_activity_date", ""),
            "settlement_duration_days": duration,
            "payout_detected_flag": payout,
            "offset_detected_flag": offset,
            "withholding_detected_flag": withholding,
            "interest_detected_flag": interest,
            "settlement_completion_status": status,
            "chain_confidence_level": conf,
        })
    return pd.DataFrame(rows).sort_values("reconstructed_claim_id").reset_index(drop=True)


def build_reversal_detection(headers, pactg_claim_rows, gap_df, pactg_df=None):
    rows = []
    for _, header in headers.iterrows():
        claim_id = header["reconstructed_claim_id"]
        policy = str(header["policy_number"]).strip()
        first_d = parse_date(header.get("first_activity_date"))
        last_d = parse_date(header.get("latest_activity_date"))
        gap_row = gap_df[gap_df["reconstructed_claim_id"] == claim_id]
        reversal_issue = "N"
        if not gap_row.empty:
            reversal_issue = gap_row.iloc[0].get("likely_reversal_issue", "N")

        suspected = "N"
        pattern = ""
        offset_n = 0
        same_day = "N"
        opposite = "N"
        codes = ""
        notes = ""
        conf = "LOW"

        if pactg_df is not None and not pactg_df.empty and first_d and last_d:
            pad = pd.Timedelta(days=GROUPING_WINDOW_PAD_DAYS)
            all_window = pactg_df[
                (pactg_df["policy_norm"] == policy)
                & pactg_df["amount_parsed"].notna()
                & pactg_df["effective_date_parsed"].notna()
                & (pactg_df["effective_date_parsed"] >= first_d - pad)
                & (pactg_df["effective_date_parsed"] <= last_d + pad)
            ]
            neg_all = all_window[all_window["amount_parsed"] < 0]
            if not neg_all.empty:
                suspected = "Y"
                pattern = pattern or "CORRECTION_CHAIN"
                code_list = norm_code_from_row(neg_all)
                if code_list:
                    codes = "|".join(sorted(set(code_list)))
                conf = "MEDIUM"
                notes = (notes + f"; {len(neg_all)} negative PACTG rows in window").strip("; ")

        if pactg_claim_rows is not None and not pactg_claim_rows.empty and first_d and last_d:
            pad = pd.Timedelta(days=GROUPING_WINDOW_PAD_DAYS)
            window = pactg_claim_rows[
                (pactg_claim_rows["policy_number"] == policy)
                & pactg_claim_rows["effective_date_parsed"].notna()
                & (pactg_claim_rows["effective_date_parsed"] >= first_d - pad)
                & (pactg_claim_rows["effective_date_parsed"] <= last_d + pad)
            ]
            neg = window[window["trans_amount"] < 0]
            if not neg.empty:
                suspected = "Y"
                pattern = "SAME_DAY_NEGATION" if len(neg) == 1 else "CORRECTION_CHAIN"
                codes = "|".join(sorted(set(neg["primary_code"].tolist())))
                conf = "MEDIUM"
                notes = f"{len(neg)} negative amount rows in claim window"

            # same-day opposite signs
            for eff, grp in window.groupby("effective_date"):
                if len(grp) < 2:
                    continue
                if (grp["trans_amount"] > 0).any() and (grp["trans_amount"] < 0).any():
                    same_day = "Y"
                    opposite = "Y"
                    suspected = "Y"
                    if not pattern:
                        pattern = "SAME_DAY_NEGATION"
                    conf = "MEDIUM"
                    notes = (notes + "; same-day opposite sign amounts").strip("; ")

            # offsetting pairs by code
            for code, grp in window.groupby("primary_code"):
                if len(grp) < 2:
                    continue
                total = grp["trans_amount"].sum()
                if abs(total) < 0.01 and (grp["trans_amount"] > 0).any() and (grp["trans_amount"] < 0).any():
                    offset_n += len(grp)
                    suspected = "Y"
                    pattern = pattern or "OFFSETTING_PAIR"
                    conf = "HIGH"
                    notes = (notes + f"; offsetting pair for code {code}").strip("; ")

        if header.get("possible_reversal_flag") == "Y":
            suspected = "Y"
            pattern = pattern or "CORRECTION_CHAIN"

        if reversal_issue == "Y" and suspected == "N":
            suspected = "Y"
            pattern = "UNLINKED_REVERSAL"
            notes = "Reversal signal in PACTG window without Phase 4 reversal flag"

        rows.append({
            "reconstructed_claim_id": claim_id,
            "policy_number": policy,
            "suspected_reversal_flag": suspected,
            "reversal_pattern_type": pattern,
            "offsetting_transaction_count": offset_n,
            "same_day_offset_flag": same_day,
            "opposite_sign_amounts_flag": opposite,
            "reversal_candidate_codes": codes,
            "reversal_confidence": conf,
            "reversal_notes": notes,
        })
    return pd.DataFrame(rows).sort_values(
        ["suspected_reversal_flag", "reconstructed_claim_id"],
        ascending=[False, True],
    ).reset_index(drop=True)


def build_grouping_quality(headers, pactg_claim_rows, lifecycle):
    rows = []
    policy_family_counts = headers.groupby(["policy_number", "claim_family"]).size()

    for _, header in headers.iterrows():
        claim_id = header["reconstructed_claim_id"]
        policy = str(header["policy_number"]).strip()
        benefit_seq = str(header.get("benefit_seq", "")).strip()
        first_d = parse_date(header.get("first_activity_date"))
        last_d = parse_date(header.get("latest_activity_date"))
        grouped_n = int(to_float(header.get("claim_activity_row_count", 0)))
        window_days = (last_d - first_d).days if first_d and last_d else 0

        multi_chain = "Y" if policy_family_counts.get((policy, header.get("claim_family")), 0) > 1 else "N"
        overgroup = "N"
        undergroup = "N"
        suspected_missing = 0
        conf = "HIGH"

        if window_days > 60:
            overgroup = "Y"
            conf = "MEDIUM"
        if grouped_n == 1 and header.get("reconstructed_lifecycle_status") == "SETTLED":
            undergroup = "Y"
            conf = "LOW"

        if pactg_claim_rows is not None and not pactg_claim_rows.empty and first_d and last_d:
            pad = pd.Timedelta(days=GROUPING_WINDOW_PAD_DAYS)
            window = pactg_claim_rows[
                (pactg_claim_rows["policy_number"] == policy)
                & pactg_claim_rows["effective_date_parsed"].notna()
                & (pactg_claim_rows["effective_date_parsed"] >= first_d - pad)
                & (pactg_claim_rows["effective_date_parsed"] <= last_d + pad)
            ]
            if len(window) > grouped_n:
                undergroup = "Y"
                suspected_missing = len(window) - grouped_n
                conf = "LOW"
            if len(window) < grouped_n:
                overgroup = "Y"

        life_n = len(lifecycle[lifecycle["reconstructed_claim_id"] == claim_id])
        if life_n > grouped_n + 2:
            overgroup = "Y"

        rows.append({
            "reconstructed_claim_id": claim_id,
            "policy_number": policy,
            "benefit_seq": benefit_seq,
            "grouped_transaction_count": grouped_n,
            "grouping_window_days": window_days,
            "multiple_claim_chain_flag": multi_chain,
            "possible_overgrouping_flag": overgroup,
            "possible_undergrouping_flag": undergroup,
            "suspected_missing_transactions": suspected_missing,
            "grouping_confidence": conf,
        })
    return pd.DataFrame(rows).sort_values("reconstructed_claim_id").reset_index(drop=True)


def build_family_behavior(gap_df, reversal_df, component_df):
    rows = []
    for family, sub in gap_df.groupby("claim_family", sort=True):
        rev_sub = reversal_df[reversal_df["reconstructed_claim_id"].isin(sub["reconstructed_claim_id"])]
        comp_sub = component_df[component_df["reconstructed_claim_id"].isin(sub["reconstructed_claim_id"])]
        balanced = int((sub["balancing_gap_category"] == "BALANCED").sum())
        unbalanced = len(sub) - balanced
        gaps = sub["balancing_difference"].abs()
        missing_parts = []
        for val in comp_sub["missing_component_candidates"].dropna():
            for part in str(val).split("|"):
                if part:
                    missing_parts.append(part)
        top_missing = ""
        if missing_parts:
            top_missing = pd.Series(missing_parts).value_counts().head(3).to_dict()
            top_missing = "; ".join(f"{k}({v})" for k, v in top_missing.items())
        rev_patterns = rev_sub[rev_sub["suspected_reversal_flag"] == "Y"]["reversal_pattern_type"]
        top_rev = ""
        if not rev_patterns.empty:
            top_rev = "; ".join(
                f"{k}({v})" for k, v in rev_patterns.value_counts().head(3).items()
            )
        unbal_rate = unbalanced / len(sub) if len(sub) else 0
        risk = "LOW" if unbal_rate < 0.3 else ("MEDIUM" if unbal_rate < 0.7 else "HIGH")
        rows.append({
            "claim_family": family,
            "claim_count": len(sub),
            "balanced_count": balanced,
            "unbalanced_count": unbalanced,
            "avg_balancing_gap": round(float(gaps.mean()), 2),
            "median_balancing_gap": round(float(gaps.median()), 2),
            "largest_balancing_gap": round(float(gaps.max()), 2),
            "most_common_missing_components": top_missing,
            "most_common_reversal_patterns": top_rev,
            "reconciliation_risk_level": risk,
        })
    return pd.DataFrame(rows).sort_values("claim_family").reset_index(drop=True)


def build_recommendations(gap_df, grouping_df, reversal_df, family_df):
    recs = []
    total = len(gap_df)
    clearing_issues = gap_df["likely_missing_components"].str.contains(
        "CLEARING_HUB_DOUBLE_COUNT", na=False,
    ).sum()
    if clearing_issues > 0:
        recs.append({
            "issue_type": "clearing_hub_inflation",
            "observed_pattern": f"{clearing_issues} claims include 0038 clearing in raw totals",
            "recommended_refinement": "Exclude clearing hub from net rollup or pair 0038 with payout/debit codes",
            "expected_impact": "HIGH",
            "implementation_priority": "P1",
            "confidence_level": "HIGH",
        })

    payout_only = gap_df["likely_missing_components"].str.contains("PAYOUT_ONLY_ROLLUP", na=False).sum()
    if payout_only > 0:
        recs.append({
            "issue_type": "disbursement_rollup",
            "observed_pattern": f"{payout_only} disbursement claims lack benefit component in net formula",
            "recommended_refinement": "Separate surrender/disbursement chains; use payment_amount as net for DISBURSEMENT_CLAIM",
            "expected_impact": "HIGH",
            "implementation_priority": "P1",
            "confidence_level": "HIGH",
        })

    undergroup = int((grouping_df["possible_undergrouping_flag"] == "Y").sum())
    if undergroup > 0:
        recs.append({
            "issue_type": "grouping_window",
            "observed_pattern": f"{undergroup} claims have more PACTG rows in window than grouped count",
            "recommended_refinement": "Expand settlement window or refine benefit_seq grouping",
            "expected_impact": "MEDIUM",
            "implementation_priority": "P2",
            "confidence_level": "MEDIUM",
        })

    reversals = int((reversal_df["suspected_reversal_flag"] == "Y").sum())
    if reversals > 0:
        recs.append({
            "issue_type": "reversal_detection",
            "observed_pattern": f"{reversals} claims with reversal signals in PACTG window",
            "recommended_refinement": "Refine reversal pairing and isolate correction chains before balancing",
            "expected_impact": "MEDIUM",
            "implementation_priority": "P2",
            "confidence_level": "MEDIUM",
        })

    for _, fam in family_df.iterrows():
        if fam["reconciliation_risk_level"] == "HIGH":
            recs.append({
                "issue_type": "claim_family_balancing",
                "observed_pattern": (
                    f"{fam['claim_family']} has {fam['unbalanced_count']}/{fam['claim_count']} unbalanced"
                ),
                "recommended_refinement": f"Family-specific balancing rules for {fam['claim_family']}",
                "expected_impact": "HIGH",
                "implementation_priority": "P1",
                "confidence_level": "MEDIUM",
            })

    loan_balanced = family_df[
        (family_df["claim_family"] == "SURRENDER_CLAIM") & (family_df["balanced_count"] > 0)
    ]
    if not loan_balanced.empty:
        recs.append({
            "issue_type": "loan_offset_chains",
            "observed_pattern": "Loan interest offset-only chains balance when isolated",
            "recommended_refinement": "Improve loan offset grouping separate from cash surrender events",
            "expected_impact": "MEDIUM",
            "implementation_priority": "P3",
            "confidence_level": "HIGH",
        })

    recs.append({
        "issue_type": "withholding_linkage",
        "observed_pattern": "0810/0820 codes largely unobserved in extract",
        "recommended_refinement": "Improve withholding linkage when tax codes appear in future extracts",
        "expected_impact": "LOW",
        "implementation_priority": "P3",
        "confidence_level": "MEDIUM",
    })

    recs.append({
        "issue_type": "delayed_payout",
        "observed_pattern": f"{int((grouping_df['grouping_window_days'] > 0).sum())} claims span multiple days",
        "recommended_refinement": "Add delayed payout detection across expanded date windows",
        "expected_impact": "MEDIUM",
        "implementation_priority": "P2",
        "confidence_level": "LOW",
    })

    out = pd.DataFrame(recs)
    if out.empty:
        return out
    priority_order = {"P1": 0, "P2": 1, "P3": 2}
    out["_sort"] = out["implementation_priority"].map(priority_order)
    return out.sort_values(["_sort", "issue_type"]).drop(columns=["_sort"]).reset_index(drop=True)


def write_summary(path, stats, output_files, inputs):
    lines = [
        "=== Claim Financial Reconciliation Summary (Phase 5) ===",
        f"Headers input: {inputs['headers']}",
        f"Financials input: {inputs['financials']}",
        f"Lifecycle input: {inputs['lifecycle']}",
        f"Exceptions input: {inputs['exceptions']}",
        f"PACTG input: {inputs['pactg']}",
        f"Catalog input: {inputs['catalog']}",
        "",
        f"Total claims analyzed: {stats['total_claims']}",
        f"Balanced claims: {stats['balanced']}",
        f"Unbalanced claims: {stats['unbalanced']}",
        f"Average balancing gap: {stats['avg_gap']}",
        f"Largest balancing gap: {stats['max_gap']}",
        f"Reversal candidates identified: {stats['reversal_candidates']}",
        f"Most common balancing issues: {stats['top_issues']}",
        f"Grouping quality observations: {stats['grouping_obs']}",
        f"Settlement chain observations: {stats['settlement_obs']}",
        f"Claim family balancing behavior: {stats['family_obs']}",
        "",
        "Recommended next-phase priorities:",
    ]
    for item in stats.get("priorities", []):
        lines.append(f"  - {item}")
    lines.append("")
    lines.append("Output files generated:")
    for f in output_files:
        lines.append(f"  - {f}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_analyzer(headers_path, financials_path, lifecycle_path, exceptions_path,
                 pactg_path, catalog_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    headers = load_csv(headers_path)
    financials = load_csv(financials_path)
    lifecycle = load_csv(lifecycle_path)
    _exceptions = load_csv(exceptions_path)  # loaded for lineage; patterns derived in analysis

    catalog, claim_codes = load_catalog(catalog_path)
    load_pactg, norm_code_fn = import_pactg_helpers()
    pactg_df, _ = load_pactg(pactg_path)
    pactg_claim_rows = annotate_pactg_claim_rows(pactg_df, catalog, claim_codes, norm_code_fn)
    logger.info("Annotated %s claim-relevant PACTG rows", len(pactg_claim_rows))

    logger.info("Building balancing_gap_analysis.csv")
    gap_df = build_balancing_gap_analysis(headers, financials, lifecycle, pactg_claim_rows)

    logger.info("Building balancing_component_breakdown.csv")
    component_df = build_component_breakdown(financials, gap_df, headers)

    logger.info("Building settlement_chain_analysis.csv")
    settlement_df = build_settlement_chain_analysis(headers, lifecycle)

    logger.info("Building reversal_detection_analysis.csv")
    reversal_df = build_reversal_detection(headers, pactg_claim_rows, gap_df, pactg_df)

    logger.info("Building claim_grouping_quality_analysis.csv")
    grouping_df = build_grouping_quality(headers, pactg_claim_rows, lifecycle)

    logger.info("Building balancing_behavior_by_claim_family.csv")
    family_df = build_family_behavior(gap_df, reversal_df, component_df)

    logger.info("Building financial_reconciliation_recommendations.csv")
    recommendations_df = build_recommendations(gap_df, grouping_df, reversal_df, family_df)

    reports = {
        "balancing_gap_analysis.csv": gap_df,
        "balancing_component_breakdown.csv": component_df,
        "settlement_chain_analysis.csv": settlement_df,
        "reversal_detection_analysis.csv": reversal_df,
        "claim_grouping_quality_analysis.csv": grouping_df,
        "balancing_behavior_by_claim_family.csv": family_df,
        "financial_reconciliation_recommendations.csv": recommendations_df,
    }

    output_files = []
    for name, frame in reports.items():
        out_path = os.path.join(output_dir, name)
        frame.to_csv(out_path, index=False, encoding="utf-8")
        output_files.append(out_path)
        logger.info("Wrote %s (%s rows)", name, len(frame))

    gaps = gap_df["balancing_difference"].abs()
    top_issues = gap_df["likely_missing_components"].str.split("|").explode()
    top_issues = top_issues[top_issues != ""].value_counts().head(5)
    top_issue_str = "; ".join(f"{k}({v})" for k, v in top_issues.items()) if not top_issues.empty else "none"

    stats = {
        "total_claims": len(gap_df),
        "balanced": int((gap_df["balancing_gap_category"] == "BALANCED").sum()),
        "unbalanced": int((gap_df["balancing_gap_category"] != "BALANCED").sum()),
        "avg_gap": round(float(gaps.mean()), 2),
        "max_gap": round(float(gaps.max()), 2),
        "reversal_candidates": int((reversal_df["suspected_reversal_flag"] == "Y").sum()),
        "top_issues": top_issue_str,
        "grouping_obs": (
            f"undergroup={int((grouping_df['possible_undergrouping_flag'] == 'Y').sum())}, "
            f"overgroup={int((grouping_df['possible_overgrouping_flag'] == 'Y').sum())}"
        ),
        "settlement_obs": (
            f"complete={int((settlement_df['settlement_completion_status'] == 'COMPLETE').sum())}, "
            f"incomplete={int((settlement_df['settlement_completion_status'] == 'INCOMPLETE').sum())}"
        ),
        "family_obs": "; ".join(
            f"{r['claim_family']}:{r['balanced_count']}/{r['claim_count']} balanced"
            for _, r in family_df.iterrows()
        ),
        "priorities": recommendations_df.head(5)["recommended_refinement"].tolist()
        if not recommendations_df.empty else [],
    }

    summary_path = os.path.join(output_dir, "claim_reconciliation_summary.txt")
    write_summary(
        summary_path,
        stats,
        output_files + [summary_path],
        {
            "headers": os.path.abspath(headers_path),
            "financials": os.path.abspath(financials_path),
            "lifecycle": os.path.abspath(lifecycle_path),
            "exceptions": os.path.abspath(exceptions_path),
            "pactg": os.path.abspath(pactg_path),
            "catalog": os.path.abspath(catalog_path),
        },
    )
    output_files.append(summary_path)
    logger.info("Wrote claim_reconciliation_summary.txt")
    return stats, output_files


def main():
    parser = argparse.ArgumentParser(
        description="Phase 5 claim financial reconciliation analyzer (read-only).",
    )
    parser.add_argument(
        "--headers",
        default=os.path.join(DEFAULT_PHASE4_DIR, "claim_candidate_header.csv"),
    )
    parser.add_argument(
        "--financials",
        default=os.path.join(DEFAULT_PHASE4_DIR, "claim_candidate_financials.csv"),
    )
    parser.add_argument(
        "--lifecycle",
        default=os.path.join(DEFAULT_PHASE4_DIR, "claim_candidate_lifecycle.csv"),
    )
    parser.add_argument(
        "--exceptions",
        default=os.path.join(DEFAULT_PHASE4_DIR, "claim_reconstruction_exceptions.csv"),
    )
    parser.add_argument("--pactg", required=True, help="Original PACTG extract CSV")
    parser.add_argument("--catalog", default=DEFAULT_CATALOG)
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
        ("Exceptions", args.exceptions),
        ("PACTG", args.pactg),
        ("Catalog", args.catalog),
    ):
        if not os.path.isfile(path):
            logger.error("%s file not found: %s", label, path)
            return 1

    try:
        stats, outputs = run_analyzer(
            args.headers, args.financials, args.lifecycle, args.exceptions,
            args.pactg, args.catalog, args.output,
        )
        print(f"Reconciliation analysis complete. Claims analyzed: {stats['total_claims']}")
        print(f"Balanced/Unbalanced: {stats['balanced']}/{stats['unbalanced']}")
        print(f"Reversal candidates: {stats['reversal_candidates']}")
        print(f"Output directory: {os.path.abspath(args.output)}")
        for p in outputs:
            print(f"  {p}")
        return 0
    except (ValueError, FileNotFoundError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
