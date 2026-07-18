"""DG-QUIKPLAN-031 through 033 — cross-table references and date warnings."""

from __future__ import annotations

from datetime import date

from data_governance.catalog.governance_items import (
    RULE_DG_QUIKPLAN_031,
    RULE_DG_QUIKPLAN_032,
    RULE_DG_QUIKPLAN_033,
)
from data_governance.config.settings import TABLE_QUIKCOMP, TABLE_QUIKPLAN
from data_governance.data_access.normalization import (
    add_calendar_months,
    decode_dbf_date,
    format_iso_date,
    normalize_dbf_character,
    normalize_identifier_preserve_zeros,
    parse_governance_run_date,
)
from data_governance.data_access.table_loader import field_value
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_FAIL, STATUS_WARN
from data_governance.rules.company_code_integrity.company_code_index import build_company_code_index
from data_governance.rules.plan_setup_integrity.common import finalize_rule_result
from data_governance.rules.plan_setup_integrity.inventories import (
    COMPANY_BEARING_TABLES,
    DATE_FIELDS,
    RATE_KEY_TABLES,
)
from data_governance.rules.plan_value_integrity.reference_index import build_single_field_index

MIN_DATE = date(1900, 1, 1)


def _base(rule) -> RuleExecutionResult:
    return RuleExecutionResult(
        governance_item_id=rule.governance_item_id,
        rule_id=rule.rule_id,
        rule_name=rule.technical_name,
        business_name=rule.business_name,
        severity=rule.severity,
        status="PASS",
    )


def run_dg_quikplan_031(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_031
    plan_loaded = store.get(TABLE_QUIKPLAN)
    if plan_loaded is None:
        from data_governance.rules.plan_setup_integrity.common import missing_table_result

        return missing_table_result(
            rule=rule,
            run_id=run_id,
            run_timestamp=run_timestamp,
            data_region_path=store.data_dir,
            table_name=TABLE_QUIKPLAN,
        )
    plan_index = build_single_field_index(plan_loaded.rows, "PLAN")
    result = _base(rule)
    seen: set[tuple[str, int, str]] = set()

    for table, plan_field, friendly in RATE_KEY_TABLES:
        loaded = store.get(table)
        if loaded is None:
            continue
        for idx, row in enumerate(loaded.rows, start=1):
            norm, orig, is_null = normalize_identifier_preserve_zeros(field_value(row, plan_field))
            if is_null or not norm:
                continue
            dedupe = (table, idx, norm)
            if dedupe in seen:
                continue
            seen.add(dedupe)
            result.records_evaluated += 1
            if plan_index.exists_once(norm):
                result.passed_count += 1
                continue
            if plan_index.is_duplicated(norm):
                msg = (
                    f"Plan {norm} is used in {friendly} but matches more than one "
                    "Plan Setup record."
                )
                cat = "AMBIGUOUS_PLAN"
            else:
                msg = f"Plan {norm} is used in {friendly} but was not found in Plan Setup."
                cat = "MISSING_PLAN"
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
                    status=STATUS_FAIL,
                    source_table=table,
                    source_field=plan_field,
                    source_record_id=str(idx),
                    key_value=norm,
                    invalid_value=norm,
                    message=msg,
                    data_region_path=store.data_dir,
                    plan=norm,
                    original_value=orig,
                    normalized_value=norm,
                    failure_category=cat,
                    reference_table=TABLE_QUIKPLAN,
                    reference_field="PLAN",
                    expected_condition="A plan defined in Plan Setup",
                )
            )
    return finalize_rule_result(result)


def run_dg_quikplan_032(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_032
    comp = store.get(TABLE_QUIKCOMP)
    if comp is None:
        from data_governance.rules.plan_setup_integrity.common import missing_table_result

        return missing_table_result(
            rule=rule,
            run_id=run_id,
            run_timestamp=run_timestamp,
            data_region_path=store.data_dir,
            table_name=TABLE_QUIKCOMP,
        )
    index = build_company_code_index(comp.rows)
    result = _base(rule)
    seen: set[tuple[str, int, str, str]] = set()

    for table, company_field in COMPANY_BEARING_TABLES:
        loaded = store.get(table)
        if loaded is None:
            continue
        for idx, row in enumerate(loaded.rows, start=1):
            code = normalize_dbf_character(field_value(row, company_field))
            if not code:
                continue
            dedupe = (table, idx, company_field, code)
            if dedupe in seen:
                continue
            seen.add(dedupe)
            result.records_evaluated += 1
            if index.exists_once(code):
                result.passed_count += 1
                continue
            if index.is_duplicated(code):
                msg = f"Company code {code} matches more than one Company Setup record."
                cat = "AMBIGUOUS_REFERENCE"
            else:
                msg = f"Company code {code} was not found in Company Setup."
                cat = "MISSING_REFERENCE"
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
                    status=STATUS_FAIL,
                    source_table=table,
                    source_field=company_field,
                    source_record_id=str(idx),
                    key_value=code,
                    invalid_value=code,
                    message=msg,
                    data_region_path=store.data_dir,
                    company_code=code,
                    failure_category=cat,
                    reference_table=TABLE_QUIKCOMP,
                    reference_field="MCOMP",
                    expected_condition="A valid company code",
                )
            )
    return finalize_rule_result(result)


def run_dg_quikplan_033(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_033
    run_date = parse_governance_run_date(run_timestamp)
    max_date = add_calendar_months(run_date, 12)
    min_iso = format_iso_date(MIN_DATE)
    max_iso = format_iso_date(max_date)
    result = _base(rule)
    seen: set[tuple[str, int, str]] = set()

    for table, date_field in DATE_FIELDS:
        loaded = store.get(table)
        if loaded is None:
            continue
        for idx, row in enumerate(loaded.rows, start=1):
            raw = field_value(row, date_field)
            decoded = decode_dbf_date(raw)
            if decoded.is_null or decoded.is_blank:
                continue
            if decoded.is_unreadable or decoded.date_value is None:
                continue
            dedupe = (table, idx, date_field)
            if dedupe in seen:
                continue
            seen.add(dedupe)
            d = decoded.date_value
            result.records_evaluated += 1
            if MIN_DATE <= d <= max_date:
                result.passed_count += 1
                continue
            if d < MIN_DATE:
                msg = "The date is earlier than January 1, 1900."
                cat = "DATE_BEFORE_MINIMUM"
            else:
                msg = (
                    "The date is more than 12 months after the date of this review "
                    f"(maximum permitted date is {max_iso})."
                )
                cat = "DATE_AFTER_MAXIMUM"
            plan_norm, _, _ = normalize_identifier_preserve_zeros(
                field_value(row, "PLAN") or field_value(row, "MPLAN")
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
                    status=STATUS_WARN,
                    source_table=table,
                    source_field=date_field,
                    source_record_id=str(idx),
                    key_value=plan_norm or decoded.decoded_display,
                    invalid_value=decoded.decoded_display,
                    message=msg,
                    data_region_path=store.data_dir,
                    plan=plan_norm or "",
                    original_value=decoded.original_display,
                    effective_date=decoded.decoded_display,
                    min_allowed_date=min_iso,
                    max_allowed_date=max_iso,
                    failure_category=cat,
                    expected_condition=f"A date from {min_iso} through {max_iso}",
                )
            )
    return finalize_rule_result(result)
