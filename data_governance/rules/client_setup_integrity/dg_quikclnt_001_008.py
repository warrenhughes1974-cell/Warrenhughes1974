"""DG-QUIKCLNT-001 through 008 — Client Setup integrity rules."""

from __future__ import annotations

from collections import defaultdict

from data_governance.catalog.governance_items_policy_data import (
    RULE_DG_QUIKCLNT_001,
    RULE_DG_QUIKCLNT_002,
    RULE_DG_QUIKCLNT_003,
    RULE_DG_QUIKCLNT_004,
    RULE_DG_QUIKCLNT_005,
    RULE_DG_QUIKCLNT_006,
    RULE_DG_QUIKCLNT_007,
    RULE_DG_QUIKCLNT_008,
)
from data_governance.config.policy_code_authority import is_approved
from data_governance.config.settings import TABLE_QUIKCLNT
from data_governance.data_access.table_loader import GovernanceDataStore, field_value
from data_governance.models.statuses import STATUS_WARN
from data_governance.rules.policy_master_integrity.common import (
    MIN_DATE,
    base_result,
    decode_date,
    fail,
    finalize,
    missing_table,
    norm_char,
    resolve_run_date,
)


def _require_clnt(store, rule, *, run_id, run_timestamp):
    clnt = store.get(TABLE_QUIKCLNT)
    if clnt is None:
        return None, missing_table(
            rule,
            run_id=run_id,
            run_timestamp=run_timestamp,
            data_dir=store.data_dir,
            table_name=TABLE_QUIKCLNT,
        )
    return clnt, None


def _client_label(row) -> str:
    cid, _, is_null = norm_char(field_value(row, "MCLIENTID"))
    if is_null or not cid:
        return "(blank)"
    return cid


def _is_individual(row) -> bool:
    mtype, _, is_null = norm_char(field_value(row, "MTYPE"))
    return not is_null and mtype == "I"


def run_dg_quikclnt_001(store: GovernanceDataStore, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKCLNT_001
    clnt, missing = _require_clnt(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = base_result(rule)
    rows = clnt.rows
    result.records_evaluated = len(rows)
    client_to_records: dict[str, list[tuple[int, str]]] = defaultdict(list)

    for idx, row in enumerate(rows, start=1):
        norm, orig, is_null = norm_char(field_value(row, "MCLIENTID"))
        if is_null:
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKCLNT,
                    field="MCLIENTID",
                    record_id=idx,
                    key_value="",
                    message="A QuikClnt record contains a null client ID.",
                    expected="MCLIENTID is populated and unique",
                    actual="Null client ID",
                    failure_category="NULL_VALUE",
                )
            )
            continue
        if norm == "":
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKCLNT,
                    field="MCLIENTID",
                    record_id=idx,
                    key_value=orig,
                    message="A QuikClnt record contains a blank client ID.",
                    expected="MCLIENTID is populated and unique",
                    actual="Blank client ID",
                    failure_category="BLANK_VALUE",
                )
            )
            continue
        client_to_records[norm].append((idx, orig))

    duplicate_groups = 0
    for client_id, record_infos in sorted(client_to_records.items()):
        if len(record_infos) <= 1:
            result.passed_count += 1
            continue
        duplicate_groups += 1
        for record_id, original in record_infos:
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKCLNT,
                    field="MCLIENTID",
                    record_id=record_id,
                    key_value=client_id,
                    message=(
                        f"QuikClnt contains {len(record_infos)} records for client ID "
                        f"'{client_id}'. Each client ID must be unique."
                    ),
                    expected="MCLIENTID occurs exactly once",
                    actual=f"Occurs {len(record_infos)} times",
                    failure_category="DUPLICATE_KEY",
                    duplicate_count=str(len(record_infos)),
                )
            )

    result.summary_metrics = {
        "distinct_client_ids": len(client_to_records),
        "duplicate_client_ids": duplicate_groups,
    }
    return finalize(result)


def _run_client_default_rule(
    store,
    rule,
    *,
    run_id,
    run_timestamp,
    field_name,
    default_value,
    authority,
):
    clnt, missing = _require_clnt(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = base_result(rule)
    rows = clnt.rows
    result.records_evaluated = len(rows)
    for idx, row in enumerate(rows, start=1):
        cid = _client_label(row)
        norm, orig, is_null = norm_char(field_value(row, field_name))
        if is_null or norm == "":
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKCLNT,
                    field=field_name,
                    record_id=idx,
                    key_value=cid,
                    message=(
                        f"Client '{cid}' has blank {field_name}; converted output must "
                        f"default to '{default_value}'."
                    ),
                    expected=f"{field_name} equals '{default_value}' or an approved value",
                    actual="Blank or null",
                    failure_category="MISSING_DEFAULT",
                )
            )
            continue
        if norm == default_value or is_approved(authority, norm):
            result.passed_count += 1
            continue
        result.findings.append(
            fail(
                rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_dir=store.data_dir,
                table=TABLE_QUIKCLNT,
                field=field_name,
                record_id=idx,
                key_value=cid,
                message=(
                    f"Client '{cid}' has unapproved {field_name} '{orig or norm}'."
                ),
                expected=f"{field_name} equals '{default_value}' or an approved value",
                actual=f"Unapproved value '{orig or norm}'",
                failure_category="UNAPPROVED_CODE",
            )
        )
    return finalize(result)


def run_dg_quikclnt_002(store: GovernanceDataStore, *, run_id, run_timestamp):
    return _run_client_default_rule(
        store,
        RULE_DG_QUIKCLNT_002,
        run_id=run_id,
        run_timestamp=run_timestamp,
        field_name="MTYPE",
        default_value="I",
        authority="MTYPE",
    )


def run_dg_quikclnt_003(store: GovernanceDataStore, *, run_id, run_timestamp):
    return _run_client_default_rule(
        store,
        RULE_DG_QUIKCLNT_003,
        run_id=run_id,
        run_timestamp=run_timestamp,
        field_name="MTAXIDTYPE",
        default_value="S",
        authority="MTAXIDTYPE",
    )


def run_dg_quikclnt_008(store: GovernanceDataStore, *, run_id, run_timestamp):
    return _run_client_default_rule(
        store,
        RULE_DG_QUIKCLNT_008,
        run_id=run_id,
        run_timestamp=run_timestamp,
        field_name="MLANGUAGE",
        default_value="E",
        authority="MLANGUAGE",
    )


def run_dg_quikclnt_004(store: GovernanceDataStore, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKCLNT_004
    clnt, missing = _require_clnt(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = base_result(rule)
    rows = clnt.rows
    result.records_evaluated = len(rows)
    for idx, row in enumerate(rows, start=1):
        cid = _client_label(row)
        if not _is_individual(row):
            result.passed_count += 1
            continue
        lname, orig, is_null = norm_char(field_value(row, "MLNAME"))
        if is_null or lname == "":
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKCLNT,
                    field="MLNAME",
                    record_id=idx,
                    key_value=cid,
                    message=f"Individual client '{cid}' has a blank last name.",
                    expected="MLNAME populated for individual clients",
                    actual="Blank or null MLNAME",
                    failure_category="BLANK_VALUE",
                )
            )
            continue
        result.passed_count += 1
    return finalize(result)


def run_dg_quikclnt_005(store: GovernanceDataStore, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKCLNT_005
    clnt, missing = _require_clnt(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = base_result(rule)
    rows = clnt.rows
    result.records_evaluated = len(rows)
    contact_fields = ("MADDR1", "MLNAME", "MFNAME", "MCITY", "MSTATE", "MZIP")

    for idx, row in enumerate(rows, start=1):
        cid = _client_label(row)
        all_blank = True
        for field_name in contact_fields:
            norm, _, is_null = norm_char(field_value(row, field_name))
            if not is_null and norm != "":
                all_blank = False
                break
        if all_blank:
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKCLNT,
                    field="MADDR1",
                    record_id=idx,
                    key_value=cid,
                    message=(
                        f"Client '{cid}' has no usable name or mailing-address information."
                    ),
                    expected="At least one name or mailing field populated",
                    actual="All verified contact fields blank",
                    status=STATUS_WARN,
                    failure_category="MISSING_CONTACT",
                )
            )
            continue
        result.passed_count += 1
    return finalize(result)


def run_dg_quikclnt_006(store: GovernanceDataStore, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKCLNT_006
    clnt, missing = _require_clnt(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = base_result(rule)
    run_date = resolve_run_date(store, run_timestamp)
    rows = clnt.rows
    result.records_evaluated = len(rows)

    for idx, row in enumerate(rows, start=1):
        cid = _client_label(row)
        decoded = decode_date(field_value(row, "MDOB"))
        display = decoded.decoded_display or decoded.original_display

        if decoded.is_null or decoded.is_blank:
            if _is_individual(row):
                result.findings.append(
                    fail(
                        rule,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_dir=store.data_dir,
                        table=TABLE_QUIKCLNT,
                        field="MDOB",
                        record_id=idx,
                        key_value=cid,
                        message=f"Individual client '{cid}' has blank date of birth.",
                        expected="MDOB populated and valid for individuals",
                        actual="Blank MDOB",
                        status=STATUS_WARN,
                        failure_category="MISSING_DOB",
                    )
                )
            else:
                result.passed_count += 1
            continue

        if decoded.is_unreadable or decoded.date_value is None:
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKCLNT,
                    field="MDOB",
                    record_id=idx,
                    key_value=cid,
                    message=(
                        f"Client '{cid}' has unreadable date of birth '{display}'."
                    ),
                    expected="MDOB is a valid date on or after 1900-01-01",
                    actual=f"Unreadable value '{display}'",
                    failure_category="INVALID_DATE",
                )
            )
            continue

        dob = decoded.date_value
        if dob > run_date:
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKCLNT,
                    field="MDOB",
                    record_id=idx,
                    key_value=cid,
                    message=(
                        f"Client '{cid}' has date of birth '{display}' after the "
                        f"governance run date."
                    ),
                    expected="MDOB on or before the governance run date",
                    actual=f"Future date '{display}'",
                    failure_category="DATE_AFTER_RUN",
                )
            )
            continue

        if dob < MIN_DATE:
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKCLNT,
                    field="MDOB",
                    record_id=idx,
                    key_value=cid,
                    message=(
                        f"Client '{cid}' has date of birth '{display}' before "
                        f"{MIN_DATE.isoformat()}."
                    ),
                    expected="MDOB on or after 1900-01-01",
                    actual=f"Date '{display}' before minimum",
                    failure_category="DATE_BEFORE_MINIMUM",
                )
            )
            continue

        result.passed_count += 1
    return finalize(result)


def run_dg_quikclnt_007(store: GovernanceDataStore, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKCLNT_007
    clnt, missing = _require_clnt(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = base_result(rule)
    rows = clnt.rows
    result.records_evaluated = len(rows)

    for idx, row in enumerate(rows, start=1):
        cid = _client_label(row)
        if not _is_individual(row):
            result.passed_count += 1
            continue
        sex, orig, is_null = norm_char(field_value(row, "MSEX"))
        if is_null or sex == "":
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKCLNT,
                    field="MSEX",
                    record_id=idx,
                    key_value=cid,
                    message=f"Individual client '{cid}' has blank sex code.",
                    expected="MSEX is M or F for individual clients",
                    actual="Blank or null MSEX",
                    failure_category="BLANK_VALUE",
                )
            )
            continue
        if sex in {"M", "F"}:
            result.passed_count += 1
            continue
        result.findings.append(
            fail(
                rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_dir=store.data_dir,
                table=TABLE_QUIKCLNT,
                field="MSEX",
                record_id=idx,
                key_value=cid,
                message=(
                    f"Individual client '{cid}' has invalid sex code '{orig or sex}'."
                ),
                expected="MSEX is M or F for individual clients",
                actual=f"Invalid value '{orig or sex}'",
                failure_category="UNAPPROVED_CODE",
            )
        )
    return finalize(result)
