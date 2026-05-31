#!/usr/bin/env python3
"""
Phase P1C — Product setup dependency analysis (read-only).

Generates product_setup_dependency_analysis.csv for architecture documentation.
Does NOT modify conversion outputs or app.py.
"""

from __future__ import annotations

import argparse
import os

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))


def strip_val(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=SCRIPT_DIR)
    args = parser.parse_args()

    src = pd.read_csv(
        os.path.join(ROOT, "plan_analysis", "quikplan_source.csv"),
        dtype=str, encoding="latin1", on_bad_lines="skip",
    ).fillna("")
    src.columns = [strip_val(c) for c in src.columns]
    src = src[src["COVERAGE_ID"].str.match(r"^[0-9A-Za-z]", na=False)]

    rb = pd.read_csv(
        os.path.join(ROOT, "QLA_Migration", "Configs", "Sync_Rulebook_quikplan.csv"),
        dtype=str,
    ).fillna("")
    rb.columns = [strip_val(c) for c in rb.columns]

    out = pd.read_csv(
        os.path.join(ROOT, "QLA_Migration", "Output", "quikplan.csv"),
        dtype=str,
    ).fillna("")

    ridr = pd.read_csv(
        os.path.join(ROOT, "QLA_Migration", "Output", "quikridr.csv"),
        dtype=str, encoding="latin1", on_bad_lines="skip",
    ).fillna("")

    xwalk = pd.read_excel(
        os.path.join(ROOT, "docs", "plan_conversion_reference", "Policy Form Crosswalk 5.22.26.xlsx")
    )
    xwalk.columns = [
        "lifepro_coverage_id", "unused", "ql_plan_code",
        "ql_form_number", "ql_plan_description", "ql_friendly_name",
    ]
    for c in xwalk.columns:
        xwalk[c] = xwalk[c].map(strip_val)

    rows = []

    def add(asset_type, asset_name, role, consumer, preservation_rule, notes):
        rows.append({
            "asset_type": asset_type,
            "asset_name": asset_name,
            "role_in_pipeline": role,
            "downstream_consumer": consumer,
            "preservation_requirement": preservation_rule,
            "notes": notes,
        })

    add("SOURCE", "plan_analysis/quikplan_source.csv", "PRIMARY_PRODUCT_SOURCE",
        "Product Setup Runner", "READ_ONLY — never mutate",
        f"{len(src)} LifePRO coverage rows; authoritative lineage input.")

    add("CROSSWALK", "Policy Form Crosswalk 5.22.26.xlsx", "CONFIGURATION_ENRICHMENT",
        "Product Setup Runner (pre-rulebook overlay)",
        "Business authority for PLAN/FORM/DESCR/PLANNAME when joined on COVERAGE_ID",
        f"{len(xwalk)} rows; join key = LifePRO Coverage_ID.")

    add("RULEBOOK", "Sync_Rulebook_quikplan.csv", "FIELD_MAPPING_AND_DEFAULTS",
        "Product Setup Runner (core transform engine)",
        "MUST NOT bypass — all mappings, defaults, Transformation_Note behavior preserved",
        f"{len(rb)} rulebook lines including PCOMP lookup joins.")

    add("LOOKUP", "plan_analysis/PCOMP.csv", "MINUNIT/MAXUNIT_LOOKUP",
        "Rulebook Lookup_Table=PCOMP Join_Key=COVERAGE_ID",
        "Preserve TO_UNITS transformation note intent",
        "Rulebook lines MIN_ISSUE_AMT1/MAX_ISSUE_AMT1 -> MINUNIT/MAXUNIT.")

    add("TRANSLATION", "Master_Value_Translation.csv", "VALUE_TRANSLATION",
        "Shared with policy batch via trans_map",
        "Preserve prefix translations (PAR_, etc.) for quikplan fields",
        "Loaded in app.py process_data; runner must load identically.")

    add("CROSSWALK_LEGACY", "Master_Crosswalk.csv (plan rows)", "PLAN_CODE_MAP",
        "app.py line ~3669 cw_map.get(val,val) on PLAN field",
        "Currently maps COVERAGE_ID -> QL Plan Code; transition to Policy Form Crosswalk",
        "Approx 237 plan-like rows mixed with policy mappings — segregate in future phase.")

    add("OUTPUT", "output/quikplan.csv", "MASTER_PRODUCT_CONFIGURATION",
        "quikridr.MPLAN, quikactg.MPLAN, validation, future DBF",
        "Schema order from app.py TABLE_SCHEMAS['quikplan']; PLAN primary key",
        f"{len(out)} rows; {out['PLAN'].nunique()} unique PLAN.")

    add("OUTPUT", "output/quikplan.dbf", "QLADMIN_LOAD_TARGET",
        "QLAdmin product setup load (future/isolated runner)",
        "Generate from final emitted CSV only (mirror Phase 21B claims pattern)",
        "No quikplan.dbf currently in repo; optional subprocess DBF stage.")

    add("VALIDATION", "validation_config/key_definitions.json", "PLAN_UNIQUENESS",
        "Product governance diagnostics",
        "Additive ERROR on duplicate PLAN — do not auto-remediate",
        "quikplan key = PLAN field.")

    mplan_set = set(ridr["MPLAN"].map(strip_val)) - {""}
    out_plans = set(out["PLAN"].map(strip_val))
    orphans = sorted(mplan_set - out_plans)
    add("DOWNSTREAM", "quikridr.csv MPLAN", "POLICY_PHASE_PLAN_REFERENCE",
        "Issued policy phases reference quikplan.PLAN catalog",
        "Diagnostic only in P1C — orphan MPLAN report, no blocking unless approved",
        f"{len(ridr)} rows; {len(orphans)} orphan MPLAN codes: {', '.join(orphans)}")

    add("DOWNSTREAM", "Sync_Rulebook_quikactg.csv", "ACCOUNTING_PLAN_REFERENCE",
        "PACTG.PLAN_CODE -> MPLAN via Master_Crosswalk",
        "Policy batch unchanged; depends on stable quikplan catalog",
        "quikactg not regenerated when product setup isolated from batch.")

    add("ENGINE", "app.py TABLE_SCHEMAS['quikplan']", "OUTPUT_SCHEMA",
        "CSV column order and DBF layout source of truth",
        "Extract as shared constant — do not duplicate field list",
        f"{len(out.columns)} fields defined at app.py ~line 162.")

    add("ENGINE", "app.py process_data rulebook loop", "TRANSFORMATION_ENGINE",
        "Currently inline ~lines 3453-3705",
        "Extract to shared module; subprocess + app.py call same function",
        "Includes ROUTE_PAY_*, age zfill, PAR exception, cw_map on PLAN.")

    dep_df = pd.DataFrame(rows)
    out_path = os.path.join(args.output_dir, "05_product_setup_dependency_analysis.csv")
    dep_df.to_csv(out_path, index=False)
    print(f"Wrote {out_path} ({len(dep_df)} rows)")


if __name__ == "__main__":
    main()
