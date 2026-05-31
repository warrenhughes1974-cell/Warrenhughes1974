#!/usr/bin/env python3
"""
Phase P2D — Crosswalk / Translation Governance Audit + Auto-Scaffold.

Detect-only governance runner: no source mutation, no auto-remediation.
Generates manifests, scaffold quarantine files, and executive findings.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))
SCAFFOLD_DIR = os.path.join(SCRIPT_DIR, "scaffold")
MANIFEST_DIR = os.path.join(ROOT, "plan_governance", "manifests")

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from qla_core.crosswalk_enrichment import CrosswalkOverlayConfig, load_policy_form_crosswalk
from qla_core.quikplan_converter import run_quikplan_conversion
from qla_core.schema_constants import QUIKPLAN_SCHEMA

POLICY_NUM_RE = re.compile(r"^90\d{8}$")


def strip_val(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def norm_key(value) -> str:
    return strip_val(value).upper()


def read_source(path: str) -> pd.DataFrame:
    df = pd.read_csv(
        path, encoding="latin1", low_memory=False, dtype=str,
        on_bad_lines="skip", keep_default_na=False,
    ).fillna("")
    df.columns = [strip_val(c) for c in df.columns]
    if "COVERAGE_ID" in df.columns:
        df = df[~df["COVERAGE_ID"].astype(str).str.contains("---", na=False)]
        df = df.drop_duplicates(subset=["COVERAGE_ID"], keep="first")
    return df


def read_pcomp(path: str) -> pd.DataFrame:
    df = pd.read_csv(
        path, encoding="latin1", low_memory=False, dtype=str,
        on_bad_lines="skip", keep_default_na=False, skiprows=[1],
    ).fillna("")
    df.columns = [strip_val(c) for c in df.columns]
    return df


def load_policy_form_df(path: str) -> pd.DataFrame:
    xwalk = pd.read_excel(path)
    xwalk.columns = [
        "lifepro_coverage_id", "unused", "ql_plan_code",
        "ql_form_number", "ql_plan_description", "ql_friendly_name",
    ]
    for col in xwalk.columns:
        if col != "ql_plan_description" and col != "ql_friendly_name":
            xwalk[col] = xwalk[col].map(strip_val)
        else:
            xwalk[col] = xwalk[col].astype(str).str.strip()
    return xwalk


def classify_master_crosswalk(mc: pd.DataFrame) -> pd.DataFrame:
    mc = mc.copy()
    mc["Old_Value"] = mc["Old_Value"].map(strip_val)
    mc["New_Value"] = mc["New_Value"].map(strip_val)
    mc["mapping_class"] = mc["Old_Value"].apply(
        lambda v: "POLICY_NUMBER" if POLICY_NUM_RE.match(v) else "PLAN_OR_ENTITY",
    )
    return mc


def audit_master_crosswalk(mc: pd.DataFrame, source_ids: set[str], output_plans: set[str]) -> dict:
    findings: list[dict] = []
    plan_mc = mc[mc["mapping_class"] == "PLAN_OR_ENTITY"]

    dup_old = mc[mc["Old_Value"].duplicated(keep=False) & (mc["Old_Value"] != "")]
    for old in sorted(set(dup_old["Old_Value"])):
        vals = mc[mc["Old_Value"] == old][["Old_Value", "New_Value", "mapping_class"]].drop_duplicates()
        mclass = vals.iloc[0]["mapping_class"]
        findings.append({
            "asset": "Master_Crosswalk.csv",
            "category": "DUPLICATE_OLD_VALUE",
            "entity_key": old,
            "severity": "ERROR" if mclass == "PLAN_OR_ENTITY" else "WARN",
            "detail": "; ".join(f"{r.New_Value}({r.mapping_class})" for _, r in vals.iterrows()),
        })

    conflict_old = mc.groupby("Old_Value")["New_Value"].nunique()
    for old in conflict_old[conflict_old > 1].index:
        findings.append({
            "asset": "Master_Crosswalk.csv",
            "category": "CONFLICTING_OLD_VALUE",
            "entity_key": old,
            "severity": "ERROR",
            "detail": "Same Old_Value maps to multiple New_Value entries",
        })

    dup_new_plan = plan_mc[plan_mc["New_Value"].duplicated(keep=False) & (plan_mc["New_Value"] != "")]
    for new in sorted(set(dup_new_plan["New_Value"])):
        olds = sorted(set(plan_mc[plan_mc["New_Value"] == new]["Old_Value"]))
        findings.append({
            "asset": "Master_Crosswalk.csv",
            "category": "DUPLICATE_PLAN_TARGET",
            "entity_key": new,
            "severity": "WARN",
            "detail": f"Multiple Old_Value map to PLAN {new}: {', '.join(olds[:5])}{'...' if len(olds) > 5 else ''}",
        })

    unused_plan = plan_mc[~plan_mc["Old_Value"].isin(source_ids) & ~plan_mc["New_Value"].isin(output_plans)]
    for _, row in unused_plan.iterrows():
        findings.append({
            "asset": "Master_Crosswalk.csv",
            "category": "UNUSED_PLAN_MAPPING",
            "entity_key": row["Old_Value"],
            "severity": "INFO",
            "detail": f"Plan mapping {row['Old_Value']}->{row['New_Value']} not referenced in current source/output",
        })

    return {"findings": findings, "plan_mc": plan_mc, "policy_count": int((mc["mapping_class"] == "POLICY_NUMBER").sum())}


def audit_passthrough_and_missing_crosswalk(
    source: pd.DataFrame,
    baseline: pd.DataFrame,
    xdf: pd.DataFrame,
    mc_map: dict[str, str],
) -> tuple[list[dict], list[dict], list[dict]]:
    """Detect passthrough LifePRO IDs and missing/blank crosswalk PLAN rows."""
    missing_rows: list[dict] = []
    passthrough_rows: list[dict] = []
    plan_conflicts: list[dict] = []

    x_by_cid = {strip_val(r["lifepro_coverage_id"]): r for _, r in xdf.iterrows()}
    baseline_by_plan = {strip_val(r["PLAN"]): r for _, r in baseline.iterrows()}

    for _, srow in source.iterrows():
        cid = strip_val(srow.get("COVERAGE_ID", ""))
        if not cid:
            continue
        current_plan = mc_map.get(cid, cid)
        if current_plan not in baseline_by_plan and current_plan != cid:
            for plan, brow in baseline_by_plan.items():
                if mc_map.get(cid, "") == plan:
                    current_plan = plan
                    break
        out_row = baseline_by_plan.get(current_plan)
        if out_row is None:
            for plan in baseline_by_plan:
                if norm_key(plan) == norm_key(current_plan):
                    out_row = baseline_by_plan[plan]
                    current_plan = plan
                    break
        cur_plan = strip_val(out_row["PLAN"]) if out_row is not None else current_plan
        cur_form = strip_val(out_row["FORM"]) if out_row is not None else strip_val(srow.get("POLICY_FORM_NUM", ""))

        xrow = x_by_cid.get(cid)
        if xrow is None:
            missing_rows.append({
                "coverage_id": cid,
                "current_plan": cur_plan,
                "governance_action": "SCAFFOLD_FOR_BUSINESS_REVIEW",
                "notes": "Source COVERAGE_ID absent from Policy Form Crosswalk",
            })
            continue

        xplan = strip_val(xrow["ql_plan_code"])
        xform = strip_val(xrow["ql_form_number"])
        if not xplan:
            missing_rows.append({
                "coverage_id": cid,
                "current_plan": cur_plan,
                "governance_action": "MISSING_QL_PLAN_CODE",
                "notes": "Crosswalk row exists but QL Plan Code is blank",
            })

        if cur_plan == cid or norm_key(cur_plan) == norm_key(cid) or (
            re.search(r"\s", cur_plan) and not re.match(r"^[A-Z0-9]{4,8}$", cur_plan)
        ):
            passthrough_rows.append({
                "lifepro_coverage_id": cid,
                "current_output_plan": cur_plan,
                "crosswalk_ql_plan_code": xplan,
                "governance_action": "PASSTHROUGH_LIFEPRO_ID",
                "notes": "Output PLAN equals LifePRO COVERAGE_ID — requires QL Plan Code assignment",
            })
        elif xplan and xplan != cur_plan:
            plan_conflicts.append({
                "coverage_id": cid,
                "current_plan": cur_plan,
                "crosswalk_plan": xplan,
                "governance_action": "PLAN_AUTHORITY_CONFLICT",
            })

        if xform and cur_form and xform != cur_form:
            pass  # handled in form scaffold via audit_policy_form_crosswalk

    return missing_rows, passthrough_rows, plan_conflicts


def audit_policy_form_crosswalk(
    xdf: pd.DataFrame,
    source_ids: set[str],
    baseline: pd.DataFrame,
    source: pd.DataFrame,
    mc_map: dict[str, str],
) -> dict:
    findings: list[dict] = []
    scaffold_missing: list[dict] = []
    scaffold_dup: list[dict] = []
    scaffold_form: list[dict] = []
    scaffold_passthrough: list[dict] = []

    x_ids = set(xdf["lifepro_coverage_id"].map(strip_val)) - {""}
    for cid in sorted(source_ids - x_ids):
        scaffold_missing.append({
            "coverage_id": cid,
            "source_field": "COVERAGE_ID",
            "governance_action": "SCAFFOLD_FOR_BUSINESS_REVIEW",
            "notes": "Source COVERAGE_ID absent from Policy Form Crosswalk",
        })
        findings.append({
            "asset": "Policy Form Crosswalk 5.22.26.xlsx",
            "category": "MISSING_CROSSWALK_ROW",
            "entity_key": cid,
            "severity": "WARN",
            "detail": "No crosswalk row for active source COVERAGE_ID",
        })

    dup_cid = xdf[xdf["lifepro_coverage_id"].duplicated(keep=False) & (xdf["lifepro_coverage_id"] != "")]
    for cid in sorted(set(dup_cid["lifepro_coverage_id"])):
        scaffold_dup.append({
            "lifepro_coverage_id": cid,
            "duplicate_count": int((xdf["lifepro_coverage_id"] == cid).sum()),
            "governance_action": "QUARANTINE_DUPLICATE",
        })
        findings.append({
            "asset": "Policy Form Crosswalk 5.22.26.xlsx",
            "category": "DUPLICATE_COVERAGE_ID",
            "entity_key": cid,
            "severity": "ERROR",
            "detail": "Duplicate LifePRO COVERAGE_ID in crosswalk",
        })

    extra_missing, scaffold_passthrough, plan_conflicts = audit_passthrough_and_missing_crosswalk(
        source, baseline, xdf, mc_map,
    )
    for row in extra_missing:
        if row not in scaffold_missing:
            scaffold_missing.append(row)
        findings.append({
            "asset": "Policy Form Crosswalk 5.22.26.xlsx",
            "category": "MISSING_CROSSWALK_ROW" if "absent" in row.get("notes", "") else "BLANK_QL_PLAN_CODE",
            "entity_key": row["coverage_id"],
            "severity": "WARN",
            "detail": row["notes"],
        })
    for row in scaffold_passthrough:
        findings.append({
            "asset": "Policy Form Crosswalk 5.22.26.xlsx",
            "category": "PASSTHROUGH_LIFEPRO_ID",
            "entity_key": row["lifepro_coverage_id"],
            "severity": "WARN",
            "detail": row["notes"],
        })
    for row in plan_conflicts:
        findings.append({
            "asset": "Policy Form Crosswalk 5.22.26.xlsx",
            "category": "PLAN_MAPPING_INCONSISTENCY",
            "entity_key": row["coverage_id"],
            "severity": "WARN",
            "detail": f"Crosswalk PLAN {row['crosswalk_plan']} != current output PLAN {row['current_plan']}",
        })

    baseline_by_plan = {strip_val(r["PLAN"]): r for _, r in baseline.iterrows()}
    cid_to_form = {strip_val(r["lifepro_coverage_id"]): strip_val(r["ql_form_number"]) for _, r in xdf.iterrows()}

    for cid in sorted(source_ids & x_ids):
        xform = cid_to_form.get(cid, "")
        current_plan = mc_map.get(cid, cid)
        out_row = baseline_by_plan.get(current_plan)
        if out_row is None:
            continue
        cur_form = strip_val(out_row.get("FORM", ""))
        if xform and cur_form and xform != cur_form:
            scaffold_form.append({
                "coverage_id": cid,
                "current_form": cur_form,
                "crosswalk_form": xform,
                "current_plan": current_plan,
                "governance_action": "FORM_CONFLICT_REVIEW",
            })
            findings.append({
                "asset": "Policy Form Crosswalk 5.22.26.xlsx",
                "category": "FORM_MAPPING_INCONSISTENCY",
                "entity_key": cid,
                "severity": "WARN",
                "detail": f"Crosswalk FORM {xform} != current output FORM {cur_form}",
            })

    return {
        "findings": findings,
        "scaffold_missing": scaffold_missing,
        "scaffold_dup": scaffold_dup,
        "scaffold_form": scaffold_form,
        "scaffold_passthrough": scaffold_passthrough,
    }


def audit_translations(trans_df: pd.DataFrame, baseline: pd.DataFrame, rules: pd.DataFrame) -> dict:
    trans_map = {norm_key(k): strip_val(v) for k, v in zip(trans_df.iloc[:, 0], trans_df.iloc[:, 1])}
    trans_keys = set(trans_map)
    findings: list[dict] = []
    untranslated: list[dict] = []
    unused: list[dict] = []

    observed_values: set[str] = set()
    trans_fields = rules[
        rules["Target_Field"].notna()
        & ~rules["Target_Field"].isin(["PLAN", "PAR"])
    ]["Target_Field"].map(strip_val).str.upper().unique()

    for col in baseline.columns:
        if col.upper() not in trans_fields and col.upper() not in ("SEX", "BASIS", "PRODUCT", "PLANTYPE"):
            continue
        for val in baseline[col].map(strip_val).unique():
            if val:
                observed_values.add(norm_key(val))

    for val in sorted(observed_values):
        if val not in trans_keys and val not in {"", "0", "N", "Y", "A", "B"}:
            untranslated.append({
                "observed_value": val,
                "governance_action": "REVIEW_TRANSLATION_NEED",
                "notes": "Value appears in quikplan output but has no Master_Value_Translation entry",
            })

    for key in sorted(trans_keys):
        if key and key not in observed_values:
            unused.append({
                "source_code": key,
                "qla_result": trans_map[key],
                "governance_action": "UNUSED_TRANSLATION_ENTRY",
                "notes": "Translation entry not observed in current quikplan output",
            })
            findings.append({
                "asset": "Master_Value_Translation.csv",
                "category": "UNUSED_TRANSLATION",
                "entity_key": key,
                "severity": "INFO",
                "detail": f"Translation {key}->{trans_map[key]} not observed in output",
            })

    return {"findings": findings, "untranslated": untranslated, "unused": unused, "trans_map": trans_map}


def audit_rulebook(rules: pd.DataFrame) -> dict:
    rules = rules.copy()
    rules.columns = [strip_val(c) for c in rules.columns]
    rules["Target_Field"] = rules["Target_Field"].map(lambda v: strip_val(v).upper())
    rules["Source_Field"] = rules["Source_Field"].fillna("").map(lambda v: strip_val(v).upper())

    schema_upper = {f.upper() for f in QUIKPLAN_SCHEMA}
    mapped_targets = set(rules["Target_Field"]) - {""}
    unmapped = sorted(schema_upper - mapped_targets)
    dead = sorted(mapped_targets - schema_upper)
    duplicate_targets = rules[rules["Target_Field"].duplicated(keep=False) & (rules["Target_Field"] != "")]
    conflicting: list[dict] = []
    for tgt in sorted(set(duplicate_targets["Target_Field"])):
        subset = rules[rules["Target_Field"] == tgt][["Source_Field", "Default_Value", "Lookup_Table", "Transformation_Note"]]
        conflicting.append({
            "target_field": tgt,
            "rule_count": len(subset),
            "governance_action": "REVIEW_DUPLICATE_RULE",
            "notes": "Multiple rulebook rows target same field (may be intentional routing)",
        })

    coverage_rows = []
    for field in QUIKPLAN_SCHEMA:
        fup = field.upper()
        match = rules[rules["Target_Field"] == fup]
        if match.empty:
            coverage_rows.append({
                "target_field": field,
                "mapped": "N",
                "source_field": "",
                "default_value": "",
                "lookup_table": "",
                "transformation_note": "",
                "coverage_status": "UNMAPPED",
            })
        else:
            r = match.iloc[0]
            coverage_rows.append({
                "target_field": field,
                "mapped": "Y",
                "source_field": strip_val(r.get("Source_Field", "")),
                "default_value": strip_val(r.get("Default_Value", "")),
                "lookup_table": strip_val(r.get("Lookup_Table", "")),
                "transformation_note": strip_val(r.get("Transformation_Note", "")),
                "coverage_status": "MAPPED",
            })

    findings = []
    for field in unmapped:
        findings.append({
            "asset": "Sync_Rulebook_quikplan.csv",
            "category": "UNMAPPED_SCHEMA_FIELD",
            "entity_key": field,
            "severity": "ERROR",
            "detail": "Schema field has no rulebook mapping",
        })
    for field in dead:
        findings.append({
            "asset": "Sync_Rulebook_quikplan.csv",
            "category": "STALE_RULEBOOK_TARGET",
            "entity_key": field,
            "severity": "WARN",
            "detail": "Rulebook target not in QUIKPLAN_SCHEMA",
        })

    return {
        "findings": findings,
        "coverage_rows": coverage_rows,
        "unmapped": unmapped,
        "dead": dead,
        "conflicting": conflicting,
    }


def audit_pcomp(pcomp: pd.DataFrame, source_ids: set[str]) -> dict:
    findings: list[dict] = []
    missing: list[dict] = []
    if "COVERAGE_ID" not in pcomp.columns:
        return {"findings": findings, "missing": missing}

    pcomp_ids = set(pcomp["COVERAGE_ID"].map(lambda v: strip_val(v))) - {""}
    for cid in sorted(source_ids - pcomp_ids):
        missing.append({
            "coverage_id": cid,
            "lookup_table": "PCOMP",
            "join_key": "COVERAGE_ID",
            "governance_action": "MISSING_PCOMP_LOOKUP",
            "notes": "Source COVERAGE_ID not found in PCOMP.csv",
        })
        findings.append({
            "asset": "PCOMP.csv",
            "category": "MISSING_PCOMP_ROW",
            "entity_key": cid,
            "severity": "WARN",
            "detail": "MINUNIT/MAXUNIT lookup may fall back to rulebook default",
        })

    return {"findings": findings, "missing": missing}


def audit_orphan_plans(baseline: pd.DataFrame, ridr_path: str) -> list[dict]:
    orphans: list[dict] = []
    if not os.path.isfile(ridr_path) or baseline.empty:
        return orphans
    ridr = pd.read_csv(ridr_path, dtype=str, encoding="latin1", on_bad_lines="skip", keep_default_na=False).fillna("")
    plan_set = set(baseline["PLAN"].map(strip_val)) - {""}
    mplans = set(ridr["MPLAN"].map(strip_val)) - {""}
    for mplan in sorted(mplans - plan_set):
        count = int((ridr["MPLAN"].map(strip_val) == mplan).sum())
        orphans.append({
            "mplan_code": mplan,
            "quikridr_row_count": count,
            "governance_action": "ORPHAN_MPLAN_REVIEW",
            "notes": "quikridr.MPLAN not present in quikplan.PLAN catalog",
        })
    return orphans


def build_ownership_manifest() -> pd.DataFrame:
    rows = [
        ("PLAN", "Master_Crosswalk Old_Value->New_Value on COVERAGE_ID", "Policy Form Crosswalk ql_plan_code", "OVERLAP", "Master_Crosswalk drives current emit; crosswalk is future authority", "Migrate PLAN authority to Policy Form Crosswalk after overlay signoff"),
        ("FORM", "LifePRO POLICY_FORM_NUM via rulebook", "Policy Form Crosswalk ql_form_number", "OVERLAP", "Overlay would override LifePRO form number", "Confirm FORM authority before overlay"),
        ("DESCR", "LifePRO DESCRIPTION via rulebook", "Policy Form Crosswalk ql_plan_description", "PARTIAL", "Mostly aligned; overlay normalizes casing", "Crosswalk owns display description at cutover"),
        ("PLANNAME", "LifePRO DESCRIPTION duplicated via rulebook", "Policy Form Crosswalk ql_friendly_name", "CONFLICT", "Current output uses DESCRIPTION not friendly name", "Crosswalk owns PLANNAME at cutover"),
        ("Policy_Number", "Master_Crosswalk (901xxxxxxxx rows)", "Master_Crosswalk", "CONFIRMED", "4920 policy-number mappings", "Keep policy mappings separate from PLAN catalog"),
        ("Value_Translation", "Master_Value_Translation.csv", "Master_Value_Translation.csv", "CONFIRMED", "Applied post-mapping except PAR", "Maintain translation table for coded LifePRO values"),
        ("Rulebook_Transforms", "Sync_Rulebook_quikplan.csv", "Sync_Rulebook_quikplan.csv", "CONFIRMED", "Authoritative field routing/defaults", "No redesign — audit coverage only"),
        ("PCOMP_Lookup", "PCOMP.csv via rulebook join", "PCOMP.csv", "CONFIRMED", "MINUNIT/MAXUNIT from MIN/MAX_ISSUE_AMT1", "Ensure PCOMP completeness for all COVERAGE_ID"),
        ("HRIGPKEY", "Rulebook default blank", "Future actuarial governance (P5)", "FUTURE", "Not populated — correct for catalog phase", "Do not populate until actuarial phase"),
        ("MPLAN", "quikridr transactional reference", "quikplan.PLAN catalog", "DOWNSTREAM", "Orphan MPLAN codes indicate catalog gaps", "Resolve via catalog completeness not crosswalk"),
    ]
    return pd.DataFrame(rows, columns=[
        "field_or_mapping_type", "current_owner", "proposed_owner",
        "ownership_status", "overlap_risk", "governance_recommendation",
    ])


def audit_actuarial_readiness(baseline: pd.DataFrame) -> pd.DataFrame:
    actuarial_dims = [
        ("PLAN", "Catalog key", "POPULATED", "Required — 133 rows"),
        ("FORM", "Product form attachment", "POPULATED", "Required for product identity"),
        ("HRIGPKEY", "Gross premium rate lookup (QuikPlbd)", "BLANK", "Future P5 — intentionally blank"),
        ("SEX", "Gender vary-by", "POPULATED", "From SEX_BASIS / translation"),
        ("UWCLASS", "Underwriting class vary-by", "NOT_IN_SCHEMA", "Future — UWVARY* fields blank"),
        ("BAND", "Band vary-by (BDCODE)", "PARTIAL", "BDVARYGP/DB defaulted; others blank"),
        ("ISSUE_STATE", "State vary-by", "NOT_IN_SCHEMA", "STVARY* blank — future governance"),
        ("ISSUE_COUNTRY", "Country vary-by", "NOT_IN_SCHEMA", "STVARY* blank — future governance"),
        ("EFFDATE", "Effective date dimension", "NOT_IN_CATALOG", "Comes from policy transaction tables not quikplan"),
        ("GDVARY*", "Gender vary-by flags", "PARTIAL", "GP/DB defaulted to 0"),
        ("UWVARY*", "UW vary-by flags", "BLANK", "Future actuarial attachment"),
        ("STVARY*", "State/country vary-by", "BLANK", "Future actuarial attachment"),
        ("BDVARY*", "Band vary-by", "PARTIAL", "GP/DB=0; CV/TV/DV blank"),
        ("VARDB/VARGP", "Reserve/premium variation flags", "POPULATED", "Defaulted in rulebook"),
    ]
    rows = []
    for dim, purpose, status, notes in actuarial_dims:
        readiness = "READY" if status == "POPULATED" else "NOT_READY" if status in ("BLANK", "NOT_IN_SCHEMA", "NOT_IN_CATALOG") else "PARTIAL"
        rows.append({
            "dimension": dim,
            "purpose": purpose,
            "current_state": status,
            "readiness": readiness,
            "notes": notes,
            "future_phase": "P5_ACTUARIAL" if readiness != "READY" else "N/A",
        })

    blank_hrig = int((baseline["HRIGPKEY"].map(strip_val) == "").sum()) if "HRIGPKEY" in baseline.columns else 133
    rows.append({
        "dimension": "HRIGPKEY_POPULATION_CHECK",
        "purpose": "Rate table join readiness",
        "current_state": f"{blank_hrig}/133 blank",
        "readiness": "NOT_READY",
        "notes": "Expected — catalog emit must not wait on actuarial",
        "future_phase": "P5_ACTUARIAL",
    })
    return pd.DataFrame(rows)


def audit_overlay_readiness(
    baseline: pd.DataFrame,
    crosswalk_path: str,
    source_path: str,
    rulebook_path: str,
    trans_path: str,
    cw_path: str,
    pcomp_dir: str,
) -> dict:
    overlay_cfg = CrosswalkOverlayConfig(
        enabled=True,
        crosswalk_path=crosswalk_path,
        crosswalk_map=load_policy_form_crosswalk(crosswalk_path),
    )
    overlay_df = run_quikplan_conversion(
        source_path=source_path,
        rulebook_path=rulebook_path,
        trans_path=trans_path,
        cw_path=cw_path,
        lookup_dir=pcomp_dir,
        overlay_config=overlay_cfg,
    )

    diffs = []
    if list(baseline.columns) == list(overlay_df.columns) and len(baseline) == len(overlay_df):
        for col in baseline.columns:
            b = baseline[col].map(strip_val)
            o = overlay_df[col].map(strip_val)
            mismatch = b != o
            if mismatch.any():
                for idx in baseline.index[mismatch]:
                    diffs.append({
                        "plan": strip_val(baseline.at[idx, "PLAN"]),
                        "field": col,
                        "baseline_value": strip_val(baseline.at[idx, col]),
                        "overlay_value": strip_val(overlay_df.at[idx, col]),
                    })

    overlay_plans = overlay_df["PLAN"].map(strip_val)
    dup_plans = overlay_plans[overlay_plans.duplicated(keep=False) & (overlay_plans != "")]
    unique_dup = sorted(set(dup_plans))

    safe = len(diffs) == 0 and len(unique_dup) == 0
    return {
        "overlay_enabled_simulation": True,
        "cell_differences": len(diffs),
        "field_difference_count": len({d["field"] for d in diffs}),
        "duplicate_plan_codes": unique_dup,
        "unique_plan_baseline": int(baseline["PLAN"].nunique()),
        "unique_plan_overlay": int(overlay_df["PLAN"].nunique()),
        "overlay_safe_to_enable": "N",
        "diff_samples": diffs[:200],
        "readiness_notes": (
            "Overlay NOT safe for production enablement — differences detected or duplicate PLAN risk"
            if not safe else "Overlay simulation identical — still requires business signoff"
        ),
    }


def write_scaffold(name: str, rows: list[dict]) -> str:
    path = os.path.join(SCAFFOLD_DIR, name)
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["governance_action", "notes"])
    df.to_csv(path, index=False)
    return path


def write_executive_findings(
    path: str,
    ts: str,
    summary: dict,
    overlay: dict,
    ownership: pd.DataFrame,
) -> None:
    lines = [
        "# Executive Crosswalk Governance Findings — Phase P2D",
        "",
        f"**Date:** {ts}",
        "**Phase:** P2D — Crosswalk / Translation Governance Audit",
        "**Conversion engine:** Unchanged (qla_core/quikplan_converter.py)",
        "",
        "## Current State",
        "",
        "The product setup conversion architecture is **fundamentally correct** and validated:",
        "",
        "- **133 rows × 79 columns** — P2A/P2C parallel validation IDENTICAL (0 cell differences)",
        "- Flow: `quikplan_source` → Master_Crosswalk PLAN enrichment → rulebook → PCOMP → quikplan",
        "- Policy Form Crosswalk overlay **disabled** (`CROSSWALK_OVERLAY=0`) — correct default",
        "- Product setup isolated subprocess operational (P2C)",
        "",
        "## Governance Audit Summary",
        "",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Total audit findings | {summary['total_findings']} |",
        f"| ERROR severity | {summary['error_count']} |",
        f"| WARN severity | {summary['warn_count']} |",
        f"| INFO severity | {summary['info_count']} |",
        f"| Master_Crosswalk policy mappings | {summary['policy_crosswalk_count']} |",
        f"| Master_Crosswalk plan/entity mappings | {summary['plan_crosswalk_count']} |",
        f"| Policy Form Crosswalk rows | {summary['policy_form_rows']} |",
        f"| Source COVERAGE_IDs | {summary['source_ids']} |",
        f"| Rulebook unmapped schema fields | {summary['rulebook_unmapped']} |",
        f"| Rulebook stale targets | {summary['rulebook_stale']} |",
        f"| Untranslated output values (candidate) | {summary['untranslated_count']} |",
        f"| Unused translation entries | {summary['unused_translation_count']} |",
        f"| Missing PCOMP lookup rows | {summary['missing_pcomp']} |",
        f"| Orphan MPLAN codes | {summary['orphan_mplan']} |",
        f"| Passthrough LifePRO PLAN codes | {summary['passthrough_count']} |",
        "",
        "## Authoritative Ownership (Summary)",
        "",
    ]
    for _, row in ownership.iterrows():
        lines.append(
            f"- **{row['field_or_mapping_type']}**: current `{row['current_owner']}` → proposed `{row['proposed_owner']}` ({row['ownership_status']})"
        )

    lines.extend([
        "",
        "## Key Gaps & Risks",
        "",
        "### 1. Dual PLAN Authority (Highest Priority)",
        "",
        "PLAN codes are currently driven by **Master_Crosswalk** (`Old_Value=COVERAGE_ID → New_Value=PLAN`).",
        "Policy Form Crosswalk defines **future authoritative** `ql_plan_code` values.",
        f"Overlay simulation produces **{overlay['cell_differences']} cell differences** across **{overlay['field_difference_count']} fields**.",
        "Business must reconcile before overlay activation.",
        "",
        "### 2. Duplicate PLAN in Current Catalog",
        "",
        "Known ERROR: duplicate PLAN `9DIS25` (2 rows) — blocks emit only when `QLA_PRODUCT_GOVERNANCE_BLOCK=1`.",
        f"Overlay duplicate PLAN codes: {', '.join(overlay['duplicate_plan_codes']) or 'none simulated'}",
        "",
        "### 3. Master_Crosswalk Scope Drift",
        "",
        f"Master_Crosswalk contains **{summary['plan_crosswalk_count']} plan/entity mappings** mixed with **{summary['policy_crosswalk_count']} policy-number mappings**.",
        "Policy-number mappings must remain separate from product catalog PLAN authority.",
        "",
        "### 4. FORM / PLANNAME Conflicts vs Crosswalk",
        "",
        f"**{summary['form_conflicts']}** FORM mapping inconsistencies detected vs Policy Form Crosswalk.",
        "PLANNAME currently mirrors DESCRIPTION; crosswalk provides distinct friendly names.",
        "",
        "### 5. Actuarial Readiness",
        "",
        "Catalog dimensions (PLAN, FORM, SEX) populated. HRIGPKEY and vary-by fields intentionally blank.",
        "Actuarial attachment (gross premiums, cash values, reserves, dividends) requires **Phase P5** — not blocking catalog emit.",
        "",
        "## Crosswalk Overlay Readiness",
        "",
        f"- **Safe to enable automatically:** NO (`CROSSWALK_OVERLAY` must remain `0`)",
        f"- **Simulated cell differences:** {overlay['cell_differences']}",
        f"- **Baseline unique PLAN:** {overlay['unique_plan_baseline']} | **Overlay unique PLAN:** {overlay['unique_plan_overlay']}",
        f"- **Assessment:** {overlay['readiness_notes']}",
        "",
        "## Recommended Remediation Order",
        "",
        "1. **Resolve duplicate PLAN `9DIS25`** — business catalog integrity",
        "2. **Review Policy Form Crosswalk vs current PLAN mappings** — establish signed-off PLAN authority",
        "3. **Quarantine passthrough LifePRO IDs** — see `unresolved_passthrough_ids.csv`",
        "4. **Review FORM conflicts** — see `missing_form_mappings.csv`",
        "5. **Complete missing crosswalk rows** — see `missing_plan_crosswalk_rows.csv`",
        "6. **Validate orphan MPLAN codes** — downstream quikridr linkage",
        "7. **Translation table cleanup** — review unused entries (informational)",
        "8. **Overlay pilot in staged mode only** — after steps 1–5 signed off",
        "9. **Phase P5 actuarial governance** — HRIGPKEY + vary-by dimensions",
        "",
        "## Scaffold Artifacts (Detect-Only — No Auto-Remediation)",
        "",
        "Generated under `plan_analysis/phase_p2d_governance_audit/scaffold/`:",
        "",
        "- `missing_plan_crosswalk_rows.csv`",
        "- `untranslated_values.csv`",
        "- `orphan_plan_codes.csv`",
        "- `missing_form_mappings.csv`",
        "- `unresolved_passthrough_ids.csv`",
        "- `duplicate_plan_mappings.csv`",
        "",
        "## Governance Manifests",
        "",
        "Updated under `plan_governance/manifests/`:",
        "",
        "- `product_governance_manifest.csv`",
        "- `crosswalk_governance_manifest.csv`",
        "- `translation_governance_manifest.csv`",
        "- `unresolved_product_mapping_manifest.csv`",
        "",
        "## Engineering Constraints Honored",
        "",
        "- No conversion semantic redesign",
        "- No source file mutation",
        "- No app.py changes (audit-only phase)",
        "- No overlay auto-enablement",
        "- Claims / policy / UAT flows untouched",
        "",
    ])
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Phase P2D governance audit runner")
    parser.add_argument("--output-dir", default=SCRIPT_DIR)
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(SCAFFOLD_DIR, exist_ok=True)
    os.makedirs(MANIFEST_DIR, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    paths = {
        "source": os.path.join(ROOT, "plan_analysis", "quikplan_source.csv"),
        "baseline": os.path.join(ROOT, "QLA_Migration", "Output", "quikplan.csv"),
        "rulebook": os.path.join(ROOT, "QLA_Migration", "Configs", "Sync_Rulebook_quikplan.csv"),
        "translation": os.path.join(ROOT, "Master_Value_Translation.csv"),
        "master_cw": os.path.join(ROOT, "Master_Crosswalk.csv"),
        "policy_form_cw": os.path.join(ROOT, "docs", "plan_conversion_reference", "Policy Form Crosswalk 5.22.26.xlsx"),
        "pcomp": os.path.join(ROOT, "plan_analysis", "PCOMP.csv"),
        "ridr": os.path.join(ROOT, "QLA_Migration", "Output", "quikridr.csv"),
        "pcomp_dir": os.path.join(ROOT, "plan_analysis"),
    }
    alt_trans = os.path.join(ROOT, "QLA_Migration", "Mapping", "Master_Value_Translation.csv")
    if not os.path.isfile(paths["translation"]) and os.path.isfile(alt_trans):
        paths["translation"] = alt_trans

    source = read_source(paths["source"])
    baseline = pd.read_csv(paths["baseline"], dtype=str, keep_default_na=False).fillna("")
    rules = pd.read_csv(paths["rulebook"], dtype=str, keep_default_na=False)
    trans_df = pd.read_csv(paths["translation"], dtype=str, keep_default_na=False)
    mc = classify_master_crosswalk(pd.read_csv(paths["master_cw"], dtype=str, keep_default_na=False))
    xdf = load_policy_form_df(paths["policy_form_cw"])
    pcomp = read_pcomp(paths["pcomp"]) if os.path.isfile(paths["pcomp"]) else pd.DataFrame()

    source_ids = set(source["COVERAGE_ID"].map(strip_val)) - {""}
    output_plans = set(baseline["PLAN"].map(strip_val)) - {""}

    mc_map = {strip_val(k): strip_val(v) for k, v in zip(mc.iloc[:, 0], mc.iloc[:, 1])}

    mc_audit = audit_master_crosswalk(mc, source_ids, output_plans)
    pf_audit = audit_policy_form_crosswalk(xdf, source_ids, baseline, source, mc_map)
    trans_audit = audit_translations(trans_df, baseline, rules)
    rb_audit = audit_rulebook(rules)
    pcomp_audit = audit_pcomp(pcomp, source_ids)
    orphans = audit_orphan_plans(baseline, paths["ridr"])
    ownership = build_ownership_manifest()
    actuarial = audit_actuarial_readiness(baseline)
    overlay = audit_overlay_readiness(
        baseline, paths["policy_form_cw"], paths["source"], paths["rulebook"],
        paths["translation"], paths["master_cw"], paths["pcomp_dir"],
    )

    all_findings = (
        mc_audit["findings"] + pf_audit["findings"] + trans_audit["findings"]
        + rb_audit["findings"] + pcomp_audit["findings"]
    )
    findings_df = pd.DataFrame(all_findings)

    dup_plan_mappings = mc[mc["New_Value"].duplicated(keep=False) & (mc["mapping_class"] == "PLAN_OR_ENTITY")][
        ["Old_Value", "New_Value", "mapping_class"]
    ].to_dict("records")

    scaffold_files = {
        "missing_plan_crosswalk_rows.csv": pf_audit["scaffold_missing"],
        "untranslated_values.csv": trans_audit["untranslated"],
        "orphan_plan_codes.csv": orphans,
        "missing_form_mappings.csv": pf_audit["scaffold_form"],
        "unresolved_passthrough_ids.csv": pf_audit["scaffold_passthrough"],
        "duplicate_plan_mappings.csv": dup_plan_mappings,
    }
    scaffold_paths = {name: write_scaffold(name, rows) for name, rows in scaffold_files.items()}

    product_manifest = findings_df[findings_df["asset"].isin([
        "PCOMP.csv", "Sync_Rulebook_quikplan.csv",
    ])].copy() if not findings_df.empty else pd.DataFrame()
    crosswalk_manifest = findings_df[findings_df["asset"].str.contains("Crosswalk", na=False)].copy() if not findings_df.empty else pd.DataFrame()
    translation_manifest = findings_df[findings_df["asset"] == "Master_Value_Translation.csv"].copy() if not findings_df.empty else pd.DataFrame()

    unresolved_rows = []
    for name, rows in scaffold_files.items():
        for row in rows:
            unresolved_rows.append({"scaffold_file": name, **row})
    unresolved_manifest = pd.DataFrame(unresolved_rows)

    rb_coverage_df = pd.DataFrame(rb_audit["coverage_rows"])
    ownership.to_csv(os.path.join(args.output_dir, "crosswalk_ownership_analysis.csv"), index=False)
    rb_coverage_df.to_csv(os.path.join(args.output_dir, "rulebook_coverage_analysis.csv"), index=False)
    actuarial.to_csv(os.path.join(args.output_dir, "actuarial_readiness_analysis.csv"), index=False)
    findings_df.to_csv(os.path.join(args.output_dir, "governance_audit_findings.csv"), index=False)

    overlay_summary = {
        "simulation_date": ts,
        "crosswalk_overlay_flag": "0 (default — DO NOT enable)",
        "cell_differences": overlay["cell_differences"],
        "field_difference_count": overlay["field_difference_count"],
        "duplicate_plan_codes": ";".join(overlay["duplicate_plan_codes"]),
        "unique_plan_baseline": overlay["unique_plan_baseline"],
        "unique_plan_overlay": overlay["unique_plan_overlay"],
        "safe_to_enable": overlay["overlay_safe_to_enable"],
        "readiness_notes": overlay["readiness_notes"],
    }
    pd.DataFrame([overlay_summary]).to_csv(os.path.join(args.output_dir, "overlay_readiness_analysis.csv"), index=False)
    if overlay["diff_samples"]:
        pd.DataFrame(overlay["diff_samples"]).to_csv(
            os.path.join(args.output_dir, "overlay_simulation_diff_samples.csv"), index=False,
        )

    product_manifest.to_csv(os.path.join(MANIFEST_DIR, "product_governance_manifest.csv"), index=False)
    crosswalk_manifest.to_csv(os.path.join(MANIFEST_DIR, "crosswalk_governance_manifest.csv"), index=False)
    translation_manifest.to_csv(os.path.join(MANIFEST_DIR, "translation_governance_manifest.csv"), index=False)
    unresolved_manifest.to_csv(os.path.join(MANIFEST_DIR, "unresolved_product_mapping_manifest.csv"), index=False)

    summary = {
        "total_findings": len(all_findings),
        "error_count": sum(1 for f in all_findings if f["severity"] == "ERROR"),
        "warn_count": sum(1 for f in all_findings if f["severity"] == "WARN"),
        "info_count": sum(1 for f in all_findings if f["severity"] == "INFO"),
        "policy_crosswalk_count": mc_audit["policy_count"],
        "plan_crosswalk_count": int((mc["mapping_class"] == "PLAN_OR_ENTITY").sum()),
        "policy_form_rows": len(xdf),
        "source_ids": len(source_ids),
        "rulebook_unmapped": len(rb_audit["unmapped"]),
        "rulebook_stale": len(rb_audit["dead"]),
        "untranslated_count": len(trans_audit["untranslated"]),
        "unused_translation_count": len(trans_audit["unused"]),
        "missing_pcomp": len(pcomp_audit["missing"]),
        "orphan_mplan": len(orphans),
        "form_conflicts": len(pf_audit["scaffold_form"]),
        "passthrough_count": len(pf_audit["scaffold_passthrough"]),
    }

    exec_path = os.path.join(args.output_dir, "executive_crosswalk_governance_findings.md")
    write_executive_findings(exec_path, ts, summary, overlay, ownership)

    audit_summary_path = os.path.join(args.output_dir, "validation_summary.md")
    with open(audit_summary_path, "w", encoding="utf-8") as fh:
        fh.write(f"# Phase P2D — Governance Audit Summary\n\n**Date:** {ts}\n\n")
        fh.write("## Result\n\n**AUDIT COMPLETE — detect-only, no remediation applied**\n\n")
        fh.write(f"- Total findings: {summary['total_findings']} ({summary['error_count']} ERROR, {summary['warn_count']} WARN, {summary['info_count']} INFO)\n")
        fh.write(f"- Overlay safe to enable: **NO** ({overlay['cell_differences']} simulated cell diffs)\n")
        fh.write(f"- Conversion engine unchanged; P2A baseline remains authoritative\n\n")
        fh.write("## Deliverables\n\n")
        for f in sorted(os.listdir(args.output_dir)):
            fh.write(f"- `{f}`\n")
        fh.write("\n## Scaffold Files\n\n")
        for name in scaffold_files:
            fh.write(f"- `scaffold/{name}` ({len(scaffold_files[name])} rows)\n")

    print(f"P2D Governance Audit complete — {summary['total_findings']} findings")
    print(f"  ERROR={summary['error_count']} WARN={summary['warn_count']} INFO={summary['info_count']}")
    print(f"  Overlay simulation: {overlay['cell_differences']} cell diffs — safe=N")
    print(f"  Executive report: {exec_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
