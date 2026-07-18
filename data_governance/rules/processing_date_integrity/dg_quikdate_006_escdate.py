"""DG-QUIKDATE-006 — ESCDATE Must Be Blank (physical field ESC_DATE)."""

from __future__ import annotations

from data_governance.catalog.governance_items import RULE_DG_QUIKDATE_006
from data_governance.config.settings import QUIKDATE_ESCDATE_FIELD, TABLE_QUIKDATE
from data_governance.data_access.normalization import (
    decode_dbf_date,
    format_iso_date,
    parse_governance_run_date,
)
from data_governance.data_access.table_loader import GovernanceDataStore, field_value
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_FAIL, STATUS_PASS
from data_governance.rules.processing_date_integrity.helpers import missing_quikdate_result

RULE = RULE_DG_QUIKDATE_006
# Physical DBF field is ESC_DATE; also accept ESCDATE alias via field_value
FIELD = QUIKDATE_ESCDATE_FIELD
FIELD_ALIASES = (QUIKDATE_ESCDATE_FIELD, "ESCDATE")


def run_dg_quikdate_006(
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

    blank_ok = 0
    populated = 0
    unreadable = 0

    for idx, row in enumerate(rows, start=1):
        decoded = decode_dbf_date(field_value(row, *FIELD_ALIASES))

        if decoded.date_value is not None:
            populated += 1
            shown = format_iso_date(decoded.date_value)
            result.findings.append(
                _finding(
                    run_id,
                    run_timestamp,
                    store.data_dir,
                    idx,
                    run_iso,
                    decoded.original_display,
                    shown,
                    f"ESCDATE contains '{shown}'. The required governance condition is blank.",
                    "populated_date",
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
                    f"ESCDATE contains '{shown}'. The required governance condition is blank.",
                    "unreadable",
                )
            )
            continue

        # Null, supported empty DBF date, or blank after trim → pass
        blank_ok += 1

    result.passed_count = blank_ok
    result.failed_count = len([f for f in result.findings if f.status == STATUS_FAIL])
    result.summary_metrics = {
        "blank_escdate_values": blank_ok,
        "populated_escdate_values": populated,
        "unreadable_dates": unreadable,
        "records_matching_expected_value": blank_ok,
        "records_with_other_value": populated,
        "blank_values": blank_ok,
        "null_values": 0,
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
        expected_condition="ESCDATE / ESC_DATE is blank",
        actual_condition=message,
        message=message,
        data_region_path=data_region_path,
        original_value=original,
        normalized_value=normalized,
        expected_value="",
        governance_run_date=run_iso,
        controlling_date=run_iso,
        failure_category=category,
    )
