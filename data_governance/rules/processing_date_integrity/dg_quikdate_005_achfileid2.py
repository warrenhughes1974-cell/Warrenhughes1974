"""DG-QUIKDATE-005 — ACHFILEID2 Must Equal A."""

from __future__ import annotations

from data_governance.catalog.governance_items import RULE_DG_QUIKDATE_005
from data_governance.config.settings import QUIKDATE_ACHFILEID2_FIELD, TABLE_QUIKDATE
from data_governance.data_access.normalization import (
    format_iso_date,
    normalize_character_casefold,
    parse_governance_run_date,
)
from data_governance.data_access.table_loader import GovernanceDataStore, field_value
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_FAIL, STATUS_PASS
from data_governance.rules.processing_date_integrity.helpers import missing_quikdate_result

RULE = RULE_DG_QUIKDATE_005
FIELD = QUIKDATE_ACHFILEID2_FIELD
EXPECTED = "A"


def run_dg_quikdate_005(
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

    match_count = other = blank = null = 0
    for idx, row in enumerate(rows, start=1):
        norm, original, is_null = normalize_character_casefold(field_value(row, FIELD))
        if is_null:
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
                    "ACHFILEID2 contains a null value. The required governance value is 'A'.",
                    "null",
                )
            )
            continue
        if norm == "":
            blank += 1
            result.findings.append(
                _finding(
                    run_id,
                    run_timestamp,
                    store.data_dir,
                    idx,
                    run_iso,
                    original,
                    "",
                    "ACHFILEID2 contains a blank value. The required governance value is 'A'.",
                    "blank",
                )
            )
            continue
        if norm != EXPECTED:
            other += 1
            result.findings.append(
                _finding(
                    run_id,
                    run_timestamp,
                    store.data_dir,
                    idx,
                    run_iso,
                    original,
                    norm,
                    f"ACHFILEID2 contains '{norm}'. The required governance value is 'A'.",
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
        "unreadable_values": 0,
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
        expected_condition="ACHFILEID2 equals A",
        actual_condition=message,
        message=message,
        data_region_path=data_region_path,
        original_value=original,
        normalized_value=normalized,
        expected_value=EXPECTED,
        governance_run_date=run_iso,
        controlling_date=run_iso,
        failure_category=category,
    )
