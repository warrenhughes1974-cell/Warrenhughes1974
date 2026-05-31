#!/usr/bin/env python3
"""
Phase 21B — UAT DBF generation from final emitted quikclms/quikclmp CSV only.

Authoritative source: output/quikclms.csv and output/quikclmp.csv after Phase 21 emit.
Does NOT read Phase 10 derivation candidates or Phase 11 prototype populations.
production_dbf_flag=N always.
"""

import argparse
import csv
import json
import logging
import os
import sys

import dbf
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
DEFAULT_RULES = os.path.join(ROOT, "config", "prototype_dbf_generation_rules.json")
DEFAULT_CLMS_DBF = "QUIKCLMS_PHASE19_UAT.DBF"
DEFAULT_CLMP_DBF = "QUIKCLMP_PHASE19_UAT.DBF"
ALIGNMENT_MANIFEST = "claims_uat_dbf_alignment_manifest.csv"
ALIGNMENT_SUMMARY = "claims_uat_dbf_alignment_summary.txt"
GOVERNANCE_POPULATION = "UAT_EMITTED_VALIDATED_ONLY"
RULEBOOK_LINEAGE = "PHASE21B_UAT_DBF_FROM_EMITTED_CSV"

logger = logging.getLogger("uat_emitted_csv_dbf")


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def strip_val(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def parse_date(value):
    s = strip_val(value)
    if not s or s.lower() in {"nan", "none", "null"}:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y%m%d", "%m-%d-%Y"):
        try:
            dt = pd.to_datetime(s, format=fmt)
            return dbf.Date(dt.year, dt.month, dt.day)
        except (ValueError, TypeError):
            continue
    try:
        dt = pd.to_datetime(s)
        return dbf.Date(dt.year, dt.month, dt.day)
    except (ValueError, TypeError):
        return None


def layout_to_dbf_spec(layout):
    parts = []
    for fld in layout:
        name = fld["field"]
        ftype = fld["type"].upper()
        length = int(fld.get("length", 10))
        decimals = int(fld.get("decimals", 0))
        if ftype == "CHARACTER":
            parts.append(f"{name} C({length})")
        elif ftype == "NUMERIC":
            parts.append(f"{name} N({length},{decimals})")
        elif ftype == "DATE":
            parts.append(f"{name} D")
        elif ftype == "LOGICAL":
            parts.append(f"{name} L")
        elif ftype == "MEMO":
            parts.append(f"{name} M")
        else:
            parts.append(f"{name} C({length})")
    return "; ".join(parts)


def truncate_char(value, length):
    s = strip_val(value)
    if not s:
        return None
    return s[:length]


def coerce_numeric(value, default=0.0):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    s = strip_val(value)
    if not s:
        return default
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return default


def coerce_logical(value, default=False):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default if default is not None else None
    if isinstance(value, bool):
        return value
    s = strip_val(value).upper()
    if not s:
        return default if default is not None else None
    if s in {"Y", "YES", "TRUE", "T", "1"}:
        return True
    if s in {"N", "NO", "FALSE", "F", "0"}:
        return False
    return default if default is not None else None


def csv_row_to_dbf_values(row, layout):
    values = []
    for fld in layout:
        name = fld["field"]
        ftype = fld["type"].upper()
        raw = row.get(name, row.get(name.lower(), ""))
        if ftype == "CHARACTER":
            val = truncate_char(raw, int(fld.get("length", 10)))
        elif ftype == "NUMERIC":
            val = coerce_numeric(raw, 0.0)
        elif ftype == "DATE":
            val = parse_date(raw) if strip_val(raw) else None
        elif ftype == "LOGICAL":
            val = coerce_logical(raw, False)
        elif ftype == "MEMO":
            val = strip_val(raw) or None
        else:
            val = truncate_char(raw, int(fld.get("length", 10)))
        values.append(val)
    return tuple(values)


def write_dbf(path, layout, row_values):
    spec = layout_to_dbf_spec(layout)
    if os.path.exists(path):
        os.remove(path)
    table = dbf.Table(path, spec)
    table.open(mode=dbf.READ_WRITE)
    for vals in row_values:
        table.append(vals)
    table.close()
    return len(row_values)


def count_dbf_rows(path):
    if not os.path.isfile(path):
        return None
    try:
        table = dbf.Table(path)
        table.open()
        count = len(table)
        table.close()
        return count
    except Exception as exc:
        logger.warning("Could not count DBF rows for %s: %s", path, exc)
        return None


def load_emit_csv(path, expected_fields):
    df = pd.read_csv(path, dtype=str).fillna("")
    df.columns = [str(c).strip().upper() for c in df.columns]
    missing = [f for f in expected_fields if f not in df.columns]
    if missing:
        raise ValueError(f"CSV missing required columns {missing}: {path}")
    return df


def generate_table_dbf(csv_path, dbf_path, layout, table_label):
    expected = [fld["field"] for fld in layout]
    df = load_emit_csv(csv_path, expected)
    source_count = len(df)
    row_values = []
    for _, series in df.iterrows():
        row_dict = {col: series[col] for col in df.columns}
        row_values.append(csv_row_to_dbf_values(row_dict, layout))
    written = write_dbf(dbf_path, layout, row_values)
    dbf_count = count_dbf_rows(dbf_path)
    if dbf_count is None:
        dbf_count = written
        row_match = "UNKNOWN"
    else:
        row_match = "Y" if dbf_count == source_count else "N"
    logger.info(
        "%s CSV rows=%s DBF rows=%s match=%s -> %s",
        table_label, source_count, dbf_count, row_match, dbf_path,
    )
    print(f"{table_label}_CSV_ROWS: {source_count}")
    print(f"{table_label}_DBF_ROWS: {dbf_count if dbf_count is not None else 'UNKNOWN'}")
    print(f"{table_label}_ROW_MATCH: {row_match}")
    return {
        "source_csv": os.path.abspath(csv_path),
        "source_row_count": source_count,
        "dbf_name": os.path.basename(dbf_path),
        "dbf_path": os.path.abspath(dbf_path),
        "dbf_row_count": dbf_count if dbf_count is not None else "UNKNOWN",
        "row_count_match": row_match,
    }


def write_alignment_manifest(output_dir, rows, run_mode, generation_ts):
    path = os.path.join(output_dir, ALIGNMENT_MANIFEST)
    fieldnames = [
        "source_csv", "source_row_count", "dbf_name", "dbf_row_count", "row_count_match",
        "production_dbf_flag", "governance_population", "deferred_population_included",
        "run_mode", "generation_timestamp", "rulebook_lineage",
    ]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "source_csv": row["source_csv"],
                "source_row_count": row["source_row_count"],
                "dbf_name": row["dbf_name"],
                "dbf_row_count": row["dbf_row_count"],
                "row_count_match": row["row_count_match"],
                "production_dbf_flag": "N",
                "governance_population": GOVERNANCE_POPULATION,
                "deferred_population_included": "N",
                "run_mode": run_mode,
                "generation_timestamp": generation_ts,
                "rulebook_lineage": RULEBOOK_LINEAGE,
            })
    return path


def write_alignment_summary(output_dir, rows, generation_ts):
    path = os.path.join(output_dir, ALIGNMENT_SUMMARY)
    all_match = all(r["row_count_match"] == "Y" for r in rows)
    any_unknown = any(r["row_count_match"] == "UNKNOWN" for r in rows)
    lines = [
        "QLAdmin Enterprise Claims — UAT DBF Alignment Summary (Phase 21B)",
        "=" * 60,
        "",
        "IMPORTANT — UAT REHEARSAL ONLY",
        "-" * 30,
        "These DBF files were generated directly from the final emitted UAT CSV files.",
        "Deferred and governance-hold records were excluded at Phase 21 emit.",
        "This is NOT production cutover and NOT production authorized DBF generation.",
        "production_dbf_flag=N",
        f"governance_population={GOVERNANCE_POPULATION}",
        "deferred_population_included=N",
        "",
        f"Generation timestamp: {generation_ts}",
        f"Rulebook lineage: {RULEBOOK_LINEAGE}",
        "",
        "ROW ALIGNMENT",
        "-" * 30,
    ]
    for row in rows:
        lines.extend([
            f"Source CSV: {row['source_csv']}",
            f"  CSV rows: {row['source_row_count']}",
            f"  DBF file: {row['dbf_name']}",
            f"  DBF rows: {row['dbf_row_count']}",
            f"  Row count match: {row['row_count_match']}",
            "",
        ])
    if all_match:
        lines.append("Overall alignment: PASS — CSV and DBF row counts match.")
    elif any_unknown:
        lines.append("Overall alignment: UNKNOWN — DBF row count could not be verified.")
    else:
        lines.append("Overall alignment: FAIL — CSV and DBF row counts do not match.")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


def main():
    parser = argparse.ArgumentParser(description="Phase 21B UAT DBF from emitted CSV only.")
    parser.add_argument("--clms-csv", required=True)
    parser.add_argument("--clmp-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--rules", default=DEFAULT_RULES)
    parser.add_argument("--run-mode", default="UAT")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    os.makedirs(args.output_dir, exist_ok=True)

    for label, path in (("CLMS CSV", args.clms_csv), ("CLMP CSV", args.clmp_csv), ("Rules", args.rules)):
        if not os.path.isfile(path):
            logger.error("%s not found: %s", label, path)
            return 1

    rules = load_json(args.rules)
    clms_layout = rules["quikclms_layout"]
    clmp_layout = rules["quikclmp_layout"]
    generation_ts = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    clms_dbf = os.path.join(args.output_dir, DEFAULT_CLMS_DBF)
    clmp_dbf = os.path.join(args.output_dir, DEFAULT_CLMP_DBF)

    try:
        clms_result = generate_table_dbf(args.clms_csv, clms_dbf, clms_layout, "QUIKCLMS")
        clmp_result = generate_table_dbf(args.clmp_csv, clmp_dbf, clmp_layout, "QUIKCLMP")
    except Exception as exc:
        logger.error("UAT DBF generation failed: %s", exc)
        print(f"ALIGNMENT_STATUS: FAILED")
        print(f"ERROR: {exc}")
        return 1

    alignment_rows = [clms_result, clmp_result]
    manifest_path = write_alignment_manifest(args.output_dir, alignment_rows, args.run_mode, generation_ts)
    summary_path = write_alignment_summary(args.output_dir, alignment_rows, generation_ts)

    all_match = all(r["row_count_match"] == "Y" for r in alignment_rows)
    any_fail = any(r["row_count_match"] == "N" for r in alignment_rows)
    if any_fail:
        status = "FAILED"
    elif all_match:
        status = "PASS"
    else:
        status = "UNKNOWN"

    print(f"ALIGNMENT_STATUS: {status}")
    print(f"ALIGNMENT_MANIFEST: {os.path.abspath(manifest_path)}")
    print(f"ALIGNMENT_SUMMARY: {os.path.abspath(summary_path)}")
    print("UAT DBF generation from emitted CSV complete.")
    return 0 if status != "FAILED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
