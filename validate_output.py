#!/usr/bin/env python3
"""
Enterprise post-conversion validator for QLAdmin migration output CSVs.

Isolated read-only utility — does not import or modify app.py.

Validation categories:
  1. Schema validation (column presence, order, extras)
  2. Blank critical field detection (config-driven)
  3. Invalid date detection
  4. Duplicate key detection
  5. Regression comparison (optional baseline)

Configuration: validation_config/*.json (override with --config-dir)
"""

import argparse
import csv
import json
import logging
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_DATE = "19000101"
BLANK_TOKENS = {"", "NAN", "NONE", "NULL", "NA", "N/A"}
DEFAULT_SAMPLE_LIMIT = 10
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_DIR = os.path.join(SCRIPT_DIR, "validation_config")

CATEGORIES = ("schema", "critical", "dates", "duplicates", "regression")

logger = logging.getLogger("validate_output")


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_json_config(path, label):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing {label} config: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_all_config(config_dir):
    return {
        "schema": load_json_config(os.path.join(config_dir, "schema_manifest.json"), "schema"),
        "critical": load_json_config(os.path.join(config_dir, "critical_fields.json"), "critical fields"),
        "dates": load_json_config(os.path.join(config_dir, "date_fields.json"), "date fields"),
        "keys": load_json_config(os.path.join(config_dir, "key_definitions.json"), "key definitions"),
    }


# ---------------------------------------------------------------------------
# Core I/O helpers
# ---------------------------------------------------------------------------

def normalize(val):
    if val is None:
        return ""
    s = str(val).strip().upper()
    if s.endswith(".0"):
        s = s[:-2]
    return s


def is_blank(val, extra_blank=None):
    tokens = BLANK_TOKENS if not extra_blank else BLANK_TOKENS | {normalize(v) for v in extra_blank}
    return normalize(val) in tokens


def read_csv_table(path):
    with open(path, newline="", encoding="latin1") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return [], []
        fieldnames = [str(c).strip() for c in reader.fieldnames]
        reader.fieldnames = fieldnames
        rows = list(reader)
    return fieldnames, rows


def discover_output_files(output_dir):
    if not os.path.isdir(output_dir):
        raise FileNotFoundError(f"Output directory not found: {output_dir}")
    return sorted(
        os.path.join(output_dir, name)
        for name in os.listdir(output_dir)
        if name.lower().endswith(".csv") and name.lower().startswith("quik")
    )


def table_name_from_path(path):
    return os.path.splitext(os.path.basename(path))[0].lower()


def field_lookup(fieldnames):
    return {f.upper(): f for f in fieldnames}


def make_finding(category, severity, table, message, row=None, field=None, context=None):
    return {
        "category": category,
        "severity": severity,
        "table": table,
        "message": message,
        "row": row,
        "field": field,
        "context": context or {},
    }


def apply_sample_limit(findings, sample_limit):
    counts = Counter(f["category"] for f in findings)
    shown = Counter()
    limited = []
    for f in findings:
        cat = f["category"]
        if shown[cat] < sample_limit:
            limited.append(f)
            shown[cat] += 1
    truncated = {cat: counts[cat] > sample_limit for cat in counts}
    return limited, counts, truncated


# ---------------------------------------------------------------------------
# Category 1: Schema validation
# ---------------------------------------------------------------------------

def check_schema(table, fieldnames, schema_cfg):
    findings = []
    if table not in schema_cfg:
        return findings

    expected = schema_cfg[table]["columns"]
    strict_order = schema_cfg[table].get("strict_order", True)
    actual_upper = [f.upper() for f in fieldnames]
    expected_upper = [c.upper() for c in expected]

    for col in expected_upper:
        if col not in actual_upper:
            findings.append(make_finding(
                "schema", "ERROR", table,
                f"Missing required column: {col}",
                field=col,
            ))

    for col in actual_upper:
        if col not in expected_upper:
            findings.append(make_finding(
                "schema", "WARN", table,
                f"Unexpected extra column: {col}",
                field=col,
            ))

    if strict_order and actual_upper[: len(expected_upper)] != expected_upper:
        findings.append(make_finding(
            "schema", "ERROR", table,
            "Column order mismatch vs schema manifest",
            context={"expected_head": expected[:5], "actual_head": fieldnames[:5]},
        ))

    return findings


# ---------------------------------------------------------------------------
# Category 2: Critical field validation
# ---------------------------------------------------------------------------

def check_critical_fields(table, fieldnames, rows, critical_cfg):
    findings = []
    rules = critical_cfg.get(table, [])
    if not rules:
        return findings

    lookup = field_lookup(fieldnames)
    for rule in rules:
        field = rule["field"].upper()
        if field not in lookup:
            continue
        col = lookup[field]
        blank_if = rule.get("blank_if")
        severity = rule.get("severity", "ERROR")
        for idx, row in enumerate(rows, start=2):
            val = row.get(col, "")
            if is_blank(val, extra_blank=blank_if):
                ctx = {}
                if "MPOLICY" in lookup:
                    ctx["MPOLICY"] = row.get(lookup["MPOLICY"], "")
                if table == "quikclid" and "MRELATION" in lookup:
                    ctx["MRELATION"] = row.get(lookup["MRELATION"], "")
                findings.append(make_finding(
                    "critical", severity, table,
                    f"Blank critical field: {field}",
                    row=idx, field=field, context=ctx,
                ))
    return findings


# ---------------------------------------------------------------------------
# Category 3: Date validation
# ---------------------------------------------------------------------------

def validate_date_value(val):
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


def resolve_date_columns(table, fieldnames, date_cfg):
    exclusions = {c.upper() for c in date_cfg.get("global_exclusions", [])}
    configured = [c.upper() for c in date_cfg.get("by_table", {}).get(table, [])]
    if configured:
        return [f for f in fieldnames if f.upper() in configured]
    cols = []
    for f in fieldnames:
        n = f.upper()
        if n in exclusions:
            continue
        if "DATE" in n or "DOB" in n or n.endswith("DT") or n in ("MPAIDTO", "MBILLTO", "MLASTANN"):
            cols.append(f)
    return cols


def check_dates(table, fieldnames, rows, date_cfg):
    findings = []
    for col in resolve_date_columns(table, fieldnames, date_cfg):
        for idx, row in enumerate(rows, start=2):
            val = row.get(col, "")
            result = validate_date_value(val)
            if result is not True and result is not None:
                findings.append(make_finding(
                    "dates", "ERROR", table,
                    f"Invalid date in {col}: {result}",
                    row=idx, field=col,
                    context={"value": val},
                ))
    return findings


# ---------------------------------------------------------------------------
# Category 4: Duplicate key validation
# ---------------------------------------------------------------------------

def check_duplicate_keys(table, fieldnames, rows, key_cfg):
    findings = []
    definitions = key_cfg.get(table, [])
    if not definitions:
        return findings

    lookup = field_lookup(fieldnames)
    for definition in definitions:
        key_name = definition["name"]
        fields = definition["fields"]
        severity = definition.get("severity", "ERROR")
        cols = []
        for f in fields:
            fu = f.upper()
            if fu not in lookup:
                cols = None
                break
            cols.append(lookup[fu])
        if not cols:
            continue

        seen = defaultdict(list)
        for idx, row in enumerate(rows, start=2):
            key = tuple(normalize(row.get(c, "")) for c in cols)
            if all(not part for part in key):
                continue
            seen[key].append(idx)

        for key, row_nums in seen.items():
            if len(row_nums) > 1:
                findings.append(make_finding(
                    "duplicates", severity, table,
                    f"Duplicate key '{key_name}': {dict(zip(fields, key))}",
                    context={"rows": row_nums, "count": len(row_nums), "key_name": key_name},
                ))
    return findings


# ---------------------------------------------------------------------------
# Category 5: Regression comparison
# ---------------------------------------------------------------------------

def build_table_metrics(table, fieldnames, findings):
    metrics = {
        "row_count": 0,
        "schema_errors": 0,
        "critical_errors": 0,
        "invalid_dates": 0,
        "duplicate_keys": 0,
        "blank_mridrid": 0,
        "missing_mphase": 0,
    }
    for f in findings:
        if f["category"] == "schema" and f["severity"] == "ERROR":
            metrics["schema_errors"] += 1
        elif f["category"] == "critical" and f["severity"] == "ERROR":
            metrics["critical_errors"] += 1
            if f.get("field") == "MRIDRID":
                metrics["blank_mridrid"] += 1
            if f.get("field") == "MPHASE":
                metrics["missing_mphase"] += 1
        elif f["category"] == "dates":
            metrics["invalid_dates"] += 1
        elif f["category"] == "duplicates":
            metrics["duplicate_keys"] += 1
    metrics["column_signature"] = "|".join(f.upper() for f in fieldnames)
    return metrics


def write_baseline(path, label, table_results):
    payload = {
        "label": label,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tables": {},
    }
    for result in table_results:
        payload["tables"][result["table"]] = {
            "row_count": result["row_count"],
            "metrics": result["metrics"],
        }
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    logger.info("Baseline written: %s", path)


def load_baseline(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_regression(table, metrics, row_count, baseline_data, strict=False):
    findings = []
    base_tables = baseline_data.get("tables", {})
    if table not in base_tables:
        findings.append(make_finding(
            "regression", "WARN", table,
            f"No baseline entry for table '{table}'",
        ))
        return findings

    base = base_tables[table]
    base_metrics = base.get("metrics", {})
    base_count = base.get("row_count", 0)

    if row_count != base_count:
        severity = "ERROR" if strict else "WARN"
        findings.append(make_finding(
            "regression", severity, table,
            f"Row count changed: baseline={base_count} current={row_count}",
            context={"delta": row_count - base_count},
        ))

    for metric in ("blank_mridrid", "missing_mphase", "invalid_dates", "duplicate_keys", "critical_errors"):
        current = metrics.get(metric, 0)
        previous = base_metrics.get(metric, 0)
        if current > previous:
            findings.append(make_finding(
                "regression", "ERROR", table,
                f"Metric regression '{metric}': baseline={previous} current={current}",
                context={"delta": current - previous},
            ))

    base_sig = base_metrics.get("column_signature", "")
    current_sig = metrics.get("column_signature", "")
    if base_sig and current_sig and base_sig != current_sig:
        findings.append(make_finding(
            "regression", "ERROR", table,
            "Column signature changed vs baseline",
        ))

    return findings


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def validate_table(path, config, enabled_categories, baseline_data=None, strict_regression=False):
    table = table_name_from_path(path)
    fieldnames, rows = read_csv_table(path)
    all_findings = []

    if "schema" in enabled_categories:
        all_findings.extend(check_schema(table, fieldnames, config["schema"]))

    if "critical" in enabled_categories:
        all_findings.extend(check_critical_fields(table, fieldnames, rows, config["critical"]))

    if "dates" in enabled_categories:
        all_findings.extend(check_dates(table, fieldnames, rows, config["dates"]))

    if "duplicates" in enabled_categories:
        all_findings.extend(check_duplicate_keys(table, fieldnames, rows, config["keys"]))

    metrics = build_table_metrics(table, fieldnames, all_findings)
    metrics["row_count"] = len(rows)

    if "regression" in enabled_categories and baseline_data:
        all_findings.extend(check_regression(table, metrics, len(rows), baseline_data, strict_regression))

    return {
        "table": table,
        "file": os.path.basename(path),
        "path": path,
        "row_count": len(rows),
        "metrics": metrics,
        "findings": all_findings,
    }


def run_validation(output_dir, config_dir, enabled_categories, sample_limit,
                   baseline_path=None, strict_regression=False):
    config = load_all_config(config_dir)
    baseline_data = load_baseline(baseline_path) if baseline_path else None
    files = discover_output_files(output_dir)
    results = []
    for path in files:
        logger.info("Validating %s", os.path.basename(path))
        results.append(validate_table(
            path, config, enabled_categories, baseline_data, strict_regression,
        ))
    return results


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def count_by_severity(findings):
    errors = sum(1 for f in findings if f["severity"] == "ERROR")
    warns = sum(1 for f in findings if f["severity"] == "WARN")
    return errors, warns


def format_text_report(results, output_dir, enabled_categories, sample_limit, baseline_path=None):
    lines = [
        "=== QLAdmin Output Validation Report ===",
        f"Directory: {os.path.abspath(output_dir)}",
        f"Categories: {', '.join(enabled_categories)}",
    ]
    if baseline_path:
        lines.append(f"Baseline: {os.path.abspath(baseline_path)}")
    lines.append("")

    total_errors = 0
    total_warns = 0
    category_totals = Counter()

    for result in results:
        findings = result["findings"]
        if not findings:
            continue
        limited, counts, truncated = apply_sample_limit(findings, sample_limit)
        errors, warns = count_by_severity(findings)
        total_errors += errors
        total_warns += warns

        lines.append(f"--- {result['file']} ({result['row_count']} rows) ---")
        by_category = defaultdict(list)
        for f in limited:
            by_category[f["category"]].append(f)

        for cat in CATEGORIES:
            if cat not in by_category:
                continue
            lines.append(f"  [{cat.upper()}] {counts[cat]} finding(s)")
            for f in by_category[cat]:
                loc = f"row {f['row']}" if f.get("row") else "file"
                field = f" {f['field']}" if f.get("field") else ""
                lines.append(f"    [{f['severity']}] {loc}{field}: {f['message']}")
                if f.get("context"):
                    ctx = ", ".join(f"{k}={v!r}" for k, v in f["context"].items() if k != "rows")
                    if ctx:
                        lines.append(f"      context: {ctx}")
                    if "rows" in f["context"]:
                        lines.append(f"      rows: {f['context']['rows'][:5]}")
            if truncated.get(cat):
                lines.append(f"    ... showing first {sample_limit} of {counts[cat]}")
            category_totals[cat] += counts[cat]
        lines.append("")

    lines.extend([
        "=== Summary ===",
        f"Files scanned: {len(results)}",
        f"Files with findings: {sum(1 for r in results if r['findings'])}",
        f"Total ERROR: {total_errors}",
        f"Total WARN: {total_warns}",
    ])
    for cat in CATEGORIES:
        if category_totals[cat]:
            lines.append(f"  {cat}: {category_totals[cat]}")
    lines.append("Status: PASS" if total_errors == 0 else "Status: FAIL")
    return "\n".join(lines)


def write_csv_report(results, csv_path, sample_limit):
    all_findings = []
    for result in results:
        all_findings.extend(result["findings"])
    limited, _, _ = apply_sample_limit(all_findings, sample_limit)
    fieldnames = ["category", "severity", "table", "row", "field", "message", "context"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for finding in limited:
            row = dict(finding)
            row["context"] = json.dumps(row.get("context", {}), ensure_ascii=True)
            writer.writerow(row)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_categories(raw):
    if not raw:
        return set(CATEGORIES) - {"regression"}
    selected = {c.strip().lower() for c in raw.split(",")}
    unknown = selected - set(CATEGORIES)
    if unknown:
        raise ValueError(f"Unknown categories: {', '.join(sorted(unknown))}")
    return selected


def setup_logging(verbose):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def main():
    parser = argparse.ArgumentParser(
        description="Enterprise validator for QLAdmin quik*.csv migration outputs.",
    )
    parser.add_argument("output_dir", nargs="?", default=".", help="Directory with quik*.csv files")
    parser.add_argument("--config-dir", default=DEFAULT_CONFIG_DIR, help="Path to validation_config/")
    parser.add_argument("--rules", help="Comma-separated categories: schema,critical,dates,duplicates,regression")
    parser.add_argument("--baseline", help="Baseline JSON for regression comparison")
    parser.add_argument("--write-baseline", help="Write baseline JSON from current output")
    parser.add_argument("--baseline-label", default="manual_baseline", help="Label stored in baseline file")
    parser.add_argument("--strict-regression", action="store_true", help="Treat row-count drift as ERROR")
    parser.add_argument("-o", "--report", help="Write text report to file")
    parser.add_argument("--csv-report", help="Write findings CSV report to file")
    parser.add_argument("--sample-limit", type=int, default=DEFAULT_SAMPLE_LIMIT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    setup_logging(args.verbose)
    output_dir = os.path.abspath(args.output_dir)

    try:
        enabled = parse_categories(args.rules)
        if args.baseline:
            enabled.add("regression")

        config = load_all_config(args.config_dir)
        files = discover_output_files(output_dir)
        if not files:
            print(f"No quik*.csv files found in: {output_dir}")
            return 0

        baseline_data = load_baseline(args.baseline) if args.baseline else None
        results = []
        for path in files:
            logger.info("Validating %s", os.path.basename(path))
            results.append(validate_table(
                path, config, enabled, baseline_data, args.strict_regression,
            ))

        if args.write_baseline:
            write_baseline(args.write_baseline, args.baseline_label, results)
            print(f"Baseline written: {args.write_baseline}")

        report = format_text_report(
            results, output_dir, sorted(enabled), args.sample_limit, args.baseline,
        )
        print(report)

        if args.report:
            with open(args.report, "w", encoding="utf-8") as f:
                f.write(report + "\n")
            print(f"Text report saved: {args.report}")

        if args.csv_report:
            write_csv_report(results, args.csv_report, args.sample_limit)
            print(f"CSV report saved: {args.csv_report}")

        has_errors = any(
            f["severity"] == "ERROR"
            for r in results for f in r["findings"]
        )
        return 1 if has_errors else 0

    except (FileNotFoundError, ValueError) as exc:
        logger.error("%s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
