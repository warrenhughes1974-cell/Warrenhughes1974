"""DG-QUIKPLAN-001 through 006 — plan code and basic setup."""

from __future__ import annotations

import re

from data_governance.catalog.governance_items import (
    RULE_DG_QUIKPLAN_001,
    RULE_DG_QUIKPLAN_002,
    RULE_DG_QUIKPLAN_003,
    RULE_DG_QUIKPLAN_004,
    RULE_DG_QUIKPLAN_005,
    RULE_DG_QUIKPLAN_006,
)
from data_governance.config.settings import TABLE_QUIKPLAN
from data_governance.data_access.normalization import normalize_character_casefold
from data_governance.data_access.table_loader import field_value
from data_governance.models.findings import RuleExecutionResult
from data_governance.models.statuses import STATUS_FAIL
from data_governance.rules.plan_setup_integrity.common import (
    empty_quikplan_result,
    finalize_rule_result,
    iterate_quikplan_rows,
    make_plan_finding,
    plan_from_row,
    plan_starts_with_a,
)

_PUA_SUFFIXES = ("PA", "XP", "XF", "XS")
_ANNUITY_BASIS = frozenset({"NONQ", "QUAL", "NQIA", "QLIA", "TXBL"})
_ALNUM = re.compile(r"^[A-Z0-9]{6}$")


def _base_result(rule) -> RuleExecutionResult:
    return RuleExecutionResult(
        governance_item_id=rule.governance_item_id,
        rule_id=rule.rule_id,
        rule_name=rule.technical_name,
        business_name=rule.business_name,
        severity=rule.severity,
        status="PASS",
    )


def _require_quikplan(store, rule, *, run_id, run_timestamp) -> RuleExecutionResult | None:
    if store.get(TABLE_QUIKPLAN) is None:
        return empty_quikplan_result(
            rule=rule,
            run_id=run_id,
            run_timestamp=run_timestamp,
            data_region_path=store.data_dir,
        )
    return None


def run_dg_quikplan_001(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_001
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = _base_result(rule)
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, is_null = plan_from_row(row)
        result.records_evaluated += 1
        if is_null or not plan:
            result.findings.append(
                make_plan_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=idx,
                    plan=plan,
                    plan_original=orig,
                    source_field="PLAN",
                    message="The plan code is blank.",
                    status=STATUS_FAIL,
                    failure_category="BLANK_VALUE",
                    original_value=orig,
                    expected_condition="Exactly six characters",
                )
            )
            continue
        if len(plan) != 6:
            result.findings.append(
                make_plan_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=idx,
                    plan=plan,
                    plan_original=orig,
                    source_field="PLAN",
                    message=f"Plan code {plan} does not contain six characters.",
                    status=STATUS_FAIL,
                    failure_category="INVALID_LENGTH",
                    original_value=orig,
                    normalized_value=plan,
                    expected_condition="Exactly six characters",
                )
            )
            continue
        result.passed_count += 1
    return finalize_rule_result(result)


def run_dg_quikplan_002(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_002
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = _base_result(rule)
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, is_null = plan_from_row(row)
        result.records_evaluated += 1
        if is_null or not plan or len(plan) != 6:
            result.findings.append(
                make_plan_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=idx,
                    plan=plan,
                    plan_original=orig,
                    source_field="PLAN",
                    message="The plan code must contain exactly six letters or numbers.",
                    status=STATUS_FAIL,
                    failure_category="INVALID_FORMAT",
                    original_value=orig,
                    expected_condition="Six letters or numbers with no spaces or special characters",
                )
            )
            continue
        upper = plan.upper()
        if " " in plan:
            msg = "The plan code contains a space."
        elif not _ALNUM.match(upper):
            msg = "The plan code contains a special character."
        else:
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
                source_field="PLAN",
                message=msg,
                status=STATUS_FAIL,
                failure_category="INVALID_FORMAT",
                original_value=orig,
                normalized_value=plan,
                expected_condition="Six letters or numbers with no spaces or special characters",
            )
        )
    return finalize_rule_result(result)


def run_dg_quikplan_003(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_003
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = _base_result(rule)
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, is_null = plan_from_row(row)
        result.records_evaluated += 1
        if is_null or not plan:
            result.passed_count += 1
            continue
        suffix = plan[-2:].upper()
        if suffix in _PUA_SUFFIXES:
            result.findings.append(
                make_plan_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=idx,
                    plan=plan,
                    plan_original=orig,
                    source_field="PLAN",
                    message=(
                        f"Plan {plan} ends with {suffix}, which is reserved for paid-up additions."
                    ),
                    status=STATUS_FAIL,
                    failure_category="RESERVED_SUFFIX",
                    original_value=orig,
                    normalized_value=plan,
                    expected_condition="A plan code that does not end in PA, XP, XF, or XS",
                )
            )
            continue
        result.passed_count += 1
    return finalize_rule_result(result)


def run_dg_quikplan_004(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_004
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = _base_result(rule)
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, _ = plan_from_row(row)
        raw = field_value(row, "PAR")
        result.records_evaluated += 1
        text = "" if raw is None else str(raw).strip()
        if text in {"0", "1"}:
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
                source_field="PAR",
                message="The participating-plan setting is invalid.",
                status=STATUS_FAIL,
                failure_category="INVALID_VALUE",
                original_value=text,
                expected_condition="0 or 1",
            )
        )
    return finalize_rule_result(result)


def run_dg_quikplan_005(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_005
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = _base_result(rule)
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, _ = plan_from_row(row)
        basis_raw = field_value(row, "BASIS")
        basis = "" if basis_raw is None else str(basis_raw).strip()
        result.records_evaluated += 1
        if plan_starts_with_a(plan):
            if basis in _ANNUITY_BASIS:
                result.passed_count += 1
                continue
            if not basis:
                msg = f"Plan {plan} has an invalid annuity basis."
            else:
                msg = f"Plan {plan} has an invalid annuity basis."
            result.findings.append(
                make_plan_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=idx,
                    plan=plan,
                    plan_original=orig,
                    source_field="BASIS",
                    message=msg,
                    status=STATUS_FAIL,
                    failure_category="INVALID_BASIS",
                    original_value=basis,
                    expected_condition="NONQ, QUAL, NQIA, QLIA, or TXBL",
                )
            )
            continue
        if basis:
            result.findings.append(
                make_plan_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=idx,
                    plan=plan,
                    plan_original=orig,
                    source_field="BASIS",
                    message=(
                        f"Plan {plan} is not an annuity plan, but an annuity basis is populated."
                    ),
                    status=STATUS_FAIL,
                    failure_category="UNEXPECTED_BASIS",
                    original_value=basis,
                    expected_condition="Blank",
                )
            )
            continue
        result.passed_count += 1
    return finalize_rule_result(result)


def run_dg_quikplan_006(store, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKPLAN_006
    missing = _require_quikplan(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = _base_result(rule)
    for idx, row in iterate_quikplan_rows(store):
        plan, orig, _ = plan_from_row(row)
        raw = field_value(row, "LOANINTX")
        norm, _, is_null = normalize_character_casefold(raw)
        result.records_evaluated += 1
        if is_null or not norm or norm not in {"A", "R"}:
            result.findings.append(
                make_plan_finding(
                    rule=rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=idx,
                    plan=plan,
                    plan_original=orig,
                    source_field="LOANINTX",
                    message="The loan interest option is invalid.",
                    status=STATUS_FAIL,
                    failure_category="INVALID_VALUE",
                    original_value="" if raw is None else str(raw),
                    normalized_value=norm or "",
                    expected_condition="A or R (default A)",
                )
            )
            continue
        result.passed_count += 1
    return finalize_rule_result(result)
