"""Enterprise final output validation orchestrator (read-only)."""



from __future__ import annotations



import os

import sys

from collections import Counter, defaultdict

from datetime import datetime

from typing import Any



from .rule_audit import RuleAuditTracker

from .validation_config import REPORT_SUBDIR, default_config_dir, known_rule_ids, load_all_configs, resolve_rule_files

from .validation_helpers import discover_quik_csvs, load_output_tables, table_name_from_path

from .validation_report_writer import write_reports

from .validation_rules import apply_findings_to_audit, convert_legacy_finding, run_extended_rules





def _ensure_validate_output_import(repo_root: str):

    if repo_root not in sys.path:

        sys.path.insert(0, repo_root)

    import validate_output as vo  # noqa: WPS433 — intentional reuse of existing validator

    return vo





def compute_overall_status(detail_rows: list[dict], audit: RuleAuditTracker) -> str:

    block = sum(1 for r in detail_rows if r.get("disposition") == "Block")

    hold = sum(1 for r in detail_rows if r.get("disposition") == "Hold")

    warn = sum(1 for r in detail_rows if r.get("disposition") == "Warning")

    internal_fail = audit.summary_counts().get("rules_failed_internally", 0)

    if block:

        return "BLOCKED"

    if hold:

        return "HOLD"

    if internal_fail:

        return "WARNING"

    if warn:

        return "WARNING"

    return "PASS"





def _mark_legacy_rules_executed(audit: RuleAuditTracker, findings: list[dict], path: str, records: int) -> None:

    """Mark legacy rules with zero findings as executed when table was scanned."""

    converted = [convert_legacy_finding(f, path) for f in findings]

    apply_findings_to_audit(audit, converted, records_scanned=records)

    by_rule = Counter(c["rule_id"] for c in converted)

    legacy_rule_map = {

        "schema": ("FMT-007", "FMT-008"),

        "critical": ("REQ-002", "REQ-003", "POL-002", "PRM-010"),

        "dates": ("DT-001",),

        "duplicates": ("POL-001", "DUP-002", "DUP-003", "CLNT-001"),

    }

    for cat, rule_ids in legacy_rule_map.items():

        cat_findings = [f for f in findings if f.get("category") == cat]

        if not cat_findings:

            for rid in rule_ids:

                row = audit._rows.get(rid)

                if row and row.get("status") == "PENDING":

                    audit.complete(rid, 0, records_scanned=records)





def _finalize_audit_for_pending(audit: RuleAuditTracker, output_dir: str, source_dir: str | None, repo_root: str) -> None:

    for rid in audit.known_rule_ids():

        row = audit._rows.get(rid, {})

        if row.get("status") != "PENDING":

            continue

        exp, found, missing, required = resolve_rule_files(rid, output_dir, source_dir, repo_root)

        if missing and not required:

            audit.skip(

                rid,

                f"Optional file(s) missing: {', '.join(missing)}",

                status="SKIPPED_MISSING_OPTIONAL_FILE",

                files_expected=exp,

                files_found=found,

                files_missing=missing,

            )

        else:

            audit.skip(rid, "Rule not applicable in this validation pass (legacy-only or conditional)")





def run_final_output_validation(

    output_dir: str,

    *,

    repo_root: str | None = None,

    source_dir: str | None = None,

    app_table_schemas: dict[str, list[str]] | None = None,

    config_dir: str | None = None,

) -> dict[str, Any]:

    """

    Read-only final validation against output/ CSVs.

    Does not mutate source or target output files.

    """

    repo_root = repo_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    output_dir = os.path.normpath(os.path.abspath(output_dir))

    config_dir = config_dir or default_config_dir(repo_root)

    reports_dir = os.path.join(output_dir, REPORT_SUBDIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")



    audit = RuleAuditTracker(known_rule_ids())

    detail_rows: list[dict] = []

    missing_files = 0



    tables = load_output_tables(output_dir)

    records_scanned = sum(t.get("row_count", 0) for t in tables.values())



    if not tables:

        finding = {

            "rule_id": "GOV-005",

            "rule_name": "No quik*.csv output files found",

            "severity": "Critical",

            "disposition": "Block",

            "table_name": "output",

            "file_name": "",

            "key_fields": "",

            "key_value": "",

            "field_name": "",

            "actual_value": "",

            "expected_value": "",

            "message": f"No quik*.csv files in output folder: {output_dir}",

            "source_file": output_dir,

            "row_number": "",

            "created_timestamp": generated_at,

        }

        detail_rows.append(finding)

        audit.begin("GOV-005", files_expected=["quik*.csv"], files_missing=["quik*.csv"])

        audit.complete("GOV-005", 1)

        missing_files = 1

    else:

        def _run_legacy_pack():

            vo = _ensure_validate_output_import(repo_root)

            config = load_all_configs(config_dir)

            vo_config = {

                "schema": config.get("schema", {}),

                "critical": config.get("critical", {}),

                "dates": config.get("dates", {}),

                "keys": config.get("keys", {}),

                "priority": config.get("priority", {}),

            }

            files = discover_quik_csvs(output_dir)

            vo_tables = {}

            pack_findings = []

            enabled = set(vo.CATEGORIES) - {"regression"}

            for path in files:

                table = table_name_from_path(path)

                fieldnames, rows = vo.read_csv_table(path)

                vo_tables[table] = {"path": path, "fieldnames": fieldnames, "rows": rows}

                result = vo.validate_table(path, vo_config, enabled)

                raw = result.get("findings") or []

                pack_findings.extend(raw)

                _mark_legacy_rules_executed(audit, raw, path, len(rows))

                for f in raw:

                    detail_rows.append(convert_legacy_finding(f, path))



            priority_findings = vo.run_priority_checks(

                vo_tables, vo_config, output_dir,

                repo_root=repo_root,

                source_dir=source_dir if source_dir and os.path.isdir(source_dir) else None,

            )

            pack_findings.extend(priority_findings)

            converted_priority = [convert_legacy_finding(f, output_dir) for f in priority_findings]

            apply_findings_to_audit(audit, converted_priority, records_scanned=records_scanned)

            detail_rows.extend(converted_priority)

            return pack_findings



        exp = [os.path.basename(p) for p in discover_quik_csvs(output_dir)]

        audit.run_guarded(

            "VO-LEGACY-PACK",

            _run_legacy_pack,

            files_expected=exp,

            files_found=exp,

            files_missing=[],

            records_scanned=records_scanned,

        )



        ext = run_extended_rules(

            tables, output_dir, repo_root, source_dir, app_table_schemas, audit=audit,

        )

        for row in ext:

            if not row.get("created_timestamp"):

                row["created_timestamp"] = generated_at

        detail_rows.extend(ext)



    _finalize_audit_for_pending(audit, output_dir, source_dir, repo_root)

    audit.finalize_unrun()



    audit_counts = audit.summary_counts()

    disposition_counts = Counter(r.get("disposition", "") for r in detail_rows)

    summary = {

        "overall_status": compute_overall_status(detail_rows, audit),

        "total_rules_executed": audit_counts.get("rules_executed", 0),

        "total_rules_known": audit_counts.get("total_rules_known", 0),

        "rules_with_findings": audit_counts.get("rules_with_findings", 0),

        "rules_skipped": audit_counts.get("rules_skipped", 0),

        "rules_failed_internally": audit_counts.get("rules_failed_internally", 0),

        "total_records_scanned": records_scanned,

        "block_count": disposition_counts.get("Block", 0),

        "hold_count": disposition_counts.get("Hold", 0),

        "warning_count": disposition_counts.get("Warning", 0),

        "report_only_count": disposition_counts.get("Report only", 0),

        "missing_file_count": missing_files,

        "disposition_counts": dict(disposition_counts),

        "audit_status_counts": dict(Counter(r.get("status", "") for r in audit.to_list())),

        "generated_at": generated_at,

        "output_dir": output_dir,

    }



    report_paths = write_reports(

        reports_dir, detail_rows, {**summary, "reports_dir": reports_dir},

        timestamp, audit_rows=audit.to_list(),

    )

    summary["reports_dir"] = reports_dir

    summary.update(report_paths)



    return {

        "status": summary["overall_status"],

        "summary": summary,

        "detail_count": len(detail_rows),

        "audit_count": len(audit.to_list()),

        "reports": report_paths,

    }


