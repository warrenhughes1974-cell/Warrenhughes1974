"""Shared helpers for QuikList governance rules."""

from __future__ import annotations

from data_governance.catalog.governance_items import RuleDefinition
from data_governance.config.settings import TABLE_QUIKLIST
from data_governance.data_access.normalization import normalize_identifier_preserve_zeros
from data_governance.data_access.table_loader import GovernanceDataStore, field_value
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_ERROR


def missing_quiklist_result(
    rule: RuleDefinition,
    store: GovernanceDataStore,
    *,
    run_id: str,
    run_timestamp: str,
    source_field: str,
) -> RuleExecutionResult:
    err = store.load_error(TABLE_QUIKLIST) or f"{TABLE_QUIKLIST} was not loaded."
    result = RuleExecutionResult(
        governance_item_id=rule.governance_item_id,
        rule_id=rule.rule_id,
        rule_name=rule.technical_name,
        business_name=rule.business_name,
        severity=rule.severity,
        status=STATUS_ERROR,
        error_count=1,
        error_message=err,
    )
    result.findings.append(
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
            source_table=TABLE_QUIKLIST,
            source_field=source_field,
            data_region_path=store.data_dir,
            message=err,
            expected_condition="QuikList table available for evaluation",
            actual_condition="Table missing or unreadable",
        )
    )
    return result


def group_label(row: dict) -> tuple[str, str, bool]:
    """Return (normalized_group, original_display, is_null) for messaging."""
    return normalize_identifier_preserve_zeros(field_value(row, "MGROUP"))


def group_display(norm: str | None, is_null: bool) -> str:
    if is_null:
        return "(null)"
    if not norm:
        return "(blank)"
    return norm
