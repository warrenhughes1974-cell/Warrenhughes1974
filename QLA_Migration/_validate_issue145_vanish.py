"""Issue 145 validator: quikspec.VANISH T iff PPOLC BILLING_REASON=VB.

Read-only against QLA_Migration/Output/. Exit 1 on FAIL.
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

from qla_core.quikspec_vanish import (  # noqa: E402
    VANISH_FALSE,
    VANISH_FIELD,
    VANISH_TRUE,
    apply_quikspec_vanish,
)

OUT = ROOT / "QLA_Migration" / "Output"
SRC = ROOT / "QLA_Migration" / "Source"
SPEC = OUT / "quikspec.csv"
TV = OUT / "Test_Validation"
SCHEMA = ("MPOLICY", "VANISH", "VANISHDT", "RESSTATE", "RESRVCAT")
TRUE_TRACES = ("9010815236C", "9011050114C", "9011069610C")
FALSE_TRACES = ("9010761639C", "9010760840C")
RESRVCAT_TRACES = {
    "9010143726C": "03",
    "9010148272C": "03",
    "9010713704C": "05",
}


def _n(val: str) -> str:
    return str(val or "").strip().upper()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish-test-validation", action="store_true")
    args = parser.parse_args()

    failures: list[str] = []
    summary: dict = {
        "rows": 0,
        "vanish_t": 0,
        "vanish_f": 0,
        "vanishdt_filled": 0,
        "missing": 0,
        "traces": {},
    }

    if not SPEC.is_file():
        print(f"FAIL: missing {SPEC}")
        return 1
    qs = pd.read_csv(SPEC, dtype=str).fillna("")
    qs.columns = [str(c).strip().upper() for c in qs.columns]
    missing_cols = [c for c in SCHEMA if c not in qs.columns]
    if missing_cols:
        failures.append(f"quikspec missing columns: {missing_cols}")
    else:
        first = [c for c in qs.columns if c in SCHEMA]
        if first != list(SCHEMA):
            failures.append(f"schema order {first} != {list(SCHEMA)}")

    summary["rows"] = len(qs)
    if VANISH_FIELD in qs.columns:
        vals = qs[VANISH_FIELD].astype(str).map(lambda x: str(x).strip().upper())
        summary["vanish_t"] = int(vals.eq(VANISH_TRUE).sum())
        summary["vanish_f"] = int(vals.eq(VANISH_FALSE).sum())
        other = int((~vals.isin([VANISH_TRUE, VANISH_FALSE])).sum())
        if other:
            failures.append(f"VANISH values other than T/F = {other}")
        if summary["rows"] >= 4000 and summary["vanish_t"] == 0:
            failures.append("VANISH T count is 0 on a full quikspec — Issue 145 dropped")

    if "VANISHDT" in qs.columns:
        dt = qs["VANISHDT"].astype(str).map(lambda x: str(x).strip())
        summary["vanishdt_filled"] = int((dt != "").sum())
        if summary["vanishdt_filled"]:
            failures.append(f"VANISHDT populated on {summary['vanishdt_filled']} rows (must be blank)")

    expected_df, stats = apply_quikspec_vanish(qs.copy(), str(SRC))
    summary["expected_t"] = stats.get("true")
    summary["vb_source"] = stats.get("vb_source")
    summary["missing"] = stats.get("missing")
    if VANISH_FIELD in qs.columns and VANISH_FIELD in expected_df.columns:
        got = qs[VANISH_FIELD].fillna("").astype(str).str.strip().str.upper()
        exp = expected_df[VANISH_FIELD].fillna("").astype(str).str.strip().str.upper()
        mismatches = int((got != exp).sum())
        summary["vanish_mismatches"] = mismatches
        if mismatches:
            failures.append(f"VANISH mismatches vs PPOLC VB = {mismatches}")
    if stats.get("true") != summary.get("vanish_t"):
        failures.append(
            f"Output VANISH T={summary.get('vanish_t')} expected {stats.get('true')}"
        )
    if int(stats.get("missing") or 0):
        failures.append(f"QuikSpec rows with no PPOLC join = {stats.get('missing')}")

    for col in ("RESSTATE", "RESRVCAT"):
        if col in qs.columns and col in expected_df.columns:
            if not qs[col].fillna("").astype(str).str.strip().equals(
                expected_df[col].fillna("").astype(str).str.strip()
            ):
                failures.append(f"{col} changed by vanish enricher (must be untouched)")

    by_pol = {}
    if "MPOLICY" in qs.columns:
        for _, row in qs.iterrows():
            by_pol[_n(row.get("MPOLICY", ""))] = row

    for pol in TRUE_TRACES:
        row = by_pol.get(_n(pol), {})
        got = str(row.get(VANISH_FIELD, "") or "").strip().upper() if len(row) else ""
        summary["traces"][pol] = got
        if got != VANISH_TRUE:
            failures.append(f"trace {pol} VANISH={got!r} expected T")
    for pol in FALSE_TRACES:
        row = by_pol.get(_n(pol), {})
        got = str(row.get(VANISH_FIELD, "") or "").strip().upper() if len(row) else ""
        summary["traces"][pol] = got
        if got != VANISH_FALSE:
            failures.append(f"trace {pol} VANISH={got!r} expected F")
    for pol, exp in RESRVCAT_TRACES.items():
        row = by_pol.get(_n(pol), {})
        got = str(row.get("RESRVCAT", "") or "").strip() if len(row) else ""
        if got != exp:
            failures.append(f"#141 trace {pol} RESRVCAT={got!r} expected {exp!r}")

    print("| Issue 145 VANISH                 | Result    |")
    print("| -------------------------------- | --------- |")
    print(f"| Rows                             | {summary['rows']:<9} |")
    print(f"| VANISH T                         | {summary['vanish_t']:<9} |")
    print(f"| VANISH F                         | {summary['vanish_f']:<9} |")
    print(f"| VANISHDT filled                  | {summary['vanishdt_filled']:<9} |")
    for pol in list(TRUE_TRACES) + list(FALSE_TRACES):
        print(f"| {pol}                    | {summary['traces'].get(pol, ''):<9} |")

    if failures:
        for f in failures[:20]:
            print(f"FAIL detail: {f}")
        print("FAIL: Issue 145 VANISH")
        return 1

    if args.publish_test_validation:
        TV.mkdir(parents=True, exist_ok=True)
        dest = TV / "quikspec.csv"
        shutil.copy2(SPEC, dest)
        print(f"OK: published quikspec.csv to {dest}")

    ev = ROOT / "Issue_Log_Items" / "Issue_145" / "evidence"
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "issue145_validation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(
        "PASS: Issue 145 VANISH — "
        f"rows={summary['rows']} T={summary['vanish_t']} F={summary['vanish_f']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
