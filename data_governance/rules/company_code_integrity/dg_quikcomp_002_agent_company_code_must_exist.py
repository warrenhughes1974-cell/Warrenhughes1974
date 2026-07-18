"""DG-QUIKCOMP-002 — Agent Company Code Must Exist in QuikComp."""

from __future__ import annotations

from data_governance.catalog.governance_items import RULE_DG_QUIKCOMP_002
from data_governance.config.settings import TABLE_QUIKAGTS, TABLE_QUIKCOMP
from data_governance.data_access.normalization import normalize_dbf_character
from data_governance.data_access.table_loader import GovernanceDataStore, field_value
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_ERROR, STATUS_FAIL, STATUS_PASS
from data_governance.rules.company_code_integrity.company_code_index import (
    build_company_code_index,
)

RULE = RULE_DG_QUIKCOMP_002


def run_dg_quikcomp_002(
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

    agts = store.get(TABLE_QUIKAGTS)
    comp = store.get(TABLE_QUIKCOMP)
    if agts is None or comp is None:
        missing = []
        if agts is None:
            missing.append(TABLE_QUIKAGTS)
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
                source_table=TABLE_QUIKAGTS,
                source_field="MCOMP",
                message=result.error_message,
                expected_condition="QuikAgts and QuikComp available",
                actual_condition="Missing: " + ", ".join(missing),
            )
        )
        return result

    index = build_company_code_index(comp.rows)
    rows = agts.rows
    result.records_evaluated = len(rows)

    for idx, row in enumerate(rows, start=1):
        agent_number = normalize_dbf_character(field_value(row, "MAGENT"))
        agent_name = normalize_dbf_character(field_value(row, "MAGTNAME"))
        company_code = normalize_dbf_character(field_value(row, "MCOMP"))
        agent_label = agent_number or f"record {idx}"

        if not company_code:
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
                    source_table=TABLE_QUIKAGTS,
                    source_field="MCOMP",
                    source_record_id=str(idx),
                    key_value=agent_number,
                    invalid_value="",
                    company_code="",
                    agent_number=agent_number,
                    agent_name=agent_name,
                    expected_condition="Agent company code exists once in QuikComp",
                    actual_condition="Blank or null company code",
                    message=f"Agent '{agent_label}' does not have a company code.",
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
                    source_table=TABLE_QUIKAGTS,
                    source_field="MCOMP",
                    source_record_id=str(idx),
                    key_value=agent_number,
                    invalid_value=company_code,
                    company_code=company_code,
                    agent_number=agent_number,
                    agent_name=agent_name,
                    expected_condition="Company code exists in QuikComp",
                    actual_condition="Company code not found in QuikComp",
                    message=(
                        f"Agent '{agent_label}' uses company code '{company_code}', "
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
                    source_table=TABLE_QUIKAGTS,
                    source_field="MCOMP",
                    source_record_id=str(idx),
                    key_value=agent_number,
                    invalid_value=company_code,
                    company_code=company_code,
                    agent_number=agent_number,
                    agent_name=agent_name,
                    duplicate_count=str(index.count(company_code)),
                    expected_condition="Exactly one QuikComp record for company code",
                    actual_condition=(
                        f"QuikComp has {index.count(company_code)} records for code"
                    ),
                    message=(
                        f"Agent '{agent_label}' references company code '{company_code}', "
                        f"but QuikComp contains duplicate records for that code."
                    ),
                )
            )
            continue

        result.passed_count += 1

    result.failed_count = len([f for f in result.findings if f.status == STATUS_FAIL])
    result.status = STATUS_FAIL if result.failed_count else STATUS_PASS
    return result
