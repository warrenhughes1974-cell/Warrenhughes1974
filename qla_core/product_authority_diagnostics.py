"""Product authority layer diagnostics, strict UAT validation (P3B), closed catalog (P3C)."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime

import pandas as pd

from qla_core.crosswalk_enrichment import CrosswalkOverlayConfig, load_policy_form_crosswalk
from qla_core.quikplan_converter import iter_quikplan_source_rows
from qla_core.normalize_utils import normalize
from qla_core.product_catalog_authority import (
    ClosedProductCatalog,
    CrosswalkAuthority,
    load_closed_product_catalog,
    load_crosswalk_authority,
    load_product_catalog_crosswalk,
    plan_contains_space,
)

AUTHORITY_POLICY_FORM = "POLICY_FORM_CROSSWALK"
AUTHORITY_PRODUCT_CATALOG = "PRODUCT_CATALOG_CROSSWALK"
AUTHORITY_MASTER_LEGACY = "MASTER_CROSSWALK_LEGACY_FALLBACK"
AUTHORITY_RAW_PASSTHROUGH = "RAW_COVERAGE_ID_PASSTHROUGH"
AUTHORITY_RULEBOOK = "RULEBOOK_DEFAULT"

PASSTHROUGH_RE = re.compile(r"\s")


def strip_val(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def strict_product_authority_enabled() -> bool:
    return os.environ.get("QLA_STRICT_PRODUCT_AUTHORITY", "0").strip().lower() in ("1", "true", "yes")


def product_authority_quarantine_enabled() -> bool:
    return os.environ.get("QLA_PRODUCT_AUTHORITY_QUARANTINE", "0").strip().lower() in ("1", "true", "yes")


def allow_legacy_product_fallback() -> bool:
    return os.environ.get("QLA_ALLOW_LEGACY_PRODUCT_FALLBACK", "0").strip().lower() in ("1", "true", "yes")


def closed_product_authority_enabled(uat_overlay: bool = False, explicit: bool | None = None) -> bool:
    """Closed catalog ON by default for UAT overlay unless explicitly disabled."""
    if allow_legacy_product_fallback():
        return False
    env = os.environ.get("QLA_CLOSED_PRODUCT_AUTHORITY", "").strip().lower()
    if env in ("0", "false", "no"):
        return False
    if env in ("1", "true", "yes"):
        return True
    if explicit is not None:
        return explicit
    return uat_overlay


def load_authorized_plan_codes(crosswalk_path: str) -> set[str]:
    """Authorized PLAN codes from Policy Form Crosswalk QL Plan Code column."""
    xwalk = load_policy_form_crosswalk(crosswalk_path)
    return {
        normalize(entry.get("ql_plan_code", ""))
        for entry in xwalk.values()
        if strip_val(entry.get("ql_plan_code", ""))
    }


def is_passthrough_plan(plan: str, coverage_id: str) -> bool:
    plan = strip_val(plan)
    cid = strip_val(coverage_id)
    if not plan:
        return False
    if plan == cid:
        return True
    return bool(PASSTHROUGH_RE.search(plan)) and not re.match(r"^[A-Z0-9]{4,12}$", plan)


def resolve_pre_overlay_plan(coverage_id: str, authority: CrosswalkAuthority) -> tuple[str, str, str]:
    """Return (plan, authority_layer, fallback_layer) before Policy Form overlay."""
    cid = normalize(coverage_id)
    catalog_map = load_product_catalog_crosswalk()
    legacy_map = authority.legacy_product_map

    if cid in catalog_map:
        plan = catalog_map[cid]
        if cid in legacy_map and legacy_map[cid] != plan:
            return plan, AUTHORITY_PRODUCT_CATALOG, AUTHORITY_MASTER_LEGACY
        if cid not in legacy_map:
            return plan, AUTHORITY_PRODUCT_CATALOG, ""
        return plan, AUTHORITY_PRODUCT_CATALOG, ""

    if cid in legacy_map:
        return legacy_map[cid], AUTHORITY_MASTER_LEGACY, ""

    if cid:
        return cid, AUTHORITY_RAW_PASSTHROUGH, ""

    return "", AUTHORITY_RULEBOOK, ""


def trace_row_authority(
    coverage_id: str,
    emitted_row: dict,
    authority: CrosswalkAuthority,
    overlay_config: CrosswalkOverlayConfig | None,
    authorized_plans: set[str],
    policy_form_map: dict | None = None,
) -> dict:
    """Trace authority layers for one quikplan row."""
    cid = strip_val(coverage_id)
    emitted_plan = strip_val(emitted_row.get("PLAN", ""))
    pre_plan, pre_layer, fallback_layer = resolve_pre_overlay_plan(cid, authority)

    overlay_applied = False
    crosswalk_plan = ""
    if policy_form_map:
        crosswalk_plan = strip_val(policy_form_map.get(normalize(cid), {}).get("ql_plan_code", ""))
    elif overlay_config and overlay_config.crosswalk_map:
        crosswalk_plan = strip_val(overlay_config.crosswalk_map.get(normalize(cid), {}).get("ql_plan_code", ""))

    if overlay_config and overlay_config.enabled and overlay_config.crosswalk_map and crosswalk_plan:
        overlay_applied = True

    if overlay_applied and emitted_plan == crosswalk_plan:
        authority_layer = AUTHORITY_POLICY_FORM
        used_product_catalog = "N"
        used_master_fallback = "N"
        raw_passthrough = "N"
    elif overlay_applied and emitted_plan != crosswalk_plan:
        authority_layer = pre_layer
        used_product_catalog = "Y" if pre_layer == AUTHORITY_PRODUCT_CATALOG else "N"
        used_master_fallback = "Y" if pre_layer == AUTHORITY_MASTER_LEGACY else "N"
        raw_passthrough = "Y" if pre_layer == AUTHORITY_RAW_PASSTHROUGH else "N"
    else:
        authority_layer = pre_layer
        used_product_catalog = "Y" if pre_layer == AUTHORITY_PRODUCT_CATALOG else "N"
        used_master_fallback = "Y" if pre_layer == AUTHORITY_MASTER_LEGACY else "N"
        raw_passthrough = "Y" if pre_layer == AUTHORITY_RAW_PASSTHROUGH else "N"

    if authority_layer == AUTHORITY_RULEBOOK and emitted_plan and emitted_plan != cid:
        authority_layer = AUTHORITY_RULEBOOK

    authorized = emitted_plan in authorized_plans if emitted_plan else False
    crosswalk_has_plan = bool(crosswalk_plan)

    if not authorized:
        if not overlay_config or not overlay_config.enabled:
            if crosswalk_plan:
                remediation = (
                    f"Enable UAT overlay (--uat-overlay) — Policy Form Crosswalk maps "
                    f"{cid} -> {crosswalk_plan}"
                )
            else:
                remediation = "Enable UAT overlay (--uat-overlay) to apply Policy Form Crosswalk authority"
        elif not crosswalk_has_plan:
            remediation = "Add Policy Form Crosswalk row with QL Plan Code for this Coverage_ID"
        elif overlay_applied and emitted_plan != crosswalk_plan:
            remediation = "Investigate overlay application — emitted PLAN differs from crosswalk authority"
        elif is_passthrough_plan(pre_plan, cid):
            remediation = "Replace product_catalog passthrough emit with crosswalk QL Plan Code via UAT overlay"
        else:
            remediation = "Review product_catalog_crosswalk and Policy Form Crosswalk alignment"
    else:
        remediation = "NONE — authorized by Policy Form Crosswalk"

    rulebook_lineage = "Sync_Rulebook_quikplan.csv"
    if used_product_catalog == "Y":
        rulebook_lineage += " -> product_catalog_crosswalk.csv"
    if used_master_fallback == "Y":
        rulebook_lineage += " -> Master_Crosswalk legacy product fallback"
    if overlay_applied:
        rulebook_lineage += " -> Policy Form Crosswalk overlay"

    return {
        "emitted_plan": emitted_plan,
        "source_coverage_id": cid,
        "source_row_identifier": cid,
        "form": strip_val(emitted_row.get("FORM", "")),
        "descr": strip_val(emitted_row.get("DESCR", "")),
        "planname": strip_val(emitted_row.get("PLANNAME", "")),
        "authority_layer_used": authority_layer,
        "fallback_layer_used": fallback_layer,
        "pre_overlay_plan": pre_plan,
        "crosswalk_ql_plan_code": crosswalk_plan,
        "product_catalog_crosswalk_used": used_product_catalog,
        "master_crosswalk_fallback_used": used_master_fallback,
        "raw_passthrough_occurred": raw_passthrough,
        "overlay_applied": "Y" if overlay_applied else "N",
        "uat_overlay_enabled": "Y" if overlay_config and overlay_config.enabled else "N",
        "authorized_by_policy_form_crosswalk": "Y" if authorized else "N",
        "rulebook_lineage": rulebook_lineage,
        "recommended_remediation": remediation,
        "business_review_status": "PENDING" if not authorized else "AUTHORIZED",
    }


def build_authority_layer_diagnostics(
    source_df: pd.DataFrame,
    staged_df: pd.DataFrame,
    authority: CrosswalkAuthority,
    overlay_config: CrosswalkOverlayConfig | None,
    crosswalk_path: str,
) -> pd.DataFrame:
    """Per-row authority layer diagnostics for staged quikplan output."""
    authorized = load_authorized_plan_codes(crosswalk_path)
    policy_form_map = load_policy_form_crosswalk(crosswalk_path)
    rows: list[dict] = []
    source_rows = list(iter_quikplan_source_rows(source_df))
    n = min(len(source_rows), len(staged_df))
    for i in range(n):
        cid = strip_val(source_rows[i].get("COVERAGE_ID", ""))
        emitted = {col: strip_val(staged_df.iloc[i].get(col, "")) for col in staged_df.columns}
        trace = trace_row_authority(
            cid, emitted, authority, overlay_config, authorized, policy_form_map=policy_form_map,
        )
        rows.append(trace)
    return pd.DataFrame(rows)


def build_unauthorized_plan_manifest(
    diagnostics_df: pd.DataFrame,
    overlay_label: str = "",
) -> pd.DataFrame:
    """Filter diagnostics to unauthorized PLAN emissions only."""
    if diagnostics_df.empty:
        return pd.DataFrame(columns=[
            "emitted_plan", "source_coverage_id", "source_row_identifier", "form", "descr", "planname",
            "authority_layer_used", "fallback_layer_used", "product_catalog_crosswalk_used",
            "master_crosswalk_fallback_used", "raw_passthrough_occurred", "rulebook_lineage",
            "recommended_remediation", "business_review_status", "overlay_context",
        ])
    unauthorized = diagnostics_df[diagnostics_df["authorized_by_policy_form_crosswalk"] == "N"].copy()
    unauthorized["overlay_context"] = overlay_label
    return unauthorized


def run_strict_authority_validation(
    staged_df: pd.DataFrame,
    source_df: pd.DataFrame,
    crosswalk_path: str,
    overlay_config: CrosswalkOverlayConfig | None,
    authority: CrosswalkAuthority | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    """
    Strict UAT product authority validation.

    Returns (unauthorized_manifest, layer_diagnostics, error_count).
    Only enforces when UAT overlay is enabled.
    """
    if authority is None:
        authority = load_crosswalk_authority(
            os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "Master_Crosswalk.csv")),
        )

    if not overlay_config or not overlay_config.enabled:
        empty = pd.DataFrame()
        return empty, empty, 0

    diagnostics = build_authority_layer_diagnostics(
        source_df, staged_df, authority, overlay_config, crosswalk_path,
    )
    manifest = build_unauthorized_plan_manifest(diagnostics, overlay_label="UAT_OVERLAY")
    error_count = len(manifest)
    return manifest, diagnostics, error_count


def apply_quarantine_filter(
    staged_df: pd.DataFrame,
    source_df: pd.DataFrame,
    unauthorized_manifest: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Hold unauthorized PLAN rows; return (authorized_emit_df, hold_manifest)."""
    if unauthorized_manifest.empty:
        return staged_df.copy(), pd.DataFrame()

    bad_cids = set(unauthorized_manifest["source_coverage_id"].map(strip_val))
    hold_rows: list[dict] = []
    keep_indices: list[int] = []

    source_rows = list(iter_quikplan_source_rows(source_df))
    n = min(len(source_rows), len(staged_df))
    for i in range(n):
        cid = strip_val(source_rows[i].get("COVERAGE_ID", ""))
        if cid in bad_cids:
            hold = {col: strip_val(staged_df.iloc[i].get(col, "")) for col in staged_df.columns}
            hold["source_coverage_id"] = cid
            hold["hold_reason"] = "UNAUTHORIZED_PLAN_STRICT_AUTHORITY"
            hold_rows.append(hold)
        else:
            keep_indices.append(i)

    emit_df = staged_df.iloc[keep_indices].reset_index(drop=True) if keep_indices else staged_df.iloc[0:0]
    hold_df = pd.DataFrame(hold_rows)
    return emit_df, hold_df


RESOLUTION_OVERLAY = "POLICY_FORM_CROSSWALK_OVERLAY"
RESOLUTION_CATALOG = "PRODUCT_CATALOG_AUTHORITATIVE"
RESOLUTION_LEGACY = "MASTER_CROSSWALK_LEGACY_FALLBACK"
RESOLUTION_PASSTHROUGH = "RAW_COVERAGE_ID_PASSTHROUGH"
RESOLUTION_RULEBOOK = "RULEBOOK_DEFAULT"


def _resolve_attempted_authority_path(
    coverage_id: str,
    attempted_plan: str,
    authority: CrosswalkAuthority,
    overlay_config: CrosswalkOverlayConfig | None,
    catalog: ClosedProductCatalog,
) -> tuple[str, str, str]:
    """Return (resolution_path, authority_source, fallback_value)."""
    cid = normalize(coverage_id)
    attempted = strip_val(attempted_plan)
    catalog_plan = strip_val(catalog.coverage_to_plan.get(cid, ""))
    legacy_map = authority.legacy_product_map
    compat_map = load_product_catalog_crosswalk(catalog.catalog_path)

    overlay_plan = ""
    if overlay_config and overlay_config.enabled and overlay_config.crosswalk_map:
        overlay_plan = strip_val(overlay_config.crosswalk_map.get(cid, {}).get("ql_plan_code", ""))

    if overlay_config and overlay_config.enabled and overlay_plan and attempted == overlay_plan:
        return RESOLUTION_OVERLAY, AUTHORITY_POLICY_FORM, ""

    if catalog_plan and attempted == catalog_plan:
        return RESOLUTION_CATALOG, AUTHORITY_PRODUCT_CATALOG, ""

    if cid in compat_map and attempted == compat_map[cid] and attempted != catalog_plan:
        return RESOLUTION_CATALOG, AUTHORITY_PRODUCT_CATALOG, compat_map[cid]

    if cid in legacy_map and attempted == legacy_map[cid]:
        return RESOLUTION_LEGACY, AUTHORITY_MASTER_LEGACY, legacy_map[cid]

    if attempted == cid:
        return RESOLUTION_PASSTHROUGH, AUTHORITY_RAW_PASSTHROUGH, cid

    return RESOLUTION_RULEBOOK, AUTHORITY_RULEBOOK, attempted


def build_closed_product_authority_trace(
    staged_df: pd.DataFrame,
    source_df: pd.DataFrame,
    source_path: str,
    catalog: ClosedProductCatalog,
    authority: CrosswalkAuthority,
    overlay_config: CrosswalkOverlayConfig | None,
    allow_legacy: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build resolution trace and unauthorized manifest for closed catalog authority."""
    trace_rows: list[dict] = []
    unauthorized_rows: list[dict] = []
    source_rows = list(iter_quikplan_source_rows(source_df))
    n = min(len(source_rows), len(staged_df))

    for i in range(n):
        src_row = source_rows[i]
        cid = strip_val(src_row.get("COVERAGE_ID", ""))
        source_row_number = int(src_row.name) + 2 if hasattr(src_row, "name") and src_row.name is not None else i + 2
        attempted_plan = strip_val(staged_df.iloc[i].get("PLAN", ""))
        attempted_form = strip_val(staged_df.iloc[i].get("FORM", ""))
        attempted_descr = strip_val(staged_df.iloc[i].get("DESCR", ""))
        source_form = strip_val(src_row.get("FORM", "")) if "FORM" in src_row.index else ""

        catalog_plan = strip_val(catalog.coverage_to_plan.get(normalize(cid), ""))
        resolution_path, authority_source, fallback_value = _resolve_attempted_authority_path(
            cid, attempted_plan, authority, overlay_config, catalog,
        )

        is_authorized = False
        failure_reason = ""
        governance_status = "AUTHORIZED"
        remediation_hint = "NONE"

        if plan_contains_space(attempted_plan):
            failure_reason = "PLAN_CONTAINS_SPACE"
            governance_status = "UNAUTHORIZED"
            remediation_hint = "Replace attempted PLAN with authoritative catalog PLAN (no spaces)"
        elif not catalog_plan:
            failure_reason = "MISSING_CATALOG_MAPPING"
            governance_status = "UNAUTHORIZED"
            remediation_hint = "Add Coverage_ID to product_catalog_crosswalk.csv with authoritative PLAN"
        elif attempted_plan == catalog_plan and attempted_plan in catalog.authoritative_plan_set:
            is_authorized = True
            governance_status = "AUTHORIZED"
        elif allow_legacy and attempted_plan:
            is_authorized = True
            governance_status = "LEGACY_FALLBACK_REPORTED"
            remediation_hint = "Legacy fallback emit — closed authority disabled via QLA_ALLOW_LEGACY_PRODUCT_FALLBACK"
        else:
            failure_reason = "PLAN_NOT_IN_CLOSED_CATALOG"
            governance_status = "UNAUTHORIZED"
            if catalog_plan:
                remediation_hint = f"Use authoritative catalog PLAN {catalog_plan} (column {catalog.authority_column})"
            else:
                remediation_hint = "Add authoritative PLAN mapping to product_catalog_crosswalk.csv"

        emitted_to_quikplan = "Y" if is_authorized else "N"

        trace_rows.append({
            "source_file": source_path,
            "source_row_number": source_row_number,
            "source_coverage_id": cid,
            "resolved_plan": catalog_plan or attempted_plan,
            "attempted_plan": attempted_plan,
            "authoritative_plan": catalog_plan,
            "is_authorized": "Y" if is_authorized else "N",
            "authority_source": authority_source,
            "authority_column_used": catalog.authority_column,
            "resolution_path": resolution_path,
            "emitted_to_quikplan": emitted_to_quikplan,
            "governance_status": governance_status,
        })

        if not is_authorized:
            unauthorized_rows.append({
                "source_file": source_path,
                "source_row_number": source_row_number,
                "source_coverage_id": cid,
                "source_form": source_form,
                "attempted_plan": attempted_plan,
                "attempted_form": attempted_form,
                "attempted_descr": attempted_descr,
                "authority_column_used": catalog.authority_column,
                "authoritative_plan": catalog_plan,
                "resolution_path": resolution_path,
                "fallback_value_used": fallback_value,
                "failure_reason": failure_reason,
                "governance_status": governance_status,
                "remediation_hint": remediation_hint,
            })

    trace_df = pd.DataFrame(trace_rows)
    unauthorized_df = pd.DataFrame(unauthorized_rows)
    config_df = pd.DataFrame(catalog.config_errors)
    return trace_df, unauthorized_df, config_df


def apply_closed_authority_emit_filter(
    staged_df: pd.DataFrame,
    source_df: pd.DataFrame,
    trace_df: pd.DataFrame,
    quarantine: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Exclude unauthorized rows from approved quikplan emit output."""
    if trace_df.empty:
        return staged_df.copy(), pd.DataFrame()

    keep_indices: list[int] = []
    hold_rows: list[dict] = []
    source_rows = list(iter_quikplan_source_rows(source_df))
    n = min(len(source_rows), len(staged_df), len(trace_df))

    for i in range(n):
        emitted = strip_val(trace_df.iloc[i].get("emitted_to_quikplan", "N"))
        if emitted == "Y":
            keep_indices.append(i)
        elif quarantine:
            hold = {col: strip_val(staged_df.iloc[i].get(col, "")) for col in staged_df.columns}
            hold["source_coverage_id"] = strip_val(source_rows[i].get("COVERAGE_ID", ""))
            hold["hold_reason"] = strip_val(trace_df.iloc[i].get("governance_status", "UNAUTHORIZED"))
            hold["failure_reason"] = "CLOSED_CATALOG_UNAUTHORIZED"
            hold_rows.append(hold)

    emit_df = staged_df.iloc[keep_indices].reset_index(drop=True) if keep_indices else staged_df.iloc[0:0]
    hold_df = pd.DataFrame(hold_rows)
    return emit_df, hold_df


def run_closed_product_authority_validation(
    staged_df: pd.DataFrame,
    source_df: pd.DataFrame,
    source_path: str = "",
    catalog_path: str | None = None,
    overlay_config: CrosswalkOverlayConfig | None = None,
    authority: CrosswalkAuthority | None = None,
    allow_legacy: bool | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, int, pd.DataFrame]:
    """
    Closed product catalog authority validation (P3C).

    Returns:
        unauthorized_manifest, resolution_trace, config_errors, error_count, approved_df
    """
    if authority is None:
        authority = load_crosswalk_authority(
            os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "Master_Crosswalk.csv")),
            catalog_path,
        )
    if allow_legacy is None:
        allow_legacy = allow_legacy_product_fallback()

    catalog = load_closed_product_catalog(catalog_path)
    trace_df, unauthorized_df, config_df = build_closed_product_authority_trace(
        staged_df, source_df, source_path, catalog, authority, overlay_config, allow_legacy=allow_legacy,
    )

    config_error_count = sum(
        1 for row in catalog.config_errors if strip_val(row.get("severity", "ERROR")) == "ERROR"
    )
    unauthorized_count = len(unauthorized_df) if not allow_legacy else 0
    error_count = unauthorized_count + config_error_count

    approved_df, _ = apply_closed_authority_emit_filter(staged_df, source_df, trace_df)
    return unauthorized_df, trace_df, config_df, error_count, approved_df


def write_closed_product_authority_summary(
    output_path: str,
    *,
    closed_enabled: bool,
    allow_legacy: bool,
    uat_overlay: bool,
    strict_authority: bool,
    catalog: ClosedProductCatalog,
    unauthorized_count: int,
    config_error_count: int,
    emitted_rows: int,
    approved_plans: list[str],
    validation_passed: bool,
) -> None:
    """Write closed_product_authority_summary.json."""
    summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "closed_product_authority": "ENABLED" if closed_enabled else "DISABLED",
        "legacy_fallback_mode": "ENABLED" if allow_legacy else "DISABLED",
        "legacy_fallback_status": "CLOSED_PRODUCT_AUTHORITY_DISABLED" if allow_legacy else "CLOSED_PRODUCT_AUTHORITY_ACTIVE",
        "uat_overlay": "Y" if uat_overlay else "N",
        "strict_product_authority": "Y" if strict_authority else "N",
        "catalog_path": catalog.catalog_path,
        "authority_column_used": catalog.authority_column,
        "authoritative_plan_count": len(catalog.authoritative_plan_set),
        "unauthorized_emit_count": unauthorized_count,
        "catalog_configuration_error_count": config_error_count,
        "emitted_rows": emitted_rows,
        "validation_passed": validation_passed,
        "plans_with_spaces_in_emit": sum(1 for p in approved_plans if plan_contains_space(p)),
        "plans_outside_authoritative_set": sum(
            1 for p in approved_plans if p not in catalog.authoritative_plan_set
        ),
        "unique_emitted_plans": sorted(set(approved_plans)),
    }
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
