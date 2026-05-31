"""quikridr MPLAN authority alignment — governance, trace, blank classification (Phase P3E)."""

from __future__ import annotations

import json
import os
from datetime import datetime

import pandas as pd

from qla_core.non_product_row_governance import (
    EXPECTED_NON_PRODUCT_ROW,
    classify_blank_mplan_governance,
    governance_status_for_classification,
    row_has_product_premium_indicators,
)
from qla_core.product_catalog_authority import (
    plan_contains_space,
    resolve_authoritative_mplan,
    strip_val,
)

TRACE_COLUMNS = [
    "source_file", "source_row_number", "mpolicy", "mphase", "source_plan_code",
    "candidate_mplan", "resolved_mplan", "is_authoritative", "exists_in_quikplan",
    "contains_spaces", "is_blank", "resolution_path", "fallback_value",
    "governance_status", "error_category", "remediation_hint", "blank_classification",
]


def classify_blank_mplan(
    source_plan_code: str,
    mphase: str,
    row_data: dict,
    *,
    source_benefit_type: str = "",
) -> str:
    """Classify blank MPLAN rows — only true product failures fail governance."""
    classification, _, _ = classify_blank_mplan_governance(
        benefit_seq=mphase,
        source_plan_code=source_plan_code,
        source_benefit_type=source_benefit_type,
        has_product_premium_indicators=row_has_product_premium_indicators(row_data),
    )
    return classification


def resolution_to_trace_row(
    resolution,
    *,
    source_file: str,
    source_row_number: int,
    mpolicy: str,
    mphase: str,
    row_data: dict,
    quikplan_plan_set: set[str],
    allow_legacy: bool,
    source_benefit_type: str = "",
) -> dict:
    """Convert MplanResolution to governance trace row."""
    resolved = strip_val(resolution.resolved_mplan)
    is_blank = resolved == ""
    blank_class = ""
    if is_blank:
        blank_class = classify_blank_mplan(
            resolution.source_plan_code, mphase, row_data,
            source_benefit_type=source_benefit_type,
        )

    exists_in_qp = "Y" if resolved and resolved in quikplan_plan_set else "N"
    contains_spaces = "Y" if plan_contains_space(resolved or resolution.fallback_value) else "N"

    if allow_legacy and resolution.resolution_path == "LEGACY_FALLBACK":
        governance_status = "LEGACY_FALLBACK_REPORTED"
    elif is_blank and blank_class == EXPECTED_NON_PRODUCT_ROW:
        governance_status = "BLANK_ALLOWED"
    elif is_blank and blank_class == "UNRESOLVED_PRODUCT":
        governance_status = "GOVERNANCE_ERROR"
    elif is_blank:
        governance_status = governance_status_for_classification(blank_class, allow_legacy=allow_legacy)
        if governance_status == "REVIEW":
            governance_status = "BLANK_ALLOWED"
    elif resolution.is_authoritative and resolved:
        governance_status = "AUTHORIZED"
    else:
        governance_status = "GOVERNANCE_ERROR"

    return {
        "source_file": source_file,
        "source_row_number": source_row_number,
        "mpolicy": strip_val(mpolicy),
        "mphase": strip_val(mphase) or "1",
        "source_plan_code": strip_val(resolution.source_plan_code),
        "candidate_mplan": strip_val(resolution.candidate_mplan),
        "resolved_mplan": resolved,
        "is_authoritative": "Y" if resolution.is_authoritative and resolved else "N",
        "exists_in_quikplan": exists_in_qp,
        "contains_spaces": contains_spaces,
        "is_blank": "Y" if is_blank else "N",
        "resolution_path": resolution.resolution_path,
        "fallback_value": strip_val(resolution.fallback_value),
        "governance_status": governance_status,
        "error_category": resolution.error_category or (blank_class if is_blank else ""),
        "remediation_hint": resolution.remediation_hint or (
            "Blank MPLAN allowed for non-product row" if governance_status == "BLANK_ALLOWED" else ""
        ),
        "blank_classification": blank_class,
    }


def build_governance_manifests(trace_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Derive orphan, blank, passthrough, and error manifests from trace."""
    if trace_df.empty:
        empty = pd.DataFrame()
        return empty, empty, empty, empty

    orphan = trace_df[
        (trace_df["governance_status"] == "GOVERNANCE_ERROR")
        & (trace_df["is_blank"] == "N")
        & (trace_df["resolved_mplan"].map(strip_val) != "")
    ].copy()

    unauthorized = trace_df[
        (trace_df["governance_status"] == "GOVERNANCE_ERROR")
        & (trace_df["is_blank"] == "N")
    ].copy()

    blank_df = trace_df[trace_df["is_blank"] == "Y"].copy()

    passthrough = trace_df[
        (trace_df["fallback_value"].map(strip_val) != "")
        & (trace_df["fallback_value"].map(strip_val) != trace_df["resolved_mplan"].map(strip_val))
        & (trace_df["contains_spaces"] == "Y")
    ].copy()

    return orphan, unauthorized, blank_df, passthrough


def apply_mplan_emit_filter(
    output_rows: list[list],
    schema: list[str],
    trace_df: pd.DataFrame,
    quarantine: bool = False,
) -> tuple[list[list], pd.DataFrame]:
    """Filter quikridr output rows — exclude governance errors when quarantine enabled."""
    if trace_df.empty or not quarantine:
        return output_rows, pd.DataFrame()

    keep_indices = []
    hold_rows = []
    for i, row in trace_df.iterrows():
        status = strip_val(row.get("governance_status", ""))
        if status in ("AUTHORIZED", "BLANK_ALLOWED", "LEGACY_FALLBACK_REPORTED"):
            keep_indices.append(i)
        else:
            if i < len(output_rows):
                hold = {schema[j]: output_rows[i][j] for j in range(len(schema))}
                hold["hold_reason"] = status
                hold["fallback_value"] = strip_val(row.get("fallback_value", ""))
                hold_rows.append(hold)

    filtered = [output_rows[i] for i in keep_indices if i < len(output_rows)]
    return filtered, pd.DataFrame(hold_rows)


def write_p3e_governance_outputs(
    output_dir: str,
    trace_df: pd.DataFrame,
    *,
    closed_enabled: bool,
    allow_legacy: bool,
    emitted_rows: int,
    validation_passed: bool,
) -> dict:
    """Write all Phase P3E governance artifacts."""
    os.makedirs(output_dir, exist_ok=True)

    orphan_df, error_df, blank_df, passthrough_df = build_governance_manifests(trace_df)

    trace_df.to_csv(os.path.join(output_dir, "mplan_resolution_trace.csv"), index=False)
    trace_df.to_csv(os.path.join(output_dir, "mplan_authority_validation_report.csv"), index=False)

    if orphan_df.empty:
        pd.DataFrame(columns=TRACE_COLUMNS).to_csv(os.path.join(output_dir, "orphan_mplan_inventory.csv"), index=False)
    else:
        orphan_df.to_csv(os.path.join(output_dir, "orphan_mplan_inventory.csv"), index=False)

    blank_df.to_csv(os.path.join(output_dir, "blank_mplan_classification.csv"), index=False)

    if passthrough_df.empty:
        pd.DataFrame(columns=TRACE_COLUMNS).to_csv(
            os.path.join(output_dir, "legacy_mplan_passthrough_inventory.csv"), index=False,
        )
    else:
        passthrough_df.to_csv(os.path.join(output_dir, "legacy_mplan_passthrough_inventory.csv"), index=False)

    error_df.to_csv(os.path.join(output_dir, "governance_error_manifest.csv"), index=False)

    orphan_count = 0
    blank_count = 0
    unresolved_blank = 0
    expected_non_product = 0
    if not trace_df.empty:
        orphan_count = int(((trace_df["governance_status"] == "GOVERNANCE_ERROR") & (trace_df["is_blank"] == "N")).sum())
        blank_count = int((trace_df["is_blank"] == "Y").sum())
        if "blank_classification" in trace_df.columns:
            unresolved_blank = int((trace_df["blank_classification"] == "UNRESOLVED_PRODUCT").sum())
            expected_non_product = int((trace_df["blank_classification"] == EXPECTED_NON_PRODUCT_ROW).sum())

    summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "closed_mplan_authority": "ENABLED" if closed_enabled else "DISABLED",
        "legacy_fallback_mode": "ENABLED" if allow_legacy else "DISABLED",
        "emitted_rows": emitted_rows,
        "trace_rows": len(trace_df),
        "orphan_mplan_count": orphan_count,
        "blank_mplan_count": blank_count,
        "unresolved_blank_count": unresolved_blank,
        "expected_non_product_blank_count": expected_non_product,
        "non_product_governance_rule": "plan_governance/non_product_row_governance_rule.md",
        "legacy_passthrough_count": len(passthrough_df),
        "validation_passed": validation_passed,
    }
    with open(os.path.join(output_dir, "p3e_alignment_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    write_executive_summary(output_dir, summary)

    return summary


def write_executive_summary(output_dir: str, summary: dict) -> None:
    """Write executive_p3e_mplan_alignment_summary.md."""
    lines = [
        "# Executive Summary — Phase P3E quikridr MPLAN Authority Alignment",
        "",
        f"Generated: {summary.get('generated_at', '')}",
        "",
        "## Result",
        "",
        f"- Closed MPLAN authority: **{summary.get('closed_mplan_authority', 'N/A')}**",
        f"- Legacy fallback: **{summary.get('legacy_fallback_mode', 'N/A')}**",
        f"- Emitted rows: **{summary.get('emitted_rows', 0)}**",
        f"- Validation passed: **{summary.get('validation_passed', False)}**",
        "",
        "## Metrics",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Trace rows | {summary.get('trace_rows', 0)} |",
        f"| Governance errors (non-blank) | {summary.get('orphan_mplan_count', 0)} |",
        f"| Blank MPLAN rows | {summary.get('blank_mplan_count', 0)} |",
        f"| Unresolved blank (UNRESOLVED_PRODUCT) | {summary.get('unresolved_blank_count', 0)} |",
        f"| Expected non-product blank (BENEFIT_SEQ 99 / UV) | {summary.get('expected_non_product_blank_count', 0)} |",
        f"| Legacy passthrough inventory | {summary.get('legacy_passthrough_count', 0)} |",
        "",
        "## Rollback",
        "",
        "Set `QLA_ALLOW_LEGACY_MPLAN_FALLBACK=1` to report but allow legacy passthrough emit.",
        "",
    ]
    with open(os.path.join(output_dir, "executive_p3e_mplan_alignment_summary.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def write_p3f_governance_outputs(
    output_dir: str,
    trace_df: pd.DataFrame,
    *,
    closed_enabled: bool,
    allow_legacy: bool,
    emitted_rows: int,
    validation_passed: bool,
    pactg_stats: dict | None = None,
) -> dict:
    """Write all Phase P3F quikactg MPLAN authority artifacts."""
    os.makedirs(output_dir, exist_ok=True)

    orphan_df, error_df, blank_df, passthrough_df = build_governance_manifests(trace_df)

    trace_df.to_csv(os.path.join(output_dir, "quikactg_mplan_resolution_trace.csv"), index=False)
    trace_df.to_csv(os.path.join(output_dir, "quikactg_mplan_authority_validation_report.csv"), index=False)
    orphan_df.to_csv(os.path.join(output_dir, "quikactg_orphan_mplan_inventory.csv"), index=False)
    blank_df.to_csv(os.path.join(output_dir, "quikactg_blank_mplan_classification.csv"), index=False)
    passthrough_df.to_csv(os.path.join(output_dir, "quikactg_legacy_mplan_passthrough_inventory.csv"), index=False)
    error_df.to_csv(os.path.join(output_dir, "quikactg_governance_error_manifest.csv"), index=False)

    orphan_count = 0
    blank_count = 0
    if not trace_df.empty:
        orphan_count = int(((trace_df["governance_status"] == "GOVERNANCE_ERROR") & (trace_df["is_blank"] == "N")).sum())
        blank_count = int((trace_df["is_blank"] == "Y").sum())

    summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "phase": "P3F",
        "component": "quikactg",
        "closed_mplan_authority": "ENABLED" if closed_enabled else "DISABLED",
        "legacy_fallback_mode": "ENABLED" if allow_legacy else "DISABLED",
        "emitted_rows": emitted_rows,
        "trace_rows": len(trace_df),
        "orphan_mplan_count": orphan_count,
        "blank_mplan_count": blank_count,
        "legacy_passthrough_count": len(passthrough_df),
        "validation_passed": validation_passed,
        "pactg_stats": pactg_stats or {},
    }
    with open(os.path.join(output_dir, "p3f_alignment_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    write_p3f_executive_summary(output_dir, summary)
    write_quikactg_authority_inventory(output_dir, summary)

    return summary


def write_p3f_executive_summary(output_dir: str, summary: dict) -> None:
    """Write executive_p3f_quikactg_alignment_summary.md."""
    pactg = summary.get("pactg_stats") or {}
    lines = [
        "# Executive Summary — Phase P3F quikactg MPLAN Authority Alignment",
        "",
        f"Generated: {summary.get('generated_at', '')}",
        "",
        "## Result",
        "",
        f"- Closed MPLAN authority: **{summary.get('closed_mplan_authority', 'N/A')}**",
        f"- Legacy fallback: **{summary.get('legacy_fallback_mode', 'N/A')}**",
        f"- Emitted plan rows: **{summary.get('emitted_rows', 0)}**",
        f"- Validation passed: **{summary.get('validation_passed', False)}**",
        "",
        "## PACTG ingestion",
        "",
        f"- PACTG rows read: **{pactg.get('pactg_rows_read', 'N/A')}**",
        f"- Distinct valid PLAN_CODE values: **{pactg.get('distinct_plans', 'N/A')}**",
        "",
        "## Metrics",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Trace rows | {summary.get('trace_rows', 0)} |",
        f"| Governance errors (non-blank) | {summary.get('orphan_mplan_count', 0)} |",
        f"| Blank MPLAN rows | {summary.get('blank_mplan_count', 0)} |",
        f"| Legacy passthrough inventory | {summary.get('legacy_passthrough_count', 0)} |",
        "",
    ]
    with open(os.path.join(output_dir, "executive_p3f_quikactg_alignment_summary.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def write_quikactg_authority_inventory(output_dir: str, summary: dict) -> None:
    """Record quikactg MPLAN authority implementation status."""
    rows = [{
        "component": "quikactg",
        "field": "MPLAN",
        "source": "PACTG.PLAN_CODE",
        "rulebook": "Sync_Rulebook_quikactg.csv",
        "current_authority": "Closed catalog resolver (P3E pattern)",
        "p3f_status": "IMPLEMENTED",
        "validation_passed": summary.get("validation_passed", False),
        "emitted_rows": summary.get("emitted_rows", 0),
        "notes": "Plan-level accounting setup; one row per distinct PLAN_CODE",
    }]
    pd.DataFrame(rows).to_csv(os.path.join(output_dir, "quikactg_authority_inventory.csv"), index=False)


def validate_emitted_mplan(
    emitted_df: pd.DataFrame,
    quikplan_plan_set: set[str],
) -> tuple[bool, dict]:
    """Final validation of emitted MPLAN values (quikridr or quikactg)."""
    if "MPLAN" not in emitted_df.columns:
        return False, {"error": "MPLAN column missing"}

    plans = [strip_val(p) for p in emitted_df["MPLAN"]]
    non_blank = [p for p in plans if p]
    outside = [p for p in non_blank if p not in quikplan_plan_set]
    spaced = [p for p in non_blank if plan_contains_space(p)]

    return (
        len(outside) == 0 and len(spaced) == 0,
        {
            "emitted_rows": len(emitted_df),
            "non_blank_mplan": len(non_blank),
            "outside_quikplan": len(outside),
            "with_spaces": len(spaced),
            "unique_outside": sorted(set(outside))[:20],
        },
    )


def validate_emitted_quikridr(
    quikridr_df: pd.DataFrame,
    quikplan_plan_set: set[str],
) -> tuple[bool, dict]:
    """Final validation of emitted quikridr MPLAN values."""
    return validate_emitted_mplan(quikridr_df, quikplan_plan_set)
