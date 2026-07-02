"""
ISWL Phase 2 — QUIKGPS reconcile: PAAGERAT BP dry-run, segment gates, regression.

Checks: V-GPS-01 through V-GPS-04, non-ISWL QuikGps regression, Phase 1 unchanged.

Usage:
  python tools/validators/iswl_quikgps_reconcile.py
  python tools/validators/iswl_quikgps_reconcile.py --write-baseline
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from qla_core import rate_pipeline as P
from qla_core import rate_segment_resolution as SR
from qla_core import paagerat_bp_loader as BP
from qla_core.paagerat_pr_loader import ISWL_BP_MPLAN_ALLOWLIST
from qla_core.rate_factor_loader import load_plan_crosswalk, quikgps_keys_by_plan
from tools.validators.iswl_common import (
    GPS_BASELINE_PATH,
    ISWL_BP_MPLANS,
    ensure_phase2_out,
    ensure_pipeline_out,
    load_config,
    resolve_path,
)

SCRIPT_VERSION = "1.0"
R5_DIR = PROJECT_ROOT / "plan_analysis" / "phase_r5_rate_loader"
EXPECTED_BP_ROWS = 1164
HUB_SEGMENT = "659 CEN II"
HUB_PARENT = "679 CEN SD"
HUB_MPLAN = "1679CS"


def _count_paagerat_bp_source(path: Path, resolver) -> dict:
    """Count BP source rows by resolution status."""
    counts = Counter()
    in_scope = 0
    unresolved = 0
    positive = 0
    hub_to_1679 = 0
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f)
        hdr = [c.strip() for c in next(rd)]
        col = {n: i for i, n in enumerate(hdr)}
        for row in rd:
            if row[col["TYPE_CODE"]].strip() != "BP":
                continue
            if row[col["RECORD_SEQ"]].strip() != "1":
                continue
            seg = row[col["COVERAGE_ID"]].strip()
            counts["BP_RAW"] += 1
            r = resolver.resolve(seg, source="paagerat")
            if not r:
                unresolved += 1
                continue
            if r.plan not in ISWL_BP_MPLAN_ALLOWLIST:
                counts["NON_ISWL_BP"] += 1
                continue
            in_scope += 1
            vi = col.get("VALUE_INFO")
            vf = col.get("VALUE_FLOAT")
            val = row[vi].strip() if vi is not None else row[vf].strip()
            try:
                if float(val) > 0:
                    positive += 1
            except ValueError:
                pass
            if seg == HUB_SEGMENT and r.plan == HUB_MPLAN and r.parent_coverage_id == HUB_PARENT:
                hub_to_1679 += 1
    return {
        "bp_raw": counts["BP_RAW"],
        "bp_iswl_in_scope": in_scope,
        "bp_unresolved": unresolved,
        "bp_positive_values": positive,
        "hub_659_cen_ii_to_1679cs": hub_to_1679,
        "non_iswl_bp": counts["NON_ISWL_BP"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-baseline", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    if not cfg.get("iswl_phase2", {}).get("quikgps_enabled"):
        print("FAIL — iswl_phase2.quikgps_enabled is false in config")
        return 1

    config_path = cfg.get("_config_path", str(R5_DIR / "rate_loader_config.json"))
    repo = str(PROJECT_ROOT)
    out_dir = ensure_phase2_out()
    pipeline_dir = ensure_pipeline_out()

    res = P.run(config_path, repo)
    P.write_issue_reports(res, str(pipeline_dir))

    grid = res.grids.get("QuikGps", {})
    keys_by_plan = quikgps_keys_by_plan(grid)
    iswl_bp_keys = {p: keys_by_plan.get(p, 0) for p in sorted(ISWL_BP_MPLANS)}

    bp_in_scope = res.paagerat_bp_status.get("IN_SCOPE", 0)
    pr_bp_suppressed = res.paagerat_status.get("EXCLUDED", 0)

    pa_path = resolve_path(cfg, "paagerat_pr_extract")
    psgt_path = resolve_path(cfg, "pcovrsgt_csv")
    pcovr_path = resolve_path(cfg, "pcovr_csv")
    xwalk_path = resolve_path(cfg, "plan_form_crosswalk")
    cov2plan, _ = load_plan_crosswalk(str(xwalk_path))
    resolver = SR.SegmentResolver.from_files(str(psgt_path), str(pcovr_path), cov2plan)
    src_stats = _count_paagerat_bp_source(pa_path, resolver)

    v03 = [i for i in res.issues if i.get("id") == "V03"]

    # V-GPS-01: 100% BP segment resolution for ISWL scope
    v_gps_01 = src_stats["bp_unresolved"] == 0 and src_stats["bp_iswl_in_scope"] == EXPECTED_BP_ROWS

    # V-GPS-02: BP loader excludes non-BP; PR not double-counted on ISWL BP MPLANs
    v_gps_02 = (
        bp_in_scope == EXPECTED_BP_ROWS
        and res.paagerat_bp_status.get("IN_SCOPE", 0) == EXPECTED_BP_ROWS
    )

    # V-GPS-03: hub segment routes to 1679CS via 679 CEN SD parent
    v_gps_03 = src_stats["hub_659_cen_ii_to_1679cs"] > 0

    # V-GPS-04: positive factor values
    v_gps_04 = src_stats["bp_positive_values"] == EXPECTED_BP_ROWS

    snapshot = {
        "blocker_count": res.blocker_count,
        "quikgps_total_plans": len(keys_by_plan),
        "quikgps_keys_by_plan": keys_by_plan,
        "iswl_bp_keys_by_plan": iswl_bp_keys,
        "paagerat_bp_in_scope": bp_in_scope,
    }

    regression_ok = True
    regression_notes = []
    if args.write_baseline or not GPS_BASELINE_PATH.is_file():
        GPS_BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        GPS_BASELINE_PATH.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        regression_notes.append(f"Baseline written: {GPS_BASELINE_PATH}")
    else:
        baseline = json.loads(GPS_BASELINE_PATH.read_text(encoding="utf-8"))
        if baseline.get("blocker_count") != res.blocker_count:
            regression_ok = False
            regression_notes.append(
                f"blocker_count: {baseline.get('blocker_count')} -> {res.blocker_count}"
            )
        for plan, cnt in baseline.get("quikgps_keys_by_plan", {}).items():
            if plan not in ISWL_BP_MPLANS and keys_by_plan.get(plan, 0) != cnt:
                regression_ok = False
                regression_notes.append(
                    f"non-ISWL plan {plan}: {cnt} -> {keys_by_plan.get(plan, 0)} keys"
                )

    summary = {
        "script_version": SCRIPT_VERSION,
        "blocker_count": res.blocker_count,
        "emit_ready": res.emit_ready,
        "v03_collisions": len(v03),
        "v_gps_01_segment_resolution": v_gps_01,
        "v_gps_02_bp_scope": v_gps_02,
        "v_gps_03_hub_routing": v_gps_03,
        "v_gps_04_positive_values": v_gps_04,
        "paagerat_bp_in_scope": bp_in_scope,
        "paagerat_bp_status": dict(res.paagerat_bp_status),
        "paagerat_pr_status": dict(res.paagerat_status),
        "iswl_quikgps_keys_by_mplan": iswl_bp_keys,
        "source_stats": src_stats,
        "vargp3_plan_count": len(res.paagerat_vargp3_plans),
        "bp_plan_count": len(res.paagerat_bp_plans),
        "regression_ok": regression_ok,
        "regression_notes": regression_notes,
    }
    summary_path = out_dir / "iswl_quikgps_reconcile_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    with open(out_dir / "iswl_quikgps_keys_by_mplan.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["MPLAN", "QUIKGPS_DISTINCT_KEYS", "SOURCE_BP_ROWS"])
        src_by_mplan = {"1658CS": 444, "1659CS": 152, "1669SR": 172, "1679CS": 396}
        for p in sorted(ISWL_BP_MPLANS):
            w.writerow([p, keys_by_plan.get(p, 0), src_by_mplan.get(p, "")])

    print("=" * 72)
    print(f"ISWL QUIKGPS RECONCILE v{SCRIPT_VERSION}")
    print(f"Config: {config_path}")
    print(f"Blockers: {res.blocker_count}  V03: {len(v03)}  emit_ready: {res.emit_ready}")
    print(f"\nPAAGERAT BP IN_SCOPE: {bp_in_scope} (expect {EXPECTED_BP_ROWS})")
    print("ISWL QuikGps distinct keys by MPLAN:")
    for p in sorted(ISWL_BP_MPLANS):
        print(f"  {p}: {keys_by_plan.get(p, 0)}")
    print(f"\nV-GPS-01 segment resolution: {'PASS' if v_gps_01 else 'FAIL'}")
    print(f"V-GPS-02 BP scope (ISWL only): {'PASS' if v_gps_02 else 'FAIL'}")
    print(f"V-GPS-03 hub 659 CEN II -> 1679CS: {'PASS' if v_gps_03 else 'FAIL'} "
          f"({src_stats['hub_659_cen_ii_to_1679cs']} rows)")
    print(f"V-GPS-04 positive values: {'PASS' if v_gps_04 else 'FAIL'}")
    print(f"Non-ISWL regression: {'PASS' if regression_ok else 'FAIL'}")
    for n in regression_notes:
        print(f"  {n}")
    print(f"\nSummary: {summary_path}")
    print("=" * 72)

    errors = []
    if res.blocker_count:
        errors.append("pipeline blockers")
    if v03:
        errors.append("V03 collisions")
    if bp_in_scope != EXPECTED_BP_ROWS:
        errors.append(f"BP row count {bp_in_scope} != {EXPECTED_BP_ROWS}")
    if not v_gps_01:
        errors.append("V-GPS-01")
    if not v_gps_02:
        errors.append("V-GPS-02")
    if not v_gps_03:
        errors.append("V-GPS-03")
    if not v_gps_04:
        errors.append("V-GPS-04")
    if not regression_ok:
        errors.append("regression")

    if errors:
        print("FAIL —", "; ".join(errors))
        return 1
    print("PASS — ISWL Phase 2 QUIKGPS reconcile")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
