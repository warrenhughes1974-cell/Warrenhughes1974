"""DG-QUIKACTG-001 — Unique QuikActg company + plan (MCOMP + MPLAN).

Verified schema: QuikActg has no single account-number key column.
Composite record key = MCOMP (C1) + MPLAN (C6).
"""

from __future__ import annotations

from collections import defaultdict

from data_governance.catalog.governance_items import RULE_DG_QUIKACTG_001
from data_governance.config.settings import (
    QUIKACTG_COMPANY_FIELD,
    QUIKACTG_PLAN_FIELD,
    TABLE_QUIKACTG,
)
from data_governance.data_access.normalization import normalize_identifier_preserve_zeros
from data_governance.data_access.table_loader import GovernanceDataStore, field_value
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_ERROR, STATUS_FAIL, STATUS_PASS

RULE = RULE_DG_QUIKACTG_001
COMP_FIELD = QUIKACTG_COMPANY_FIELD
PLAN_FIELD = QUIKACTG_PLAN_FIELD


def _display_key(company: str, plan: str) -> str:
    return f"Company {company} | Plan {plan}"


def run_dg_quikactg_001(
    store: GovernanceDataStore,
    *,
    run_id: str,
    run_timestamp: str,
) -> RuleExecutionResult:
    result = RuleExecutionResult(
        governance_item_id=RULE.governance_item_id,
        rule_id=RULE.rule_id,
        rule_name=RULE.technical_name,
        business_name=RULE.business_name,
        severity=RULE.severity,
        status=STATUS_PASS,
    )

    actg = store.get(TABLE_QUIKACTG)
    if actg is None:
        err = store.load_error(TABLE_QUIKACTG) or f"{TABLE_QUIKACTG} was not loaded."
        result.status = STATUS_ERROR
        result.error_count = 1
        result.error_message = err
        result.findings.append(
            make_finding(
                run_id=run_id,
                run_timestamp=run_timestamp,
                governance_item_id=RULE.governance_item_id,
                rule_id=RULE.rule_id,
                rule_name=RULE.technical_name,
                business_name=RULE.business_name,
                description=RULE.purpose,
                severity=RULE.severity,
                status=STATUS_ERROR,
                source_table=TABLE_QUIKACTG,
                source_field=f"{COMP_FIELD},{PLAN_FIELD}",
                data_region_path=store.data_dir,
                message=err,
                company_code_source_field=COMP_FIELD,
                account_number_source_field=PLAN_FIELD,
            )
        )
        return result

    rows = actg.rows
    result.records_evaluated = len(rows)

    blank_company = 0
    null_company = 0
    blank_plan = 0
    null_plan = 0
    companies: set[str] = set()
    plans: set[str] = set()
    combo_to_records: dict[tuple[str, str], list[int]] = defaultdict(list)
    # Track rows that already failed blank/null so they are not also counted as combos
    failed_blank_null: set[int] = set()

    parsed: list[tuple[int, str, str, str, str, bool, bool]] = []

    for idx, row in enumerate(rows, start=1):
        raw_comp = field_value(row, COMP_FIELD)
        raw_plan = field_value(row, PLAN_FIELD)
        norm_comp, orig_comp, comp_null = normalize_identifier_preserve_zeros(raw_comp)
        norm_plan, orig_plan, plan_null = normalize_identifier_preserve_zeros(raw_plan)

        if comp_null:
            null_company += 1
            failed_blank_null.add(idx)
            result.findings.append(
                _finding(
                    run_id,
                    run_timestamp,
                    store.data_dir,
                    idx,
                    orig_comp,
                    "",
                    orig_plan,
                    norm_plan or "",
                    (
                        f"A QuikActg record for plan code '{norm_plan or '(blank)'}' "
                        f"does not contain a company code."
                        if (norm_plan or "") != ""
                        else "A QuikActg record does not contain a company code."
                    ),
                )
            )
        elif norm_comp == "":
            blank_company += 1
            failed_blank_null.add(idx)
            result.findings.append(
                _finding(
                    run_id,
                    run_timestamp,
                    store.data_dir,
                    idx,
                    orig_comp,
                    "",
                    orig_plan,
                    norm_plan or "",
                    (
                        f"A QuikActg record for plan code '{norm_plan}' "
                        f"does not contain a company code."
                        if norm_plan
                        else "A QuikActg record does not contain a company code."
                    ),
                )
            )

        if plan_null:
            null_plan += 1
            failed_blank_null.add(idx)
            result.findings.append(
                _finding(
                    run_id,
                    run_timestamp,
                    store.data_dir,
                    idx,
                    orig_comp,
                    norm_comp or "",
                    orig_plan,
                    "",
                    (
                        f"A QuikActg record for company code '{norm_comp}' "
                        f"does not contain a plan code (MPLAN)."
                        if norm_comp
                        else "A QuikActg record does not contain a plan code (MPLAN)."
                    ),
                )
            )
        elif not plan_null and norm_plan == "":
            blank_plan += 1
            failed_blank_null.add(idx)
            result.findings.append(
                _finding(
                    run_id,
                    run_timestamp,
                    store.data_dir,
                    idx,
                    orig_comp,
                    norm_comp or "",
                    orig_plan,
                    "",
                    (
                        f"A QuikActg record for company code '{norm_comp}' "
                        f"does not contain a plan code (MPLAN)."
                        if norm_comp
                        else "A QuikActg record does not contain a plan code (MPLAN)."
                    ),
                )
            )

        if idx in failed_blank_null:
            continue

        assert norm_comp is not None and norm_plan is not None
        companies.add(norm_comp)
        plans.add(norm_plan)
        combo_to_records[(norm_comp, norm_plan)].append(idx)
        parsed.append((idx, orig_comp, norm_comp, orig_plan, norm_plan, False, False))

    duplicate_combos = 0
    records_in_dupes = 0
    for (comp, plan), record_nos in sorted(combo_to_records.items()):
        if len(record_nos) > 1:
            duplicate_combos += 1
            records_in_dupes += len(record_nos)
            for record_no in record_nos:
                # recover originals from parsed
                orig_c, orig_p = "", ""
                for p in parsed:
                    if p[0] == record_no:
                        orig_c, orig_p = p[1], p[3]
                        break
                result.findings.append(
                    _finding(
                        run_id,
                        run_timestamp,
                        store.data_dir,
                        record_no,
                        orig_c,
                        comp,
                        orig_p,
                        plan,
                        (
                            f"QuikActg contains {len(record_nos)} records for company code "
                            f"'{comp}' and plan code '{plan}'. Each company-and-plan "
                            f"combination must be unique."
                        ),
                        duplicate_count=str(len(record_nos)),
                    )
                )

    valid = sum(1 for nos in combo_to_records.values() if len(nos) == 1)
    result.passed_count = valid
    result.failed_count = len([f for f in result.findings if f.status == STATUS_FAIL])
    result.summary_metrics = {
        "distinct_company_codes": len(companies),
        "distinct_account_numbers": len(plans),  # plan codes (MPLAN)
        "distinct_company_account_combinations": len(combo_to_records),
        "duplicate_combinations": duplicate_combos,
        "records_involved_in_duplicates": records_in_dupes,
        "blank_company_codes": blank_company,
        "null_company_codes": null_company,
        "blank_account_numbers": blank_plan,
        "null_account_numbers": null_plan,
    }
    result.status = STATUS_FAIL if result.failed_count else STATUS_PASS
    return result


def _finding(
    run_id: str,
    run_timestamp: str,
    data_region_path: str,
    record_id: int,
    orig_comp: str,
    norm_comp: str,
    orig_plan: str,
    norm_plan: str,
    message: str,
    duplicate_count: str = "",
):
    composite = _display_key(norm_comp, norm_plan) if norm_comp and norm_plan else ""
    return make_finding(
        run_id=run_id,
        run_timestamp=run_timestamp,
        governance_item_id=RULE.governance_item_id,
        rule_id=RULE.rule_id,
        rule_name=RULE.technical_name,
        business_name=RULE.business_name,
        description=RULE.purpose,
        severity=RULE.severity,
        status=STATUS_FAIL,
        source_table=TABLE_QUIKACTG,
        source_field=f"{COMP_FIELD},{PLAN_FIELD}",
        source_record_id=str(record_id),
        key_value=composite,
        invalid_value=composite or norm_comp or norm_plan,
        expected_condition="Unique normalized MCOMP + MPLAN combination",
        actual_condition=message,
        message=message,
        data_region_path=data_region_path,
        company_code=norm_comp,
        company_code_source_field=COMP_FIELD,
        account_number_source_field=PLAN_FIELD,
        original_company_code=orig_comp,
        normalized_company_code=norm_comp,
        original_account_number=orig_plan,
        normalized_account_number=norm_plan,
        composite_business_key=composite,
        duplicate_count=duplicate_count,
    )
