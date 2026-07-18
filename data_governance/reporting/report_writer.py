"""Write machine-readable and business-readable governance outputs."""

from __future__ import annotations

import csv
import json
import os
from collections import defaultdict

from data_governance.catalog.governance_items import ALL_GOVERNANCE_ITEMS, ALL_RULE_DEFINITIONS
from data_governance.config.settings import (
    VALIDATION_GUIDE_NAME,
    VALIDATION_MANIFEST_NAME,
    GovernancePaths,
)
from data_governance.models.findings import GovernanceRunResult
from data_governance.models.statuses import STATUS_ERROR, STATUS_FAIL, STATUS_PASS
from data_governance.reporting.accuracy import calculate_conformance_accuracy
from data_governance.reporting.executive_summary import (
    build_executive_summary_lines,
    count_rule_statuses,
)
from data_governance.reporting.validation_guide import (
    build_validation_manifest,
    write_validation_guide,
    write_validation_manifest,
)


FINDINGS_FIELDNAMES = [
    "governance_item_id",
    "rule_id",
    "rule_name",
    "business_name",
    "description",
    "severity",
    "status",
    "data_region_path",
    "source_table",
    "source_field",
    "source_record_id",
    "key_value",
    "invalid_value",
    "expected_condition",
    "actual_condition",
    "message",
    "run_id",
    "run_timestamp",
    "company_code",
    "agent_number",
    "agent_name",
    "policy_number",
    "duplicate_count",
    "original_policy_number",
    "normalized_policy_number",
    "policy_number_length",
    "min_permitted_length",
    "max_permitted_length",
    "company_code_source_field",
    "account_number_source_field",
    "original_company_code",
    "normalized_company_code",
    "original_account_number",
    "normalized_account_number",
    "composite_business_key",
    "reference_table",
    "reference_field",
    "reference_match_count",
    "group_number",
    "original_group_number",
    "normalized_group_number",
    "original_billing_name",
    "normalized_billing_name",
    "original_value",
    "normalized_value",
    "expected_value",
    "governance_run_date",
    "controlling_date",
    "expected_prior_month_end",
    "failure_category",
    "plan",
    "mortality_table",
    "eti_mortality_table",
    "gender",
    "underwriting_class",
    "band",
    "issue_state",
    "effective_date",
    "min_allowed_date",
    "max_allowed_date",
]

SUMMARY_FIELDNAMES = [
    "run_id",
    "run_timestamp",
    "governance_item_id",
    "rule_id",
    "rule_name",
    "business_name",
    "severity",
    "status",
    "records_evaluated",
    "passed_count",
    "failed_count",
    "error_count",
    "error_message",
    "Rules_Executed",
    "Rules_Passed",
    "Rules_Failed",
    "Rules_Not_Run",
    "Rules_Error",
    "Data_Conformance_Accuracy_Percent",
    "Data_Conformance_Accuracy_Display",
    "Validation_Guide_File",
    "Validation_Manifest_File",
    "records_shorter_than_4",
    "records_longer_than_11",
    "blank_policy_numbers",
    "null_policy_numbers",
    "distinct_company_codes",
    "distinct_account_numbers",
    "distinct_company_account_combinations",
    "duplicate_combinations",
    "records_involved_in_duplicates",
    "blank_company_codes",
    "null_company_codes",
    "blank_account_numbers",
    "null_account_numbers",
    "valid_company_references",
    "missing_company_references",
    "blank_company_references",
    "null_company_references",
    "references_to_duplicated_quikcomp",
    "distinct_group_numbers",
    "duplicate_group_numbers",
    "blank_group_numbers",
    "null_group_numbers",
    "populated_billing_names",
    "blank_billing_names",
    "null_billing_names",
    "records_matching_expected_value",
    "records_with_other_value",
    "blank_values",
    "null_values",
    "unreadable_values",
    "matching_prior_month_end",
    "other_dates",
    "blank_dates",
    "null_dates",
    "unreadable_dates",
    "blank_escdate_values",
    "populated_escdate_values",
    "valid_defaults",
    "valid_reference_matches",
    "missing_references",
    "ambiguous_references",
    "records_using_00",
    "records_using_valid_states",
    "invalid_state_codes",
    "dates_within_range",
    "dates_before_minimum",
    "dates_after_maximum",
    "source_table_summary",
]

_STATUS_PLAIN = {
    "PASS": "PASSED — no problems found",
    "FAIL": "FAILED — problems were found that need attention",
    "ERROR": "ERROR — the check could not finish (usually a missing file)",
    "NOT_RUN": "NOT RUN — this check was not executed",
}


RESULTS_CSV_FIELDNAMES = [
    "Row_Type",
    "Overall_Result",
    "Check_Name",
    "Check_Result",
    "What_We_Checked",
    "Records_Reviewed",
    "Looked_Fine",
    "Problems_Found",
    "Problem_Detail",
    "When_It_Ran",
    "Run_ID",
    "Data_Folder",
    "Rules_Executed",
    "Rules_Passed",
    "Rules_Failed",
    "Rules_Not_Run",
    "Rules_Error",
    "Data_Conformance_Accuracy_Percent",
    "Data_Conformance_Accuracy_Display",
    "Validation_Guide_File",
    "Validation_Manifest_File",
]


def attach_conformance_metrics(result: GovernanceRunResult):
    """Attach Data Conformance Accuracy fields to the run result."""
    accuracy = calculate_conformance_accuracy(
        records_reviewed=result.records_evaluated,
        looked_fine=result.passed_count,
        problems_found=result.failed_count,
        warnings_found=int(getattr(result, "warn_count", 0) or 0),
    )
    result.data_conformance_accuracy_percent = accuracy.percent_raw
    result.data_conformance_accuracy_display = accuracy.percent_display
    result.report_warnings = [accuracy.warning] if accuracy.warning else []
    return accuracy


def write_governance_outputs(result: GovernanceRunResult, paths: GovernancePaths) -> None:
    os.makedirs(paths.output_dir, exist_ok=True)
    os.makedirs(paths.internal_dir, exist_ok=True)
    accuracy = attach_conformance_metrics(result)

    # User-facing reports at run folder root
    from data_governance.reporting.simplified_reports import (
        build_business_summary,
        write_items_needing_attention_csv,
        write_what_was_checked_html,
    )

    biz = build_business_summary(result)
    result.business_overall_result = biz.overall_result
    result.checks_incomplete_count = biz.checks_incomplete
    if biz.warning and biz.warning not in result.report_warnings:
        result.report_warnings.append(biz.warning)

    write_what_was_checked_html(result, paths.what_was_checked_html)
    write_items_needing_attention_csv(result, paths.items_needing_attention_csv)
    result.what_was_checked_path = paths.what_was_checked_html
    result.items_needing_attention_path = paths.items_needing_attention_csv

    # Technical artifacts retained under internal/ for troubleshooting
    _write_results_csv(result, paths.results_csv, accuracy)
    _write_findings_csv(result, paths.findings_csv)
    _write_summary_csv(result, paths.summary_csv, accuracy)

    manifest = build_validation_manifest(result, accuracy)
    write_validation_manifest(manifest, paths.validation_manifest)
    write_validation_guide(result, accuracy, paths.validation_guide, manifest)

    _write_report_md(result, paths.report_md, accuracy)

    result.results_csv_path = paths.results_csv
    result.findings_csv_path = paths.findings_csv
    result.summary_csv_path = paths.summary_csv
    result.report_md_path = paths.report_md
    result.validation_guide_path = paths.validation_guide
    result.validation_manifest_path = paths.validation_manifest

    _write_run_summary_json(result, paths.run_summary_json)


def _overall_reporting_fields(result: GovernanceRunResult, accuracy) -> dict[str, str]:
    statuses = count_rule_statuses(result)
    percent = (
        ""
        if accuracy.percent_raw is None
        else repr(accuracy.percent_raw)
        if isinstance(accuracy.percent_raw, float)
        else str(accuracy.percent_raw)
    )
    # Prefer full-precision string without forcing scientific notation
    if accuracy.percent_raw is not None:
        percent = format(accuracy.percent_raw, ".12f").rstrip("0").rstrip(".")
        if "." not in percent:
            percent = f"{percent}.0"
    return {
        "Rules_Executed": str(statuses["executed"]),
        "Rules_Passed": str(statuses["passed"]),
        "Rules_Failed": str(statuses["failed"]),
        "Rules_Not_Run": str(statuses["not_run"]),
        "Rules_Error": str(statuses["error"]),
        "Data_Conformance_Accuracy_Percent": percent,
        "Data_Conformance_Accuracy_Display": accuracy.percent_display,
        "Validation_Guide_File": VALIDATION_GUIDE_NAME,
        "Validation_Manifest_File": VALIDATION_MANIFEST_NAME,
    }


def _empty_overall_reporting_fields() -> dict[str, str]:
    return {
        "Rules_Executed": "",
        "Rules_Passed": "",
        "Rules_Failed": "",
        "Rules_Not_Run": "",
        "Rules_Error": "",
        "Data_Conformance_Accuracy_Percent": "",
        "Data_Conformance_Accuracy_Display": "",
        "Validation_Guide_File": "",
        "Validation_Manifest_File": "",
    }


def _write_results_csv(result: GovernanceRunResult, path: str, accuracy) -> None:
    """Primary Excel-friendly plain-language results file."""
    by_rule = {r.rule_id: r for r in result.rule_results}
    findings_by_rule: dict[str, list] = defaultdict(list)
    for finding in result.findings:
        findings_by_rule[finding.rule_id].append(finding)

    overall_fields = _overall_reporting_fields(result, accuracy)
    blank_overall = _empty_overall_reporting_fields()

    rows: list[dict[str, str]] = []
    rows.append(
        {
            "Row_Type": "OVERALL",
            "Overall_Result": _plain_status(result.overall_status),
            "Check_Name": "All selected governance checks",
            "Check_Result": _plain_status(result.overall_status),
            "What_We_Checked": (
                "Selected QLAdmin governance rules for this run "
                "(company, policy, accounting, and group-billing integrity as applicable)."
            ),
            "Records_Reviewed": str(result.records_evaluated),
            "Looked_Fine": str(result.passed_count),
            "Problems_Found": str(result.failed_count),
            "Problem_Detail": (
                "No problems found."
                if result.overall_status == "PASS"
                else f"{result.failed_count} problem(s) listed in the rows below."
            ),
            "When_It_Ran": result.run_timestamp,
            "Run_ID": result.run_id,
            "Data_Folder": result.data_dir,
            **overall_fields,
        }
    )

    for definition in ALL_RULE_DEFINITIONS:
        rule_result = by_rule.get(definition.rule_id)
        if rule_result is None:
            continue
        detail = findings_by_rule.get(definition.rule_id, [])
        fail_or_error = [f for f in detail if f.status in (STATUS_FAIL, STATUS_ERROR)]
        if not fail_or_error:
            rows.append(
                {
                    "Row_Type": "CHECK",
                    "Overall_Result": _plain_status(result.overall_status),
                    "Check_Name": definition.business_name,
                    "Check_Result": _plain_status(rule_result.status),
                    "What_We_Checked": definition.purpose,
                    "Records_Reviewed": str(rule_result.records_evaluated),
                    "Looked_Fine": str(rule_result.passed_count),
                    "Problems_Found": str(rule_result.failed_count),
                    "Problem_Detail": "No issues. Nothing to fix for this check.",
                    "When_It_Ran": result.run_timestamp,
                    "Run_ID": result.run_id,
                    "Data_Folder": result.data_dir,
                    **blank_overall,
                }
            )
        else:
            for finding in fail_or_error:
                rows.append(
                    {
                        "Row_Type": "PROBLEM",
                        "Overall_Result": _plain_status(result.overall_status),
                        "Check_Name": definition.business_name,
                        "Check_Result": _plain_status(rule_result.status),
                        "What_We_Checked": definition.purpose,
                        "Records_Reviewed": str(rule_result.records_evaluated),
                        "Looked_Fine": str(rule_result.passed_count),
                        "Problems_Found": str(rule_result.failed_count),
                        "Problem_Detail": finding.message,
                        "When_It_Ran": result.run_timestamp,
                        "Run_ID": result.run_id,
                        "Data_Folder": result.data_dir,
                        **blank_overall,
                    }
                )

    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=RESULTS_CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def _write_findings_csv(result: GovernanceRunResult, path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FINDINGS_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for finding in result.findings:
            writer.writerow(finding.to_row())


def _write_summary_csv(result: GovernanceRunResult, path: str, accuracy) -> None:
    overall_fields = _overall_reporting_fields(result, accuracy)
    blank_overall = _empty_overall_reporting_fields()

    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=SUMMARY_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        overall_row = {
            "run_id": result.run_id,
            "run_timestamp": result.run_timestamp,
            "governance_item_id": "OVERALL",
            "rule_id": "OVERALL",
            "rule_name": "All selected governance checks",
            "business_name": "Executive overall summary",
            "severity": "",
            "status": result.overall_status,
            "records_evaluated": str(result.records_evaluated),
            "passed_count": str(result.passed_count),
            "failed_count": str(result.failed_count),
            "error_count": str(result.error_count),
            "error_message": "; ".join(result.report_warnings),
            **overall_fields,
        }
        writer.writerow(overall_row)
        for rule_result in result.rule_results:
            row = rule_result.to_summary_row(result.run_id, result.run_timestamp)
            row.update(blank_overall)
            writer.writerow(row)


def _write_run_summary_json(result: GovernanceRunResult, path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(result.to_run_summary(), fh, indent=2)


def _plain_status(status: str) -> str:
    return _STATUS_PLAIN.get(status, status)


def _write_report_md(result: GovernanceRunResult, path: str, accuracy) -> None:
    """Single plain-language report — the primary human-readable deliverable."""
    by_rule = {r.rule_id: r for r in result.rule_results}
    findings_by_rule: dict[str, list] = defaultdict(list)
    for finding in result.findings:
        findings_by_rule[finding.rule_id].append(finding)

    lines: list[str] = []
    lines.extend(build_executive_summary_lines(result, accuracy))
    lines.append("---")
    lines.append("")
    lines.append("# QLAdmin Data Governance — Results (Plain Language)")
    lines.append("")
    lines.append("## Bottom line")
    lines.append("")
    lines.append(f"**{_plain_status(result.overall_status)}**")
    lines.append("")
    if result.overall_status == "PASS":
        lines.append(
            "All selected governance checks completed successfully. "
            "No problems were found in the records reviewed for this run."
        )
    elif result.overall_status == "FAIL":
        lines.append(
            f"We found **{result.failed_count} problem(s)** in the data reviewed. "
            "Details are listed below by check. Nothing in the source files was changed — "
            "this report only points out issues for review."
        )
    elif result.overall_status == "ERROR":
        lines.append(
            "One or more checks could not finish (for example, a required table was missing). "
            "See the error notes below."
        )
    else:
        lines.append("No governance checks were run.")
    lines.append("")

    lines.append("## What this report covers")
    lines.append("")
    lines.append(
        "These checks review the selected QLAdmin tables against the active governance "
        "rules for this run (uniqueness, references, required fields, formats, and "
        "configured default values)."
    )
    lines.append("")
    lines.append("| | |")
    lines.append("|---|---|")
    lines.append(f"| When it ran | {result.run_timestamp} |")
    lines.append(f"| Run ID | {result.run_id} |")
    lines.append(f"| Data region (full path) | `{result.data_dir}` |")
    lines.append(f"| Output folder for this run | `{result.output_dir}` |")
    lines.append(f"| Source opened read-only | {'Yes' if result.source_opened_read_only else 'No'} |")
    lines.append(f"| Source files modified | {'Yes' if result.source_files_modified else 'No'} |")
    lines.append(f"| Records reviewed | {result.records_evaluated:,} |")
    lines.append(f"| Records that looked fine | {result.passed_count:,} |")
    lines.append(f"| Problems found | {result.failed_count:,} |")
    lines.append(f"| Data Conformance Accuracy | {accuracy.percent_display} |")
    lines.append(f"| Technical errors | {result.error_count} |")
    lines.append(f"| Validation guide | `{VALIDATION_GUIDE_NAME}` |")
    lines.append(f"| Validation manifest | `{VALIDATION_MANIFEST_NAME}` |")
    lines.append("")

    item_map = {item.item_id: item for item in ALL_GOVERNANCE_ITEMS}
    rules_by_item: dict[str, list] = defaultdict(list)
    for definition in ALL_RULE_DEFINITIONS:
        if definition.rule_id in by_rule:
            rules_by_item[definition.governance_item_id].append(definition)

    for item_id, definitions in rules_by_item.items():
        item = item_map.get(item_id)
        if item:
            lines.append(f"## Item {item.item_number}: {item.name}")
            lines.append("")
            lines.append(item.description)
            lines.append("")
        else:
            lines.append(f"## {item_id}")
            lines.append("")

        for definition in definitions:
            rule_result = by_rule.get(definition.rule_id)
            if rule_result is None:
                continue

            lines.append(f"### Check: {definition.business_name}")
            lines.append("")
            lines.append(f"**Result:** {_plain_status(rule_result.status)}")
            lines.append("")
            lines.append(f"**What we checked:** {definition.purpose}")
            lines.append("")
            lines.append(
                f"Looked at **{rule_result.records_evaluated}** record(s): "
                f"**{rule_result.passed_count}** looked fine, "
                f"**{rule_result.failed_count}** had a problem"
                + (
                    f", **{rule_result.error_count}** had a processing error"
                    if rule_result.error_count
                    else ""
                )
                + "."
            )
            lines.append("")

            if rule_result.status == STATUS_PASS:
                lines.append("No issues. Nothing to fix for this check.")
                lines.append("")
                continue

            detail = findings_by_rule.get(definition.rule_id, [])
            fail_rows = [f for f in detail if f.status == STATUS_FAIL]
            error_rows = [f for f in detail if f.status == STATUS_ERROR]

            if fail_rows:
                lines.append("**Problems found:**")
                lines.append("")
                for i, finding in enumerate(fail_rows, start=1):
                    lines.append(f"{i}. {finding.message}")
                lines.append("")

            if error_rows:
                lines.append("**Could not finish:**")
                lines.append("")
                for i, finding in enumerate(error_rows, start=1):
                    lines.append(f"{i}. {finding.message}")
                lines.append("")

            if not fail_rows and not error_rows and rule_result.error_message:
                lines.append(f"Note: {rule_result.error_message}")
                lines.append("")

    lines.append("## What to do next")
    lines.append("")
    if result.overall_status == "PASS":
        lines.append("No action needed for the selected governance checks.")
    else:
        lines.append(
            "1. Review each problem listed above with the business owner of the related data."
        )
        lines.append(
            "2. Correct the source QLAdmin data if the finding is valid "
            "(this tool does **not** change the data for you)."
        )
        lines.append("3. Re-run the governance checks after corrections.")
    lines.append("")
    lines.append(
        "Companion files: `data_governance_validation_guide.md` (what was validated), "
        "`data_governance_validation_manifest.json`, `data_governance_findings.csv`, "
        "`data_governance_summary.csv`."
    )
    lines.append("")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines).rstrip() + "\n")
