"""
Phase P3G — quikplan coverage completeness + blank MPLAN business review reporting.

Preserves raw source values exactly (no trim/normalize/overlay) in business-facing reports.
"""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime

import pandas as pd

from qla_core.product_catalog_authority import (
    build_authoritative_mplan_resolver,
    load_closed_product_catalog,
    load_crosswalk_authority,
    load_quikplan_plan_set,
    resolve_authoritative_mplan,
    strip_val,
)
from qla_core.quikplan_source_loader import load_quikplan_source_csv

from qla_core.non_product_row_governance import (
    EXPECTED_NON_PRODUCT_ROW,
    GOVERNANCE_FAILURE_CLASSIFICATIONS,
    classify_blank_mplan_governance,
    governance_status_for_classification,
)


def load_ppben_raw_rows(ppben_path: str) -> tuple[list[str], list[dict]]:
    """Load filtered PPBEN rows preserving exact field values (row-order aligned with quikridr)."""
    if not os.path.isfile(ppben_path):
        return [], []

    with open(ppben_path, encoding="latin1", newline="") as fh:
        lines = fh.readlines()

    if len(lines) < 3:
        return [], []

    header = list(csv.reader([lines[0].rstrip("\r\n")]))[0]
    rows: list[dict] = []

    for line_idx, raw_line in enumerate(lines[2:], start=3):
        stripped = raw_line.rstrip("\r\n")
        if not stripped or stripped.startswith("---"):
            continue
        fields = list(csv.reader([stripped]))[0]
        if len(fields) < len(header):
            fields = fields + [""] * (len(header) - len(fields))
        row_dict = {header[i]: fields[i] for i in range(len(header))}
        pol = row_dict.get("POLICY_NUMBER", "")
        if "---" in pol:
            continue
        seq = row_dict.get("BENEFIT_SEQ", "").strip().replace(".0", "")
        if not seq.isdigit() or int(seq) < 1:
            continue
        rows.append({
            "source_row_number": line_idx,
            "raw_fields": row_dict,
            "raw_line": stripped,
        })

    return header, rows


def _raw_field(raw_fields: dict, *names: str) -> str:
    for name in names:
        if name in raw_fields:
            return raw_fields[name]
        for key, val in raw_fields.items():
            if key.strip().upper() == name.strip().upper():
                return val
    return ""


def classify_blank_mplan_p3g(
    *,
    mphase: str,
    raw_plan_code: str,
    raw_benefit_type: str,
    exists_in_catalog: bool,
    exists_in_quikplan: bool,
    parser_dropped: bool,
    allow_legacy: bool,
    resolution_path: str,
) -> tuple[str, str, str]:
    """Classify blank MPLAN row via shared non-product governance rule."""
    return classify_blank_mplan_governance(
        benefit_seq=mphase,
        source_plan_code=raw_plan_code,
        source_benefit_type=raw_benefit_type,
        exists_in_catalog=exists_in_catalog,
        exists_in_quikplan=exists_in_quikplan,
        parser_dropped=parser_dropped,
        allow_legacy=allow_legacy,
        resolution_path=resolution_path,
    )


def build_quikplan_missing_catalog_emit_inventory(
    catalog_df: pd.DataFrame,
    source_df: pd.DataFrame,
    quikplan_df: pd.DataFrame,
    ingestion_trace: list[dict],
) -> pd.DataFrame:
    """Catalog products in source that failed quikplan emission."""
    emitted_plans = set()
    if not quikplan_df.empty and "PLAN" in quikplan_df.columns:
        emitted_plans = set(quikplan_df["PLAN"].tolist())

    source_ids: dict[str, int] = {}
    if not source_df.empty and "COVERAGE_ID" in source_df.columns:
        for cid in source_df["COVERAGE_ID"].tolist():
            source_ids[cid] = source_ids.get(cid, 0) + 1

    parser_skipped: dict[str, list[dict]] = {}
    for row in ingestion_trace:
        cid = row.get("parsed_coverage_id", "")
        if row.get("skip_reason", "").startswith("COMMA_OVERFLOW") and row.get("row_classification") == "DATA":
            parser_skipped.setdefault(cid, []).append(row)

    rows = []
    id_col = "lifepro_coverage_id"
    auth_col = "crosswalk_ql_plan_code"
    for _, cat in catalog_df.iterrows():
        cid = cat.get(id_col, "")
        auth = cat.get(auth_col, "")
        if not cid or not auth:
            continue
        seen = cid in source_ids or cid.strip() in {k.strip() for k in source_ids}
        count = source_ids.get(cid, 0)
        if not count:
            for k, v in source_ids.items():
                if k.strip() == cid.strip():
                    count = v
                    break
        emitted = auth in emitted_plans
        if seen and not emitted:
            failure_stage = "QUIKPLAN_EMIT"
            failure_reason = "Authoritative PLAN not in quikplan.csv"
            if any(cid.strip() == k.strip() for k in parser_skipped):
                failure_stage = "SOURCE_PARSER"
                failure_reason = "Row recovered by P3G comma-overflow merge; re-run emit"
            rows.append({
                "source_coverage_id": cid,
                "authoritative_plan": auth,
                "source_row_count": count,
                "was_seen_in_source": "Y" if seen else "N",
                "was_emitted_to_quikplan": "Y" if emitted else "N",
                "failure_stage": failure_stage,
                "failure_reason": failure_reason,
                "parser_section": "DESCRIPTION_COMMA_OVERFLOW",
                "separator_context": "",
                "recommended_fix": "Ensure load_quikplan_source_csv used; re-run product setup",
            })

    return pd.DataFrame(rows)


def build_blank_mplan_business_review_report(
    quikridr_df: pd.DataFrame,
    ppben_rows: list[dict],
    resolver,
    quikplan_plan_set: set[str],
    catalog_plan_set: set[str],
    catalog_coverage_ids: set[str],
    parser_dropped_coverage_ids: set[str],
    *,
    allow_legacy: bool,
    master_cw_map: dict[str, str],
) -> pd.DataFrame:
    """Business-reviewable blank MPLAN report with exact source values."""
    rows = []
    if "MPLAN" not in quikridr_df.columns:
        return pd.DataFrame()

    for i, qr in quikridr_df.iterrows():
        mplan = qr.get("MPLAN", "")
        if mplan != "":
            continue

        mpolicy = qr.get("MPOLICY", "")
        mphase = qr.get("MPHASE", "")
        ppben = ppben_rows[i] if i < len(ppben_rows) else {}
        raw_fields = ppben.get("raw_fields", {})
        source_row_number = ppben.get("source_row_number", i + 2)
        raw_plan = _raw_field(raw_fields, "PLAN_CODE")
        raw_benefit_type = _raw_field(raw_fields, "BENEFIT_TYPE")

        candidate = master_cw_map.get(raw_plan.strip(), raw_plan.strip()) if raw_plan.strip() else ""
        resolution = resolve_authoritative_mplan(
            raw_plan.strip(), candidate, resolver, allow_legacy=allow_legacy,
        )

        cid_exact = raw_plan  # PPBEN PLAN_CODE is source plan key for MPLAN path
        exists_catalog = (
            cid_exact in catalog_coverage_ids
            or cid_exact.strip() in {c.strip() for c in catalog_coverage_ids}
            or strip_val(resolution.resolved_mplan) in catalog_plan_set
        )
        exists_qp = strip_val(resolution.resolved_mplan) in quikplan_plan_set
        parser_dropped = (
            cid_exact.strip() in {c.strip() for c in parser_dropped_coverage_ids}
            or cid_exact in parser_dropped_coverage_ids
        )

        classification, blank_reason, recommended = classify_blank_mplan_p3g(
            mphase=mphase,
            raw_plan_code=raw_plan,
            raw_benefit_type=raw_benefit_type,
            exists_in_catalog=exists_catalog,
            exists_in_quikplan=exists_qp,
            parser_dropped=parser_dropped,
            allow_legacy=allow_legacy,
            resolution_path=resolution.resolution_path,
        )

        if classification in GOVERNANCE_FAILURE_CLASSIFICATIONS:
            governance_status = "GOVERNANCE_FAILURE"
        elif classification == EXPECTED_NON_PRODUCT_ROW:
            governance_status = "CLASSIFIED_OK"
        elif classification == "ROLLBACK_FALLBACK_ONLY":
            governance_status = "LEGACY_MODE"
        else:
            governance_status = governance_status_for_classification(classification, allow_legacy=allow_legacy)
            if governance_status == "REVIEW":
                governance_status = "CLASSIFIED_OK"

        authority_status = "AUTHORIZED" if resolution.is_authoritative and resolution.resolved_mplan else "UNAUTHORIZED"

        rows.append({
            "source_file": "PPBEN.csv",
            "source_row_number": source_row_number,
            "mpolicy": mpolicy,
            "mphase": mphase,
            "benefit_seq": mphase,
            "raw_source_plan_code": raw_plan,
            "raw_source_coverage_id": raw_plan,
            "raw_source_form": _raw_field(raw_fields, "POL_LINE_OF_BUSNSS", "PRODUCT_TYPE"),
            "raw_source_description": "",
            "raw_source_benefit_type": raw_benefit_type,
            "raw_source_rider_code": _raw_field(raw_fields, "INF_RIDER_SEQ"),
            "raw_source_product_code": _raw_field(raw_fields, "PRODUCT_TYPE"),
            "raw_source_columns_json": json.dumps(raw_fields, ensure_ascii=False),
            "candidate_mplan": candidate,
            "resolved_mplan": resolution.resolved_mplan,
            "blank_reason": blank_reason,
            "classification": classification,
            "authority_status": authority_status,
            "exists_in_catalog": "Y" if exists_catalog else "N",
            "exists_in_quikplan": "Y" if exists_qp else "N",
            "governance_status": governance_status,
            "recommended_action": recommended,
        })

    return pd.DataFrame(rows)


def write_p3g_completeness_summary(
    output_path: str,
    *,
    source_coverage_count: int,
    emitted_quikplan_plans: int,
    authoritative_catalog_size: int,
    missing_catalog_emits: int,
    blank_mplan_count: int,
    expected_non_product_blanks: int,
    unresolved_product_rows: int,
    governance_errors: int,
    parser_skips_recovered: int,
    before_emitted_plans: int,
    after_emitted_plans: int,
) -> dict:
    summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "phase": "P3G",
        "source_coverage_ids": source_coverage_count,
        "emitted_quikplan_plans": emitted_quikplan_plans,
        "authoritative_catalog_size": authoritative_catalog_size,
        "missing_catalog_emits": missing_catalog_emits,
        "blank_mplan_count": blank_mplan_count,
        "expected_non_product_blank_rows": expected_non_product_blanks,
        "unresolved_product_rows": unresolved_product_rows,
        "governance_errors": governance_errors,
        "parser_skips_recovered": parser_skips_recovered,
        "before_emitted_quikplan_plans": before_emitted_plans,
        "after_emitted_quikplan_plans": after_emitted_plans,
        "completeness_delta": after_emitted_plans - before_emitted_plans,
    }
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    return summary
