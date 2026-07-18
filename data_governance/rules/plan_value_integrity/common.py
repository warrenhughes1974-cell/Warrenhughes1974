"""Shared multi-source evaluation helpers for DG-PLANVALUES."""

from __future__ import annotations

import json
from dataclasses import dataclass

from data_governance.catalog.governance_items import RuleDefinition
from data_governance.config.settings import PLANVALUE_SOURCE_TABLES
from data_governance.data_access.normalization import (
    normalize_character_casefold,
    normalize_identifier_preserve_zeros,
)
from data_governance.data_access.table_loader import GovernanceDataStore, field_value
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_ERROR, STATUS_FAIL, STATUS_PASS


@dataclass
class SourceRowContext:
    table: str
    record_id: int
    plan: str
    plan_original: str
    gender: str
    uwclass: str
    band: str
    issuest: str
    mort: str
    etimort: str
    effdate_raw: Any


@dataclass
class TableStats:
    reviewed: int = 0
    passed: int = 0
    failed: int = 0
    not_run: int = 0
    not_run_reason: str = ""


def row_context(table: str, record_id: int, row: dict) -> SourceRowContext:
    def _n(name: str) -> tuple[str, str]:
        raw = field_value(row, name)
        norm, orig, is_null = normalize_identifier_preserve_zeros(raw)
        if is_null:
            return "", ""
        return norm or "", orig

    plan, plan_orig = _n("PLAN")
    gender, _ = _n("GENDER")
    uw, _ = _n("UWCLASS")
    band, _ = _n("BAND")
    state, _ = _n("ISSUEST")
    mort, _ = _n("MORT")
    eti, _ = _n("ETIMORT")
    return SourceRowContext(
        table=table,
        record_id=record_id,
        plan=plan,
        plan_original=plan_orig,
        gender=gender,
        uwclass=uw,
        band=band,
        issuest=state,
        mort=mort,
        etimort=eti,
        effdate_raw=field_value(row, "EFFDATE"),
    )


def table_has_field(store: GovernanceDataStore, table: str, field_name: str) -> bool:
    loaded = store.get(table)
    if loaded is None or not loaded.rows:
        # Empty table: check via missing table vs empty — field presence unknown;
        # treat as present so empty tables evaluate zero rows.
        return loaded is not None
    sample = loaded.rows[0]
    return field_value(sample, field_name) is not None or any(
        str(k).strip().upper() == field_name.upper() for k in sample.keys()
    )


def make_planvalue_finding(
    *,
    rule: RuleDefinition,
    run_id: str,
    run_timestamp: str,
    data_region_path: str,
    ctx: SourceRowContext,
    source_field: str,
    original: str,
    normalized: str,
    message: str,
    failure_category: str,
    expected_condition: str,
    reference_table: str = "",
    reference_field: str = "",
    reference_match_count: str = "",
    effective_date: str = "",
    min_allowed_date: str = "",
    max_allowed_date: str = "",
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
        status=STATUS_FAIL,
        source_table=ctx.table,
        source_field=source_field,
        source_record_id=str(ctx.record_id),
        key_value=ctx.plan or normalized or original,
        invalid_value=normalized or original,
        expected_condition=expected_condition,
        actual_condition=message,
        message=message,
        data_region_path=data_region_path,
        original_value=original,
        normalized_value=normalized,
        expected_value="",
        reference_table=reference_table,
        reference_field=reference_field,
        reference_match_count=reference_match_count,
        failure_category=failure_category,
        plan=ctx.plan,
        mortality_table=ctx.mort,
        eti_mortality_table=ctx.etimort,
        gender=ctx.gender,
        underwriting_class=ctx.uwclass,
        band=ctx.band,
        issue_state=ctx.issuest,
        effective_date=effective_date,
        min_allowed_date=min_allowed_date,
        max_allowed_date=max_allowed_date,
    )


def finalize_multi_source_result(
    result: RuleExecutionResult,
    table_stats: dict[str, TableStats],
    extra_metrics: dict | None = None,
) -> RuleExecutionResult:
    result.summary_metrics = {
        "source_table_summary": json.dumps(
            {
                t: {
                    "reviewed": s.reviewed,
                    "passed": s.passed,
                    "failed": s.failed,
                    "not_run": s.not_run,
                    "not_run_reason": s.not_run_reason,
                }
                for t, s in table_stats.items()
            },
            sort_keys=True,
        ),
    }
    if extra_metrics:
        result.summary_metrics.update({k: v for k, v in extra_metrics.items()})
    result.failed_count = len([f for f in result.findings if f.status == STATUS_FAIL])
    error_findings = len([f for f in result.findings if f.status == STATUS_ERROR])
    if result.error_count < error_findings:
        result.error_count = error_findings

    all_skipped = bool(table_stats) and all(
        s.not_run and s.reviewed == 0 for s in table_stats.values()
    )
    if result.failed_count:
        result.status = STATUS_FAIL
    elif result.error_count or error_findings:
        result.status = STATUS_ERROR
    elif all_skipped and result.records_evaluated == 0:
        result.status = STATUS_ERROR
        result.error_count = max(result.error_count, 1)
        if not result.error_message:
            result.error_message = (
                "No applicable source tables were available for evaluation."
            )
    else:
        result.status = STATUS_PASS
    return result


def iter_applicable_source_tables(
    store: GovernanceDataStore,
    *,
    required_field: str | None,
    tables: tuple[str, ...] = PLANVALUE_SOURCE_TABLES,
) -> list[tuple[str, str | None]]:
    """Return (table_name, skip_reason_or_None) for each source table."""
    out: list[tuple[str, str | None]] = []
    for table in tables:
        if store.get(table) is None:
            out.append((table, f"{table} was not loaded."))
            continue
        if required_field and not table_has_field(store, table, required_field):
            out.append((table, f"{table} does not contain field {required_field}."))
            continue
        out.append((table, None))
    return out


def normalize_code(value, *, uppercase: bool = False) -> tuple[str | None, str, bool]:
    norm, orig, is_null = normalize_identifier_preserve_zeros(value)
    if is_null:
        return None, "", True
    if uppercase and norm:
        # Casefold via character helper for letter codes; preserve digits/zeros
        folded, _, _ = normalize_character_casefold(norm)
        return folded or "", orig, False
    return norm or "", orig, False
