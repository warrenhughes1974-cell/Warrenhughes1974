"""Shared helpers for Policy Master / Client / Relationship governance."""

from __future__ import annotations

from datetime import date
from typing import Any

from data_governance.data_access.normalization import (
    add_calendar_months,
    decode_dbf_date,
    normalize_character_casefold,
    normalize_policy_number_for_length,
    parse_governance_run_date,
)
from data_governance.data_access.table_loader import field_value
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_ERROR, STATUS_FAIL, STATUS_NOT_RUN, STATUS_PASS, STATUS_WARN


MIN_DATE = date(1900, 1, 1)
POLICY_LEVEL_RELATIONS = frozenset(
    {"OWNR", "OWNC", "PAYR", "PRIM", "ASGN", "BENP", "BENC"}
)


def base_result(rule) -> RuleExecutionResult:
    return RuleExecutionResult(
        governance_item_id=rule.governance_item_id,
        rule_id=rule.rule_id,
        rule_name=rule.technical_name,
        business_name=rule.business_name,
        severity=rule.severity,
        status=STATUS_PASS,
    )


def finalize(result: RuleExecutionResult) -> RuleExecutionResult:
    fails = [f for f in result.findings if f.status == STATUS_FAIL]
    warns = [f for f in result.findings if f.status == STATUS_WARN]
    errs = [f for f in result.findings if f.status == STATUS_ERROR]
    result.failed_count = len(fails)
    result.warn_count = len(warns)
    result.error_count = len(errs)
    # Count only pass/fail/warn outcomes. Could-Not-Be-Checked (ERROR) findings
    # are incomplete coverage and must not inflate records_evaluated.
    result.records_evaluated = (
        result.passed_count + result.failed_count + result.warn_count
    )
    if fails:
        result.status = STATUS_FAIL
    elif errs:
        result.status = STATUS_ERROR
    else:
        result.status = STATUS_PASS
    return result


def missing_table(rule, *, run_id, run_timestamp, data_dir, table_name, message=None):
    result = base_result(rule)
    result.status = STATUS_ERROR
    result.error_count = 1
    result.error_message = message or f"Required table not loaded: {table_name}"
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
            source_table=table_name,
            data_region_path=data_dir,
            message=result.error_message,
            failure_category="MISSING_REFERENCE_TABLE",
            expected_condition=f"{table_name} available",
            actual_condition="Missing",
        )
    )
    return result


def deferred_result(rule, *, run_id, run_timestamp, data_dir, note: str):
    """Deferred rules: PASS with zero evaluations and no findings."""
    result = base_result(rule)
    result.summary_metrics = {"deferred": 1, "note": note}
    result.status = STATUS_PASS
    return result


def norm_char(raw) -> tuple[str, str, bool]:
    return normalize_character_casefold(raw)


def norm_policy(raw) -> tuple[str, str, bool]:
    return normalize_policy_number_for_length(raw)


def decode_date(raw):
    return decode_dbf_date(raw)


def date_in_governance_range(d: date, run_date: date) -> bool:
    max_d = add_calendar_months(run_date, 12)
    return MIN_DATE <= d <= max_d


def resolve_run_date(store, run_timestamp: str) -> date:
    """Governance run date: store.run_date when set, else parse run_timestamp."""
    stored = getattr(store, "run_date", None)
    if isinstance(stored, date):
        return stored
    return parse_governance_run_date(run_timestamp)


def parse_phase(raw) -> int | None:
    if raw is None:
        return None
    try:
        if isinstance(raw, (int, float)):
            return int(raw)
        text = str(raw).strip()
        if text == "":
            return None
        return int(float(text))
    except (TypeError, ValueError):
        return None


def build_id_index(rows, field: str) -> dict[str, list[int]]:
    index: dict[str, list[int]] = {}
    for idx, row in enumerate(rows, start=1):
        norm, _, is_null = normalize_character_casefold(field_value(row, field))
        if is_null or norm == "":
            continue
        key = norm.upper() if field in ("MPOLICY", "MCLIENTID", "MGROUP") else norm
        # Preserve casefold for policy/client: use uppercase for lookup consistency
        key = norm.strip()
        if field in ("MPOLICY", "MCLIENTID", "MGROUP"):
            # policy numbers: use length-normalize then as key
            if field == "MPOLICY":
                key, _, _ = normalize_policy_number_for_length(field_value(row, field))
            else:
                key = norm
        index.setdefault(key, []).append(idx)
    return index


def build_policy_index(rows) -> dict[str, list[int]]:
    index: dict[str, list[int]] = {}
    for idx, row in enumerate(rows, start=1):
        key, _, is_null = normalize_policy_number_for_length(field_value(row, "MPOLICY"))
        if is_null or key == "":
            continue
        index.setdefault(key, []).append(idx)
    return index


def build_client_index(rows) -> dict[str, list[int]]:
    index: dict[str, list[int]] = {}
    for idx, row in enumerate(rows, start=1):
        key, _, is_null = normalize_character_casefold(field_value(row, "MCLIENTID"))
        if is_null or key == "":
            continue
        index.setdefault(key, []).append(idx)
    return index


def build_group_index(rows) -> dict[str, list[int]]:
    index: dict[str, list[int]] = {}
    for idx, row in enumerate(rows, start=1):
        key, _, is_null = normalize_character_casefold(field_value(row, "MGROUP"))
        if is_null or key == "":
            continue
        index.setdefault(key, []).append(idx)
    return index


def build_ridr_phase_index(rows) -> dict[tuple[str, int], list[int]]:
    index: dict[tuple[str, int], list[int]] = {}
    for idx, row in enumerate(rows, start=1):
        pol, _, is_null = normalize_policy_number_for_length(field_value(row, "MPOLICY"))
        if is_null or pol == "":
            continue
        phase = parse_phase(field_value(row, "MPHASE"))
        if phase is None:
            continue
        index.setdefault((pol, phase), []).append(idx)
    return index


def policy_key_from_row(row) -> str:
    key, _, _ = normalize_policy_number_for_length(field_value(row, "MPOLICY"))
    return key


def fail(
    rule,
    *,
    run_id,
    run_timestamp,
    data_dir,
    table,
    field,
    record_id,
    key_value,
    message,
    expected,
    actual="",
    status=STATUS_FAIL,
    failure_category="DATA_PROBLEM",
    policy_number="",
    **extra,
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
        source_table=table,
        source_field=field,
        source_record_id=str(record_id),
        key_value=str(key_value or ""),
        invalid_value=str(actual or key_value or ""),
        expected_condition=expected,
        actual_condition=actual or message,
        message=message,
        data_region_path=data_dir,
        failure_category=failure_category,
        policy_number=policy_number or str(key_value or ""),
        **extra,
    )
