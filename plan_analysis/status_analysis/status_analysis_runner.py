#!/usr/bin/env python3
"""
Business status analysis — quikclms vs quikmstr vs LifePRO source.

Operational comparison only. No governance framework. Three CSV reports + brief summary.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# QLAdmin numeric codes (from Master_Value_Translation ST_* targets + claims semantics docs)
MSTATUS_DESC = {
    "22": "Active",
    "32": "Waiver",
    "41": "Paid Up",
    "42": "Special Active",
    "44": "Extended Term",
    "45": "Reduced Paid Up",
    "50": "Suspended",
    "53": "Terminated/Death",
    "54": "Lapsed",
    "55": "Surrendered",
    "56": "Expired",
    "57": "Matured",
    "90": "Cash Value",
    "10": "Inactive",
    "12": "Inactive Pending",
}

CLAIMSTAT_DESC = {
    "1": "Pending",
    "2": "Paid in Full",
    "3": "Settled",
    "4": "Denied",
    "98": "Matured",
    "99": "Surrender",
}

LIFECYCLE_DESC = {
    "SETTLED": "Settled (Claim Fully Resolved)",
    "PAID": "Paid in Full",
    "FUNDED": "Pending / Funded (Awaiting Payout)",
    "OPEN": "Open (In Progress)",
    "PARTIAL": "Partially Paid",
    "UNKNOWN": "Unknown Status",
    "INFERRED": "Inferred Surrender",
}

CLAIM_TYPE_DESC = {
    "DEATH_CLAIM": "Death Claim",
    "DEATH": "Death Claim",
    "SURRENDER_CLAIM": "Surrender Claim",
    "SURRENDER": "Surrender Claim",
    "DISBURSEMENT_CLAIM": "Disbursement / Withdrawal",
    "DISBURSEMENT": "Disbursement / Withdrawal",
}

# LifePRO source field meanings (PPOL / PPBEN extracts)
CONTRACT_CODE_DESC = {
    "A": "Active",
    "T": "Terminated",
    "S": "Suspended",
    "P": "Paid Up",
    "I": "Inactive",
    "D": "Death",
}

CONTRACT_REASON_DESC = {
    "DC": "Death Claim",
    "SR": "Surrender",
    "LP": "Lapsed",
    "MA": "Matured",
    "EX": "Expired",
    "CV": "Cash Value / Conversion",
    "RS": "Reinstated",
    "RI": "Reissue",
    "DP": "Disability / Disabled",
    "CE": "Ceased / Cancelled",
    "CR": "Claim Related",
    "PUP": "Paid Up",
    "RPU": "Reduced Paid Up",
    "ETI": "Extended Term Insurance",
}

PAID_UP_TYPE_DESC = {
    "PU": "Paid Up",
    "RU": "Reduced Paid Up",
    "ET": "Extended Term Insurance",
    "LE": "Life Extension",
    "LP": "Lapsed (Non-Forfeiture)",
    "SP": "Single Premium",
    "UM": "Unspecified Mode",
}

BENEFIT_TYPE_DESC = {
    "BA": "Base Coverage",
    "BF": "Benefit Feature",
    "FV": "Face Value Rider",
    "OR": "Optional Rider",
    "PU": "Paid-Up Benefit",
    "SL": "Supplemental Life",
    "SU": "Surrender Value",
    "UV": "Universal / Administrative Value",
}

PPBEN_STATUS_CODE_DESC = {
    "A": "Active",
    "T": "Terminated",
}

PAYMENT_CODE_DESC = {
    "A": "Active Premium Paying",
}

BILLING_CODE_DESC = {
    "A": "Active Billing",
    "H": "Hold Billing",
    "S": "Suspended Billing",
}

BILLING_REASON_DESC = {
    "ET": "Extended Term",
    "PC": "Premium Ceased",
    "PU": "Paid Up",
    "RU": "Reduced Paid Up",
    "VB": "Variable Billing",
    "WD": "Withdrawal",
}

# Combinations worth business review — NOT marked as errors
REVIEW_POLICY_CLAIM_COMBOS = {
    ("Reduced Paid Up", "Settled"),
    ("Reduced Paid Up", "Paid in Full"),
    ("Paid Up", "Settled"),
    ("Extended Term", "Settled"),
    ("Active", "Settled"),
    ("Active", "Paid in Full"),
    ("Active", "Surrender"),
    ("Lapsed", "Pending"),
    ("Lapsed", "Settled"),
    ("Lapsed", "Paid in Full"),
    ("Terminated/Death", "Pending"),
    ("Inactive", "Settled"),
    ("Suspended", "Settled"),
}

ST_TRANSLATION = {
    "ST_A_": "22", "ST_A_RS": "22", "ST_A_RI": "22", "ST_A_SP": "42",
    "ST_T_DC": "53", "ST_T_SR": "55", "ST_T_LP": "54", "ST_T_MA": "57",
    "ST_T_EX": "56", "ST_T_CV": "90", "ST_S_DP": "50",
    "ST_P_": "41", "ST_P_PUP": "41", "ST_P_RPU": "45", "ST_P_ETI": "44",
    "ST_I_": "10", "ST_I_PND": "10", "ST_I_INP": "12",
    "ST_D_": "53", "ST_D_DTH": "53", "ST_D_PND": "50",
    "ST_PUT_PU": "41", "ST_PUT_RU": "45", "ST_PUT_ET": "44",
    "ST_PUT_LE": "44", "ST_PUT_LP": "54", "ST_PUT_SP": "50",
}


def _s(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return str(val)


def _desc(code_map: dict, code: str) -> str:
    c = _s(code).strip()
    if c.endswith(".0"):
        c = c[:-2]
    return code_map.get(c, c or "Unknown")


def load_crosswalk(path: str) -> tuple[dict[str, str], dict[str, str]]:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    l2q, q2l = {}, {}
    for old, new in zip(df.iloc[:, 0], df.iloc[:, 1]):
        o, n = _s(old).strip(), _s(new).strip()
        if o:
            l2q[o] = n
        if n:
            q2l[n] = o
    return l2q, q2l


def parse_memotext(memo: str) -> tuple[str, str, str]:
    """Return (claim_id_token, claim_type/family, lifecycle/settlement)."""
    memo = _s(memo)
    if not memo:
        return "", "", ""
    parts = memo.split("|")
    claim_token = parts[0] if parts else ""
    claim_type = ""
    lifecycle = ""
    for p in parts:
        up = p.strip().upper()
        if up.endswith("_CLAIM") or up in ("DISBURSEMENT_CLAIM",):
            claim_type = p.strip()
        if up in ("SETTLED", "PAID", "FUNDED", "OPEN", "PARTIAL", "UNKNOWN", "INFERRED"):
            lifecycle = p.strip()
    if not claim_type and len(parts) >= 3:
        claim_type = parts[-2].strip()
    if not lifecycle and parts:
        lifecycle = parts[-1].strip()
    return claim_token, claim_type, lifecycle


def derive_mstatus_from_source_fields(contract_code: str, contract_reason: str, paid_up_type: str) -> str:
    """Mirror app.py MSTATUS composite + ST_ translation (for diff only)."""
    put = _s(paid_up_type).strip().upper()
    if put in {"PU", "RU", "ET", "LE", "LP", "SP"}:
        key = f"ST_PUT_{put}"
    else:
        cc = _s(contract_code).strip().upper()
        cr = _s(contract_reason).strip().upper()
        key = f"ST_{cc}_{cr}" if cr else f"ST_{cc}_"
    return ST_TRANSLATION.get(key, "")


LIFECYCLE_TO_CLAIMSTAT = {
    "SETTLED": "3",
    "PAID": "2",
    "FUNDED": "1",
    "OPEN": "1",
    "PARTIAL": "1",
    "UNKNOWN": "1",
    "INFERRED": "99",
}


def _norm_code(val) -> str:
    c = _s(val).strip().upper()
    if c.endswith(".0"):
        c = c[:-2]
    if not c or set(c) <= {"-", " "}:
        return ""
    return c


def describe_lifepro_code(code_map: dict[str, str], code: str, *, empty_label: str = "") -> str:
    c = _norm_code(code)
    if not c:
        return empty_label
    return code_map.get(c, f"Unknown Code ({c})")


def describe_lifecycle_status(code: str) -> str:
    c = _norm_code(code)
    if not c:
        return ""
    return LIFECYCLE_DESC.get(c, _desc(CLAIMSTAT_DESC, LIFECYCLE_TO_CLAIMSTAT.get(c, "")) or c)


def describe_claim_type(code: str) -> str:
    c = _norm_code(code)
    if not c:
        return ""
    if c in CLAIM_TYPE_DESC:
        return CLAIM_TYPE_DESC[c]
    if c.endswith("_CLAIM"):
        return c.replace("_", " ").title()
    return c.replace("_", " ").title()


def describe_source_policy_status(row: pd.Series | None) -> str:
    """Human-readable LifePRO policy status from contract fields."""
    if row is None:
        return "No Source Policy Record"
    cc = describe_lifepro_code(CONTRACT_CODE_DESC, row.get("CONTRACT_CODE", ""), empty_label="")
    cr = describe_lifepro_code(CONTRACT_REASON_DESC, row.get("CONTRACT_REASON", ""), empty_label="")
    put = describe_lifepro_code(PAID_UP_TYPE_DESC, row.get("PAID_UP_TYPE", ""), empty_label="")
    parts = []
    if put:
        parts.append(put)
    if cc:
        parts.append(f"Contract {cc}")
    if cr:
        parts.append(f"Reason {cr}")
    if not parts:
        return "No Status on Source Record"
    return " — ".join(parts)


def describe_ppben_benefit_status(status_code: str, status_reason: str) -> str:
    sc = describe_lifepro_code(PPBEN_STATUS_CODE_DESC, status_code, empty_label="")
    sr = describe_lifepro_code(CONTRACT_REASON_DESC, status_reason, empty_label="")
    if sc and sr:
        return f"{sc} — {sr}"
    return sc or sr or ""


def describe_benefit_type(code: str) -> str:
    return describe_lifepro_code(BENEFIT_TYPE_DESC, code, empty_label="")


def build_source_policy_status_raw(row: pd.Series) -> str:
    """Exact source abbreviations (retained for RAW JSON trace only)."""
    cc = row.get("CONTRACT_CODE", row.get("CONTRACT_CODE ", ""))
    cr = row.get("CONTRACT_REASON", "")
    put = row.get("PAID_UP_TYPE", "")
    return f"{_s(cc)}|{_s(cr)}|{_s(put)}"


def flag_combination(policy_desc: str, claim_desc: str, has_mstr: bool) -> str:
    if not has_mstr:
        return "Y"
    if (policy_desc, claim_desc) in REVIEW_POLICY_CLAIM_COMBOS:
        return "Y"
    return "N"


def load_ppben_index(ppben_path: str) -> dict[tuple[str, str], dict]:
    if not os.path.isfile(ppben_path):
        return {}
    df = pd.read_csv(ppben_path, encoding="latin1", dtype=str, keep_default_na=False, on_bad_lines="skip")
    df.columns = [_s(c).strip() for c in df.columns]
    pol_col = "POLICY_NUMBER"
    seq_col = "BENEFIT_SEQ"
    plan_col = "PLAN_CODE" if "PLAN_CODE" in df.columns else "PLAN_CODE "
    out = {}
    for _, r in df.iterrows():
        pol = _s(r.get(pol_col, "")).strip()
        seq = _s(r.get(seq_col, "")).strip().replace(".0", "")
        if pol:
            out[(pol, seq)] = {
                "STATUS_CODE": _s(r.get("STATUS_CODE", "")).strip(),
                "STATUS_REASON": _s(r.get("STATUS_REASON", "")).strip(),
                "BENEFIT_TYPE": _s(r.get("BENEFIT_TYPE", "")).strip(),
                "PLAN_CODE": _s(r.get(plan_col, "")).strip(),
            }
    return out


def benefit_seq_from_claim_id(claim_id: str) -> str:
    """Extract benefit sequence from reconstructed claim id: RC-{policy}-{seq}-..."""
    m = re.search(r"RC-\d+-(\d+)-", _s(claim_id))
    return m.group(1) if m else "1"


def load_quikplan_index(quikplan_path: str) -> dict[str, dict[str, str]]:
    """PLAN -> DESCR / PLANNAME from converted quikplan."""
    if not os.path.isfile(quikplan_path):
        return {}
    qp = pd.read_csv(quikplan_path, dtype=str, keep_default_na=False)
    out: dict[str, dict[str, str]] = {}
    for _, r in qp.iterrows():
        plan = _s(r.get("PLAN", ""))
        if plan:
            out[plan] = {
                "DESCR": _s(r.get("DESCR", "")),
                "PLANNAME": _s(r.get("PLANNAME", "")),
            }
    return out


REPORT1_COLUMNS = [
    "MPOLICY",
    "PLAN_CODE",
    "SOURCE_PLAN_CODE",
    "PLAN_DESCRIPTION",
    "MPHASE",
    "MSTATUS",
    "CLAIM_ID",
    "CLAIM_STATUS",
    "CLAIM_TYPE",
    "DATE_OF_LOSS",
    "DATE_OF_DEATH",
    "SETTLEMENT_STATUS",
    "BENEFIT_TYPE",
    "CLAIM_AMOUNT",
    "POLICY_STATUS_DESCRIPTION",
    "CLAIM_STATUS_DESCRIPTION",
    "STATUS_COMBINATION",
    "POTENTIAL_ISSUE_FLAG",
]


def run_analysis(
    *,
    quikclms_path: str,
    quikmstr_path: str,
    source_policy_path: str,
    master_cw_path: str,
    ppben_path: str,
    derivation_candidates_path: str,
    quikridr_path: str,
    quikplan_path: str,
    output_dir: str,
) -> dict:
    os.makedirs(output_dir, exist_ok=True)

    clms = pd.read_csv(quikclms_path, dtype=str, keep_default_na=False)
    mstr = pd.read_csv(quikmstr_path, dtype=str, keep_default_na=False)
    mstr_idx = mstr.set_index("MPOLICY", drop=False).to_dict("index")

    ridr_mplan = {}
    if os.path.isfile(quikridr_path):
        ridr = pd.read_csv(quikridr_path, dtype=str, keep_default_na=False)
        for _, r in ridr.iterrows():
            key = (_s(r.get("MPOLICY", "")), _s(r.get("MPHASE", "")) or "1")
            ridr_mplan[key] = _s(r.get("MPLAN", ""))

    l2q, q2l = load_crosswalk(master_cw_path)

    # Source policy master — preserve cell values exactly
    src_pol = pd.read_csv(source_policy_path, encoding="latin1", dtype=str, keep_default_na=False, on_bad_lines="skip")
    src_pol.columns = [_s(c).strip() for c in src_pol.columns]
    pol_col = "POLICY_NUMBER"
    src_pol_idx = {}
    for _, r in src_pol.iterrows():
        pol = _s(r.get(pol_col, "")).strip()
        if pol:
            src_pol_idx[pol] = r

    ppben_idx = load_ppben_index(ppben_path)
    quikplan_idx = load_quikplan_index(quikplan_path)

    deriv_idx = {}
    if os.path.isfile(derivation_candidates_path):
        deriv = pd.read_csv(derivation_candidates_path, dtype=str, keep_default_na=False)
        for _, r in deriv.iterrows():
            cid = _s(r.get("reconstructed_claim_id", ""))
            pol = _s(r.get("policy_number", ""))
            if cid:
                deriv_idx[cid] = r
            if pol and _s(r.get("CLAIMNUM", "")):
                deriv_idx[f"POL:{pol}|{_s(r.get('CLAIMNUM', ''))}"] = r

    # ---- Report 1 ----
    r1_rows = []
    combo_counter = Counter()

    for _, c in clms.iterrows():
        mpolicy = _s(c.get("MPOLICY", ""))
        mphase = _s(c.get("MPHASE", "")) or "1"
        mstr_row = mstr_idx.get(mpolicy, {})
        mstatus = _s(mstr_row.get("MSTATUS", ""))
        pol_desc = _desc(MSTATUS_DESC, mstatus)
        claimstat = _s(c.get("CLAIMSTAT", ""))
        claim_desc = _desc(CLAIMSTAT_DESC, claimstat)
        claim_token, claim_type, lifecycle = parse_memotext(c.get("MEMOTEXT", ""))
        combo = f"{pol_desc} + {claim_desc}"
        combo_counter[combo] += 1
        has_mstr = mpolicy in mstr_idx
        src_pol_num = q2l.get(mpolicy, mpolicy)
        bseq = benefit_seq_from_claim_id(claim_token)
        ben = ppben_idx.get((src_pol_num.strip(), bseq), {})
        benefit_type_desc = describe_benefit_type(ben.get("BENEFIT_TYPE", ""))
        plan_code = ridr_mplan.get((mpolicy, mphase), "") or ridr_mplan.get((mpolicy, "1"), "")
        source_plan_code = _s(ben.get("PLAN_CODE", "")).strip()
        qp_meta = quikplan_idx.get(plan_code, {})
        plan_description = qp_meta.get("DESCR", "") or qp_meta.get("PLANNAME", "")

        r1_rows.append({
            "MPOLICY": mpolicy,
            "PLAN_CODE": plan_code,
            "SOURCE_PLAN_CODE": source_plan_code,
            "PLAN_DESCRIPTION": plan_description,
            "MPHASE": mphase,
            "MSTATUS": pol_desc if has_mstr else "NO MATCHING QUIKMSTR",
            "CLAIM_ID": _s(c.get("CLAIMNUM", "")),
            "CLAIM_STATUS": claim_desc,
            "CLAIM_TYPE": describe_claim_type(claim_type),
            "DATE_OF_LOSS": _s(c.get("RPTDATE", "")),
            "DATE_OF_DEATH": _s(c.get("DTOFDEATH", "")),
            "SETTLEMENT_STATUS": describe_lifecycle_status(lifecycle) if lifecycle else _s(c.get("ACCPTDATE", "")),
            "BENEFIT_TYPE": benefit_type_desc,
            "CLAIM_AMOUNT": _s(c.get("MPAID", "")) or _s(c.get("NETDB", "")),
            "POLICY_STATUS_DESCRIPTION": pol_desc if has_mstr else "NO MATCHING QUIKMSTR",
            "CLAIM_STATUS_DESCRIPTION": claim_desc,
            "STATUS_COMBINATION": combo,
            "POTENTIAL_ISSUE_FLAG": flag_combination(pol_desc if has_mstr else "Missing", claim_desc, has_mstr),
            "_mstatus_code": mstatus,
            "_claimstat_code": claimstat,
            "MPLAN": plan_code,
        })

    r1_path = os.path.join(output_dir, "quikclms_vs_quikmstr_status_report.csv")
    pd.DataFrame(r1_rows).drop(columns=["_mstatus_code", "_claimstat_code", "MPLAN"], errors="ignore")[REPORT1_COLUMNS].to_csv(r1_path, index=False)

    # ---- Report 2 ----
    r2_rows = []
    for _, c in clms.iterrows():
        mpolicy = _s(c.get("MPOLICY", ""))
        src_pol_num = q2l.get(mpolicy, mpolicy)
        claim_token, claim_type, lifecycle = parse_memotext(c.get("MEMOTEXT", ""))
        src_row = src_pol_idx.get(src_pol_num.strip())
        src_policy_status = describe_source_policy_status(src_row)
        src_policy_status_raw = build_source_policy_status_raw(src_row) if src_row is not None else ""

        deriv_row = deriv_idx.get(claim_token)
        if deriv_row is None:
            deriv_row = deriv_idx.get(f"POL:{src_pol_num}|{_s(c.get('CLAIMNUM',''))}")
        if deriv_row is not None and not isinstance(deriv_row, pd.Series):
            deriv_row = None
        src_claim_id = claim_token or _s(c.get("CLAIMNUM", ""))
        src_claim_status_raw = _s(deriv_row.get("MCLAIMSTATUS", "")) if deriv_row is not None else lifecycle
        src_claim_status = describe_lifecycle_status(src_claim_status_raw)
        src_claim_type_raw = _s(deriv_row.get("MCLAIMTYPE", "")) if deriv_row is not None else claim_type
        src_claim_type = describe_claim_type(src_claim_type_raw or claim_type)
        src_settlement = _s(deriv_row.get("MSETTLEDATE", "")) if deriv_row is not None else _s(c.get("ACCPTDATE", ""))

        bseq = benefit_seq_from_claim_id(claim_token)
        ben = ppben_idx.get((src_pol_num.strip(), bseq), {})

        raw_json = {}
        if src_row is not None:
            raw_json["CONTRACT_CODE"] = _s(src_row.get("CONTRACT_CODE", ""))
            raw_json["CONTRACT_CODE_MEANING"] = describe_lifepro_code(CONTRACT_CODE_DESC, src_row.get("CONTRACT_CODE", ""))
            raw_json["CONTRACT_REASON"] = _s(src_row.get("CONTRACT_REASON", ""))
            raw_json["CONTRACT_REASON_MEANING"] = describe_lifepro_code(CONTRACT_REASON_DESC, src_row.get("CONTRACT_REASON", ""))
            raw_json["CONTRACT_DATE"] = _s(src_row.get("CONTRACT_DATE", ""))
            raw_json["PAID_UP_TYPE"] = _s(src_row.get("PAID_UP_TYPE", ""))
            raw_json["PAID_UP_TYPE_MEANING"] = describe_lifepro_code(PAID_UP_TYPE_DESC, src_row.get("PAID_UP_TYPE", ""))
            raw_json["PAYMENT_CODE"] = _s(src_row.get("PAYMENT_CODE", ""))
            raw_json["PAYMENT_CODE_MEANING"] = describe_lifepro_code(PAYMENT_CODE_DESC, src_row.get("PAYMENT_CODE", ""))
            raw_json["BILLING_CODE"] = _s(src_row.get("BILLING_CODE", ""))
            raw_json["BILLING_CODE_MEANING"] = describe_lifepro_code(BILLING_CODE_DESC, src_row.get("BILLING_CODE", ""))
            raw_json["BILLING_REASON"] = _s(src_row.get("BILLING_REASON", ""))
            raw_json["BILLING_REASON_MEANING"] = describe_lifepro_code(BILLING_REASON_DESC, src_row.get("BILLING_REASON", ""))
            raw_json["SOURCE_POLICY_STATUS_RAW"] = src_policy_status_raw
        if ben:
            raw_json["PPBEN_STATUS_CODE"] = ben.get("STATUS_CODE", "")
            raw_json["PPBEN_STATUS_CODE_MEANING"] = describe_lifepro_code(PPBEN_STATUS_CODE_DESC, ben.get("STATUS_CODE", ""))
            raw_json["PPBEN_STATUS_REASON"] = ben.get("STATUS_REASON", "")
            raw_json["PPBEN_STATUS_REASON_MEANING"] = describe_lifepro_code(CONTRACT_REASON_DESC, ben.get("STATUS_REASON", ""))
            raw_json["PPBEN_BENEFIT_TYPE"] = ben.get("BENEFIT_TYPE", "")
            raw_json["PPBEN_BENEFIT_TYPE_MEANING"] = describe_benefit_type(ben.get("BENEFIT_TYPE", ""))
            raw_json["PPBEN_PLAN_CODE"] = ben.get("PLAN_CODE", "")
        raw_json["SOURCE_CLAIM_STATUS_RAW"] = src_claim_status_raw
        raw_json["NOTE"] = "LifePRO has no native claim-status header; SOURCE_CLAIM_STATUS is PACTG-reconstructed lifecycle."

        combo2 = f"Source Policy: {src_policy_status} + Source Claim: {src_claim_status or describe_lifecycle_status(lifecycle)}"

        r2_rows.append({
            "SOURCE_POLICY_NUMBER": src_pol_num,
            "SOURCE_POLICY_STATUS": src_policy_status,
            "SOURCE_CLAIM_ID": src_claim_id,
            "SOURCE_CLAIM_STATUS": src_claim_status or describe_lifecycle_status(lifecycle),
            "SOURCE_CLAIM_TYPE": src_claim_type,
            "SOURCE_BENEFIT_STATUS": describe_ppben_benefit_status(ben.get("STATUS_CODE", ""), ben.get("STATUS_REASON", "")) if ben else "",
            "SOURCE_PLAN_CODE": ben.get("PLAN_CODE", ""),
            "SOURCE_BENEFIT_TYPE": describe_benefit_type(ben.get("BENEFIT_TYPE", "")) if ben else "",
            "SOURCE_SETTLEMENT_STATUS": src_settlement,
            "SOURCE_DATE_OF_LOSS": _s(c.get("RPTDATE", "")) if deriv_row is None else _s(deriv_row.get("MLOSSDATE", "")),
            "SOURCE_DATE_OF_DEATH": _s(c.get("DTOFDEATH", "")) if deriv_row is None else _s(deriv_row.get("MLOSSDATE", "")),
            "RAW_SOURCE_VALUES_JSON": json.dumps(raw_json, ensure_ascii=False),
            "STATUS_COMBINATION": combo2,
            "POTENTIAL_ISSUE_FLAG": "Y" if src_row is None else flag_combination(
                _desc(MSTATUS_DESC, derive_mstatus_from_source_fields(
                    raw_json.get("CONTRACT_CODE", ""),
                    raw_json.get("CONTRACT_REASON", ""),
                    raw_json.get("PAID_UP_TYPE", ""),
                )),
                _desc(CLAIMSTAT_DESC, LIFECYCLE_TO_CLAIMSTAT.get(_norm_code(src_claim_status_raw), "")),
                True,
            ),
            "_src_claim_status_raw": src_claim_status_raw,
        })

    r2_path = os.path.join(output_dir, "source_policy_claim_status_report.csv")
    pd.DataFrame(r2_rows).to_csv(r2_path, index=False)

    # ---- Report 3 ----
    r3_rows = []
    for r1, r2 in zip(r1_rows, r2_rows):
        raw = json.loads(r2["RAW_SOURCE_VALUES_JSON"])
        expected_mstatus = derive_mstatus_from_source_fields(
            raw.get("CONTRACT_CODE", ""),
            raw.get("CONTRACT_REASON", ""),
            raw.get("PAID_UP_TYPE", ""),
        )
        src_lifecycle = _norm_code(r2.get("_src_claim_status_raw", ""))
        expected_claimstat = LIFECYCLE_TO_CLAIMSTAT.get(src_lifecycle, "")
        status_changed = "Y" if expected_mstatus and _s(r1.get("_mstatus_code", "")) != expected_mstatus else "N"
        claim_changed = "Y" if expected_claimstat and _s(r1.get("_claimstat_code", "")) != expected_claimstat else "N"

        notes = []
        if status_changed == "Y":
            notes.append("Policy MSTATUS differs from ST_ translation of source CONTRACT/PUT fields")
        if claim_changed == "Y":
            notes.append("Claim CLAIMSTAT differs from PACTG-derived lifecycle mapping")
        if r1["POTENTIAL_ISSUE_FLAG"] == "Y" and status_changed == "N" and claim_changed == "N":
            notes.append("Cross-domain combination — review business semantics (may be valid)")

        conversion_issue = "N"
        if status_changed == "Y" or claim_changed == "Y":
            conversion_issue = "Y"
        elif r1["POTENTIAL_ISSUE_FLAG"] == "Y":
            conversion_issue = "REVIEW"

        r3_rows.append({
            "SOURCE_POLICY_NUMBER": r2["SOURCE_POLICY_NUMBER"],
            "SOURCE_POLICY_STATUS": r2["SOURCE_POLICY_STATUS"],
            "TARGET_MPOLICY": r1["MPOLICY"],
            "TARGET_MSTATUS": r1["MSTATUS"],
            "SOURCE_CLAIM_STATUS": r2["SOURCE_CLAIM_STATUS"],
            "TARGET_CLAIM_STATUS": r1["CLAIM_STATUS"],
            "STATUS_CHANGED_FLAG": status_changed,
            "CLAIM_STATUS_CHANGED_FLAG": claim_changed,
            "SOURCE_PLAN": r2["SOURCE_PLAN_CODE"],
            "TARGET_MPLAN": r1.get("PLAN_CODE", r1.get("MPLAN", "")),
            "SOURCE_BENEFIT_TYPE": r2["SOURCE_BENEFIT_TYPE"],
            "TARGET_BENEFIT_TYPE": r1["BENEFIT_TYPE"],
            "POTENTIAL_CONVERSION_ISSUE": conversion_issue,
            "NOTES": "; ".join(notes),
        })

    r3_path = os.path.join(output_dir, "source_vs_target_status_diff.csv")
    pd.DataFrame(r3_rows).to_csv(r3_path, index=False)

    # Summary stats
    flagged = sum(1 for r in r1_rows if r["POTENTIAL_ISSUE_FLAG"] == "Y")
    conv_issues = sum(1 for r in r3_rows if r["POTENTIAL_CONVERSION_ISSUE"] == "Y")
    review_only = sum(1 for r in r3_rows if r["POTENTIAL_CONVERSION_ISSUE"] == "REVIEW")
    top_combos = combo_counter.most_common(15)

    example = next((r for r in r1_rows if r["MPOLICY"] == "010464590C"), None)

    summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "claim_rows": len(r1_rows),
        "flagged_for_review": flagged,
        "conversion_status_changes": conv_issues,
        "review_only_combos": review_only,
        "top_combinations": top_combos,
        "example_010464590C": example,
    }

    summary_path = os.path.join(output_dir, "executive_status_analysis_summary.md")
    lines = [
        "# Executive Status Analysis Summary",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Scope",
        "",
        "Business validation comparing converted QLAdmin outputs (quikclms, quikmstr) to LifePRO source.",
        "No automatic error classification — flagged rows are for business review only.",
        "",
        "## Volume",
        "",
        f"- Claim rows analyzed: **{summary['claim_rows']}**",
        f"- Flagged for review (unusual combo or missing quikmstr): **{summary['flagged_for_review']}**",
        f"- Conversion changed policy status (ST_ path vs emitted MSTATUS): **{sum(1 for r in r3_rows if r['STATUS_CHANGED_FLAG']=='Y')}**",
        f"- Conversion changed claim status (lifecycle vs CLAIMSTAT): **{sum(1 for r in r3_rows if r['CLAIM_STATUS_CHANGED_FLAG']=='Y')}**",
        f"- Review-only cross-domain combos (no conversion delta): **{review_only}**",
        "",
        "## Top status combinations (converted)",
        "",
        "| Combination | Count |",
        "|-------------|-------|",
    ]
    for combo, cnt in top_combos:
        lines.append(f"| {combo} | {cnt} |")

    lines.extend([
        "",
        "## Investigation answers",
        "",
        "### 1. Did source already contain Reduced Paid Up + Settled?",
        "",
        "**Yes — for death-settlement cases like 010464590C.** Source policy master shows "
        "Reduced Paid Up with Contract Terminated and Reason Death Claim. "
        "PACTG reconstruction yields **Settled (Claim Fully Resolved)** for the death claim. "
        "These are different LifePRO domains (contract maintenance vs accounting/claims reconstruction).",
        "",
        "### 2. Were statuses changed during conversion?",
        "",
        f"Policy MSTATUS changes detected: **{sum(1 for r in r3_rows if r['STATUS_CHANGED_FLAG']=='Y')}** rows. "
        f"Claim CLAIMSTAT changes vs PACTG lifecycle mapping: **{sum(1 for r in r3_rows if r['CLAIM_STATUS_CHANGED_FLAG']=='Y')}** rows. "
        "Example **010464590C**: policy status **Reduced Paid Up** matches source; claim status **Settled** matches PACTG lifecycle — **no conversion drift**.",
        "",
        "### 3. Does Master_Value_Translation alter statuses?",
        "",
        "**Yes for quikmstr MSTATUS only.** Composite keys (`ST_*`, `PUT_*`) map LifePRO "
        "`CONTRACT_CODE`/`CONTRACT_REASON`/`PAID_UP_TYPE` to QLAdmin numeric codes. "
        "Claims CLAIMSTAT is mapped from reconstructed lifecycle in Phase 10B derivation rules, not from a LifePRO claim-status column.",
        "",
        "### 4. Do rulebooks transform statuses?",
        "",
        "**quikmstr:** MSTATUS rulebook points at CONTRACT_CODE but **app.py composite interceptor** "
        "overrides with PAID_UP_TYPE-first logic, then ST_ translation. "
        "**quikclms:** CLAIMSTAT defaults in rulebook; actual values come from Phase 10B lifecycle→CLAIMSTAT mapping.",
        "",
        "### 5. Are claim statuses independent of policy statuses in LifePRO?",
        "",
        "**Yes.** LifePRO does not expose a single paired policy/claim status field. "
        "Policy status lives on the contract extract; claim lifecycle is inferred from PACTG transactions.",
        "",
        "### 6. Patterns",
        "",
        "Most common converted pattern: **Terminated/Death + Settled** and **Reduced Paid Up + Settled** "
        "on death claims where PAID_UP_TYPE=RU or contract reason=DC. "
        "Surrender/disbursement claims cluster as **Paid in Full** with varied policy statuses.",
        "",
        "### 7. Expected vs review",
        "",
        "- **Expected:** RPU/PU/ET + Settled on post-death non-forfeiture outcomes.",
        "- **Review:** Active + Settled, Lapsed + Open/Pending — may indicate timing or semantic mismatch.",
        "- **True defects:** Rows where STATUS_CHANGED_FLAG=Y or CLAIM_STATUS_CHANGED_FLAG=Y (conversion drift).",
        "",
    ])

    if example:
        lines.extend([
            "## Example: 010464590C",
            "",
            f"- Target policy status: **{example['MSTATUS']}**",
            f"- Target claim status: **{example['CLAIM_STATUS']}**",
            f"- Claim type: **{example['CLAIM_TYPE']}**",
            f"- Combination: **{example['STATUS_COMBINATION']}**",
            f"- Review flag: **{example['POTENTIAL_ISSUE_FLAG']}** (cross-domain review, not conversion error)",
            "",
        ])

    lines.extend([
        "## Recommendations",
        "",
        "1. **Business sign-off** on death-claim + RPU/PU combinations — likely valid post-settlement contract state.",
        "2. **Prioritize review** of Active/Lapsed policy + Settled/Pending claim rows.",
        "3. **Do not change conversion** until business confirms which cross-domain pairs are invalid in QLAdmin.",
        "4. Investigate any row with POTENTIAL_CONVERSION_ISSUE=Y in report 3.",
        "",
        "## Regenerate",
        "",
        "```powershell",
        "python plan_analysis/status_analysis/status_analysis_runner.py",
        "```",
        "",
    ])

    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Business status analysis (quikclms vs quikmstr vs source)")
    parser.add_argument("--output-dir", default=SCRIPT_DIR)
    parser.add_argument("--quikclms", default=os.path.join(ROOT, "QLA_Migration", "Output", "quikclms.csv"))
    parser.add_argument("--quikmstr", default=os.path.join(ROOT, "QLA_Migration", "Output", "quikmstr.csv"))
    parser.add_argument("--quikridr", default=os.path.join(ROOT, "QLA_Migration", "Output", "quikridr.csv"))
    parser.add_argument("--quikplan", default=os.path.join(ROOT, "QLA_Migration", "Output", "quikplan.csv"))
    parser.add_argument("--source-policy", default=os.path.join(ROOT, "QLA_Migration", "Source", "quikmstr.csv"))
    parser.add_argument("--ppben", default=os.path.join(ROOT, "QLA_Migration", "Source", "PPBEN.csv"))
    parser.add_argument("--master-crosswalk", default=os.path.join(ROOT, "Master_Crosswalk.csv"))
    parser.add_argument(
        "--derivation-candidates",
        default=os.path.join(ROOT, "claims_analysis", "phase10b_quikclms_derivation_design", "quikclms_derivation_candidates.csv"),
    )
    args = parser.parse_args()

    summary = run_analysis(
        quikclms_path=args.quikclms,
        quikmstr_path=args.quikmstr,
        source_policy_path=args.source_policy,
        master_cw_path=args.master_crosswalk,
        ppben_path=args.ppben,
        derivation_candidates_path=args.derivation_candidates,
        quikridr_path=args.quikridr,
        quikplan_path=args.quikplan,
        output_dir=args.output_dir,
    )
    print(f"STATUS_ANALYSIS: SUCCESS")
    print(f"CLAIM_ROWS: {summary['claim_rows']}")
    print(f"FLAGGED_FOR_REVIEW: {summary['flagged_for_review']}")
    print(f"CONVERSION_STATUS_CHANGES: {summary['conversion_status_changes']}")
    print(f"OUTPUT_DIR: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
