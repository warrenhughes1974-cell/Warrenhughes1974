"""
ISWL Phase 6 — QUIKISSC reconcile: Rate_Table SL → QuikIssc dry-run validation.

Checks: V-ISSC-01 through V-ISSC-12.

Usage:
  python tools/validators/iswl_quikissc_reconcile.py
  python tools/validators/iswl_quikissc_reconcile.py --write-baseline
  python tools/validators/iswl_quikissc_reconcile.py --emit-csv
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from qla_core import rate_dbf_schema as S
from qla_core import rate_pipeline as P
from qla_core import quikissc_loader as ISSC
from tools.validators.iswl_common import (
    EXPECTED_ISSC_ROWS,
    ISWL_COVERAGE_IDS,
    ISWL_ISSC_MPLANS,
    ISSC_BASELINE_PATH,
    ensure_issue33_baselines_out,
    ensure_phase6_out,
    ensure_pipeline_out,
    load_config,
    resolve_path,
)

SCRIPT_VERSION = "1.0"
R5_DIR = PROJECT_ROOT / "plan_analysis" / "phase_r5_rate_loader"
MIGRATION_RATES = PROJECT_ROOT / "QLA_Migration" / "Output" / "rates" / "QuikIssc.csv"
EXPECTED_SCHEDULE = ISSC.expected_hub_schg_schedule()
INDEX_FIELDS = ("PLAN", "GENDER", "UWCLASS", "BAND", "ISSCNTRY", "ISSUEST")
SCHG_POPULATED = tuple(f"SCHG{i:02d}" for i in range(1, 15))
SCHG_BLANK = tuple(f"SCHG{i:02d}" for i in range(15, 21))


def _psegt_sl_gate(psegt_path: Path, pcovrsgt_path: Path) -> tuple[bool, int]:
    types_by_seg: dict[str, set[str]] = defaultdict(set)
    with open(psegt_path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            seg = (r.get("SEGMENT_ID") or "").strip()
            typ = (r.get("SEGT_TYPE") or "").strip()
            if seg and typ and typ != "---------":
                types_by_seg[seg].add(typ)
    cov_hit: set[str] = set()
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
            if seg and "SL" in types_by_seg.get(seg, set()):
                cov_hit.add(cov)
    return len(cov_hit) == 8, len(cov_hit)


def _check_schema_fields() -> bool:
    fields = S.quikissc_fields()
    names = [f[0] for f in fields]
    expected = (
        ["PLAN", "AGE", "GENDER", "UWCLASS", "BAND", "ISSCNTRY", "ISSUEST"]
        + list(SCHG_POPULATED)
        + list(SCHG_BLANK)
    )
    return names == expected


def _rate_is_percent_literal(rate: str) -> bool:
    try:
        v = float(rate)
    except ValueError:
        return False
    return v >= 2.0


def _analyze_rows(rows: list[dict]) -> dict:
    by_plan: dict[str, dict] = {}
    for r in rows:
        by_plan[r["PLAN"]] = r
    index_keys = [tuple(r[f] for f in INDEX_FIELDS) for r in rows]
    dupes = len(index_keys) - len(set(index_keys))

    uwclass_ok = all(r.get("UWCLASS") == "SM" for r in rows)
    age_ok = all(str(r.get("AGE", "")).strip() == "0" for r in rows)
    schg_tail_blank = all(
        all(not str(r.get(f, "")).strip() for f in SCHG_BLANK) for r in rows
    )
    percent_ok = all(
        _rate_is_percent_literal(r[f]) for r in rows for f in SCHG_POPULATED if r.get(f)
    )
    schg_ok = True
    for plan in ISWL_ISSC_MPLANS:
        r = by_plan.get(plan)
        if not r:
            schg_ok = False
            continue
        for dur, exp in EXPECTED_SCHEDULE.items():
            field = f"SCHG{dur:02d}"
            got = r.get(field, "")
            if not got or f"{float(got):.4f}" != exp:
                schg_ok = False

    return {
        "row_count": len(rows),
        "distinct_plans": len(by_plan),
        "rows_by_plan": {p: 1 if p in by_plan else 0 for p in sorted(ISWL_ISSC_MPLANS)},
        "duplicate_index_keys": dupes,
        "uwclass_sm": uwclass_ok,
        "age_zero": age_ok,
        "schg01_14_ok": schg_ok,
        "schg15_20_blank": schg_tail_blank,
        "percent_literal": percent_ok,
    }


def _phase1_5_regression() -> tuple[bool, list[str]]:
    notes: list[str] = []
    scripts = [
        ("Phase1", PROJECT_ROOT / "tools" / "validators" / "iswl_quikcvs_reconcile.py"),
        ("Phase2", PROJECT_ROOT / "tools" / "validators" / "iswl_quikgps_reconcile.py"),
        ("Phase3", PROJECT_ROOT / "tools" / "validators" / "iswl_quikcoi_reconcile.py"),
        ("Phase4", PROJECT_ROOT / "tools" / "validators" / "iswl_quikgcoi_reconcile.py"),
        ("Phase5", PROJECT_ROOT / "tools" / "validators" / "iswl_quikuint_reconcile.py"),
    ]
    ok = True
    for label, script in scripts:
        if not script.is_file():
            notes.append(f"{label}: script missing")
            ok = False
            continue
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            ok = False
            notes.append(f"{label}: FAIL (exit {proc.returncode})")
        else:
            notes.append(f"{label}: PASS")
    return ok, notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-baseline", action="store_true")
    ap.add_argument("--emit-csv", action="store_true", help="write QuikIssc.csv to QLA_Migration/Output/rates")
    args = ap.parse_args()

    cfg = load_config()
    if not cfg.get("iswl_phase6", {}).get("quikissc_enabled"):
        print("FAIL — iswl_phase6.quikissc_enabled is false")
        return 1

    config_path = cfg.get("_config_path", str(R5_DIR / "rate_loader_config.json"))
    repo = str(PROJECT_ROOT)
    out_dir = ensure_phase6_out()
    pipeline_dir = ensure_pipeline_out()

    res = P.run(config_path, repo)
    P.write_issue_reports(res, str(pipeline_dir))

    rows = list(res.quikissc_rows)
    analysis = _analyze_rows(rows)

    psegt_path = resolve_path(cfg, "psegt_csv")
    psgt_path = resolve_path(cfg, "pcovrsgt_csv")
    sl_ok, sl_count = _psegt_sl_gate(psegt_path, psgt_path)

    rate_path = resolve_path(cfg, "source_rate_extract")
    phase6 = cfg.get("iswl_phase6", {})
    hub_cov = phase6.get("rate_coverage_id", "659 CEN II")
    hub_schedule = ISSC.load_rate_table_sl_schedule(
        str(rate_path),
        coverage_id=hub_cov,
        type_code=phase6.get("rate_type_code", "SL"),
    )

    v01 = _check_schema_fields()
    v02 = sl_ok and len(hub_schedule) == 14
    v03 = analysis["distinct_plans"] == 8 and set(analysis["rows_by_plan"].keys()) == ISWL_ISSC_MPLANS
    v04 = analysis["row_count"] == EXPECTED_ISSC_ROWS
    v05 = analysis["uwclass_sm"]
    v06 = analysis["age_zero"]
    v07 = analysis["schg01_14_ok"]
    v08 = analysis["schg15_20_blank"]
    v09 = analysis["percent_literal"]
    v10 = analysis["duplicate_index_keys"] == 0

    snapshot = {
        "blocker_count": res.blocker_count,
        "quikissc_rows": analysis["row_count"],
        "rows_by_plan": analysis["rows_by_plan"],
        "quikuint_rows_unchanged": len(res.quikuint_rows),
        "factor_rows_unchanged": {
            "QuikCvs": len(res.factor_rows.get("QuikCvs", [])),
            "QuikGps": len(res.factor_rows.get("QuikGps", [])),
            "QuikCoi": len(res.factor_rows.get("QuikCoi", [])),
            "QuikGcoi": len(res.factor_rows.get("QuikGcoi", [])),
        },
    }

    ensure_issue33_baselines_out()
    regression_ok = True
    regression_notes: list[str] = []
    if args.write_baseline or not ISSC_BASELINE_PATH.is_file():
        ISSC_BASELINE_PATH.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        regression_notes.append(f"ISSC baseline written: {ISSC_BASELINE_PATH}")
    else:
        baseline = json.loads(ISSC_BASELINE_PATH.read_text(encoding="utf-8"))
        if len(res.quikuint_rows) != baseline.get("quikuint_rows_unchanged"):
            regression_ok = False
            regression_notes.append("QuikUint row count changed")
        for k, v in baseline.get("factor_rows_unchanged", {}).items():
            if len(res.factor_rows.get(k, [])) != v:
                regression_ok = False
                regression_notes.append(f"{k} row count changed")

    v11, phase_notes = _phase1_5_regression()
    regression_ok = regression_ok and v11

    v12 = False
    if args.emit_csv and v04 and v03 and res.blocker_count == 0:
        from qla_core import rate_dbf_writer as W

        MIGRATION_RATES.parent.mkdir(parents=True, exist_ok=True)
        W.write_quikissc_csv(str(MIGRATION_RATES), rows, overwrite=True)
        v12 = MIGRATION_RATES.is_file()
    elif MIGRATION_RATES.is_file():
        v12 = True

    summary = {
        "script_version": SCRIPT_VERSION,
        "blocker_count": res.blocker_count,
        "emit_ready": res.emit_ready,
        "v_iss_c_01_schema": v01,
        "v_iss_c_02_psegt_sl": v02,
        "v_iss_c_03_mplans_8_8": v03,
        "v_iss_c_04_row_count_8": v04,
        "v_iss_c_05_uwclass_sm": v05,
        "v_iss_c_06_age_zero": v06,
        "v_iss_c_07_schg01_14": v07,
        "v_iss_c_08_schg15_20_blank": v08,
        "v_iss_c_09_percent_literal": v09,
        "v_iss_c_10_unique_index": v10,
        "v_iss_c_11_phase1_5_regression": v11,
        "v_iss_c_12_quikissc_csv": v12,
        "psegt_sl_gate": {"pass": sl_ok, "count": sl_count},
        "hub_sl_durations": len(hub_schedule),
        "hub_schedule": hub_schedule,
        "analysis": analysis,
        "regression_ok": regression_ok,
        "regression_notes": regression_notes,
        "phase1_5_notes": phase_notes,
        "quikissc_csv": str(MIGRATION_RATES) if MIGRATION_RATES.is_file() else None,
    }
    (out_dir / "iswl_quikissc_reconcile_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")

    schg_hdr = list(SCHG_POPULATED) + list(SCHG_BLANK)
    with open(out_dir / "iswl_quikissc_keys_by_mplan.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["PLAN", "AGE", "GENDER", "UWCLASS", "BAND", "ISSCNTRY", "ISSUEST"] + schg_hdr)
        for r in sorted(rows, key=lambda x: x["PLAN"]):
            w.writerow([r["PLAN"], r["AGE"], r["GENDER"], r["UWCLASS"], r["BAND"],
                        r["ISSCNTRY"], r["ISSUEST"]] + [r.get(h, "") for h in schg_hdr])

    print("=" * 72)
    print(f"ISWL QUIKISSC RECONCILE v{SCRIPT_VERSION}")
    print(f"Blockers: {res.blocker_count}  emit_ready: {res.emit_ready}")
    print(f"QuikIssc rows: {analysis['row_count']} (expect {EXPECTED_ISSC_ROWS})")
    for p in sorted(ISWL_ISSC_MPLANS):
        print(f"  {p}: {analysis['rows_by_plan'].get(p, 0)} row(s)")
    print(f"V-ISSC-01 schema: {'PASS' if v01 else 'FAIL'}")
    print(f"V-ISSC-02 PSEGT->SL: {'PASS' if v02 else 'FAIL'} ({sl_count}/8 coverages, {len(hub_schedule)} durations)")
    print(f"V-ISSC-03 MPLANs 8/8: {'PASS' if v03 else 'FAIL'}")
    print(f"V-ISSC-04 row count 8: {'PASS' if v04 else 'FAIL'}")
    print(f"V-ISSC-05 UWCLASS=SM: {'PASS' if v05 else 'FAIL'}")
    print(f"V-ISSC-06 AGE=0: {'PASS' if v06 else 'FAIL'}")
    print(f"V-ISSC-07 SCHG01-14: {'PASS' if v07 else 'FAIL'}")
    print(f"V-ISSC-08 SCHG15-20 blank: {'PASS' if v08 else 'FAIL'}")
    print(f"V-ISSC-09 percent literal: {'PASS' if v09 else 'FAIL'}")
    print(f"V-ISSC-10 unique index: {'PASS' if v10 else 'FAIL'} (dupes={analysis['duplicate_index_keys']})")
    print(f"V-ISSC-11 Phase1-5 regression: {'PASS' if v11 else 'FAIL'}")
    print(f"V-ISSC-12 QuikIssc.csv: {'PASS' if v12 else 'FAIL'}")
    print(f"PSEGT SL gate: {sl_count}/8")
    print("=" * 72)

    errors = []
    if res.blocker_count:
        errors.append("blockers")
    for tag, ok in [
        ("V-ISSC-01", v01), ("V-ISSC-02", v02), ("V-ISSC-03", v03), ("V-ISSC-04", v04),
        ("V-ISSC-05", v05), ("V-ISSC-06", v06), ("V-ISSC-07", v07), ("V-ISSC-08", v08),
        ("V-ISSC-09", v09), ("V-ISSC-10", v10), ("V-ISSC-11", v11),
    ]:
        if not ok:
            errors.append(tag)
    if not regression_ok:
        errors.append("factor regression")
    if args.emit_csv and not v12:
        errors.append("V-ISSC-12")

    if errors:
        print("FAIL —", "; ".join(errors))
        return 1
    print("PASS — ISWL Phase 6 QUIKISSC reconcile")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
