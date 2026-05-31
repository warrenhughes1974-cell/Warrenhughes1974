#!/usr/bin/env python3
"""
Phase P2C/P3/P3B/P3C — Product Setup Conversion subprocess runner.

Calls shared qla_core.quikplan_converter; emits governance diagnostics.
UAT overlay: --uat-overlay or QLA_PRODUCT_UAT_OVERLAY=1 (isolated; batch CROSSWALK_OVERLAY unchanged).
Strict authority: --strict-authority or QLA_STRICT_PRODUCT_AUTHORITY=1 (UAT overlay only).
Closed catalog: --closed-product-authority or QLA_CLOSED_PRODUCT_AUTHORITY=1 (default ON with UAT overlay).
Legacy rollback: --allow-legacy-product-fallback or QLA_ALLOW_LEGACY_PRODUCT_FALLBACK=1.
Quarantine: QLA_PRODUCT_AUTHORITY_QUARANTINE=1 (optional; default off).
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from qla_core.crosswalk_enrichment import load_policy_form_crosswalk, resolve_product_setup_overlay_config
from qla_core.product_authority_diagnostics import (
    allow_legacy_product_fallback,
    apply_closed_authority_emit_filter,
    apply_quarantine_filter,
    closed_product_authority_enabled,
    product_authority_quarantine_enabled,
    run_closed_product_authority_validation,
    run_strict_authority_validation,
    strict_product_authority_enabled,
    write_closed_product_authority_summary,
)
from qla_core.product_catalog_authority import load_closed_product_catalog
from qla_core.quikplan_converter import prepare_quikplan_source, run_quikplan_conversion
from qla_core.quikplan_source_loader import load_quikplan_source_csv

sys.path.insert(0, SCRIPT_DIR)

from product_setup_governance_engine import run_product_governance_diagnostics


def governance_block_enabled() -> bool:
    return os.environ.get("QLA_PRODUCT_GOVERNANCE_BLOCK", "0").strip().lower() in ("1", "true", "yes")


def _load_source_df(source_path: str) -> pd.DataFrame:
    df, _ = load_quikplan_source_csv(source_path, collect_trace=False)
    df.columns = [str(c).strip() for c in df.columns]
    return prepare_quikplan_source(df)


def main():
    parser = argparse.ArgumentParser(description="Product Setup Conversion runner")
    parser.add_argument("--source", default=os.path.join(ROOT, "plan_analysis", "quikplan_source.csv"))
    parser.add_argument("--rulebook", default=os.path.join(ROOT, "QLA_Migration", "Configs", "Sync_Rulebook_quikplan.csv"))
    parser.add_argument("--translation", default=os.path.join(ROOT, "Master_Value_Translation.csv"))
    parser.add_argument("--plan-crosswalk", default=os.path.join(ROOT, "Master_Crosswalk.csv"))
    parser.add_argument("--product-catalog", default=os.path.join(ROOT, "plan_governance", "product_catalog_crosswalk.csv"))
    parser.add_argument("--policy-form-crosswalk", default=os.path.join(
        ROOT, "docs", "plan_conversion_reference", "Policy Form Crosswalk 5.22.26.xlsx",
    ))
    parser.add_argument("--pcomp-dir", default=os.path.join(ROOT, "plan_analysis"))
    parser.add_argument("--stage-dir", default=os.path.join(ROOT, "plan_governance", "staged"))
    parser.add_argument("--manifest-dir", default=os.path.join(ROOT, "plan_governance", "manifests"))
    parser.add_argument("--analysis-dir", default=os.path.join(ROOT, "plan_analysis", "phase_p3c_closed_product_authority"))
    parser.add_argument("--ridr-reference", default=os.path.join(ROOT, "QLA_Migration", "Output", "quikridr.csv"))
    parser.add_argument("--output-dir", default="", help="Emit target when --emit set")
    parser.add_argument("--emit", action="store_true")
    parser.add_argument(
        "--uat-overlay",
        action="store_true",
        help="Enable Policy Form Crosswalk authority (UAT cutover — isolated from batch)",
    )
    parser.add_argument(
        "--strict-authority",
        action="store_true",
        help="Strict UAT product authority — flag/block unauthorized PLAN emissions",
    )
    parser.add_argument(
        "--closed-product-authority",
        action="store_true",
        help="Closed product catalog authority — only authoritative catalog PLANs may emit",
    )
    parser.add_argument(
        "--allow-legacy-product-fallback",
        action="store_true",
        help="Rollback mode — allow legacy fallback PLAN emit with reporting (disables closed authority)",
    )
    parser.add_argument(
        "--no-closed-product-authority",
        action="store_true",
        help="Explicitly disable closed authority for UAT overlay (rollback)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.translation):
        alt = os.path.join(ROOT, "QLA_Migration", "Mapping", "Master_Value_Translation.csv")
        if os.path.isfile(alt):
            args.translation = alt

    os.makedirs(args.stage_dir, exist_ok=True)
    os.makedirs(args.manifest_dir, exist_ok=True)
    os.makedirs(args.analysis_dir, exist_ok=True)

    if args.no_closed_product_authority:
        os.environ["QLA_CLOSED_PRODUCT_AUTHORITY"] = "0"

    allow_legacy = args.allow_legacy_product_fallback or allow_legacy_product_fallback()
    if allow_legacy:
        os.environ["QLA_ALLOW_LEGACY_PRODUCT_FALLBACK"] = "1"

    strict_authority = args.strict_authority or strict_product_authority_enabled()
    closed_authority = closed_product_authority_enabled(
        uat_overlay=args.uat_overlay,
        explicit=args.closed_product_authority if args.closed_product_authority else None,
    )
    quarantine = product_authority_quarantine_enabled()

    overlay = resolve_product_setup_overlay_config(
        crosswalk_path=args.policy_form_crosswalk if os.path.isfile(args.policy_form_crosswalk) else None,
        uat_overlay=args.uat_overlay,
    )
    if overlay.enabled and not overlay.crosswalk_map and os.path.isfile(args.policy_form_crosswalk):
        overlay.crosswalk_path = args.policy_form_crosswalk
        overlay.crosswalk_map = load_policy_form_crosswalk(args.policy_form_crosswalk)

    df = run_quikplan_conversion(
        source_path=args.source,
        rulebook_path=args.rulebook,
        trans_path=args.translation,
        cw_path=args.plan_crosswalk,
        lookup_dir=args.pcomp_dir,
        overlay_config=overlay,
        product_catalog_path=args.product_catalog,
    )

    source_df = _load_source_df(args.source)
    unauthorized_manifest = pd.DataFrame()
    layer_diagnostics = pd.DataFrame()
    hold_manifest = pd.DataFrame()
    strict_error_count = 0
    closed_unauthorized = pd.DataFrame()
    closed_trace = pd.DataFrame()
    closed_config_errors = pd.DataFrame()
    closed_error_count = 0

    if closed_authority and os.path.isfile(args.product_catalog):
        closed_unauthorized, closed_trace, closed_config_errors, closed_error_count, approved_df = (
            run_closed_product_authority_validation(
                df,
                source_df,
                source_path=args.source,
                catalog_path=args.product_catalog,
                overlay_config=overlay,
                allow_legacy=allow_legacy,
            )
        )
        closed_unauthorized.to_csv(
            os.path.join(args.analysis_dir, "unauthorized_product_emit_manifest.csv"), index=False,
        )
        closed_trace.to_csv(
            os.path.join(args.analysis_dir, "product_authority_resolution_trace.csv"), index=False,
        )
        closed_config_errors.to_csv(
            os.path.join(args.analysis_dir, "product_catalog_configuration_errors.csv"), index=False,
        )

        if not allow_legacy:
            if quarantine and not closed_unauthorized.empty:
                approved_df, hold_manifest = apply_closed_authority_emit_filter(
                    df, source_df, closed_trace, quarantine=True,
                )
                hold_manifest.to_csv(
                    os.path.join(args.analysis_dir, "product_authority_hold_manifest.csv"), index=False,
                )
            df = approved_df

        catalog = load_closed_product_catalog(args.product_catalog)
        emit_plans = df["PLAN"].map(lambda v: str(v).strip()).tolist() if "PLAN" in df.columns else []
        blocking_config_errors = sum(
            1 for row in catalog.config_errors if str(row.get("severity", "ERROR")).upper() == "ERROR"
        )
        write_closed_product_authority_summary(
            os.path.join(args.analysis_dir, "closed_product_authority_summary.json"),
            closed_enabled=closed_authority,
            allow_legacy=allow_legacy,
            uat_overlay=overlay.enabled,
            strict_authority=strict_authority,
            catalog=catalog,
            unauthorized_count=len(closed_unauthorized),
            config_error_count=blocking_config_errors,
            emitted_rows=len(df),
            approved_plans=emit_plans,
            validation_passed=(
                len(closed_unauthorized) == 0
                and all(" " not in p for p in emit_plans if p)
                and all(p in catalog.authoritative_plan_set for p in emit_plans if p)
            ),
        )

    if strict_authority and overlay.enabled and os.path.isfile(args.policy_form_crosswalk):
        p3b_dir = os.path.join(ROOT, "plan_analysis", "phase_p3b_strict_authority")
        os.makedirs(p3b_dir, exist_ok=True)
        unauthorized_manifest, layer_diagnostics, strict_error_count = run_strict_authority_validation(
            df, source_df, args.policy_form_crosswalk, overlay,
        )
        unauthorized_manifest.to_csv(os.path.join(p3b_dir, "unauthorized_plan_emit_manifest.csv"), index=False)
        layer_diagnostics.to_csv(os.path.join(p3b_dir, "product_authority_layer_diagnostics.csv"), index=False)
        if quarantine and not unauthorized_manifest.empty:
            df, hold_manifest = apply_quarantine_filter(df, source_df, unauthorized_manifest)
            hold_manifest.to_csv(os.path.join(p3b_dir, "product_authority_hold_manifest.csv"), index=False)

    staged_path = os.path.join(args.stage_dir, "quikplan_staged.csv")
    df.to_csv(staged_path, index=False)

    diag_df, warn_count, err_count = run_product_governance_diagnostics(
        df,
        source_path=args.source,
        ridr_path=args.ridr_reference if os.path.isfile(args.ridr_reference) else "",
        crosswalk_path=args.policy_form_crosswalk if os.path.isfile(args.policy_form_crosswalk) else "",
        overlay_enabled=overlay.enabled,
        strict_authority=strict_authority,
        closed_authority=closed_authority,
        allow_legacy=allow_legacy,
        source_df=source_df,
        overlay_config=overlay,
        product_catalog_path=args.product_catalog,
        closed_unauthorized=closed_unauthorized,
        closed_config_errors=closed_config_errors,
    )
    if strict_authority and overlay.enabled:
        err_count = max(err_count, strict_error_count)
    if closed_authority and not allow_legacy:
        err_count = max(err_count, closed_error_count)
    diag_path = os.path.join(args.manifest_dir, "product_governance_diagnostics.csv")
    diag_df.to_csv(diag_path, index=False)

    block = governance_block_enabled()
    emit_allowed = args.emit and (not block or err_count == 0)
    emitted_path = ""
    if emit_allowed and args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        emitted_path = os.path.join(args.output_dir, "quikplan.csv")
        planvalopt_y = int((df["PLANVALOPT"] == "Y").sum()) if "PLANVALOPT" in df.columns else 0
        df.to_csv(emitted_path, index=False)
        print(f"RATE_VARIATION_FLAGS: PLANVALOPT_Y={planvalopt_y}")
    elif args.emit and block and err_count > 0:
        print(f"PRODUCT_SETUP_EMIT_BLOCKED: Y (QLA_PRODUCT_GOVERNANCE_BLOCK=1, errors={err_count})")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "SUCCESS" if err_count == 0 or not block else "BLOCKED"
    print(f"PRODUCT_SETUP_STATUS: {status}")
    print(f"RUN_TIMESTAMP: {ts}")
    print(f"SOURCE_ROWS: {len(df)}")
    print(f"STAGED_ROWS: {len(df)}")
    print(f"EMITTED_ROWS: {len(df) if emit_allowed else 0}")
    print(f"UNIQUE_PLAN: {df['PLAN'].nunique() if 'PLAN' in df.columns else 0}")
    print(f"COLUMN_COUNT: {len(df.columns)}")
    print(f"CROSSWALK_OVERLAY: {'Y' if overlay.enabled else 'N'}")
    print(f"PRODUCT_UAT_OVERLAY: {'Y' if overlay.enabled else 'N'}")
    print(f"STRICT_PRODUCT_AUTHORITY: {'Y' if strict_authority else 'N'}")
    print(f"CLOSED_PRODUCT_AUTHORITY: {'Y' if closed_authority else 'N'}")
    print(f"LEGACY_PRODUCT_FALLBACK: {'Y' if allow_legacy else 'N'}")
    print(f"LEGACY_FALLBACK_STATUS: {'CLOSED_PRODUCT_AUTHORITY_DISABLED' if allow_legacy else 'CLOSED_PRODUCT_AUTHORITY_ACTIVE'}")
    print(f"PRODUCT_AUTHORITY_QUARANTINE: {'Y' if quarantine else 'N'}")
    print(f"UNAUTHORIZED_PLAN_COUNT: {len(unauthorized_manifest)}")
    print(f"CLOSED_UNAUTHORIZED_COUNT: {len(closed_unauthorized)}")
    print(f"CATALOG_CONFIG_FINDINGS: {len(closed_config_errors)}")
    print(f"CATALOG_CONFIG_ERROR_COUNT: {sum(1 for _, r in closed_config_errors.iterrows() if str(r.get('severity', 'ERROR')).upper() == 'ERROR') if not closed_config_errors.empty else 0}")
    print(f"QUARANTINE_HELD_ROWS: {len(hold_manifest)}")
    print(f"DIAGNOSTIC_WARNINGS: {warn_count}")
    print(f"DIAGNOSTIC_ERRORS: {err_count}")
    print(f"GOVERNANCE_BLOCK: {'Y' if block else 'N'}")
    print(f"STAGED_PATH: {staged_path}")
    print(f"EMITTED_PATH: {emitted_path or 'NOT_EMITTED'}")
    print(f"DIAGNOSTICS_PATH: {diag_path}")
    print(f"CLOSED_AUTHORITY_DIR: {args.analysis_dir}")
    print(f"RULEBOOK_LINEAGE: Sync_Rulebook_quikplan.csv")
    return 0 if status == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
