"""Business-readable HTML and CSV reports for QLAdmin Data Governance."""

from __future__ import annotations

import csv
import html
import os
import re
from dataclasses import dataclass
from datetime import datetime

from data_governance.models.findings import GovernanceFinding, GovernanceRunResult
from data_governance.models.statuses import STATUS_ERROR, STATUS_FAIL, STATUS_NOT_RUN, STATUS_PASS
from data_governance.reporting.business_descriptions import (
    AREA_DESCRIPTIONS,
    FRIENDLY_TABLE_NAMES,
    friendly_table_name,
    get_area,
    get_rule_description,
)
from data_governance.reporting.executive_summary import format_business_datetime

TYPE_DATA_PROBLEM = "Data Problem"
TYPE_COULD_NOT = "Could Not Be Checked"
TYPE_INFORMATION = "Information"

_TYPE_SORT = {TYPE_DATA_PROBLEM: 0, TYPE_COULD_NOT: 1, TYPE_INFORMATION: 2}

_TECHNICAL_PATTERNS = (
    re.compile(r"Traceback \(most recent call last\)", re.I),
    re.compile(r"FileNotFoundError", re.I),
    re.compile(r"KeyError:", re.I),
    re.compile(r"Exception:", re.I),
    re.compile(r"Processing error while running", re.I),
)


@dataclass(frozen=True)
class BusinessSummary:
    overall_result: str
    percentage_passed_display: str
    validation_coverage_incomplete: bool
    records_checked: int
    records_passed: int
    problems_found: int
    checks_incomplete: int
    reconciles: bool
    warning: str
    review_scope: str


@dataclass
class AttentionRow:
    area: str
    table: str
    record: str
    problem: str
    current_value: str
    required_value: str
    type: str
    reference: str


def blank_display(value: str | None) -> str:
    if value is None:
        return "Blank"
    text = str(value).strip()
    if text == "" or text.lower() in {"none", "null", "nan"}:
        return "Blank"
    return text


def build_business_summary(result: GovernanceRunResult) -> BusinessSummary:
    records_checked = int(result.records_evaluated or 0)
    records_passed = int(result.passed_count or 0)
    problems_found = int(result.failed_count or 0)
    reconciles = records_checked == records_passed + problems_found
    warning = ""
    if not reconciles:
        warning = (
            "The completed-check counts do not add up correctly. "
            "Please review the internal run details."
        )

    incomplete = sum(
        1
        for r in result.rule_results
        if r.status in (STATUS_ERROR, STATUS_NOT_RUN)
    )

    if records_checked == 0:
        pct_display = "Not Available"
        pct_raw = None
    else:
        pct_raw = (records_passed / records_checked) * 100.0
        pct_display = f"{pct_raw:.2f}%"

    has_problems = problems_found > 0
    has_incomplete = incomplete > 0
    if has_problems and has_incomplete:
        overall = "Items Need Attention and Review Is Incomplete"
    elif has_problems:
        overall = "Some Items Need Attention"
    elif has_incomplete:
        overall = "Incomplete Review"
    else:
        overall = "Passed"

    coverage_incomplete = (
        (not has_problems)
        and has_incomplete
        and records_checked > 0
        and problems_found == 0
    )

    return BusinessSummary(
        overall_result=overall,
        percentage_passed_display=pct_display,
        validation_coverage_incomplete=coverage_incomplete,
        records_checked=records_checked,
        records_passed=records_passed,
        problems_found=problems_found,
        checks_incomplete=incomplete,
        reconciles=reconciles,
        warning=warning,
        review_scope=_review_scope_label(result),
    )


def _review_scope_label(result: GovernanceRunResult) -> str:
    scope = getattr(result, "review_scope", "") or "all"
    item = getattr(result, "selected_governance_item_id", "") or ""
    rule = getattr(result, "selected_rule_id", "") or ""
    if scope == "rule" and rule:
        desc = get_rule_description(rule).check_description.rstrip(".")
        return f"{desc} Only"
    if scope == "item" and item:
        area = get_area(item).area_name
        return f"{area} Only"
    return "All Active Governance Checks"


def _record_label(finding: GovernanceFinding, strategy: str) -> str:
    if strategy == "company_code":
        return blank_display(finding.company_code or finding.key_value or finding.normalized_value)
    if strategy == "agent_number":
        agent = finding.agent_number or finding.key_value
        if agent and finding.company_code:
            return f"{agent} (company {finding.company_code})"
        return blank_display(agent)
    if strategy == "policy_number":
        return blank_display(
            finding.policy_number
            or finding.normalized_policy_number
            or finding.original_policy_number
            or finding.key_value
        )
    if strategy == "group_number":
        return blank_display(
            finding.group_number
            or finding.normalized_group_number
            or finding.key_value
        )
    if strategy == "company_plan":
        if finding.composite_business_key:
            return blank_display(finding.composite_business_key)
        comp = finding.normalized_company_code or finding.company_code
        plan = finding.key_value
        if comp and plan:
            return f"{comp} / {plan}"
        return blank_display(comp or plan)
    if strategy == "plan":
        return blank_display(finding.plan or finding.key_value or finding.normalized_value)
    if strategy == "plan_detail":
        plan = finding.plan or ""
        bits = [plan] if plan else []
        for part in (
            finding.mortality_table,
            finding.eti_mortality_table,
            finding.gender,
            finding.underwriting_class,
            finding.band,
            finding.issue_state,
        ):
            if part and part not in bits:
                bits.append(part)
        if bits:
            return " / ".join(bits)
        if finding.source_record_id:
            return f"Record {finding.source_record_id}"
        return "Blank"
    if strategy == "record_number":
        rid = finding.source_record_id
        if rid and str(rid).strip().isdigit():
            return f"Record {int(rid)}"
        if rid:
            return f"Record {rid}"
        return "Record 1"
    if strategy == "key_value":
        return blank_display(finding.key_value or finding.normalized_value or finding.invalid_value)
    if finding.source_record_id and str(finding.source_record_id).strip().isdigit():
        return f"Record {int(finding.source_record_id)}"
    return blank_display(finding.key_value)


def _current_value(finding: GovernanceFinding) -> str:
    # Prefer the field under review; avoid substituting another identifier (e.g. group #)
    field = (finding.source_field or "").upper()
    if "BILLNAME" in field or field == "MBILLNAME":
        return blank_display(finding.original_billing_name or finding.original_value)
    if field in {"MCOMP", "COMPANY"} or "COMPANY" in field:
        return blank_display(
            finding.original_company_code
            or finding.original_value
            or finding.normalized_company_code
            or finding.invalid_value
        )
    if "POLICY" in field or field == "MPOLICY":
        return blank_display(
            finding.original_policy_number
            or finding.original_value
            or finding.normalized_policy_number
        )
    if field == "EFFDATE" or "DATE" in field:
        if finding.original_value is not None and str(finding.original_value).strip() != "":
            return blank_display(finding.original_value)
        return blank_display(finding.effective_date or finding.normalized_value)
    for candidate in (
        finding.original_value,
        finding.invalid_value,
        finding.normalized_value,
        finding.original_company_code,
        finding.original_billing_name,
        finding.original_policy_number,
        finding.effective_date,
    ):
        if candidate is not None and str(candidate).strip() != "":
            return blank_display(candidate)
    return "Blank"


def _is_incomplete_finding(finding: GovernanceFinding) -> bool:
    if finding.status in (STATUS_ERROR, STATUS_NOT_RUN):
        return True
    cat = (finding.failure_category or "").upper()
    if cat in {
        "MISSING_REFERENCE_TABLE",
        "REFERENCE_TABLE_UNAVAILABLE",
        "MISSING_SOURCE_TABLE",
        "MISSING_FIELD",
    }:
        return True
    msg = finding.message or ""
    if "was not loaded" in msg.lower() or "not found in data region" in msg.lower():
        return True
    if "could not be validated" in msg.lower() and "not available" in msg.lower():
        return True
    return False


def _plain_problem(finding: GovernanceFinding, rule_desc) -> str:
    msg = finding.message or ""
    # Strip technical wrappers
    for pat in _TECHNICAL_PATTERNS:
        if pat.search(msg):
            return _incomplete_problem_text(finding, rule_desc)
    cat = (finding.failure_category or "").upper()
    value = blank_display(
        finding.normalized_value or finding.invalid_value or finding.original_value
    )

    if finding.rule_id == "DG-QUIKLIST-002":
        if value == "Blank" or cat in {"BLANK_VALUE", "NULL_VALUE"}:
            return "The group does not contain a company code."
        if value != "Blank" or "does not exist" in msg.lower() or cat == "MISSING_REFERENCE":
            code = value if value != "Blank" else blank_display(finding.invalid_value)
            return f"Company code {code} was not found in Company Setup."
    if finding.rule_id == "DG-QUIKLIST-004":
        return "The billing sort setting is incorrect."
    if finding.rule_id in {"DG-QUIKCOMP-002", "DG-QUIKCOMP-003", "DG-QUIKACTG-002"}:
        if value != "Blank" or "does not exist" in msg.lower() or cat == "MISSING_REFERENCE":
            code = value if value != "Blank" else blank_display(finding.invalid_value)
            if code != "Blank":
                return f"Company code {code} was not found in Company Setup."
    if finding.rule_id == "DG-PLANVALUES-001" and (
        cat == "MISSING_REFERENCE" or "does not exist" in msg.lower()
    ):
        return f"Mortality table {value} was not found in Mortality Table Setup."
    if finding.rule_id == "DG-PLANVALUES-002" and (
        cat == "MISSING_REFERENCE" or "does not exist" in msg.lower()
    ):
        return f"ETI mortality table {value} was not found in Mortality Table Setup."
    if finding.rule_id == "DG-PLANVALUES-003" and (
        cat == "MISSING_REFERENCE" or "does not exist" in msg.lower()
    ):
        return f"Plan {value} was not found in Plan Setup."
    if finding.rule_id == "DG-PLANVALUES-008":
        if cat == "DATE_AFTER_MAXIMUM":
            max_d = finding.max_allowed_date or "the maximum date for this review"
            return (
                f"The effective date is more than 12 months after the date of this review "
                f"(maximum permitted date is {max_d})."
            )
        if cat == "DATE_BEFORE_MINIMUM":
            return "The effective date is earlier than January 1, 1900."
        if cat in {"INVALID_DATE", "BLANK_VALUE", "NULL_VALUE"}:
            return "The effective date is missing or could not be read."
    if finding.rule_id.startswith("DG-QUIKDATE-00") and finding.rule_id[-1] in "123":
        if finding.expected_prior_month_end and value not in ("Blank", finding.expected_prior_month_end):
            return (
                f"{rule_desc.problem_default.rstrip('.')} "
                f"(found {value}; required {finding.expected_prior_month_end})."
            )
    if cat == "AMBIGUOUS_REFERENCE":
        return (
            f"The value {value} matches more than one setup record and cannot be resolved uniquely."
        )
    if cat in {"BLANK_VALUE", "NULL_VALUE"}:
        return rule_desc.problem_default or "A required value is blank."
    if rule_desc.problem_default:
        # Prefer short default over technical message when message looks technical
        if any(x in msg for x in ("normalized", "DBF", "KeyError", "exists once", "lookup")):
            return rule_desc.problem_default
    # Soften existing business-ish messages
    cleaned = msg
    cleaned = cleaned.replace("QuikQxs", "Mortality Table Setup")
    cleaned = cleaned.replace("QuikPlan", "Plan Setup")
    cleaned = cleaned.replace("QuikPlGd", "Gender Setup")
    cleaned = cleaned.replace("QuikPlUw", "Underwriting Class Setup")
    cleaned = cleaned.replace("QuikPlBd", "Band Setup")
    cleaned = cleaned.replace("QuikComp", "Company Setup")
    return cleaned or rule_desc.problem_default or "This check found a problem."


def _incomplete_problem_text(finding, rule_desc) -> str:
    table = friendly_table_name(
        getattr(finding, "source_table", "") or getattr(finding, "reference_table", "") or ""
    )
    msg = getattr(finding, "message", "") or ""
    msg_l = msg.lower()
    area_check = rule_desc.check_description.rstrip(".")
    if "not found in data region" in msg_l or "required table" in msg_l:
        if table:
            return (
                f"{area_check} could not be completed because the {table} file was not found."
            )
        return f"{area_check} could not be completed because a required file was not found."
    if "was not loaded" in msg_l or "missing_reference_table" in (finding.failure_category or "").lower():
        ref = friendly_table_name(finding.reference_table or finding.source_table or "")
        label = ref or "required setup"
        return (
            f"{area_check} could not be completed because the {label} file was not found."
        )
    if "does not contain field" in msg_l or "missing field" in msg_l:
        return (
            f"{area_check} could not be completed because a required field was not found."
        )
    if "could not be opened" in msg_l or "parsing" in msg_l:
        return (
            f"{area_check} could not be completed because the file could not be opened."
        )
    if "reference table" in msg_l and "not available" in msg_l:
        ref = friendly_table_name(finding.reference_table or "")
        return (
            f"{area_check} could not be completed because "
            f"{ref or 'the required setup file'} was not available."
        )
    return f"{area_check} could not be completed."


def _required_value_text(finding: GovernanceFinding, rule_desc) -> str:
    if finding.rule_id.startswith("DG-QUIKDATE-00") and finding.rule_id[-1] in "123":
        if finding.expected_prior_month_end:
            return finding.expected_prior_month_end
    if finding.rule_id == "DG-PLANVALUES-008" and finding.max_allowed_date:
        return (
            f"A date from January 1, 1900 through {finding.max_allowed_date}"
        )
    if finding.expected_value and str(finding.expected_value).strip():
        return blank_display(finding.expected_value)
    return rule_desc.required_value


def build_attention_rows(result: GovernanceRunResult) -> list[AttentionRow]:
    rows: list[AttentionRow] = []
    seen_data: set[tuple] = set()
    seen_incomplete: set[tuple] = set()

    # Rule-level ERROR/NOT_RUN without flooding from per-row ERROR findings
    for rule in result.rule_results:
        if rule.status not in (STATUS_ERROR, STATUS_NOT_RUN):
            continue
        rule_desc = get_rule_description(rule.rule_id, business_name=rule.business_name)
        # Prefer a single incomplete row from the rule error message
        sample = next(
            (f for f in rule.findings if f.status in (STATUS_ERROR, STATUS_NOT_RUN)),
            None,
        )
        table = ""
        problem = f"{rule_desc.check_description.rstrip('.')} could not be completed."
        if sample:
            table = friendly_table_name(sample.source_table or sample.reference_table or "")
            problem = _incomplete_problem_text(sample, rule_desc)
        elif rule.error_message:
            # Synthesize a minimal finding-like object
            class _F:
                pass

            fake = _F()
            fake.message = rule.error_message
            fake.source_table = ""
            fake.reference_table = ""
            fake.failure_category = ""
            problem = _incomplete_problem_text(fake, rule_desc)  # type: ignore[arg-type]
            # Extract table name hints
            for name in FRIENDLY_TABLE_NAMES:
                if name.lower() in rule.error_message.lower():
                    table = FRIENDLY_TABLE_NAMES[name]
                    break
        key = (rule.rule_id, table, problem)
        if key in seen_incomplete:
            continue
        seen_incomplete.add(key)
        rows.append(
            AttentionRow(
                area=rule_desc.area_name,
                table=table or "Blank",
                record="Blank",
                problem=problem,
                current_value="Blank",
                required_value="Blank",
                type=TYPE_COULD_NOT,
                reference=rule.rule_id,
            )
        )

    for finding in result.findings:
        if finding.status == STATUS_PASS:
            continue
        rule_desc = get_rule_description(finding.rule_id, business_name=finding.business_name)
        if _is_incomplete_finding(finding):
            # Already covered by rule-level incomplete collapse when rule ERROR
            rule_result = next(
                (r for r in result.rule_results if r.rule_id == finding.rule_id),
                None,
            )
            if rule_result and rule_result.status in (STATUS_ERROR, STATUS_NOT_RUN):
                continue
            problem = _incomplete_problem_text(finding, rule_desc)
            table = friendly_table_name(finding.source_table or finding.reference_table or "")
            key = (finding.rule_id, table, problem)
            if key in seen_incomplete:
                continue
            seen_incomplete.add(key)
            rows.append(
                AttentionRow(
                    area=rule_desc.area_name,
                    table=table or "Blank",
                    record="Blank",
                    problem=problem,
                    current_value="Blank",
                    required_value="Blank",
                    type=TYPE_COULD_NOT,
                    reference=finding.rule_id,
                )
            )
            continue

        if finding.status != STATUS_FAIL:
            continue

        problem = _plain_problem(finding, rule_desc)
        record = _record_label(finding, rule_desc.record_strategy)
        table = friendly_table_name(finding.source_table) or finding.source_table or "Blank"
        current = _current_value(finding)
        required = _required_value_text(finding, rule_desc)
        dedupe_key = (
            finding.rule_id,
            finding.source_table,
            finding.source_record_id,
            problem,
            current,
        )
        if dedupe_key in seen_data:
            continue
        seen_data.add(dedupe_key)
        rows.append(
            AttentionRow(
                area=rule_desc.area_name,
                table=table,
                record=record,
                problem=problem,
                current_value=current,
                required_value=required,
                type=TYPE_DATA_PROBLEM,
                reference=finding.rule_id,
            )
        )

    if not rows:
        incomplete = any(
            r.status in (STATUS_ERROR, STATUS_NOT_RUN) for r in result.rule_results
        )
        if incomplete:
            rows.append(
                AttentionRow(
                    area="All Areas",
                    table="Blank",
                    record="Blank",
                    problem=(
                        "No data problems were found, but one or more checks "
                        "could not be completed."
                    ),
                    current_value="Blank",
                    required_value="Blank",
                    type=TYPE_INFORMATION,
                    reference="",
                )
            )
        else:
            rows.append(
                AttentionRow(
                    area="All Areas",
                    table="Blank",
                    record="Blank",
                    problem=(
                        "No data problems were found and all checks completed successfully."
                    ),
                    current_value="Blank",
                    required_value="Blank",
                    type=TYPE_INFORMATION,
                    reference="",
                )
            )

    rows.sort(
        key=lambda r: (
            _TYPE_SORT.get(r.type, 9),
            r.area,
            r.table,
            r.record,
            r.problem,
        )
    )
    return rows


def write_items_needing_attention_csv(result: GovernanceRunResult, path: str) -> list[AttentionRow]:
    rows = build_attention_rows(result)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fieldnames = [
        "Area",
        "Table",
        "Record",
        "Problem",
        "Current Value",
        "Required Value",
        "Type",
        "Reference",
    ]
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "Area": row.area,
                    "Table": "" if row.table == "Blank" else row.table,
                    "Record": "" if row.record == "Blank" else row.record,
                    "Problem": row.problem,
                    "Current Value": "" if row.current_value == "Blank" else row.current_value,
                    "Required Value": "" if row.required_value == "Blank" else row.required_value,
                    "Type": row.type,
                    "Reference": row.reference,
                }
            )
    return rows


def _area_result_label(*, problems: int, incomplete_rules: int) -> str:
    if problems > 0 and incomplete_rules > 0:
        return "Needs Attention (Incomplete)"
    if problems > 0:
        return "Needs Attention"
    if incomplete_rules > 0:
        return "Incomplete"
    return "Passed"


def _areas_in_run(result: GovernanceRunResult) -> list[str]:
    seen: list[str] = []
    for rule in result.rule_results:
        item = rule.governance_item_id
        if item and item not in seen:
            seen.append(item)
    # Stable business order
    def _key(item_id: str) -> tuple[int, str]:
        area = get_area(item_id)
        return (area.sort_order, area.area_name)

    return sorted(seen, key=_key)


def write_what_was_checked_html(result: GovernanceRunResult, path: str) -> BusinessSummary:
    summary = build_business_summary(result)
    attention = build_attention_rows(result)
    problems_by_area: dict[str, int] = {}
    for row in attention:
        if row.type == TYPE_DATA_PROBLEM:
            problems_by_area[row.area] = problems_by_area.get(row.area, 0) + 1

    area_ids = _areas_in_run(result)
    sections: list[str] = []
    table_rows: list[str] = []

    for item_id in area_ids:
        area = get_area(item_id)
        rules = [r for r in result.rule_results if r.governance_item_id == item_id]
        problems = sum(r.failed_count for r in rules)
        incomplete_n = sum(1 for r in rules if r.status in (STATUS_ERROR, STATUS_NOT_RUN))
        result_label = _area_result_label(problems=problems, incomplete_rules=incomplete_n)
        # Prefer summary from area; bullets from rule descriptions
        bullets = []
        for r in rules:
            desc = get_rule_description(r.rule_id, business_name=r.business_name)
            bullets.append(desc.check_description)
        table_rows.append(
            "<tr>"
            f"<td>{html.escape(area.area_name)}</td>"
            f"<td>{html.escape(area.summary_what_checked)}</td>"
            f"<td>{html.escape(result_label)}</td>"
            f"<td>{problems:,}</td>"
            "</tr>"
        )
        incomplete_note = ""
        if incomplete_n:
            incomplete_note = (
                f"<p><strong>Checks that could not be completed:</strong> {incomplete_n}</p>"
            )
        bullet_html = "".join(f"<li>{html.escape(b)}</li>" for b in bullets)
        sections.append(
            f"<h3>{html.escape(area.area_name)}</h3>\n"
            f"<p>We checked that:</p>\n<ul>\n{bullet_html}\n</ul>\n"
            f"<p><strong>Result:</strong> {html.escape(result_label)}</p>\n"
            f"<p><strong>Problems Found:</strong> {problems:,}</p>\n"
            f"{incomplete_note}"
        )

    coverage_block = ""
    if summary.validation_coverage_incomplete:
        coverage_block = (
            "<p><strong>Validation Coverage:</strong> Incomplete</p>\n"
            "<p>All completed record checks passed, but some governance checks "
            "could not be completed.</p>\n"
        )
    warning_block = ""
    if summary.warning:
        warning_block = f"<p class=\"warn\">{html.escape(summary.warning)}</p>\n"

    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Data Governance Review</title>
<style>
body {{ font-family: Georgia, "Times New Roman", serif; color: #222; margin: 2rem; line-height: 1.45; }}
h1, h2, h3 {{ font-family: Arial, Helvetica, sans-serif; font-weight: 600; }}
h1 {{ font-size: 1.6rem; margin-bottom: 0.25rem; }}
h2 {{ font-size: 1.25rem; margin-top: 2rem; border-bottom: 1px solid #ccc; padding-bottom: 0.25rem; }}
h3 {{ font-size: 1.05rem; margin-top: 1.5rem; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #bbb; padding: 0.45rem 0.6rem; text-align: left; vertical-align: top; }}
th {{ background: #f3f3f3; font-family: Arial, Helvetica, sans-serif; }}
.summary dt {{ font-family: Arial, Helvetica, sans-serif; font-weight: 600; margin-top: 0.6rem; }}
.summary dd {{ margin: 0.15rem 0 0 0; }}
.warn {{ color: #6a4b00; }}
@media print {{ body {{ margin: 0.75in; }} }}
</style>
</head>
<body>
<h1>Data Governance Review</h1>
<h2>Executive Summary</h2>
<dl class="summary">
<dt>Overall Result</dt><dd>{html.escape(summary.overall_result)}</dd>
<dt>Percentage Passed</dt><dd>{html.escape(summary.percentage_passed_display)}</dd>
{coverage_block}
<dt>Records Checked</dt><dd>{summary.records_checked:,}</dd>
<dt>Records Passed</dt><dd>{summary.records_passed:,}</dd>
<dt>Problems Found</dt><dd>{summary.problems_found:,}</dd>
<dt>Checks That Could Not Be Completed</dt><dd>{summary.checks_incomplete:,}</dd>
<dt>Review Scope</dt><dd>{html.escape(summary.review_scope)}</dd>
<dt>Run Date</dt><dd>{html.escape(format_business_datetime(result.run_timestamp))}</dd>
<dt>Data Folder</dt><dd>{html.escape(result.data_dir or "")}</dd>
</dl>
{warning_block}
<h2>What We Checked</h2>
<table>
<thead><tr><th>Area</th><th>What We Checked</th><th>Result</th><th>Problems Found</th></tr></thead>
<tbody>
{''.join(table_rows)}
</tbody>
</table>
<h2>Area Details</h2>
{''.join(sections)}
</body>
</html>
"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    return summary


def write_simplified_user_reports(result: GovernanceRunResult, run_folder: str) -> tuple[str, str]:
    html_path = os.path.join(run_folder, "1_What_Was_Checked.html")
    csv_path = os.path.join(run_folder, "2_Items_Needing_Attention.csv")
    write_what_was_checked_html(result, html_path)
    write_items_needing_attention_csv(result, csv_path)
    return html_path, csv_path
