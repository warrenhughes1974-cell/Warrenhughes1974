"""DG-QUIKDATE-004 — ACHFILEID Must Equal 0."""

from __future__ import annotations

from data_governance.catalog.governance_items import RULE_DG_QUIKDATE_004
from data_governance.config.settings import QUIKDATE_ACHFILEID_FIELD, TABLE_QUIKDATE
from data_governance.data_access.normalization import (
    decode_numeric_zero,
    format_iso_date,
    parse_governance_run_date,
)
from data_governance.data_access.table_loader import GovernanceDataStore, field_value
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_FAIL, STATUS_PASS
from data_governance.rules.processing_date_integrity.helpers import missing_quikdate_result

RULE = RULE_DG_QUIKDATE_004
FIELD = QUIKDATE_ACHFILEID_FIELD


def run_dg_quikdate_004(
    store: GovernanceDataStore,
    *,
    run_id: str,
    run_timestamp: str,
) -> RuleExecutionResult:
    if store.get(TABLE_QUIKDATE) is None:
        return missing_quikdate_result(
            RULE, store, run_id=run_id, run_timestamp=run_timestamp, source_field=FIELD
        )

    result = RuleExecutionResult(
        governance_item_id=RULE.governance_item_id,
        rule_id=RULE.rule_id,
        rule_name=RULE.technical_name,
        business_name=RULE.business_name,
        severity=RULE.severity,
        status=STATUS_PASS,
    )
    rows = store.get(TABLE_QUIKDATE).rows
    result.records_evaluated = len(rows)
    run_iso = format_iso_date(parse_governance_run_date(run_timestamp))

    match_count = other = blank = null = unreadable = 0
    for idx, row in enumerate(rows, start=1):
        decoded = decode_numeric_zero(field_value(row, FIELD))
        if decoded.is_null:
            null += 1
            result.findings.append(
                _finding(
                    run_id,
                    run_timestamp,
                    store.data_dir,
                    idx,
                    run_iso,
                    "",
                    "",
                    "ACHFILEID contains a null value. The required governance value is 0.",
                    "null",
                )
            )
            continue
        if decoded.is_blank:
            blank += 1
            result.findings.append(
                _finding(
                    run_id,
                    run_timestamp,
                    store.data_dir,
                    idx,
                    run_iso,
                    decoded.original_display,
                    "",
                    "ACHFILEID contains a blank value. The required governance value is 0.",
                    "blank",
                )
            )
            continue
        if decoded.is_unreadable:
            unreadable += 1
            shown = decoded.decoded_display or decoded.original_display
            result.findings.append(
                _finding(
                    run_id,
                    run_timestamp,
                    store.data_dir,
                    idx,
                    run_iso,
                    decoded.original_display,
                    shown,
                    f"ACHFILEID contains '{shown}'. The required governance value is 0.",
                    "unreadable",
                )
            )
            continue
        if not decoded.is_zero:
            other += 1
            shown = decoded.decoded_display or decoded.original_display.strip()
            result.findings.append(
                _finding(
                    run_id,
                    run_timestamp,
                    store.data_dir,
                    idx,
                    run_iso,
                    decoded.original_display,
                    shown,
                    f"ACHFILEID contains '{shown}'. The required governance value is 0.",
                    "wrong_value",
                )
            )
            continue
        match_count += 1

    result.passed_count = match_count
    result.failed_count = len([f for f in result.findings if f.status == STATUS_FAIL])
    result.summary_metrics = {
        "records_matching_expected_value": match_count,
        "records_with_other_value": other,
        "blank_values": blank,
        "null_values": null,
        "unreadable_values": unreadable,
    }
    result.status = STATUS_FAIL if result.failed_count else STATUS_PASS
    return result


def _finding(
    run_id, run_timestamp, data_region_path, record_id, run_iso, original, normalized, message, category
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
        source_table=TABLE_QUIKDATE,
        source_field=FIELD,
        source_record_id=str(record_id),
        key_value=normalized or original,
        invalid_value=normalized or original,
        expected_condition="ACHFILEID equals 0",
        actual_condition=message,
        message=message,
        data_region_path=data_region_path,
        original_value=original,
        normalized_value=normalized,
        expected_value="0",
        governance_run_date=run_iso,
        controlling_date=run_iso,
        failure_category=category,
    )
