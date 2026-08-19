"""Issue 141 validator: quikspec.RESRVCAT from PCOVR.PRODUCT_TYPE via PPBEN seq-1.

Read-only against QLA_Migration/Output/. Exit 0 on PASS.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qla_core.normalize_utils import normalize  # noqa: E402
from qla_core.quikspec_resrvcat import (  # noqa: E402
    RESRVCAT_FIELD,
    apply_quikspec_resrvcat,
    load_pcovr_product_types,
    load_ppben_seq1_plans,
)

OUT = ROOT / "QLA_Migration" / "Output"
SRC = ROOT / "QLA_Migration" / "Source"
SPEC = OUT / "quikspec.csv"
PLAN = OUT / "quikplan.csv"
TV = OUT / "Test_Validation"
SCHEMA = ("MPOLICY", "VANISH", "VANISHDT", "RESSTATE", "RESRVCAT")
TRACES = {
    "9010143726C": "03",
    "9010148272C": "03",
    "9010713704C": "05",
}
ISWL_PLANS = ("1658C1", "1658CS", "1659C2", "1659CS", "1659CR", "1659SR", "1669SR", "1679CS")


def _norm_pol(val: str) -> str:
    return str(val or "").strip().upper()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish-test-validation", action="store_true")
    args = parser.parse_args()

    failures: list[str] = []
    summary = {
        "rows": 0,
        "filled": 0,
        "blank": 0,
        "iswlfe_on_resrvcat": 0,
        "join_mismatches": 0,
        "traces": {},
    }

    if not SPEC.is_file():
        print(f"FAIL: missing {SPEC}")
        return 1
    qs = pd.read_csv(SPEC, dtype=str).fillna("")
    qs.columns = [str(c).strip().upper() for c in qs.columns]
    missing = [c for c in SCHEMA if c not in qs.columns]
    if missing:
        failures.append(f"quikspec missing columns: {missing}")
    else:
        cols = [c for c in qs.columns if c in SCHEMA]
        if cols[:5] != list(SCHEMA):
            # Allow extra columns after RESRVCAT; require the first five in order.
            first = [c for c in qs.columns if c in SCHEMA]
            if first != list(SCHEMA):
                failures.append(f"schema order {first} != {list(SCHEMA)}")

    summary["rows"] = len(qs)
    if RESRVCAT_FIELD in qs.columns:
        vals = qs[RESRVCAT_FIELD].astype(str).map(lambda x: str(x).strip())
        summary["filled"] = int((vals != "").sum())
        summary["blank"] = int((vals == "").sum())
        summary["iswlfe_on_resrvcat"] = int(vals.str.upper().eq("ISWLFE").sum())
        if summary["iswlfe_on_resrvcat"]:
            failures.append(f"RESRVCAT=ISWLFE rows={summary['iswlfe_on_resrvcat']}")

    cov_pt = load_pcovr_product_types(str(SRC))
    seq1 = load_ppben_seq1_plans(str(SRC))
    if "MPOLICY" in qs.columns and RESRVCAT_FIELD in qs.columns:
        mismatches = 0
        for _, row in qs.iterrows():
            pol = str(row.get("MPOLICY", "")).strip()
            got = str(row.get(RESRVCAT_FIELD, "") or "").strip()
            plan = seq1.get(pol, "")
            exp = cov_pt.get(plan, "") if plan else ""
            if got != exp:
                mismatches += 1
        summary["join_mismatches"] = mismatches
        if mismatches:
            failures.append(f"RESRVCAT join mismatches={mismatches}")

    spec_by_pol = {}
    if "MPOLICY" in qs.columns:
        for _, row in qs.iterrows():
            spec_by_pol[_norm_pol(row.get("MPOLICY", ""))] = row
    for pol, exp in TRACES.items():
        row = spec_by_pol.get(_norm_pol(pol), {})
        got = str(row.get(RESRVCAT_FIELD, "") or "").strip() if len(row) else ""
        vanish = str(row.get("VANISH", "") or "").strip() if len(row) else ""
        summary["traces"][pol] = {"resrvcat": got, "vanish": vanish, "expected": exp}
        if got != exp:
            failures.append(f"trace {pol} RESRVCAT={got!r} expected {exp!r}")

    if PLAN.is_file():
        qp = pd.read_csv(PLAN, dtype=str).fillna("")
        qp.columns = [str(c).strip().upper() for c in qp.columns]
        by_plan = {normalize(r.get("PLAN", "")): r for _, r in qp.iterrows()}
        for plan in ISWL_PLANS:
            row = by_plan.get(normalize(plan), {})
            if not len(row):
                continue
            for fld in ("HLOB", "PRODUCT", "MKTG"):
                if fld in row and normalize(row.get(fld, "")) != "ISWLFE":
                    failures.append(f"quikplan {plan} {fld}={row.get(fld)!r} expected ISWLFE")

    expected_df, exp_stats = apply_quikspec_resrvcat(qs.copy(), str(SRC))
    summary["expected_filled"] = exp_stats.get("filled")
    if RESRVCAT_FIELD in qs.columns and RESRVCAT_FIELD in expected_df.columns:
        if not qs[RESRVCAT_FIELD].fillna("").astype(str).str.strip().equals(
            expected_df[RESRVCAT_FIELD].fillna("").astype(str).str.strip()
        ):
            failures.append("Output RESRVCAT does not match live source enricher")

    print("| Issue 141 RESRVCAT              | Result    |")
    print("| ------------------------------- | --------- |")
    print(f"| Rows                            | {summary['rows']:<9} |")
    print(f"| Filled                          | {summary['filled']:<9} |")
    print(f"| Blank                           | {summary['blank']:<9} |")
    print(f"| Join mismatches                 | {summary['join_mismatches']:<9} |")
    print(f"| ISWLFE on RESRVCAT              | {summary['iswlfe_on_resrvcat']:<9} |")
    for pol, info in summary["traces"].items():
        print(f"| {pol}                   | {info['resrvcat']:<9} |")

    if failures:
        for f in failures[:20]:
            print(f"FAIL detail: {f}")
        print("FAIL: Issue 141 RESRVCAT")
        return 1

    if args.publish_test_validation:
        TV.mkdir(parents=True, exist_ok=True)
        dest = TV / "quikspec.csv"
        shutil.copy2(SPEC, dest)
        print(f"OK: published quikspec.csv to {dest}")

    ev = ROOT / "Issue_Log_Items" / "Issue_141" / "evidence"
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "issue141_validation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(
        "PASS: Issue 141 RESRVCAT — "
        f"rows={summary['rows']} filled={summary['filled']} mismatches=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
