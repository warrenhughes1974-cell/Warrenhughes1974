"""DG-QUIKLIST-002 — QuikList company code must exist in QuikComp."""

from __future__ import annotations

from data_governance.catalog.governance_items import RULE_DG_QUIKLIST_002
from data_governance.config.settings import TABLE_QUIKCOMP, TABLE_QUIKLIST
from data_governance.data_access.normalization import normalize_identifier_preserve_zeros
from data_governance.data_access.table_loader import GovernanceDataStore, field_value
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_ERROR, STATUS_FAIL, STATUS_PASS
from data_governance.rules.company_code_integrity.company_code_index import (
    build_company_code_index,
)
from data_governance.rules.group_billing_integrity.helpers import (
    group_display,
    group_label,
)

RULE = RULE_DG_QUIKLIST_002


def run_dg_quiklist_002(
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

    quiklist = store.get(TABLE_QUIKLIST)
    comp = store.get(TABLE_QUIKCOMP)
    if quiklist is None or comp is None:
        missing = []
        if quiklist is None:
            missing.append(TABLE_QUIKLIST)
        if comp is None:
            missing.append(TABLE_QUIKCOMP)
        result.status = STATUS_ERROR
        result.error_count = 1
        result.error_message = "Required table(s) not loaded: " + ", ".join(missing)
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
                source_table=TABLE_QUIKLIST,
                source_field="MCOMP",
                data_region_path=store.data_dir,
                message=result.error_message,
                reference_table=TABLE_QUIKCOMP,
                reference_field="MCOMP",
            )
        )
        return result

    # Reuse shared QuikComp normalization / index from Item 1
    index = build_company_code_index(comp.rows)
    rows = quiklist.rows
    result.records_evaluated = len(rows)

    valid_refs = 0
    missing_refs = 0
    blank_refs = 0
    null_refs = 0
    dup_refs = 0

    for idx, row in enumerate(rows, start=1):
        raw_comp = field_value(row, "MCOMP")
        norm_comp, orig_comp, comp_null = normalize_identifier_preserve_zeros(raw_comp)
        g_norm, g_orig, g_null = group_label(row)
        g_label = group_display(g_norm, g_null)

        if comp_null:
            null_refs += 1
            result.findings.append(
                _ref_finding(
                    run_id,
                    run_timestamp,
                    store.data_dir,
                    idx,
                    g_norm or "",
                    g_orig,
                    orig_comp,
                    "",
                    f"Group number '{g_label}' does not contain a company code.",
                    match_count="0",
                )
            )
            continue

        if norm_comp == "":
            blank_refs += 1
            result.findings.append(
                _ref_finding(
                    run_id,
                    run_timestamp,
                    store.data_dir,
                    idx,
                    g_norm or "",
                    g_orig,
                    orig_comp,
                    "",
                    f"Group number '{g_label}' does not contain a company code.",
                    match_count="0",
                )
            )
            continue

        if not index.exists(norm_comp):
            missing_refs += 1
            result.findings.append(
                _ref_finding(
                    run_id,
                    run_timestamp,
                    store.data_dir,
                    idx,
                    g_norm or "",
                    g_orig,
                    orig_comp,
                    norm_comp,
                    (
                        f"Group number '{g_label}' uses company code '{norm_comp}', "
                        f"but company code '{norm_comp}' does not exist in QuikComp."
                    ),
                    match_count="0",
                )
            )
            continue

        if index.is_duplicated(norm_comp):
            dup_refs += 1
            result.findings.append(
                _ref_finding(
                    run_id,
                    run_timestamp,
                    store.data_dir,
                    idx,
                    g_norm or "",
                    g_orig,
                    orig_comp,
                    norm_comp,
                    (
                        f"Group number '{g_label}' uses company code '{norm_comp}', "
                        f"but QuikComp contains multiple records for company code "
                        f"'{norm_comp}'."
                    ),
                    match_count=str(index.count(norm_comp)),
                )
            )
            continue

        valid_refs += 1

    result.passed_count = valid_refs
    result.failed_count = len([f for f in result.findings if f.status == STATUS_FAIL])
    result.summary_metrics = {
        "valid_company_references": valid_refs,
        "missing_company_references": missing_refs,
        "blank_company_references": blank_refs,
        "null_company_references": null_refs,
        "references_to_duplicated_quikcomp": dup_refs,
    }
    result.status = STATUS_FAIL if result.failed_count else STATUS_PASS
    return result


def _ref_finding(
    run_id: str,
    run_timestamp: str,
    data_region_path: str,
    record_id: int,
    group_number: str,
    original_group: str,
    orig_comp: str,
    norm_comp: str,
    message: str,
    match_count: str,
):
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
        source_table=TABLE_QUIKLIST,
        source_field="MCOMP",
        source_record_id=str(record_id),
        key_value=group_number or norm_comp,
        invalid_value=norm_comp,
        expected_condition="Company code exists exactly once in QuikComp",
        actual_condition=message,
        message=message,
        data_region_path=data_region_path,
        company_code=norm_comp,
        original_company_code=orig_comp,
        normalized_company_code=norm_comp,
        group_number=group_number,
        original_group_number=original_group,
        normalized_group_number=group_number,
        reference_table=TABLE_QUIKCOMP,
        reference_field="MCOMP",
        reference_match_count=match_count,
    )
