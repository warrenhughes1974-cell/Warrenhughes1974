"""
ISWL Phase 1 — QUIKCVS reconcile: pipeline dry-run, CSO crosswalk, regression baseline.

Checks: V-CVS-02, V-CVS-03, V-CVS-04, V-X-01, V-X-03

Usage:
  python tools/validators/iswl_quikcvs_reconcile.py
  python tools/validators/iswl_quikcvs_reconcile.py --write-baseline
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from qla_core import rate_dbf_schema as S
from qla_core import rate_pipeline as P
from qla_core.cso_mortality_crosswalk import (
    CV_ASSUMPTION_FIELDS,
    ISWL_MPLAN_ALLOWLIST,
    load_cso_mortality_crosswalk,
    default_crosswalk_path,
)
from qla_core.rate_factor_loader import quikcvs_keys_by_plan
from tools.validators.iswl_common import (
    BASELINE_PATH,
    ISWL_COVERAGE_IDS,
    ensure_phase1_out,
    ensure_pipeline_out,
    load_config,
    resolve_path,
)

SCRIPT_VERSION = "1.0"
R5_DIR = PROJECT_ROOT / "plan_analysis" / "phase_r5_rate_loader"


def _count_rate_table_cv(path: Path) -> dict[str, int]:
    counts = {c: 0 for c in ISWL_COVERAGE_IDS}
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f)
        next(rd, None)
        for row in rd:
            if len(row) < 2:
                continue
            cov = row[0].strip()
            typ = row[1].strip()
            if typ == "CV" and cov in counts:
                counts[cov] += 1
    return counts


def _cso_check(repo_root: str) -> tuple[bool, list[str]]:
    path = default_crosswalk_path(repo_root)
    resolver = load_cso_mortality_crosswalk(path)
    failures = []
    for plan in sorted(ISWL_MPLAN_ALLOWLIST):
        res = resolver.resolve(plan)
        if not res.get("matched"):
            failures.append(f"{plan}: not in crosswalk")
            continue
        for fld in CV_ASSUMPTION_FIELDS:
            if fld in ("ETIMORT",) and res.get(fld) == "":
                continue  # blank ETI allowed
            if not str(res.get(fld, "")).strip():
                failures.append(f"{plan}: blank {fld}")
    return len(failures) == 0, failures


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-baseline", action="store_true",
                    help="Write regression baseline JSON (first-time capture)")
    args = ap.parse_args()

    cfg = load_config()
    config_path = cfg.get("_config_path", str(R5_DIR / "rate_loader_config.json"))
    repo = str(PROJECT_ROOT)
    out_dir = ensure_phase1_out()
    pipeline_dir = ensure_pipeline_out()

    res = P.run(config_path, repo)
    P.write_issue_reports(res, str(pipeline_dir))

    grid = res.grids.get("QuikCvs", {})
    keys_by_plan = quikcvs_keys_by_plan(grid)
    iswl_plans = sorted(ISWL_MPLAN_ALLOWLIST)

    v03 = [i for i in res.issues if i.get("id") == "V03"]
    effdate_issues = [
        i for i in res.issues
        if i.get("id") == "V07" or "EFFDATE" in str(i.get("detail", ""))
    ]

    rt_counts = _count_rate_table_cv(resolve_path(cfg, "source_rate_extract"))
    rt_missing = [c for c, n in rt_counts.items() if n == 0]

    cso_ok, cso_fail = _cso_check(repo)

    iswl_key_report = {p: keys_by_plan.get(p, 0) for p in iswl_plans}
    missing_plans = [p for p in iswl_plans if keys_by_plan.get(p, 0) == 0]

    all_plans = sorted(keys_by_plan.keys())
    snapshot = {
        "blocker_count": res.blocker_count,
        "quikcvs_total_plans": len(all_plans),
        "quikcvs_keys_by_plan": keys_by_plan,
        "iswl_keys_by_plan": iswl_key_report,
    }

    regression_ok = True
    regression_notes = []
    if args.write_baseline or not BASELINE_PATH.is_file():
        BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        BASELINE_PATH.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        regression_notes.append(f"Baseline written: {BASELINE_PATH}")
    else:
        baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        if baseline.get("blocker_count") != res.blocker_count:
            regression_ok = False
            regression_notes.append(
                f"blocker_count changed: {baseline.get('blocker_count')} -> {res.blocker_count}"
            )
        for plan, cnt in baseline.get("quikcvs_keys_by_plan", {}).items():
            if plan not in ISWL_MPLAN_ALLOWLIST and keys_by_plan.get(plan, 0) != cnt:
                regression_ok = False
                regression_notes.append(
                    f"non-ISWL plan {plan}: {cnt} -> {keys_by_plan.get(plan, 0)} keys"
                )

    summary_path = out_dir / "iswl_quikcvs_reconcile_summary.json"
    summary_path.write_text(json.dumps({
        "script_version": SCRIPT_VERSION,
        "blocker_count": res.blocker_count,
        "emit_ready": res.emit_ready,
        "v03_collisions": len(v03),
        "iswl_quikcvs_keys_by_plan": iswl_key_report,
        "rate_table_cv_rows_by_coverage": rt_counts,
        "cso_crosswalk_ok": cso_ok,
        "cso_failures": cso_fail,
        "effdate_blockers": len(effdate_issues),
        "regression_ok": regression_ok,
        "regression_notes": regression_notes,
    }, indent=2), encoding="utf-8")

    with open(out_dir / "iswl_quikcvs_keys_by_mplan.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["MPLAN", "QUIKCVS_DISTINCT_KEYS"])
        for p in iswl_plans:
            w.writerow([p, keys_by_plan.get(p, 0)])

    print("=" * 72)
    print(f"ISWL QUIKCVS RECONCILE v{SCRIPT_VERSION}")
    print(f"Config: {config_path}")
    print(f"Blockers: {res.blocker_count}  V03 collisions: {len(v03)}  emit_ready: {res.emit_ready}")
    print("\nISWL QuikCvs distinct keys by MPLAN:")
    for p in iswl_plans:
        print(f"  {p}: {keys_by_plan.get(p, 0)}")
    print(f"\nV-CVS-02 Rate_Table CV rows — missing coverages: {rt_missing or 'none'}")
    print(f"V-CVS-04 CSO crosswalk: {'PASS' if cso_ok else 'FAIL'}")
    if cso_fail:
        for x in cso_fail:
            print(f"  {x}")
    print(f"V-X-03 QuikPlNb EFFDATE blockers: {len(effdate_issues)} (expect 0)")
    print(f"V-X-01 Regression: {'PASS' if regression_ok else 'FAIL'}")
    for n in regression_notes:
        print(f"  {n}")
    print(f"\nPipeline artifacts: {pipeline_dir}")
    print(f"Summary: {summary_path}")
    print("=" * 72)

    errors = []
    if res.blocker_count:
        errors.append("pipeline blockers")
    if v03:
        errors.append("V03 grid collisions")
    if missing_plans:
        errors.append(f"missing ISWL plans: {missing_plans}")
    if rt_missing:
        errors.append(f"Rate_Table CV missing: {rt_missing}")
    if not cso_ok:
        errors.append("CSO crosswalk")
    if effdate_issues:
        errors.append("EFFDATE gate")
    if not regression_ok:
        errors.append("regression")

    if errors:
        print("FAIL —", "; ".join(errors))
        return 1
    print("PASS — ISWL Phase 1 QUIKCVS reconcile")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
