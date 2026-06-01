"""
QuikPlan conversion engine — extracted from app.py v55.7 (Phase P2A).

Preserves Sync_Rulebook_quikplan mappings, defaults, transforms, and formatting.
Phase P2F: honors rulebook Transformation_Note SKIP_TRANSLATION for literal QLAdmin defaults.
"""

from __future__ import annotations

import os

import pandas as pd

from qla_core.crosswalk_enrichment import (
    CrosswalkOverlayConfig,
    apply_crosswalk_overlay,
    resolve_crosswalk_overlay_config,
)
from qla_core.lookup_loader import build_lookup_tables
from qla_core.normalize_utils import extract_day, normalize, normalize_columns
from qla_core.product_catalog_authority import CrosswalkAuthority, load_crosswalk_authority
from qla_core.quikplan_source_loader import load_quikplan_source_csv
from qla_core.schema_constants import QUIKPLAN_SCHEMA
from qla_core.variation_classification import recommendations_by_plan

PRODUCT_PLAN_FIELDS = frozenset({"PLAN", "MPLAN"})
POLICY_CROSSWALK_FIELDS = frozenset({
    "MPOLICY", "MCLIENTID", "MPRIMID", "MOWNRID", "MPAYRID", "MASGNID", "MBENPID", "MBENCID",
    "MCID", "MOWNCID", "MRIDRID",
})


def prepare_quikplan_source(source: pd.DataFrame) -> pd.DataFrame:
    if "COVERAGE_ID" in source.columns:
        source = source.drop_duplicates(subset=["COVERAGE_ID"], keep="first")
    return source


def iter_quikplan_source_rows(source: pd.DataFrame):
    """Yield source rows in quikplan conversion order (skips separator rows)."""
    for _, src_row in source.iterrows():
        if any("---" in str(v) for v in src_row.values[:3]):
            continue
        yield src_row


def _rule_note(rule: pd.Series) -> str:
    if "Transformation_Note" in rule.index and pd.notna(rule.get("Transformation_Note")):
        return str(rule["Transformation_Note"]).strip().upper()
    if "Notes" in rule.index and pd.notna(rule.get("Notes")):
        return str(rule["Notes"]).strip().upper()
    return ""


def _apply_crosswalk_value(
    t_f: str,
    val: str,
    cw_map: dict,
    crosswalk_authority: CrosswalkAuthority | None,
) -> str:
    if crosswalk_authority is not None:
        if t_f in PRODUCT_PLAN_FIELDS:
            return crosswalk_authority.product_plan_map.get(val, val)
        if t_f in POLICY_CROSSWALK_FIELDS:
            return crosswalk_authority.policy_map.get(val, val)
        return cw_map.get(val, val)
    if t_f in PRODUCT_PLAN_FIELDS or t_f in POLICY_CROSSWALK_FIELDS or t_f == "PLAN":
        return cw_map.get(val, val)
    return val


def _map_field_value(
    src_row: pd.Series,
    source: pd.DataFrame,
    rule: pd.Series,
    schema: list[str],
    lookups: dict,
    trans_map: dict,
    cw_map: dict,
    crosswalk_authority: CrosswalkAuthority | None = None,
) -> tuple[str, str]:
    """Map one rulebook field for quikplan — mirrors app.py generic loop (quikplan path only)."""
    s_f = str(rule.get("Source_Field", "")).strip().upper()
    t_f = str(rule.get("Target_Field", "")).strip().upper()
    lt = str(rule.get("Lookup_Table", "")).strip() if "Lookup_Table" in rule.index else ""
    jk = str(rule.get("Join_Key", "")).strip().upper() if "Join_Key" in rule.index else ""

    if s_f in ["NAN", "NONE", "NULL"]:
        s_f = ""
    if t_f in ["NAN", "NONE", "NULL"]:
        t_f = ""

    if t_f not in [h.upper() for h in schema]:
        return "", ""

    actual_h = [h for h in schema if h.upper() == t_f][0]
    note = _rule_note(rule)

    val = ""
    if lt and jk and lt in lookups and jk in lookups[lt]:
        join_val = normalize(src_row.get(jk))
        if join_val in lookups[lt][jk]:
            val = normalize(lookups[lt][jk][join_val].get(s_f, ""))
        else:
            val = normalize(rule.get("Default_Value", ""))
    else:
        default_val = str(rule.get("Default_Value", "")).strip()
        if not s_f and default_val and default_val.lower() not in ["nan", "none"]:
            val = normalize(default_val)
        else:
            if s_f and s_f in source.columns:
                val = normalize(src_row.get(s_f))
            elif t_f in source.columns:
                val = normalize(src_row.get(t_f))
            else:
                val = normalize(default_val)

    if not val:
        val = normalize(rule.get("Default_Value", ""))

    if note == "EXTRACT_DAY":
        val = extract_day(val)
    elif note == "ROUTE_PAY_YRS":
        c_type = str(src_row.get("PREM_CEASE_TYPE", "")).strip().upper()
        val = val if c_type == "D" else "0"
    elif note == "ROUTE_PAY_AGE":
        c_type = str(src_row.get("PREM_CEASE_TYPE", "")).strip().upper()
        val = val if c_type == "A" else "0"
    elif note == "ROUTE_INS_YRS":
        c_type = str(src_row.get("BENEFIT_CEASE_TYPE", "")).strip().upper()
        val = val if c_type == "D" else "0"
    elif note == "ROUTE_INS_AGE":
        c_type = str(src_row.get("BENEFIT_CEASE_TYPE", "")).strip().upper()
        val = val if c_type == "A" else "0"

    if any(k in t_f for k in ["AGE", "DUR", "YRS"]) and "VAL" not in t_f and "VPU" not in t_f and "PREM" not in t_f:
        if val.isdigit() and len(val) == 1:
            val = val.zfill(2)

    if t_f == "PAR" or note == "SKIP_TRANSLATION":
        pass
    else:
        prefix = ""
        if not (t_f == "MTYPE"):
            val = trans_map.get(f"{prefix}{val}", trans_map.get(val, val))

    if t_f in PRODUCT_PLAN_FIELDS or t_f in POLICY_CROSSWALK_FIELDS:
        val = _apply_crosswalk_value(t_f, val, cw_map, crosswalk_authority)

    return actual_h, val


def apply_variation_recommendations(
    row_data: dict,
    recommendations: dict[str, dict] | None,
    auto_apply: bool,
) -> dict:
    """Apply structure-based VARGP/VARDB when AUTO_APPLY_VARIATION_CODES is enabled."""
    if not auto_apply or not recommendations:
        return row_data
    plan = normalize(row_data.get("PLAN", ""))
    rec = recommendations.get(plan)
    if not rec:
        return row_data
    out = dict(row_data)
    vg = rec.get("Recommended_VARGP")
    vd = rec.get("Recommended_VARDB")
    if vg not in (None, ""):
        out["VARGP"] = str(vg)
    if vd not in (None, ""):
        out["VARDB"] = str(vd)
    return out


def convert_quikplan_row(
    src_row: pd.Series,
    source: pd.DataFrame,
    rules: pd.DataFrame,
    schema: list[str],
    lookups: dict,
    trans_map: dict,
    cw_map: dict,
    overlay_config: CrosswalkOverlayConfig | None = None,
    crosswalk_authority: CrosswalkAuthority | None = None,
    variation_recommendations: dict[str, dict] | None = None,
    auto_apply_variation_codes: bool = False,
) -> dict:
    row_data = {h: "" for h in schema}
    for _, rule in rules.iterrows():
        actual_h, val = _map_field_value(
            src_row, source, rule, schema, lookups, trans_map, cw_map, crosswalk_authority,
        )
        if actual_h:
            row_data[actual_h] = val

    coverage_id = normalize(src_row.get("COVERAGE_ID", ""))
    if overlay_config is not None:
        row_data = apply_crosswalk_overlay(row_data, coverage_id, overlay_config)

    return apply_variation_recommendations(
        row_data, variation_recommendations, auto_apply_variation_codes,
    )


def convert_quikplan_to_output(
    source: pd.DataFrame,
    rules: pd.DataFrame,
    lookups: dict,
    trans_map: dict,
    cw_map: dict,
    schema: list[str] | None = None,
    overlay_config: CrosswalkOverlayConfig | None = None,
    crosswalk_authority: CrosswalkAuthority | None = None,
    variation_recommendations: dict[str, dict] | None = None,
    auto_apply_variation_codes: bool = False,
) -> list[list]:
    schema = schema or QUIKPLAN_SCHEMA
    if overlay_config is None:
        overlay_config = resolve_crosswalk_overlay_config()

    output: list[list] = []
    for src_row in iter_quikplan_source_rows(source):
        row_data = convert_quikplan_row(
            src_row, source, rules, schema, lookups, trans_map, cw_map, overlay_config,
            crosswalk_authority, variation_recommendations, auto_apply_variation_codes,
        )
        output.append([row_data[h] for h in schema])
    return output


def convert_quikplan_dataframe(
    source: pd.DataFrame,
    rules: pd.DataFrame,
    lookups: dict,
    trans_map: dict,
    cw_map: dict,
    schema: list[str] | None = None,
    overlay_config: CrosswalkOverlayConfig | None = None,
    crosswalk_authority: CrosswalkAuthority | None = None,
    variation_recommendations: dict[str, dict] | None = None,
    auto_apply_variation_codes: bool = False,
) -> pd.DataFrame:
    schema = schema or QUIKPLAN_SCHEMA
    rows = convert_quikplan_to_output(
        source, rules, lookups, trans_map, cw_map, schema, overlay_config, crosswalk_authority,
        variation_recommendations, auto_apply_variation_codes,
    )
    return pd.DataFrame(rows, columns=schema)


def load_translation_map(trans_path: str) -> dict:
    if not trans_path or not os.path.isfile(trans_path):
        return {}
    trans_df = pd.read_csv(trans_path, dtype=str)
    return {normalize(k): str(v).strip() for k, v in zip(trans_df.iloc[:, 0], trans_df.iloc[:, 1])}


def load_crosswalk_map(cw_path: str) -> dict:
    if not cw_path or not os.path.isfile(cw_path):
        return {}
    cw_df = pd.read_csv(cw_path, dtype=str)
    return {normalize(k): normalize(v) for k, v in zip(cw_df.iloc[:, 0], cw_df.iloc[:, 1])}


def run_quikplan_conversion(
    source_path: str,
    rulebook_path: str,
    trans_path: str = "",
    cw_path: str = "",
    lookup_dir: str | None = None,
    schema: list[str] | None = None,
    overlay_config: CrosswalkOverlayConfig | None = None,
    product_catalog_path: str | None = None,
    variation_audit_path: str | None = None,
) -> pd.DataFrame:
    """End-to-end quikplan conversion from file paths (subprocess runner entry)."""
    source, _ = load_quikplan_source_csv(source_path, collect_trace=False)
    source = normalize_columns(source)
    source = prepare_quikplan_source(source)

    rules = pd.read_csv(rulebook_path, dtype=str)
    rules.columns = [str(col).strip() for col in rules.columns]

    source_dir = os.path.dirname(os.path.abspath(source_path))
    lookups = build_lookup_tables(rules, source_dir, lookup_dir=lookup_dir)
    trans_map = load_translation_map(trans_path)
    cw_map = load_crosswalk_map(cw_path)
    crosswalk_authority = load_crosswalk_authority(cw_path, product_catalog_path)

    if overlay_config is None:
        overlay_config = resolve_crosswalk_overlay_config()

    variation_recommendations = None
    auto_apply = False
    try:
        from qla_core.variation_classification import (
            VariationClassificationConfig,
            classify_all_plans,
            write_variation_audit_csv,
        )

        repo_root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
        var_cfg = VariationClassificationConfig.from_env_and_defaults(repo_root)
        audit_rows = classify_all_plans(var_cfg)
        variation_recommendations = recommendations_by_plan(audit_rows)
        auto_apply = var_cfg.auto_apply_variation_codes
        if variation_audit_path:
            write_variation_audit_csv(audit_rows, variation_audit_path)
    except Exception:
        variation_recommendations = None
        auto_apply = False

    df = convert_quikplan_dataframe(
        source, rules, lookups, trans_map, cw_map, schema, overlay_config, crosswalk_authority,
        variation_recommendations, auto_apply,
    )
    df = apply_rate_variation_flag_enrichment(df)
    df = apply_cso_cv_assumptions(df)
    return df


def apply_rate_variation_flag_enrichment(
    df: pd.DataFrame,
    repo_root: str | None = None,
) -> pd.DataFrame:
    """Post-process quikplan with rate-derived PLANVALOPT / *VARY* flags (Phase R7B)."""
    try:
        from qla_core.quikplan_rate_variation_flags import (
            RateVariationEnrichmentConfig,
            enrich_quikplan_rows,
            write_r7b_integration_outputs,
        )
    except ImportError:
        return df

    repo_root = repo_root or os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    cfg = RateVariationEnrichmentConfig.from_env_and_defaults(repo_root)
    if not cfg.apply_rate_variation_flags:
        return df

    schema = list(df.columns) if len(df.columns) else QUIKPLAN_SCHEMA
    rows = [{c: "" if pd.isna(df.at[i, c]) else str(df.at[i, c]).strip() for c in schema} for i in df.index]
    result = enrich_quikplan_rows(rows, cfg, repo_root)
    if result.validation_blockers:
        return df
    out = pd.DataFrame(result.enriched_rows, columns=QUIKPLAN_SCHEMA)
    audit_dir = os.environ.get("QLA_RATE_VARIATION_AUDIT", "").strip()
    if audit_dir in ("1", "true", "yes", "y") and cfg.integration_audit_dir:
        write_r7b_integration_outputs(result, cfg.integration_audit_dir)
    return out


def apply_cso_cv_assumptions(
    df: pd.DataFrame,
    repo_root: str | None = None,
    log=None,
) -> pd.DataFrame:
    """Populate quikplan NFOINT / INTMETHCV from the CSO Mortality Crosswalk (isolated,
    blank-safe, rollback-safe). Mirrors the GUI conversion path so the authoritative
    product-setup quikplan carries the same CV assumptions. The per-plan QA summary is
    stashed on df.attrs['cso_cv_qa'] for callers that emit a QA artifact. No-op if the
    crosswalk module/file is unavailable (deferred behavior preserved)."""
    try:
        from qla_core.cso_mortality_crosswalk import (
            apply_quikplan_cv_assumptions,
            default_crosswalk_path,
            load_cso_mortality_crosswalk,
        )
    except ImportError:
        return df

    repo_root = repo_root or os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    resolver = load_cso_mortality_crosswalk(default_crosswalk_path(repo_root))
    if not resolver.plans_loaded:
        return df

    qa = apply_quikplan_cv_assumptions(df, resolver, log=log)
    try:
        df.attrs["cso_cv_qa"] = qa
    except Exception:
        pass
    return df
