"""DG-QUIKPLAN-025 through 030 — supporting rate and value tables."""

from __future__ import annotations

from data_governance.catalog.governance_items import (
    RULE_DG_QUIKPLAN_025,
    RULE_DG_QUIKPLAN_026,
    RULE_DG_QUIKPLAN_027,
    RULE_DG_QUIKPLAN_028,
    RULE_DG_QUIKPLAN_029,
    RULE_DG_QUIKPLAN_030,
)
from data_governance.config.settings import (
    TABLE_QUIKDBS,
    TABLE_QUIKGPS,
    TABLE_QUIKPLAN,
    TABLE_QUIKPLDB,
    TABLE_QUIKPLGP,
    TABLE_QUIKUINT,
)
from data_governance.data_access.normalization import normalize_character_casefold
from data_governance.data_access.table_loader import field_value
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_FAIL, STATUS_WARN
from data_governance.rules.plan_setup_integrity.common import (
    classification_unavailable_result,
    decode_logical,
    empty_quikplan_result,
    finalize_rule_result,
    iterate_quikplan_rows,
    make_plan_finding,
    missing_table_result,
    plan_from_row,
    plan_starts_with_a,
    traditional_plan,
)
from data_governance.rules.plan_setup_integrity.inventories import (
    ANNUITY_SUPPORT_TABLES,
    TRADITIONAL_VALUE_TABLES,
)
from data_governance.rules.plan_setup_integrity.plan_classification import is_ul, load_plan_classification
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


def _var_not_four(value) -> bool:
    norm, _, is_null = normalize_character_casefold(value)
    return not is_null and norm != "4"


def _paired_support_rule(
    store,
    *,
    rule,
    flag_field: str,
    table_a: str,
    table_b: str,
    label_a: str,
    label_b: str,
    run_id,
    run_timestamp,
):
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    applicable: list[tuple[int, dict, str, str]] = []
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, _ = plan_from_row(row)
        if not _var_not_four(field_value(row, flag_field)):
            continue
        applicable.append((idx, row, plan, orig))
    result = _base(rule)
    if not applicable:
        return finalize_rule_result(result)

    loaded_a = store.get(table_a)
    loaded_b = store.get(table_b)
    if loaded_a is None:
        return missing_table_result(
            rule=rule,
            run_id=run_id,
            run_timestamp=run_timestamp,
            data_region_path=store.data_dir,
            table_name=table_a,
        )
    if loaded_b is None:
        return missing_table_result(
            rule=rule,
            run_id=run_id,
            run_timestamp=run_timestamp,
            data_region_path=store.data_dir,
            table_name=table_b,
        )
    index_a = build_single_field_index(loaded_a.rows, "PLAN")
    index_b = build_single_field_index(loaded_b.rows, "PLAN")
    for idx, row, plan, orig in applicable:
        for index, table_name, label in (
            (index_a, table_a, label_a),
            (index_b, table_b, label_b),
        ):
            result.records_evaluated += 1
            if index.exists(plan):
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
                    source_field=flag_field,
                    message=f"Plan {plan} was not found in {label}.",
                    status=STATUS_FAIL,
                    failure_category="MISSING_SUPPORTING_PLAN",
                    reference_table=table_name,
                    expected_condition="A supporting record for the plan",
                )
            )
    return finalize_rule_result(result)


def run_dg_quikplan_025(store, *, run_id, run_timestamp):
    return _paired_support_rule(
        store,
        rule=RULE_DG_QUIKPLAN_025,
        flag_field="VARGP",
        table_a=TABLE_QUIKGPS,
        table_b=TABLE_QUIKPLGP,
        label_a="Gross Premium Setup",
        label_b="Gross Premium Plan Values",
        run_id=run_id,
        run_timestamp=run_timestamp,
    )


def run_dg_quikplan_026(store, *, run_id, run_timestamp):
    return _paired_support_rule(
        store,
        rule=RULE_DG_QUIKPLAN_026,
        flag_field="VARDB",
        table_a=TABLE_QUIKDBS,
        table_b=TABLE_QUIKPLDB,
        label_a="Death Benefit Setup",
        label_b="Death Benefit Plan Values",
        run_id=run_id,
        run_timestamp=run_timestamp,
    )


def run_dg_quikplan_027(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_027
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    applicable = [
        (idx, row, plan_from_row(row)[0])
        for idx, row in iterate_quikplan_rows(store)
        if traditional_plan(plan_from_row(row)[0])
    ]
    result = _base(rule)
    if not applicable:
        return finalize_rule_result(result)

    table_indexes: dict[str, object] = {}
    for table, _label in TRADITIONAL_VALUE_TABLES:
        loaded = store.get(table)
        if loaded is None:
            return missing_table_result(
                rule=rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_region_path=store.data_dir,
                table_name=table,
            )
        table_indexes[table] = build_single_field_index(loaded.rows, "PLAN")
    for idx, row, plan in applicable:
        for table, label in TRADITIONAL_VALUE_TABLES:
            result.records_evaluated += 1
            if table_indexes[table].exists(plan):
                result.passed_count += 1
                continue
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
                    source_field="PLAN",
                    source_record_id=str(idx),
                    key_value=plan,
                    message=f"Plan {plan} does not have a {label} record.",
                    data_region_path=store.data_dir,
                    plan=plan,
                    failure_category="MISSING_TRADITIONAL_TABLE",
                    expected_condition=f"A {label} record",
                    actual_condition="Missing",
                )
            )
    return finalize_rule_result(result)


def run_dg_quikplan_028(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_028
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    applicable = [
        (idx, row, plan_from_row(row)[0])
        for idx, row in iterate_quikplan_rows(store)
        if plan_starts_with_a(plan_from_row(row)[0])
    ]
    result = _base(rule)
    if not applicable:
        return finalize_rule_result(result)

    table_indexes: dict[str, object] = {}
    for table, _label in ANNUITY_SUPPORT_TABLES:
        loaded = store.get(table)
        if loaded is None:
            return missing_table_result(
                rule=rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_region_path=store.data_dir,
                table_name=table,
            )
        table_indexes[table] = build_single_field_index(loaded.rows, "MPLAN")
    for idx, row, plan in applicable:
        for table, label in ANNUITY_SUPPORT_TABLES:
            result.records_evaluated += 1
            if table_indexes[table].exists(plan):
                result.passed_count += 1
                continue
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
                    source_field="MPLAN",
                    source_record_id=str(idx),
                    key_value=plan,
                    message=f"Annuity plan {plan} does not have a {label} record.",
                    data_region_path=store.data_dir,
                    plan=plan,
                    failure_category="MISSING_ANNUITY_TABLE",
                    expected_condition=f"A {label} record",
                    actual_condition="Missing",
                )
            )
    return finalize_rule_result(result)


def run_dg_quikplan_029(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_029
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
    applicable = [
        (idx, row, plan_from_row(row)[0])
        for idx, row in iterate_quikplan_rows(store)
        if is_ul(cfg, plan_from_row(row)[0])
    ]
    result = _base(rule)
    if not applicable:
        return finalize_rule_result(result)

    uint = store.get(TABLE_QUIKUINT)
    if uint is None:
        return missing_table_result(
            rule=rule,
            run_id=run_id,
            run_timestamp=run_timestamp,
            data_region_path=store.data_dir,
            table_name=TABLE_QUIKUINT,
        )
    index = build_single_field_index(uint.rows, "MPLAN")
    for idx, row, plan in applicable:
        result.records_evaluated += 1
        if index.exists(plan):
            result.passed_count += 1
            continue
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
                source_table=TABLE_QUIKUINT,
                source_field="MPLAN",
                source_record_id=str(idx),
                key_value=plan,
                message=(
                    f"Universal Life plan {plan} was not found in Universal Life "
                    "Interest Setup."
                ),
                data_region_path=store.data_dir,
                plan=plan,
                failure_category="MISSING_UL_RECORD",
                expected_condition="A Universal Life interest record",
            )
        )
    return finalize_rule_result(result)


def run_dg_quikplan_030(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_030
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = _base(rule)
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, _ = plan_from_row(row)
        ptype, _, _ = normalize_character_casefold(field_value(row, "PLANTYPE"))
        hcomm, hcomm_orig, _ = decode_logical(field_value(row, "HCOMMIP"))
        hrig, hrig_orig, _ = decode_logical(field_value(row, "HRIGPKEY"))
        result.records_evaluated += 1
        is_meds = ptype == "MEDS"
        if hcomm is None or hrig is None:
            result.findings.append(
                make_plan_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=idx,
                    plan=plan,
                    plan_original=orig,
                    source_field="HCOMMIP",
                    message="The commission or rating-key indicator could not be read.",
                    status=STATUS_FAIL,
                    failure_category="INVALID_LOGICAL",
                    original_value=f"{hcomm_orig}/{hrig_orig}",
                    expected_condition="Enabled for MEDS plans and disabled for other plans",
                )
            )
            continue
        if is_meds:
            if not hcomm:
                result.findings.append(
                    make_plan_finding(
                        rule=rule,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_region_path=store.data_dir,
                        record_id=idx,
                        plan=plan,
                        plan_original=orig,
                        source_field="HCOMMIP",
                        message="A MEDS plan must have the commission indicator enabled.",
                        status=STATUS_FAIL,
                        failure_category="MEDS_FLAG_MISMATCH",
                        expected_condition="Commission indicator enabled",
                    )
                )
            if not hrig:
                result.findings.append(
                    make_plan_finding(
                        rule=rule,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_region_path=store.data_dir,
                        record_id=idx,
                        plan=plan,
                        plan_original=orig,
                        source_field="HRIGPKEY",
                        message="A MEDS plan must have the rating-key indicator enabled.",
                        status=STATUS_FAIL,
                        failure_category="MEDS_FLAG_MISMATCH",
                        expected_condition="Rating-key indicator enabled",
                    )
                )
            if hcomm and hrig:
                result.passed_count += 1
            continue
        if hcomm or hrig:
            field_name = "HCOMMIP" if hcomm else "HRIGPKEY"
            msg = (
                "This is not a MEDS plan, so the commission indicator must be turned off."
                if hcomm
                else "This is not a MEDS plan, so the rating-key indicator must be turned off."
            )
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
                    failure_category="MEDS_FLAG_MISMATCH",
                    expected_condition="Indicators turned off for non-MEDS plans",
                )
            )
            continue
        result.passed_count += 1
    return finalize_rule_result(result)
