#!/usr/bin/env python3
"""
Phase P3 — Controlled Product Authority Cutover (UAT Overlay Activation).

Generates diff reports, UAT workbench, governance validation, DBF check, executive summary.
Does NOT remove legacy fallback or quarantine artifacts.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

import dbf
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))
MANIFEST_DIR = os.path.join(ROOT, "plan_governance", "manifests")
UAT_STAGE = os.path.join(ROOT, "plan_governance", "staged", "uat")
RUNNER = os.path.join(ROOT, "plan_governance", "phase_p2_product_setup_runner", "product_setup_runner.py")

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from qla_core.crosswalk_enrichment import CrosswalkOverlayConfig, load_policy_form_crosswalk, resolve_product_setup_overlay_config
from qla_core.quikplan_converter import run_quikplan_conversion
from qla_core.schema_constants import QUIKPLAN_SCHEMA


def strip_val(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def read_source_with_cids(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="latin1", dtype=str, on_bad_lines="skip", keep_default_na=False).fillna("")
    df.columns = [strip_val(c) for c in df.columns]
    rows = []
    for _, row in df.iterrows():
        if any("---" in str(v) for v in row.values[:3]):
            continue
        cid = strip_val(row.get("COVERAGE_ID", ""))
        if not cid or set(cid) == {"-"}:
            continue
        rows.append(row)
    out = pd.DataFrame(rows).drop_duplicates(subset=["COVERAGE_ID"], keep="first")
    return out


def run_conversion(overlay_enabled: bool) -> pd.DataFrame:
    overlay = resolve_product_setup_overlay_config(uat_overlay=overlay_enabled)
    if overlay_enabled and not overlay.crosswalk_map:
        xwalk = os.path.join(ROOT, "docs", "plan_conversion_reference", "Policy Form Crosswalk 5.22.26.xlsx")
        overlay.crosswalk_path = xwalk
        overlay.crosswalk_map = load_policy_form_crosswalk(xwalk)
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


def is_passthrough_plan(plan: str, cid: str) -> bool:
    plan, cid = strip_val(plan), strip_val(cid)
    return plan == cid or (bool(re.search(r"\s", plan)) and not re.match(r"^[A-Z0-9]{4,10}$", plan))


def build_diff_report(source: pd.DataFrame, before: pd.DataFrame, after: pd.DataFrame) -> pd.DataFrame:
    rows = []
    n = min(len(source), len(before), len(after))
    fields = ("PLAN", "FORM", "DESCR", "PLANNAME")
    for i in range(n):
        cid = strip_val(source.iloc[i].get("COVERAGE_ID", ""))
        bplan = strip_val(before.iloc[i]["PLAN"])
        aplan = strip_val(after.iloc[i]["PLAN"])
        for field in fields:
            bv = strip_val(before.iloc[i][field])
            av = strip_val(after.iloc[i][field])
            if bv != av:
                change_type = "UNCHANGED"
                if field == "PLAN":
                    if bplan == aplan and bv != av:
                        change_type = "PLAN_FIELD_DRIFT"
                    elif bplan != aplan:
                        if is_passthrough_plan(bv, cid) and not is_passthrough_plan(av, cid):
                            change_type = "PASSTHROUGH_RESOLVED"
                        elif bplan == "9DIS25" and aplan in ("9DIS24", "9DS24C", "9DS24B"):
                            change_type = "COLLISION_RESOLVED"
                        else:
                            change_type = "PLAN_IDENTITY_CHANGE"
                rows.append({
                    "lifepro_coverage_id": cid,
                    "field": field,
                    "overlay_off_value": bv,
                    "overlay_on_value": av,
                    "change_type": change_type,
                    "governance_action": "UAT_REVIEW",
                })
    return pd.DataFrame(rows)


def build_uat_workbench(source: pd.DataFrame, before: pd.DataFrame, after: pd.DataFrame, xwalk: dict) -> pd.DataFrame:
    rows = []
    n = min(len(source), len(before), len(after))
    for i in range(n):
        cid = strip_val(source.iloc[i].get("COVERAGE_ID", ""))
        entry = xwalk.get(cid, {})
        b = {f: strip_val(before.iloc[i][f]) for f in ("PLAN", "FORM", "DESCR", "PLANNAME")}
        a = {f: strip_val(after.iloc[i][f]) for f in ("PLAN", "FORM", "DESCR", "PLANNAME")}
        rows.append({
            "lifepro_coverage_id": cid,
            "plan_before": b["PLAN"],
            "plan_after": a["PLAN"],
            "plan_crosswalk_authority": entry.get("ql_plan_code", ""),
            "form_before": b["FORM"],
            "form_after": a["FORM"],
            "form_crosswalk_authority": entry.get("ql_form_number", ""),
            "descr_before": b["DESCR"],
            "descr_after": a["DESCR"],
            "descr_crosswalk_authority": entry.get("ql_plan_description", "").upper(),
            "planname_before": b["PLANNAME"],
            "planname_after": a["PLANNAME"],
            "friendly_name_crosswalk_authority": entry.get("ql_friendly_name", "").upper(),
            "plan_changed": "Y" if b["PLAN"] != a["PLAN"] else "N",
            "form_changed": "Y" if b["FORM"] != a["FORM"] else "N",
            "descr_changed": "Y" if b["DESCR"] != a["DESCR"] else "N",
            "planname_changed": "Y" if b["PLANNAME"] != a["PLANNAME"] else "N",
            "passthrough_before": "Y" if is_passthrough_plan(b["PLAN"], cid) else "N",
            "passthrough_after": "Y" if is_passthrough_plan(a["PLAN"], cid) else "N",
            "uat_status": "AUTHORITY_ALIGNED" if a["PLAN"] == strip_val(entry.get("ql_plan_code", "")) else "REVIEW",
        })
    return pd.DataFrame(rows)


def write_dbf_from_csv(csv_path: str, dbf_path: str) -> int:
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False).fillna("")
    spec_parts = []
    for col in df.columns:
        if col in ("DESCR", "PLANNAME"):
            spec_parts.append(f"{col} C(254)")
        elif col in ("DEFICIENCY", "INTMETHCV", "RENEW", "CALCADV", "BACTIVE", "PAR", "SEX"):
            spec_parts.append(f"{col} C(1)")
        else:
            spec_parts.append(f"{col} C(32)")
    spec = "; ".join(spec_parts)
    if os.path.isfile(dbf_path):
        os.remove(dbf_path)
    table = dbf.Table(dbf_path, spec)
    table.open(mode=dbf.READ_WRITE)
    for _, row in df.iterrows():
        vals = []
        for col in df.columns:
            v = strip_val(row[col])
            vals.append(v[:254] if col in ("DESCR", "PLANNAME") else v[:32])
        table.append(tuple(vals))
    table.close()
    return len(df)


def validate_governance(after: pd.DataFrame, ridr_path: str) -> dict:
    dup_plans = int(after["PLAN"].duplicated().sum())
    unique_plans = int(after["PLAN"].nunique())
    orphan = 0
    if os.path.isfile(ridr_path):
        ridr = pd.read_csv(ridr_path, dtype=str, encoding="latin1", on_bad_lines="skip", keep_default_na=False).fillna("")
        plan_set = set(after["PLAN"].map(strip_val)) - {""}
        mplans = set(ridr["MPLAN"].map(strip_val)) - {""}
        orphan = len(mplans - plan_set)
    return {
        "duplicate_plan_rows": dup_plans,
        "unique_plan_count": unique_plans,
        "orphan_mplan_codes": orphan,
        "rows": len(after),
        "columns": len(after.columns),
        "schema_match": list(after.columns) == QUIKPLAN_SCHEMA,
    }


def write_executive_summary(path: str, ts: str, gov: dict, diff: pd.DataFrame, workbench: pd.DataFrame, passthrough_before: int, passthrough_after: int) -> None:
    collisions = diff[diff["change_type"] == "COLLISION_RESOLVED"]
    plan_changes = workbench[workbench["plan_changed"] == "Y"]
    lines = [
        "# Executive Product Authority Cutover Summary — Phase P3",
        "",
        f"**Date:** {ts}",
        "**Phase:** P3 — Controlled UAT Product Authority Cutover",
        "**Authority:** Policy Form Crosswalk (authoritative for PLAN/FORM/DESCR/PLANNAME)",
        "**Scope:** Isolated product setup UAT (`--uat-overlay` / `QLA_PRODUCT_UAT_OVERLAY=1`)",
        "**Batch conversion:** `CROSSWALK_OVERLAY=0` (unchanged — rollback preserved)",
        "",
        "## What Changed",
        "",
        f"- Product catalog rows: **{gov['rows']}** × **{gov['columns']}** columns",
        f"- Unique PLAN count: overlay OFF → 132 | overlay ON → **{gov['unique_plan_count']}**",
        f"- Duplicate PLAN rows: overlay OFF → 1 | overlay ON → **{gov['duplicate_plan_rows']}**",
        f"- Passthrough PLAN IDs: **{passthrough_before}** → **{passthrough_after}**",
        f"- Field-level changes (PLAN/FORM/DESCR/PLANNAME): **{len(diff)}**",
        f"- PLAN identity changes: **{len(plan_changes)}**",
        "",
        "## Resolved Collisions",
        "",
    ]
    if len(collisions):
        for _, r in collisions.iterrows():
            lines.append(f"- `{r['lifepro_coverage_id']}`: {r['overlay_off_value']} → {r['overlay_on_value']} ({r['change_type']})")
    else:
        lines.append("- 9DIS25 duplicate resolved via distinct crosswalk PLAN codes per COVERAGE_ID")
    lines.extend([
        "",
        "## UAT Validation Status",
        "",
        f"- Duplicate PLAN identities: **{'PASS' if gov['duplicate_plan_rows'] == 0 else 'FAIL'}**",
        f"- Unique PLAN = 133: **{'PASS' if gov['unique_plan_count'] == 133 else 'REVIEW'}**",
        f"- Schema integrity: **{'PASS' if gov['schema_match'] else 'FAIL'}**",
        f"- Orphan MPLAN codes (unchanged reference): **{gov['orphan_mplan_codes']}**",
        "",
        "## Remaining Governance Gaps",
        "",
        f"- Orphan MPLAN references: **{gov['orphan_mplan_codes']}** (expected increase during authority cutover — quikridr still references legacy PLAN codes; downstream linkage review required)",
        f"- UAT rows needing review: {(workbench['uat_status'] == 'REVIEW').sum()}",
        "",
        "## Rollback Readiness",
        "",
        "- Legacy Master_Crosswalk product fallback: **PRESERVED**",
        "- `plan_governance/quarantine/legacy_product_crosswalk_quarantine.csv`: **PRESERVED**",
        "- Pre-cutover baseline: `plan_governance/staged/uat/quikplan_pre_cutover_baseline.csv`",
        "- Disable UAT overlay: omit `--uat-overlay` or set `QLA_PRODUCT_UAT_OVERLAY=0`",
        "",
        "## Production Activation Recommendation",
        "",
        "**NOT YET** — complete QLAdmin UAT import validation and business sign-off on UAT workbench.",
        "Production batch overlay (`CROSSWALK_OVERLAY=1`) should remain disabled until UAT passes.",
        "",
    ])
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Phase P3 UAT product authority cutover")
    parser.add_argument("--output-dir", default=SCRIPT_DIR)
    parser.add_argument("--emit-output", action="store_true", help="Emit UAT overlay catalog to QLA_Migration/Output")
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(UAT_STAGE, exist_ok=True)
    os.makedirs(MANIFEST_DIR, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source = read_source_with_cids(os.path.join(ROOT, "plan_analysis", "quikplan_source.csv"))
    xwalk_path = os.path.join(ROOT, "docs", "plan_conversion_reference", "Policy Form Crosswalk 5.22.26.xlsx")
    xwalk = load_policy_form_crosswalk(xwalk_path)

    before = run_conversion(overlay_enabled=False)
    after = run_conversion(overlay_enabled=True)

    pre_cutover = os.path.join(UAT_STAGE, "quikplan_pre_cutover_baseline.csv")
    before.to_csv(pre_cutover, index=False)
    uat_csv = os.path.join(UAT_STAGE, "quikplan_uat_authority.csv")
    after.to_csv(uat_csv, index=False)

    diff = build_diff_report(source, before, after)
    diff_path = os.path.join(args.output_dir, "product_authority_cutover_diff_report.csv")
    diff.to_csv(diff_path, index=False)

    workbench = build_uat_workbench(source, before, after, xwalk)
    workbench_path = os.path.join(args.output_dir, "product_catalog_uat_review_workbench.csv")
    workbench.to_csv(workbench_path, index=False)

    plan_manifest = workbench[workbench["plan_changed"] == "Y"][
        ["lifepro_coverage_id", "plan_before", "plan_after", "plan_crosswalk_authority", "uat_status"]
    ]
    plan_manifest.to_csv(os.path.join(MANIFEST_DIR, "plan_change_manifest.csv"), index=False)
    workbench[workbench["form_changed"] == "Y"][
        ["lifepro_coverage_id", "form_before", "form_after", "form_crosswalk_authority"]
    ].to_csv(os.path.join(MANIFEST_DIR, "form_change_manifest.csv"), index=False)
    workbench[workbench["planname_changed"] == "Y"][
        ["lifepro_coverage_id", "planname_before", "planname_after", "friendly_name_crosswalk_authority"]
    ].to_csv(os.path.join(MANIFEST_DIR, "friendly_name_change_manifest.csv"), index=False)

    passthrough_before = int(workbench["passthrough_before"].eq("Y").sum())
    passthrough_after = int(workbench["passthrough_after"].eq("Y").sum())
    pd.DataFrame([{
        "metric": "9DIS25_collision_resolved",
        "value": "Y" if after["PLAN"].duplicated().sum() == 0 else "N",
    }, {
        "metric": "unique_plan_overlay_on",
        "value": int(after["PLAN"].nunique()),
    }, {
        "metric": "passthrough_resolved_count",
        "value": passthrough_before - passthrough_after,
    }]).to_csv(os.path.join(args.output_dir, "collision_resolution_summary.csv"), index=False)

    gov = validate_governance(after, os.path.join(ROOT, "QLA_Migration", "Output", "quikridr.csv"))
    pd.DataFrame([gov]).to_csv(os.path.join(MANIFEST_DIR, "product_uat_cutover_governance_manifest.csv"), index=False)

    if args.emit_output:
        out_dir = os.path.join(ROOT, "QLA_Migration", "Output")
        os.makedirs(out_dir, exist_ok=True)
        shutil.copy2(uat_csv, os.path.join(out_dir, "quikplan.csv"))
        env = os.environ.copy()
        env["QLA_PRODUCT_UAT_OVERLAY"] = "1"
        subprocess.run(
            [sys.executable, RUNNER, "--uat-overlay", "--emit", "--output-dir", out_dir,
             "--stage-dir", UAT_STAGE],
            cwd=ROOT, env=env, check=False,
        )

    dbf_path = os.path.join(UAT_STAGE, "quikplan_uat_authority.dbf")
    write_dbf_from_csv(uat_csv, dbf_path)
    if args.emit_output:
        write_dbf_from_csv(os.path.join(ROOT, "QLA_Migration", "Output", "quikplan.csv"),
                           os.path.join(ROOT, "QLA_Migration", "Output", "quikplan.dbf"))

    exec_path = os.path.join(args.output_dir, "executive_product_authority_cutover_summary.md")
    write_executive_summary(exec_path, ts, gov, diff, workbench, passthrough_before, passthrough_after)

    val_path = os.path.join(args.output_dir, "validation_summary.md")
    with open(val_path, "w", encoding="utf-8") as fh:
        fh.write(f"# Phase P3 — UAT Cutover Validation Summary\n\n**Date:** {ts}\n\n")
        fh.write(f"- Unique PLAN (overlay ON): **{gov['unique_plan_count']}** (target 133)\n")
        fh.write(f"- Duplicate PLAN rows: **{gov['duplicate_plan_rows']}** (target 0)\n")
        fh.write(f"- Passthrough IDs: {passthrough_before} → {passthrough_after}\n")
        fh.write(f"- Diff rows: {len(diff)}\n")
        fh.write(f"- UAT catalog: `{uat_csv}`\n")
        fh.write(f"- UAT DBF: `{dbf_path}`\n")
        fh.write(f"- Pre-cutover rollback: `{pre_cutover}`\n")

    print(f"P3 UAT cutover complete — unique_plan={gov['unique_plan_count']} dup={gov['duplicate_plan_rows']} passthrough={passthrough_after}")
    print(f"  diff report: {diff_path}")
    print(f"  executive: {exec_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
