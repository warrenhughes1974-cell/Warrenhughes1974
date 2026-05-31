#!/usr/bin/env python3
"""
Phase P3E — quikridr MPLAN Authority Alignment runner.

Re-aligns quikridr.MPLAN against P3C authoritative quikplan catalog without
rewriting stable MPHASE/MRIDRID/relationship logic.
"""

from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))
OUTPUT_DIR = SCRIPT_DIR

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from qla_core.mplan_authority import (
    apply_mplan_emit_filter,
    resolution_to_trace_row,
    validate_emitted_quikridr,
    write_p3e_governance_outputs,
)
from qla_core.product_catalog_authority import (
    allow_legacy_mplan_fallback,
    build_authoritative_mplan_resolver,
    closed_mplan_authority_enabled,
    load_closed_product_catalog,
    load_crosswalk_authority,
    load_quikplan_plan_set,
    resolve_authoritative_mplan,
    split_master_crosswalk_rows,
    strip_val,
)


def align_quikridr_mplan(
    quikridr_path: str,
    quikplan_path: str,
    ppben_path: str,
    master_cw_path: str,
    catalog_path: str,
    *,
    closed_authority: bool,
    allow_legacy: bool,
    quarantine: bool,
    emit: bool,
) -> int:
    qr = pd.read_csv(quikridr_path, dtype=str, keep_default_na=False)
    schema = list(qr.columns)

    quikplan_set = load_quikplan_plan_set(quikplan_path)
    catalog = load_closed_product_catalog(catalog_path)
    authority = load_crosswalk_authority(master_cw_path, catalog_path)
    resolver = build_authoritative_mplan_resolver(
        catalog=catalog,
        legacy_product_map=authority.legacy_product_map,
        quikplan_plan_set=quikplan_set,
    )

    ppben = pd.read_csv(ppben_path, encoding="latin1", dtype=str, on_bad_lines="skip", keep_default_na=False)
    ppben.columns = [strip_val(c) for c in ppben.columns]
    if "POLICY_NUMBER" in ppben.columns:
        ppben = ppben[~ppben["POLICY_NUMBER"].astype(str).str.contains("-", na=False)]
    if "BENEFIT_SEQ" in ppben.columns:
        ppben["BENEFIT_SEQ"] = ppben["BENEFIT_SEQ"].astype(str).str.strip().str.replace(".0", "", regex=False)
        ppben = ppben[ppben["BENEFIT_SEQ"].apply(lambda x: x.isdigit() and int(x) >= 1)].reset_index(drop=True)

    cw_df = pd.read_csv(master_cw_path, dtype=str, keep_default_na=False)
    cw_df.columns = ["Old_Value", "New_Value"]
    cw_map = {strip_val(k): strip_val(v) for k, v in zip(cw_df.iloc[:, 0], cw_df.iloc[:, 1])}

    trace_rows = []
    output_rows = []

    for i, qr_row in qr.iterrows():
        mpolicy = strip_val(qr_row.get("MPOLICY", ""))
        mphase = strip_val(qr_row.get("MPHASE", "")) or "1"
        src_plan = ""
        src_benefit_type = ""
        src_row_num = i + 2
        if i < len(ppben):
            pp_row = ppben.iloc[i]
            plan_col = "PLAN_CODE" if "PLAN_CODE" in ppben.columns else "PLAN_CODE "
            src_plan = strip_val(pp_row.get(plan_col, pp_row.get("PLAN_CODE", "")))
            src_benefit_type = str(pp_row.get("BENEFIT_TYPE", ""))
            src_row_num = int(pp_row.name) + 2 if pp_row.name is not None else i + 2

        candidate = strip_val(qr_row.get("MPLAN", ""))
        if closed_authority:
            legacy_candidate = cw_map.get(src_plan, src_plan) if src_plan else candidate
            resolution = resolve_authoritative_mplan(
                src_plan, legacy_candidate or candidate, resolver, allow_legacy=allow_legacy,
            )
            resolved_mplan = resolution.resolved_mplan
        else:
            from qla_core.product_catalog_authority import MplanResolution
            resolution = MplanResolution(
                resolved_mplan=candidate,
                resolution_path="UNCHANGED",
                fallback_value=candidate,
                is_authoritative=candidate in quikplan_set,
                source_plan_code=src_plan,
                candidate_mplan=candidate,
            )
            resolved_mplan = candidate

        row_data = {c: strip_val(qr_row.get(c, "")) for c in schema}
        row_data["MPLAN"] = resolved_mplan

        trace_rows.append(resolution_to_trace_row(
            resolution,
            source_file=os.path.basename(ppben_path),
            source_row_number=src_row_num,
            mpolicy=mpolicy,
            mphase=mphase,
            row_data=row_data,
            quikplan_plan_set=quikplan_set,
            allow_legacy=allow_legacy,
            source_benefit_type=src_benefit_type,
        ))
        output_rows.append([row_data[c] for c in schema])

    trace_df = pd.DataFrame(trace_rows)
    if quarantine and closed_authority:
        output_rows, _ = apply_mplan_emit_filter(output_rows, schema, trace_df, quarantine=True)

    aligned_df = pd.DataFrame(output_rows, columns=schema)
    passed, val_stats = validate_emitted_quikridr(aligned_df, quikplan_set)

    if emit:
        aligned_df.to_csv(quikridr_path, index=False)

    write_p3e_governance_outputs(
        OUTPUT_DIR,
        trace_df,
        closed_enabled=closed_authority,
        allow_legacy=allow_legacy,
        emitted_rows=len(aligned_df),
        validation_passed=passed and closed_authority,
    )

    print(f"P3E_STATUS: {'SUCCESS' if passed or not closed_authority else 'VALIDATION_FAILED'}")
    print(f"CLOSED_MPLAN_AUTHORITY: {'Y' if closed_authority else 'N'}")
    print(f"LEGACY_MPLAN_FALLBACK: {'Y' if allow_legacy else 'N'}")
    print(f"ALIGNED_ROWS: {len(aligned_df)}")
    print(f"VALIDATION: {val_stats}")
    print(f"OUTPUT_DIR: {OUTPUT_DIR}")
    return 0 if (passed or not closed_authority) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase P3E quikridr MPLAN authority alignment")
    parser.add_argument("--quikridr", default=os.path.join(ROOT, "QLA_Migration", "Output", "quikridr.csv"))
    parser.add_argument("--quikplan", default=os.path.join(ROOT, "QLA_Migration", "Output", "quikplan.csv"))
    parser.add_argument("--ppben", default=os.path.join(ROOT, "QLA_Migration", "Source", "PPBEN.csv"))
    parser.add_argument("--master-crosswalk", default=os.path.join(ROOT, "Master_Crosswalk.csv"))
    parser.add_argument("--product-catalog", default=os.path.join(ROOT, "plan_governance", "product_catalog_crosswalk.csv"))
    parser.add_argument("--closed-mplan-authority", action="store_true")
    parser.add_argument("--allow-legacy-mplan-fallback", action="store_true")
    parser.add_argument("--quarantine", action="store_true")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()

    if args.allow_legacy_mplan_fallback:
        os.environ["QLA_ALLOW_LEGACY_MPLAN_FALLBACK"] = "1"
    if args.closed_mplan_authority:
        os.environ["QLA_CLOSED_MPLAN_AUTHORITY"] = "1"

    closed = args.closed_mplan_authority or closed_mplan_authority_enabled()
    allow_legacy = args.allow_legacy_mplan_fallback or allow_legacy_mplan_fallback()

    return align_quikridr_mplan(
        args.quikridr,
        args.quikplan,
        args.ppben,
        args.master_crosswalk,
        args.product_catalog,
        closed_authority=closed,
        allow_legacy=allow_legacy,
        quarantine=args.quarantine,
        emit=args.emit,
    )


if __name__ == "__main__":
    raise SystemExit(main())
