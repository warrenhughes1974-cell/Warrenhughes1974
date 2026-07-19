"""DG-PLANVALUES-001/002/003 — MORT, ETIMORT, PLAN reference rules."""

from __future__ import annotations

from data_governance.catalog.governance_items import (
    RULE_DG_PLANVALUES_001,
    RULE_DG_PLANVALUES_002,
    RULE_DG_PLANVALUES_003,
)
from data_governance.config.settings import TABLE_QUIKPLAN, TABLE_QUIKQXS
from data_governance.data_access.table_loader import GovernanceDataStore, field_value
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_ERROR
from data_governance.rules.plan_value_integrity.common import (
    TableStats,
    finalize_multi_source_result,
    iter_applicable_source_tables,
    make_planvalue_finding,
    normalize_code,
    row_context,
)
from data_governance.rules.plan_value_integrity.reference_index import build_single_field_index


def _run_simple_reference(
    store: GovernanceDataStore,
    *,
    rule,
    source_field: str,
    required_field: str,
    ref_table: str,
    ref_field: str,
    label: str,
    run_id: str,
    run_timestamp: str,
    allow_blank: bool = False,
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
    valid_refs = missing = ambiguous = blank = null = skipped_blank = 0

    # Always record per-source availability even when the reference table is missing
    for table, skip in iter_applicable_source_tables(store, required_field=required_field):
        stats = TableStats()
        table_stats[table] = stats
        if skip:
            stats.not_run = 1
            stats.not_run_reason = skip

    ref = store.get(ref_table)
    if ref is None:
        result.status = STATUS_ERROR
        result.error_count = 1
        result.error_message = f"Required reference table not loaded: {ref_table}"
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
                source_table=ref_table,
                source_field=source_field,
                data_region_path=store.data_dir,
                message=result.error_message,
                reference_table=ref_table,
                reference_field=ref_field,
                failure_category="MISSING_REFERENCE_TABLE",
            )
        )
        return finalize_multi_source_result(result, table_stats)

    index = build_single_field_index(ref.rows, ref_field, uppercase=False)

    for table, skip in iter_applicable_source_tables(store, required_field=required_field):
        stats = table_stats[table]
        if skip:
            continue

        for idx, row in enumerate(store.get(table).rows, start=1):
            ctx = row_context(table, idx, row)
            raw = field_value(row, source_field)
            norm, orig, is_null = normalize_code(raw, uppercase=False)

            # DG-R-011: MORT/ETIMORT blank/null are optional (populated-only reference check).
            if allow_blank and (is_null or norm == ""):
                skipped_blank += 1
                continue

            stats.reviewed += 1
            result.records_evaluated += 1

            if is_null:
                null += 1
                stats.failed += 1
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
                        message=f"{table} plan '{ctx.plan or '(blank)'}' contains a null {label}.",
                        failure_category="NULL_VALUE",
                        expected_condition=f"{source_field} exists once in {ref_table}.{ref_field}",
                        reference_table=ref_table,
                        reference_field=ref_field,
                        reference_match_count="0",
                    )
                )
                continue

            if norm == "":
                blank += 1
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
                        normalized="",
                        message=f"{table} plan '{ctx.plan or '(blank)'}' contains a blank {label}.",
                        failure_category="BLANK_VALUE",
                        expected_condition=f"{source_field} exists once in {ref_table}.{ref_field}",
                        reference_table=ref_table,
                        reference_field=ref_field,
                        reference_match_count="0",
                    )
                )
                continue

            count = index.count(norm)
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
                            f"{table} plan '{ctx.plan or '(blank)'}' uses {label} '{norm}', "
                            f"but that value does not exist in {ref_table}."
                        ),
                        failure_category="MISSING_REFERENCE",
                        expected_condition=f"{source_field} exists once in {ref_table}.{ref_field}",
                        reference_table=ref_table,
                        reference_field=ref_field,
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
                            f"but {ref_table} contains {count} matching records."
                        ),
                        failure_category="AMBIGUOUS_REFERENCE",
                        expected_condition=f"{source_field} exists once in {ref_table}.{ref_field}",
                        reference_table=ref_table,
                        reference_field=ref_field,
                        reference_match_count=str(count),
                    )
                )
                continue

            valid_refs += 1
            stats.passed += 1
            result.passed_count += 1

    return finalize_multi_source_result(
        result,
        table_stats,
        {
            "valid_defaults": 0,
            "valid_reference_matches": valid_refs,
            "missing_references": missing,
            "ambiguous_references": ambiguous,
            "blank_values": blank,
            "null_values": null,
            "skipped_blank_or_null": skipped_blank,
        },
    )


def run_dg_planvalues_001(store, *, run_id, run_timestamp):
    # DG-R-011: blank/null MORT skipped; only populated codes must exist in QuikQxs.
    return _run_simple_reference(
        store,
        rule=RULE_DG_PLANVALUES_001,
        source_field="MORT",
        required_field="MORT",
        ref_table=TABLE_QUIKQXS,
        ref_field="MORT",
        label="mortality table",
        run_id=run_id,
        run_timestamp=run_timestamp,
        allow_blank=True,
    )


def run_dg_planvalues_002(store, *, run_id, run_timestamp):
    # DG-R-011: blank/null ETIMORT skipped; only populated codes must exist in QuikQxs.
    return _run_simple_reference(
        store,
        rule=RULE_DG_PLANVALUES_002,
        source_field="ETIMORT",
        required_field="ETIMORT",
        ref_table=TABLE_QUIKQXS,
        ref_field="MORT",
        label="ETI mortality table",
        run_id=run_id,
        run_timestamp=run_timestamp,
        allow_blank=True,
    )


def run_dg_planvalues_003(store, *, run_id, run_timestamp):
    return _run_simple_reference(
        store,
        rule=RULE_DG_PLANVALUES_003,
        source_field="PLAN",
        required_field="PLAN",
        ref_table=TABLE_QUIKPLAN,
        ref_field="PLAN",
        label="plan",
        run_id=run_id,
        run_timestamp=run_timestamp,
    )
