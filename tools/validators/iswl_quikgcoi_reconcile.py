"""
ISWL Phase 4 — QUIKGCOI reconcile: PAAGERAT U5 dry-run, segment gates, regression.

Checks: V-GCOI-01 through V-GCOI-04, Phase 1/2/3 regression.

Usage:
  python tools/validators/iswl_quikgcoi_reconcile.py
  python tools/validators/iswl_quikgcoi_reconcile.py --write-baseline
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from qla_core import rate_dbf_schema as S
from qla_core import rate_pipeline as P
from qla_core import rate_segment_resolution as SR
from qla_core import paagerat_ul_coi_loader as COI
from qla_core.rate_factor_loader import load_plan_crosswalk, quikcoi_keys_by_plan, quikgcoi_keys_by_plan
from tools.validators.iswl_common import (
    COI_BASELINE_PATH,
    GCOI_BASELINE_PATH,
    ISWL_COI_MPLANS,
    ISWL_COVERAGE_IDS,
    ISWL_GCOI_MPLANS,
    ensure_phase4_out,
    ensure_pipeline_out,
    load_config,
    resolve_path,
)

SCRIPT_VERSION = "1.0"
R5_DIR = PROJECT_ROOT / "plan_analysis" / "phase_r5_rate_loader"
EXPECTED_U5_ROWS = COI.EXPECTED_U5_SOURCE_ROWS
EXPECTED_OUTPUT_MIN = 198
EXPECTED_OUTPUT_MAX = 200
U5_SEGMENT_IDS = COI.U5_SEGMENT_IDS
U5_HUB_SEGMENT = "659 CEN II"
U5_HUB_MPLAN = "1679CS"


def _psegt_u5_gate(psegt_path: Path, pcovrsgt_path: Path) -> tuple[bool, int]:
    types_by_seg: dict[str, set[str]] = defaultdict(set)
    with open(psegt_path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            seg = (r.get("SEGMENT_ID") or "").strip()
            typ = (r.get("SEGT_TYPE") or "").strip()
            if seg and typ and typ != "---------":
                types_by_seg[seg].add(typ)
    cov_u5 = set()
    with open(pcovrsgt_path, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f)
        hdr = [c.strip() for c in next(rd)]
        col = {n: i for i, n in enumerate(hdr)}
        for row in rd:
            cov = row[col["COVERAGE_ID"]].strip()
            if cov not in ISWL_COVERAGE_IDS:
                continue
            if row[col["SEGT_FLAG"]].strip().upper() != "Y":
                continue
            seg = row[col["SEGT_ID"]].strip()
            if seg and "U5" in types_by_seg.get(seg, set()):
                cov_u5.add(cov)
    return len(cov_u5) == 8, len(cov_u5)


def _count_u5_source(path: Path, resolver) -> dict:
    in_scope = 0
    unresolved = 0
    nc_rows = 0
    u6_rows = 0
    segs = Counter()
    value_info_used = 0
    plans = Counter()
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f)
        hdr = [c.strip() for c in next(rd)]
        col = {n: i for i, n in enumerate(hdr)}
        for row in rd:
            typ = row[col["TYPE_CODE"]].strip()
            if typ == "NC":
                nc_rows += 1
                continue
            if typ == "U6":
                u6_rows += 1
                continue
            if typ != "U5" or row[col["RECORD_SEQ"]].strip() != "1":
                continue
            seg = row[col["COVERAGE_ID"]].strip()
            r = resolver.resolve(seg, source="paagerat")
            if not r:
                unresolved += 1
                segs[seg] += 1
                continue
            if r.plan not in ISWL_GCOI_MPLANS:
                continue
            in_scope += 1
            segs[seg] += 1
            plans[r.plan] += 1
            vi = row[col["VALUE_INFO"]].strip()
            if vi:
                value_info_used += 1
    return {
        "u5_in_scope": in_scope,
        "u5_unresolved": unresolved,
        "u5_segments": dict(segs),
        "nc_rows": nc_rows,
        "u6_rows": u6_rows,
        "value_info_rows": value_info_used,
        "plans": dict(plans),
    }


def _check_factor_rows(factor_rows: list[dict]) -> dict:
    qx1_blank = True
    value_info_ok = True
    schema_ok = True
    for row in factor_rows:
        for i in range(1, S.N_DURATION_COLS):
            if row.get(f"QX{i}", "").strip():
                qx1_blank = False
        if row.get("CNTL", "") != "00":
            schema_ok = False
        qx0 = row.get("QX0", "").strip()
        if not qx0:
            value_info_ok = False
    return {
        "qx1_qx9_blank": qx1_blank,
        "value_info_populated": value_info_ok,
        "cntl_00": schema_ok,
        "factor_row_count": len(factor_rows),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-baseline", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    if not cfg.get("iswl_phase4", {}).get("quikgcoi_enabled"):
        print("FAIL — iswl_phase4.quikgcoi_enabled is false")
        return 1

    config_path = cfg.get("_config_path", str(R5_DIR / "rate_loader_config.json"))
    repo = str(PROJECT_ROOT)
    out_dir = ensure_phase4_out()
    pipeline_dir = ensure_pipeline_out()

    res = P.run(config_path, repo)
    P.write_issue_reports(res, str(pipeline_dir))

    grid = res.grids.get("QuikGcoi", {})
    keys_by_plan = quikgcoi_keys_by_plan(grid)
    gcoi_keys = {p: keys_by_plan.get(p, 0) for p in sorted(ISWL_GCOI_MPLANS)}
    factor_rows = res.factor_rows.get("QuikGcoi", [])
    gcoi_in_scope = res.paagerat_gcoi_status.get("IN_SCOPE", 0)

    coi_factor_rows = res.factor_rows.get("QuikCoi", [])
    coi_keys_by_plan = quikcoi_keys_by_plan(res.grids.get("QuikCoi", {}))

    pa_path = resolve_path(cfg, "paagerat_pr_extract")
    psgt_path = resolve_path(cfg, "pcovrsgt_csv")
    pcovr_path = resolve_path(cfg, "pcovr_csv")
    psegt_path = resolve_path(cfg, "psegt_csv")
    xwalk_path = resolve_path(cfg, "plan_form_crosswalk")
    cov2plan, _ = load_plan_crosswalk(str(xwalk_path))
    resolver = SR.SegmentResolver.from_files(str(psgt_path), str(pcovr_path), cov2plan)
    src_stats = _count_u5_source(pa_path, resolver)
    factor_check = _check_factor_rows(factor_rows)

    psegt_ok, psegt_cov_count = _psegt_u5_gate(psegt_path, psgt_path)

    age_cap_u5 = sum(
        n for (plan, typ, orig, emit), n in res.age_cap.items()
        if typ == "U5" and orig == "100"
    )
    cap_collision_u5 = sum(
        1 for (_, _, _, plan, typ, _, _) in res.cap_collisions if typ == "U5"
    )

    # V-GCOI-01: U5 vs U6 separation — GCOI stream excludes U6/NC; COI stream unchanged
    v_gcoi_01 = (
        src_stats["u5_unresolved"] == 0
        and "U6" not in res.paagerat_gcoi_status
        and "NC" not in res.paagerat_gcoi_status
        and res.paagerat_coi_status.get("IN_SCOPE", 0) == 800
    )
    # V-GCOI-02: single parent concentration — 659 CEN II -> 1679CS only
    v_gcoi_02 = (
        gcoi_in_scope == EXPECTED_U5_ROWS
        and set(src_stats.get("plans", {}).keys()) == {U5_HUB_MPLAN}
        and set(src_stats["u5_segments"].keys()) <= U5_SEGMENT_IDS
        and src_stats["u5_segments"].get(U5_HUB_SEGMENT, 0) == EXPECTED_U5_ROWS
    )
    v_gcoi_03 = factor_check["cntl_00"] and len(factor_rows) > 0 and psegt_ok
    v_gcoi_04 = (
        factor_check["value_info_populated"]
        and src_stats["value_info_rows"] == EXPECTED_U5_ROWS
        and factor_check["qx1_qx9_blank"]
    )
    output_ok = EXPECTED_OUTPUT_MIN <= len(factor_rows) <= EXPECTED_OUTPUT_MAX

    snapshot = {
        "blocker_count": res.blocker_count,
        "quikgcoi_factor_rows": len(factor_rows),
        "quikgcoi_keys_by_plan": keys_by_plan,
        "iswl_gcoi_keys_by_plan": gcoi_keys,
        "paagerat_gcoi_in_scope": gcoi_in_scope,
    }

    regression_ok = True
    regression_notes = []
    if args.write_baseline or not GCOI_BASELINE_PATH.is_file():
        GCOI_BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        GCOI_BASELINE_PATH.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        regression_notes.append(f"Baseline written: {GCOI_BASELINE_PATH}")
    else:
        baseline = json.loads(GCOI_BASELINE_PATH.read_text(encoding="utf-8"))
        for plan, cnt in baseline.get("quikgcoi_keys_by_plan", {}).items():
            if plan not in ISWL_GCOI_MPLANS and keys_by_plan.get(plan, 0) != cnt:
                regression_ok = False
                regression_notes.append(f"non-ISWL QuikGcoi plan {plan} changed")

    # Phase 3 regression: QuikCoi unchanged
    if COI_BASELINE_PATH.is_file():
        coi_baseline = json.loads(COI_BASELINE_PATH.read_text(encoding="utf-8"))
        if len(coi_factor_rows) != coi_baseline.get("quikcoi_factor_rows"):
            regression_ok = False
            regression_notes.append(
                f"QuikCoi row count changed: {len(coi_factor_rows)} vs baseline "
                f"{coi_baseline.get('quikcoi_factor_rows')}"
            )
        for plan in ISWL_COI_MPLANS:
            base_cnt = coi_baseline.get("quikcoi_keys_by_plan", {}).get(plan)
            if base_cnt is not None and coi_keys_by_plan.get(plan, 0) != base_cnt:
                regression_ok = False
                regression_notes.append(f"QuikCoi {plan} keys changed")

    non_iswl_gcoi = [p for p in keys_by_plan if p not in ISWL_GCOI_MPLANS]
    if non_iswl_gcoi:
        regression_ok = False
        regression_notes.append(f"unexpected QuikGcoi plans: {non_iswl_gcoi}")

    summary = {
        "script_version": SCRIPT_VERSION,
        "blocker_count": res.blocker_count,
        "emit_ready": res.emit_ready,
        "v_gcoi_01_u5_u6_separation": v_gcoi_01,
        "v_gcoi_02_single_parent": v_gcoi_02,
        "v_gcoi_03_schema_psegt": v_gcoi_03,
        "v_gcoi_04_value_info_qx_blank": v_gcoi_04,
        "v_gcoi_seq100_caps": age_cap_u5,
        "v_gcoi_cap_collisions": cap_collision_u5,
        "paagerat_gcoi_in_scope": gcoi_in_scope,
        "quikgcoi_factor_rows": len(factor_rows),
        "iswl_gcoi_keys_by_mplan": gcoi_keys,
        "source_stats": src_stats,
        "factor_check": factor_check,
        "output_in_expected_range": output_ok,
        "regression_ok": regression_ok,
        "regression_notes": regression_notes,
        "phase3_quikcoi_rows": len(coi_factor_rows),
    }
    (out_dir / "iswl_quikgcoi_reconcile_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")

    with open(out_dir / "iswl_quikgcoi_keys_by_mplan.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["MPLAN", "QUIKGCOI_FACTOR_ROWS", "SOURCE_U5_ROWS"])
        for p in sorted(ISWL_GCOI_MPLANS):
            w.writerow([p, gcoi_keys.get(p, 0), src_stats.get("plans", {}).get(p, "")])

    print("=" * 72)
    print(f"ISWL QUIKGCOI RECONCILE v{SCRIPT_VERSION}")
    print(f"Blockers: {res.blocker_count}  emit_ready: {res.emit_ready}")
    print(f"PAAGERAT U5 IN_SCOPE: {gcoi_in_scope} (expect {EXPECTED_U5_ROWS})")
    print(f"QuikGcoi factor rows: {len(factor_rows)} (expect {EXPECTED_OUTPUT_MIN}–{EXPECTED_OUTPUT_MAX})")
    for p in sorted(ISWL_GCOI_MPLANS):
        print(f"  {p}: {gcoi_keys.get(p, 0)} keys")
    print(f"V-GCOI-01 U5/U6 separation: {'PASS' if v_gcoi_01 else 'FAIL'}")
    print(f"V-GCOI-02 single parent 659 CEN II: {'PASS' if v_gcoi_02 else 'FAIL'}")
    print(f"V-GCOI-03 schema + PSEGT U5 8/8: {'PASS' if v_gcoi_03 else 'FAIL'} ({psegt_cov_count}/8)")
    print(f"V-GCOI-04 VALUE_INFO + QX1–QX9 blank: {'PASS' if v_gcoi_04 else 'FAIL'}")
    print(f"SEQ=100 caps: {age_cap_u5} age_caps, {cap_collision_u5} cap_collisions")
    print(f"Phase 3 QuikCoi rows (regression): {len(coi_factor_rows)}")
    print(f"Non-ISWL + Phase 1–3 regression: {'PASS' if regression_ok else 'FAIL'}")
    print("=" * 72)

    errors = []
    if res.blocker_count:
        errors.append("blockers")
    if gcoi_in_scope != EXPECTED_U5_ROWS:
        errors.append(f"U5 count {gcoi_in_scope}")
    if not output_ok:
        errors.append(f"output rows {len(factor_rows)}")
    if not v_gcoi_01:
        errors.append("V-GCOI-01")
    if not v_gcoi_02:
        errors.append("V-GCOI-02")
    if not v_gcoi_03:
        errors.append("V-GCOI-03")
    if not v_gcoi_04:
        errors.append("V-GCOI-04")
    if not regression_ok:
        errors.append("regression")

    if errors:
        print("FAIL —", "; ".join(errors))
        return 1
    print("PASS — ISWL Phase 4 QUIKGCOI reconcile")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
