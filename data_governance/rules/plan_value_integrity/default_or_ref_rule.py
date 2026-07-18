"""Shared default-or-reference evaluation for GENDER / UWCLASS / BAND."""

from __future__ import annotations

from data_governance.catalog.governance_items import RuleDefinition
from data_governance.data_access.table_loader import GovernanceDataStore, field_value
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_ERROR, STATUS_FAIL
from data_governance.rules.plan_value_integrity.common import (
    TableStats,
    finalize_multi_source_result,
    iter_applicable_source_tables,
    make_planvalue_finding,
    normalize_code,
    row_context,
)
from data_governance.rules.plan_value_integrity.reference_index import (
    build_composite_plan_code_index,
    composite_key,
)


def run_default_or_composite_reference(
    store: GovernanceDataStore,
    *,
    rule: RuleDefinition,
    source_field: str,
    default_value: str,
    ref_table: str,
    ref_plan_field: str,
    ref_code_field: str,
    label: str,
    run_id: str,
    run_timestamp: str,
    uppercase_code: bool = True,
) -> RuleExecutionResult:
    result = RuleExecutionResult(
        governance_item_id=rule.governance_item_id,
        rule_id=rule.rule_id,
        rule_name=rule.technical_name,
        business_name=rule.business_name,
        severity=rule.severity,
        status="PASS",
    )
    table_stats: dict[str, TableStats] = {}
    valid_defaults = valid_refs = missing = ambiguous = blank = null = unresolved = 0

    ref = store.get(ref_table)
    index = None
    if ref is not None:
        index = build_composite_plan_code_index(
            ref.rows,
            plan_field=ref_plan_field,
            code_field=ref_code_field,
            uppercase_code=uppercase_code,
        )

    for table, skip in iter_applicable_source_tables(store, required_field=source_field):
        stats = TableStats()
        table_stats[table] = stats
        if skip:
            stats.not_run = 1
            stats.not_run_reason = skip
            continue

        for idx, row in enumerate(store.get(table).rows, start=1):
            ctx = row_context(table, idx, row)
            raw = field_value(row, source_field)
            norm, orig, is_null = normalize_code(raw, uppercase=False)
            if uppercase_code and norm:
                norm = norm.upper()

            if is_null:
                null += 1
                stats.reviewed += 1
                stats.failed += 1
                result.records_evaluated += 1
                result.findings.append(
                    make_planvalue_finding(
                        rule=rule,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_region_path=store.data_dir,
                        ctx=ctx,
                        source_field=source_field,
                        original="",
                        normalized="",
                        message=(
                            f"{table} plan '{ctx.plan or '(blank)'}' contains a null {label}."
                        ),
                        failure_category="NULL_VALUE",
                        expected_condition=(
                            f"{source_field} is '{default_value}' or exists once in "
                            f"{ref_table}.{ref_code_field} for the same PLAN"
                        ),
                        reference_table=ref_table,
                        reference_field=ref_code_field,
                        reference_match_count="0",
                    )
                )
                continue

            if norm == "":
                blank += 1
                stats.reviewed += 1
                stats.failed += 1
                result.records_evaluated += 1
                result.findings.append(
                    make_planvalue_finding(
                        rule=rule,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_region_path=store.data_dir,
                        ctx=ctx,
                        source_field=source_field,
                        original=orig,
                        normalized="",
                        message=(
                            f"{table} plan '{ctx.plan or '(blank)'}' contains a blank {label}."
                        ),
                        failure_category="BLANK_VALUE",
                        expected_condition=(
                            f"{source_field} is '{default_value}' or exists once in "
                            f"{ref_table}.{ref_code_field} for the same PLAN"
                        ),
                        reference_table=ref_table,
                        reference_field=ref_code_field,
                        reference_match_count="0",
                    )
                )
                continue

            if norm == default_value:
                valid_defaults += 1
                stats.reviewed += 1
                stats.passed += 1
                result.records_evaluated += 1
                result.passed_count += 1
                continue

            if index is None:
                # Reference table unavailable — do not invent MISSING_REFERENCE findings
                unresolved += 1
                result.error_count += 1
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
                        source_table=table,
                        source_field=source_field,
                        source_record_id=str(idx),
                        key_value=ctx.plan or norm,
                        invalid_value=norm,
                        expected_condition=(
                            f"{source_field} is '{default_value}' or exists once in "
                            f"{ref_table}.{ref_code_field} for the same PLAN"
                        ),
                        actual_condition=(
                            f"Reference table {ref_table} was not loaded; "
                            f"non-default {label} '{norm}' could not be validated."
                        ),
                        message=(
                            f"{table} plan '{ctx.plan or '(blank)'}' uses {label} '{norm}'. "
                            f"The value is not the default '{default_value}', and {ref_table} "
                            f"was not available for reference validation."
                        ),
                        data_region_path=store.data_dir,
                        original_value=orig,
                        normalized_value=norm,
                        reference_table=ref_table,
                        reference_field=ref_code_field,
                        failure_category="REFERENCE_TABLE_UNAVAILABLE",
                        plan=ctx.plan,
                        mortality_table=ctx.mort,
                        eti_mortality_table=ctx.etimort,
                        gender=ctx.gender,
                        underwriting_class=ctx.uwclass,
                        band=ctx.band,
                        issue_state=ctx.issuest,
                    )
                )
                continue

            key = composite_key(ctx.plan, norm, uppercase_code=uppercase_code)
            count = index.count(key)
            stats.reviewed += 1
            result.records_evaluated += 1
            if count == 0:
                missing += 1
                stats.failed += 1
                result.findings.append(
                    make_planvalue_finding(
                        rule=rule,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_region_path=store.data_dir,
                        ctx=ctx,
                        source_field=source_field,
                        original=orig,
                        normalized=norm,
                        message=(
                            f"{table} plan '{ctx.plan or '(blank)'}' uses {label} '{norm}'. "
                            f"The value must be '{default_value}' or a valid code defined in "
                            f"{ref_table}."
                        ),
                        failure_category="MISSING_REFERENCE",
                        expected_condition=(
                            f"{source_field} is '{default_value}' or exists once in "
                            f"{ref_table}.{ref_code_field} for the same PLAN"
                        ),
                        reference_table=ref_table,
                        reference_field=ref_code_field,
                        reference_match_count="0",
                    )
                )
                continue
            if count > 1:
                ambiguous += 1
                stats.failed += 1
                result.findings.append(
                    make_planvalue_finding(
                        rule=rule,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_region_path=store.data_dir,
                        ctx=ctx,
                        source_field=source_field,
                        original=orig,
                        normalized=norm,
                        message=(
                            f"{table} plan '{ctx.plan or '(blank)'}' uses {label} '{norm}', "
                            f"but {ref_table} contains {count} matching records for that plan."
                        ),
                        failure_category="AMBIGUOUS_REFERENCE",
                        expected_condition=(
                            f"{source_field} is '{default_value}' or exists once in "
                            f"{ref_table}.{ref_code_field} for the same PLAN"
                        ),
                        reference_table=ref_table,
                        reference_field=ref_code_field,
                        reference_match_count=str(count),
                    )
                )
                continue

            valid_refs += 1
            stats.passed += 1
            result.passed_count += 1

    finalize_multi_source_result(
        result,
        table_stats,
        {
            "valid_defaults": valid_defaults,
            "valid_reference_matches": valid_refs,
            "missing_references": missing,
            "ambiguous_references": ambiguous,
            "blank_values": blank,
            "null_values": null,
            "unresolved_reference_validations": unresolved,
            "approved_default": default_value,
        },
    )
    if unresolved and result.status != STATUS_FAIL:
        result.status = STATUS_ERROR
        if not result.error_message:
            result.error_message = (
                f"Reference table {ref_table} was not loaded; non-default values "
                f"could not be reference-validated."
            )
    return result
