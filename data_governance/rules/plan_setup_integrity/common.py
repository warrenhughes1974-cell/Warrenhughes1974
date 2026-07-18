"""Shared helpers for DG-QUIKPLAN Plan Setup rules."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Iterator

from data_governance.catalog.governance_items import RuleDefinition
from data_governance.config.settings import TABLE_QUIKPLAN
from data_governance.data_access.normalization import (
    is_null_value,
    normalize_character_casefold,
    normalize_identifier_preserve_zeros,
)
from data_governance.data_access.table_loader import GovernanceDataStore, field_value
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_ERROR, STATUS_FAIL, STATUS_PASS, STATUS_WARN


def trim_plan_code(value: Any) -> tuple[str, str, bool]:
    """Return (normalized_plan, original, is_null)."""
    return normalize_identifier_preserve_zeros(value)


def decode_numeric(value: Any) -> tuple[Decimal | None, str, bool, bool]:
    """Return (decimal_or_none, display, is_null, is_unreadable)."""
    if is_null_value(value):
        return None, "", True, False
    if isinstance(value, bool):
        return None, str(value), False, True
    original = str(value)
    text = original.strip()
    if text == "" or text.lower() in {"none", "null", "nan"}:
        return None, original, False, False
    try:
        return Decimal(text), text, False, False
    except (InvalidOperation, ValueError):
        return None, text, False, True


def decode_logical(value: Any) -> tuple[bool | None, str, bool]:
    """Return (True/False/None invalid, original, is_null)."""
    if is_null_value(value):
        return None, "", True
    original = str(value)
    if isinstance(value, bool):
        return value, original, False
    text = original.strip()
    if text == "" or text.lower() in {"none", "null", "nan"}:
        return None, original, False
    upper, _, _ = normalize_character_casefold(text)
    if upper in {"T", "Y", "1"}:
        return True, original, False
    if upper in {"F", "N", "0"}:
        return False, original, False
    return None, original, False


def iterate_quikplan_rows(store: GovernanceDataStore) -> Iterator[tuple[int, dict]]:
    loaded = store.get(TABLE_QUIKPLAN)
    if loaded is None:
        return
    for idx, row in enumerate(loaded.rows, start=1):
        yield idx, row


def plan_from_row(row: dict) -> tuple[str, str, bool]:
    return trim_plan_code(field_value(row, "PLAN"))


def make_plan_finding(
    *,
    rule: RuleDefinition,
    run_id: str,
    run_timestamp: str,
    data_region_path: str,
    record_id: int,
    plan: str,
    plan_original: str,
    source_field: str,
    message: str,
    status: str,
    failure_category: str = "",
    original_value: str = "",
    normalized_value: str = "",
    expected_condition: str = "",
    reference_table: str = "",
    reference_field: str = "",
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
        status=status,
        source_table=TABLE_QUIKPLAN,
        source_field=source_field,
        source_record_id=str(record_id),
        key_value=plan or plan_original,
        invalid_value=normalized_value or original_value,
        expected_condition=expected_condition,
        actual_condition=message,
        message=message,
        data_region_path=data_region_path,
        original_value=original_value,
        normalized_value=normalized_value,
        failure_category=failure_category,
        plan=plan,
    )


def missing_table_result(
    *,
    rule: RuleDefinition,
    run_id: str,
    run_timestamp: str,
    data_region_path: str,
    table_name: str,
    message: str | None = None,
) -> RuleExecutionResult:
    msg = message or (
        f"{rule.business_name} could not be completed because "
        f"{table_name} was not available."
    )
    result = RuleExecutionResult(
        governance_item_id=rule.governance_item_id,
        rule_id=rule.rule_id,
        rule_name=rule.technical_name,
        business_name=rule.business_name,
        severity=rule.severity,
        status=STATUS_ERROR,
        error_count=1,
        error_message=msg,
        findings=[
            make_finding(
                run_id=run_id,
                run_timestamp=run_timestamp,
                governance_item_id=rule.governance_item_id,
                rule_id=rule.rule_id,
                rule_name=rule.technical_name,
                business_name=rule.business_name,
                description=rule.purpose,
                severity=rule.severity,
                status=STATUS_ERROR,
                source_table=table_name,
                source_field="",
                message=msg,
                data_region_path=data_region_path,
                failure_category="MISSING_REFERENCE_TABLE",
                reference_table=table_name,
                expected_condition=f"{table_name} loaded in data region",
                actual_condition="Table not loaded",
            )
        ],
    )
    return result


def empty_quikplan_result(
    *,
    rule: RuleDefinition,
    run_id: str,
    run_timestamp: str,
    data_region_path: str,
) -> RuleExecutionResult:
    return missing_table_result(
        rule=rule,
        run_id=run_id,
        run_timestamp=run_timestamp,
        data_region_path=data_region_path,
        table_name=TABLE_QUIKPLAN,
        message=(
            f"{rule.business_name} could not be completed because "
            "Plan Setup was not available."
        ),
    )


def classification_unavailable_result(
    *,
    rule: RuleDefinition,
    run_id: str,
    run_timestamp: str,
    data_region_path: str,
) -> RuleExecutionResult:
    msg = (
        f"{rule.business_name} could not be completed because plan "
        "classification is unavailable."
    )
    result = RuleExecutionResult(
        governance_item_id=rule.governance_item_id,
        rule_id=rule.rule_id,
        rule_name=rule.technical_name,
        business_name=rule.business_name,
        severity=rule.severity,
        status=STATUS_ERROR,
        error_count=1,
        error_message=msg,
        findings=[
            make_finding(
                run_id=run_id,
                run_timestamp=run_timestamp,
                governance_item_id=rule.governance_item_id,
                rule_id=rule.rule_id,
                rule_name=rule.technical_name,
                business_name=rule.business_name,
                description=rule.purpose,
                severity=rule.severity,
                status=STATUS_ERROR,
                source_table=TABLE_QUIKPLAN,
                source_field="",
                message=msg,
                data_region_path=data_region_path,
                failure_category="CLASSIFICATION_UNAVAILABLE",
                expected_condition="Plan classification config with confirmed flags",
                actual_condition="Classification unavailable",
            )
        ],
    )
    return result


def finalize_rule_result(result: RuleExecutionResult) -> RuleExecutionResult:
    result.failed_count = len([f for f in result.findings if f.status == STATUS_FAIL])
    result.warn_count = len([f for f in result.findings if f.status == STATUS_WARN])
    error_findings = len([f for f in result.findings if f.status == STATUS_ERROR])
    if result.error_count < error_findings:
        result.error_count = error_findings

    evaluated = int(result.records_evaluated or 0)
    accounted = result.failed_count + result.warn_count
    # Prefer rule-maintained passed_count when multi-finding checks already counted
    # outcomes explicitly; otherwise derive from evaluated - fail/warn.
    if result.passed_count == 0 and evaluated and accounted <= evaluated:
        result.passed_count = evaluated - accounted
    elif result.passed_count == 0 and not result.findings and evaluated:
        result.passed_count = evaluated

    if result.failed_count:
        result.status = STATUS_FAIL
    elif result.error_count or error_findings:
        result.status = STATUS_ERROR
    else:
        result.status = STATUS_PASS
    return result


def plan_starts_with_5(plan: str) -> bool:
    return bool(plan) and plan[0] == "5"


def plan_starts_with_a(plan: str) -> bool:
    return bool(plan) and plan[0].upper() == "A"


def traditional_plan(plan: str) -> bool:
    return bool(plan) and plan[0].isdigit() and plan[0] != "9"


def deficiency_applies(plan: str) -> bool:
    if not plan:
        return False
    first = plan[0].upper()
    return first.isalpha() or first == "9"


def approx_equal_1000(value: Decimal) -> bool:
    return abs(value - Decimal("1000")) <= Decimal("0.01")
