"""DG-PLANVALUES-008 — Effective Date Must Be Within the Approved Range."""

from __future__ import annotations

from datetime import date

from data_governance.catalog.governance_items import RULE_DG_PLANVALUES_008
from data_governance.data_access.normalization import (
    add_calendar_months,
    decode_dbf_date,
    format_iso_date,
    parse_governance_run_date,
)
from data_governance.data_access.table_loader import field_value
from data_governance.models.findings import RuleExecutionResult
from data_governance.rules.plan_value_integrity.common import (
    TableStats,
    finalize_multi_source_result,
    iter_applicable_source_tables,
    make_planvalue_finding,
    row_context,
)

RULE = RULE_DG_PLANVALUES_008
MIN_DATE = date(1900, 1, 1)


def run_dg_planvalues_008(store, *, run_id, run_timestamp):
    result = RuleExecutionResult(
        governance_item_id=RULE.governance_item_id,
        rule_id=RULE.rule_id,
        rule_name=RULE.technical_name,
        business_name=RULE.business_name,
        severity=RULE.severity,
        status="PASS",
    )
    table_stats: dict[str, TableStats] = {}
    within = before_min = after_max = blank = null = invalid = 0

    run_date = parse_governance_run_date(run_timestamp)
    max_date = add_calendar_months(run_date, 12)
    min_iso = format_iso_date(MIN_DATE)
    max_iso = format_iso_date(max_date)

    for table, skip in iter_applicable_source_tables(store, required_field="EFFDATE"):
        stats = TableStats()
        table_stats[table] = stats
        if skip:
            stats.not_run = 1
            stats.not_run_reason = skip
            continue

        for idx, row in enumerate(store.get(table).rows, start=1):
            ctx = row_context(table, idx, row)
            raw = field_value(row, "EFFDATE")
            decoded = decode_dbf_date(raw)
            stats.reviewed += 1
            result.records_evaluated += 1
            eff_display = decoded.decoded_display or decoded.original_display

            if decoded.is_null and not decoded.original_display:
                null += 1
                stats.failed += 1
                result.findings.append(
                    make_planvalue_finding(
                        rule=RULE,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_region_path=store.data_dir,
                        ctx=ctx,
                        source_field="EFFDATE",
                        original="",
                        normalized="",
                        message=(
                            f"{table} plan '{ctx.plan or '(blank)'}' contains an invalid "
                            f"effective date value."
                        ),
                        failure_category="NULL_VALUE",
                        expected_condition=(
                            f"EFFDATE between {min_iso} and {max_iso} inclusive"
                        ),
                        effective_date="",
                        min_allowed_date=min_iso,
                        max_allowed_date=max_iso,
                    )
                )
                continue

            if decoded.is_blank:
                blank += 1
                stats.failed += 1
                result.findings.append(
                    make_planvalue_finding(
                        rule=RULE,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_region_path=store.data_dir,
                        ctx=ctx,
                        source_field="EFFDATE",
                        original=decoded.original_display,
                        normalized="",
                        message=(
                            f"{table} plan '{ctx.plan or '(blank)'}' contains an invalid "
                            f"effective date value."
                        ),
                        failure_category="BLANK_VALUE",
                        expected_condition=(
                            f"EFFDATE between {min_iso} and {max_iso} inclusive"
                        ),
                        effective_date="",
                        min_allowed_date=min_iso,
                        max_allowed_date=max_iso,
                    )
                )
                continue

            if decoded.is_unreadable or decoded.date_value is None:
                invalid += 1
                stats.failed += 1
                result.findings.append(
                    make_planvalue_finding(
                        rule=RULE,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_region_path=store.data_dir,
                        ctx=ctx,
                        source_field="EFFDATE",
                        original=decoded.original_display,
                        normalized=decoded.decoded_display,
                        message=(
                            f"{table} plan '{ctx.plan or '(blank)'}' contains an invalid "
                            f"effective date value."
                        ),
                        failure_category="INVALID_DATE",
                        expected_condition=(
                            f"EFFDATE between {min_iso} and {max_iso} inclusive"
                        ),
                        effective_date=eff_display,
                        min_allowed_date=min_iso,
                        max_allowed_date=max_iso,
                    )
                )
                continue

            d = decoded.date_value
            if d < MIN_DATE:
                before_min += 1
                stats.failed += 1
                result.findings.append(
                    make_planvalue_finding(
                        rule=RULE,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_region_path=store.data_dir,
                        ctx=ctx,
                        source_field="EFFDATE",
                        original=decoded.original_display,
                        normalized=decoded.decoded_display,
                        message=(
                            f"{table} plan '{ctx.plan or '(blank)'}' has "
                            f"EFFDATE='{decoded.decoded_display}'. Effective dates may not "
                            f"be earlier than January 1, 1900."
                        ),
                        failure_category="DATE_BEFORE_MINIMUM",
                        expected_condition=(
                            f"EFFDATE between {min_iso} and {max_iso} inclusive"
                        ),
                        effective_date=decoded.decoded_display,
                        min_allowed_date=min_iso,
                        max_allowed_date=max_iso,
                    )
                )
                continue

            if d > max_date:
                after_max += 1
                stats.failed += 1
                result.findings.append(
                    make_planvalue_finding(
                        rule=RULE,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_region_path=store.data_dir,
                        ctx=ctx,
                        source_field="EFFDATE",
                        original=decoded.original_display,
                        normalized=decoded.decoded_display,
                        message=(
                            f"{table} plan '{ctx.plan or '(blank)'}' has "
                            f"EFFDATE='{decoded.decoded_display}'. The maximum permitted "
                            f"date for this run is '{max_iso}'."
                        ),
                        failure_category="DATE_AFTER_MAXIMUM",
                        expected_condition=(
                            f"EFFDATE between {min_iso} and {max_iso} inclusive"
                        ),
                        effective_date=decoded.decoded_display,
                        min_allowed_date=min_iso,
                        max_allowed_date=max_iso,
                    )
                )
                continue

            within += 1
            stats.passed += 1
            result.passed_count += 1

    return finalize_multi_source_result(
        result,
        table_stats,
        {
            "dates_within_range": within,
            "dates_before_minimum": before_min,
            "dates_after_maximum": after_max,
            "blank_dates": blank,
            "null_dates": null,
            "unreadable_dates": invalid,
            "min_allowed_date": min_iso,
            "max_allowed_date": max_iso,
            "governance_run_date": format_iso_date(run_date),
            "calendar_month_arithmetic": (
                "add_calendar_months clamps day to target month length "
                "(e.g. 2024-02-29 + 12 months → 2025-02-28)"
            ),
        },
    )
