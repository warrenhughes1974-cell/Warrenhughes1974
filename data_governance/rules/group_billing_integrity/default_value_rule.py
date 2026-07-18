"""Shared runners for QuikList character and numeric default-value rules."""

from __future__ import annotations

from data_governance.catalog.governance_items import RuleDefinition
from data_governance.config.settings import TABLE_QUIKLIST
from data_governance.data_access.normalization import (
    decode_numeric_zero,
    normalize_character_casefold,
)
from data_governance.data_access.table_loader import GovernanceDataStore, field_value
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_FAIL, STATUS_PASS
from data_governance.rules.group_billing_integrity.helpers import (
    group_display,
    group_label,
    missing_quiklist_result,
)


def run_character_default_rule(
    store: GovernanceDataStore,
    *,
    rule: RuleDefinition,
    source_field: str,
    expected: str,
    run_id: str,
    run_timestamp: str,
) -> RuleExecutionResult:
    if store.get(TABLE_QUIKLIST) is None:
        return missing_quiklist_result(
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
    rows = store.get(TABLE_QUIKLIST).rows
    result.records_evaluated = len(rows)

    match_count = 0
    other_count = 0
    blank_count = 0
    null_count = 0
    expected_upper = expected.upper()

    for idx, row in enumerate(rows, start=1):
        raw = field_value(row, source_field)
        norm, original, is_null = normalize_character_casefold(raw)
        g_norm, g_orig, g_null = group_label(row)
        g_label = group_display(g_norm, g_null)

        if is_null:
            null_count += 1
            result.findings.append(
                _default_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    source_field=source_field,
                    record_id=str(idx),
                    group_number=g_norm or "",
                    original_group=g_orig,
                    normalized_group=g_norm or "",
                    original_value=original,
                    normalized_value="",
                    expected_value=expected_upper,
                    message=(
                        f"Group number '{g_label}' has {source_field}=(null). "
                        f"The required governance value is '{expected_upper}'."
                    ),
                    actual="Null value",
                )
            )
            continue

        if norm == "":
            blank_count += 1
            result.findings.append(
                _default_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    source_field=source_field,
                    record_id=str(idx),
                    group_number=g_norm or "",
                    original_group=g_orig,
                    normalized_group=g_norm or "",
                    original_value=original,
                    normalized_value="",
                    expected_value=expected_upper,
                    message=(
                        f"Group number '{g_label}' has {source_field}=(blank). "
                        f"The required governance value is '{expected_upper}'."
                    ),
                    actual="Blank value",
                )
            )
            continue

        if norm != expected_upper:
            other_count += 1
            result.findings.append(
                _default_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    source_field=source_field,
                    record_id=str(idx),
                    group_number=g_norm or "",
                    original_group=g_orig,
                    normalized_group=g_norm or "",
                    original_value=original,
                    normalized_value=norm,
                    expected_value=expected_upper,
                    message=(
                        f"Group number '{g_label}' has {source_field}='{norm}'. "
                        f"The required governance value is '{expected_upper}'."
                    ),
                    actual=f"Value '{norm}'",
                )
            )
            continue

        match_count += 1

    result.passed_count = match_count
    result.failed_count = len([f for f in result.findings if f.status == STATUS_FAIL])
    result.summary_metrics = {
        "records_matching_expected_value": match_count,
        "records_with_other_value": other_count,
        "blank_values": blank_count,
        "null_values": null_count,
        "unreadable_values": 0,
    }
    result.status = STATUS_FAIL if result.failed_count else STATUS_PASS
    return result


def run_numeric_zero_default_rule(
    store: GovernanceDataStore,
    *,
    rule: RuleDefinition,
    source_field: str,
    run_id: str,
    run_timestamp: str,
) -> RuleExecutionResult:
    if store.get(TABLE_QUIKLIST) is None:
        return missing_quiklist_result(
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
    rows = store.get(TABLE_QUIKLIST).rows
    result.records_evaluated = len(rows)

    match_count = 0
    other_count = 0
    blank_count = 0
    null_count = 0
    unreadable_count = 0

    for idx, row in enumerate(rows, start=1):
        decoded = decode_numeric_zero(field_value(row, source_field))
        g_norm, g_orig, g_null = group_label(row)
        g_label = group_display(g_norm, g_null)

        if decoded.is_null:
            null_count += 1
            result.findings.append(
                _default_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    source_field=source_field,
                    record_id=str(idx),
                    group_number=g_norm or "",
                    original_group=g_orig,
                    normalized_group=g_norm or "",
                    original_value="",
                    normalized_value="",
                    expected_value="0",
                    message=(
                        f"Group number '{g_label}' has {source_field}=(null). "
                        f"The required governance value is 0."
                    ),
                    actual="Null value",
                )
            )
            continue

        if decoded.is_blank:
            blank_count += 1
            result.findings.append(
                _default_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    source_field=source_field,
                    record_id=str(idx),
                    group_number=g_norm or "",
                    original_group=g_orig,
                    normalized_group=g_norm or "",
                    original_value=decoded.original_display,
                    normalized_value="",
                    expected_value="0",
                    message=(
                        f"Group number '{g_label}' has {source_field}=(blank). "
                        f"The required governance value is 0."
                    ),
                    actual="Blank value",
                )
            )
            continue

        if decoded.is_unreadable:
            unreadable_count += 1
            result.findings.append(
                _default_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    source_field=source_field,
                    record_id=str(idx),
                    group_number=g_norm or "",
                    original_group=g_orig,
                    normalized_group=g_norm or "",
                    original_value=decoded.original_display,
                    normalized_value=decoded.decoded_display,
                    expected_value="0",
                    message=(
                        f"Group number '{g_label}' has {source_field}="
                        f"'{decoded.decoded_display}'. The required governance value is 0."
                    ),
                    actual="Unreadable value",
                )
            )
            continue

        if not decoded.is_zero:
            other_count += 1
            shown = decoded.decoded_display or decoded.original_display.strip()
            result.findings.append(
                _default_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    source_field=source_field,
                    record_id=str(idx),
                    group_number=g_norm or "",
                    original_group=g_orig,
                    normalized_group=g_norm or "",
                    original_value=decoded.original_display,
                    normalized_value=shown,
                    expected_value="0",
                    message=(
                        f"Group number '{g_label}' has {source_field}='{shown}'. "
                        f"The required governance value is 0."
                    ),
                    actual=f"Value '{shown}'",
                )
            )
            continue

        match_count += 1

    result.passed_count = match_count
    result.failed_count = len([f for f in result.findings if f.status == STATUS_FAIL])
    result.summary_metrics = {
        "records_matching_expected_value": match_count,
        "records_with_other_value": other_count,
        "blank_values": blank_count,
        "null_values": null_count,
        "unreadable_values": unreadable_count,
    }
    result.status = STATUS_FAIL if result.failed_count else STATUS_PASS
    return result


def _default_finding(
    *,
    rule: RuleDefinition,
    run_id: str,
    run_timestamp: str,
    data_region_path: str,
    source_field: str,
    record_id: str,
    group_number: str,
    original_group: str,
    normalized_group: str,
    original_value: str,
    normalized_value: str,
    expected_value: str,
    message: str,
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
        source_table=TABLE_QUIKLIST,
        source_field=source_field,
        source_record_id=record_id,
        key_value=group_number or normalized_value,
        invalid_value=normalized_value or original_value,
        expected_condition=f"{source_field} equals {expected_value}",
        actual_condition=actual,
        message=message,
        data_region_path=data_region_path,
        group_number=group_number,
        original_group_number=original_group,
        normalized_group_number=normalized_group,
        original_value=original_value,
        normalized_value=normalized_value,
        expected_value=expected_value,
    )
