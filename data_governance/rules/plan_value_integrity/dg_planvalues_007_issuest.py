"""DG-PLANVALUES-007 — Issue State Must Be 00 or a Valid State Abbreviation."""

from __future__ import annotations

from data_governance.catalog.governance_items import RULE_DG_PLANVALUES_007
from data_governance.data_access.table_loader import field_value
from data_governance.models.findings import RuleExecutionResult
from data_governance.rules.plan_value_integrity.common import (
    TableStats,
    finalize_multi_source_result,
    iter_applicable_source_tables,
    make_planvalue_finding,
    normalize_code,
    row_context,
)
from data_governance.rules.plan_value_integrity.us_states import (
    APPROVED_US_STATE_ABBREVIATIONS,
)

RULE = RULE_DG_PLANVALUES_007
DEFAULT = "00"


def run_dg_planvalues_007(store, *, run_id, run_timestamp):
    result = RuleExecutionResult(
        governance_item_id=RULE.governance_item_id,
        rule_id=RULE.rule_id,
        rule_name=RULE.technical_name,
        business_name=RULE.business_name,
        severity=RULE.severity,
        status="PASS",
    )
    table_stats: dict[str, TableStats] = {}
    using_00 = using_state = invalid = blank = null = 0
    approved_sorted = ",".join(sorted(APPROVED_US_STATE_ABBREVIATIONS))

    for table, skip in iter_applicable_source_tables(store, required_field="ISSUEST"):
        stats = TableStats()
        table_stats[table] = stats
        if skip:
            stats.not_run = 1
            stats.not_run_reason = skip
            continue

        for idx, row in enumerate(store.get(table).rows, start=1):
            ctx = row_context(table, idx, row)
            raw = field_value(row, "ISSUEST")
            norm, orig, is_null = normalize_code(raw, uppercase=True)
            stats.reviewed += 1
            result.records_evaluated += 1

            if is_null:
                null += 1
                stats.failed += 1
                result.findings.append(
                    make_planvalue_finding(
                        rule=RULE,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_region_path=store.data_dir,
                        ctx=ctx,
                        source_field="ISSUEST",
                        original="",
                        normalized="",
                        message=(
                            f"{table} plan '{ctx.plan or '(blank)'}' contains a null issue state."
                        ),
                        failure_category="NULL_VALUE",
                        expected_condition="ISSUEST is '00' or an approved US state/DC abbreviation",
                    )
                )
                continue

            if norm == "":
                blank += 1
                stats.failed += 1
                result.findings.append(
                    make_planvalue_finding(
                        rule=RULE,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_region_path=store.data_dir,
                        ctx=ctx,
                        source_field="ISSUEST",
                        original=orig,
                        normalized="",
                        message=(
                            f"{table} plan '{ctx.plan or '(blank)'}' contains a blank issue state."
                        ),
                        failure_category="BLANK_VALUE",
                        expected_condition="ISSUEST is '00' or an approved US state/DC abbreviation",
                    )
                )
                continue

            if norm == DEFAULT:
                using_00 += 1
                stats.passed += 1
                result.passed_count += 1
                continue

            if len(norm) != 2:
                invalid += 1
                stats.failed += 1
                result.findings.append(
                    make_planvalue_finding(
                        rule=RULE,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_region_path=store.data_dir,
                        ctx=ctx,
                        source_field="ISSUEST",
                        original=orig,
                        normalized=norm,
                        message=(
                            f"{table} plan '{ctx.plan or '(blank)'}' uses issue state '{norm}'. "
                            f"The value must be '{DEFAULT}' or a valid state abbreviation."
                        ),
                        failure_category="INVALID_STATE",
                        expected_condition="ISSUEST is '00' or an approved two-character US state/DC abbreviation",
                    )
                )
                continue

            if norm in APPROVED_US_STATE_ABBREVIATIONS:
                using_state += 1
                stats.passed += 1
                result.passed_count += 1
                continue

            invalid += 1
            stats.failed += 1
            result.findings.append(
                make_planvalue_finding(
                    rule=RULE,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    ctx=ctx,
                    source_field="ISSUEST",
                    original=orig,
                    normalized=norm,
                    message=(
                        f"{table} plan '{ctx.plan or '(blank)'}' uses issue state '{norm}'. "
                        f"The value must be '{DEFAULT}' or a valid state abbreviation."
                    ),
                    failure_category="INVALID_STATE",
                    expected_condition="ISSUEST is '00' or an approved two-character US state/DC abbreviation",
                )
            )

    return finalize_multi_source_result(
        result,
        table_stats,
        {
            "records_using_00": using_00,
            "records_using_valid_states": using_state,
            "invalid_state_codes": invalid,
            "blank_values": blank,
            "null_values": null,
            "approved_state_abbreviations": approved_sorted,
            "approved_default": DEFAULT,
        },
    )
