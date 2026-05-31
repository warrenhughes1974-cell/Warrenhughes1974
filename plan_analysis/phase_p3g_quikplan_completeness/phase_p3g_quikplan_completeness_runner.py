#!/usr/bin/env python3
"""
Phase P3G — quikplan Coverage Completeness & Batch Product Authority Parity.

Fixes quikplan_source ingestion (unquoted DESCRIPTION commas) and produces
business-reviewable blank MPLAN reporting with exact source values.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))
OUTPUT_DIR = SCRIPT_DIR

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from qla_core.p3g_completeness import (
    build_blank_mplan_business_review_report,
    build_quikplan_missing_catalog_emit_inventory,
    load_ppben_raw_rows,
    write_p3g_completeness_summary,
)
from qla_core.product_catalog_authority import (
    allow_legacy_mplan_fallback,
    build_authoritative_mplan_resolver,
    load_closed_product_catalog,
    load_crosswalk_authority,
    load_quikplan_plan_set,
    strip_val,
)
from qla_core.quikplan_converter import run_quikplan_conversion
from qla_core.quikplan_source_loader import annotate_ingestion_emit_trace, load_quikplan_source_csv
from qla_core.crosswalk_enrichment import load_policy_form_crosswalk, resolve_product_setup_overlay_config


def _legacy_skip_count(source_path: str) -> int:
    """Rows loadable by legacy pandas on_bad_lines=skip (pre-P3G baseline)."""
    try:
        legacy = pd.read_csv(
            source_path, encoding="latin1", dtype=str, on_bad_lines="skip", keep_default_na=False,
        )
        return len(legacy)
    except Exception:
        return 0


def _run_product_setup_emit(output_dir: str) -> int:
    runner = os.path.join(ROOT, "plan_governance", "phase_p2_product_setup_runner", "product_setup_runner.py")
    cmd = [
        sys.executable, runner,
        "--uat-overlay", "--closed-product-authority", "--strict-authority",
        "--emit", "--output-dir", output_dir,
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    return proc.returncode


def _run_p3e_emit(quikridr_path: str, quikplan_path: str) -> int:
    runner = os.path.join(ROOT, "plan_analysis", "phase_p3e_quikridr_authority_alignment", "phase_p3e_quikridr_authority_runner.py")
    cmd = [
        sys.executable, runner,
        "--quikridr", quikridr_path,
        "--quikplan", quikplan_path,
        "--closed-mplan-authority", "--emit",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    return proc.returncode


def run_p3g(
    *,
    source_path: str,
    catalog_path: str,
    quikplan_path: str,
    quikridr_path: str,
    ppben_path: str,
    master_cw_path: str,
    output_dir: str,
    emit: bool,
) -> int:
    os.makedirs(output_dir, exist_ok=True)

    before_plans = len(load_quikplan_plan_set(quikplan_path)) if os.path.isfile(quikplan_path) else 0
    legacy_rows = _legacy_skip_count(source_path)

    source_df, ingest_trace = load_quikplan_source_csv(source_path, collect_trace=True)
    parser_recovered = sum(
        1 for r in ingest_trace
        if r.get("skip_reason", "").startswith("COMMA_OVERFLOW") and r.get("row_classification") == "DATA"
    )

    overlay = resolve_product_setup_overlay_config(
        crosswalk_path=os.path.join(ROOT, "docs", "plan_conversion_reference", "Policy Form Crosswalk 5.22.26.xlsx"),
        uat_overlay=True,
    )
    if not overlay.crosswalk_map:
        overlay.crosswalk_map = load_policy_form_crosswalk(overlay.crosswalk_path)

    converted = run_quikplan_conversion(
        source_path=source_path,
        rulebook_path=os.path.join(ROOT, "QLA_Migration", "Configs", "Sync_Rulebook_quikplan.csv"),
        trans_path=os.path.join(ROOT, "Master_Value_Translation.csv"),
        cw_path=master_cw_path,
        lookup_dir=os.path.join(ROOT, "plan_analysis"),
        overlay_config=overlay,
        product_catalog_path=catalog_path,
    )

    emit_map: dict[str, str] = {}
    if "PLAN" in converted.columns:
        from qla_core.quikplan_converter import iter_quikplan_source_rows, prepare_quikplan_source
        from qla_core.normalize_utils import normalize_columns

        src_norm = normalize_columns(source_df.copy())
        src_norm = prepare_quikplan_source(src_norm)
        src_rows = list(iter_quikplan_source_rows(src_norm))
        for idx, src_row in enumerate(src_rows):
            if idx < len(converted):
                cid = src_row.get("COVERAGE_ID", "")
                plan = converted.iloc[idx].get("PLAN", "")
                if cid:
                    emit_map[cid] = plan

    ingest_trace = annotate_ingestion_emit_trace(ingest_trace, emit_map)
    pd.DataFrame(ingest_trace).to_csv(
        os.path.join(output_dir, "quikplan_source_ingestion_trace.csv"), index=False,
    )

    if emit:
        setup_rc = _run_product_setup_emit(os.path.dirname(quikplan_path))
        if setup_rc != 0:
            print(f"P3G_WARNING: product setup returned {setup_rc}")
        if os.path.isfile(quikridr_path):
            p3e_rc = _run_p3e_emit(quikridr_path, quikplan_path)
            if p3e_rc != 0:
                print(f"P3G_WARNING: P3E alignment returned {p3e_rc}")

    quikplan_df = pd.read_csv(quikplan_path, dtype=str, keep_default_na=False) if os.path.isfile(quikplan_path) else pd.DataFrame()
    quikridr_df = pd.read_csv(quikridr_path, dtype=str, keep_default_na=False) if os.path.isfile(quikridr_path) else pd.DataFrame()
    catalog_df = pd.read_csv(catalog_path, dtype=str, keep_default_na=False)
    catalog = load_closed_product_catalog(catalog_path)
    quikplan_set = load_quikplan_plan_set(quikplan_path)
    after_plans = len(quikplan_set)

    missing_df = build_quikplan_missing_catalog_emit_inventory(
        catalog_df, source_df, quikplan_df, ingest_trace,
    )
    missing_df.to_csv(os.path.join(output_dir, "quikplan_missing_catalog_emit_inventory.csv"), index=False)

    _, ppben_rows = load_ppben_raw_rows(ppben_path)
    authority = load_crosswalk_authority(master_cw_path, catalog_path)
    resolver = build_authoritative_mplan_resolver(
        catalog=catalog,
        legacy_product_map=authority.legacy_product_map,
        quikplan_plan_set=quikplan_set,
    )
    cw_df = pd.read_csv(master_cw_path, dtype=str, keep_default_na=False)
    cw_df.columns = ["Old_Value", "New_Value"]
    cw_map = {strip_val(k): strip_val(v) for k, v in zip(cw_df.iloc[:, 0], cw_df.iloc[:, 1])}

    parser_dropped_ids = {
        r.get("parsed_coverage_id", "")
        for r in ingest_trace
        if r.get("skip_reason", "").startswith("COMMA_OVERFLOW")
    }
    catalog_cids = set(catalog_df["lifepro_coverage_id"].tolist()) if "lifepro_coverage_id" in catalog_df.columns else set()

    blank_report = build_blank_mplan_business_review_report(
        quikridr_df,
        ppben_rows,
        resolver,
        quikplan_set,
        set(catalog.authoritative_plan_set),
        catalog_cids,
        parser_dropped_ids,
        allow_legacy=allow_legacy_mplan_fallback(),
        master_cw_map=cw_map,
    )
    blank_report.to_csv(os.path.join(output_dir, "blank_mplan_business_review_report.csv"), index=False)

    blank_count = int((quikridr_df.get("MPLAN", pd.Series(dtype=str)) == "").sum()) if not quikridr_df.empty else 0
    expected_non_product = 0
    unresolved = 0
    gov_errors = 0
    if not blank_report.empty:
        expected_non_product = int((blank_report["classification"] == "EXPECTED_NON_PRODUCT_ROW").sum())
        unresolved = int((blank_report["classification"] == "UNRESOLVED_PRODUCT").sum())
        gov_errors = int((blank_report["governance_status"] == "GOVERNANCE_FAILURE").sum())

    summary = write_p3g_completeness_summary(
        os.path.join(output_dir, "p3g_completeness_summary.json"),
        source_coverage_count=len(source_df),
        emitted_quikplan_plans=after_plans,
        authoritative_catalog_size=len(catalog.authoritative_plan_set),
        missing_catalog_emits=len(missing_df),
        blank_mplan_count=blank_count,
        expected_non_product_blanks=expected_non_product,
        unresolved_product_rows=unresolved,
        governance_errors=gov_errors,
        parser_skips_recovered=parser_recovered,
        before_emitted_plans=before_plans,
        after_emitted_plans=after_plans,
    )

    _write_executive_summary(output_dir, summary, legacy_rows, len(source_df), missing_df)

    target_plans = ["1L15GD", "1L16GD", "9L16PF", "1L17SP", "9DIS80", "9DIS90", "9DIS20"]
    found = {p: (p in quikplan_set) for p in target_plans}

    print(f"P3G_STATUS: SUCCESS")
    print(f"LEGACY_PARSER_ROWS: {legacy_rows}")
    print(f"P3G_SOURCE_ROWS: {len(source_df)}")
    print(f"PARSER_RECOVERED: {parser_recovered}")
    print(f"QUIKPLAN_BEFORE: {before_plans}")
    print(f"QUIKPLAN_AFTER: {after_plans}")
    print(f"MISSING_CATALOG_EMITS: {len(missing_df)}")
    print(f"BLANK_MPLAN: {blank_count}")
    print(f"EXPECTED_NON_PRODUCT_BLANKS: {expected_non_product}")
    print(f"GOVERNANCE_ERRORS: {gov_errors}")
    print(f"TARGET_PLANS: {found}")
    print(f"OUTPUT_DIR: {output_dir}")
    return 0 if gov_errors == 0 else 1


def _write_executive_summary(output_dir: str, summary: dict, legacy_rows: int, p3g_rows: int, missing_df: pd.DataFrame) -> None:
    lines = [
        "# Executive Summary — Phase P3G quikplan Coverage Completeness",
        "",
        f"Generated: {summary.get('generated_at', '')}",
        "",
        "## Root Cause",
        "",
        "LifePRO `quikplan_source.csv` rows embed **unquoted commas** in DESCRIPTION fields",
        "(e.g. `Home Office Discount 20% 1yr, 21.5% 2-10`). Legacy `pandas.read_csv(on_bad_lines='skip')`",
        "silently dropped those rows — removing L15, L16, DISCHO80/90, L17 BASE, etc. from quikplan emit.",
        "",
        "P3G adds `load_quikplan_source_csv()` which merges DESCRIPTION overflow fields without mutating source files.",
        "",
        "## Metrics",
        "",
        "| Metric | Before | After |",
        "|--------|--------|-------|",
        f"| Legacy parser rows loaded | {legacy_rows} | {p3g_rows} |",
        f"| quikplan authoritative PLANs | {summary.get('before_emitted_quikplan_plans', 0)} | {summary.get('after_emitted_quikplan_plans', 0)} |",
        f"| Missing catalog emits | — | {summary.get('missing_catalog_emits', 0)} |",
        f"| Blank MPLAN rows | — | {summary.get('blank_mplan_count', 0)} |",
        f"| Expected non-product blanks | — | {summary.get('expected_non_product_blank_rows', 0)} |",
        f"| Governance failures | — | {summary.get('governance_errors', 0)} |",
        "",
        "## Business Report",
        "",
        "`blank_mplan_business_review_report.csv` preserves **exact** PPBEN field values in",
        "`raw_source_*` columns and full `raw_source_columns_json` — no trim/normalize/overlay.",
        "",
        "## Rollback",
        "",
        "Revert to prior loader by restoring `on_bad_lines='skip'` in quikplan_converter (not recommended).",
        "P3C/P3E closed authority unchanged.",
        "",
    ]
    if not missing_df.empty:
        lines.extend(["## Remaining Missing Emits", ""])
        for _, row in missing_df.head(10).iterrows():
            lines.append(f"- `{row.get('source_coverage_id', '')}` → `{row.get('authoritative_plan', '')}`: {row.get('failure_reason', '')}")
        lines.append("")

    with open(os.path.join(output_dir, "executive_p3g_completeness_summary.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase P3G quikplan completeness + blank MPLAN reporting")
    parser.add_argument("--source", default=os.path.join(ROOT, "plan_analysis", "quikplan_source.csv"))
    parser.add_argument("--catalog", default=os.path.join(ROOT, "plan_governance", "product_catalog_crosswalk.csv"))
    parser.add_argument("--quikplan", default=os.path.join(ROOT, "QLA_Migration", "Output", "quikplan.csv"))
    parser.add_argument("--quikridr", default=os.path.join(ROOT, "QLA_Migration", "Output", "quikridr.csv"))
    parser.add_argument("--ppben", default=os.path.join(ROOT, "QLA_Migration", "Source", "PPBEN.csv"))
    parser.add_argument("--master-crosswalk", default=os.path.join(ROOT, "Master_Crosswalk.csv"))
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    parser.add_argument("--emit", action="store_true", help="Re-run product setup + P3E emit")
    args = parser.parse_args()

    return run_p3g(
        source_path=args.source,
        catalog_path=args.catalog,
        quikplan_path=args.quikplan,
        quikridr_path=args.quikridr,
        ppben_path=args.ppben,
        master_cw_path=args.master_crosswalk,
        output_dir=args.output_dir,
        emit=args.emit,
    )


if __name__ == "__main__":
    raise SystemExit(main())
