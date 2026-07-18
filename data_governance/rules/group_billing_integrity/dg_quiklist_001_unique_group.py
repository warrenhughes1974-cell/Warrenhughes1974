"""DG-QUIKLIST-001 — Group Number Must Be Unique."""

from __future__ import annotations

from collections import defaultdict

from data_governance.catalog.governance_items import RULE_DG_QUIKLIST_001
from data_governance.config.settings import TABLE_QUIKLIST
from data_governance.data_access.normalization import normalize_identifier_preserve_zeros
from data_governance.data_access.table_loader import GovernanceDataStore, field_value
from data_governance.models.findings import RuleExecutionResult, make_finding
from data_governance.models.statuses import STATUS_FAIL, STATUS_PASS
from data_governance.rules.group_billing_integrity.helpers import missing_quiklist_result

RULE = RULE_DG_QUIKLIST_001


def run_dg_quiklist_001(
    store: GovernanceDataStore,
    *,
    run_id: str,
    run_timestamp: str,
) -> RuleExecutionResult:
    if store.get(TABLE_QUIKLIST) is None:
        return missing_quiklist_result(
            RULE, store, run_id=run_id, run_timestamp=run_timestamp, source_field="MGROUP"
        )

    result = RuleExecutionResult(
        governance_item_id=RULE.governance_item_id,
        rule_id=RULE.rule_id,
        rule_name=RULE.technical_name,
        business_name=RULE.business_name,
        severity=RULE.severity,
        status=STATUS_PASS,
    )
    rows = store.get(TABLE_QUIKLIST).rows
    result.records_evaluated = len(rows)

    group_to_records: dict[str, list[tuple[int, str]]] = defaultdict(list)
    blank_count = 0
    null_count = 0

    for idx, row in enumerate(rows, start=1):
        raw = field_value(row, "MGROUP")
        normalized, original, is_null = normalize_identifier_preserve_zeros(raw)

        if is_null:
            null_count += 1
            result.findings.append(
                _finding(
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=str(idx),
                    original="",
                    normalized="",
                    message="A QuikList record contains a null group number.",
                    actual="Null group number",
                    duplicate_count="",
                )
            )
            continue

        if normalized == "":
            blank_count += 1
            result.findings.append(
                _finding(
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_region_path=store.data_dir,
                    record_id=str(idx),
                    original=original,
                    normalized="",
                    message="A QuikList record contains a blank group number.",
                    actual="Blank group number",
                    duplicate_count="",
                )
            )
            continue

        group_to_records[normalized].append((idx, original))

    duplicate_groups = 0
    records_in_dupes = 0
    for group, record_infos in sorted(group_to_records.items()):
        if len(record_infos) > 1:
            duplicate_groups += 1
            records_in_dupes += len(record_infos)
            for record_id, original in record_infos:
                result.findings.append(
                    _finding(
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_region_path=store.data_dir,
                        record_id=str(record_id),
                        original=original,
                        normalized=group,
                        message=(
                            f"QuikList contains {len(record_infos)} records for group number "
                            f"'{group}'. Each group number must be unique."
                        ),
                        actual=f"Occurs {len(record_infos)} times",
                        duplicate_count=str(len(record_infos)),
                    )
                )

    unique_pass = sum(1 for infos in group_to_records.values() if len(infos) == 1)
    result.passed_count = unique_pass
    result.failed_count = len([f for f in result.findings if f.status == STATUS_FAIL])
    result.summary_metrics = {
        "distinct_group_numbers": len(group_to_records),
        "duplicate_group_numbers": duplicate_groups,
        "records_involved_in_duplicates": records_in_dupes,
        "blank_group_numbers": blank_count,
        "null_group_numbers": null_count,
    }
    result.status = STATUS_FAIL if result.failed_count else STATUS_PASS
    return result


def _finding(
    *,
    run_id: str,
    run_timestamp: str,
    data_region_path: str,
    record_id: str,
    original: str,
    normalized: str,
    message: str,
    actual: str,
    duplicate_count: str,
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
        source_field="MGROUP",
        source_record_id=record_id,
        key_value=normalized or original,
        invalid_value=normalized or original,
        expected_condition="Group number occurs exactly once",
        actual_condition=actual,
        message=message,
        data_region_path=data_region_path,
        duplicate_count=duplicate_count,
        group_number=normalized or original,
        original_group_number=original,
        normalized_group_number=normalized,
    )
