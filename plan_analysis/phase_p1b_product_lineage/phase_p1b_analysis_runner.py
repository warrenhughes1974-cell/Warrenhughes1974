#!/usr/bin/env python3
"""
Phase P1B — Product Source Lineage + Dependency Analysis + Governance Scaffold.

Analysis and governance design ONLY. Does NOT modify app.py, conversion outputs,
or source extracts.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))
DEFAULT_OUTPUT = SCRIPT_DIR


def strip_val(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [strip_val(c) for c in df.columns]
    return df


def load_source_table(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", on_bad_lines="skip").fillna("")
    df = norm_cols(df)
    if "COVERAGE_ID" in df.columns:
        df = df[df["COVERAGE_ID"].str.match(r"^[0-9A-Za-z]", na=False)]
    return df


def load_crosswalk(path: str) -> pd.DataFrame:
    xwalk = pd.read_excel(path)
    xwalk.columns = [
        "lifepro_coverage_id",
        "unused",
        "ql_plan_code",
        "ql_form_number",
        "ql_plan_description",
        "ql_friendly_name",
    ]
    for col in xwalk.columns:
        xwalk[col] = xwalk[col].map(strip_val)
    return xwalk[xwalk["lifepro_coverage_id"] != "nan"]


def load_master_crosswalk(path: str) -> pd.DataFrame:
    cw = pd.read_csv(path, dtype=str, header=None, names=["old_value", "new_value"])
    cw["old_value"] = cw["old_value"].map(strip_val)
    cw["new_value"] = cw["new_value"].map(strip_val)
    return cw


def classify_component_type(comp_type: str) -> str:
    mapping = {
        "BA": "BASE_PLAN_CANDIDATE",
        "WP": "RIDER_WAIVER_PREMIUM",
        "AD": "RIDER_ACCIDENTAL_DEATH",
        "OR": "RIDER_OPTIONAL",
        "CR": "RIDER_CHILD",
        "GI": "RIDER_GUARANTEED_INSURABILITY",
        "BF": "RIDER_BENEFIT_FEATURE",
        "FR": "RIDER_FAMILY",
        "SC": "RIDER_SPECIAL",
        "SR": "RIDER_SPECIAL",
        "PS": "RIDER_PAID_UP_SPOUSE",
        "DI": "RIDER_DISABILITY",
    }
    return mapping.get(strip_val(comp_type), "UNKNOWN_COMPONENT")


def classify_exhibit(code: str) -> str:
    mapping = {
        "SUP": "SUPPLEMENTAL_COVERAGE",
        "WHO": "WHOLE_LIFE_BASE",
        "END": "ENDOWMENT_BASE",
        "OTD": "OTHER_TERM",
        "NPE": "NON_PAR_ENDOWMENT",
        "TPO": "TERM_PAID_UP",
        "OTI": "OTHER_TERM_ISSUE",
        "TPD": "TERM_PAID",
    }
    return mapping.get(strip_val(code), "UNCLASSIFIED_EXHIBIT")


def infer_qla_domain(
    comp_type: str,
    exhibit: str,
    max_as_rider: str,
    description: str,
) -> str:
    ct = strip_val(comp_type)
    ex = strip_val(exhibit)
    desc = strip_val(description).upper()
    if ct == "BA" or ex in {"WHO", "END", "NPE"}:
        return "QUIKPLAN_BASE"
    if ct in {"WP", "AD", "CR", "GI", "BF", "FR", "SC", "SR", "PS", "DI", "OR"}:
        return "QUIKRIDR_RIDER"
    if strip_val(max_as_rider) not in {"", "0"}:
        return "QUIKRIDR_RIDER"
    if "RIDER" in desc or "WAIVER" in desc or "ADB" in desc:
        return "QUIKRIDR_RIDER"
    if ex == "SUP":
        return "SEMANTIC_REVIEW_SUPPLEMENTAL"
    return "SEMANTIC_REVIEW_REQUIRED"


def build_dependency_map(ridr: pd.DataFrame, rulebooks: dict, key_defs: dict) -> pd.DataFrame:
    rows = []
    mplan_counts = ridr["MPLAN"].map(strip_val).value_counts()
    blank_mplan = int(mplan_counts.get("", 0))

    static_deps = [
        ("quikridr", "MPLAN", "quikplan", "PLAN", "FK_REFERENCE", "ERROR",
         "Every policy phase references a plan code; orphan MPLAN breaks rider linkage."),
        ("quikactg", "MPLAN", "quikplan", "PLAN", "FK_REFERENCE", "HIGH",
         "Accounting transaction rows carry plan code via PACTG.PLAN_CODE + Master_Crosswalk."),
        ("quikplan", "PLAN", "validation_config", "key_definitions.plan", "PRIMARY_KEY", "ERROR",
         "PLAN is the sole uniqueness key for quikplan validation."),
        ("quikplan", "FORM", "QLAdmin", "PolicyForm", "BUSINESS_REFERENCE", "HIGH",
         "FORM identifies policy form; must align with crosswalk QL Form Number."),
        ("quikplan", "PLANNAME", "QLAdmin", "DisplayName", "BUSINESS_REFERENCE", "MEDIUM",
         "Friendly display name; crosswalk QL Friendly Name is business authority."),
        ("quikplan", "DESCR", "QLAdmin", "PlanDescription", "BUSINESS_REFERENCE", "MEDIUM",
         "Plan description shown in QLAdmin screens."),
        ("quikplan", "PLANTYPE", "QLAdmin", "PlanType", "BUSINESS_REFERENCE", "HIGH",
         "Currently blank in output; QLAdmin expects plan type classification."),
        ("quikplan", "HRIGPKEY", "QuikPlbd", "RateLookupKey", "FUTURE_ACTUARIAL", "CRITICAL",
         "Logical gross premium rate lookup; not populated yet."),
        ("quikplan", "UWVARY*", "QuikPlbd", "UWClassVary", "FUTURE_ACTUARIAL", "HIGH",
         "Underwriting class vary-by dimension for rate attachment."),
        ("quikplan", "BDVARY*", "QuikPlbd", "BandVary", "FUTURE_ACTUARIAL", "HIGH",
         "Band vary-by dimension; QuikPlbd index key includes PLAN + BDCODE."),
        ("quikplan", "STVARY*", "QuikPlbd", "StateVary", "FUTURE_ACTUARIAL", "HIGH",
         "State/country vary-by dimension for rate tables."),
        ("quikplan", "GDVARY*", "QuikPlbd", "GenderVary", "FUTURE_ACTUARIAL", "HIGH",
         "Gender vary-by dimension for rate tables."),
        ("quikplan", "MINUNIT/MAXUNIT", "PCOMP", "IssueAmounts", "LOOKUP_JOIN", "MEDIUM",
         "Rulebook joins PCOMP on COVERAGE_ID for unit limits."),
        ("quikridr", "MPHASE", "BusinessRule", "MPHASE=1 base", "BUSINESS_RULE", "CRITICAL",
         "Confirmed: MPHASE 1 = base coverage; riders use MPHASE > 1."),
        ("quikmstr", "MPOLICY", "quikridr", "MPOLICY", "INDIRECT", "MEDIUM",
         "Policy master indirectly depends on plan catalog via quikridr MPLAN."),
        ("DBF_generation", "PLAN", "quikplan.csv", "PLAN", "UAT_EMIT", "HIGH",
         "UAT DBF generation reads final emitted quikplan.csv."),
        ("Master_Crosswalk.csv", "Old_Value", "quikplan/quikridr", "PLAN/MPLAN", "LEGACY_MAPPING", "CRITICAL",
         "Currently contains ~240 plan mappings mixed with policy mappings — governance risk."),
    ]

    for consumer_table, consumer_field, provider_table, provider_field, dep_type, severity, notes in static_deps:
        affected_rows = ""
        if consumer_field == "MPLAN":
            affected_rows = str(len(ridr))
        rows.append({
            "dependency_id": f"DEP-{consumer_table}-{consumer_field}",
            "consumer_table": consumer_table,
            "consumer_field": consumer_field,
            "provider_table": provider_table,
            "provider_field": provider_field,
            "dependency_type": dep_type,
            "severity_if_changed": severity,
            "notes": notes,
            "affected_row_count": affected_rows,
        })

    for plan, count in mplan_counts.items():
        if not plan:
            continue
        rows.append({
            "dependency_id": f"DEP-MPLAN-USAGE-{plan}",
            "consumer_table": "quikridr",
            "consumer_field": "MPLAN",
            "provider_table": "quikplan",
            "provider_field": "PLAN",
            "dependency_type": "RUNTIME_USAGE",
            "severity_if_changed": "HIGH" if count > 100 else "MEDIUM",
            "notes": f"MPLAN={plan} referenced by {count} quikridr rows.",
            "affected_row_count": str(count),
        })

    rows.append({
        "dependency_id": "DEP-MPLAN-BLANK",
        "consumer_table": "quikridr",
        "consumer_field": "MPLAN",
        "provider_table": "quikplan",
        "provider_field": "PLAN",
        "dependency_type": "DATA_QUALITY",
        "severity_if_changed": "HIGH",
        "notes": "Blank MPLAN rows cannot resolve to quikplan.",
        "affected_row_count": str(blank_mplan),
    })

    for rb_name, rb_path in rulebooks.items():
        if os.path.isfile(rb_path):
            rb = pd.read_csv(rb_path, dtype=str)
            rb.columns = [strip_val(c) for c in rb.columns]
            target_col = "Target_Field" if "Target_Field" in rb.columns else ""
            source_col = "Source_Field" if "Source_Field" in rb.columns else ""
            if target_col:
                for _, rule in rb.iterrows():
                    tf = strip_val(rule.get(target_col, ""))
                    sf = strip_val(rule.get(source_col, "")) if source_col else ""
                    if tf in {"PLAN", "MPLAN", "FORM", "PLANNAME", "PLANTYPE", "HRIGPKEY"} or "VARY" in tf:
                        rows.append({
                            "dependency_id": f"DEP-RB-{rb_name}-{tf}-{sf}",
                            "consumer_table": rb_name.replace("Sync_Rulebook_", ""),
                            "consumer_field": tf,
                            "provider_table": sf or "DEFAULT/RULEBOOK",
                            "provider_field": sf or "Default_Value",
                            "dependency_type": "RULEBOOK_ROUTING",
                            "severity_if_changed": "HIGH",
                            "notes": strip_val(rule.get("Transformation_Note", "")),
                            "affected_row_count": "",
                        })

    if key_defs.get("quikplan"):
        for kd in key_defs["quikplan"]:
            rows.append({
                "dependency_id": f"DEP-KEY-{kd.get('name', 'plan')}",
                "consumer_table": "validation_pipeline",
                "consumer_field": ",".join(kd.get("fields", [])),
                "provider_table": "quikplan",
                "provider_field": "PLAN",
                "dependency_type": "VALIDATION_KEY",
                "severity_if_changed": kd.get("severity", "ERROR"),
                "notes": "Defined in validation_config/key_definitions.json",
                "affected_row_count": "",
            })

    dep_df = pd.DataFrame(rows).drop_duplicates(subset=["dependency_id"])
    return dep_df


def build_semantic_workbench(src: pd.DataFrame, pcomp: pd.DataFrame, out: pd.DataFrame, ridr: pd.DataFrame) -> pd.DataFrame:
    src = src.copy()
    src["COVERAGE_ID_N"] = src["COVERAGE_ID"].map(strip_val)
    pcomp = pcomp.copy()
    pcomp["COVERAGE_ID_N"] = pcomp["COVERAGE_ID"].map(strip_val)

    pcomp_agg = pcomp.groupby("COVERAGE_ID_N").agg({
        "COMPONENT_TYPE": lambda s: strip_val(s.iloc[0]) if len(s) else "",
        "COMPONENT_NUMBER": "count",
        "END_DATE": lambda s: strip_val(s.iloc[0]) if len(s) else "",
    }).reset_index()
    pcomp_agg.columns = ["COVERAGE_ID_N", "COMPONENT_TYPE", "PCOMP_COMPONENT_COUNT", "PCOMP_END_DATE"]

    out_map = {}
    for _, row in out.iterrows():
        plan = strip_val(row.get("PLAN", ""))
        out_map[plan] = row

    src_to_out = {}
    for _, row in out.iterrows():
        # reverse lookup not trivial; we'll join via crosswalk later in lineage
        pass

    ridr_usage = ridr.groupby(ridr["MPLAN"].map(strip_val)).agg(
        ridr_row_count=("MPLAN", "size"),
        mphases=("MPHASE", lambda s: "|".join(sorted(set(strip_val(v) for v in s if strip_val(v))))),
        base_phase_rows=("MPHASE", lambda s: int(sum(strip_val(v) == "1" for v in s))),
        rider_phase_rows=("MPHASE", lambda s: int(sum(strip_val(v) not in {"", "1"} for v in s))),
    ).reset_index()
    ridr_usage.columns = ["PLAN_OR_MPLAN", "RIDR_ROW_COUNT", "MPHASE_VALUES", "MPHASE1_ROWS", "MPHASE_GT1_ROWS"]

    rows = []
    for _, srow in src.iterrows():
        cid = strip_val(srow["COVERAGE_ID"])
        desc = strip_val(srow.get("DESCRIPTION", ""))
        exhibit = strip_val(srow.get("EXHIBIT_CODE", ""))
        plan_type = strip_val(srow.get("PLAN_TYPE", ""))
        max_rider = strip_val(srow.get("MAX_ISSUE_AS_RIDER", ""))
        form = strip_val(srow.get("POLICY_FORM_NUM", ""))

        pc = pcomp_agg[pcomp_agg["COVERAGE_ID_N"] == cid]
        comp_type = strip_val(pc.iloc[0]["COMPONENT_TYPE"]) if not pc.empty else ""
        comp_count = int(pc.iloc[0]["PCOMP_COMPONENT_COUNT"]) if not pc.empty else 0

        # Find output row: PLAN may be QL code; check if any out row DESCR matches
        out_matches = out[out["DESCR"].str.upper().str.strip() == desc.upper()]
        emitted_plan = strip_val(out_matches.iloc[0]["PLAN"]) if not out_matches.empty else ""
        emitted_form = strip_val(out_matches.iloc[0]["FORM"]) if not out_matches.empty else ""

        ridr_match = ridr_usage[
            (ridr_usage["PLAN_OR_MPLAN"] == cid) | (ridr_usage["PLAN_OR_MPLAN"] == emitted_plan)
        ]
        ridr_rows = int(ridr_match["RIDR_ROW_COUNT"].sum()) if not ridr_match.empty else 0
        mph1 = int(ridr_match["MPHASE1_ROWS"].sum()) if not ridr_match.empty else 0
        mph_gt1 = int(ridr_match["MPHASE_GT1_ROWS"].sum()) if not ridr_match.empty else 0

        qla_domain = infer_qla_domain(comp_type, exhibit, max_rider, desc)
        collision = ""
        if qla_domain == "QUIKPLAN_BASE" and mph_gt1 > mph1 and ridr_rows > 0:
            collision = "BASE_CLASSIFICATION_BUT_RIDER_PHASES_PRESENT"
        elif qla_domain == "QUIKRIDR_RIDER" and mph1 > 0 and mph_gt1 == 0 and ridr_rows > 0:
            collision = "RIDER_CLASSIFICATION_BUT_ONLY_MPHASE1_USAGE"
        elif emitted_plan and emitted_plan == cid:
            collision = "PLAN_ID_NOT_QL_CODE_TRANSFORMED"

        risk = "LOW"
        if collision:
            risk = "HIGH"
        elif qla_domain.startswith("SEMANTIC"):
            risk = "MEDIUM"

        rows.append({
            "lifepro_coverage_id": cid,
            "description": desc,
            "policy_form_num": form,
            "exhibit_code": exhibit,
            "exhibit_classification": classify_exhibit(exhibit),
            "plan_type_lifepro": plan_type,
            "max_issue_as_rider": max_rider,
            "pcomp_component_type": comp_type,
            "pcomp_component_classification": classify_component_type(comp_type),
            "pcomp_component_count": comp_count,
            "recommended_qla_domain": qla_domain,
            "current_output_plan": emitted_plan,
            "current_output_form": emitted_form,
            "quikridr_reference_count": ridr_rows,
            "quikridr_mphase1_rows": mph1,
            "quikridr_mphase_gt1_rows": mph_gt1,
            "semantic_collision_flag": collision or "NONE",
            "review_priority": risk,
            "business_review_notes": (
                "Confirm whether this LifePRO coverage belongs in QuikPlan (catalog) "
                "vs QuikRidr (issued rider) before any crosswalk integration."
            ),
        })

    return pd.DataFrame(rows)


def build_authority_analysis(
    src: pd.DataFrame,
    pcomp: pd.DataFrame,
    out: pd.DataFrame,
    xwalk: pd.DataFrame,
    master_cw: pd.DataFrame,
) -> pd.DataFrame:
    mcw_map = dict(zip(master_cw["old_value"], master_cw["new_value"]))
    rows = []

    field_specs = [
        ("PLAN", "ql_plan_code", "COVERAGE_ID", "Master_Crosswalk New_Value / COVERAGE_ID direct",
         "Policy Form Crosswalk QL Plan Code"),
        ("FORM", "ql_form_number", "POLICY_FORM_NUM", "LifePRO POLICY_FORM_NUM via rulebook",
         "Policy Form Crosswalk QL Form Number"),
        ("DESCR", "ql_plan_description", "DESCRIPTION", "LifePRO DESCRIPTION via rulebook",
         "Policy Form Crosswalk QL Plan Description"),
        ("PLANNAME", "ql_friendly_name", "DESCRIPTION", "LifePRO DESCRIPTION duplicated as PLANNAME",
         "Policy Form Crosswalk QL Friendly Name"),
    ]

    xwalk_by_lifepro = xwalk.set_index("lifepro_coverage_id").to_dict("index")
    xwalk_by_ql = xwalk.set_index("ql_plan_code").to_dict("index")

    for _, orow in out.iterrows():
        plan = strip_val(orow["PLAN"])
        form = strip_val(orow["FORM"])
        descr = strip_val(orow["DESCR"])
        planname = strip_val(orow["PLANNAME"])

        lifepro_id = ""
        for cid, mapped in mcw_map.items():
            if mapped == plan:
                lifepro_id = cid
                break
        if not lifepro_id and plan in xwalk_by_lifepro:
            lifepro_id = plan

        xw = xwalk_by_ql.get(plan) or xwalk_by_lifepro.get(plan) or xwalk_by_lifepro.get(lifepro_id, {})
        if not xw and lifepro_id:
            xw = xwalk_by_lifepro.get(lifepro_id, {})

        src_row = src[src["COVERAGE_ID"].map(strip_val) == strip_val(lifepro_id)] if lifepro_id else pd.DataFrame()
        if src_row.empty:
            src_row = src[src["DESCRIPTION"].str.upper().str.strip() == descr.upper()]
        s = src_row.iloc[0].to_dict() if not src_row.empty else {}

        for target_field, xwalk_field, source_field, current_authority, proposed_authority in field_specs:
            current_val = strip_val(orow.get(target_field, ""))
            xwalk_val = strip_val(xw.get(xwalk_field, "")) if xw else ""
            source_val = strip_val(s.get(source_field, "")) if s else ""
            if source_field == "DESCRIPTION":
                source_val = strip_val(s.get("DESCRIPTION", ""))

            match_xwalk = current_val.upper() == xwalk_val.upper() if xwalk_val else False
            match_source = current_val.upper() == source_val.upper() if source_val else False

            if not xwalk_val and not source_val:
                precedence = "UNRESOLVED"
                conflict = "MISSING_AUTHORITY"
            elif match_xwalk and not match_source:
                precedence = "CROSSWALK_ALIGNED"
                conflict = "SOURCE_DIVERGENT"
            elif match_source and not match_xwalk:
                precedence = "SOURCE_ALIGNED"
                conflict = "CROSSWALK_DIVERGENT"
            elif match_xwalk and match_source:
                precedence = "ALIGNED"
                conflict = "NONE"
            else:
                precedence = "CONFLICT"
                conflict = "CROSSWALK_AND_SOURCE_DIVERGENT"

            if target_field == "PLAN":
                if plan in xwalk_by_ql:
                    recommended = "Policy Form Crosswalk QL Plan Code"
                elif plan in xwalk_by_lifepro:
                    recommended = "LifePRO COVERAGE_ID (legacy passthrough — requires remediation)"
                else:
                    recommended = proposed_authority
            elif target_field == "FORM" and not match_xwalk and xwalk_val:
                recommended = "Policy Form Crosswalk QL Form Number (override LifePRO form)"
            else:
                recommended = proposed_authority

            rows.append({
                "output_plan": plan,
                "lifepro_coverage_id": lifepro_id or (plan if plan in xwalk_by_lifepro else ""),
                "target_field": target_field,
                "current_output_value": current_val,
                "crosswalk_authoritative_value": xwalk_val,
                "lifepro_source_value": source_val,
                "current_logic_authority": current_authority,
                "recommended_authority": recommended,
                "alignment_status": precedence,
                "conflict_flag": conflict,
                "governance_action": "BUSINESS_REVIEW" if conflict != "NONE" else "CONFIRMED",
            })

    # Unmapped source rows not in output
    emitted_lifepro = {strip_val(r["lifepro_coverage_id"]) for r in rows if strip_val(r.get("lifepro_coverage_id"))}
    for _, srow in src.iterrows():
        cid = strip_val(srow["COVERAGE_ID"])
        if cid in emitted_lifepro:
            continue
        rows.append({
            "output_plan": "",
            "lifepro_coverage_id": cid,
            "target_field": "PLAN",
            "current_output_value": "",
            "crosswalk_authoritative_value": strip_val(
                xwalk_by_lifepro.get(cid, {}).get("ql_plan_code", "")
            ),
            "lifepro_source_value": cid,
            "current_logic_authority": "NOT_EMITTED",
            "recommended_authority": "Policy Form Crosswalk QL Plan Code",
            "alignment_status": "UNMAPPED",
            "conflict_flag": "SOURCE_NOT_IN_OUTPUT",
            "governance_action": "HOLD_UNMAPPED_PLAN",
        })

    return pd.DataFrame(rows)


def build_rate_attachment_analysis(out: pd.DataFrame, rulebook: pd.DataFrame) -> pd.DataFrame:
    vary_cols = [c for c in out.columns if "VARY" in c.upper()]
    rows = []
    for col in vary_cols:
        nonblank = int((out[col].map(strip_val) != "").sum())
        unique_vals = sorted(set(out[col].map(strip_val)) - {""})
        rows.append({
            "field_name": col,
            "field_group": col[:6],
            "qla_purpose": {
                "UWVARY": "Underwriting class vary-by for gross premium rates",
                "BDVARY": "Band vary-by; QuikPlbd keyed by PLAN + BDCODE",
                "STVARY": "State/country vary-by for rate tables",
                "GDVARY": "Gender vary-by for rate tables",
            }.get(col[:6], "Vary-by dimension"),
            "current_populated_rows": nonblank,
            "total_plan_rows": len(out),
            "unique_values": "|".join(unique_vals[:20]),
            "hrigpkey_required": "Y" if col.startswith(("UW", "BD", "ST", "GD")) else "N",
            "implementation_status": "NOT_IMPLEMENTED" if col == "HRIGPKEY" else (
                "PARTIAL_DEFAULT" if nonblank == len(out) and len(unique_vals) <= 2 else "REVIEW"
            ),
            "future_dependency": "QuikPlbd rate load; reserve/dividend tables",
            "governance_note": "Do NOT populate HRIGPKEY until plan catalog governance signoff.",
        })

    rows.append({
        "field_name": "HRIGPKEY",
        "field_group": "HRIGPKEY",
        "qla_purpose": "Logical indicator for gross premium rate lookup in QuikPlbd",
        "current_populated_rows": int((out["HRIGPKEY"].map(strip_val) != "").sum()),
        "total_plan_rows": len(out),
        "unique_values": "",
        "hrigpkey_required": "Y",
        "implementation_status": "NOT_IMPLEMENTED",
        "future_dependency": "All gross premium rate attachment",
        "governance_note": "Requires deterministic PLAN + vary-by + actuarial load strategy.",
    })

    rb_vary = rulebook[rulebook["Target_Field"].str.contains("VARY|HRIGPKEY", na=False)]
    for _, rule in rb_vary.iterrows():
        tf = strip_val(rule["Target_Field"])
        if tf == "HRIGPKEY":
            continue
        if any(r["field_name"] == tf for r in rows):
            continue
        rows.append({
            "field_name": tf,
            "field_group": tf[:6],
            "qla_purpose": "Rulebook default routing",
            "current_populated_rows": int((out[tf].map(strip_val) != "").sum()) if tf in out.columns else 0,
            "total_plan_rows": len(out),
            "unique_values": "",
            "hrigpkey_required": "Y",
            "implementation_status": "RULEBOOK_DEFAULT_ONLY",
            "future_dependency": "QuikPlbd",
            "governance_note": strip_val(rule.get("Default_Value", "")),
        })

    return pd.DataFrame(rows)


def build_effective_date_governance(src: pd.DataFrame, pcomp: pd.DataFrame, xwalk: pd.DataFrame, out: pd.DataFrame) -> pd.DataFrame:
    rows = []
    dup_plans = out[out.duplicated("PLAN", keep=False)]["PLAN"].tolist()
    for plan in sorted(set(dup_plans)):
        matches = out[out["PLAN"] == plan]
        rows.append({
            "governance_topic": "DUPLICATE_PLAN_CODE",
            "entity_key": plan,
            "entity_type": "QL_PLAN_CODE",
            "effective_date_signal": "",
            "risk_level": "CRITICAL",
            "overlap_count": len(matches),
            "notes": "Duplicate PLAN in quikplan output breaks primary key validation.",
            "recommended_hold_category": "DUPLICATE_PLAN",
        })

    form_groups = out.groupby("FORM")["PLAN"].nunique()
    for form, plan_count in form_groups.items():
        if plan_count > 5:
            rows.append({
                "governance_topic": "FORM_COLLISION",
                "entity_key": strip_val(form),
                "entity_type": "FORM",
                "effective_date_signal": "",
                "risk_level": "MEDIUM",
                "overlap_count": int(plan_count),
                "notes": f"FORM {form} maps to {plan_count} distinct PLAN codes.",
                "recommended_hold_category": "FORM_COLLISION_REVIEW",
            })

    xwalk_dups = xwalk[xwalk.duplicated("ql_plan_code", keep=False)]
    for code in sorted(set(xwalk_dups["ql_plan_code"].tolist())):
        rows.append({
            "governance_topic": "CROSSWALK_DUPLICATE_QL_CODE",
            "entity_key": code,
            "entity_type": "QL_PLAN_CODE",
            "effective_date_signal": "",
            "risk_level": "HIGH",
            "overlap_count": int((xwalk["ql_plan_code"] == code).sum()),
            "notes": "Duplicate QL plan code in crosswalk would break deterministic mapping.",
            "recommended_hold_category": "CROSSWALK_CONFLICT",
        })

    for _, srow in src.iterrows():
        cid = strip_val(srow["COVERAGE_ID"])
        mod_date = strip_val(srow.get("MOD_DATE", ""))
        status = strip_val(srow.get("STATUS_CODE", ""))
        pc = pcomp[pcomp["COVERAGE_ID"].map(strip_val) == cid]
        end_date = strip_val(pc.iloc[0]["END_DATE"]) if not pc.empty else ""
        rows.append({
            "governance_topic": "PRODUCT_VERSION_LINEAGE",
            "entity_key": cid,
            "entity_type": "LIFEPRO_COVERAGE_ID",
            "effective_date_signal": mod_date or end_date,
            "risk_level": "MEDIUM" if status != "A" else "LOW",
            "overlap_count": 1,
            "notes": (
                f"Status={status or 'unknown'}; PCOMP END_DATE={end_date or 'unknown'}. "
                "Crosswalk has no effective-date dimension — grandfathering risk."
            ),
            "recommended_hold_category": "EFFECTIVE_DATE_REVIEW" if status != "A" else "",
        })

    rows.append({
        "governance_topic": "MISSING_EFFECTIVE_DATE_IN_CROSSWALK",
        "entity_key": "Policy Form Crosswalk 5.22.26",
        "entity_type": "CROSSWALK",
        "effective_date_signal": "NONE",
        "risk_level": "HIGH",
        "overlap_count": len(xwalk),
        "notes": "Crosswalk is not versioned by effective date; superseded forms cannot be distinguished.",
        "recommended_hold_category": "CROSSWALK_VERSIONING_GAP",
    })

    return pd.DataFrame(rows)


def build_lineage(
    src: pd.DataFrame,
    pcomp: pd.DataFrame,
    out: pd.DataFrame,
    xwalk: pd.DataFrame,
    master_cw: pd.DataFrame,
    ridr: pd.DataFrame,
) -> pd.DataFrame:
    mcw_map = dict(zip(master_cw["old_value"], master_cw["new_value"]))
    xwalk_lp = xwalk.set_index("lifepro_coverage_id").to_dict("index")

    ridr_counts = ridr.groupby(ridr["MPLAN"].map(strip_val)).size().to_dict()

    rows = []
    for _, srow in src.iterrows():
        cid = strip_val(srow["COVERAGE_ID"])
        desc = strip_val(srow.get("DESCRIPTION", ""))
        form_src = strip_val(srow.get("POLICY_FORM_NUM", ""))

        xw = xwalk_lp.get(cid, {})
        ql_plan = strip_val(xw.get("ql_plan_code", ""))
        ql_form = strip_val(xw.get("ql_form_number", ""))
        mcw_plan = strip_val(mcw_map.get(cid, ""))

        out_row = out[out["PLAN"].map(strip_val).isin({ql_plan, mcw_plan, cid})]
        if out_row.empty:
            out_row = out[out["DESCR"].str.upper().str.strip() == desc.upper()]
        oplan = strip_val(out_row.iloc[0]["PLAN"]) if not out_row.empty else ""
        oform = strip_val(out_row.iloc[0]["FORM"]) if not out_row.empty else ""
        odescr = strip_val(out_row.iloc[0]["DESCR"]) if not out_row.empty else ""

        lineage_path = "LifePRO quikplan_source -> "
        if cid in xwalk_lp:
            lineage_path += "Policy Form Crosswalk -> "
        if mcw_plan:
            lineage_path += "Master_Crosswalk (legacy plan map) -> "
        lineage_path += "Sync_Rulebook_quikplan -> output/quikplan.csv"

        ridr_n = ridr_counts.get(oplan, 0) + ridr_counts.get(cid, 0)

        rows.append({
            "lifepro_coverage_id": cid,
            "lifepro_description": desc,
            "lifepro_form": form_src,
            "crosswalk_ql_plan_code": ql_plan,
            "crosswalk_ql_form": ql_form,
            "master_crosswalk_plan_map": mcw_plan,
            "pcomp_match": "Y" if cid in set(pcomp["COVERAGE_ID"].map(strip_val)) else "N",
            "rulebook_source_fields": "COVERAGE_ID->PLAN; POLICY_FORM_NUM->FORM; DESCRIPTION->DESCR/PLANNAME",
            "output_plan": oplan,
            "output_form": oform,
            "output_descr": odescr,
            "plan_transform_method": (
                "QL_CROSSWALK" if oplan == ql_plan else
                "MASTER_CROSSWALK" if oplan == mcw_plan else
                "PASSTHROUGH" if oplan == cid else
                "UNRESOLVED"
            ),
            "quikridr_mplan_dependency_count": ridr_n,
            "lineage_path": lineage_path,
            "lineage_integrity": "OK" if oplan else "NOT_EMITTED",
        })

    # orphan MPLAN not in source
    out_plans = set(out["PLAN"].map(strip_val))
    for mplan, count in ridr_counts.items():
        if not mplan or mplan in out_plans:
            continue
        rows.append({
            "lifepro_coverage_id": "",
            "lifepro_description": "",
            "lifepro_form": "",
            "crosswalk_ql_plan_code": "",
            "crosswalk_ql_form": "",
            "master_crosswalk_plan_map": mplan,
            "pcomp_match": "",
            "rulebook_source_fields": "quikridr.PLAN_CODE->MPLAN",
            "output_plan": mplan,
            "output_form": "",
            "output_descr": "",
            "plan_transform_method": "RIDR_ONLY_ORPHAN",
            "quikridr_mplan_dependency_count": count,
            "lineage_path": "quikridr PLAN_CODE -> MPLAN (no quikplan catalog row)",
            "lineage_integrity": "ORPHAN_MPLAN",
        })

    return pd.DataFrame(rows)


def write_governance_model(path: str) -> None:
    content = """# Proposed Product Governance Model (Phase P1B — Design Only)

## Purpose

Mirror the claims conversion governance pattern: **hold, review, replay, emit** — never silent exclusion or auto-remediation of semantic conflicts.

## Governance Principles

1. Honor confirmed business decisions (MPHASE 1 = base; riders MPHASE > 1).
2. Policy Form Crosswalk 5.22.26 is the business authority for PLAN, FORM, DESCR, PLANNAME — once join key is confirmed.
3. Master_Crosswalk.csv must remain **policy-number authority only**; plan mappings currently embedded (~240 rows) require segregation before production.
4. No HRIGPKEY population or actuarial load until plan catalog is governance-cleared.
5. All holds are reversible via manifest + rollback flag (pattern: `QLA_PRODUCT_GOVERNANCE_HOLD=0`).

## Hold Categories

| Hold Category | Trigger | Review Owner | Emit Behavior |
|---|---|---|---|
| UNMAPPED_PLAN | LifePRO COVERAGE_ID absent from Policy Form Crosswalk | Product / Actuarial | Block quikplan row emit |
| DUPLICATE_PLAN | Duplicate PLAN primary key in staged quikplan | Product | Block affected rows |
| INVALID_FORM | FORM blank or not in crosswalk QL Form Number | Product | Hold row; allow base plan review |
| ORPHAN_RIDER | quikridr.MPLAN not in quikplan.PLAN | Conversion / Product | Hold dependent quikridr rows |
| MISSING_HRIGPKEY | Rate attachment attempted without HRIGPKEY strategy | Actuarial | Block actuarial phase only |
| INVALID_VARYBY | Inconsistent UWVARY/BDVARY/STVARY/GDVARY combination | Actuarial | Hold plan row for rate prep |
| CROSSWALK_CONFLICT | Crosswalk vs source vs output divergence | Product | Hold; business review workbench |
| SEMANTIC_CLASSIFICATION_CONFLICT | Base vs rider vs supplemental ambiguity | Product | Hold; semantic workbench |
| LEGACY_MASTER_CROSSWALK_PLAN | Plan mapping sourced from Master_Crosswalk | Architecture | Hold until segregated |
| EFFECTIVE_DATE_OVERLAP | Superseded form/plan without version key | Product / Compliance | Hold pending version decision |

## Manifest Pattern (Proposed)

`plan_governance/manifests/product_review_hold_manifest.csv`

Columns aligned to claims governance:
- hold_category, lifepro_coverage_id, output_plan, target_field
- source_value, crosswalk_value, current_output_value
- governance_status, business_review_required, remediation_recommendation
- rulebook_lineage, audit_timestamp, rollback_flag

## Replay Model

1. Analyst updates crosswalk or business decision record (not source extracts).
2. Re-run isolated product runner (`phase_p1c+`) against frozen `plan_analysis/quikplan_source.csv`.
3. Diff staged vs prior manifest; append governance delta summary.
4. Business signoff gate before merge to `output/quikplan.csv`.

## Rollback Model

- Staged outputs under `plan_governance/staged/` never overwrite production output directly.
- app.py Product tab emits only governance-cleared rows.
- Rollback = restore prior manifest + prior staged CSV snapshot.

## Relationship to Claims Governance

Product governance is **upstream** of claims/policy conversion:
- quikridr.MPLAN → quikplan.PLAN
- quikactg.MPLAN → quikplan.PLAN
- Orphan plan catalog breaks policy phase linkage and downstream validation

Do NOT alter claims orchestration; product runner remains isolated subprocess.
"""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def write_folder_structure(path: str) -> None:
    content = """# Recommended Plan Governance Folder Structure

## Recommendation

Create `plan_governance/` parallel to `claims_analysis/`, with `plan_analysis/` retained as the **read-only authoritative source analysis zone**.

```
plan_analysis/                          # Frozen source extracts + analysis inputs
  quikplan_source.csv                   # PRIMARY product lineage source (authoritative)
  PCOMP.csv                             # Component attributes lookup
  phase_p1b_product_lineage/            # Phase P1B deliverables (this phase)
  README.md                             # Source lineage documentation

plan_governance/                        # Operational governance (future phases)
  config/
    product_governance_rules.json
    semantic_classification_rules.json
    plan_crosswalk_authority_rules.json
  manifests/
    product_review_hold_manifest.csv
    product_governance_delta_summary.txt
  staged/
    quikplan_staged.csv
    quikridr_plan_dependency_report.csv
  workbench/
    product_semantic_classification_workbench.csv  # synced from analysis
    plan_crosswalk_review_queue.csv
  phase_p1c_crosswalk_validation/       # Next phase: join-key proof
  phase_p2_product_runner/              # Isolated conversion runner
  logs/
    product_runner_audit.log
  replay/
    snapshots/                          # Timestamped rollback snapshots

docs/plan_conversion_reference/
  Policy Form Crosswalk 5.22.26.xlsx    # Business authority (versioned)
```

## Rationale

| Zone | Purpose |
|---|---|
| `plan_analysis/` | Discovery, lineage, read-only source analysis — no production emit |
| `plan_governance/` | Holds, manifests, staged emit, replay — mirrors claims_analysis |
| `docs/plan_conversion_reference/` | Business-owned crosswalk artifacts with version dates |

## Manifests

- `product_review_hold_manifest.csv` — active holds blocking emit
- `product_dependency_manifest.json` — machine-readable dependency graph export
- `product_lineage_replay_manifest.csv` — audit trail per rerun

## Do NOT

- Repurpose `Master_Crosswalk.csv` for plan mapping in new architecture
- Write governance artifacts into `QLA_Migration/Output/` without signoff
- Mix product holds into `claims_review_hold_manifest.csv`
"""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def write_runner_architecture(path: str) -> None:
    content = """# Recommended Product Runner Architecture

## Design Goal

app.py v55.7 remains an **orchestration wrapper / launcher / governance controller**. Complex product logic must NOT be inlined into app.py.

## Proposed Tab: "Product Setup Conversion"

### UI Responsibilities (app.py — minimal)

- Path pickers: `quikplan_source.csv`, Policy Form Crosswalk, PCOMP, output targets
- Launch button → subprocess runner
- Display governance summary counts (held / staged / emitted)
- Rollback toggle: `QLA_PRODUCT_GOVERNANCE_HOLD`
- No field-level transformation logic in app.py

### Subprocess Runner (isolated)

```
plan_governance/phase_p2_product_runner/product_setup_runner.py
```

Pipeline stages:
1. **Load** — read `plan_analysis/quikplan_source.csv` (never `output/quikplan.csv`)
2. **Crosswalk Join** — Policy Form Crosswalk on confirmed join key (TBD in P1C)
3. **Rulebook Transform** — `Sync_Rulebook_quikplan.csv` field routing
4. **PCOMP Lookup** — MINUNIT/MAXUNIT joins
5. **Semantic Governance** — classification holds (no auto-fix)
6. **Dependency Check** — quikridr MPLAN orphan detection
7. **Stage** — write `plan_governance/staged/quikplan_staged.csv`
8. **Validate** — key_definitions PLAN uniqueness, schema order
9. **Manifest** — append holds to `product_review_hold_manifest.csv`
10. **Emit** ( gated ) — copy cleared rows to `output/quikplan.csv`

### Isolation Boundaries

| Concern | Product Runner | Policy/Claims Batch |
|---|---|---|
| Source | plan_analysis/quikplan_source.csv | QLA_Migration/Source/* |
| Crosswalk | Policy Form Crosswalk 5.22.26 | Master_Crosswalk (policy only) |
| Holds manifest | product_review_hold_manifest.csv | claims_review_hold_manifest.csv |
| Logs | plan_governance/logs/ | claims_analysis logs |
| Replay | plan_governance/replay/ | claims phase15 replay |

### Dependency Validation Subprocess

Before emit, runner validates:
- Every distinct `quikridr.MPLAN` exists in staged `quikplan.PLAN`
- No duplicate PLAN keys
- FORM present when crosswalk specifies form
- PLANTYPE / HRIGPKEY holds enforced (future phase)

### Execution Command Pattern

```bash
python plan_governance/phase_p2_product_runner/product_setup_runner.py \
  --source plan_analysis/quikplan_source.csv \
  --crosswalk "docs/plan_conversion_reference/Policy Form Crosswalk 5.22.26.xlsx" \
  --rulebook QLA_Migration/Configs/Sync_Rulebook_quikplan.csv \
  --pcomp plan_analysis/PCOMP.csv \
  --ridr QLA_Migration/Output/quikridr.csv \
  --stage-dir plan_governance/staged \
  --manifest plan_governance/manifests/product_review_hold_manifest.csv \
  --hold-mode 1
```

app.py invokes this via `subprocess.run` with captured stdout → UI log panel.

## Why Subprocess Isolation

1. **Rollback safety** — product experimentation cannot destabilize claims v55.7 batch path
2. **Audit clarity** — separate logs/manifests per domain
3. **Business review** — product team can rerun without full policy conversion
4. **Determinism** — frozen source + versioned crosswalk + manifest = reproducible lineage

## Integration Point in app.py (future — NOT this phase)

```python
# Pseudocode only — do not implement in P1B
if product_tab_run_requested:
    subprocess.run([sys.executable, PRODUCT_RUNNER, *args], check=False)
    self._load_product_governance_summary()
```

## Regression Risks if NOT Isolated

- Master_Crosswalk plan/policy collision affects claims MPOLICY and plan MPLAN simultaneously
- Silent PLAN remap breaks quikridr orphan detection
- HRIGPKEY premature population blocks actuarial review cycles
"""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def write_executive_findings(
    path: str,
    stats: dict,
    dep_df: pd.DataFrame,
    semantic_df: pd.DataFrame,
    authority_df: pd.DataFrame,
) -> None:
    high_sem = semantic_df[semantic_df["review_priority"] == "HIGH"]
    conflicts = authority_df[authority_df["conflict_flag"] != "NONE"]

    content = f"""# Executive Product Conversion Findings — Phase P1B

**Date:** {datetime.now().strftime("%Y-%m-%d")}  
**Scope:** Analysis + governance scaffold only — no conversion code changes  
**Primary Source:** `plan_analysis/quikplan_source.csv`

---

## Executive Summary

Phase P1B confirms that product setup conversion is a **distinct governance domain** upstream of policy and claims conversion. Plan identity currently flows through multiple authorities (LifePRO source, PCOMP, Master_Crosswalk plan rows, Policy Form Crosswalk, rulebook defaults) with material semantic and FORM alignment risk.

---

## Key Metrics

| Metric | Value |
|---|---|
| LifePRO source coverages (quikplan_source) | {stats['src_rows']} |
| PCOMP component rows | {stats['pcomp_rows']} |
| Policy Form Crosswalk rows | {stats['xwalk_rows']} |
| Current quikplan output rows | {stats['out_rows']} |
| Unique output PLAN codes | {stats['unique_plans']} |
| quikridr rows | {stats['ridr_rows']} |
| Distinct quikridr MPLAN values | {stats['unique_mplan']} |
| MPLAN orphan (not in quikplan.PLAN) | {stats['orphan_mplan_count']} |
| Blank quikridr MPLAN rows | {stats['blank_mplan']} |
| Master_Crosswalk plan-like mappings | {stats['mcw_plan_rows']} |
| FORM conflicts (crosswalk vs output) | {stats['form_conflicts']} |
| Duplicate PLAN in output | {stats['duplicate_plans']} |
| High-priority semantic review rows | {len(high_sem)} |
| Authority conflict rows | {len(conflicts)} |

---

## Critical Findings

### 1. Join Key Ambiguity (Highest Risk)

- Source `COVERAGE_ID` uses LifePRO plan identifiers (e.g., `0822 620`, `L17 1`).
- Output `PLAN` uses QL plan codes (e.g., `920ADB`) for ~77% of rows via mapping.
- Policy Form Crosswalk links LifePRO Coverage_ID → QL Plan Code — **correct business join path**.
- Master_Crosswalk.csv contains ~{stats['mcw_plan_rows']} plan mappings mixed with policy numbers — **violates stated policy-only authority** and creates collision risk with claims crosswalk.

### 2. FORM Authority Divergence

Only **{stats['form_match_count']}** of **{stats['ql_plan_matched']}** crosswalk-matched plans have FORM aligned to QL Form Number. LifePRO `POLICY_FORM_NUM` is currently winning in rulebook routing — business crosswalk should override after signoff.

### 3. quikridr Dependency Explosion

- **{stats['ridr_rows']:,}** quikridr rows depend on **{stats['unique_mplan']}** MPLAN values.
- **{stats['orphan_mplan_count']}** MPLAN codes have no quikplan catalog row ({stats['orphan_mplan_list']}).
- **{stats['blank_mplan']:,}** rows have blank MPLAN — linkage integrity risk.

### 4. Semantic Blurring (LifePRO vs QLAdmin)

LifePRO mixes base plans, riders, supplemental coverages, and form variants in one source table. PCOMP `COMPONENT_TYPE` (BA, WP, AD, etc.) and EXHIBIT_CODE (SUP, WHO, etc.) provide separation signals QLAdmin expects via QuikPlan vs QuikRidr.

### 5. Future Actuarial Attachment Not Ready

- HRIGPKEY: **0/{stats['out_rows']}** populated (correct — not implemented).
- PLANTYPE: **blank on all rows**.
- GDVARYGP/BDVARY* defaulted; UWVARY/STVARY blank — rate attachment dimensions undefined.

### 6. Effective Date / Versioning Gap

Policy Form Crosswalk has **no effective-date dimension**. PCOMP END_DATE is uniformly 20991231. Product versioning and grandfathering cannot be governed without business date keys.

---

## Confirmed Business Decisions Honored

- MPHASE 1 = base coverage; riders MPHASE > 1
- Master_Crosswalk.csv stated role: policy numbers only (current state deviates — flagged)
- No HRIGPKEY implementation in this phase
- No silent auto-remediation
- Rulebook-driven architecture preserved

---

## Recommendations (Next Phases)

1. **P1C — Join Key Proof:** Validate LifePRO COVERAGE_ID → Crosswalk join with business signoff sample set.
2. **Segregate plan mappings** from Master_Crosswalk into Policy Form Crosswalk authority path.
3. **Stand up plan_governance/** with hold manifests mirroring claims Phase 22 pattern.
4. **Build isolated product runner** — do not integrate into core batch until governance cleared.
5. **FORM override policy** — crosswalk FORM wins over LifePRO POLICY_FORM_NUM after review.
6. **Orphan MPLAN remediation** — 7 codes + 2,348 blank rows require product review before UAT.

---

## Deliverables Produced (Phase P1B)

1. `plan_dependency_map.csv`
2. `product_semantic_classification_workbench.csv`
3. `plan_crosswalk_authority_analysis.csv`
4. `future_rate_attachment_analysis.csv`
5. `plan_effective_date_governance_analysis.csv`
6. `proposed_product_governance_model.md`
7. `plan_source_to_output_lineage.csv`
8. `recommended_plan_governance_folder_structure.md`
9. `recommended_product_runner_architecture.md`
10. `executive_product_conversion_findings.md`

---

## Explicit Non-Actions (This Phase)

- No app.py changes
- No quikplan conversion rewrite
- No claims orchestration changes
- No HRIGPKEY / actuarial load implementation
- No source extract mutation
"""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def run_analysis(output_dir: str) -> dict:
    os.makedirs(output_dir, exist_ok=True)

    src_path = os.path.join(ROOT, "plan_analysis", "quikplan_source.csv")
    pcomp_path = os.path.join(ROOT, "plan_analysis", "PCOMP.csv")
    out_path = os.path.join(ROOT, "QLA_Migration", "Output", "quikplan.csv")
    ridr_path = os.path.join(ROOT, "QLA_Migration", "Output", "quikridr.csv")
    xwalk_path = os.path.join(ROOT, "docs", "plan_conversion_reference", "Policy Form Crosswalk 5.22.26.xlsx")
    mcw_path = os.path.join(ROOT, "Master_Crosswalk.csv")
    rb_path = os.path.join(ROOT, "QLA_Migration", "Configs", "Sync_Rulebook_quikplan.csv")
    key_path = os.path.join(ROOT, "validation_config", "key_definitions.json")

    src = load_source_table(src_path)
    pcomp = load_source_table(pcomp_path)
    out = norm_cols(pd.read_csv(out_path, dtype=str).fillna(""))
    ridr = norm_cols(pd.read_csv(ridr_path, dtype=str, encoding="latin1", on_bad_lines="skip").fillna(""))
    xwalk = load_crosswalk(xwalk_path)
    master_cw = load_master_crosswalk(mcw_path)
    rulebook = norm_cols(pd.read_csv(rb_path, dtype=str))
    with open(key_path, encoding="utf-8") as fh:
        key_defs = json.load(fh)

    src_ids = set(src["COVERAGE_ID"].map(strip_val))
    xwalk_ids = set(xwalk["lifepro_coverage_id"].map(strip_val))
    ql_codes = set(xwalk["ql_plan_code"].map(strip_val))
    out_plans = set(out["PLAN"].map(strip_val))
    mplan_set = set(ridr["MPLAN"].map(strip_val)) - {""}
    orphan_mplan = sorted(mplan_set - out_plans)

    mcw_plan_rows = int(
        master_cw["old_value"].isin(src_ids | xwalk_ids).sum()
    )

    merged = out.merge(xwalk, left_on="PLAN", right_on="ql_plan_code", how="inner")
    form_match = int((merged["FORM"].map(strip_val) == merged["ql_form_number"].map(strip_val)).sum())

    dep_df = build_dependency_map(
        ridr,
        {
            "Sync_Rulebook_quikplan": rb_path,
            "Sync_Rulebook_quikridr": os.path.join(ROOT, "QLA_Migration", "Configs", "Sync_Rulebook_quikridr.csv"),
            "Sync_Rulebook_quikactg": os.path.join(ROOT, "QLA_Migration", "Configs", "Sync_Rulebook_quikactg.csv"),
        },
        key_defs,
    )
    semantic_df = build_semantic_workbench(src, pcomp, out, ridr)
    authority_df = build_authority_analysis(src, pcomp, out, xwalk, master_cw)
    rate_df = build_rate_attachment_analysis(out, rulebook)
    effective_df = build_effective_date_governance(src, pcomp, xwalk, out)
    lineage_df = build_lineage(src, pcomp, out, xwalk, master_cw, ridr)

    dep_df.to_csv(os.path.join(output_dir, "plan_dependency_map.csv"), index=False)
    semantic_df.to_csv(os.path.join(output_dir, "product_semantic_classification_workbench.csv"), index=False)
    authority_df.to_csv(os.path.join(output_dir, "plan_crosswalk_authority_analysis.csv"), index=False)
    rate_df.to_csv(os.path.join(output_dir, "future_rate_attachment_analysis.csv"), index=False)
    effective_df.to_csv(os.path.join(output_dir, "plan_effective_date_governance_analysis.csv"), index=False)
    lineage_df.to_csv(os.path.join(output_dir, "plan_source_to_output_lineage.csv"), index=False)

    write_governance_model(os.path.join(output_dir, "proposed_product_governance_model.md"))
    write_folder_structure(os.path.join(output_dir, "recommended_plan_governance_folder_structure.md"))
    write_runner_architecture(os.path.join(output_dir, "recommended_product_runner_architecture.md"))

    dup_plans = out[out.duplicated("PLAN", keep=False)]["PLAN"].tolist()
    stats = {
        "src_rows": len(src),
        "pcomp_rows": len(pcomp),
        "xwalk_rows": len(xwalk),
        "out_rows": len(out),
        "unique_plans": out["PLAN"].nunique(),
        "ridr_rows": len(ridr),
        "unique_mplan": ridr["MPLAN"].map(strip_val).nunique(),
        "orphan_mplan_count": len(orphan_mplan),
        "orphan_mplan_list": ", ".join(orphan_mplan),
        "blank_mplan": int((ridr["MPLAN"].map(strip_val) == "").sum()),
        "mcw_plan_rows": mcw_plan_rows,
        "form_conflicts": len(merged) - form_match,
        "form_match_count": form_match,
        "ql_plan_matched": len(merged),
        "duplicate_plans": len(set(dup_plans)),
    }
    write_executive_findings(
        os.path.join(output_dir, "executive_product_conversion_findings.md"),
        stats,
        dep_df,
        semantic_df,
        authority_df,
    )
    return stats


def main():
    parser = argparse.ArgumentParser(description="Phase P1B product lineage analysis runner")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    stats = run_analysis(args.output_dir)
    print("Phase P1B analysis complete.")
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
