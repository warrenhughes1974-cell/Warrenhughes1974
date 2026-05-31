"""
Phase R7A — QuikPlan rate variation flag enrichment runner.

Usage:
  python plan_analysis/phase_r7a_quikplan_rate_variation_flags/run_r7a_enrichment.py

Optional:
  python .../run_r7a_enrichment.py --quikplan QLA_Migration/Output/quikplan.csv
"""
import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from qla_core import plan_source_paths as PSP
from qla_core.quikplan_rate_variation_flags import (
    ANALYSIS_FIELDS,
    UPDATE_FIELDS,
    analyze_rate_segmentation,
    apply_flag_updates_to_quikplan_rows,
    build_summary_markdown,
    load_quikplan_csv,
    validate_enrichment,
    write_csv,
)
from qla_core.schema_constants import QUIKPLAN_SCHEMA

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

DEFAULT_QUIKPLAN = os.path.join(ROOT, "QLA_Migration", "Output", "quikplan.csv")
DEFAULT_EMIT_DBF = os.path.join(ROOT, "plan_analysis", "phase_r5_rate_loader", "emitted_dbf")


def main():
    ap = argparse.ArgumentParser(description="R7A quikplan rate variation flag enrichment")
    ap.add_argument("--quikplan", default=DEFAULT_QUIKPLAN, help="Input quikplan.csv")
    ap.add_argument("--emitted-dbf", default=DEFAULT_EMIT_DBF, help="Emitted rate-key DBF dir")
    ap.add_argument("--skip-quikplan-output", action="store_true", help="Audit only; no enriched CSV")
    args = ap.parse_args()

    analysis_rows, updates = analyze_rate_segmentation(
        emitted_dbf_dir=args.emitted_dbf if os.path.isdir(args.emitted_dbf) else None,
    )

    analysis_path = os.path.join(HERE, "quikplan_rate_variation_analysis.csv")
    updates_path = os.path.join(HERE, "quikplan_variation_flag_updates.csv")
    summary_path = os.path.join(HERE, "quikplan_variation_flag_summary.md")
    enriched_path = os.path.join(HERE, "quikplan_with_rate_variation_flags.csv")

    write_csv(analysis_path, ANALYSIS_FIELDS, analysis_rows)
    write_csv(updates_path, UPDATE_FIELDS, [updates[p] for p in sorted(updates)])

    validation_issues = []
    if os.path.isfile(args.quikplan):
        original = load_quikplan_csv(args.quikplan)
        quikplan_plans = {r["PLAN"].strip() for r in original if r.get("PLAN", "").strip()}
        # Only update plans present in both quikplan and rate-derived updates
        applicable = {p: u for p, u in updates.items() if p in quikplan_plans}
        enriched = apply_flag_updates_to_quikplan_rows(original, applicable)
        validation_issues = validate_enrichment(quikplan_plans, applicable, original, enriched)

        if not args.skip_quikplan_output and not validation_issues:
            with open(enriched_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=QUIKPLAN_SCHEMA, extrasaction="ignore")
                w.writeheader()
                for row in enriched:
                    w.writerow({c: row.get(c, "") for c in QUIKPLAN_SCHEMA})
        elif validation_issues:
            print(f"VALIDATION BLOCKED enriched output ({len(validation_issues)} issue(s))")
            for iss in validation_issues[:10]:
                print(f"  [{iss['severity']}] {iss.get('plan','')}: {iss['detail']}")
    else:
        applicable = updates
        enriched_path = "(skipped — quikplan input not found)"

    paths = {
        "Analysis": os.path.relpath(analysis_path, ROOT),
        "Flag updates": os.path.relpath(updates_path, ROOT),
        "Summary": os.path.relpath(summary_path, ROOT),
        "Enriched quikplan": os.path.relpath(enriched_path, ROOT) if isinstance(enriched_path, str) and os.path.isfile(enriched_path) else enriched_path,
    }
    summary_md = build_summary_markdown(analysis_rows, applicable, validation_issues, paths)
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_md)

    from collections import Counter
    flag_y = Counter()
    for u in applicable.values():
        for k, v in u.items():
            if k.startswith(("GDVARY", "UWVARY", "BDVARY", "STVARY")) and v == "Y":
                flag_y[k] += 1

    report = {
        "plans_analyzed": len(set(r["PLAN"] for r in analysis_rows)),
        "plan_family_rows": len(analysis_rows),
        "plans_updated": len(applicable),
        "planvalopt_y": sum(1 for u in applicable.values() if u["PLANVALOPT"] == "Y"),
        "validation_blockers": len(validation_issues),
        "top_flags_y": dict(flag_y.most_common(10)),
        "outputs": paths,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
