"""Reusable read-only helpers for final output validation."""

from __future__ import annotations

import csv
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any

BLANK_TOKENS = frozenset({"", "NAN", "NONE", "NULL", "NA", "N/A"})
MIN_DATE = "19000101"


def normalize(val: Any) -> str:
    if val is None:
        return ""
    s = str(val).strip().upper()
    if s.endswith(".0"):
        s = s[:-2]
    return s


def is_blank(val: Any) -> bool:
    return normalize(val) in BLANK_TOKENS


def normalize_headers(fieldnames: list[str]) -> list[str]:
    return [str(c).replace("\ufeff", "").strip() for c in fieldnames]


def load_csv_safely(path: str) -> tuple[list[str], list[dict[str, str]], str | None]:
    if not os.path.isfile(path):
        return [], [], f"File not found: {path}"
    try:
        with open(path, newline="", encoding="latin1") as fh:
            reader = csv.DictReader(fh)
            if not reader.fieldnames:
                return [], [], None
            fieldnames = normalize_headers(list(reader.fieldnames))
            reader.fieldnames = fieldnames
            rows = [{k: (v if v is not None else "") for k, v in row.items()} for row in reader]
        return fieldnames, rows, None
    except Exception as exc:
        return [], [], str(exc)


def get_column(fieldnames: list[str], name: str) -> str | None:
    lookup = {f.upper(): f for f in fieldnames}
    return lookup.get(name.upper())


def field_lookup(fieldnames: list[str]) -> dict[str, str]:
    return {f.upper(): f for f in fieldnames}


def discover_quik_csvs(output_dir: str) -> list[str]:
    if not os.path.isdir(output_dir):
        return []
    return sorted(
        os.path.join(output_dir, n)
        for n in os.listdir(output_dir)
        if n.lower().endswith(".csv") and n.lower().startswith("quik")
    )


def table_name_from_path(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0].lower()


def load_output_tables(output_dir: str) -> dict[str, dict[str, Any]]:
    tables: dict[str, dict[str, Any]] = {}
    for path in discover_quik_csvs(output_dir):
        table = table_name_from_path(path)
        fieldnames, rows, err = load_csv_safely(path)
        tables[table] = {
            "path": path,
            "fieldnames": fieldnames,
            "rows": rows,
            "error": err,
            "row_count": len(rows),
        }
    return tables


def parse_date_yyyymmdd(val: str) -> str | None:
    d = re.sub(r"[^0-9]", "", str(val))
    return d if len(d) == 8 else None


def max_future_date(months_ahead: int = 12) -> str:
    dt = datetime.now() + timedelta(days=months_ahead * 31)
    return dt.strftime("%Y%m%d")


def validate_unique_rows(
    table: str,
    fieldnames: list[str],
    rows: list[dict],
    key_fields: list[str],
    rule_id: str,
    rule_name: str,
    severity: str,
    disposition: str,
    source_file: str,
    max_samples: int = 25,
) -> list[dict]:
    lookup = field_lookup(fieldnames)
    cols = [lookup.get(f.upper()) for f in key_fields]
    if any(c is None for c in cols):
        return []
    seen: dict[tuple, int] = {}
    dups: list[tuple] = []
    for idx, row in enumerate(rows, start=2):
        key = tuple(normalize(row.get(c, "")) for c in cols)
        if any(is_blank(k) for k in key):
            continue
        if key in seen:
            dups.append((key, idx, seen[key]))
        else:
            seen[key] = idx
    results = []
    shown = set()
    for key, row_num, first_row in dups[:max_samples]:
        if key in shown:
            continue
        shown.add(key)
        results.append(_result(
            rule_id, rule_name, severity, disposition, table, source_file,
            message=f"Duplicate key {key_fields}={key}",
            key_fields=",".join(key_fields),
            key_value="|".join(key),
            row_number=row_num,
        ))
    if len(dups) > max_samples:
        results.append(_result(
            rule_id, rule_name, severity, disposition, table, source_file,
            message=f"Additional duplicate keys truncated ({len(dups) - max_samples} more)",
            key_fields=",".join(key_fields),
        ))
    return results


def validate_reference(
    child_table: str,
    child_fieldnames: list[str],
    child_rows: list[dict],
    parent_table: str,
    parent_fieldnames: list[str],
    parent_rows: list[dict],
    child_field: str,
    parent_field: str,
    rule_id: str,
    rule_name: str,
    severity: str,
    disposition: str,
    source_file: str,
    skip_blank: bool = True,
    max_samples: int = 25,
) -> list[dict]:
    c_lookup = field_lookup(child_fieldnames)
    p_lookup = field_lookup(parent_fieldnames)
    cc = c_lookup.get(child_field.upper())
    pc = p_lookup.get(parent_field.upper())
    if not cc or not pc:
        return []
    parent_set = {normalize(r.get(pc, "")) for r in parent_rows if not is_blank(r.get(pc, ""))}
    orphans = []
    for idx, row in enumerate(child_rows, start=2):
        val = normalize(row.get(cc, ""))
        if skip_blank and is_blank(val):
            continue
        if val not in parent_set:
            orphans.append((val, idx))
    results = []
    for val, row_num in orphans[:max_samples]:
        results.append(_result(
            rule_id, rule_name, severity, disposition, child_table, source_file,
            message=f"Orphan {child_field}={val!r} not in {parent_table}.{parent_field}",
            key_fields=child_field,
            key_value=val,
            row_number=row_num,
        ))
    if len(orphans) > max_samples:
        results.append(_result(
            rule_id, rule_name, severity, disposition, child_table, source_file,
            message=f"Additional orphan references truncated ({len(orphans) - max_samples} more)",
        ))
    return results


def _result(
    rule_id: str,
    rule_name: str,
    severity: str,
    disposition: str,
    table_name: str,
    source_file: str,
    message: str,
    key_fields: str = "",
    key_value: str = "",
    field_name: str = "",
    actual_value: str = "",
    expected_value: str = "",
    row_number: int | None = None,
    created_timestamp: str | None = None,
) -> dict:
    return {
        "rule_id": rule_id,
        "rule_name": rule_name,
        "severity": severity,
        "disposition": disposition,
        "table_name": table_name,
        "file_name": os.path.basename(source_file) if source_file else "",
        "key_fields": key_fields,
        "key_value": key_value,
        "field_name": field_name,
        "actual_value": actual_value,
        "expected_value": expected_value,
        "message": message,
        "source_file": source_file,
        "row_number": row_number or "",
        "created_timestamp": created_timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def make_result(
    rule_id: str,
    message: str,
    table_name: str = "",
    source_file: str = "",
    **kwargs,
) -> dict:
    from .validation_config import rule_meta
    meta = rule_meta(rule_id)
    return _result(
        rule_id,
        meta.get("rule_name", rule_id),
        meta.get("severity", "High"),
        meta.get("disposition", "Hold"),
        table_name,
        source_file,
        message,
        **kwargs,
    )


def not_executed(rule_id: str, reason: str, table_name: str = "") -> dict:
    from .validation_config import rule_meta
    meta = rule_meta(rule_id)
    return _result(
        rule_id,
        meta.get("rule_name", rule_id),
        "Informational",
        "Report only",
        table_name,
        "",
        f"Rule not executed: {reason}",
    )
