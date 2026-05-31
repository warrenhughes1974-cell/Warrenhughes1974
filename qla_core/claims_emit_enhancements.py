"""Surgical UAT emit enhancements for quikclms/quikclmp (CLAIMNUM, ISWL/98, MSEQ)."""

from __future__ import annotations

import csv
import json
import os
import re
from typing import Any

import pandas as pd

from qla_core.normalize_utils import normalize

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.normpath(os.path.join(_SCRIPT_DIR, ".."))
_DEFAULT_RULES = os.path.join(
    _ROOT, "claims_analysis", "config", "claims_emit_enhancements.json"
)

_GOVERNANCE_COLUMNS = frozenset({
    "audit_timestamp",
    "rollback_snapshot_id",
    "production_dbf_flag",
    "record_type",
    "reconstructed_claim_id",
    "prototype_claimnum",
    "derivation_candidate_id",
    "replay_source",
    "uat_segment",
    "governance_status",
    "business_review_required",
    "replay_authorization_status",
    "reconciliation_status",
    "generation_status",
    "blocker_category",
    "business_explanation",
    "orphan_impact",
    "reconciliation_impact",
    "replay_eligibility",
    "remediation_recommendation",
    "rulebook_lineage",
})

_RC_SEQ_RE = re.compile(r"-C(\d+)-", re.IGNORECASE)


def load_enhancement_rules(path: str | None = None) -> dict[str, Any]:
    rules_path = path or _DEFAULT_RULES
    with open(rules_path, encoding="utf-8") as fh:
        return json.load(fh)


def normalize_claimnum_13(value) -> str:
    """Return first 13 characters of trimmed source claim id; empty when absent."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if not text or text.lower() in ("nan", "none"):
        return ""
    return text[:13]


def _strip_lower(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if not text or text.lower() in ("nan", "none"):
        return ""
    return text


def resolve_source_claim_id(combined: dict, rules: dict | None = None) -> str:
    cfg = rules or load_enhancement_rules()
    for field in cfg.get("source_claim_id_fields", []):
        val = _strip_lower(combined.get(field, ""))
        if val:
            return val
    return ""


def build_plan_metadata_lookup(
    quikridr_path: str,
    quikplan_path: str,
) -> dict[str, dict[str, str]]:
    """Map converted MPOLICY -> plan metadata from quikridr phase-1 MPLAN + quikplan."""
    lookup: dict[str, dict[str, str]] = {}
    if not os.path.isfile(quikridr_path) or not os.path.isfile(quikplan_path):
        return lookup

    try:
        ridr = pd.read_csv(quikridr_path, dtype=str).fillna("")
        ridr.columns = [str(c).strip().upper() for c in ridr.columns]
        plan_df = pd.read_csv(quikplan_path, dtype=str).fillna("")
        plan_df.columns = [str(c).strip().upper() for c in plan_df.columns]
    except Exception:
        return lookup

    plan_index: dict[str, dict[str, str]] = {}
    for _, row in plan_df.iterrows():
        plan_code = normalize(row.get("PLAN", ""))
        if not plan_code:
            continue
        plan_index[plan_code] = {
            "mplan": plan_code,
            "descr": _strip_lower(row.get("DESCR", "")),
            "planname": _strip_lower(row.get("PLANNAME", "")),
            "plantype": _strip_lower(row.get("PLANTYPE", "")),
            "hlob": _strip_lower(row.get("HLOB", "")),
            "product": _strip_lower(row.get("PRODUCT", "")),
        }

    if "MPOLICY" not in ridr.columns:
        return lookup

    phase_col = "MPHASE" if "MPHASE" in ridr.columns else None
    grouped = ridr.groupby("MPOLICY", sort=False)
    for mpolicy, grp in grouped:
        pol = normalize(mpolicy)
        if not pol:
            continue
        target = grp
        if phase_col:
            phase1 = grp[grp[phase_col].astype(str).str.strip() == "1"]
            if not phase1.empty:
                target = phase1
        mplan = normalize(target.iloc[0].get("MPLAN", ""))
        meta = dict(plan_index.get(mplan, {}))
        meta.setdefault("mplan", mplan)
        lookup[pol] = meta
    return lookup


def _contains_iswl(*values: str) -> bool:
    for val in values:
        text = _strip_lower(val).upper()
        if text and "ISWL" in text:
            return True
    return False


def is_iswl_claim_record(
    combined: dict,
    plan_meta: dict | None = None,
    rules: dict | None = None,
) -> bool:
    cfg = rules or load_enhancement_rules()
    tokens: list[str] = []
    for field in cfg.get("iswl_indicator_fields", []):
        tokens.append(_strip_lower(combined.get(field, "")))
    if plan_meta:
        tokens.extend(
            _strip_lower(plan_meta.get(key, ""))
            for key in ("mplan", "descr", "planname", "plantype", "hlob", "product")
        )
    return _contains_iswl(*tokens)


def _plan_description_values(combined: dict, plan_meta: dict | None, rules: dict) -> list[str]:
    values: list[str] = []
    for field in rules.get("plan_description_fields", []):
        values.append(_strip_lower(combined.get(field, "")))
    if plan_meta:
        values.append(_strip_lower(plan_meta.get("descr", "")))
        values.append(_strip_lower(plan_meta.get("planname", "")))
    return values


def has_disbursement_withdrawal_signal(
    combined: dict,
    plan_meta: dict | None = None,
    rules: dict | None = None,
) -> bool:
    cfg = rules or load_enhancement_rules()
    phrase = str(cfg.get("disbursement_withdrawal_phrase", "Disbursement / Withdrawal")).strip()
    phrase_lower = phrase.lower()
    for val in _plan_description_values(combined, plan_meta, cfg):
        if val and phrase_lower in val.lower():
            return True
    family_tokens = {t.upper() for t in cfg.get("disbursement_family_tokens", [])}
    for field in ("claim_family", "mclaimfamily", "mclaimtype"):
        token = _strip_lower(combined.get(field, "")).upper()
        if token in family_tokens:
            return True
    return False


def classify_iswl_surrender_claimstat(
    combined: dict,
    plan_meta: dict | None = None,
    rules: dict | None = None,
) -> str | None:
    cfg = rules or load_enhancement_rules()
    if not has_disbursement_withdrawal_signal(combined, plan_meta, cfg):
        return None
    return str(cfg.get("claimstat_iswl_surrender", "99")).strip()


def _parse_claim_sequence_mseq(reconstructed_claim_id: str) -> str:
    match = _RC_SEQ_RE.search(str(reconstructed_claim_id or ""))
    if not match:
        return ""
    try:
        return str(int(match.group(1)) + 1)
    except ValueError:
        return ""


def resolve_status_98_mseq(combined: dict) -> str:
    for field in ("mseq", "payment_sequence"):
        raw = _strip_lower(combined.get(field, ""))
        if raw and raw not in ("0", "0.0"):
            try:
                return str(int(float(raw.replace(",", ""))))
            except ValueError:
                continue
    parsed = _parse_claim_sequence_mseq(combined.get("reconstructed_claim_id", ""))
    if parsed:
        return parsed
    return "1"


def resolve_emit_mseq(
    table_key: str,
    combined: dict,
    claimstat: str,
    rules: dict | None = None,
) -> str:
    cfg = rules or load_enhancement_rules()
    target_98 = str(cfg.get("claimstat_iswl_surrender", "98")).strip()
    default_mseq = str(cfg.get("default_mseq", "0")).strip() or "0"
    if str(claimstat or "").strip() != target_98:
        return default_mseq
    return resolve_status_98_mseq(combined)


def apply_claims_emit_enhancements(
    qla_row: dict,
    combined: dict,
    table_key: str,
    plan_lookup: dict | None = None,
    rules: dict | None = None,
) -> dict:
    cfg = rules or load_enhancement_rules()
    out = dict(qla_row)
    mpolicy = normalize(out.get("MPOLICY", ""))
    plan_meta = (plan_lookup or {}).get(mpolicy, {})

    if table_key == "quikclms":
        source_id = resolve_source_claim_id(combined, cfg)
        if source_id:
            out["CLAIMNUM"] = normalize_claimnum_13(source_id)
        iswl_stat = classify_iswl_surrender_claimstat(combined, plan_meta, cfg)
        if iswl_stat:
            out["CLAIMSTAT"] = iswl_stat
            out["ORIGSTTUS"] = iswl_stat
        if not str(out.get("MSEQ", "")).strip():
            out["MSEQ"] = str(cfg.get("default_mseq", "0")).strip() or "0"
    elif table_key == "quikclmp":
        if not str(out.get("MSEQ", "")).strip():
            out["MSEQ"] = str(cfg.get("default_mseq", "0")).strip() or "0"
    return out


def validate_claims_emit_enhancements(
    clms_df: pd.DataFrame | None,
    clmp_df: pd.DataFrame | None,
    clms_schema: list[str],
    clmp_schema: list[str],
    rules: dict | None = None,
) -> dict[str, Any]:
    cfg = rules or load_enhancement_rules()
    target_98 = str(cfg.get("claimstat_iswl_surrender", "98")).strip()
    default_mseq = str(cfg.get("default_mseq", "0")).strip() or "0"
    max_len = int(cfg.get("claimnum_max_length", 13))

    clms = clms_df if clms_df is not None else pd.DataFrame(columns=clms_schema)
    clmp = clmp_df if clmp_df is not None else pd.DataFrame(columns=clmp_schema)

    claimnums = clms["CLAIMNUM"].astype(str).str.strip() if "CLAIMNUM" in clms.columns else pd.Series(dtype=str)
    normalized_count = int((claimnums != "").sum()) if not claimnums.empty else 0
    over_len = int(claimnums.str.len().gt(max_len).sum()) if not claimnums.empty else 0

    iswl_98_count = 0
    if "CLAIMSTAT" in clms.columns:
        iswl_98_count = int((clms["CLAIMSTAT"].astype(str).str.strip() == target_98).sum())

    non98_clms_bad = 0
    if "MSEQ" in clms.columns and "CLAIMSTAT" in clms.columns:
        mask = clms["CLAIMSTAT"].astype(str).str.strip() != target_98
        non98_clms_bad = int((mask & (clms["MSEQ"].astype(str).str.strip() != default_mseq)).sum())

    non98_clmp_bad = 0
    status98_mseq_values: set[str] = set()
    claim_keys: set[tuple[str, str, str]] = set()
    clms_98_keys: set[tuple[str, str, str]] = set()
    if not clms.empty and {"MPOLICY", "MPHASE", "MSEQ"}.issubset(clms.columns):
        for _, row in clms.iterrows():
            key = (
                normalize(row.get("MPOLICY", "")),
                str(row.get("MPHASE", "")).strip(),
                str(row.get("MSEQ", "")).strip(),
            )
            claim_keys.add(key)
            if str(row.get("CLAIMSTAT", "")).strip() == target_98:
                clms_98_keys.add(key)
                if key[2] != default_mseq:
                    status98_mseq_values.add(key[2])

    if "MSEQ" in clmp.columns and not clmp.empty:
        for _, row in clmp.iterrows():
            key = (
                normalize(row.get("MPOLICY", "")),
                str(row.get("MPHASE", "")).strip(),
                str(row.get("MSEQ", "")).strip(),
            )
            mseq_val = key[2]
            if key in clms_98_keys and mseq_val != default_mseq:
                status98_mseq_values.add(mseq_val)
            if mseq_val != default_mseq and key not in clms_98_keys:
                non98_clmp_bad += 1

    orphan_payments = 0
    orphan_claims = 0
    if claim_keys and not clmp.empty and {"MPOLICY", "MPHASE", "MSEQ"}.issubset(clmp.columns):
        payment_keys = {
            (
                normalize(r["MPOLICY"]),
                str(r["MPHASE"]).strip(),
                str(r["MSEQ"]).strip(),
            )
            for _, r in clmp.iterrows()
        }
        orphan_payments = len(payment_keys - claim_keys)
        orphan_claims = len(claim_keys - payment_keys)

    clms_schema_ok = list(clms.columns) == list(clms_schema) if not clms.empty else True
    clmp_schema_ok = list(clmp.columns) == list(clmp_schema) if not clmp.empty else True
    clms_gov_leak = int(any(col.lower() in _GOVERNANCE_COLUMNS for col in clms.columns))
    clmp_gov_leak = int(any(col.lower() in _GOVERNANCE_COLUMNS for col in clmp.columns))

    linkage_ok = orphan_payments == 0
    claimnum_ok = over_len == 0
    mseq_ok = non98_clms_bad == 0 and non98_clmp_bad == 0
    governance_ok = clms_gov_leak == 0 and clmp_gov_leak == 0 and clms_schema_ok and clmp_schema_ok

    return {
        "claimnum_normalized_count": normalized_count,
        "claimnum_over_max_length": over_len,
        "claimnum_max_length": max_len,
        "iswl_status_98_count": iswl_98_count,
        "non98_clms_mseq_not_zero": non98_clms_bad,
        "non98_clmp_mseq_not_zero": non98_clmp_bad,
        "status98_nonzero_mseq_values": sorted(status98_mseq_values),
        "orphan_payments": orphan_payments,
        "orphan_claims": orphan_claims,
        "clms_schema_ok": clms_schema_ok,
        "clmp_schema_ok": clmp_schema_ok,
        "governance_metadata_leaked": clms_gov_leak + clmp_gov_leak,
        "validation_status": "PASS" if claimnum_ok and mseq_ok and governance_ok else "REVIEW",
        "linkage_status": "PASS" if linkage_ok else "REVIEW",
    }


def write_claims_emit_enhancement_validation(
    output_dir: str,
    metrics: dict[str, Any],
    audit_ts: str,
    prod_flag: str,
    report_name: str = "claims_emit_enhancement_validation.csv",
    summary_name: str = "claims_emit_enhancement_validation_summary.txt",
) -> tuple[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, report_name)
    summary_path = os.path.join(output_dir, summary_name)

    row = {
        "audit_timestamp": audit_ts,
        "production_dbf_flag": prod_flag,
        "metric": "",
        "value": "",
        "validation_status": metrics.get("validation_status", ""),
        "linkage_status": metrics.get("linkage_status", ""),
    }
    rows = []
    for key, val in metrics.items():
        if key in ("validation_status", "linkage_status"):
            continue
        rows.append({**row, "metric": key, "value": val})

    fieldnames = [
        "audit_timestamp",
        "production_dbf_flag",
        "metric",
        "value",
        "validation_status",
        "linkage_status",
    ]
    with open(report_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "QLAdmin Enterprise Claims — Emit Enhancement Validation Summary",
        "=" * 60,
        f"Audit Timestamp: {audit_ts}",
        f"production_dbf_flag={prod_flag}",
        "",
        f"CLAIMNUM normalized rows: {metrics.get('claimnum_normalized_count', 0)}",
        f"CLAIMNUM length violations (> {metrics.get('claimnum_max_length', 13)}): "
        f"{metrics.get('claimnum_over_max_length', 0)}",
        f"ISWL Disbursement/Withdrawal classified to CLAIMSTAT {metrics.get('iswl_status_98_count', 0)} "
        f"(target 98 population count)",
        f"Non-98 quikclms rows with MSEQ != 0: {metrics.get('non98_clms_mseq_not_zero', 0)}",
        f"Non-98 quikclmp rows with MSEQ != 0: {metrics.get('non98_clmp_mseq_not_zero', 0)}",
        f"Status-98 non-zero MSEQ values observed: {metrics.get('status98_nonzero_mseq_values', [])}",
        f"Orphan payments (MPOLICY+MPHASE+MSEQ): {metrics.get('orphan_payments', 0)}",
        f"Orphan claims (no matching payment key): {metrics.get('orphan_claims', 0)}",
        f"Governance metadata leaked to outputs: {metrics.get('governance_metadata_leaked', 0)}",
        f"quikclms target schema only: {metrics.get('clms_schema_ok', False)}",
        f"quikclmp target schema only: {metrics.get('clmp_schema_ok', False)}",
        "",
        f"Overall validation status: {metrics.get('validation_status', 'UNKNOWN')}",
        f"Payment linkage status: {metrics.get('linkage_status', 'UNKNOWN')}",
    ]
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return report_path, summary_path
