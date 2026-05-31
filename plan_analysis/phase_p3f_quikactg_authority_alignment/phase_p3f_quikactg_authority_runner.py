#!/usr/bin/env python3
"""
Phase P3F — quikactg MPLAN Authority Alignment runner.

Builds quikactg from PACTG (one row per PLAN_CODE) and applies the same closed
MPLAN resolver used for quikridr (P3E) without altering account pivot logic.
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

from qla_core.mplan_authority import validate_emitted_mplan, write_p3f_governance_outputs
from qla_core.product_catalog_authority import (
    allow_legacy_mplan_fallback,
    build_authoritative_mplan_resolver,
    closed_mplan_authority_enabled,
    load_closed_product_catalog,
    load_crosswalk_authority,
    load_quikplan_plan_set,
    strip_val,
)
from qla_core.quikactg_converter import convert_quikactg_from_pactg


def align_quikactg_mplan(
    pactg_path: str,
    quikplan_path: str,
    master_cw_path: str,
    catalog_path: str,
    rulebook_path: str,
    quikactg_path: str,
    *,
    closed_authority: bool,
    allow_legacy: bool,
    emit: bool,
) -> int:
    quikplan_set = load_quikplan_plan_set(quikplan_path)
    catalog = load_closed_product_catalog(catalog_path)
    authority = load_crosswalk_authority(master_cw_path, catalog_path)
    resolver = build_authoritative_mplan_resolver(
        catalog=catalog,
        legacy_product_map=authority.legacy_product_map,
        quikplan_plan_set=quikplan_set,
    )

    cw_df = pd.read_csv(master_cw_path, dtype=str, keep_default_na=False)
    cw_map = {strip_val(k): strip_val(v) for k, v in zip(cw_df.iloc[:, 0], cw_df.iloc[:, 1])}

    output_df, trace_df, stats = convert_quikactg_from_pactg(
        pactg_path,
        cw_map=cw_map,
        resolver=resolver if closed_authority else None,
        quikplan_plan_set=quikplan_set,
        closed_authority=closed_authority,
        allow_legacy=allow_legacy,
        rulebook_path=rulebook_path,
    )

    passed, val_stats = validate_emitted_mplan(output_df, quikplan_set)
    stats.update(val_stats)

    if emit:
        output_df.to_csv(quikactg_path, index=False)

    write_p3f_governance_outputs(
        OUTPUT_DIR,
        trace_df,
        closed_enabled=closed_authority,
        allow_legacy=allow_legacy,
        emitted_rows=len(output_df),
        validation_passed=passed and closed_authority,
        pactg_stats=stats,
    )

    print(f"P3F_STATUS: {'SUCCESS' if passed or not closed_authority else 'VALIDATION_FAILED'}")
    print(f"CLOSED_MPLAN_AUTHORITY: {'Y' if closed_authority else 'N'}")
    print(f"LEGACY_MPLAN_FALLBACK: {'Y' if allow_legacy else 'N'}")
    print(f"EMITTED_ROWS: {len(output_df)}")
    print(f"VALIDATION: {val_stats}")
    print(f"OUTPUT_DIR: {OUTPUT_DIR}")
    return 0 if (passed or not closed_authority) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase P3F quikactg MPLAN authority alignment")
    parser.add_argument(
        "--pactg",
        default=os.path.join(ROOT, "QLA_Migration", "Source", "PACTG_Accounting_Extract20260427.csv"),
    )
    parser.add_argument("--quikplan", default=os.path.join(ROOT, "QLA_Migration", "Output", "quikplan.csv"))
    parser.add_argument("--quikactg", default=os.path.join(ROOT, "QLA_Migration", "Output", "quikactg.csv"))
    parser.add_argument("--rulebook", default=os.path.join(ROOT, "Sync_Rulebook_quikactg.csv"))
    parser.add_argument("--master-crosswalk", default=os.path.join(ROOT, "Master_Crosswalk.csv"))
    parser.add_argument("--product-catalog", default=os.path.join(ROOT, "plan_governance", "product_catalog_crosswalk.csv"))
    parser.add_argument("--closed-mplan-authority", action="store_true")
    parser.add_argument("--allow-legacy-mplan-fallback", action="store_true")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()

    if args.allow_legacy_mplan_fallback:
        os.environ["QLA_ALLOW_LEGACY_MPLAN_FALLBACK"] = "1"
    if args.closed_mplan_authority:
        os.environ["QLA_CLOSED_MPLAN_AUTHORITY"] = "1"

    closed = args.closed_mplan_authority or closed_mplan_authority_enabled()
    allow_legacy = args.allow_legacy_mplan_fallback or allow_legacy_mplan_fallback()

    return align_quikactg_mplan(
        args.pactg,
        args.quikplan,
        args.master_crosswalk,
        args.product_catalog,
        args.rulebook,
        args.quikactg,
        closed_authority=closed,
        allow_legacy=allow_legacy,
        emit=args.emit,
    )


if __name__ == "__main__":
    raise SystemExit(main())
