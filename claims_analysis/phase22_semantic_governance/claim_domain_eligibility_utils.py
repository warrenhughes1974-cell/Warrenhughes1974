"""Shared claim-domain eligibility helpers (Phase 22C — read-only on Phase 4-10 artifacts)."""

import json
import os
import re

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_RULES = os.path.join(ROOT, "config", "claim_domain_eligibility_rules.json")
PHASE4 = os.path.join(ROOT, "phase4_claim_event_reconstruction")
PHASE10B = os.path.join(ROOT, "phase10b_quikclms_derivation_design")
PHASE17 = os.path.join(ROOT, "phase17_uat_governance_reporting")


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_csv(path):
    if not os.path.isfile(path):
        return pd.DataFrame()
    df = pd.read_csv(path, dtype=str).fillna("")
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def strip_val(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def norm_code(code):
    digits = re.sub(r"[^0-9]", "", str(code))
    if not digits:
        return ""
    return str(int(digits)).zfill(4)


def parse_codes(value):
    codes = set()
    for part in strip_val(value).split("|"):
        c = norm_code(part)
        if c:
            codes.add(c)
    return codes


def lifecycle_tx_codes(lifecycle_df, claim_id):
    if lifecycle_df.empty:
        return set()
    sub = lifecycle_df[lifecycle_df["reconstructed_claim_id"].astype(str) == claim_id]
    codes = set()
    for val in sub.get("source_transaction_code", pd.Series(dtype=str)):
        c = norm_code(val)
        if c:
            codes.add(c)
    return codes


def to_float(value, default=0.0):
    s = strip_val(value)
    if not s:
        return default
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return default


def eligible_code_set(rules):
    explicit = {norm_code(c) for c in rules.get("claim_domain_eligible_codes", [])}
    payout = {norm_code(c) for c in rules.get("claim_domain_payout_codes", [])}
    benefit = {norm_code(c) for c in rules.get("claim_domain_benefit_codes", [])}
    return explicit or (payout | benefit)


def non_claim_code_set(rules):
    return {norm_code(c) for c in rules.get("non_claim_accounting_codes", [])}


def borrowed_code_set(rules):
    return {norm_code(c) for c in rules.get("borrowed_money_codes", rules.get("non_claim_accounting_codes", []))}


def has_claim_domain_semantics(tx_codes, rules):
    return bool(tx_codes & eligible_code_set(rules))


def is_borrowed_money_only(tx_codes, rules):
    borrowed = borrowed_code_set(rules)
    if not tx_codes:
        return False
    return tx_codes.issubset(borrowed)


def is_non_claim_accounting_only(tx_codes, rules):
    non_claim = non_claim_code_set(rules)
    if not tx_codes:
        return False
    return tx_codes.issubset(non_claim)


def build_reason_codes(tx_codes, rules, annual_flag=False):
    reasons = set()
    if is_borrowed_money_only(tx_codes, rules):
        reasons.add("BORROWED_MONEY_ONLY_CHAIN")
    if is_non_claim_accounting_only(tx_codes, rules):
        reasons.add("NON_CLAIM_ACCOUNTING_ACTIVITY")
    reasons.add("NO_CLAIM_PAYOUT_SEMANTICS")
    if "0412" in tx_codes:
        reasons.add("LOAN_INTEREST_CAPITALIZATION_PATTERN")
    if "0411" in tx_codes and "0412" in tx_codes:
        reasons.add("LOAN_PRINCIPAL_ACCOUNTING_PATTERN")
    if "0451" in tx_codes:
        reasons.add("UNEARNED_INTEREST_INCOME_PATTERN")
    reasons.add("QLADMIN_DOMAIN_MISMATCH_QUIKLOAN")
    if annual_flag:
        reasons.add("ANNUAL_LOAN_CAPITALIZATION_PATTERN")
        reasons.add("ACTIVE_POLICY_SURRENDER_CONTRADICTION")
    configured = rules.get("reason_codes", [])
    return "|".join(sorted(r for r in reasons if r in configured or r in reasons))


def load_phase_artifacts():
    hdr = load_csv(os.path.join(PHASE4, "claim_candidate_header.csv"))
    life = load_csv(os.path.join(PHASE4, "claim_candidate_lifecycle.csv"))
    p10 = load_csv(os.path.join(PHASE10B, "quikclms_derivation_candidates.csv"))
    uat = load_csv(os.path.join(PHASE17, "uat_candidate_quikclms.csv"))
    uat_ids = set()
    if not uat.empty and "reconstructed_claim_id" in uat.columns:
        uat_ids = set(uat["reconstructed_claim_id"].astype(str).str.strip()) - {""}
    return hdr, life, p10, uat_ids


def p10_index(p10):
    idx = {}
    if p10.empty:
        return idx
    for _, row in p10.iterrows():
        cid = strip_val(row.get("reconstructed_claim_id", ""))
        if cid:
            idx[cid] = row
    return idx


def resolve_tx_codes(row, life, claim_id):
    tx = lifecycle_tx_codes(life, claim_id)
    header_codes = parse_codes(row.get("claim_relevant_transaction_codes", ""))
    return tx or header_codes


def row_financials(p10_row):
    if p10_row is None:
        return {"mpaid": 0.0, "mintamt": 0.0, "netdb": 0.0, "mface": 0.0}
    if hasattr(p10_row, "empty") and p10_row.empty:
        return {"mpaid": 0.0, "mintamt": 0.0, "netdb": 0.0, "mface": 0.0}
    if isinstance(p10_row, dict) and not p10_row:
        return {"mpaid": 0.0, "mintamt": 0.0, "netdb": 0.0, "mface": 0.0}
    return {
        "mpaid": to_float(p10_row.get("mpaid", p10_row.get("MPAID", 0))),
        "mintamt": to_float(p10_row.get("mintamt", p10_row.get("MINTAMT", 0))),
        "netdb": to_float(p10_row.get("netdb", p10_row.get("NETDB", 0))),
        "mface": to_float(p10_row.get("mface", p10_row.get("MGROSSAMT", p10_row.get("MGROSSAMT", 0)))),
    }


def should_hold_non_claim_accounting(row, tx_codes, rules, uat_ids):
    if uat_ids and strip_val(row.get("reconstructed_claim_id", "")) not in uat_ids:
        return False
    families = {f.upper() for f in rules.get("eligible_claim_families_for_hold_scan", [])}
    family = strip_val(row.get("claim_family", "")).upper()
    if families and family not in families:
        return False
    if has_claim_domain_semantics(tx_codes, rules):
        return False
    if rules.get("require_accounting_codes_subset_of_non_claim", True):
        return is_non_claim_accounting_only(tx_codes, rules)
    return is_borrowed_money_only(tx_codes, rules)
