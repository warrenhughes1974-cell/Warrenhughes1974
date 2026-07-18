"""DG-QUIKMSTR-001 — Policy Number Must Contain 4 to 11 Characters."""

from __future__ import annotations

from data_governance.catalog.governance_items import RULE_DG_QUIKMSTR_001
from data_governance.config.settings import (
    POLICY_NUMBER_MAX_LENGTH,
    POLICY_NUMBER_MIN_LENGTH,
    TABLE_QUIKMSTR,
)
from data_governance.data_access.normalization import normalize_policy_number_for_length
from data_governance.data_access.table_loader import GovernanceDataStore, field_value
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_ERROR, STATUS_FAIL, STATUS_PASS

RULE = RULE_DG_QUIKMSTR_001
MIN_LEN = POLICY_NUMBER_MIN_LENGTH
MAX_LEN = POLICY_NUMBER_MAX_LENGTH


def run_dg_quikmstr_001(
    store: GovernanceDataStore,
    *,
    run_id: str,
    run_timestamp: str,
) -> RuleExecutionResult:
    result = RuleExecutionResult(
        governance_item_id=RULE.governance_item_id,
        rule_id=RULE.rule_id,
        rule_name=RULE.technical_name,
        business_name=RULE.business_name,
        severity=RULE.severity,
        status=STATUS_PASS,
    )

    mstr = store.get(TABLE_QUIKMSTR)
    if mstr is None:
        err = store.load_error(TABLE_QUIKMSTR) or f"{TABLE_QUIKMSTR} was not loaded."
        result.status = STATUS_ERROR
        result.error_count = 1
        result.error_message = err
        result.findings.append(
            make_finding(
                run_id=run_id,
                run_timestamp=run_timestamp,
                governance_item_id=RULE.governance_item_id,
                rule_id=RULE.rule_id,
                rule_name=RULE.technical_name,
                business_name=RULE.business_name,
                description=RULE.purpose,
                severity=RULE.severity,
                status=STATUS_ERROR,
                source_table=TABLE_QUIKMSTR,
                source_field="MPOLICY",
                data_region_path=store.data_dir,
                message=err,
                expected_condition="QuikMstr table available for evaluation",
                actual_condition="Table missing or unreadable",
            )
        )
        return result

    short_count = 0
    long_count = 0
    blank_count = 0
    null_count = 0
    rows = mstr.rows
    result.records_evaluated = len(rows)

    for idx, row in enumerate(rows, start=1):
        raw = field_value(row, "MPOLICY")
        normalized, original_display, is_null = normalize_policy_number_for_length(raw)

        if is_null:
            null_count += 1
            result.findings.append(
                _length_finding(
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=str(idx),
                    original="",
                    normalized="",
                    length="",
                    message=(
                        "A QuikMstr record contains a null policy number. "
                        f"Policy numbers must contain between {MIN_LEN} and {MAX_LEN} characters."
                    ),
                    actual="Null policy number",
                )
            )
            continue

        if normalized == "":
            blank_count += 1
            result.findings.append(
                _length_finding(
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=str(idx),
                    original=original_display,
                    normalized="",
                    length="0",
                    message=(
                        "A QuikMstr record contains a blank policy number. "
                        f"Policy numbers must contain between {MIN_LEN} and {MAX_LEN} characters."
                    ),
                    actual="Blank policy number",
                )
            )
            continue

        length = len(normalized)
        if length < MIN_LEN:
            short_count += 1
            result.findings.append(
                _length_finding(
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=str(idx),
                    original=original_display,
                    normalized=normalized,
                    length=str(length),
                    message=(
                        f"Policy number '{normalized}' contains {length} characters. "
                        f"Policy numbers must contain between {MIN_LEN} and {MAX_LEN} characters."
                    ),
                    actual=f"Length {length} (too short)",
                )
            )
            continue

        if length > MAX_LEN:
            long_count += 1
            result.findings.append(
                _length_finding(
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=str(idx),
                    original=original_display,
                    normalized=normalized,
                    length=str(length),
                    message=(
                        f"Policy number '{normalized}' contains {length} characters. "
                        f"Policy numbers must contain between {MIN_LEN} and {MAX_LEN} characters."
                    ),
                    actual=f"Length {length} (too long)",
                )
            )
            continue

        result.passed_count += 1

    result.failed_count = len([f for f in result.findings if f.status == STATUS_FAIL])
    result.summary_metrics = {
        "records_shorter_than_4": short_count,
        "records_longer_than_11": long_count,
        "blank_policy_numbers": blank_count,
        "null_policy_numbers": null_count,
    }
    result.status = STATUS_FAIL if result.failed_count else STATUS_PASS
    return result


def _length_finding(
    *,
    run_id: str,
    run_timestamp: str,
    data_region_path: str,
    record_id: str,
    original: str,
    normalized: str,
    length: str,
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
        source_table=TABLE_QUIKMSTR,
        source_field="MPOLICY",
        source_record_id=record_id,
        key_value=normalized or original,
        invalid_value=normalized or original,
        expected_condition=f"Policy number length between {MIN_LEN} and {MAX_LEN}",
        actual_condition=actual,
        message=message,
        data_region_path=data_region_path,
        policy_number=normalized or original,
        original_policy_number=original,
        normalized_policy_number=normalized,
        policy_number_length=length,
        min_permitted_length=str(MIN_LEN),
        max_permitted_length=str(MAX_LEN),
    )
