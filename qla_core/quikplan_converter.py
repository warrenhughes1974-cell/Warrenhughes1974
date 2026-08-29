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
from qla_core.modal_premium_factors import apply_modal_factors_to_quikplan as apply_issue21j_modal_factors
from qla_core.normalize_utils import extract_day, format_qladmin_mpolicy, normalize, normalize_columns
from qla_core.product_catalog_authority import CrosswalkAuthority, load_crosswalk_authority
from qla_core.quikplan_source_loader import load_quikplan_source_csv
from qla_core.schema_constants import QUIKPLAN_SCHEMA
from qla_core.variation_classification import recommendations_by_plan

PRODUCT_PLAN_FIELDS = frozenset({"PLAN", "MPLAN"})
POLICY_CROSSWALK_FIELDS = frozenset({
    "MPOLICY", "MCLIENTID", "MPRIMID", "MOWNRID", "MPAYRID", "MASGNID", "MBENPID", "MBENCID",
    "MCID", "MOWNCID", "MRIDRID",
})

def map_loan_adv_arrears_to_loanintx(raw) -> tuple[str, str]:
    """Map PCOVR LOAN_ADV_ARREARS to QuikPlan LOANINTX (A/R). Issue #70 CSO codebook.

    Returns (loanintx, audit_tag). audit_tag is mapped_0 / mapped_n / mapped_1 /
    blank_default / unknown_default. Blank and unknown fall back to A.
    """
    v = normalize(raw)
    if v == "0":
        return "A", "mapped_0"
    if v == "N":
        return "A", "mapped_n"
    if v == "1":
        return "R", "mapped_1"
    if not v:
        return "A", "blank_default"
    return "A", "unknown_default"


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
    # Issue #2: MPOLICY identity is source + C via format_qladmin_mpolicy — no strip-9 remap
    if t_f == "MPOLICY":
        return val
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
    elif note == "SEX_BASIS_BOTH_BLANK" and val.upper() == "B":
        val = ""

    # Issue #70: LOAN_ADV_ARREARS codebook → A/R (before SKIP_TRANSLATION / status maps).
    if t_f == "LOANINTX" and s_f == "LOAN_ADV_ARREARS":
        raw_laa = normalize(src_row.get(s_f)) if s_f in source.columns else ""
        val, _audit_tag = map_loan_adv_arrears_to_loanintx(raw_laa)

    if any(k in t_f for k in ["AGE", "DUR", "YRS"]) and "VAL" not in t_f and "VPU" not in t_f and "PREM" not in t_f:
        if val.isdigit() and len(val) == 1:
            val = val.zfill(2)

    if note == "SKIP_TRANSLATION":
        pass
    elif t_f == "PAR":
        # LifePRO EXHIBIT_PAR_NONPAR (P/N/X/F) → QLAdmin PAR (1=participating, 0=non-par)
        translated = trans_map.get(f"PAR_{val}", trans_map.get(val, ""))
        if translated != "":
            val = translated
        elif val not in ("0", "1"):
            val = normalize(rule.get("Default_Value", "0")) or "0"
    else:
        prefix = ""
        if not (t_f == "MTYPE"):
            val = trans_map.get(f"{prefix}{val}", trans_map.get(val, val))

    if t_f in PRODUCT_PLAN_FIELDS or t_f in POLICY_CROSSWALK_FIELDS:
        val = _apply_crosswalk_value(t_f, val, cw_map, crosswalk_authority)

    if t_f == "MPOLICY" and val:
        val = format_qladmin_mpolicy(val)

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


# Option B: when DB structure is known (policy-year / issue+duration / attained-age),
# override rulebook VARDB=0 with the structure code. Does not change VARGP.
_STRUCTURE_VARDB_CODES = frozenset({"1", "2", "3"})


def apply_vardb_structure_overrides(
    row_data: dict,
    recommendations: dict[str, dict] | None,
) -> dict:
    """Set VARDB from structure classification when Recommended_VARDB is 1, 2, or 3."""
    if not recommendations:
        return row_data
    plan = normalize(row_data.get("PLAN", ""))
    rec = recommendations.get(plan)
    if not rec:
        return row_data
    vd = str(rec.get("Recommended_VARDB") or "").strip()
    if vd not in _STRUCTURE_VARDB_CODES:
        return row_data
    out = dict(row_data)
    out["VARDB"] = vd
    return out


def apply_vardb_structure_overrides_df(
    df: pd.DataFrame,
    recommendations: dict[str, dict] | None,
) -> pd.DataFrame:
    """Apply Option B VARDB overrides across a quikplan DataFrame."""
    if df is None or df.empty or not recommendations or "PLAN" not in df.columns:
        return df
    if "VARDB" not in df.columns:
        return df
    out = df.copy()
    for idx in out.index:
        plan = normalize(out.at[idx, "PLAN"])
        rec = recommendations.get(plan)
        if not rec:
            continue
        vd = str(rec.get("Recommended_VARDB") or "").strip()
        if vd in _STRUCTURE_VARDB_CODES:
            out.at[idx, "VARDB"] = vd
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
    loanintx_audits: list | None = None,
) -> dict:
    row_data = {h: "" for h in schema}
    for _, rule in rules.iterrows():
        actual_h, val = _map_field_value(
            src_row, source, rule, schema, lookups, trans_map, cw_map, crosswalk_authority,
        )
        if actual_h:
            row_data[actual_h] = val

    # Issue #70: authoritative same-row PCOVR LOAN_ADV_ARREARS → LOANINTX
    # (overrides rulebook default / raw source digit so A/R emit is source-driven).
    raw_laa = ""
    if "LOAN_ADV_ARREARS" in getattr(src_row, "index", []):
        raw_laa = normalize(src_row.get("LOAN_ADV_ARREARS", ""))
    loanintx, audit_tag = map_loan_adv_arrears_to_loanintx(raw_laa)
    row_data["LOANINTX"] = loanintx
    if loanintx_audits is not None and audit_tag in ("blank_default", "unknown_default"):
        loanintx_audits.append(
            {
                "COVERAGE_ID": normalize(src_row.get("COVERAGE_ID", "")),
                "LOAN_ADV_ARREARS": raw_laa,
                "LOANINTX": loanintx,
                "AUDIT": audit_tag,
            }
        )

    coverage_id = normalize(src_row.get("COVERAGE_ID", ""))
    if overlay_config is not None:
        row_data = apply_crosswalk_overlay(row_data, coverage_id, overlay_config)

    row_data = apply_variation_recommendations(
        row_data, variation_recommendations, auto_apply_variation_codes,
    )
    return apply_vardb_structure_overrides(row_data, variation_recommendations)


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
    loanintx_audits: list[dict] = []
    for src_row in iter_quikplan_source_rows(source):
        row_data = convert_quikplan_row(
            src_row, source, rules, schema, lookups, trans_map, cw_map, overlay_config,
            crosswalk_authority, variation_recommendations, auto_apply_variation_codes,
            loanintx_audits=loanintx_audits,
        )
        output.append([row_data[h] for h in schema])
    # Issue #70 audit/trace for blank/unknown LOAN_ADV_ARREARS → A fallback
    convert_quikplan_to_output.last_loanintx_qa = {  # type: ignore[attr-defined]
        "fallback_count": len(loanintx_audits),
        "fallbacks": loanintx_audits,
    }
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
    # Option B: VARDB 1/2/3 from DB structure even when full AUTO_APPLY is off
    df = apply_vardb_structure_overrides_df(df, variation_recommendations)
    df = apply_rate_variation_flag_enrichment(df)
    df = apply_single_premium_payment_settings(df)
    df = apply_cso_cv_assumptions(df)
    repo_root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    df = apply_ploan_loanint_enrichment(df, repo_root=repo_root, crosswalk_path=cw_path or None)
    df, modal_stats = apply_issue21j_modal_factors(df, repo_root=repo_root)
    try:
        df.attrs["issue21j_modal_stats"] = modal_stats
    except Exception:
        pass
    # Issue A A1: #21J re-applies modal factors; SP zeros must win after overlay.
    df = apply_single_premium_payment_settings(df, repo_root=repo_root)
    from qla_core.issue_a_plan_setup import apply_issue_a_plan_setup

    df = apply_issue_a_plan_setup(df, repo_root=repo_root)
    from qla_core.issue142_sl_rider import seed_9sublf_plan

    df = seed_9sublf_plan(df)
    df = apply_iswl_product_tags(df)
    # Issue #70: preserve the authoritative A/R codebook after all enrichment
    # steps, including the A fallback for blank/unknown source values.
    df = _restore_authoritative_loanintx_from_source(df, source)
    return df


def apply_iswl_product_tags(
    df: pd.DataFrame,
    log=None,
) -> pd.DataFrame:
    """Issue #99: tag ISWL MPLANs with MKTG/PRODUCT/HLOB = ISWLFE for QLAdmin pickup."""
    if df is None or df.empty or "PLAN" not in df.columns:
        return df
    try:
        from qla_core.cso_mortality_crosswalk import (
            ISWL_PRODUCT_TAG,
            ISWL_PRODUCT_TAG_FIELDS,
            is_iswl_mplan,
        )
    except ImportError:
        return df

    updated = 0
    for idx in df.index:
        plan = normalize(df.at[idx, "PLAN"])
        if not is_iswl_mplan(plan):
            continue
        for col in ISWL_PRODUCT_TAG_FIELDS:
            if col in df.columns:
                df.at[idx, col] = ISWL_PRODUCT_TAG
        updated += 1

    if log is not None and updated:
        try:
            log(
                f"Issue #99: ISWL product tags applied to {updated} plans "
                f"({ISWL_PRODUCT_TAG} on {', '.join(ISWL_PRODUCT_TAG_FIELDS)})"
            )
        except Exception:
            pass
    try:
        df.attrs["iswl_product_tags_updated"] = updated
    except Exception:
        pass
    return df


def default_single_premium_plans_path(repo_root: str) -> str:
    return os.path.normpath(
        os.path.join(repo_root, "QLA_Migration", "Configs", "single_premium_plans.csv")
    )


def load_single_premium_plans(repo_root: str) -> set[str]:
    """Load confirmed single-premium PLAN codes (DG-R-009).

    Primary: QLA_Migration/Configs/single_premium_plans.csv (PLAN column).
    Also merges data_governance/config/plan_classification.csv rows with
    IS_SINGLE_PREMIUM = Y when that file is present.
    """
    plans: set[str] = set()
    primary = default_single_premium_plans_path(repo_root)
    if os.path.isfile(primary):
        try:
            cfg = pd.read_csv(primary, dtype=str)
            if "PLAN" in cfg.columns:
                for raw in cfg["PLAN"].fillna(""):
                    plan = normalize(raw)
                    if plan:
                        plans.add(plan)
        except Exception:
            pass
    class_path = os.path.normpath(
        os.path.join(repo_root, "data_governance", "config", "plan_classification.csv")
    )
    if os.path.isfile(class_path):
        try:
            cfg = pd.read_csv(class_path, dtype=str)
            if "PLAN" in cfg.columns and "IS_SINGLE_PREMIUM" in cfg.columns:
                for _, row in cfg.iterrows():
                    flag = str(row.get("IS_SINGLE_PREMIUM", "") or "").strip().upper()
                    if flag in ("Y", "YES", "1", "TRUE", "T"):
                        plan = normalize(row.get("PLAN", ""))
                        if plan:
                            plans.add(plan)
        except Exception:
            pass
    return plans


def apply_single_premium_payment_settings(
    df: pd.DataFrame,
    repo_root: str | None = None,
    log=None,
) -> pd.DataFrame:
    """Force single-premium payment settings on confirmed plans (DG-R-009).

    Sets PAYYRS=1, PAYAGE=0, and SEMI/QTRL/MTHD/MTHB=0.
    No-op when config is empty or PLAN column is missing.
    """
    if df is None or df.empty or "PLAN" not in df.columns:
        return df
    repo_root = repo_root or os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    plans = load_single_premium_plans(repo_root)
    if not plans:
        return df
    updated = 0
    for idx in df.index:
        plan = normalize(df.at[idx, "PLAN"])
        if plan not in plans:
            continue
        df.at[idx, "PAYYRS"] = "1"
        if "PAYAGE" in df.columns:
            df.at[idx, "PAYAGE"] = "0"
        for col in ("SEMI", "QTRL", "MTHD", "MTHB"):
            if col in df.columns:
                df.at[idx, col] = "0"
        updated += 1
    if log is not None and updated:
        try:
            log(f"Single-premium payment settings (DG-R-009): {updated} plans PAYYRS=1")
        except Exception:
            pass
    try:
        df.attrs["single_premium_payment_updated"] = updated
    except Exception:
        pass
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


def _resolve_default_ploan_path(repo_root: str) -> str:
    """Locate newest PLOAN Loan Information extract under QLA_Migration/Source."""
    try:
        from qla_core.lifepro_source_resolver import resolve_table_source
    except ImportError:
        resolve_table_source = None  # type: ignore

    source_dir = os.path.normpath(os.path.join(repo_root, "QLA_Migration", "Source"))
    if resolve_table_source is not None and os.path.isdir(source_dir):
        path, _label = resolve_table_source(source_dir, "quikloan")
        if path and os.path.isfile(path):
            return path
    if not os.path.isdir(source_dir):
        return ""
    candidates = []
    for name in os.listdir(source_dir):
        upper = name.upper()
        if upper.startswith("PLOAN") and upper.endswith(".CSV"):
            candidates.append(os.path.join(source_dir, name))
    if not candidates:
        return ""
    candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return candidates[0]


def build_ploan_loanint_by_quikplan(
    ploan_path: str,
    crosswalk_path: str | None = None,
) -> dict[str, str]:
    """
    Aggregate PLOAN.INTEREST_RATE by LifePRO PLAN_CODE (modal rate), map to QuikPlan PLAN,
    and return PLAN -> LOANINT percent string (AS_PERCENT, e.g. '.0500' -> '5.00').
    """
    from collections import Counter

    from qla_core.quikloan_converter import (
        load_ploan_extract,
        load_ploan_plan_to_quikplan_map,
        normalize_loan_interest_rate,
        sanitize_ploan_rows,
    )

    if not ploan_path or not os.path.isfile(ploan_path):
        return {}

    raw = load_ploan_extract(ploan_path)
    valid, _excluded = sanitize_ploan_rows(raw)
    if valid.empty or "PLAN_CODE" not in valid.columns or "INTEREST_RATE" not in valid.columns:
        return {}

    plan_to_quikplan = load_ploan_plan_to_quikplan_map(crosswalk_path)
    rate_counts: dict[str, Counter] = {}
    for _, row in valid.iterrows():
        lp_plan = normalize(row.get("PLAN_CODE", ""))
        if not lp_plan or lp_plan.startswith("-"):
            continue
        rate_raw = str(row.get("INTEREST_RATE", "") or "").strip()
        if not rate_raw:
            continue
        ql_plan = plan_to_quikplan.get(lp_plan.upper(), "")
        if not ql_plan:
            # Crosswalk may already store QLA plan as target; also try identity
            ql_plan = plan_to_quikplan.get(lp_plan, "")
        if not ql_plan:
            continue
        rate_counts.setdefault(ql_plan.upper(), Counter())[rate_raw] += 1

    out: dict[str, str] = {}
    for ql_plan, counts in rate_counts.items():
        mode_rate, _n = counts.most_common(1)[0]
        emit, _note = normalize_loan_interest_rate(mode_rate, "AS_PERCENT")
        if emit:
            out[ql_plan] = emit
    return out


def _normalize_quikplan_loanintx(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Issue #70 safety net: invalid/missing LOANINTX → A; preserves/canonicalizes A or R."""
    if df is None or df.empty or "LOANINTX" not in df.columns:
        return df, 0
    fixed = 0
    for i in df.index:
        cur_x = str(df.at[i, "LOANINTX"] or "").strip().upper()
        if cur_x in ("A", "R"):
            if str(df.at[i, "LOANINTX"] or "") != cur_x:
                df.at[i, "LOANINTX"] = cur_x
        else:
            df.at[i, "LOANINTX"] = "A"
            fixed += 1
    return df, fixed


def _restore_authoritative_loanintx_from_source(
    df: pd.DataFrame,
    source: pd.DataFrame,
) -> pd.DataFrame:
    """Restore source-confirmed arrears after later plan enrichment steps."""
    if (
        df is None
        or df.empty
        or source is None
        or source.empty
        or "LOANINTX" not in df.columns
        or "LOAN_ADV_ARREARS" not in source.columns
    ):
        return df
    for out_idx, src_row in zip(df.index, iter_quikplan_source_rows(source)):
        loanintx, _audit_tag = map_loan_adv_arrears_to_loanintx(
            src_row.get("LOAN_ADV_ARREARS", "")
        )
        # Re-apply the complete source codebook after later enrichment:
        # unknown/blank source values must retain the A fallback too.
        df.at[out_idx, "LOANINTX"] = loanintx
    return df


def apply_ploan_loanint_enrichment(
    df: pd.DataFrame,
    repo_root: str | None = None,
    ploan_path: str | None = None,
    crosswalk_path: str | None = None,
    log=None,
) -> pd.DataFrame:
    """
    Populate quikplan.LOANINT from PLOAN.INTEREST_RATE (modal rate per plan, AS_PERCENT).

    Rulebook defaults LOANINT to 0.00 with no LifePRO source — Product Setup never saw
    loan rates. QuikLoan already maps PLOAN→MLOANINT; this lifts the same authority onto
    the plan catalog. LOANINTX is source-mapped from PCOVR.LOAN_ADV_ARREARS (Issue #70);
    this path only applies the A/R safety net (preserves valid R).
    Blank-safe: plans with no PLOAN evidence keep existing LOANINT.
    """
    if df is None or df.empty or "PLAN" not in df.columns or "LOANINT" not in df.columns:
        return df

    repo_root = repo_root or os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    path = ploan_path or _resolve_default_ploan_path(repo_root)
    if not path:
        if log:
            log("PLOAN loan-int enrichment: no PLOAN extract found; LOANINT left as-is.")
        df, intx_fixed = _normalize_quikplan_loanintx(df)
        if log and intx_fixed:
            log(f"LOANINTX normalized to A on {intx_fixed} plans (Issue #70).")
        return df

    if not crosswalk_path:
        cw_candidate = os.path.normpath(
            os.path.join(repo_root, "QLA_Migration", "Mapping", "Master_Crosswalk.csv")
        )
        if os.path.isfile(cw_candidate):
            crosswalk_path = cw_candidate

    try:
        rate_by_plan = build_ploan_loanint_by_quikplan(path, crosswalk_path)
    except Exception as exc:
        if log:
            log(f"PLOAN loan-int enrichment failed: {exc}")
        df, intx_fixed = _normalize_quikplan_loanintx(df)
        if log and intx_fixed:
            log(f"LOANINTX normalized to A on {intx_fixed} plans (Issue #70).")
        return df

    if not rate_by_plan:
        if log:
            log(f"PLOAN loan-int enrichment: no plan rates derived from {path}")
        df, intx_fixed = _normalize_quikplan_loanintx(df)
        if log and intx_fixed:
            log(f"LOANINTX normalized to A on {intx_fixed} plans (Issue #70).")
        return df

    placeholder = {"", "0", "0.0", "0.00", "0.000", "0.0000"}
    updated = 0
    for i in df.index:
        plan = normalize(df.at[i, "PLAN"]).upper()
        if not plan or plan not in rate_by_plan:
            continue
        new_rate = rate_by_plan[plan]
        cur = str(df.at[i, "LOANINT"] if "LOANINT" in df.columns else "").strip()
        if cur in placeholder or cur != new_rate:
            df.at[i, "LOANINT"] = new_rate
            updated += 1

    # Issue #70: LOANINTX must be A or R on every plan (not only PLOAN-matched).
    # Safety net only — preserves source-mapped R from LOAN_ADV_ARREARS.
    df, intx_fixed = _normalize_quikplan_loanintx(df)

    qa = {
        "ploan_path": path,
        "plans_with_ploan_rate": len(rate_by_plan),
        "loanint_cells_updated": updated,
        "loanintx_invalid_normalized_to_a": intx_fixed,
    }
    try:
        df.attrs["ploan_loanint_qa"] = qa
    except Exception:
        pass
    if log:
        log(
            f"PLOAN loan-int enrichment: plans_with_rate={qa['plans_with_ploan_rate']} "
            f"LOANINT updated={updated} LOANINTX invalid→A={intx_fixed} "
            f"source={os.path.basename(path)}"
        )
    return df
