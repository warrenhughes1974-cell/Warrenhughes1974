"""DG-QUIKCOMP-003 — Policy Number Company Code Must Exist in QuikComp."""

from __future__ import annotations

from data_governance.catalog.governance_items import RULE_DG_QUIKCOMP_003
from data_governance.config.settings import TABLE_QUIKCOMP, TABLE_QUIKMSTR
from data_governance.data_access.normalization import (
    derive_policy_company_code,
    normalize_dbf_character,
)
from data_governance.data_access.table_loader import GovernanceDataStore, field_value
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_ERROR, STATUS_FAIL, STATUS_PASS
from data_governance.rules.company_code_integrity.company_code_index import (
    build_company_code_index,
)

RULE = RULE_DG_QUIKCOMP_003


def run_dg_quikcomp_003(
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

    mstr = store.get(TABLE_QUIKMSTR)
    comp = store.get(TABLE_QUIKCOMP)
    if mstr is None or comp is None:
        missing = []
        if mstr is None:
            missing.append(TABLE_QUIKMSTR)
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
                source_table=TABLE_QUIKMSTR,
                source_field="MPOLICY",
                message=result.error_message,
                expected_condition="QuikMstr and QuikComp available",
                actual_condition="Missing: " + ", ".join(missing),
            )
        )
        return result

    index = build_company_code_index(comp.rows)
    rows = mstr.rows
    result.records_evaluated = len(rows)

    for idx, row in enumerate(rows, start=1):
        raw_policy = field_value(row, "MPOLICY")
        policy_number = normalize_dbf_character(raw_policy)
        company_code = derive_policy_company_code(raw_policy)

        if not policy_number or company_code is None:
            display = policy_number if policy_number else "(blank)"
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
                    status=STATUS_FAIL,
                    source_table=TABLE_QUIKMSTR,
                    source_field="MPOLICY",
                    source_record_id=str(idx),
                    key_value=policy_number,
                    invalid_value=policy_number,
                    policy_number=policy_number,
                    company_code="",
                    expected_condition="Company code derivable from policy number",
                    actual_condition="Blank policy or no derivable company code",
                    message=(
                        f"A company code could not be derived from policy number '{display}'."
                    ),
                )
            )
            continue

        if not index.exists(company_code):
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
                    status=STATUS_FAIL,
                    source_table=TABLE_QUIKMSTR,
                    source_field="MPOLICY",
                    source_record_id=str(idx),
                    key_value=policy_number,
                    invalid_value=company_code,
                    policy_number=policy_number,
                    company_code=company_code,
                    expected_condition="Derived company code exists in QuikComp",
                    actual_condition="Company code not found in QuikComp",
                    message=(
                        f"Policy '{policy_number}' has company code '{company_code}', "
                        f"but '{company_code}' does not exist in QuikComp."
                    ),
                )
            )
            continue

        if index.is_duplicated(company_code):
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
                    status=STATUS_FAIL,
                    source_table=TABLE_QUIKMSTR,
                    source_field="MPOLICY",
                    source_record_id=str(idx),
                    key_value=policy_number,
                    invalid_value=company_code,
                    policy_number=policy_number,
                    company_code=company_code,
                    duplicate_count=str(index.count(company_code)),
                    expected_condition="Exactly one QuikComp record for company code",
                    actual_condition=(
                        f"QuikComp has {index.count(company_code)} records for code"
                    ),
                    message=(
                        f"Policy '{policy_number}' references company code '{company_code}', "
                        f"but QuikComp contains duplicate records for that code."
                    ),
                )
            )
            continue

        result.passed_count += 1

    result.failed_count = len([f for f in result.findings if f.status == STATUS_FAIL])
    result.status = STATUS_FAIL if result.failed_count else STATUS_PASS
    return result
