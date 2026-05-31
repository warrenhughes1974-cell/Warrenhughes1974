#!/usr/bin/env python3
"""
Phase P2A — Parallel validation: qla_core quikplan converter vs baseline output.

Generates diff artifacts in plan_analysis/phase_p2a_validation/.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))
DEFAULT_OUTPUT = SCRIPT_DIR

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from qla_core.crosswalk_enrichment import resolve_crosswalk_overlay_config
from qla_core.quikplan_converter import run_quikplan_conversion


def strip_val(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def main():
    parser = argparse.ArgumentParser(description="Phase P2A quikplan parallel validation")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    source_path = os.path.join(ROOT, "plan_analysis", "quikplan_source.csv")
    pcomp_dir = os.path.join(ROOT, "plan_analysis")
    rulebook_path = os.path.join(ROOT, "QLA_Migration", "Configs", "Sync_Rulebook_quikplan.csv")
    trans_path = os.path.join(ROOT, "Master_Value_Translation.csv")
    if not os.path.isfile(trans_path):
        trans_path = os.path.join(ROOT, "QLA_Migration", "Mapping", "Master_Value_Translation.csv")
    cw_path = os.path.join(ROOT, "Master_Crosswalk.csv")
    baseline_path = os.path.join(ROOT, "QLA_Migration", "Output", "quikplan.csv")

    overlay = resolve_crosswalk_overlay_config()
    generated = run_quikplan_conversion(
        source_path=source_path,
        rulebook_path=rulebook_path,
        trans_path=trans_path,
        cw_path=cw_path,
        lookup_dir=pcomp_dir,
        overlay_config=overlay,
    )

    gen_path = os.path.join(args.output_dir, "quikplan_generated_p2a.csv")
    generated.to_csv(gen_path, index=False)

    baseline = pd.read_csv(baseline_path, dtype=str, keep_default_na=False).fillna("")
    baseline.columns = [strip_val(c) for c in baseline.columns]
    generated.columns = [strip_val(c) for c in generated.columns]

    row_comp = pd.DataFrame([
        {"metric": "baseline_rows", "value": len(baseline)},
        {"metric": "generated_rows", "value": len(generated)},
        {"metric": "baseline_columns", "value": len(baseline.columns)},
        {"metric": "generated_columns", "value": len(generated.columns)},
        {"metric": "row_count_match", "value": "Y" if len(baseline) == len(generated) else "N"},
        {"metric": "column_count_match", "value": "Y" if list(baseline.columns) == list(generated.columns) else "N"},
        {"metric": "crosswalk_overlay_enabled", "value": "Y" if overlay.enabled else "N"},
    ])
    row_comp.to_csv(os.path.join(args.output_dir, "row_count_comparison.csv"), index=False)

    field_diffs = []
    if list(baseline.columns) != list(generated.columns):
        field_diffs.append({
            "field": "__SCHEMA__",
            "baseline_col_count": len(baseline.columns),
            "generated_col_count": len(generated.columns),
            "difference_type": "COLUMN_ORDER_OR_NAME",
        })
    else:
        min_rows = min(len(baseline), len(generated))
        for col in baseline.columns:
            b_vals = baseline[col].head(min_rows).map(strip_val)
            g_vals = generated[col].head(min_rows).map(strip_val)
            mismatches = (b_vals != g_vals).sum()
            if mismatches:
                first_idx = int((b_vals != g_vals).idxmax()) if mismatches else -1
                field_diffs.append({
                    "field": col,
                    "mismatch_count": int(mismatches),
                    "rows_compared": min_rows,
                    "first_mismatch_row": first_idx,
                    "baseline_sample": strip_val(baseline.loc[first_idx, col]) if first_idx >= 0 else "",
                    "generated_sample": strip_val(generated.loc[first_idx, col]) if first_idx >= 0 else "",
                    "difference_type": "VALUE_MISMATCH",
                })

    field_df = pd.DataFrame(field_diffs)
    field_df.to_csv(os.path.join(args.output_dir, "field_level_differences.csv"), index=False)

    diff_rows = []
    if list(baseline.columns) == list(generated.columns):
        max_rows = max(len(baseline), len(generated))
        for i in range(max_rows):
            if i >= len(baseline) or i >= len(generated):
                diff_rows.append({
                    "row_index": i,
                    "field": "__ROW__",
                    "baseline_value": "MISSING" if i >= len(baseline) else "PRESENT",
                    "generated_value": "MISSING" if i >= len(generated) else "PRESENT",
                })
                continue
            for col in baseline.columns:
                bv = strip_val(baseline.iloc[i][col])
                gv = strip_val(generated.iloc[i][col])
                if bv != gv:
                    diff_rows.append({
                        "row_index": i,
                        "field": col,
                        "baseline_value": bv,
                        "generated_value": gv,
                        "plan_baseline": strip_val(baseline.iloc[i].get("PLAN", "")),
                        "plan_generated": strip_val(generated.iloc[i].get("PLAN", "")),
                    })

    diff_df = pd.DataFrame(diff_rows)
    diff_df.to_csv(os.path.join(args.output_dir, "quikplan_diff_report.csv"), index=False)

    identical = (
        len(baseline) == len(generated)
        and list(baseline.columns) == list(generated.columns)
        and diff_df.empty
    )

    summary_lines = [
        "# Phase P2A — QuikPlan Parallel Validation Summary",
        "",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Crosswalk overlay:** {'ENABLED' if overlay.enabled else 'DISABLED (default)'}",
        "",
        "## Result",
        "",
        f"**{'IDENTICAL' if identical else 'DIFFERENCES DETECTED'}**",
        "",
        "## Counts",
        "",
        f"- Baseline rows: {len(baseline)}",
        f"- Generated rows: {len(generated)}",
        f"- Baseline columns: {len(baseline.columns)}",
        f"- Generated columns: {len(generated.columns)}",
        f"- Field-level mismatches: {len(field_df)}",
        f"- Cell-level differences: {len(diff_df)}",
        "",
        "## Inputs",
        "",
        f"- Source: `{source_path}`",
        f"- Rulebook: `{rulebook_path}`",
        f"- Translation: `{trans_path}`",
        f"- Crosswalk map: `{cw_path}`",
        f"- PCOMP lookup dir: `{pcomp_dir}`",
        f"- Baseline: `{baseline_path}`",
        "",
        "## Artifacts",
        "",
        "- `quikplan_generated_p2a.csv`",
        "- `row_count_comparison.csv`",
        "- `field_level_differences.csv`",
        "- `quikplan_diff_report.csv`",
        "",
    ]
    if not identical and not field_df.empty:
        summary_lines.extend(["## Top Field Mismatches", ""])
        for _, r in field_df.head(10).iterrows():
            summary_lines.append(f"- **{r['field']}**: {r['mismatch_count']} mismatches")

    summary_path = os.path.join(args.output_dir, "validation_summary.md")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(summary_lines) + "\n")

    print(f"Validation: {'IDENTICAL' if identical else 'DIFFERENCES'}")
    print(f"  baseline={len(baseline)} generated={len(generated)} diffs={len(diff_df)}")
    print(f"  summary: {summary_path}")
    return 0 if identical else 1


if __name__ == "__main__":
    raise SystemExit(main())
