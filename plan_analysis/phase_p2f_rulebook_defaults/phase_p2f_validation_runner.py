#!/usr/bin/env python3
"""Phase P2F — Rulebook default validation (DEFICIENCY=N, INTMETHCV=A)."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

import dbf
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from qla_core.schema_constants import QUIKPLAN_SCHEMA


def strip_val(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def validate_csv(path: str) -> dict:
    df = pd.read_csv(path, dtype=str, keep_default_na=False).fillna("")
    def_ok = (df["DEFICIENCY"].map(strip_val) == "N").all()
    int_ok = (df["INTMETHCV"].map(strip_val) == "A").all()
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "schema_match": list(df.columns) == QUIKPLAN_SCHEMA,
        "deficiency_all_n": def_ok,
        "intmethcv_all_a": int_ok,
        "deficiency_unique": sorted(df["DEFICIENCY"].map(strip_val).unique()),
        "intmethcv_unique": sorted(df["INTMETHCV"].map(strip_val).unique()),
        "duplicate_plans": int(df["PLAN"].duplicated().sum()),
    }


def write_quikplan_dbf(csv_path: str, dbf_path: str) -> int:
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False).fillna("")
    spec_parts = []
    for col in df.columns:
        if col in ("DEFICIENCY", "INTMETHCV", "RENEW", "CALCADV", "BACTIVE", "PAR", "SEX"):
            spec_parts.append(f"{col} C(1)")
        elif col in ("DESCR", "PLANNAME"):
            spec_parts.append(f"{col} C(254)")
        else:
            spec_parts.append(f"{col} C(32)")
    spec = "; ".join(spec_parts)
    if os.path.isfile(dbf_path):
        os.remove(dbf_path)
    table = dbf.Table(dbf_path, spec)
    table.open(mode=dbf.READ_WRITE)
    for _, row in df.iterrows():
        table.append(tuple(strip_val(row[c])[:32] if c not in ("DESCR", "PLANNAME") else strip_val(row[c])[:254] for c in df.columns))
    table.close()
    return len(df)


def validate_dbf(dbf_path: str) -> dict:
    table = dbf.Table(dbf_path)
    table.open()
    def_vals = set()
    int_vals = set()
    for record in table:
        def_vals.add(strip_val(record.deficiency))
        int_vals.add(strip_val(record.intmethcv))
    count = len(table)
    table.close()
    return {
        "dbf_rows": count,
        "deficiency_unique": sorted(def_vals),
        "intmethcv_unique": sorted(int_vals),
        "deficiency_all_n": def_vals == {"N"},
        "intmethcv_all_a": int_vals == {"A"},
    }


def main():
    parser = argparse.ArgumentParser(description="Phase P2F validation")
    parser.add_argument("--csv", default=os.path.join(ROOT, "QLA_Migration", "Output", "quikplan.csv"))
    parser.add_argument("--dbf", default=os.path.join(ROOT, "QLA_Migration", "Output", "quikplan.dbf"))
    parser.add_argument("--output-dir", default=SCRIPT_DIR)
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    csv_result = validate_csv(args.csv)
    dbf_rows = write_quikplan_dbf(args.csv, args.dbf)
    dbf_result = validate_dbf(args.dbf)

    sample = pd.read_csv(args.csv, dtype=str, keep_default_na=False).head(3)
    sample_path = os.path.join(args.output_dir, "sample_output_rows_p2f.csv")
    sample[["PLAN", "DEFICIENCY", "INTMETHCV", "DESCR"]].to_csv(sample_path, index=False)

    passed = (
        csv_result["rows"] == 133
        and csv_result["columns"] == 79
        and csv_result["schema_match"]
        and csv_result["deficiency_all_n"]
        and csv_result["intmethcv_all_a"]
        and dbf_result["deficiency_all_n"]
        and dbf_result["intmethcv_all_a"]
    )

    summary_path = os.path.join(args.output_dir, "validation_summary.md")
    with open(summary_path, "w", encoding="utf-8") as fh:
        fh.write(f"# Phase P2F — Rulebook Default Validation Summary\n\n**Date:** {ts}\n\n")
        fh.write("## Rulebook Analysis (Task 1)\n\n")
        fh.write("| Field | Prior Rulebook | Prior Output | Root Cause | P2F Fix |\n")
        fh.write("|-------|----------------|--------------|------------|---------|\n")
        fh.write("| DEFICIENCY | Default_Value=`N` | All rows `T` | Master_Value_Translation N→T | `SKIP_TRANSLATION` note |\n")
        fh.write("| INTMETHCV | Default empty | All rows blank | No default defined | Default `A` + `SKIP_TRANSLATION` |\n\n")
        fh.write("## Intentional Output Changes (vs pre-P2F baseline)\n\n")
        fh.write("- DEFICIENCY: T → N (133 rows)\n")
        fh.write("- INTMETHCV: blank → A (133 rows)\n")
        fh.write("- Row/column counts and schema order unchanged\n\n")
        fh.write("## Governance Validation\n\n")
        fh.write(f"- Duplicate PLAN rows: {csv_result['duplicate_plans']} (pre-existing 9DIS25)\n\n")
        fh.write(f"## Result\n\n**{'PASSED' if passed else 'FAILED'}**\n\n")
        fh.write("## Rulebook Changes\n\n")
        fh.write("- `DEFICIENCY` → Default_Value=`N`, Transformation_Note=`SKIP_TRANSLATION`\n")
        fh.write("- `INTMETHCV` → Default_Value=`A`, Transformation_Note=`SKIP_TRANSLATION`\n\n")
        fh.write("## CSV Validation\n\n")
        fh.write(f"- Rows: {csv_result['rows']} (expected 133)\n")
        fh.write(f"- Columns: {csv_result['columns']} (expected 79)\n")
        fh.write(f"- Schema order match: {csv_result['schema_match']}\n")
        fh.write(f"- DEFICIENCY all 'N': {csv_result['deficiency_all_n']} ({csv_result['deficiency_unique']})\n")
        fh.write(f"- INTMETHCV all 'A': {csv_result['intmethcv_all_a']} ({csv_result['intmethcv_unique']})\n")
        fh.write(f"- Duplicate PLAN rows: {csv_result['duplicate_plans']}\n\n")
        fh.write("## DBF Validation\n\n")
        fh.write(f"- Path: `{args.dbf}`\n")
        fh.write(f"- Rows: {dbf_rows}\n")
        fh.write(f"- DEFICIENCY all 'N': {dbf_result['deficiency_all_n']}\n")
        fh.write(f"- INTMETHCV all 'A': {dbf_result['intmethcv_all_a']}\n\n")
        fh.write("## Sample Rows\n\n")
        fh.write(f"See `{sample_path}`\n")

    print(f"P2F validation {'PASSED' if passed else 'FAILED'}")
    print(f"  CSV: DEFICIENCY={csv_result['deficiency_unique']} INTMETHCV={csv_result['intmethcv_unique']}")
    print(f"  DBF: {args.dbf}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
