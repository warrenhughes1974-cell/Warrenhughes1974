"""
Robust quikplan_source.csv loader (Phase P3G).

LifePRO quikplan_source exports embed unquoted commas in DESCRIPTION fields.
pandas read_csv(on_bad_lines='skip') silently drops those rows — causing catalog
products (L15, DISCHO80, etc.) to never reach quikplan emit.

This loader merges overflow fields back into DESCRIPTION without mutating source files.
"""

from __future__ import annotations

import csv
import os
from io import StringIO

import pandas as pd

DESCRIPTION_FIELD_INDEX = 2


def _is_separator_row(fields: list[str]) -> bool:
    if not fields:
        return True
    first = fields[0]
    return "---" in first or first.strip("-") == ""


def _is_header_row(fields: list[str], header_fields: list[str]) -> bool:
    if not fields or not header_fields:
        return False
    return fields[0].strip().upper() == header_fields[0].strip().upper()


def _merge_description_overflow(fields: list[str], ncol: int, desc_idx: int = DESCRIPTION_FIELD_INDEX) -> list[str]:
    """Rejoin fields split by unquoted commas inside DESCRIPTION."""
    if len(fields) <= ncol:
        if len(fields) < ncol:
            return fields + [""] * (ncol - len(fields))
        return fields
    extra = len(fields) - ncol
    merged_desc = ",".join(fields[desc_idx : desc_idx + extra + 1])
    return fields[:desc_idx] + [merged_desc] + fields[desc_idx + extra + 1 :]


def _classify_row(fields: list[str], line_number: int, header_fields: list[str]) -> str:
    if line_number == 1:
        return "HEADER"
    if not fields or all(not f for f in fields):
        return "BLANK"
    if _is_separator_row(fields):
        return "SEPARATOR"
    if _is_header_row(fields, header_fields):
        return "SEPARATOR"
    return "DATA"


def load_quikplan_source_csv(
    source_path: str,
    *,
    collect_trace: bool = True,
) -> tuple[pd.DataFrame, list[dict]]:
    """
    Load quikplan_source.csv preserving field values exactly as stored.

    Returns (dataframe, ingestion_trace_rows).
    """
    if not source_path or not os.path.isfile(source_path):
        return pd.DataFrame(), []

    with open(source_path, encoding="latin1", newline="") as fh:
        raw_lines = fh.readlines()

    if not raw_lines:
        return pd.DataFrame(), []

    header_reader = csv.reader([raw_lines[0]])
    header_fields = next(header_reader)
    ncol = len(header_fields)
    columns = [str(c).replace("\ufeff", "").strip() for c in header_fields]

    data_rows: list[list[str]] = []
    trace_rows: list[dict] = []

    for line_idx, raw_line in enumerate(raw_lines, start=1):
        raw_line_stripped = raw_line.rstrip("\r\n")
        parsed = list(csv.reader([raw_line_stripped]))[0] if raw_line_stripped else []
        classification = _classify_row(parsed, line_idx, header_fields)
        separator_detected = classification in ("SEPARATOR", "HEADER")
        skip_reason = ""
        was_skipped = False
        parsed_coverage_id = parsed[0] if parsed else ""
        merged_fields = parsed

        if classification == "HEADER":
            was_skipped = True
            skip_reason = "HEADER_ROW"
        elif classification in ("SEPARATOR", "BLANK"):
            was_skipped = True
            skip_reason = classification
        elif classification == "DATA":
            pre_len = len(parsed)
            merged_fields = _merge_description_overflow(parsed, ncol)
            if pre_len > ncol:
                skip_reason = f"COMMA_OVERFLOW_MERGED_{pre_len}_TO_{len(merged_fields)}"
            elif pre_len < ncol:
                skip_reason = f"PADDED_{pre_len}_TO_{len(merged_fields)}"
            data_rows.append(merged_fields)
        else:
            was_skipped = True
            skip_reason = "UNKNOWN"

        if collect_trace:
            trace_rows.append({
                "line_number": line_idx,
                "raw_line": raw_line_stripped,
                "parsed_coverage_id": parsed_coverage_id,
                "row_classification": classification,
                "separator_detected": "Y" if separator_detected else "N",
                "was_skipped": "Y" if was_skipped else "N",
                "skip_reason": skip_reason,
                "was_emitted": "N",
                "emitted_plan": "",
            })

    df = pd.DataFrame(data_rows, columns=columns)
    return df.fillna(""), trace_rows


def annotate_ingestion_emit_trace(
    trace_rows: list[dict],
    emitted_plan_by_coverage: dict[str, str],
) -> list[dict]:
    """Mark ingestion trace rows that produced quikplan emit."""
    for row in trace_rows:
        if row.get("was_skipped") == "Y":
            continue
        cid = row.get("parsed_coverage_id", "")
        # Match emit map with exact key first, then stripped key for lineage only
        plan = emitted_plan_by_coverage.get(cid, "")
        if not plan:
            plan = emitted_plan_by_coverage.get(cid.strip(), "")
        if plan:
            row["was_emitted"] = "Y"
            row["emitted_plan"] = plan
    return trace_rows
