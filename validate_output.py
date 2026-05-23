#!/usr/bin/env python3
"""
Lightweight post-conversion validator for QLAdmin migration output CSVs.

Reports:
  - blank MRIDRID values (quikridr)
  - missing MPHASE values (quikridr, quikclid)
  - invalid dates (non-empty values that fail QLA date rules)

Does not modify conversion output or app.py logic.
"""

import argparse
import csv
import os
import re
import sys
from datetime import datetime


MIN_DATE = "19000101"
BLANK_TOKENS = {"", "NAN", "NONE", "NULL", "NA", "N/A"}
MPHASE_TABLES = ("quikridr.csv", "quikclid.csv")
MRIDRID_TABLE = "quikridr.csv"
SAMPLE_LIMIT = 10


def normalize(val):
    if val is None:
        return ""
    s = str(val).strip().upper()
    if s.endswith(".0"):
        s = s[:-2]
    return s


def is_blank(val):
    return normalize(val) in BLANK_TOKENS


def is_missing_mphase(val):
    n = normalize(val)
    return n in BLANK_TOKENS or n == "0"


def is_date_column(name):
    n = name.upper().strip()
    if n == "MPHASE":
        return False
    if n in ("MBILLDAY", "MBLLDOM", "MORGBLLDOM", "MLOCKTYP"):
        return False
    if "DATE" in n or "DOB" in n:
        return True
    if n.endswith("DT"):
        return True
    if n in ("MPAIDTO", "MBILLTO", "MLASTANN"):
        return True
    return False


def validate_date_value(val):
    """
    Return None if blank (skip), True if valid, or an error reason string.
    Aligns with app.py MDOB / MINTDATE digit sanitization expectations.
    """
    if is_blank(val):
        return None

    raw = str(val).strip()
    digits = re.sub(r"[^0-9]", "", raw)

    if len(digits) == 8:
        if digits < MIN_DATE:
            return f"before {MIN_DATE}"
        try:
            datetime.strptime(digits, "%Y%m%d")
            return True
        except ValueError:
            return "invalid YYYYMMDD calendar date"

    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            parsed = datetime.strptime(raw, fmt)
            if parsed.strftime("%Y%m%d") < MIN_DATE:
                return f"before {MIN_DATE}"
            return True
        except ValueError:
            continue

    return f"unrecognized date format ({raw!r})"


def read_csv_rows(path):
    with open(path, newline="", encoding="latin1") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return [], []
        fieldnames = [str(c).strip() for c in reader.fieldnames]
        reader.fieldnames = fieldnames
        rows = list(reader)
    return fieldnames, rows


def validate_file(path, sample_limit=SAMPLE_LIMIT):
    filename = os.path.basename(path).lower()
    fieldnames, rows = read_csv_rows(path)
    findings = {
        "file": filename,
        "path": path,
        "row_count": len(rows),
        "blank_mridrid": [],
        "missing_mphase": [],
        "invalid_dates": [],
    }

    if not rows:
        return findings

    upper_fields = {f.upper(): f for f in fieldnames}

    if filename == MRIDRID_TABLE and "MRIDRID" in upper_fields:
        col = upper_fields["MRIDRID"]
        for idx, row in enumerate(rows, start=2):
            if is_blank(row.get(col)):
                findings["blank_mridrid"].append(
                    {"row": idx, "MPOLICY": row.get(upper_fields.get("MPOLICY", "MPOLICY"), "")}
                )

    if filename in MPHASE_TABLES and "MPHASE" in upper_fields:
        col = upper_fields["MPHASE"]
        pol_col = upper_fields.get("MPOLICY")
        for idx, row in enumerate(rows, start=2):
            if is_missing_mphase(row.get(col)):
                entry = {"row": idx, "MPHASE": row.get(col, "")}
                if pol_col:
                    entry["MPOLICY"] = row.get(pol_col, "")
                if filename == "quikclid.csv" and "MRELATION" in upper_fields:
                    entry["MRELATION"] = row.get(upper_fields["MRELATION"], "")
                findings["missing_mphase"].append(entry)

    date_cols = [f for f in fieldnames if is_date_column(f)]
    for col in date_cols:
        for idx, row in enumerate(rows, start=2):
            val = row.get(col, "")
            result = validate_date_value(val)
            if result is not True and result is not None:
                findings["invalid_dates"].append(
                    {"row": idx, "field": col, "value": val, "reason": result}
                )

    for key in ("blank_mridrid", "missing_mphase", "invalid_dates"):
        findings[f"{key}_count"] = len(findings[key])
        if len(findings[key]) > sample_limit:
            findings[key] = findings[key][:sample_limit]
            findings[f"{key}_truncated"] = True

    return findings


def scan_directory(output_dir):
    if not os.path.isdir(output_dir):
        raise FileNotFoundError(f"Output directory not found: {output_dir}")

    csv_files = sorted(
        os.path.join(output_dir, f)
        for f in os.listdir(output_dir)
        if f.lower().endswith(".csv") and f.lower().startswith("quik")
    )
    return [validate_file(path) for path in csv_files]


def format_report(results, output_dir):
    lines = [
        "=== QLAdmin Output Validation Report ===",
        f"Directory: {os.path.abspath(output_dir)}",
        "",
    ]

    total_mridrid = 0
    total_mphase = 0
    total_dates = 0
    files_with_issues = 0

    for r in results:
        issue_count = (
            r.get("blank_mridrid_count", 0)
            + r.get("missing_mphase_count", 0)
            + r.get("invalid_dates_count", 0)
        )
        if issue_count == 0:
            continue

        files_with_issues += 1
        total_mridrid += r.get("blank_mridrid_count", 0)
        total_mphase += r.get("missing_mphase_count", 0)
        total_dates += r.get("invalid_dates_count", 0)

        lines.append(f"--- {r['file']} ({r['row_count']} rows) ---")

        if r.get("blank_mridrid_count", 0):
            lines.append(f"  Blank MRIDRID: {r['blank_mridrid_count']}")
            for item in r["blank_mridrid"]:
                lines.append(f"    row {item['row']}  MPOLICY={item.get('MPOLICY', '')!r}")
            if r.get("blank_mridrid_truncated"):
                lines.append(f"    ... showing first {SAMPLE_LIMIT} of {r['blank_mridrid_count']}")

        if r.get("missing_mphase_count", 0):
            lines.append(f"  Missing MPHASE: {r['missing_mphase_count']}")
            for item in r["missing_mphase"]:
                extra = "  ".join(f"{k}={v!r}" for k, v in item.items() if k != "row")
                lines.append(f"    row {item['row']}  {extra}")
            if r.get("missing_mphase_truncated"):
                lines.append(f"    ... showing first {SAMPLE_LIMIT} of {r['missing_mphase_count']}")

        if r.get("invalid_dates_count", 0):
            lines.append(f"  Invalid dates: {r['invalid_dates_count']}")
            for item in r["invalid_dates"]:
                lines.append(
                    f"    row {item['row']}  {item['field']}={item['value']!r}  ({item['reason']})"
                )
            if r.get("invalid_dates_truncated"):
                lines.append(f"    ... showing first {SAMPLE_LIMIT} of {r['invalid_dates_count']}")

        lines.append("")

    lines.extend(
        [
            "=== Summary ===",
            f"Files scanned: {len(results)}",
            f"Files with issues: {files_with_issues}",
            f"Blank MRIDRID total: {total_mridrid}",
            f"Missing MPHASE total: {total_mphase}",
            f"Invalid date total: {total_dates}",
        ]
    )

    if files_with_issues == 0:
        lines.append("Status: PASS (no issues detected)")
    else:
        lines.append("Status: FAIL (see findings above)")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Validate QLAdmin migration output CSVs for MRIDRID, MPHASE, and date integrity."
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        default=".",
        help="Directory containing converted quik*.csv files (default: current directory)",
    )
    parser.add_argument(
        "-o", "--report",
        help="Optional path to write the validation report as a text file",
    )
    args = parser.parse_args()

    output_dir = os.path.abspath(args.output_dir)
    try:
        results = scan_directory(output_dir)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not results:
        print(f"No CSV files found in: {output_dir}")
        return 0

    report = format_report(results, output_dir)
    print(report)

    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"\nReport saved: {args.report}")

    has_issues = any(
        r.get("blank_mridrid_count", 0)
        + r.get("missing_mphase_count", 0)
        + r.get("invalid_dates_count", 0)
        for r in results
    )
    return 1 if has_issues else 0


if __name__ == "__main__":
    sys.exit(main())
