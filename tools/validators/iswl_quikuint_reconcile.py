"""
ISWL Phase 5 — QUIKUINT reconcile: PDINT union_merge → QuikUint dry-run validation.

Checks: V-UINT-01 through V-UINT-10.

Usage:
  python tools/validators/iswl_quikuint_reconcile.py
  python tools/validators/iswl_quikuint_reconcile.py --write-baseline
  python tools/validators/iswl_quikuint_reconcile.py --emit-csv
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from qla_core import rate_dbf_schema as S
from qla_core import rate_pipeline as P
from qla_core import quikuint_loader as UINT
from qla_core.cso_mortality_crosswalk import ISWL_MPLAN_ALLOWLIST
from tools.validators.iswl_common import (
    EXPECTED_UINT_ROWS,
    EXPECTED_UINT_TIERS_PER_MPLAN,
    ISWL_COVERAGE_IDS,
    ISWL_UINT_MPLANS,
    PHASE5_OUT,
    PIPELINE_OUT,
    UINT_BASELINE_PATH,
    ensure_issue32_baselines_out,
    ensure_phase5_out,
    ensure_pipeline_out,
    load_config,
    resolve_path,
)

SCRIPT_VERSION = "1.0"
R5_DIR = PROJECT_ROOT / "plan_analysis" / "phase_r5_rate_loader"
MIGRATION_RATES = PROJECT_ROOT / "QLA_Migration" / "Output" / "rates" / "QuikUint.csv"
EXPECTED_SCHEDULE = UINT.expected_union_schedule()


def _psegt_interest_gate(psegt_path: Path, pcovrsgt_path: Path, seg_type: str) -> tuple[bool, int]:
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
            if seg and seg_type in types_by_seg.get(seg, set()):
                cov_hit.add(cov)
    return len(cov_hit) == 8, len(cov_hit)


def _check_schema_fields() -> bool:
    fields = S.quikuint_fields()
    names = [f[0] for f in fields]
    return names == ["MPLAN", "MEFFDATE", "MGTDRATE", "MCURRATE"]


def _rate_is_percent_literal(rate: str) -> bool:
    try:
        v = float(rate)
    except ValueError:
        return False
    return v >= 1.0 or rate.startswith(("4.", "5.", "7.", "9.", "11."))


def _analyze_rows(rows: list[dict]) -> dict:
    by_mplan: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_mplan[r["MPLAN"]].append(r)
    index_keys = [(r["MPLAN"], r["MEFFDATE"]) for r in rows]
    dupes = len(index_keys) - len(set(index_keys))
    mirror_ok = all(r["MGTDRATE"] == r["MCURRATE"] for r in rows)
    percent_ok = all(_rate_is_percent_literal(r["MCURRATE"]) for r in rows)
    schedule_ok = True
    for mplan in ISWL_UINT_MPLANS:
        dates = {r["MEFFDATE"] for r in by_mplan.get(mplan, [])}
        if dates != set(EXPECTED_SCHEDULE.keys()):
            schedule_ok = False
        for r in by_mplan.get(mplan, []):
            exp = EXPECTED_SCHEDULE.get(r["MEFFDATE"])
            if exp and f"{float(r['MCURRATE']):.4f}" != exp:
                schedule_ok = False
    return {
        "row_count": len(rows),
        "distinct_mplans": len(by_mplan),
        "rows_by_mplan": {p: len(by_mplan.get(p, [])) for p in sorted(ISWL_UINT_MPLANS)},
        "duplicate_index_keys": dupes,
        "mgt_mcur_mirror": mirror_ok,
        "percent_literal": percent_ok,
        "schedule_ok": schedule_ok,
        "loan_columns_absent": all(
            k not in (rows[0].keys() if rows else []) for k in ("LOANINT", "MLOANINT", "LN")
        ),
    }


def _phase1_4_regression() -> tuple[bool, list[str]]:
    notes: list[str] = []
    scripts = [
        ("Phase1", PROJECT_ROOT / "tools" / "validators" / "iswl_quikcvs_reconcile.py"),
        ("Phase2", PROJECT_ROOT / "tools" / "validators" / "iswl_quikgps_reconcile.py"),
        ("Phase3", PROJECT_ROOT / "tools" / "validators" / "iswl_quikcoi_reconcile.py"),
        ("Phase4", PROJECT_ROOT / "tools" / "validators" / "iswl_quikgcoi_reconcile.py"),
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
    ap.add_argument("--emit-csv", action="store_true", help="write QuikUint.csv to QLA_Migration/Output/rates")
    args = ap.parse_args()

    cfg = load_config()
    if not cfg.get("iswl_phase5", {}).get("quikuint_enabled"):
        print("FAIL — iswl_phase5.quikuint_enabled is false")
        return 1

    config_path = cfg.get("_config_path", str(R5_DIR / "rate_loader_config.json"))
    repo = str(PROJECT_ROOT)
    out_dir = ensure_phase5_out()
    pipeline_dir = ensure_pipeline_out()

    res = P.run(config_path, repo)
    P.write_issue_reports(res, str(pipeline_dir))

    rows = list(res.quikuint_rows)
    analysis = _analyze_rows(rows)

    psegt_path = resolve_path(cfg, "psegt_csv")
    psgt_path = resolve_path(cfg, "pcovrsgt_csv")
    a1_ok, a1_count = _psegt_interest_gate(psegt_path, psgt_path, "A1")
    g1_ok, g1_count = _psegt_interest_gate(psegt_path, psgt_path, "G1")
    ln_ok, ln_count = _psegt_interest_gate(psegt_path, psgt_path, "LN")

    pdinttbl_path = resolve_path(cfg, "pdinttbl_extract")
    raw_tiers = UINT.load_pdinttbl_tiers(str(pdinttbl_path), ident="CENII", type_code="A1", dint_rules=("0", "3"))
    merged = UINT.union_merge_tiers(raw_tiers, tiebreak_rule="3")

    v01 = _check_schema_fields()
    v02 = len(raw_tiers) == 6 and all(t.ident == "CENII" and t.type_code == "A1" for t in raw_tiers)
    v03 = analysis["schedule_ok"] and len(merged) == EXPECTED_UINT_TIERS_PER_MPLAN
    v04 = analysis["row_count"] == EXPECTED_UINT_ROWS
    v05 = analysis["distinct_mplans"] == 8 and set(analysis["rows_by_mplan"].keys()) == ISWL_UINT_MPLANS
    v06 = analysis["mgt_mcur_mirror"]
    v07 = analysis["percent_literal"]
    v08 = analysis["loan_columns_absent"]
    v09 = analysis["duplicate_index_keys"] == 0

    snapshot = {
        "blocker_count": res.blocker_count,
        "quikuint_rows": analysis["row_count"],
        "rows_by_mplan": analysis["rows_by_mplan"],
        "factor_rows_unchanged": {
            "QuikCvs": len(res.factor_rows.get("QuikCvs", [])),
            "QuikGps": len(res.factor_rows.get("QuikGps", [])),
            "QuikCoi": len(res.factor_rows.get("QuikCoi", [])),
            "QuikGcoi": len(res.factor_rows.get("QuikGcoi", [])),
        },
    }

    ensure_issue32_baselines_out()
    regression_ok = True
    regression_notes: list[str] = []
    if args.write_baseline or not UINT_BASELINE_PATH.is_file():
        UINT_BASELINE_PATH.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        regression_notes.append(f"UINT baseline written: {UINT_BASELINE_PATH}")
    else:
        baseline = json.loads(UINT_BASELINE_PATH.read_text(encoding="utf-8"))
        for k, v in baseline.get("factor_rows_unchanged", {}).items():
            if len(res.factor_rows.get(k, [])) != v:
                regression_ok = False
                regression_notes.append(f"{k} row count changed")

    v10, phase_notes = _phase1_4_regression()
    regression_ok = regression_ok and v10

    if args.emit_csv and v04 and v05 and res.blocker_count == 0:
        from qla_core import rate_dbf_writer as W

        MIGRATION_RATES.parent.mkdir(parents=True, exist_ok=True)
        W.write_quikuint_csv(str(MIGRATION_RATES), rows, overwrite=True)

    summary = {
        "script_version": SCRIPT_VERSION,
        "blocker_count": res.blocker_count,
        "emit_ready": res.emit_ready,
        "v_uint_01_schema": v01,
        "v_uint_02_cenii_a1": v02,
        "v_uint_03_union_merge": v03,
        "v_uint_04_row_count_32": v04,
        "v_uint_05_mplans_8_8": v05,
        "v_uint_06_mirror": v06,
        "v_uint_07_percent_literal": v07,
        "v_uint_08_no_loan": v08,
        "v_uint_09_unique_index": v09,
        "v_uint_10_phase1_4_regression": v10,
        "psegt_a1_gate": {"pass": a1_ok, "count": a1_count},
        "psegt_g1_gate": {"pass": g1_ok, "count": g1_count},
        "psegt_ln_gate": {"pass": ln_ok, "count": ln_count},
        "union_merge_tiers": [
            {"start": t.start_date, "rate": t.declared_rate, "rule": t.dint_rule} for t in merged
        ],
        "analysis": analysis,
        "regression_ok": regression_ok,
        "regression_notes": regression_notes,
        "phase1_4_notes": phase_notes,
        "quikuint_csv": str(MIGRATION_RATES) if MIGRATION_RATES.is_file() else None,
    }
    (out_dir / "iswl_quikuint_reconcile_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")

    with open(out_dir / "iswl_quikuint_rates_by_mplan.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["MPLAN", "MEFFDATE", "MCURRATE", "MGTDRATE"])
        for r in sorted(rows, key=lambda x: (x["MPLAN"], x["MEFFDATE"])):
            w.writerow([r["MPLAN"], r["MEFFDATE"], r["MCURRATE"], r["MGTDRATE"]])

    print("=" * 72)
    print(f"ISWL QUIKUINT RECONCILE v{SCRIPT_VERSION}")
    print(f"Blockers: {res.blocker_count}  emit_ready: {res.emit_ready}")
    print(f"QuikUint rows: {analysis['row_count']} (expect {EXPECTED_UINT_ROWS})")
    for p in sorted(ISWL_UINT_MPLANS):
        print(f"  {p}: {analysis['rows_by_mplan'].get(p, 0)} tiers")
    print(f"V-UINT-01 schema: {'PASS' if v01 else 'FAIL'}")
    print(f"V-UINT-02 CENII/A1: {'PASS' if v02 else 'FAIL'} ({len(raw_tiers)} source tiers)")
    print(f"V-UINT-03 union_merge: {'PASS' if v03 else 'FAIL'}")
    print(f"V-UINT-04 row count 32: {'PASS' if v04 else 'FAIL'}")
    print(f"V-UINT-05 MPLANs 8/8: {'PASS' if v05 else 'FAIL'}")
    print(f"V-UINT-06 MGTDRATE=MCURRATE: {'PASS' if v06 else 'FAIL'}")
    print(f"V-UINT-07 percent literal: {'PASS' if v07 else 'FAIL'}")
    print(f"V-UINT-08 no loan column: {'PASS' if v08 else 'FAIL'}")
    print(f"V-UINT-09 unique index: {'PASS' if v09 else 'FAIL'} (dupes={analysis['duplicate_index_keys']})")
    print(f"V-UINT-10 Phase1-4 regression: {'PASS' if v10 else 'FAIL'}")
    print(f"PSEGT A1/G1/LN: {a1_count}/{g1_count}/{ln_count}/8")
    print("=" * 72)

    errors = []
    if res.blocker_count:
        errors.append("blockers")
    if not v01:
        errors.append("V-UINT-01")
    if not v02:
        errors.append("V-UINT-02")
    if not v03:
        errors.append("V-UINT-03")
    if not v04:
        errors.append("V-UINT-04")
    if not v05:
        errors.append("V-UINT-05")
    if not v06:
        errors.append("V-UINT-06")
    if not v07:
        errors.append("V-UINT-07")
    if not v08:
        errors.append("V-UINT-08")
    if not v09:
        errors.append("V-UINT-09")
    if not v10:
        errors.append("V-UINT-10")
    if not regression_ok:
        errors.append("factor regression")

    if errors:
        print("FAIL —", "; ".join(errors))
        return 1
    print("PASS — ISWL Phase 5 QUIKUINT reconcile")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
