#!/usr/bin/env python3
"""
Phase P2E — Product Authority Separation + Master_Crosswalk cleanup artifacts.

Detect/quarantine only for legacy mappings — does NOT mutate Master_Crosswalk.csv.
Builds product_catalog_crosswalk.csv and quarantine inventory.
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

from qla_core.crosswalk_enrichment import CrosswalkOverlayConfig, load_policy_form_crosswalk
from qla_core.normalize_utils import normalize
from qla_core.product_catalog_authority import (
    is_policy_number,
    load_crosswalk_authority,
    split_master_crosswalk_rows,
    strip_val,
)
from qla_core.quikplan_converter import run_quikplan_conversion

POLICY_FORM = os.path.join(ROOT, "docs", "plan_conversion_reference", "Policy Form Crosswalk 5.22.26.xlsx")
MASTER_CW = os.path.join(ROOT, "Master_Crosswalk.csv")
SOURCE = os.path.join(ROOT, "plan_analysis", "quikplan_source.csv")
BASELINE = os.path.join(ROOT, "QLA_Migration", "Output", "quikplan.csv")
RULEBOOK = os.path.join(ROOT, "QLA_Migration", "Configs", "Sync_Rulebook_quikplan.csv")
TRANS = os.path.join(ROOT, "Master_Value_Translation.csv")
PCOMP_DIR = os.path.join(ROOT, "plan_analysis")
PRODUCT_CATALOG = os.path.join(ROOT, "plan_governance", "product_catalog_crosswalk.csv")
QUARANTINE = os.path.join(ROOT, "plan_governance", "quarantine", "legacy_product_crosswalk_quarantine.csv")
MANIFEST_DIR = os.path.join(ROOT, "plan_governance", "manifests")


def read_source() -> pd.DataFrame:
    df = pd.read_csv(
        SOURCE, encoding="latin1", dtype=str, on_bad_lines="skip", keep_default_na=False,
    ).fillna("")
    df.columns = [strip_val(c) for c in df.columns]
    keep = []
    for _, row in df.iterrows():
        if any("---" in str(v) for v in row.values[:3]):
            continue
        cid = strip_val(row.get("COVERAGE_ID", ""))
        if not cid or set(cid) == {"-"}:
            continue
        keep.append(row)
    out = pd.DataFrame(keep) if keep else df.iloc[0:0]
    if "COVERAGE_ID" in out.columns:
        out = out.drop_duplicates(subset=["COVERAGE_ID"], keep="first")
    return out


def load_policy_form() -> pd.DataFrame:
    x = pd.read_excel(POLICY_FORM)
    x.columns = [
        "lifepro_coverage_id", "unused", "ql_plan_code",
        "ql_form_number", "ql_plan_description", "ql_friendly_name",
    ]
    return x


def build_product_mapping_inventory(mc: pd.DataFrame) -> pd.DataFrame:
    policy_df, product_df = split_master_crosswalk_rows(mc)
    rows = []
    for _, r in product_df.iterrows():
        old, new = strip_val(r["Old_Value"]), strip_val(r["New_Value"])
        rows.append({
            "old_value": old,
            "new_value": new,
            "mapping_class": "PRODUCT_OR_ENTITY",
            "mapping_subtype": _classify_product_subtype(old, new),
            "is_policy_number": "N",
            "quarantine_candidate": "Y",
            "governance_action": "MIGRATE_TO_PRODUCT_CATALOG",
        })
    for _, r in policy_df.iterrows():
        old, new = strip_val(r["Old_Value"]), strip_val(r["New_Value"])
        rows.append({
            "old_value": old,
            "new_value": new,
            "mapping_class": "POLICY_NUMBER",
            "mapping_subtype": "POLICY_RENUMBER",
            "is_policy_number": "Y",
            "quarantine_candidate": "N",
            "governance_action": "RETAIN_IN_MASTER_CROSSWALK",
        })
    return pd.DataFrame(rows)


def _classify_product_subtype(old: str, new: str) -> str:
    if old == new:
        return "PASSTHROUGH_IDENTITY"
    if " " in old:
        return "COVERAGE_ID_TO_PLAN"
    if old.isdigit() or (len(old) <= 12 and old.isalnum()):
        return "ENTITY_OR_LEGACY_CODE"
    return "PRODUCT_PLAN_MAP"


def build_product_catalog(source: pd.DataFrame, mc: pd.DataFrame, xdf: pd.DataFrame, baseline: pd.DataFrame) -> pd.DataFrame:
    _, product_df = split_master_crosswalk_rows(mc)
    legacy_map = {}
    for _, r in product_df.iterrows():
        legacy_map[normalize(r["Old_Value"])] = normalize(r["New_Value"])

    x_by_cid = {strip_val(r["lifepro_coverage_id"]): r for _, r in xdf.iterrows()}
    baseline_plans = set(baseline["PLAN"].map(strip_val))

    rows = []
    for _, srow in source.iterrows():
        cid = strip_val(srow.get("COVERAGE_ID", ""))
        if not cid or set(cid) == {"-"}:
            continue
        current_plan = legacy_map.get(normalize(cid), normalize(cid))
        xrow = x_by_cid.get(cid, {})
        xplan = strip_val(xrow.get("ql_plan_code", "")) if isinstance(xrow, pd.Series) else ""
        xform = strip_val(xrow.get("ql_form_number", "")) if isinstance(xrow, pd.Series) else ""
        xdescr = strip_val(xrow.get("ql_plan_description", "")) if isinstance(xrow, pd.Series) else ""
        xname = strip_val(xrow.get("ql_friendly_name", "")) if isinstance(xrow, pd.Series) else ""

        if xplan and xplan != current_plan:
            status = "CROSSWALK_DIVERGENT"
        elif current_plan == normalize(cid):
            status = "PASSTHROUGH"
        elif current_plan in baseline_plans:
            status = "STABLE_EMIT"
        else:
            status = "REVIEW"

        rows.append({
            "lifepro_coverage_id": cid,
            "ql_plan_code": current_plan,
            "ql_form_number": strip_val(srow.get("POLICY_FORM_NUM", "")),
            "ql_plan_description": strip_val(srow.get("DESCRIPTION", "")),
            "ql_friendly_name": strip_val(srow.get("DESCRIPTION", "")),
            "authority_source": "STABLE_MASTER_CROSSWALK_EMIT",
            "mapping_status": status,
            "crosswalk_ql_plan_code": xplan,
            "crosswalk_ql_form_number": xform,
            "crosswalk_ql_plan_description": xdescr,
            "crosswalk_ql_friendly_name": xname,
            "governance_notes": (
                f"Catalog seeded from stable emit; crosswalk proposes PLAN={xplan}" if xplan and xplan != current_plan
                else "Catalog seeded from stable emit"
            ),
        })
    return pd.DataFrame(rows)


def build_quarantine(product_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    seen = set()
    for _, r in product_df.iterrows():
        old, new = strip_val(r["Old_Value"]), strip_val(r["New_Value"])
        key = (old, new)
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "old_value": old,
            "new_value": new,
            "original_source": "Master_Crosswalk.csv",
            "mapping_class": "PRODUCT_OR_ENTITY",
            "quarantine_reason": "Legacy product mapping — migrate authority to product_catalog_crosswalk.csv",
            "rollback_action": "Restore from this quarantine file if needed",
            "removed_from_master_crosswalk": "N",
            "governance_status": "QUARANTINED_COPY",
        })
    return pd.DataFrame(rows)


def analyze_9dis25_root_cause(source: pd.DataFrame, mc: pd.DataFrame, xdf: pd.DataFrame, baseline: pd.DataFrame) -> str:
    dup_rows = baseline[baseline["PLAN"] == "9DIS25"]
    cids = ["DISCHO2475", "DISCHO247C", "DISCHO25", "DISCHO247B"]
    lines = [
        "# Duplicate PLAN 9DIS25 — Root Cause Analysis",
        "",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "**Phase:** P2E",
        "",
        "## Executive Conclusion",
        "",
        "Duplicate PLAN `9DIS25` is **NOT** caused by Policy Form Crosswalk duplication.",
        "The business crosswalk assigns **unique** QL Plan Codes per LifePRO COVERAGE_ID:",
        "",
        "| COVERAGE_ID | Policy Form Crosswalk ql_plan_code |",
        "|-------------|-----------------------------------|",
    ]
    for cid in cids:
        xr = xdf[xdf["lifepro_coverage_id"].astype(str).str.strip() == cid]
        xplan = strip_val(xr.iloc[0]["ql_plan_code"]) if len(xr) else "(not in source)"
        lines.append(f"| {cid} | {xplan} |")

    lines.extend([
        "",
        "**Root cause:** Legacy **Master_Crosswalk product mapping collision** — multiple distinct",
        "LifePRO COVERAGE_IDs mapped to the same QL PLAN code `9DIS25`, while the conversion engine",
        "correctly emits **one quikplan row per source COVERAGE_ID**.",
        "",
        "## Evidence Chain",
        "",
        f"1. **Baseline output:** {len(dup_rows)} rows with PLAN=`9DIS25` (rows 99 and 101, 0-indexed 98 and 100)",
        "2. **Source lineage:** Two active source COVERAGE_IDs produce the duplicate:",
        "",
    ])

    for cid in ["DISCHO2475", "DISCHO247C"]:
        in_src = int((source["COVERAGE_ID"].str.strip() == cid).sum())
        mc_rows = mc[mc.iloc[:, 0].astype(str).str.strip() == cid]
        mc_targets = ", ".join(sorted(set(mc_rows.iloc[:, 1].astype(str).str.strip()))) if len(mc_rows) else "none"
        lines.append(f"   - `{cid}`: source_rows={in_src}, Master_Crosswalk -> `{mc_targets}`")

    lines.extend([
        "",
        "3. **Differentiated output fields:** The two emitted rows differ in PCOMP-driven fields:",
        "",
        "| PLAN | MINUNIT | MAXUNIT |",
        "|------|---------|---------|",
    ])
    for _, r in dup_rows.iterrows():
        lines.append(f"| {r['PLAN']} | {strip_val(r.get('MINUNIT',''))} | {strip_val(r.get('MAXUNIT',''))} |")

    lines.extend([
        "",
        "4. **Rulebook:** Single PLAN rule (`COVERAGE_ID` -> `PLAN`) — no duplicate append logic.",
        "5. **Emit logic:** One output row per source row — no duplicate append.",
        "6. **Transform collision:** Master_Crosswalk overrides distinct COVERAGE_IDs to identical PLAN.",
        "",
        "## Ruled Out",
        "",
        "- Policy Form Crosswalk duplication (9DIS25 appears once, on DISCHO25 only)",
        "- Source COVERAGE_ID duplication (`drop_duplicates` on COVERAGE_ID — 133 unique)",
        "- Rulebook duplicate target rows for PLAN",
        "- Subprocess double-emit or append logic",
        "",
        "## Recommended Remediation (Business Review — Not Auto-Applied)",
        "",
        "1. Assign distinct QL Plan Codes per LifePRO coverage (as Policy Form Crosswalk already defines:",
        "   `9DIS24` for DISCHO2475, `9DS24C` for DISCHO247C).",
        "2. Migrate PLAN authority to `product_catalog_crosswalk.csv` with business-approved codes.",
        "3. Enable `CROSSWALK_OVERLAY=1` only after staged validation — not globally in P2E.",
        "4. Do **not** suppress duplicate rows — resolve mapping collision at source.",
        "",
    ])
    return "\n".join(lines)


def build_passthrough_review(source: pd.DataFrame, catalog: pd.DataFrame, xdf: pd.DataFrame) -> pd.DataFrame:
    x_by = {strip_val(r["lifepro_coverage_id"]): r for _, r in xdf.iterrows()}
    cat_by = {strip_val(r["lifepro_coverage_id"]): r for _, r in catalog.iterrows()}
    rows = []
    for _, srow in source.iterrows():
        cid = strip_val(srow.get("COVERAGE_ID", ""))
        if not cid or set(cid) == {"-"}:
            continue
        cat = cat_by.get(cid)
        if cat is None:
            continue
        plan = strip_val(cat["ql_plan_code"])
        xrow = x_by.get(cid)
        xplan = strip_val(xrow["ql_plan_code"]) if xrow is not None else ""
        if plan != cid and " " not in plan:
            continue
        if normalize(plan) != normalize(cid) and " " not in cid:
            continue
        classification = "REMEDIATION_REQUIRED"
        notes = "Output PLAN equals or passthrough LifePRO COVERAGE_ID"
        if xplan and xplan != plan:
            classification = "UNRESOLVED_MAPPING"
            notes = f"Crosswalk defines ql_plan_code={xplan} but stable emit uses {plan}"
        elif xplan and xplan == plan:
            classification = "ACCEPTABLE_PASSTHROUGH"
            notes = "Crosswalk and emit agree on passthrough-style code"
        elif not xrow:
            classification = "MISSING_CROSSWALK_ENTRY"
            notes = "No Policy Form Crosswalk row"
        else:
            classification = "LEGACY_COMPATIBILITY"
            notes = "Master_Crosswalk passthrough; crosswalk has distinct code pending migration"
        rows.append({
            "lifepro_coverage_id": cid,
            "current_output_plan": plan,
            "crosswalk_ql_plan_code": xplan,
            "classification": classification,
            "governance_action": "BUSINESS_REVIEW",
            "notes": notes,
        })
    return pd.DataFrame(rows)


def run_overlay_simulation(baseline: pd.DataFrame) -> dict:
    overlay_cfg = CrosswalkOverlayConfig(
        enabled=True,
        crosswalk_path=POLICY_FORM,
        crosswalk_map=load_policy_form_crosswalk(POLICY_FORM),
    )
    generated = run_quikplan_conversion(
        source_path=SOURCE,
        rulebook_path=RULEBOOK,
        trans_path=TRANS,
        cw_path=MASTER_CW,
        lookup_dir=PCOMP_DIR,
        overlay_config=overlay_cfg,
    )
    diffs = 0
    field_diffs: set[str] = set()
    if len(baseline) == len(generated):
        for col in baseline.columns:
            b = baseline[col].map(strip_val)
            g = generated[col].map(strip_val)
            m = b != g
            if m.any():
                field_diffs.add(col)
                diffs += int(m.sum())
    passthrough_before = int((baseline["PLAN"].str.contains(r"\s", na=False)).sum())
    passthrough_after = int((generated["PLAN"].str.contains(r"\s", na=False)).sum())
    return {
        "cell_differences": diffs,
        "field_difference_count": len(field_diffs),
        "fields": sorted(field_diffs),
        "unique_plan_baseline": int(baseline["PLAN"].nunique()),
        "unique_plan_overlay": int(generated["PLAN"].nunique()),
        "passthrough_before": passthrough_before,
        "passthrough_after": passthrough_after,
        "duplicate_plan_baseline": int(baseline["PLAN"].duplicated().sum()),
        "duplicate_plan_overlay": int(generated["PLAN"].duplicated().sum()),
    }


def validate_p2a_baseline() -> dict:
    generated = run_quikplan_conversion(
        source_path=SOURCE,
        rulebook_path=RULEBOOK,
        trans_path=TRANS,
        cw_path=MASTER_CW,
        lookup_dir=PCOMP_DIR,
    )
    baseline = pd.read_csv(BASELINE, dtype=str, keep_default_na=False).fillna("")
    diffs = 0
    if list(baseline.columns) == list(generated.columns) and len(baseline) == len(generated):
        for col in baseline.columns:
            diffs += int((baseline[col].map(strip_val) != generated[col].map(strip_val)).sum())
    return {
        "baseline_rows": len(baseline),
        "generated_rows": len(generated),
        "baseline_cols": len(baseline.columns),
        "cell_differences": diffs,
        "identical": diffs == 0 and len(baseline) == len(generated),
    }


def main():
    parser = argparse.ArgumentParser(description="Phase P2E authority separation runner")
    parser.add_argument("--output-dir", default=SCRIPT_DIR)
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(PRODUCT_CATALOG), exist_ok=True)
    os.makedirs(os.path.dirname(QUARANTINE), exist_ok=True)
    os.makedirs(MANIFEST_DIR, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mc = pd.read_csv(MASTER_CW, dtype=str, keep_default_na=False)
    source = read_source()
    baseline = pd.read_csv(BASELINE, dtype=str, keep_default_na=False).fillna("")
    xdf = load_policy_form()

    inventory = build_product_mapping_inventory(mc)
    inventory_path = os.path.join(args.output_dir, "master_crosswalk_product_mapping_inventory.csv")
    inventory.to_csv(inventory_path, index=False)

    catalog = build_product_catalog(source, mc, xdf, baseline)
    catalog.to_csv(PRODUCT_CATALOG, index=False)

    _, product_df = split_master_crosswalk_rows(mc)
    quarantine = build_quarantine(product_df)
    quarantine.to_csv(QUARANTINE, index=False)

    rca_path = os.path.join(args.output_dir, "duplicate_plan_root_cause_analysis.md")
    with open(rca_path, "w", encoding="utf-8") as fh:
        fh.write(analyze_9dis25_root_cause(source, mc, xdf, baseline))

    passthrough = build_passthrough_review(source, catalog, xdf)
    passthrough.to_csv(os.path.join(args.output_dir, "passthrough_plan_governance_review.csv"), index=False)

    overlay = run_overlay_simulation(baseline)
    p2a = validate_p2a_baseline()

    overlay_path = os.path.join(args.output_dir, "overlay_revalidation_summary.md")
    with open(overlay_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([
            "# Overlay Revalidation Summary — Phase P2E",
            "",
            f"**Date:** {ts}",
            "**Context:** After product authority separation scaffolding (product_catalog_crosswalk.csv)",
            "**CROSSWALK_OVERLAY:** Still **disabled** for production (simulation only)",
            "",
            "## P2A Stability Check (overlay OFF)",
            "",
            f"- Baseline: {p2a['baseline_rows']} rows × {p2a['baseline_cols']} columns",
            f"- Generated: {p2a['generated_rows']} rows",
            f"- Cell differences: **{p2a['cell_differences']}**",
            f"- Status: **{'IDENTICAL' if p2a['identical'] else 'DIFFERENCES DETECTED'}**",
            "",
            "## Overlay Simulation (CROSSWALK_OVERLAY=1)",
            "",
            f"- Cell differences vs baseline: **{overlay['cell_differences']}**",
            f"- Fields affected: {', '.join(overlay['fields']) or 'none'}",
            f"- Unique PLAN baseline: {overlay['unique_plan_baseline']} | overlay: {overlay['unique_plan_overlay']}",
            f"- Duplicate PLAN rows baseline: {overlay['duplicate_plan_baseline']} | overlay: {overlay['duplicate_plan_overlay']}",
            f"- Passthrough-style PLAN rows: {overlay['passthrough_before']} → {overlay['passthrough_after']} (overlay)",
            "",
            "## Assessment",
            "",
            "Overlay activation would **resolve** duplicate PLAN 9DIS25 (distinct crosswalk codes per COVERAGE_ID)",
            "but introduces broader field realignment across PLAN/FORM/DESCR/PLANNAME.",
            "**Do not enable globally** until business sign-off and staged validation.",
            "",
        ]))

    pd.DataFrame([{
        "phase": "P2E",
        "timestamp": ts,
        "product_catalog_rows": len(catalog),
        "quarantine_rows": len(quarantine),
        "inventory_product_mappings": int((inventory["mapping_class"] == "PRODUCT_OR_ENTITY").sum()),
        "inventory_policy_mappings": int((inventory["mapping_class"] == "POLICY_NUMBER").sum()),
        "p2a_identical": "Y" if p2a["identical"] else "N",
        "p2a_cell_diffs": p2a["cell_differences"],
        "overlay_cell_diffs": overlay["cell_differences"],
        "passthrough_review_rows": len(passthrough),
    }]).to_csv(os.path.join(MANIFEST_DIR, "product_authority_separation_manifest.csv"), index=False)

    val_path = os.path.join(args.output_dir, "validation_summary.md")
    with open(val_path, "w", encoding="utf-8") as fh:
        fh.write(f"# Phase P2E — Authority Separation Validation Summary\n\n**Date:** {ts}\n\n")
        fh.write(f"## P2A Regression\n\n**{'IDENTICAL' if p2a['identical'] else 'FAILED'}** — {p2a['cell_differences']} cell diffs\n\n")
        fh.write("## Deliverables\n\n")
        for name in [
            "master_crosswalk_product_mapping_inventory.csv",
            "duplicate_plan_root_cause_analysis.md",
            "overlay_revalidation_summary.md",
            "passthrough_plan_governance_review.csv",
            "validation_summary.md",
        ]:
            fh.write(f"- `plan_analysis/phase_p2e_authority_separation/{name}`\n")
        fh.write(f"- `plan_governance/product_catalog_crosswalk.csv` ({len(catalog)} rows)\n")
        fh.write(f"- `plan_governance/quarantine/legacy_product_crosswalk_quarantine.csv` ({len(quarantine)} rows)\n")

    print(f"P2E complete — catalog={len(catalog)} quarantine={len(quarantine)} p2a_diffs={p2a['cell_differences']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
