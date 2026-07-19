"""DG-QUIKPLAN-007 through 015 — plan type, periods, and initial value."""

from __future__ import annotations

from data_governance.catalog.governance_items import (
    RULE_DG_QUIKPLAN_007,
    RULE_DG_QUIKPLAN_008,
    RULE_DG_QUIKPLAN_009,
    RULE_DG_QUIKPLAN_010,
    RULE_DG_QUIKPLAN_011,
    RULE_DG_QUIKPLAN_012,
    RULE_DG_QUIKPLAN_013,
    RULE_DG_QUIKPLAN_014,
    RULE_DG_QUIKPLAN_015,
)
from data_governance.config.settings import QUIKPLAN_PAYYRS_FIELD, TABLE_QUIKPLAN
from data_governance.data_access.normalization import normalize_character_casefold
from data_governance.data_access.table_loader import field_value
from data_governance.models.findings import RuleExecutionResult
from data_governance.models.statuses import STATUS_FAIL, STATUS_WARN
from data_governance.rules.plan_setup_integrity.common import (
    approx_equal_1000,
    classification_unavailable_result,
    decode_numeric,
    empty_quikplan_result,
    finalize_rule_result,
    iterate_quikplan_rows,
    make_plan_finding,
    plan_from_row,
    plan_starts_with_5,
)
from data_governance.rules.plan_setup_integrity.plan_classification import (
    has_initval_exception,
    is_myga,
    is_single_premium,
    load_plan_classification,
)


def _base(rule) -> RuleExecutionResult:
    return RuleExecutionResult(
        governance_item_id=rule.governance_item_id,
        rule_id=rule.rule_id,
        rule_name=rule.technical_name,
        business_name=rule.business_name,
        severity=rule.severity,
        status="PASS",
    )


def _require_quikplan(store, rule, *, run_id, run_timestamp):
    if store.get(TABLE_QUIKPLAN) is None:
        return empty_quikplan_result(
            rule=rule,
            run_id=run_id,
            run_timestamp=run_timestamp,
            data_region_path=store.data_dir,
        )
    return None


def _numeric_zero(value) -> tuple[bool, bool]:
    dec, _, is_null, unreadable = decode_numeric(value)
    if is_null or unreadable or dec is None:
        return False, True
    return dec == 0, False


def run_dg_quikplan_007(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_007
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    cfg = load_plan_classification()
    if not cfg.available:
        return classification_unavailable_result(
            rule=rule,
            run_id=run_id,
            run_timestamp=run_timestamp,
            data_region_path=store.data_dir,
        )
    result = _base(rule)
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, _ = plan_from_row(row)
        if not is_myga(cfg, plan):
            continue
        dec, disp, is_null, unreadable = decode_numeric(field_value(row, "DEPINT"))
        result.records_evaluated += 1
        if is_null or unreadable or dec is None or dec <= 0:
            result.findings.append(
                make_plan_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=idx,
                    plan=plan,
                    plan_original=orig,
                    source_field="DEPINT",
                    message=(
                        "This MYGA plan does not have a deposit interest value greater than zero."
                    ),
                    status=STATUS_FAIL,
                    failure_category="INVALID_DEPINT",
                    original_value=disp,
                    expected_condition="A value greater than zero",
                )
            )
            continue
        result.passed_count += 1
    return finalize_rule_result(result)


def run_dg_quikplan_008(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_008
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = _base(rule)
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, _ = plan_from_row(row)
        lo_dec, lo_disp, lo_null, lo_bad = decode_numeric(field_value(row, "LOAGE"))
        hi_dec, hi_disp, hi_null, hi_bad = decode_numeric(field_value(row, "HIAGE"))
        result.records_evaluated += 1
        if lo_null or hi_null or lo_bad or hi_bad or lo_dec is None or hi_dec is None:
            result.findings.append(
                make_plan_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=idx,
                    plan=plan,
                    plan_original=orig,
                    source_field="LOAGE",
                    message="The low age or high age could not be read.",
                    status=STATUS_FAIL,
                    failure_category="UNREADABLE_VALUE",
                    original_value=f"{lo_disp}/{hi_disp}",
                    expected_condition="Readable low age below high age",
                )
            )
            continue
        if lo_dec >= hi_dec:
            result.findings.append(
                make_plan_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=idx,
                    plan=plan,
                    plan_original=orig,
                    source_field="HIAGE",
                    message="The low age must be less than the high age.",
                    status=STATUS_FAIL,
                    failure_category="LOAGE_NOT_BELOW_HIAGE",
                    original_value=f"{lo_disp}/{hi_disp}",
                    expected_condition="Low age below high age",
                )
            )
            continue
        result.passed_count += 1
    return finalize_rule_result(result)


def run_dg_quikplan_009(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_009
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = _base(rule)
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, _ = plan_from_row(row)
        norm, orig_val, is_null = normalize_character_casefold(field_value(row, "RENEW"))
        result.records_evaluated += 1
        allowed = {"N", "Y"} if plan_starts_with_5(plan) else {"N"}
        if is_null or not norm or norm not in allowed:
            result.findings.append(
                make_plan_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=idx,
                    plan=plan,
                    plan_original=orig,
                    source_field="RENEW",
                    message="The renewal setting is invalid for this plan.",
                    status=STATUS_FAIL,
                    failure_category="INVALID_RENEW",
                    original_value=orig_val,
                    normalized_value=norm or "",
                    expected_condition="N, or N or Y for plans beginning with 5",
                )
            )
            continue
        result.passed_count += 1
    return finalize_rule_result(result)


def _both_zero_rule(store, *, rule, pay_field, age_field, message, run_id, run_timestamp):
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = _base(rule)
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, _ = plan_from_row(row)
        if plan_starts_with_5(plan):
            continue
        pay_zero, pay_bad = _numeric_zero(field_value(row, pay_field))
        age_zero, age_bad = _numeric_zero(field_value(row, age_field))
        result.records_evaluated += 1
        if pay_bad or age_bad:
            result.findings.append(
                make_plan_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=idx,
                    plan=plan,
                    plan_original=orig,
                    source_field=pay_field,
                    message="The payment or insurance period could not be read.",
                    status=STATUS_FAIL,
                    failure_category="UNREADABLE_VALUE",
                    expected_condition="At least one value greater than zero",
                )
            )
            continue
        if pay_zero and age_zero:
            result.findings.append(
                make_plan_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=idx,
                    plan=plan,
                    plan_original=orig,
                    source_field=pay_field,
                    message=message,
                    status=STATUS_FAIL,
                    failure_category="BOTH_ZERO",
                    expected_condition="At least one value greater than zero",
                )
            )
            continue
        result.passed_count += 1
    return finalize_rule_result(result)


def run_dg_quikplan_010(store, *, run_id, run_timestamp):
    return _both_zero_rule(
        store,
        rule=RULE_DG_QUIKPLAN_010,
        pay_field=QUIKPLAN_PAYYRS_FIELD,
        age_field="PAYAGE",
        message="Both the payment years and payment age are zero.",
        run_id=run_id,
        run_timestamp=run_timestamp,
    )


def run_dg_quikplan_011(store, *, run_id, run_timestamp):
    return _both_zero_rule(
        store,
        rule=RULE_DG_QUIKPLAN_011,
        pay_field="INSYRS",
        age_field="INSAGE",
        message="Both the insurance years and insurance age are zero.",
        run_id=run_id,
        run_timestamp=run_timestamp,
    )


def run_dg_quikplan_012(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_012
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    cfg = load_plan_classification()
    if not cfg.available:
        return classification_unavailable_result(
            rule=rule,
            run_id=run_id,
            run_timestamp=run_timestamp,
            data_region_path=store.data_dir,
        )
    checks = (
        (QUIKPLAN_PAYYRS_FIELD, 1, "A single-premium plan must have payment years set to 1."),
        ("PAYAGE", 0, "A single-premium plan must have payment age set to 0."),
        ("SEMI", 0, "A single-premium plan cannot have a semiannual payment value."),
        ("QTRL", 0, "A single-premium plan cannot have a quarterly payment value."),
        ("MTHD", 0, "A single-premium plan cannot have a monthly debit payment value."),
        ("MTHB", 0, "A single-premium plan cannot have a monthly bill payment value."),
    )
    result = _base(rule)
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, _ = plan_from_row(row)
        if not is_single_premium(cfg, plan):
            continue
        for field_name, expected, msg in checks:
            dec, disp, is_null, unreadable = decode_numeric(field_value(row, field_name))
            result.records_evaluated += 1
            if is_null or unreadable or dec is None or dec != expected:
                result.findings.append(
                    make_plan_finding(
                        rule=rule,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_region_path=store.data_dir,
                        record_id=idx,
                        plan=plan,
                        plan_original=orig,
                        source_field=field_name,
                        message=msg,
                        status=STATUS_FAIL,
                        failure_category="INVALID_SP_SETTING",
                        original_value=disp,
                        expected_condition=str(expected),
                    )
                )
            else:
                result.passed_count += 1
    return finalize_rule_result(result)


def _max_age_rule(store, *, rule, field_name, run_id, run_timestamp):
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = _base(rule)
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, _ = plan_from_row(row)
        dec, disp, is_null, unreadable = decode_numeric(field_value(row, field_name))
        result.records_evaluated += 1
        if is_null or unreadable or dec is None:
            result.passed_count += 1
            continue
        if dec > 125:
            result.findings.append(
                make_plan_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=idx,
                    plan=plan,
                    plan_original=orig,
                    source_field=field_name,
                    message=f"The {field_name.lower()} age is greater than 125.",
                    status=STATUS_FAIL,
                    failure_category="AGE_ABOVE_MAX",
                    original_value=disp,
                    expected_condition="125 or less",
                )
            )
            continue
        result.passed_count += 1
    return finalize_rule_result(result)


def run_dg_quikplan_013(store, *, run_id, run_timestamp):
    return _max_age_rule(
        store,
        rule=RULE_DG_QUIKPLAN_013,
        field_name="PAYAGE",
        run_id=run_id,
        run_timestamp=run_timestamp,
    )


def run_dg_quikplan_014(store, *, run_id, run_timestamp):
    return _max_age_rule(
        store,
        rule=RULE_DG_QUIKPLAN_014,
        field_name="INSAGE",
        run_id=run_id,
        run_timestamp=run_timestamp,
    )


def run_dg_quikplan_015(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_015
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    cfg = load_plan_classification()
    result = _base(rule)
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, _ = plan_from_row(row)
        dec, disp, is_null, unreadable = decode_numeric(field_value(row, "INITVAL"))
        result.records_evaluated += 1
        if is_null or unreadable or dec is None:
            result.findings.append(
                make_plan_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=idx,
                    plan=plan,
                    plan_original=orig,
                    source_field="INITVAL",
                    message="The initial value could not be read.",
                    status=STATUS_FAIL,
                    failure_category="UNREADABLE_VALUE",
                    original_value=disp,
                    expected_condition="1000 unless an approved transformation applies",
                )
            )
            continue
        if approx_equal_1000(dec) or has_initval_exception(cfg, plan):
            result.passed_count += 1
            continue
        result.findings.append(
            make_plan_finding(
                rule=rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_region_path=store.data_dir,
                record_id=idx,
                plan=plan,
                plan_original=orig,
                source_field="INITVAL",
                message="The initial value differs from the expected default of 1000.",
                status=STATUS_WARN,
                failure_category="INITVAL_NON_DEFAULT",
                original_value=disp,
                expected_condition="1000 unless an approved transformation applies",
            )
        )
    return finalize_rule_result(result)
