"""Write final output validation reports (read-only artifacts)."""



from __future__ import annotations



import csv

import json

import os

from datetime import datetime

from typing import Any



from .rule_audit import AUDIT_COLUMNS





DETAIL_COLUMNS = [

    "rule_id", "rule_name", "severity", "disposition", "table_name", "file_name",

    "key_fields", "key_value", "field_name", "actual_value", "expected_value",

    "message", "source_file", "row_number", "created_timestamp",

]



SUMMARY_COLUMNS = [

    "metric", "value",

]





def write_reports(

    reports_dir: str,

    detail_rows: list[dict],

    summary: dict[str, Any],

    timestamp: str | None = None,

    audit_rows: list[dict] | None = None,

) -> dict[str, str]:

    os.makedirs(reports_dir, exist_ok=True)

    ts = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")



    detail_path = os.path.join(reports_dir, "final_output_validation_detail.csv")

    summary_path = os.path.join(reports_dir, "final_output_validation_summary.csv")

    audit_path = os.path.join(reports_dir, "final_output_validation_rule_audit.csv")

    detail_ts = os.path.join(reports_dir, f"final_output_validation_detail_{ts}.csv")

    summary_ts = os.path.join(reports_dir, f"final_output_validation_summary_{ts}.csv")

    audit_ts = os.path.join(reports_dir, f"final_output_validation_rule_audit_{ts}.csv")

    json_path = os.path.join(reports_dir, f"final_output_validation_summary_{ts}.json")



    _write_detail_csv(detail_path, detail_rows)

    _write_detail_csv(detail_ts, detail_rows)

    _write_summary_csv(summary_path, summary)

    _write_summary_csv(summary_ts, summary)

    if audit_rows is not None:

        _write_audit_csv(audit_path, audit_rows)

        _write_audit_csv(audit_ts, audit_rows)



    with open(json_path, "w", encoding="utf-8") as fh:

        json.dump(summary, fh, indent=2)



    paths = {

        "detail_csv": detail_path,

        "summary_csv": summary_path,

        "detail_csv_timestamped": detail_ts,

        "summary_csv_timestamped": summary_ts,

        "summary_json": json_path,

        "reports_dir": reports_dir,

    }

    if audit_rows is not None:

        paths["rule_audit_csv"] = audit_path

        paths["rule_audit_csv_timestamped"] = audit_ts

    return paths





def _write_detail_csv(path: str, rows: list[dict]) -> None:

    with open(path, "w", newline="", encoding="utf-8") as fh:

        writer = csv.DictWriter(fh, fieldnames=DETAIL_COLUMNS, extrasaction="ignore")

        writer.writeheader()

        for row in rows:

            writer.writerow({k: row.get(k, "") for k in DETAIL_COLUMNS})





def _write_audit_csv(path: str, rows: list[dict]) -> None:

    with open(path, "w", newline="", encoding="utf-8") as fh:

        writer = csv.DictWriter(fh, fieldnames=AUDIT_COLUMNS, extrasaction="ignore")

        writer.writeheader()

        for row in rows:

            writer.writerow({k: row.get(k, "") for k in AUDIT_COLUMNS})





def _write_summary_csv(path: str, summary: dict) -> None:

    rows = [

        ("overall_status", summary.get("overall_status", "")),

        ("total_rules_known", summary.get("total_rules_known", 0)),

        ("total_rules_executed", summary.get("total_rules_executed", 0)),

        ("rules_with_findings", summary.get("rules_with_findings", 0)),

        ("rules_skipped", summary.get("rules_skipped", 0)),

        ("rules_failed_internally", summary.get("rules_failed_internally", 0)),

        ("total_records_scanned", summary.get("total_records_scanned", 0)),

        ("block_count", summary.get("block_count", 0)),

        ("hold_count", summary.get("hold_count", 0)),

        ("warning_count", summary.get("warning_count", 0)),

        ("report_only_count", summary.get("report_only_count", 0)),

        ("missing_file_count", summary.get("missing_file_count", 0)),

        ("generated_at", summary.get("generated_at", "")),

        ("output_dir", summary.get("output_dir", "")),

        ("reports_dir", summary.get("reports_dir", "")),

    ]

    for k, v in (summary.get("disposition_counts") or {}).items():

        rows.append((f"disposition_{k}", v))

    for k, v in (summary.get("audit_status_counts") or {}).items():

        rows.append((f"audit_status_{k}", v))

    with open(path, "w", newline="", encoding="utf-8") as fh:

        writer = csv.writer(fh)

        writer.writerow(SUMMARY_COLUMNS)

        writer.writerows(rows)


