"""Validation companion report and machine-readable manifest."""

from __future__ import annotations

import json
import os

from data_governance.catalog.governance_items import ALL_RULE_DEFINITIONS
from data_governance.catalog.registry import get_registry
from data_governance.models.findings import GovernanceRunResult, RuleExecutionResult
from data_governance.models.statuses import STATUS_ERROR, STATUS_NOT_RUN
from data_governance.reporting.accuracy import ConformanceAccuracy, format_accuracy_short
from data_governance.reporting.executive_summary import format_business_datetime


_PLAIN = {
    "PASS": "PASSED",
    "FAIL": "FAILED",
    "ERROR": "ERROR",
    "NOT_RUN": "NOT RUN",
}


def _split_reference_fields(source_fields: tuple[str, ...], source_tables: tuple[str, ...]):
    """Derive primary vs reference tables/fields from rule metadata."""
    primary = source_tables[0] if source_tables else ""
    reference_tables: list[str] = []
    reference_fields: list[str] = []
    primary_fields: list[str] = []
    for field in source_fields:
        if "." in field:
            table, col = field.split(".", 1)
            if table != primary and table in source_tables:
                if table not in reference_tables:
                    reference_tables.append(table)
                reference_fields.append(f"{table}.{col}")
            else:
                primary_fields.append(field if "." in field else f"{primary}.{field}" if primary else field)
        else:
            primary_fields.append(f"{primary}.{field}" if primary else field)
    for table in source_tables[1:]:
        if table not in reference_tables:
            reference_tables.append(table)
    return primary, primary_fields, reference_tables, reference_fields


_PLANVALUES_LIMITATIONS = {
    "DG-PLANVALUES-001": [
        "This rule confirms that the mortality-table code exists in QuikQxs. "
        "It does not confirm that the mortality table is actuarially appropriate for the plan.",
    ],
    "DG-PLANVALUES-002": [
        "This rule confirms that the ETI mortality-table code exists in QuikQxs. "
        "It does not confirm that the mortality table is actuarially appropriate for the plan.",
    ],
    "DG-PLANVALUES-003": [
        "This rule confirms that the plan code exists in QuikPlan. "
        "It does not confirm that the source rate record belongs to the correct plan.",
    ],
    "DG-PLANVALUES-004": [
        "This rule confirms that the gender code is the approved default or a valid "
        "QuikPlGd setup reference. It does not confirm that the selected code is "
        "appropriate for a particular insured or product.",
    ],
    "DG-PLANVALUES-005": [
        "This rule confirms that the underwriting class is the approved default or a "
        "valid QuikPlUw setup reference. It does not confirm product appropriateness.",
    ],
    "DG-PLANVALUES-006": [
        "This rule confirms that the band is the approved default or a valid QuikPlBd "
        "setup reference (QuikPlVd was not present in the verified CSO region). "
        "It does not confirm product appropriateness.",
    ],
    "DG-PLANVALUES-007": [
        "This rule confirms that the value is '00' or an approved state abbreviation. "
        "It does not confirm that the rate is legally approved for sale in that state.",
    ],
    "DG-PLANVALUES-008": [
        "This rule confirms that the date falls within the approved governance range. "
        "It does not confirm that the date is the correct effective date for the "
        "product or rate filing.",
    ],
}


def _default_limitations(definition) -> list[str]:
    specific = list(_PLANVALUES_LIMITATIONS.get(definition.rule_id, []))
    return specific + [
        "Whether values are factually or actuarially correct beyond this rule's checks.",
        "Fields on the same table that are not listed in this rule.",
        "Business intent that is not encoded in the rule definition.",
        "Whether missing reference data should be created automatically.",
    ]


def _pass_conditions(definition) -> list[str]:
    # Invert failure conditions into positive pass language when possible
    passes = [
        "The record was available for evaluation.",
        "None of the listed failure conditions applied after normalization.",
    ]
    if definition.business_rule:
        passes.insert(0, definition.business_rule)
    return passes


def build_rule_manifest_entry(
    definition,
    rule_result: RuleExecutionResult | None,
    *,
    not_run_reason: str = "",
) -> dict:
    primary, primary_fields, ref_tables, ref_fields = _split_reference_fields(
        definition.source_fields, definition.source_tables
    )
    status = rule_result.status if rule_result else STATUS_NOT_RUN
    records_reviewed = rule_result.records_evaluated if rule_result else 0
    looked_fine = rule_result.passed_count if rule_result else 0
    problems = rule_result.failed_count if rule_result else 0
    reason = not_run_reason
    if rule_result and rule_result.status == STATUS_ERROR and not reason:
        reason = rule_result.error_message or "Processing error or missing required table."
    if rule_result and rule_result.status == STATUS_NOT_RUN and not reason:
        reason = "Rule was selected but marked NOT_RUN."

    metrics = dict(rule_result.summary_metrics) if rule_result else {}
    return {
        "governance_item_id": definition.governance_item_id,
        "rule_id": definition.rule_id,
        "business_name": definition.business_name,
        "technical_name": definition.technical_name,
        "purpose": definition.purpose,
        "severity": definition.severity,
        "source_tables": list(definition.source_tables),
        "source_fields": list(definition.source_fields),
        "primary_table": primary,
        "primary_fields": primary_fields,
        "reference_tables": ref_tables,
        "reference_fields": ref_fields,
        "expected_condition": definition.business_rule,
        "failure_conditions": list(definition.failure_conditions),
        "normalization": definition.business_rule,
        "records_reviewed": records_reviewed,
        "looked_fine": looked_fine,
        "problems_found": problems,
        "result": _PLAIN.get(status, status),
        "execution_status": status,
        "not_run_reason": reason,
        "limitations": _default_limitations(definition),
        "pass_conditions": _pass_conditions(definition),
        "summary_metrics": metrics,
    }


def build_validation_manifest(
    result: GovernanceRunResult,
    accuracy: ConformanceAccuracy,
) -> dict:
    """Manifest reflecting the actual selected rules for this run."""
    registry = get_registry()
    by_id = {r.rule_id: r for r in result.rule_results}
    selected_defs = []
    for rule_id in result.rules_executed:
        if rule_id in registry:
            selected_defs.append(registry[rule_id].definition)
        else:
            # Fall back to catalog definition if present
            for definition in ALL_RULE_DEFINITIONS:
                if definition.rule_id == rule_id:
                    selected_defs.append(definition)
                    break

    rules = [
        build_rule_manifest_entry(definition, by_id.get(definition.rule_id))
        for definition in selected_defs
    ]

    # Catalog rules not selected for this run (item/rule filter)
    selected_ids = {d.rule_id for d in selected_defs}
    excluded = []
    for definition in ALL_RULE_DEFINITIONS:
        if definition.rule_id not in selected_ids:
            excluded.append(
                build_rule_manifest_entry(
                    definition,
                    None,
                    not_run_reason=(
                        "Not selected for this run (full suite not requested, or "
                        "a single governance item/rule filter was applied)."
                    ),
                )
            )

    tables_reviewed = sorted(
        {
            table
            for entry in rules
            for table in entry["source_tables"]
            if entry["execution_status"] not in (STATUS_ERROR, STATUS_NOT_RUN)
            or entry["records_reviewed"] > 0
        }
    )
    # Also include tables named on ERROR rules as required-but-unavailable
    unavailable = sorted(
        {
            table
            for entry in rules
            if entry["execution_status"] == STATUS_ERROR
            for table in entry["source_tables"]
        }
    )

    return {
        "run_id": result.run_id,
        "run_timestamp": result.run_timestamp,
        "data_region_path": result.data_dir,
        "output_path": result.output_dir,
        "overall_result": result.overall_status,
        "data_conformance_accuracy": accuracy.to_dict(),
        "source_opened_read_only": result.source_opened_read_only,
        "source_files_modified": result.source_files_modified,
        "tables_reviewed": tables_reviewed,
        "tables_unavailable_or_errored": unavailable,
        "rules_executed": rules,
        "rules_not_selected": excluded,
        "generated_from": "registered rules selected for this run + RuleExecutionResult counts",
    }


def write_validation_manifest(manifest: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)


def write_validation_guide(
    result: GovernanceRunResult,
    accuracy: ConformanceAccuracy,
    path: str,
    manifest: dict,
) -> None:
    lines: list[str] = []
    lines.append("# QLAdmin Data Governance Validation Guide")
    lines.append("")
    lines.append(
        "This companion document explains exactly what the governance process "
        "validated in this specific run. It is generated from the registered rules "
        "that were selected and from the actual run results."
    )
    lines.append("")

    lines.append("## Run Information")
    lines.append("")
    lines.append("| | |")
    lines.append("|---|---|")
    lines.append(f"| Run ID | `{result.run_id}` |")
    lines.append(f"| Run date and time | {format_business_datetime(result.run_timestamp)} |")
    lines.append(f"| Data-region path | `{result.data_dir}` |")
    lines.append(f"| Output path | `{result.output_dir}` |")
    lines.append(f"| Overall result | {_PLAIN.get(result.overall_status, result.overall_status)} |")
    lines.append(f"| Data Conformance Accuracy | {accuracy.percent_display} |")
    lines.append(
        f"| Source opened read-only | {'Yes' if result.source_opened_read_only else 'No'} |"
    )
    lines.append(
        f"| Source files modified | {'Yes' if result.source_files_modified else 'No'} |"
    )
    lines.append("")
    lines.append(format_accuracy_short(accuracy.percent_display))
    lines.append("")

    lines.append("## What This Run Did")
    lines.append("")
    lines.append(
        "This run reviewed the selected QLAdmin data region against the active "
        "governance rules listed below. It did not change any source data. Each "
        "rule checked a specific table, field, relationship, format, uniqueness "
        "requirement, or expected value."
    )
    lines.append("")

    lines.append("## Tables Reviewed")
    lines.append("")
    tables = manifest.get("tables_reviewed") or []
    if tables:
        for table in tables:
            lines.append(f"- {table}")
    else:
        lines.append("- (No tables completed evaluation in this run.)")
    lines.append("")
    unavailable = manifest.get("tables_unavailable_or_errored") or []
    if unavailable:
        lines.append("### Tables required but unavailable or errored")
        lines.append("")
        for table in unavailable:
            lines.append(f"- {table}")
        lines.append("")

    lines.append("## Validation Rules Executed")
    lines.append("")
    for entry in manifest["rules_executed"]:
        lines.extend(_rule_section_lines(entry))

    incomplete = [
        e
        for e in manifest["rules_executed"]
        if e["execution_status"] in (STATUS_ERROR, STATUS_NOT_RUN)
    ]
    excluded = manifest.get("rules_not_selected") or []
    lines.append("## Rules Not Executed or Not Completed")
    lines.append("")
    if not incomplete and not excluded:
        lines.append("All selected rules completed evaluation.")
        lines.append("")
    else:
        if incomplete:
            lines.append("### Selected rules that did not complete successfully")
            lines.append("")
            for entry in incomplete:
                lines.append(f"- **{entry['rule_id']}** — {entry['business_name']}")
                lines.append(f"  - Status: {entry['result']}")
                lines.append(
                    f"  - Reason: {entry['not_run_reason'] or 'See rule section above.'}"
                )
                lines.append(
                    "  - Unrelated checks continued: Yes (rule failures/errors are isolated)."
                )
            lines.append("")
        if excluded:
            lines.append("### Registered rules not selected for this run")
            lines.append("")
            for entry in excluded:
                lines.append(f"- **{entry['rule_id']}** — {entry['business_name']}")
                lines.append(f"  - Status: NOT SELECTED")
                lines.append(f"  - Reason: {entry['not_run_reason']}")
            lines.append("")

    lines.append("## What This Governance Run Does Not Prove")
    lines.append("")
    lines.append("This run:")
    lines.append("")
    lines.append("- Validates only the currently registered and selected governance rules.")
    lines.append("- Does not guarantee that all QLAdmin data is correct.")
    lines.append("- Does not validate fields for which no rule has been created.")
    lines.append("- Does not confirm actuarial calculations unless a specific actuarial rule exists.")
    lines.append("- Does not confirm business intent beyond the rule definitions.")
    lines.append("- Does not modify or repair source data.")
    lines.append("- Does not replace user acceptance testing.")
    lines.append("- Does not replace reconciliation to an authoritative source system.")
    lines.append(
        "- Does not confirm that an expected default is correct for every client "
        "unless the rule is configured as a universal standard."
    )
    lines.append("")
    lines.append(
        "A high Data Conformance Accuracy percentage means most evaluated records "
        "matched the active governance rules. It does not mean untested data is correct."
    )
    lines.append("")

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines).rstrip() + "\n")


def _rule_section_lines(entry: dict) -> list[str]:
    lines: list[str] = []
    lines.append(f"## {entry['rule_id']} — {entry['business_name']}")
    lines.append("")
    lines.append(f"**Governance item ID:** {entry['governance_item_id']}")
    lines.append("")
    lines.append(f"**Technical name:** {entry['technical_name']}")
    lines.append("")
    lines.append("**Purpose:**")
    lines.append("")
    lines.append(entry["purpose"])
    lines.append("")
    lines.append("**Tables reviewed:**")
    lines.append("")
    for table in entry["source_tables"]:
        lines.append(f"- {table}")
    lines.append("")
    lines.append("**Fields reviewed:**")
    lines.append("")
    for field in entry["source_fields"]:
        lines.append(f"- {field}")
    lines.append("")
    if entry["reference_tables"] or entry["reference_fields"]:
        lines.append("**Reference tables / fields:**")
        lines.append("")
        for table in entry["reference_tables"]:
            lines.append(f"- {table}")
        for field in entry["reference_fields"]:
            lines.append(f"- {field}")
        lines.append("")

    lines.append("**Severity:** " + entry["severity"])
    lines.append("")
    lines.append(f"**Records reviewed:** {entry['records_reviewed']:,}")
    lines.append("")
    lines.append(f"**Records that looked fine:** {entry['looked_fine']:,}")
    lines.append("")
    lines.append(f"**Problems found:** {entry['problems_found']:,}")
    lines.append("")
    lines.append(f"**Result:** {entry['result']}")
    lines.append("")

    metrics = entry.get("summary_metrics") or {}
    if metrics.get("approved_default") not in (None, ""):
        lines.append(f"**Approved default value:** `{metrics['approved_default']}`")
        lines.append("")
    if metrics.get("approved_state_abbreviations"):
        lines.append("**Approved state abbreviations used in this run:**")
        lines.append("")
        lines.append(metrics["approved_state_abbreviations"])
        lines.append("")
    if metrics.get("max_allowed_date"):
        lines.append(
            f"**Effective-date bounds for this run:** "
            f"{metrics.get('min_allowed_date', '')} through "
            f"{metrics.get('max_allowed_date', '')} "
            f"(run date {metrics.get('governance_run_date', '')}; "
            f"{metrics.get('calendar_month_arithmetic', 'calendar-month arithmetic')})"
        )
        lines.append("")
    if metrics.get("source_table_summary"):
        lines.append("**Totals by source table:**")
        lines.append("")
        lines.append(f"`{metrics['source_table_summary']}`")
        lines.append("")

    lines.append("**Exact validation performed:**")
    lines.append("")
    lines.append(entry["expected_condition"] or entry["purpose"])
    lines.append("")
    lines.append("**Normalization / interpretation applied:**")
    lines.append("")
    lines.append(entry["normalization"] or "(See exact validation text above.)")
    lines.append("")

    lines.append("**Conditions that pass:**")
    lines.append("")
    for cond in entry["pass_conditions"]:
        lines.append(f"- {cond}")
    lines.append("")

    lines.append("**Conditions that fail:**")
    lines.append("")
    for cond in entry["failure_conditions"]:
        lines.append(f"- {cond}")
    if not entry["failure_conditions"]:
        lines.append("- (No failure conditions listed in the rule catalog.)")
    lines.append("")

    if entry["not_run_reason"] and entry["execution_status"] in (STATUS_ERROR, STATUS_NOT_RUN):
        lines.append("**Why this rule did not complete:**")
        lines.append("")
        lines.append(entry["not_run_reason"])
        lines.append("")

    lines.append("**What this rule does not validate:**")
    lines.append("")
    for item in entry["limitations"]:
        lines.append(f"- {item}")
    lines.append("")
    return lines
