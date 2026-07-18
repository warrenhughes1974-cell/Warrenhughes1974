"""Shared runner for QuikDate prior-month-end bill date rules."""

from __future__ import annotations

from data_governance.catalog.governance_items import RuleDefinition
from data_governance.config.settings import TABLE_QUIKDATE
from data_governance.data_access.normalization import (
    decode_dbf_date,
    format_iso_date,
    parse_governance_run_date,
    prior_month_end,
)
from data_governance.data_access.table_loader import GovernanceDataStore, field_value
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_FAIL, STATUS_PASS
from data_governance.rules.processing_date_integrity.helpers import missing_quikdate_result


def run_prior_month_end_bill_date_rule(
    store: GovernanceDataStore,
    *,
    rule: RuleDefinition,
    source_field: str,
    business_label: str,
    run_id: str,
    run_timestamp: str,
) -> RuleExecutionResult:
    if store.get(TABLE_QUIKDATE) is None:
        return missing_quikdate_result(
            rule, store, run_id=run_id, run_timestamp=run_timestamp, source_field=source_field
        )

    result = RuleExecutionResult(
        governance_item_id=rule.governance_item_id,
        rule_id=rule.rule_id,
        rule_name=rule.technical_name,
        business_name=rule.business_name,
        severity=rule.severity,
        status=STATUS_PASS,
    )
    rows = store.get(TABLE_QUIKDATE).rows
    result.records_evaluated = len(rows)

    run_date = parse_governance_run_date(run_timestamp)
    expected = prior_month_end(run_date)
    expected_iso = format_iso_date(expected)
    run_iso = format_iso_date(run_date)

    match_count = 0
    other_count = 0
    blank_count = 0
    null_count = 0
    unreadable_count = 0

    for idx, row in enumerate(rows, start=1):
        decoded = decode_dbf_date(field_value(row, source_field))

        if decoded.is_null and decoded.date_value is None and not decoded.original_display:
            # Pure null from DBF empty date / None
            null_count += 1
            result.findings.append(
                _bill_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    source_field=source_field,
                    record_id=str(idx),
                    run_iso=run_iso,
                    expected_iso=expected_iso,
                    original="",
                    normalized="",
                    message=(
                        f"The {business_label} date is null. "
                        f"The required date for this run is '{expected_iso}'."
                    ),
                    failure_category="null",
                    actual="Null date",
                )
            )
            continue

        if decoded.is_blank and decoded.date_value is None and not decoded.is_unreadable:
            blank_count += 1
            result.findings.append(
                _bill_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    source_field=source_field,
                    record_id=str(idx),
                    run_iso=run_iso,
                    expected_iso=expected_iso,
                    original=decoded.original_display,
                    normalized="",
                    message=(
                        f"The {business_label} date is blank. "
                        f"The required date for this run is '{expected_iso}'."
                    ),
                    failure_category="blank",
                    actual="Blank date",
                )
            )
            continue

        if decoded.is_unreadable or decoded.date_value is None:
            unreadable_count += 1
            shown = decoded.decoded_display or decoded.original_display or "(unreadable)"
            result.findings.append(
                _bill_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    source_field=source_field,
                    record_id=str(idx),
                    run_iso=run_iso,
                    expected_iso=expected_iso,
                    original=decoded.original_display,
                    normalized=shown,
                    message=(
                        f"The {business_label} date '{shown}' is invalid or unreadable. "
                        f"The required date for this run is '{expected_iso}'."
                    ),
                    failure_category="unreadable",
                    actual="Unreadable date",
                )
            )
            continue

        actual_iso = format_iso_date(decoded.date_value)
        if decoded.date_value != expected:
            other_count += 1
            result.findings.append(
                _bill_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    source_field=source_field,
                    record_id=str(idx),
                    run_iso=run_iso,
                    expected_iso=expected_iso,
                    original=decoded.original_display,
                    normalized=actual_iso,
                    message=(
                        f"The {business_label} date is '{actual_iso}'. "
                        f"The required date for this run is '{expected_iso}'."
                    ),
                    failure_category="wrong_date",
                    actual=f"Date {actual_iso}",
                )
            )
            continue

        match_count += 1

    result.passed_count = match_count
    result.failed_count = len([f for f in result.findings if f.status == STATUS_FAIL])
    result.summary_metrics = {
        "matching_prior_month_end": match_count,
        "other_dates": other_count,
        "blank_dates": blank_count,
        "null_dates": null_count,
        "unreadable_dates": unreadable_count,
        "expected_prior_month_end": expected_iso,
        "governance_run_date": run_iso,
    }
    result.status = STATUS_FAIL if result.failed_count else STATUS_PASS
    return result


def _bill_finding(
    *,
    rule: RuleDefinition,
    run_id: str,
    run_timestamp: str,
    data_region_path: str,
    source_field: str,
    record_id: str,
    run_iso: str,
    expected_iso: str,
    original: str,
    normalized: str,
    message: str,
    failure_category: str,
    actual: str,
):
    return make_finding(
        run_id=run_id,
        run_timestamp=run_timestamp,
        governance_item_id=rule.governance_item_id,
        rule_id=rule.rule_id,
        rule_name=rule.technical_name,
        business_name=rule.business_name,
        description=rule.purpose,
        severity=rule.severity,
        status=STATUS_FAIL,
        source_table=TABLE_QUIKDATE,
        source_field=source_field,
        source_record_id=record_id,
        key_value=normalized or original,
        invalid_value=normalized or original,
        expected_condition=f"Date equals prior month end {expected_iso}",
        actual_condition=actual,
        message=message,
        data_region_path=data_region_path,
        original_value=original,
        normalized_value=normalized,
        expected_value=expected_iso,
        governance_run_date=run_iso,
        controlling_date=run_iso,
        expected_prior_month_end=expected_iso,
        failure_category=failure_category,
    )
