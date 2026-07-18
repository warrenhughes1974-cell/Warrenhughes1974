"""Standard finding and run result models for QLAdmin Data Governance."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from data_governance.models.statuses import (
    OVERALL_ERROR,
    OVERALL_FAIL,
    OVERALL_NOT_RUN,
    OVERALL_PASS,
    STATUS_ERROR,
    STATUS_FAIL,
    STATUS_NOT_RUN,
    STATUS_PASS,
)


@dataclass
class GovernanceFinding:
    """One detailed finding row (failures and processing errors only)."""

    governance_item_id: str
    rule_id: str
    rule_name: str
    business_name: str
    description: str
    severity: str
    status: str
    source_table: str
    source_field: str
    source_record_id: str
    key_value: str
    invalid_value: str
    expected_condition: str
    actual_condition: str
    message: str
    run_id: str
    run_timestamp: str
    data_region_path: str = ""
    # Optional enrichment columns (present when applicable)
    company_code: str = ""
    agent_number: str = ""
    agent_name: str = ""
    policy_number: str = ""
    duplicate_count: str = ""
    original_policy_number: str = ""
    normalized_policy_number: str = ""
    policy_number_length: str = ""
    min_permitted_length: str = ""
    max_permitted_length: str = ""
    # Accounting / composite-key enrichment
    company_code_source_field: str = ""
    account_number_source_field: str = ""
    original_company_code: str = ""
    normalized_company_code: str = ""
    original_account_number: str = ""
    normalized_account_number: str = ""
    composite_business_key: str = ""
    reference_table: str = ""
    reference_field: str = ""
    reference_match_count: str = ""
    # QuikList / group-billing enrichment
    group_number: str = ""
    original_group_number: str = ""
    normalized_group_number: str = ""
    original_billing_name: str = ""
    normalized_billing_name: str = ""
    original_value: str = ""
    normalized_value: str = ""
    expected_value: str = ""
    # QuikDate / processing-date enrichment
    governance_run_date: str = ""
    controlling_date: str = ""
    expected_prior_month_end: str = ""
    failure_category: str = ""
    # Plan-value enrichment
    plan: str = ""
    mortality_table: str = ""
    eti_mortality_table: str = ""
    gender: str = ""
    underwriting_class: str = ""
    band: str = ""
    issue_state: str = ""
    effective_date: str = ""
    min_allowed_date: str = ""
    max_allowed_date: str = ""

    def to_row(self) -> dict[str, str]:
        return {k: "" if v is None else str(v) for k, v in asdict(self).items()}


@dataclass
class RuleExecutionResult:
    """Per-rule execution outcome with summary counts (no PASS detail rows)."""

    governance_item_id: str
    rule_id: str
    rule_name: str
    business_name: str
    severity: str
    status: str
    records_evaluated: int = 0
    passed_count: int = 0
    failed_count: int = 0
    error_count: int = 0
    findings: list[GovernanceFinding] = field(default_factory=list)
    error_message: str = ""
    # Optional rule-specific metrics (e.g. short/long/blank/null counts)
    summary_metrics: dict[str, Any] = field(default_factory=dict)

    def to_summary_row(self, run_id: str, run_timestamp: str) -> dict[str, str]:
        row = {
            "run_id": run_id,
            "run_timestamp": run_timestamp,
            "governance_item_id": self.governance_item_id,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "business_name": self.business_name,
            "severity": self.severity,
            "status": self.status,
            "records_evaluated": str(self.records_evaluated),
            "passed_count": str(self.passed_count),
            "failed_count": str(self.failed_count),
            "error_count": str(self.error_count),
            "error_message": self.error_message,
            "records_shorter_than_4": str(self.summary_metrics.get("records_shorter_than_4", "")),
            "records_longer_than_11": str(self.summary_metrics.get("records_longer_than_11", "")),
            "blank_policy_numbers": str(self.summary_metrics.get("blank_policy_numbers", "")),
            "null_policy_numbers": str(self.summary_metrics.get("null_policy_numbers", "")),
            "distinct_company_codes": str(self.summary_metrics.get("distinct_company_codes", "")),
            "distinct_account_numbers": str(self.summary_metrics.get("distinct_account_numbers", "")),
            "distinct_company_account_combinations": str(
                self.summary_metrics.get("distinct_company_account_combinations", "")
            ),
            "duplicate_combinations": str(self.summary_metrics.get("duplicate_combinations", "")),
            "records_involved_in_duplicates": str(
                self.summary_metrics.get("records_involved_in_duplicates", "")
            ),
            "blank_company_codes": str(self.summary_metrics.get("blank_company_codes", "")),
            "null_company_codes": str(self.summary_metrics.get("null_company_codes", "")),
            "blank_account_numbers": str(self.summary_metrics.get("blank_account_numbers", "")),
            "null_account_numbers": str(self.summary_metrics.get("null_account_numbers", "")),
            "valid_company_references": str(self.summary_metrics.get("valid_company_references", "")),
            "missing_company_references": str(
                self.summary_metrics.get("missing_company_references", "")
            ),
            "blank_company_references": str(self.summary_metrics.get("blank_company_references", "")),
            "null_company_references": str(self.summary_metrics.get("null_company_references", "")),
            "references_to_duplicated_quikcomp": str(
                self.summary_metrics.get("references_to_duplicated_quikcomp", "")
            ),
            "distinct_group_numbers": str(self.summary_metrics.get("distinct_group_numbers", "")),
            "duplicate_group_numbers": str(self.summary_metrics.get("duplicate_group_numbers", "")),
            "blank_group_numbers": str(self.summary_metrics.get("blank_group_numbers", "")),
            "null_group_numbers": str(self.summary_metrics.get("null_group_numbers", "")),
            "populated_billing_names": str(self.summary_metrics.get("populated_billing_names", "")),
            "blank_billing_names": str(self.summary_metrics.get("blank_billing_names", "")),
            "null_billing_names": str(self.summary_metrics.get("null_billing_names", "")),
            "records_matching_expected_value": str(
                self.summary_metrics.get("records_matching_expected_value", "")
            ),
            "records_with_other_value": str(
                self.summary_metrics.get("records_with_other_value", "")
            ),
            "blank_values": str(self.summary_metrics.get("blank_values", "")),
            "null_values": str(self.summary_metrics.get("null_values", "")),
            "unreadable_values": str(self.summary_metrics.get("unreadable_values", "")),
            "matching_prior_month_end": str(
                self.summary_metrics.get("matching_prior_month_end", "")
            ),
            "other_dates": str(self.summary_metrics.get("other_dates", "")),
            "blank_dates": str(self.summary_metrics.get("blank_dates", "")),
            "null_dates": str(self.summary_metrics.get("null_dates", "")),
            "unreadable_dates": str(self.summary_metrics.get("unreadable_dates", "")),
            "blank_escdate_values": str(self.summary_metrics.get("blank_escdate_values", "")),
            "populated_escdate_values": str(
                self.summary_metrics.get("populated_escdate_values", "")
            ),
            "valid_defaults": str(self.summary_metrics.get("valid_defaults", "")),
            "valid_reference_matches": str(
                self.summary_metrics.get("valid_reference_matches", "")
            ),
            "missing_references": str(self.summary_metrics.get("missing_references", "")),
            "ambiguous_references": str(self.summary_metrics.get("ambiguous_references", "")),
            "records_using_00": str(self.summary_metrics.get("records_using_00", "")),
            "records_using_valid_states": str(
                self.summary_metrics.get("records_using_valid_states", "")
            ),
            "invalid_state_codes": str(self.summary_metrics.get("invalid_state_codes", "")),
            "dates_within_range": str(self.summary_metrics.get("dates_within_range", "")),
            "dates_before_minimum": str(self.summary_metrics.get("dates_before_minimum", "")),
            "dates_after_maximum": str(self.summary_metrics.get("dates_after_maximum", "")),
            "min_allowed_date": str(self.summary_metrics.get("min_allowed_date", "")),
            "max_allowed_date": str(self.summary_metrics.get("max_allowed_date", "")),
            "governance_run_date": str(self.summary_metrics.get("governance_run_date", "")),
            "approved_default": str(self.summary_metrics.get("approved_default", "")),
            "approved_state_abbreviations": str(
                self.summary_metrics.get("approved_state_abbreviations", "")
            ),
            "source_table_summary": str(self.summary_metrics.get("source_table_summary", "")),
        }
        return row


@dataclass
class GovernanceRunResult:
    """Full governance run: summaries + detailed findings + output paths."""

    run_id: str
    run_timestamp: str
    data_dir: str
    output_dir: str
    output_base: str = ""
    rules_executed: list[str] = field(default_factory=list)
    rule_results: list[RuleExecutionResult] = field(default_factory=list)
    findings: list[GovernanceFinding] = field(default_factory=list)
    records_evaluated: int = 0
    passed_count: int = 0
    failed_count: int = 0
    error_count: int = 0
    overall_status: str = OVERALL_NOT_RUN
    # User-facing reports
    what_was_checked_path: str = ""
    items_needing_attention_path: str = ""
    # Internal technical paths (under internal/)
    results_csv_path: str = ""
    findings_csv_path: str = ""
    summary_csv_path: str = ""
    report_md_path: str = ""
    validation_guide_path: str = ""
    validation_manifest_path: str = ""
    run_log_path: str = ""
    source_opened_read_only: bool = True
    source_files_modified: bool = False
    # Selection scope for Report 1
    review_scope: str = "all"  # all | item | rule
    selected_governance_item_id: str = ""
    selected_rule_id: str = ""
    # Reporting metrics (attached after finalize / during report write)
    data_conformance_accuracy_percent: float | None = None
    data_conformance_accuracy_display: str = ""
    report_warnings: list[str] = field(default_factory=list)
    business_overall_result: str = ""
    checks_incomplete_count: int = 0

    def finalize(self) -> None:
        self.records_evaluated = sum(r.records_evaluated for r in self.rule_results)
        self.passed_count = sum(r.passed_count for r in self.rule_results)
        self.failed_count = sum(r.failed_count for r in self.rule_results)
        self.error_count = sum(r.error_count for r in self.rule_results)
        self.findings = [f for r in self.rule_results for f in r.findings]
        self.rules_executed = [r.rule_id for r in self.rule_results]

        if not self.rule_results:
            self.overall_status = OVERALL_NOT_RUN
        elif any(r.status == STATUS_ERROR for r in self.rule_results):
            # Prefer FAIL over ERROR when both exist so data issues surface clearly
            if any(r.status == STATUS_FAIL for r in self.rule_results):
                self.overall_status = OVERALL_FAIL
            else:
                self.overall_status = OVERALL_ERROR
        elif any(r.status == STATUS_FAIL for r in self.rule_results):
            self.overall_status = OVERALL_FAIL
        elif all(r.status == STATUS_PASS for r in self.rule_results):
            self.overall_status = OVERALL_PASS
        else:
            # Mix of PASS and NOT_RUN
            if any(r.status == STATUS_PASS for r in self.rule_results):
                self.overall_status = OVERALL_PASS
            else:
                self.overall_status = OVERALL_NOT_RUN

    def to_run_summary(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "run_timestamp": self.run_timestamp,
            "data_region_path": self.data_dir,
            "data_dir": self.data_dir,
            "output_base": self.output_base,
            "output_dir": self.output_dir,
            "rules_executed": list(self.rules_executed),
            "records_evaluated": self.records_evaluated,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "error_count": self.error_count,
            "Records_Reviewed": self.records_evaluated,
            "Looked_Fine": self.passed_count,
            "Problems_Found": self.failed_count,
            "Data_Conformance_Accuracy_Percent": self.data_conformance_accuracy_percent,
            "Data_Conformance_Accuracy_Display": self.data_conformance_accuracy_display,
            "overall_status": self.overall_status,
            "source_opened_read_only": self.source_opened_read_only,
            "source_files_modified": self.source_files_modified,
            "what_was_checked_path": self.what_was_checked_path,
            "items_needing_attention_path": self.items_needing_attention_path,
            "results_csv_path": self.results_csv_path,
            "findings_csv_path": self.findings_csv_path,
            "summary_csv_path": self.summary_csv_path,
            "report_md_path": self.report_md_path,
            "validation_guide_path": self.validation_guide_path,
            "validation_manifest_path": self.validation_manifest_path,
            "review_scope": self.review_scope,
            "selected_governance_item_id": self.selected_governance_item_id,
            "selected_rule_id": self.selected_rule_id,
            "business_overall_result": self.business_overall_result,
            "checks_incomplete_count": self.checks_incomplete_count,
            "Validation_Guide_File": (
                os.path.basename(self.validation_guide_path)
                if self.validation_guide_path
                else ""
            ),
            "Validation_Manifest_File": (
                os.path.basename(self.validation_manifest_path)
                if self.validation_manifest_path
                else ""
            ),
            "run_log_path": self.run_log_path,
            "report_warnings": list(self.report_warnings),
        }


def new_run_id(now: datetime | None = None) -> tuple[str, str]:
    current = now or datetime.now()
    stamp = current.strftime("%Y%m%d_%H%M%S")
    # Microseconds keep concurrent / back-to-back runs isolated
    micros = current.strftime("%f")
    return f"DG-{stamp}_{micros}", current.strftime("%Y-%m-%d %H:%M:%S")


def make_finding(
    *,
    run_id: str,
    run_timestamp: str,
    governance_item_id: str,
    rule_id: str,
    rule_name: str,
    business_name: str,
    description: str,
    severity: str,
    status: str,
    source_table: str,
    source_field: str,
    message: str,
    source_record_id: str = "",
    key_value: str = "",
    invalid_value: str = "",
    expected_condition: str = "",
    actual_condition: str = "",
    data_region_path: str = "",
    company_code: str = "",
    agent_number: str = "",
    agent_name: str = "",
    policy_number: str = "",
    duplicate_count: str = "",
    original_policy_number: str = "",
    normalized_policy_number: str = "",
    policy_number_length: str = "",
    min_permitted_length: str = "",
    max_permitted_length: str = "",
    company_code_source_field: str = "",
    account_number_source_field: str = "",
    original_company_code: str = "",
    normalized_company_code: str = "",
    original_account_number: str = "",
    normalized_account_number: str = "",
    composite_business_key: str = "",
    reference_table: str = "",
    reference_field: str = "",
    reference_match_count: str = "",
    group_number: str = "",
    original_group_number: str = "",
    normalized_group_number: str = "",
    original_billing_name: str = "",
    normalized_billing_name: str = "",
    original_value: str = "",
    normalized_value: str = "",
    expected_value: str = "",
    governance_run_date: str = "",
    controlling_date: str = "",
    expected_prior_month_end: str = "",
    failure_category: str = "",
    plan: str = "",
    mortality_table: str = "",
    eti_mortality_table: str = "",
    gender: str = "",
    underwriting_class: str = "",
    band: str = "",
    issue_state: str = "",
    effective_date: str = "",
    min_allowed_date: str = "",
    max_allowed_date: str = "",
) -> GovernanceFinding:
    return GovernanceFinding(
        governance_item_id=governance_item_id,
        rule_id=rule_id,
        rule_name=rule_name,
        business_name=business_name,
        description=description,
        severity=severity,
        status=status,
        source_table=source_table,
        source_field=source_field,
        source_record_id=source_record_id,
        key_value=key_value,
        invalid_value=invalid_value,
        expected_condition=expected_condition,
        actual_condition=actual_condition,
        message=message,
        run_id=run_id,
        run_timestamp=run_timestamp,
        data_region_path=data_region_path,
        company_code=company_code,
        agent_number=agent_number,
        agent_name=agent_name,
        policy_number=policy_number,
        duplicate_count=duplicate_count,
        original_policy_number=original_policy_number,
        normalized_policy_number=normalized_policy_number,
        policy_number_length=policy_number_length,
        min_permitted_length=min_permitted_length,
        max_permitted_length=max_permitted_length,
        company_code_source_field=company_code_source_field,
        account_number_source_field=account_number_source_field,
        original_company_code=original_company_code,
        normalized_company_code=normalized_company_code,
        original_account_number=original_account_number,
        normalized_account_number=normalized_account_number,
        composite_business_key=composite_business_key,
        reference_table=reference_table,
        reference_field=reference_field,
        reference_match_count=reference_match_count,
        group_number=group_number,
        original_group_number=original_group_number,
        normalized_group_number=normalized_group_number,
        original_billing_name=original_billing_name,
        normalized_billing_name=normalized_billing_name,
        original_value=original_value,
        normalized_value=normalized_value,
        expected_value=expected_value,
        governance_run_date=governance_run_date,
        controlling_date=controlling_date,
        expected_prior_month_end=expected_prior_month_end,
        failure_category=failure_category,
        plan=plan,
        mortality_table=mortality_table,
        eti_mortality_table=eti_mortality_table,
        gender=gender,
        underwriting_class=underwriting_class,
        band=band,
        issue_state=issue_state,
        effective_date=effective_date,
        min_allowed_date=min_allowed_date,
        max_allowed_date=max_allowed_date,
    )


def empty_rule_result(
    *,
    governance_item_id: str,
    rule_id: str,
    rule_name: str,
    business_name: str,
    severity: str,
    status: str = STATUS_NOT_RUN,
) -> RuleExecutionResult:
    return RuleExecutionResult(
        governance_item_id=governance_item_id,
        rule_id=rule_id,
        rule_name=rule_name,
        business_name=business_name,
        severity=severity,
        status=status,
    )
