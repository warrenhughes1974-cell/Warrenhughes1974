"""
R7 — PAAGERAT segment resolution reconciliation (READ-ONLY).

Validates business join chain:
  PAAGERAT (TYPE_CODE=PR) -> PCOVRSGT -> PCOVR -> Policy Form Crosswalk -> PLAN

Produces:
  paagerat_segment_resolution_trace.csv
  paagerat_pr_plan_summary.csv
  paagerat_pr_gaps_vs_emitted.csv
  paagerat_segment_resolution_summary.json

Run:
  python plan_analysis/phase_r7_paagerat_segment_resolution/_reconcile_paagerat.py
"""
import os
import sys
import csv
import json
import collections

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import dbf

from qla_core import plan_source_paths as PSP
from qla_core import rate_factor_loader as L
from qla_core import rate_segment_resolution as SR
from qla_core import paagerat_pr_loader as PA

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
EMIT_GPS = os.path.join(ROOT, "plan_analysis", "phase_r5_rate_loader", "emitted_dbf", "QuikGps.dbf")


def emitted_gp_plans():
    if not os.path.isfile(EMIT_GPS):
        return set()
    t = dbf.Table(EMIT_GPS)
    t.open(mode=dbf.READ_ONLY)
    plans = {str(r.PLAN).strip() for r in t}
    t.close()
    return plans


def main():
    paagerat = PSP.paagerat_extract()
    pcovrsgt = PSP.pcovrsgt_csv()
    pcovr = PSP.pcovr_csv()
    xwalk = PSP.policy_form_crosswalk()

    cov2plan, _ = L.load_plan_crosswalk(xwalk)
    resolver = SR.SegmentResolver.from_files(pcovrsgt, pcovr, cov2plan)
    config = L.LoaderConfig()

    status = collections.Counter()
    by_plan = collections.Counter()
    trace_rows = []
    unresolved = []

    for t in PA.transform_paagerat_pr(paagerat, resolver, config):
        st = t["status"]
        status[st] += 1
        if st == "IN_SCOPE":
            by_plan[t["plan"]] += 1
            if len(trace_rows) < 5000:  # cap trace size
                trace_rows.append({
                    "SOURCE_SEGMENT_ID": t["coverage_id"],
                    "PARENT_COVERAGE_ID": t["parent_coverage_id"],
                    "PLAN": t["plan"],
                    "RESOLUTION_PATH": t["resolution_path"],
                    "PCOVR_DESCRIPTION": t.get("pcovr_description", ""),
                    "SEX": t["gender"],
                    "BAND": t["band"],
                    "UWCLASS": t["uwclass"],
                    "ATTAINED_AGE_SEQ": t["attained_age_seq"],
                    "QL_AGE": t["age"],
                    "VALUE": t["value"],
                    "LINENO": t["lineno"],
                })
        elif st == "SEGMENT_UNRESOLVED":
            unresolved.append(t)

    emitted = emitted_gp_plans()
    paagerat_plans = set(by_plan)
    gaps = sorted(paagerat_plans - emitted)
    overlap = sorted(paagerat_plans & emitted)

    # trace
    trace_path = os.path.join(HERE, "paagerat_segment_resolution_trace.csv")
    if trace_rows:
        with open(trace_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(trace_rows[0].keys()))
            w.writeheader()
            w.writerows(trace_rows)

    # plan summary
    summary_path = os.path.join(HERE, "paagerat_pr_plan_summary.csv")
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["PLAN", "PAAGERAT_PR_ROWS", "IN_EMITTED_QUikGps"])
        for plan in sorted(by_plan):
            w.writerow([plan, by_plan[plan], "Y" if plan in emitted else "N"])

    # gaps
    gaps_path = os.path.join(HERE, "paagerat_pr_gaps_vs_emitted.csv")
    with open(gaps_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["PLAN", "PAAGERAT_PR_ROWS", "GAP_TYPE", "NOTES"])
        for plan in gaps:
            w.writerow([plan, by_plan[plan], "MISSING_FROM_EMITTED_QUikGps",
                        "Segment-resolved PR not in current R5 QuikGps emit"])
        for plan in sorted(set(emitted) - paagerat_plans):
            w.writerow([plan, 0, "EMITTED_NOT_IN_PAAGERAT_PR",
                        "Current QuikGps plan has no PAAGERAT PR segment chain"])

    result = {
        "phase": "R7 PAAGERAT SEGMENT RESOLUTION",
        "sources": {
            "paagerat": os.path.relpath(paagerat, ROOT).replace("\\", "/"),
            "pcovrsgt": os.path.relpath(pcovrsgt, ROOT).replace("\\", "/"),
            "pcovr": os.path.relpath(pcovr, ROOT).replace("\\", "/"),
            "crosswalk": os.path.relpath(xwalk, ROOT).replace("\\", "/"),
        },
        "business_rules": {
            "join": "PAAGERAT.COVERAGE_ID -> PCOVRSGT.SEGT_ID -> PCOVRSGT.COVERAGE_ID -> PCOVR -> crosswalk PLAN",
            "type_code_filter": "PR only for policy premium rates",
        },
        "row_status": dict(status),
        "distinct_plans_resolved": len(by_plan),
        "distinct_plans_emitted_quikgps": len(emitted),
        "overlap_plans": len(overlap),
        "paagerat_only_plans": len(gaps),
        "unresolved_pr_segments": len(unresolved),
        "segment_keys_loaded": len(resolver._segt_to_parent),
        "all_pr_segments_resolved": len(unresolved) == 0,
    }
    json_path = os.path.join(HERE, "paagerat_segment_resolution_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    print(f"trace rows written: {len(trace_rows)} (capped at 5000)")
    print(f"plans in PAAGERAT PR: {len(by_plan)} | gaps vs emit: {len(gaps)}")
    if gaps[:10]:
        print("sample gaps:", gaps[:10])
    return 0 if result["all_pr_segments_resolved"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
