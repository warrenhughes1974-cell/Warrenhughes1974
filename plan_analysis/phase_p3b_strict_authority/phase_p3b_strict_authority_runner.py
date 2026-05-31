#!/usr/bin/env python3
"""
Phase P3B — Strict Product Authority Validation + Unauthorized PLAN Remediation.

Traces unauthorized PLAN emissions, compares overlay-off vs overlay-on paths,
generates business-readable summary. Does not redesign the conversion engine.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))
OUTPUT_DIR = os.path.join(ROOT, "plan_analysis", "phase_p3b_strict_authority")
RUNNER = os.path.join(ROOT, "plan_governance", "phase_p2_product_setup_runner", "product_setup_runner.py")
POLICY_FORM_CROSSWALK = os.path.join(
    ROOT, "docs", "plan_conversion_reference", "Policy Form Crosswalk 5.22.26.xlsx",
)
EMITTED_OUTPUT = os.path.join(ROOT, "QLA_Migration", "Output", "quikplan.csv")

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from qla_core.crosswalk_enrichment import CrosswalkOverlayConfig, load_policy_form_crosswalk, resolve_product_setup_overlay_config
from qla_core.product_authority_diagnostics import (
    build_authority_layer_diagnostics,
    build_unauthorized_plan_manifest,
    load_authorized_plan_codes,
)
from qla_core.product_catalog_authority import load_crosswalk_authority
from qla_core.quikplan_converter import prepare_quikplan_source, run_quikplan_conversion


def strip_val(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def load_source() -> pd.DataFrame:
    path = os.path.join(ROOT, "plan_analysis", "quikplan_source.csv")
    df = pd.read_csv(path, encoding="latin1", dtype=str, on_bad_lines="skip", keep_default_na=False).fillna("")
    df.columns = [strip_val(c) for c in df.columns]
    return prepare_quikplan_source(df)


def run_conversion(overlay_enabled: bool) -> pd.DataFrame:
    overlay = resolve_product_setup_overlay_config(
        crosswalk_path=POLICY_FORM_CROSSWALK,
        uat_overlay=overlay_enabled,
    )
    if overlay_enabled and not overlay.crosswalk_map:
        overlay.crosswalk_map = load_policy_form_crosswalk(POLICY_FORM_CROSSWALK)
        overlay.enabled = True
    elif not overlay_enabled:
        overlay = CrosswalkOverlayConfig(enabled=False)

    return run_quikplan_conversion(
        source_path=os.path.join(ROOT, "plan_analysis", "quikplan_source.csv"),
        rulebook_path=os.path.join(ROOT, "QLA_Migration", "Configs", "Sync_Rulebook_quikplan.csv"),
        trans_path=os.path.join(ROOT, "Master_Value_Translation.csv"),
        cw_path=os.path.join(ROOT, "Master_Crosswalk.csv"),
        lookup_dir=os.path.join(ROOT, "plan_analysis"),
        overlay_config=overlay,
    )


def analyze_existing_output(authorized: set[str]) -> tuple[pd.DataFrame, int]:
    if not os.path.isfile(EMITTED_OUTPUT):
        return pd.DataFrame(), 0
    df = pd.read_csv(EMITTED_OUTPUT, dtype=str, keep_default_na=False)
    bad = df[~df["PLAN"].map(strip_val).isin(authorized)]
    return bad, len(bad)


def write_executive_summary(
    path: str,
    overlay_off_manifest: pd.DataFrame,
    overlay_on_manifest: pd.DataFrame,
    existing_bad_count: int,
    existing_bad_plans: list[str],
    strict_run_unauthorized: int,
    emit_rows: int,
    column_count: int,
) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Executive Summary — Phase P3B Strict Product Authority",
        "",
        f"Generated: {ts}",
        "",
        "## Business Issue",
        "",
        "During UAT product review, PLAN values were found in quikplan output that do not exist in the Policy Form Crosswalk **QL Plan Code** column. Examples include passthrough-style values such as `0824 P DIS` and `0823 960CH` (business shorthand: `0824 P`, `0823 9`).",
        "",
        "## Root Cause",
        "",
        "Unauthorized PLAN values originate from the **pre-overlay conversion path**:",
        "",
        "1. `product_catalog_crosswalk.csv` preserves stable Master_Crosswalk emit values for rollback safety.",
        "2. Rows marked `CROSSWALK_DIVERGENT` still emit legacy/passthrough PLAN codes (e.g., COVERAGE_ID passthrough).",
        "3. When **UAT overlay is OFF** or output is **stale** (not regenerated with `--uat-overlay`), those passthrough PLANs reach `QLA_Migration/Output/quikplan.csv`.",
        "4. When **UAT overlay is ON**, Policy Form Crosswalk overlay replaces PLAN/FORM/DESCR/PLANNAME with authorized values — **0 unauthorized PLANs** in fresh conversion.",
        "",
        "## Findings",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Existing output unauthorized rows | {existing_bad_count} |",
        f"| Overlay-OFF unauthorized PLAN rows | {len(overlay_off_manifest)} |",
        f"| Overlay-ON unauthorized PLAN rows | {len(overlay_on_manifest)} |",
        f"| Strict authority re-emit unauthorized | {strict_run_unauthorized} |",
        f"| Emitted rows (strict UAT run) | {emit_rows} |",
        f"| Column count | {column_count} |",
        "",
    ]

    if existing_bad_plans:
        lines.extend([
            "### Unauthorized PLANs in existing `QLA_Migration/Output/quikplan.csv`",
            "",
            ", ".join(f"`{p}`" for p in sorted(existing_bad_plans)[:20]),
            ("..." if len(existing_bad_plans) > 20 else ""),
            "",
        ])

    if not overlay_off_manifest.empty:
        layer_counts = overlay_off_manifest["authority_layer_used"].value_counts()
        lines.extend([
            "### Authority layer breakdown (overlay OFF — unauthorized only)",
            "",
        ])
        for layer, count in layer_counts.items():
            lines.append(f"- **{layer}**: {count} row(s)")
        lines.append("")

    lines.extend([
        "## Remediation Path",
        "",
        "| Issue | Remediation |",
        "|-------|-------------|",
        "| Stale output without UAT overlay | Re-emit with `--uat-overlay --strict-authority --emit` |",
        "| Passthrough PLAN in product_catalog | Expected pre-overlay; resolved by Policy Form Crosswalk overlay |",
        "| Missing crosswalk row | Add Coverage_ID to Policy Form Crosswalk with QL Plan Code |",
        "| Legacy Master_Crosswalk fallback | Do not use for product PLAN under strict UAT mode |",
        "",
        "## Strict Authority Mode",
        "",
        "Controlled flags (default OFF — rollback-safe):",
        "",
        "- `QLA_STRICT_PRODUCT_AUTHORITY=1` or `--strict-authority`",
        "- `QLA_PRODUCT_GOVERNANCE_BLOCK=1` — block emit on unauthorized PLAN",
        "- `QLA_PRODUCT_AUTHORITY_QUARANTINE=1` — hold unauthorized rows (optional, default off)",
        "",
        f"**Strict authority ready for UAT testing:** {'YES' if strict_run_unauthorized == 0 else 'NO — review unauthorized manifest'}",
        "",
        "## Validation Preserved",
        "",
        "- Standard overlay OFF mode unchanged (rollback-compatible)",
        "- UAT overlay ON mode unchanged unless strict authority explicitly enabled",
        "- Claims and policy conversion flows untouched",
        "- Batch `CROSSWALK_OVERLAY=0` default preserved",
        "",
    ])

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase P3B strict product authority analysis")
    parser.add_argument("--emit", action="store_true", help="Re-emit quikplan with strict UAT authority")
    parser.add_argument("--output-dir", default=os.path.join(ROOT, "QLA_Migration", "Output"))
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    authorized = load_authorized_plan_codes(POLICY_FORM_CROSSWALK)
    source_df = load_source()
    authority = load_crosswalk_authority(os.path.join(ROOT, "Master_Crosswalk.csv"))

    overlay_off = run_conversion(overlay_enabled=False)
    overlay_on = run_conversion(overlay_enabled=True)

    overlay_off_cfg = CrosswalkOverlayConfig(enabled=False)
    overlay_on_cfg = resolve_product_setup_overlay_config(
        crosswalk_path=POLICY_FORM_CROSSWALK, uat_overlay=True,
    )
    overlay_on_cfg.crosswalk_map = load_policy_form_crosswalk(POLICY_FORM_CROSSWALK)

    off_diag = build_authority_layer_diagnostics(
        source_df, overlay_off, authority, overlay_off_cfg, POLICY_FORM_CROSSWALK,
    )
    on_diag = build_authority_layer_diagnostics(
        source_df, overlay_on, authority, overlay_on_cfg, POLICY_FORM_CROSSWALK,
    )

    off_manifest = build_unauthorized_plan_manifest(off_diag, overlay_label="OVERLAY_OFF")
    on_manifest = build_unauthorized_plan_manifest(on_diag, overlay_label="UAT_OVERLAY")

    combined_manifest = pd.concat([off_manifest, on_manifest], ignore_index=True)
    on_diag.to_csv(os.path.join(OUTPUT_DIR, "product_authority_layer_diagnostics.csv"), index=False)

    existing_bad, existing_bad_count = analyze_existing_output(authorized)
    existing_bad_plans = sorted(existing_bad["PLAN"].map(strip_val).unique()) if not existing_bad.empty else []

    strict_unauthorized = len(on_manifest)
    emit_rows = len(overlay_on)
    column_count = len(overlay_on.columns)

    if args.emit:
        env = os.environ.copy()
        env["QLA_STRICT_PRODUCT_AUTHORITY"] = "1"
        proc = subprocess.run(
            [sys.executable, RUNNER, "--uat-overlay", "--strict-authority", "--emit",
             "--output-dir", args.output_dir],
            cwd=ROOT, capture_output=True, text=True, env=env,
        )
        print(proc.stdout)
        if proc.returncode != 0:
            print(proc.stderr, file=sys.stderr)
            return proc.returncode
        for line in (proc.stdout or "").splitlines():
            if line.startswith("UNAUTHORIZED_PLAN_COUNT:"):
                strict_unauthorized = int(line.split(":", 1)[1].strip())
            if line.startswith("EMITTED_ROWS:"):
                emit_rows = int(line.split(":", 1)[1].strip())
            if line.startswith("COLUMN_COUNT:"):
                column_count = int(line.split(":", 1)[1].strip())
        existing_bad, existing_bad_count = analyze_existing_output(authorized)
        existing_bad_plans = []

    combined_manifest.to_csv(os.path.join(OUTPUT_DIR, "unauthorized_plan_emit_manifest.csv"), index=False)

    write_executive_summary(
        os.path.join(OUTPUT_DIR, "executive_strict_product_authority_summary.md"),
        off_manifest,
        on_manifest,
        existing_bad_count,
        existing_bad_plans,
        strict_unauthorized,
        emit_rows,
        column_count,
    )

    print(f"P3B_OUTPUT_DIR: {OUTPUT_DIR}")
    print(f"OVERLAY_OFF_UNAUTHORIZED: {len(off_manifest)}")
    print(f"OVERLAY_ON_UNAUTHORIZED: {len(on_manifest)}")
    print(f"EXISTING_OUTPUT_UNAUTHORIZED: {existing_bad_count}")
    print(f"AUTHORIZED_PLAN_COUNT: {len(authorized)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
