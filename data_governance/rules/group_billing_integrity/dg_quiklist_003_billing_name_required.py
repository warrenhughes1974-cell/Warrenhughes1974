"""DG-QUIKLIST-003 — Group Billing Name Must Be Populated."""

from __future__ import annotations

from data_governance.catalog.governance_items import RULE_DG_QUIKLIST_003
from data_governance.config.settings import TABLE_QUIKLIST
from data_governance.data_access.normalization import normalize_identifier_preserve_zeros
from data_governance.data_access.table_loader import GovernanceDataStore, field_value
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_FAIL, STATUS_PASS
from data_governance.rules.group_billing_integrity.helpers import (
    group_display,
    group_label,
    missing_quiklist_result,
)

RULE = RULE_DG_QUIKLIST_003


def run_dg_quiklist_003(
    store: GovernanceDataStore,
    *,
    run_id: str,
    run_timestamp: str,
) -> RuleExecutionResult:
    if store.get(TABLE_QUIKLIST) is None:
        return missing_quiklist_result(
            RULE, store, run_id=run_id, run_timestamp=run_timestamp, source_field="MBILLNAME"
        )

    result = RuleExecutionResult(
        governance_item_id=RULE.governance_item_id,
        rule_id=RULE.rule_id,
        rule_name=RULE.technical_name,
        business_name=RULE.business_name,
        severity=RULE.severity,
        status=STATUS_PASS,
    )
    rows = store.get(TABLE_QUIKLIST).rows
    result.records_evaluated = len(rows)

    populated = 0
    blank_count = 0
    null_count = 0

    for idx, row in enumerate(rows, start=1):
        raw = field_value(row, "MBILLNAME")
        normalized, original, is_null = normalize_identifier_preserve_zeros(raw)
        g_norm, g_orig, g_null = group_label(row)
        g_label = group_display(g_norm, g_null)

        if is_null:
            null_count += 1
            result.findings.append(
                _finding(
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=str(idx),
                    group_number=g_norm or "",
                    original_group=g_orig,
                    original_name="",
                    normalized_name="",
                    message=(
                        f"Group number '{g_label}' does not contain a group billing name "
                        f"in MBILLNAME."
                    ),
                    actual="Null billing name",
                )
            )
            continue

        if normalized == "":
            blank_count += 1
            result.findings.append(
                _finding(
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=str(idx),
                    group_number=g_norm or "",
                    original_group=g_orig,
                    original_name=original,
                    normalized_name="",
                    message=(
                        f"Group number '{g_label}' does not contain a group billing name "
                        f"in MBILLNAME."
                    ),
                    actual="Blank billing name",
                )
            )
            continue

        populated += 1

    result.passed_count = populated
    result.failed_count = len([f for f in result.findings if f.status == STATUS_FAIL])
    result.summary_metrics = {
        "populated_billing_names": populated,
        "blank_billing_names": blank_count,
        "null_billing_names": null_count,
    }
    result.status = STATUS_FAIL if result.failed_count else STATUS_PASS
    return result


def _finding(
    *,
    run_id: str,
    run_timestamp: str,
    data_region_path: str,
    record_id: str,
    group_number: str,
    original_group: str,
    original_name: str,
    normalized_name: str,
    message: str,
    actual: str,
):
    return make_finding(
        run_id=run_id,
        run_timestamp=run_timestamp,
        governance_item_id=RULE.governance_item_id,
        rule_id=RULE.rule_id,
        rule_name=RULE.technical_name,
        business_name=RULE.business_name,
        description=RULE.purpose,
        severity=RULE.severity,
        status=STATUS_FAIL,
        source_table=TABLE_QUIKLIST,
        source_field="MBILLNAME",
        source_record_id=record_id,
        key_value=group_number,
        invalid_value=normalized_name or original_name,
        expected_condition="MBILLNAME populated after trim",
        actual_condition=actual,
        message=message,
        data_region_path=data_region_path,
        group_number=group_number,
        original_group_number=original_group,
        normalized_group_number=group_number,
        original_billing_name=original_name,
        normalized_billing_name=normalized_name,
    )
