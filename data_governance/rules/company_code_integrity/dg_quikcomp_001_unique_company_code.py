"""DG-QUIKCOMP-001 — Unique QuikComp Company Code."""

from __future__ import annotations

from data_governance.catalog.governance_items import RULE_DG_QUIKCOMP_001
from data_governance.config.settings import TABLE_QUIKCOMP
from data_governance.data_access.table_loader import GovernanceDataStore
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_ERROR, STATUS_FAIL, STATUS_PASS
from data_governance.rules.company_code_integrity.company_code_index import (
    build_company_code_index,
)

RULE = RULE_DG_QUIKCOMP_001


def run_dg_quikcomp_001(
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
    table = store.get(TABLE_QUIKCOMP)
    if table is None:
        result.status = STATUS_ERROR
        result.error_count = 1
        result.error_message = f"{TABLE_QUIKCOMP} was not loaded."
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
                source_table=TABLE_QUIKCOMP,
                source_field="MCOMP",
                message=result.error_message,
                expected_condition="QuikComp table available for evaluation",
                actual_condition="Table missing",
            )
        )
        return result

    rows = table.rows
    result.records_evaluated = len(rows)
    index = build_company_code_index(rows)

    for record_no in index.blank_record_numbers:
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
                source_table=TABLE_QUIKCOMP,
                source_field="MCOMP",
                source_record_id=str(record_no),
                key_value="",
                invalid_value="",
                company_code="",
                expected_condition="Nonblank unique company code",
                actual_condition="Blank or null company code",
                message="QuikComp contains a blank company code.",
            )
        )

    for code, record_nos in sorted(index.code_to_records.items()):
        if len(record_nos) > 1:
            for record_no in record_nos:
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
                        source_table=TABLE_QUIKCOMP,
                        source_field="MCOMP",
                        source_record_id=str(record_no),
                        key_value=code,
                        invalid_value=code,
                        company_code=code,
                        duplicate_count=str(len(record_nos)),
                        expected_condition="Company code occurs exactly once",
                        actual_condition=f"Occurs {len(record_nos)} times",
                        message=(
                            f"Duplicate company code '{code}' exists "
                            f"{len(record_nos)} times in QuikComp."
                        ),
                    )
                )

    result.failed_count = len(result.findings)
    failing_records = {f.source_record_id for f in result.findings}
    result.passed_count = sum(
        1 for i in range(1, len(rows) + 1) if str(i) not in failing_records
    )
    result.status = STATUS_FAIL if result.failed_count else STATUS_PASS
    return result
