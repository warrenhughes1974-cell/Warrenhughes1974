#!/usr/bin/env python3
"""Phase P3D — MPLAN authority impact analysis (governance assessment only)."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))
OUTPUT_DIR = SCRIPT_DIR

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from qla_core.product_catalog_authority import load_closed_product_catalog, plan_contains_space

POLICY_RE = re.compile(r"^90\d{8}$")


def sv(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def load_outputs():
    qp_path = os.path.join(ROOT, "QLA_Migration", "Output", "quikplan.csv")
    qr_path = os.path.join(ROOT, "QLA_Migration", "Output", "quikridr.csv")
    qp = pd.read_csv(qp_path, dtype=str, keep_default_na=False)
    qr = pd.read_csv(qr_path, dtype=str, keep_default_na=False)
    return qp, qr, qp_path, qr_path


def load_master_product_crosswalk():
    mcw = pd.read_csv(os.path.join(ROOT, "Master_Crosswalk.csv"), dtype=str, keep_default_na=False)
    mcw.columns = ["Old_Value", "New_Value"]
    mcw["Old_n"] = mcw["Old_Value"].map(sv)
    mcw["New_n"] = mcw["New_Value"].map(sv)
    product = mcw[~mcw["Old_n"].str.match(POLICY_RE, na=False)].copy()
    return product


def build_referential_integrity(qp, qr, catalog):
    plan_set = set(qp["PLAN"].map(sv)) - {""}
    mplan_vals = qr["MPLAN"].map(sv)
    mplan_set = set(mplan_vals) - {""}
    blank_mplan = int((mplan_vals == "").sum())
    orphans = sorted(mplan_set - plan_set)

    rows = []
    for m in orphans:
        sub = qr[mplan_vals == m]
        rows.append({
            "mplan_code": m,
            "quikridr_row_count": len(sub),
            "mphase_values": ";".join(sorted(set(sub["MPHASE"].map(sv)))),
            "plan_contains_spaces": "Y" if plan_contains_space(m) else "N",
            "in_authoritative_catalog": "Y" if m in catalog.authoritative_plan_set else "N",
            "in_quikplan_plan": "N",
            "in_p3c_closed_catalog": "Y" if m in catalog.authoritative_plan_set else "N",
            "referential_status": "ORPHAN_MPLAN",
            "risk_level": "HIGH" if len(sub) > 10 else "MEDIUM",
            "p3c_impact": "MPLAN emitted by quikridr but absent from P3C closed-authority quikplan.PLAN",
            "rider_linkage_risk": "Y" if any(p != "1" for p in sub["MPHASE"].map(sv)) else "BASE_ONLY",
            "claims_linkage_risk": "LOW",
        })

    rows.append({
        "mplan_code": "(BLANK)",
        "quikridr_row_count": blank_mplan,
        "mphase_values": "",
        "plan_contains_spaces": "N",
        "in_authoritative_catalog": "N",
        "in_quikplan_plan": "N",
        "in_p3c_closed_catalog": "N",
        "referential_status": "BLANK_MPLAN",
        "risk_level": "CRITICAL",
        "p3c_impact": "Blank MPLAN on quikridr rows — not governed by P3C",
        "rider_linkage_risk": "UNKNOWN",
        "claims_linkage_risk": "LOW",
    })

    aligned = sorted(mplan_set & plan_set)
    for m in aligned[:5]:
        rows.append({
            "mplan_code": m,
            "quikridr_row_count": int((mplan_vals == m).sum()),
            "mphase_values": "sample_aligned",
            "plan_contains_spaces": "N",
            "in_authoritative_catalog": "Y",
            "in_quikplan_plan": "Y",
            "in_p3c_closed_catalog": "Y",
            "referential_status": "ALIGNED_SAMPLE",
            "risk_level": "LOW",
            "p3c_impact": "Referential integrity satisfied",
            "rider_linkage_risk": "N",
            "claims_linkage_risk": "LOW",
        })

    return pd.DataFrame(rows)


def build_dependency_trace(qp, qr, catalog, product_mcw):
    auth_col = catalog.authority_column
    cat_df = pd.read_csv(catalog.catalog_path, dtype=str, keep_default_na=False)
    rows = []

    components = [
        ("quikplan", "PLAN", "quikplan_source", "COVERAGE_ID", "Sync_Rulebook_quikplan.csv",
         "qla_core/quikplan_converter.py + product_catalog_authority + crosswalk_enrichment",
         "P3C closed catalog + optional UAT overlay", "YES"),
        ("quikridr", "MPLAN", "PPBEN", "PLAN_CODE", "Sync_Rulebook_quikridr.csv",
         "app.py process_data generic loop (~3960)", "Flat Master_Crosswalk.csv only", "NO"),
        ("quikmstr", "N/A", "PPBEN/PPOL", "POLICY_NUMBER", "Sync_Rulebook_quikmstr.csv",
         "app.py process_data", "Policy-number crosswalk only", "NO"),
        ("quikactg", "MPLAN", "PACTG", "PLAN_CODE", "Sync_Rulebook_quikactg.csv",
         "app.py process_data generic loop", "Flat Master_Crosswalk.csv only", "NO"),
        ("product_setup_runner", "PLAN", "quikplan_source", "COVERAGE_ID", "Sync_Rulebook_quikplan.csv",
         "product_setup_runner.py + closed authority", "P3C closed catalog default with UAT overlay", "YES"),
        ("batch_quikplan", "PLAN", "quikplan_source", "COVERAGE_ID", "Sync_Rulebook_quikplan.csv",
         "app.py convert_quikplan_to_output", "CrosswalkAuthority unless CROSSWALK_OVERLAY=1", "PARTIAL"),
        ("governance", "ORPHAN_MPLAN", "quikridr", "MPLAN", "product_setup_governance_engine.py",
         "WARN only — compares ridr MPLAN to staged quikplan", "Diagnostic — no batch enforcement", "N/A"),
        ("claims", "MPOLICY", "quikmstr", "MPOLICY", "Sync_Rulebook_quikclms/quikclmp",
         "app.py Phase 20 MPOLICY validation", "No MPLAN/PLAN dependency", "N/A"),
    ]
    for comp in components:
        rows.append({
            "component": comp[0],
            "target_field": comp[1],
            "source_table": comp[2],
            "source_key_field": comp[3],
            "rulebook": comp[4],
            "engine_path": comp[5],
            "authority_layer": comp[6],
            "p3c_closed_authority_applied": comp[7],
            "consumes_quikplan_output": "YES" if comp[0] in ("governance",) else "NO",
            "independent_plan_derivation": "YES" if comp[0] in ("quikridr", "quikactg") else "NO",
        })

    divergent = cat_df[cat_df["ql_plan_code"].map(sv) != cat_df[auth_col].map(sv)]
    for _, r in divergent.iterrows():
        cid = sv(r["lifepro_coverage_id"])
        compat = sv(r["ql_plan_code"])
        auth = sv(r[auth_col])
        ridr_count = int((qr["MPLAN"].map(sv) == compat).sum()) if compat else 0
        rows.append({
            "component": "crosswalk_divergence",
            "target_field": "MPLAN/PLAN",
            "source_table": "PPBEN/quikplan_source",
            "source_key_field": f"PLAN_CODE/{cid}",
            "rulebook": "Master_Crosswalk + product_catalog_crosswalk",
            "engine_path": "quikridr uses compat via passthrough; quikplan P3C uses auth",
            "authority_layer": f"compat={compat} auth={auth}",
            "p3c_closed_authority_applied": "quikplan YES / quikridr NO",
            "consumes_quikplan_output": "NO",
            "independent_plan_derivation": "YES",
            "quikridr_compat_emit_rows": ridr_count,
        })

    return pd.DataFrame(rows)


def build_legacy_inventory(product_mcw, catalog):
    rows = []
    auth_col = catalog.authority_column
    cat_df = pd.read_csv(catalog.catalog_path, dtype=str, keep_default_na=False)
    cat_old = set(cat_df["lifepro_coverage_id"].map(sv))

    for _, r in product_mcw.iterrows():
        old, new = sv(r["Old_n"]), sv(r["New_n"])
        in_catalog = "Y" if old in cat_old else "N"
        auth_plan = sv(catalog.coverage_to_plan.get(old, ""))
        rows.append({
            "legacy_old_value": old,
            "legacy_new_value": new,
            "in_product_catalog_crosswalk": in_catalog,
            "authoritative_plan": auth_plan,
            "legacy_matches_authoritative": "Y" if new == auth_plan else "N",
            "contains_spaces_old": "Y" if plan_contains_space(old) else "N",
            "contains_spaces_new": "Y" if plan_contains_space(new) else "N",
            "still_used_by_quikridr_path": "Y",
            "p3c_status": "OBSOLETE_FOR_QUIKPLAN" if in_catalog == "Y" and new != auth_plan else "ACTIVE_LEGACY",
            "dependency_type": "Master_Crosswalk product row",
        })

    return pd.DataFrame(rows)


def build_remediation_matrix(qp, qr, catalog):
    rows = [
        {
            "finding_id": "P3D-001",
            "category": "REQUIRED before MPLAN governance cutover",
            "component": "quikridr MPLAN population",
            "root_cause": "quikridr derives MPLAN from PPBEN.PLAN_CODE via flat Master_Crosswalk; P3C does not apply",
            "production_uat_risk": "39 orphan MPLAN codes vs P3C quikplan; 31 space-containing MPLAN values",
            "minimal_remediation": "P3E: Add closed-authority MPLAN resolution using product_catalog crosswalk_ql_plan_code keyed on PLAN_CODE reverse lookup or explicit PLAN_CODE→authoritative map",
            "phase": "P3E quikridr Authority Alignment",
        },
        {
            "finding_id": "P3D-002",
            "category": "REQUIRED before MPLAN governance cutover",
            "component": "Referential FK quikridr.MPLAN → quikplan.PLAN",
            "root_cause": "No runtime enforcement; governance WARN only",
            "production_uat_risk": "Silent orphan MPLAN persists through batch emit and DBF generation",
            "minimal_remediation": "P3D: Add batch referential governance gate before quikridr/quikplan DBF emit",
            "phase": "P3D MPLAN Referential Governance",
        },
        {
            "finding_id": "P3D-003",
            "category": "REQUIRED before MPLAN governance cutover",
            "component": "Blank MPLAN (~2348 rows)",
            "root_cause": "PPBEN PLAN_CODE blank or crosswalk passthrough to empty; not in validate_output critical fields",
            "production_uat_risk": "Rider rows without plan identity; breaks FK semantics",
            "minimal_remediation": "P3D: Add BLANK_MPLAN ERROR in batch governance; trace to source PPBEN rows",
            "phase": "P3D MPLAN Referential Governance",
        },
        {
            "finding_id": "P3D-004",
            "category": "RECOMMENDED hardening",
            "component": "quikactg MPLAN",
            "root_cause": "Same flat Master_Crosswalk path as quikridr",
            "production_uat_risk": "Accounting MPLAN drift from closed quikplan catalog",
            "minimal_remediation": "Extend P3E closed authority to quikactg after quikridr alignment",
            "phase": "P3F Product Referential Validation Layer",
        },
        {
            "finding_id": "P3D-005",
            "category": "RECOMMENDED hardening",
            "component": "Batch quikplan path",
            "root_cause": "app.py batch quikplan uses CrosswalkAuthority but not P3C closed emit filter by default",
            "production_uat_risk": "Batch quikplan may emit passthrough PLAN if product setup isolated",
            "minimal_remediation": "Align batch quikplan with product setup runner when CROSSWALK_OVERLAY=1",
            "phase": "P3G Batch Product Authority Parity",
        },
        {
            "finding_id": "P3D-006",
            "category": "SAFE TO LEAVE AS-IS",
            "component": "quikmstr",
            "root_cause": "No MPLAN field; policy master only",
            "production_uat_risk": "None for MPLAN authority",
            "minimal_remediation": "None",
            "phase": "N/A",
        },
        {
            "finding_id": "P3D-007",
            "category": "SAFE TO LEAVE AS-IS",
            "component": "Claims pipeline",
            "root_cause": "Validates MPOLICY only; no MPLAN/PLAN dependency",
            "production_uat_risk": "Low direct claims impact from MPLAN orphan",
            "minimal_remediation": "Monitor only",
            "phase": "N/A",
        },
        {
            "finding_id": "P3D-008",
            "category": "OBSOLETE LEGACY LOGIC",
            "component": "Master_Crosswalk product passthrough for quikplan",
            "root_cause": "Superseded by product_catalog_crosswalk + P3C closed authority",
            "production_uat_risk": "Rollback-only via QLA_ALLOW_LEGACY_PRODUCT_FALLBACK",
            "minimal_remediation": "Keep for diagnostics; do not use for emit under UAT",
            "phase": "P2E quarantine maintained",
        },
        {
            "finding_id": "P3D-009",
            "category": "OBSOLETE LEGACY LOGIC",
            "component": "ql_plan_code passthrough emit values",
            "root_cause": "33 CROSSWALK_DIVERGENT rows with compat passthrough in product catalog",
            "production_uat_risk": "quikridr still emits compat values with spaces",
            "minimal_remediation": "Catalog compat column retained for lineage only; authoritative column governs quikplan",
            "phase": "P3C complete for quikplan",
        },
    ]
    return pd.DataFrame(rows)


def build_obsolete_inventory(catalog):
    rows = []
    cat_df = pd.read_csv(catalog.catalog_path, dtype=str, keep_default_na=False)
    for _, r in cat_df.iterrows():
        cid = sv(r["lifepro_coverage_id"])
        compat = sv(r["ql_plan_code"])
        auth = sv(r["crosswalk_ql_plan_code"])
        if compat == auth:
            continue
        rows.append({
            "lifepro_coverage_id": cid,
            "obsolete_emit_value": compat,
            "authoritative_value": auth,
            "obsolete_reason": "CROSSWALK_DIVERGENT compat passthrough superseded by P3C crosswalk_ql_plan_code",
            "still_emitted_by_quikridr": "LIKELY_IF_PLAN_CODE_MATCHES_COMPAT",
            "still_emitted_by_quikplan_p3c": "N",
            "remediation_owner": "P3E quikridr alignment",
        })
    rows.append({
        "lifepro_coverage_id": "ENGINE",
        "obsolete_emit_value": "cw_map.get(val,val) passthrough",
        "authoritative_value": "product_catalog crosswalk_ql_plan_code",
        "obsolete_reason": "Flat Master_Crosswalk passthrough on quikridr/quikactg MPLAN path",
        "still_emitted_by_quikridr": "Y",
        "still_emitted_by_quikplan_p3c": "N",
        "remediation_owner": "P3E/P3F closed authority extension",
    })
    return pd.DataFrame(rows)


def write_executive_summary(qp, qr, catalog, ref_df, remediation_df):
    plan_set = set(qp["PLAN"].map(sv)) - {""}
    mplan_set = set(qr["MPLAN"].map(sv)) - {""}
    orphans = mplan_set - plan_set
    blank = int((qr["MPLAN"].map(sv) == "").sum())
    spaced = [m for m in mplan_set if plan_contains_space(m)]

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Executive Summary — Phase P3D MPLAN Authority Impact Analysis",
        "",
        f"Generated: {ts}",
        "",
        "## Governance Risk Rating: **HIGH**",
        "",
        "P3C closed product catalog authority successfully governs **quikplan.PLAN** emission, but **quikridr.MPLAN** and **quikactg.MPLAN** continue to derive plan codes independently via legacy flat `Master_Crosswalk.csv` passthrough. Referential integrity `quikridr.MPLAN → quikplan.PLAN` is **not enforced at runtime**.",
        "",
        "## Key Metrics (current outputs)",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| quikplan.PLAN rows (P3C) | {len(qp)} |",
        f"| quikplan unique PLAN | {len(plan_set)} |",
        f"| quikplan PLAN outside closed catalog | {len(plan_set - catalog.authoritative_plan_set)} |",
        f"| quikplan PLAN with spaces | {sum(1 for p in plan_set if plan_contains_space(p))} |",
        f"| quikridr rows | {len(qr)} |",
        f"| quikridr unique MPLAN | {len(mplan_set)} |",
        f"| quikridr blank MPLAN | {blank} |",
        f"| Orphan MPLAN (not in quikplan.PLAN) | {len(orphans)} |",
        f"| MPLAN containing spaces | {len(spaced)} |",
        "",
        "## Direct Answers",
        "",
        "| Question | Answer |",
        "|----------|--------|",
        "| Can quikmstr/quikridr emit MPLAN not in authoritative quikplan? | **YES** — quikridr/quikactg unchanged by P3C; 39 orphan MPLAN codes observed |",
        "| Does quikmstr populate MPLAN? | **NO** — no MPLAN column |",
        "| Do quikridr/quikactg consume quikplan output? | **NO** — derive from PPBEN/PACTG PLAN_CODE independently |",
        "| Are rider PLANs failing authority resolution? | **YES** for 31 space-containing passthrough MPLANs and 39 orphan codes |",
        "| Do rules still generate passthrough PLAN identities? | **YES** — `app.py` `cw_map.get(val,val)` for MPLAN on quikridr/quikactg |",
        "| Assumptions that PLANs may contain spaces? | **YES** — quikridr still emits 31 spaced MPLAN values |",
        "| Does rider phase logic depend on COVERAGE_ID? | **NO** — MPHASE from BENEFIT_SEQ; MPLAN from PLAN_CODE regardless of phase |",
        "| Claims/governance replay obsolete PLAN risk? | **LOW direct** — claims use MPOLICY; indirect via product screens |",
        "| Is MPLAN closed-authority required next? | **YES** — P3C creates authority split that must be closed on quikridr |",
        "",
        "## MPLAN Governance Cutover Safety",
        "",
        "**NOT SAFE NOW.** Additional hardening required before MPLAN governance cutover.",
        "",
        "Required first: P3D referential governance gate + P3E quikridr authority alignment.",
        "",
        "## Recommended Phase Order",
        "",
        "1. **P3D** — MPLAN Referential Governance (diagnostics + batch gate, no engine rewrite)",
        "2. **P3E** — quikridr Authority Alignment (closed catalog MPLAN resolution)",
        "3. **P3F** — Product Referential Validation Layer (quikactg + DBF pre-emit checks)",
        "4. **P3G** — Batch Product Authority Parity (optional batch quikplan closed authority)",
        "",
    ]
    with open(os.path.join(OUTPUT_DIR, "executive_mplan_authority_impact_summary.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    qp, qr, qp_path, qr_path = load_outputs()
    catalog = load_closed_product_catalog()
    product_mcw = load_master_product_crosswalk()

    ref_df = build_referential_integrity(qp, qr, catalog)
    trace_df = build_dependency_trace(qp, qr, catalog, product_mcw)
    legacy_df = build_legacy_inventory(product_mcw, catalog)
    remediation_df = build_remediation_matrix(qp, qr, catalog)
    obsolete_df = build_obsolete_inventory(catalog)

    ref_df.to_csv(os.path.join(OUTPUT_DIR, "mplan_referential_integrity_analysis.csv"), index=False)
    trace_df.to_csv(os.path.join(OUTPUT_DIR, "product_authority_dependency_trace.csv"), index=False)
    legacy_df.to_csv(os.path.join(OUTPUT_DIR, "legacy_product_dependency_inventory.csv"), index=False)
    remediation_df.to_csv(os.path.join(OUTPUT_DIR, "required_remediation_matrix.csv"), index=False)
    obsolete_df.to_csv(os.path.join(OUTPUT_DIR, "obsolete_legacy_product_logic_inventory.csv"), index=False)

    write_executive_summary(qp, qr, catalog, ref_df, remediation_df)

    summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "governance_risk_rating": "HIGH",
        "mplan_cutover_safe": False,
        "orphan_mplan_count": int((ref_df["referential_status"] == "ORPHAN_MPLAN").sum()),
        "blank_mplan_rows": int(ref_df.loc[ref_df["mplan_code"] == "(BLANK)", "quikridr_row_count"].sum()) if "(BLANK)" in set(ref_df["mplan_code"]) else 0,
        "mplan_with_spaces": int(ref_df["plan_contains_spaces"].eq("Y").sum()),
        "quikplan_plans_outside_catalog": len(set(qp["PLAN"].map(sv)) - catalog.authoritative_plan_set),
        "output_dir": OUTPUT_DIR,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
