"""Lightweight product setup governance diagnostics (Phase P2C/P3B — additive warnings only)."""

from __future__ import annotations

import os

import pandas as pd

from qla_core.normalize_utils import normalize
from qla_core.product_authority_diagnostics import (
    run_strict_authority_validation,
)


def strip_val(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def run_product_governance_diagnostics(
    staged_df: pd.DataFrame,
    source_path: str = "",
    ridr_path: str = "",
    crosswalk_path: str = "",
    overlay_enabled: bool = False,
    strict_authority: bool = False,
    closed_authority: bool = False,
    allow_legacy: bool = False,
    source_df: pd.DataFrame | None = None,
    overlay_config=None,
    product_catalog_path: str = "",
    closed_unauthorized: pd.DataFrame | None = None,
    closed_config_errors: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, int, int]:
    """Return diagnostics dataframe, warning count, error count."""
    rows: list[dict] = []
    errors = 0
    warnings = 0

    if staged_df.empty:
        rows.append(_diag("ERROR", "EMPTY_OUTPUT", "", "quikplan", "No staged rows produced"))
        return pd.DataFrame(rows), 0, 1

    if "PLAN" not in staged_df.columns:
        rows.append(_diag("ERROR", "MISSING_PLAN_COLUMN", "", "PLAN", "PLAN column absent"))
        return pd.DataFrame(rows), 0, 1

    plans = staged_df["PLAN"].map(strip_val)
    dup_mask = plans.duplicated(keep=False) & (plans != "")
    for plan in sorted(set(plans[dup_mask])):
        rows.append(_diag("ERROR", "DUPLICATE_PLAN", plan, "PLAN", f"Duplicate PLAN code ({plan})"))
        errors += 1

    for field in ("PLAN", "DESCR", "PRODUCT"):
        if field not in staged_df.columns:
            continue
        blank = staged_df[field].map(strip_val) == ""
        for idx in staged_df.index[blank]:
            plan = strip_val(staged_df.at[idx, "PLAN"]) if "PLAN" in staged_df.columns else ""
            rows.append(_diag("WARN", "BLANK_CRITICAL_FIELD", plan, field, f"Blank {field} on staged row"))
            warnings += 1

    if source_path and os.path.isfile(source_path) and crosswalk_path and os.path.isfile(crosswalk_path):
        try:
            src = pd.read_csv(
                source_path, dtype=str, encoding="latin1", on_bad_lines="skip", keep_default_na=False,
            ).fillna("")
            src.columns = [strip_val(c) for c in src.columns]
            src = src[src["COVERAGE_ID"].str.match(r"^[0-9A-Za-z]", na=False)]
            xwalk = pd.read_excel(crosswalk_path)
            xwalk.columns = [
                "lifepro_coverage_id", "unused", "ql_plan_code",
                "ql_form_number", "ql_plan_description", "ql_friendly_name",
            ]
            xwalk_ids = set(xwalk["lifepro_coverage_id"].map(strip_val))
            for cid in src["COVERAGE_ID"].map(strip_val):
                if cid and cid not in xwalk_ids:
                    rows.append(_diag("WARN", "MISSING_CROSSWALK_MATCH", cid, "COVERAGE_ID", "No Policy Form Crosswalk row"))
                    warnings += 1
        except Exception:
            pass

    if ridr_path and os.path.isfile(ridr_path) and "PLAN" in staged_df.columns:
        try:
            ridr = pd.read_csv(
                ridr_path, dtype=str, encoding="latin1", on_bad_lines="skip", keep_default_na=False,
            ).fillna("")
            plan_set = set(staged_df["PLAN"].map(strip_val)) - {""}
            mplans = set(ridr["MPLAN"].map(strip_val)) - {""}
            for mplan in sorted(mplans - plan_set):
                count = int((ridr["MPLAN"].map(strip_val) == mplan).sum())
                rows.append(_diag(
                    "WARN", "ORPHAN_MPLAN", mplan, "MPLAN",
                    f"quikridr.MPLAN not in staged quikplan.PLAN ({count} rows)",
                ))
                warnings += 1
            blank_mplan = int((ridr["MPLAN"].map(strip_val) == "").sum())
            if blank_mplan:
                rows.append(_diag(
                    "WARN", "BLANK_MPLAN", "", "MPLAN",
                    f"{blank_mplan} quikridr rows with blank MPLAN",
                ))
                warnings += 1
        except Exception:
            pass

    if closed_authority and not allow_legacy:
        if closed_config_errors is not None and not closed_config_errors.empty:
            for _, row in closed_config_errors.iterrows():
                if strip_val(row.get("severity", "ERROR")) != "ERROR":
                    continue
                rows.append(_diag(
                    "ERROR",
                    strip_val(row.get("error_type", "CATALOG_CONFIG_ERROR")),
                    strip_val(row.get("lifepro_coverage_id", "")),
                    strip_val(row.get("field", "PLAN")),
                    strip_val(row.get("notes", "Product catalog configuration error")),
                ))
                errors += 1

        if closed_unauthorized is not None and not closed_unauthorized.empty:
            for _, row in closed_unauthorized.iterrows():
                rows.append(_diag(
                    "ERROR",
                    strip_val(row.get("failure_reason", "UNAUTHORIZED_PRODUCT_EMIT")),
                    strip_val(row.get("attempted_plan", "")),
                    "PLAN",
                    (
                        f"Closed catalog unauthorized emit "
                        f"(coverage_id={strip_val(row.get('source_coverage_id', ''))}, "
                        f"authoritative={strip_val(row.get('authoritative_plan', ''))}, "
                        f"remediation={strip_val(row.get('remediation_hint', ''))})"
                    ),
                ))
                errors += 1

        if "PLAN" in staged_df.columns:
            for plan in sorted(set(staged_df["PLAN"].map(strip_val)) - {""}):
                if " " in plan:
                    rows.append(_diag(
                        "ERROR", "PLAN_CONTAINS_SPACE", plan, "PLAN",
                        "Emitted PLAN contains spaces — not allowed under closed product authority",
                    ))
                    errors += 1

    if strict_authority and overlay_enabled and crosswalk_path and os.path.isfile(crosswalk_path):
        try:
            src = source_df
            if src is None and source_path and os.path.isfile(source_path):
                src = pd.read_csv(
                    source_path, dtype=str, encoding="latin1", on_bad_lines="skip", keep_default_na=False,
                ).fillna("")
                src.columns = [strip_val(c) for c in src.columns]
                src = src[src["COVERAGE_ID"].astype(str).str.match(r"^[0-9A-Za-z]", na=False)]
            if src is not None and not src.empty:
                manifest, _, strict_errors = run_strict_authority_validation(
                    staged_df, src, crosswalk_path, overlay_config,
                )
                for _, row in manifest.iterrows():
                    rows.append(_diag(
                        "ERROR",
                        "UNAUTHORIZED_PLAN_EMIT",
                        strip_val(row.get("emitted_plan", "")),
                        "PLAN",
                        (
                            f"PLAN not in Policy Form Crosswalk QL Plan Code "
                            f"(coverage_id={strip_val(row.get('source_coverage_id', ''))}, "
                            f"authority={strip_val(row.get('authority_layer_used', ''))}, "
                            f"remediation={strip_val(row.get('recommended_remediation', ''))})"
                        ),
                    ))
                    errors += 1
                if strict_errors and errors < strict_errors:
                    errors = strict_errors
        except Exception:
            pass

    return pd.DataFrame(rows), warnings, errors


def _diag(severity, category, entity_key, field, notes):
    return {
        "severity": severity,
        "category": category,
        "entity_key": entity_key,
        "target_field": field,
        "notes": notes,
        "governance_action": "BLOCK" if severity == "ERROR" else "WARN",
    }
