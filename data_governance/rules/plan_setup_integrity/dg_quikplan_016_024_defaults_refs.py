"""DG-QUIKPLAN-016 through 024 — defaults and related setup references.

DG-QUIKPLAN-022 retired 2026-07-18 (DG-R-006).
"""

from __future__ import annotations

from data_governance.catalog.governance_items import (
    RULE_DG_QUIKPLAN_016,
    RULE_DG_QUIKPLAN_017,
    RULE_DG_QUIKPLAN_018,
    RULE_DG_QUIKPLAN_019,
    RULE_DG_QUIKPLAN_020,
    RULE_DG_QUIKPLAN_021,
    RULE_DG_QUIKPLAN_023,
    RULE_DG_QUIKPLAN_024,
)
from data_governance.config.settings import (
    QUIKPLAN_MAXUNIT_FIELD,
    QUIKPLAN_RRULE_FIELD,
    TABLE_QUIKCOMM,
    TABLE_QUIKPLAN,
)
from data_governance.data_access.normalization import (
    decode_numeric_zero,
    normalize_character_casefold,
    normalize_dbf_character,
)
from data_governance.data_access.table_loader import field_value
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_FAIL
from data_governance.rules.plan_setup_integrity.common import (
    decode_logical,
    decode_numeric,
    deficiency_applies,
    empty_quikplan_result,
    finalize_rule_result,
    iterate_quikplan_rows,
    make_plan_finding,
    missing_table_result,
    plan_from_row,
)
from data_governance.rules.plan_value_integrity.reference_index import build_single_field_index


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


def run_dg_quikplan_016(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_016
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    comm = store.get(TABLE_QUIKCOMM)
    if comm is None:
        return missing_table_result(
            rule=rule,
            run_id=run_id,
            run_timestamp=run_timestamp,
            data_region_path=store.data_dir,
            table_name=TABLE_QUIKCOMM,
            message=(
                "Commission IDs could not be checked because Commission Setup was not found."
            ),
        )
    index = build_single_field_index(comm.rows, "COMMID")
    result = _base(rule)
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, _ = plan_from_row(row)
        commid = normalize_dbf_character(field_value(row, "COMMID"))
        if not commid:
            continue
        result.records_evaluated += 1
        if index.exists_once(commid):
            result.passed_count += 1
            continue
        if index.is_duplicated(commid):
            msg = f"Commission ID {commid} matches more than one Commission Setup record."
            cat = "AMBIGUOUS_REFERENCE"
        else:
            msg = f"Commission ID {commid} was not found in Commission Setup."
            cat = "MISSING_REFERENCE"
        result.findings.append(
            make_plan_finding(
                rule=rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_region_path=store.data_dir,
                record_id=idx,
                plan=plan,
                plan_original=orig,
                source_field="COMMID",
                message=msg,
                status=STATUS_FAIL,
                failure_category=cat,
                original_value=commid,
                reference_table=TABLE_QUIKCOMM,
                reference_field="COMMID",
                expected_condition="A valid commission ID or blank",
            )
        )
    return finalize_rule_result(result)


def run_dg_quikplan_017(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_017
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = _base(rule)
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, _ = plan_from_row(row)
        max_dec, max_disp, max_null, max_bad = decode_numeric(field_value(row, QUIKPLAN_MAXUNIT_FIELD))
        min_dec, min_disp, min_null, min_bad = decode_numeric(field_value(row, "MINUNIT"))
        result.records_evaluated += 1
        if max_null or min_null or max_bad or min_bad or max_dec is None or min_dec is None:
            result.findings.append(
                make_plan_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=idx,
                    plan=plan,
                    plan_original=orig,
                    source_field=QUIKPLAN_MAXUNIT_FIELD,
                    message="The maximum or minimum units could not be read.",
                    status=STATUS_FAIL,
                    failure_category="UNREADABLE_VALUE",
                    original_value=f"{max_disp}/{min_disp}",
                    expected_condition="Maximum units greater than or equal to minimum units",
                )
            )
            continue
        if max_dec >= min_dec:
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
                source_field=QUIKPLAN_MAXUNIT_FIELD,
                message="The maximum units are less than the minimum units.",
                status=STATUS_FAIL,
                failure_category="MAX_BELOW_MIN",
                original_value=f"{max_disp}/{min_disp}",
                expected_condition="Maximum units greater than or equal to minimum units",
            )
        )
    return finalize_rule_result(result)


def _default_char_rule(store, *, rule, field_name, expected, problem, run_id, run_timestamp):
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = _base(rule)
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, _ = plan_from_row(row)
        norm, orig_val, is_null = normalize_character_casefold(field_value(row, field_name))
        result.records_evaluated += 1
        if is_null or norm != expected:
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
                    message=problem,
                    status=STATUS_FAIL,
                    failure_category="INVALID_DEFAULT",
                    original_value=orig_val,
                    normalized_value=norm or "",
                    expected_condition=expected,
                )
            )
            continue
        result.passed_count += 1
    return finalize_rule_result(result)


def run_dg_quikplan_018(store, *, run_id, run_timestamp):
    return _default_char_rule(
        store,
        rule=RULE_DG_QUIKPLAN_018,
        field_name=QUIKPLAN_RRULE_FIELD,
        expected="B",
        problem="The rounding rule is not set to B.",
        run_id=run_id,
        run_timestamp=run_timestamp,
    )


def run_dg_quikplan_019(store, *, run_id, run_timestamp):
    return _default_char_rule(
        store,
        rule=RULE_DG_QUIKPLAN_019,
        field_name="AUTONFO",
        expected="0",
        problem="The automatic nonforfeiture setting is not set to 0.",
        run_id=run_id,
        run_timestamp=run_timestamp,
    )


def run_dg_quikplan_020(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_020
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = _base(rule)
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, _ = plan_from_row(row)
        if not deficiency_applies(plan):
            continue
        norm, orig_val, is_null = normalize_character_casefold(field_value(row, "DEFICIENCY"))
        result.records_evaluated += 1
        if is_null or norm != "N":
            result.findings.append(
                make_plan_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=idx,
                    plan=plan,
                    plan_original=orig,
                    source_field="DEFICIENCY",
                    message="The deficiency setting must be N for this plan.",
                    status=STATUS_FAIL,
                    failure_category="INVALID_DEFICIENCY",
                    original_value=orig_val,
                    normalized_value=norm or "",
                    expected_condition="N",
                )
            )
            continue
        result.passed_count += 1
    return finalize_rule_result(result)


def run_dg_quikplan_021(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_021
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = _base(rule)
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, _ = plan_from_row(row)
        logical, orig_val, is_null = decode_logical(field_value(row, "BACTIVE"))
        result.records_evaluated += 1
        if is_null or logical is None:
            result.findings.append(
                make_plan_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=idx,
                    plan=plan,
                    plan_original=orig,
                    source_field="BACTIVE",
                    message="The new-business status is not a valid yes-or-no value.",
                    status=STATUS_FAIL,
                    failure_category="INVALID_LOGICAL",
                    original_value=orig_val,
                    expected_condition="True or False",
                )
            )
            continue
        result.passed_count += 1
    return finalize_rule_result(result)


def run_dg_quikplan_023(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_023
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = _base(rule)
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, _ = plan_from_row(row)
        decoded = decode_numeric_zero(field_value(row, "MLAPSE"))
        result.records_evaluated += 1
        if decoded.is_null or decoded.is_blank or decoded.is_unreadable or not decoded.is_zero:
            result.findings.append(
                make_plan_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=idx,
                    plan=plan,
                    plan_original=orig,
                    source_field="MLAPSE",
                    message="The lapse setting is not set to 0.",
                    status=STATUS_FAIL,
                    failure_category="INVALID_DEFAULT",
                    original_value=decoded.original_display,
                    expected_condition="0",
                )
            )
            continue
        result.passed_count += 1
    return finalize_rule_result(result)


def run_dg_quikplan_024(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_024
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = _base(rule)
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, _ = plan_from_row(row)
        norm, orig_val, is_null = normalize_character_casefold(field_value(row, "MNAICLOB"))
        result.records_evaluated += 1
        if is_null or norm != "NAPLAN":
            result.findings.append(
                make_plan_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=idx,
                    plan=plan,
                    plan_original=orig,
                    source_field="MNAICLOB",
                    message="The NAIC line-of-business setting is not set to NAPLAN.",
                    status=STATUS_FAIL,
                    failure_category="INVALID_DEFAULT",
                    original_value=orig_val,
                    normalized_value=norm or "",
                    expected_condition="NAPLAN",
                )
            )
            continue
        result.passed_count += 1
    return finalize_rule_result(result)
