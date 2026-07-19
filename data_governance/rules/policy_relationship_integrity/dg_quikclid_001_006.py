"""DG-QUIKCLID-001 through 006 — Policy Relationship integrity rules."""

from __future__ import annotations

from data_governance.catalog.governance_items_policy_data import (
    RULE_DG_QUIKCLID_001,
    RULE_DG_QUIKCLID_002,
    RULE_DG_QUIKCLID_003,
    RULE_DG_QUIKCLID_004,
    RULE_DG_QUIKCLID_005,
    RULE_DG_QUIKCLID_006,
)
from data_governance.config.policy_code_authority import is_approved
from data_governance.config.settings import (
    TABLE_QUIKCLID,
    TABLE_QUIKCLNT,
    TABLE_QUIKMSTR,
    TABLE_QUIKRIDR,
)
from data_governance.data_access.table_loader import GovernanceDataStore, field_value
from data_governance.models.statuses import STATUS_ERROR
from data_governance.rules.policy_master_integrity.common import (
    base_result,
    build_client_index,
    build_policy_index,
    build_ridr_phase_index,
    fail,
    finalize,
    missing_table,
    norm_char,
    norm_policy,
    parse_phase,
    policy_key_from_row,
)


def _require_clid(store, rule, *, run_id, run_timestamp):
    clid = store.get(TABLE_QUIKCLID)
    if clid is None:
        return None, missing_table(
            rule,
            run_id=run_id,
            run_timestamp=run_timestamp,
            data_dir=store.data_dir,
            table_name=TABLE_QUIKCLID,
        )
    return clid, None


def _relation_code(row) -> str:
    code, _, is_null = norm_char(field_value(row, "MRELATION"))
    return "" if is_null else code


def _relationship_key(row) -> str:
    pol = policy_key_from_row(row)
    client, _, _ = norm_char(field_value(row, "MCLIENTID"))
    relation = _relation_code(row)
    phase = parse_phase(field_value(row, "MPHASE"))
    phase_text = "" if phase is None else str(phase)
    return f"{pol}|{client}|{relation}|{phase_text}"


def run_dg_quikclid_001(store: GovernanceDataStore, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKCLID_001
    clid, missing = _require_clid(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    clnt = store.get(TABLE_QUIKCLNT)
    client_index = build_client_index(clnt.rows) if clnt is not None else None
    result = base_result(rule)
    rows = clid.rows
    result.records_evaluated = len(rows)
    cnbc_reported = False

    for idx, row in enumerate(rows, start=1):
        key = _relationship_key(row)
        client, orig, is_null = norm_char(field_value(row, "MCLIENTID"))
        if is_null or client == "":
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKCLID,
                    field="MCLIENTID",
                    record_id=idx,
                    key_value=key,
                    policy_number=policy_key_from_row(row),
                    message="A QuikClid record has a blank client ID.",
                    expected="MCLIENTID populated and exists in QuikClnt",
                    actual="Blank or null MCLIENTID",
                    failure_category="BLANK_VALUE",
                )
            )
            continue
        if client_index is None:
            if not cnbc_reported:
                result.findings.append(
                    fail(
                        rule,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_dir=store.data_dir,
                        table=TABLE_QUIKCLID,
                        field="MCLIENTID",
                        record_id=idx,
                        key_value=key,
                        policy_number=policy_key_from_row(row),
                        message=(
                            "Relationship client references could not be checked because "
                            "QuikClnt was not loaded."
                        ),
                        expected="MCLIENTID exists in QuikClnt",
                        actual="Could Not Be Checked — QuikClnt unavailable",
                        status=STATUS_ERROR,
                        failure_category="COULD_NOT_BE_CHECKED",
                        reference_table=TABLE_QUIKCLNT,
                        reference_field="MCLIENTID",
                    )
                )
                cnbc_reported = True
            continue
        if client in client_index:
            result.passed_count += 1
            continue
        result.findings.append(
            fail(
                rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_dir=store.data_dir,
                table=TABLE_QUIKCLID,
                field="MCLIENTID",
                record_id=idx,
                key_value=key,
                policy_number=policy_key_from_row(row),
                message=(
                    f"Relationship references client '{orig or client}' that does not "
                    f"exist in QuikClnt."
                ),
                expected="MCLIENTID exists in QuikClnt",
                actual=f"Missing client '{orig or client}'",
                failure_category="MISSING_REFERENCE",
                reference_table=TABLE_QUIKCLNT,
                reference_field="MCLIENTID",
                reference_match_count="0",
            )
        )
    return finalize(result)


def run_dg_quikclid_002(store: GovernanceDataStore, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKCLID_002
    clid, missing = _require_clid(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    mstr = store.get(TABLE_QUIKMSTR)
    policy_index = build_policy_index(mstr.rows) if mstr is not None else None
    result = base_result(rule)
    rows = clid.rows
    result.records_evaluated = len(rows)
    cnbc_reported = False

    for idx, row in enumerate(rows, start=1):
        key = _relationship_key(row)
        pol, orig, is_null = norm_policy(field_value(row, "MPOLICY"))
        if is_null or pol == "":
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKCLID,
                    field="MPOLICY",
                    record_id=idx,
                    key_value=key,
                    message="A QuikClid record has a blank policy number.",
                    expected="MPOLICY populated and exists in QuikMstr",
                    actual="Blank or null MPOLICY",
                    failure_category="BLANK_VALUE",
                )
            )
            continue
        if policy_index is None:
            if not cnbc_reported:
                result.findings.append(
                    fail(
                        rule,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_dir=store.data_dir,
                        table=TABLE_QUIKCLID,
                        field="MPOLICY",
                        record_id=idx,
                        key_value=key,
                        policy_number=pol,
                        message=(
                            "Relationship policy references could not be checked because "
                            "QuikMstr was not loaded."
                        ),
                        expected="MPOLICY exists in QuikMstr",
                        actual="Could Not Be Checked — QuikMstr unavailable",
                        status=STATUS_ERROR,
                        failure_category="COULD_NOT_BE_CHECKED",
                        reference_table=TABLE_QUIKMSTR,
                        reference_field="MPOLICY",
                    )
                )
                cnbc_reported = True
            continue
        if pol in policy_index:
            result.passed_count += 1
            continue
        result.findings.append(
            fail(
                rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_dir=store.data_dir,
                table=TABLE_QUIKCLID,
                field="MPOLICY",
                record_id=idx,
                key_value=key,
                policy_number=pol,
                message=(
                    f"Relationship references policy '{orig or pol}' that does not "
                    f"exist in QuikMstr."
                ),
                expected="MPOLICY exists in QuikMstr",
                actual=f"Missing policy '{orig or pol}'",
                failure_category="MISSING_REFERENCE",
                reference_table=TABLE_QUIKMSTR,
                reference_field="MPOLICY",
                reference_match_count="0",
            )
        )
    return finalize(result)


def run_dg_quikclid_003(store: GovernanceDataStore, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKCLID_003
    clid, missing = _require_clid(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    ridr = store.get(TABLE_QUIKRIDR)
    phase_index = build_ridr_phase_index(ridr.rows) if ridr is not None else None
    result = base_result(rule)
    rows = clid.rows
    result.records_evaluated = len(rows)
    cnbc_reported = False

    for idx, row in enumerate(rows, start=1):
        key = _relationship_key(row)
        pol = policy_key_from_row(row)
        phase = parse_phase(field_value(row, "MPHASE"))
        if phase is None or phase == 0:
            result.passed_count += 1
            continue
        if phase_index is None:
            if not cnbc_reported:
                result.findings.append(
                    fail(
                        rule,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_dir=store.data_dir,
                        table=TABLE_QUIKCLID,
                        field="MPHASE",
                        record_id=idx,
                        key_value=key,
                        policy_number=pol,
                        message=(
                            "Nonzero relationship phases could not be checked because "
                            "QuikRidr was not loaded."
                        ),
                        expected="(MPOLICY, MPHASE) exists in QuikRidr when MPHASE is not 0",
                        actual="Could Not Be Checked — QuikRidr unavailable",
                        status=STATUS_ERROR,
                        failure_category="COULD_NOT_BE_CHECKED",
                        reference_table=TABLE_QUIKRIDR,
                        reference_field="MPHASE",
                    )
                )
                cnbc_reported = True
            continue
        matches = phase_index.get((pol, phase), [])
        if matches:
            result.passed_count += 1
            continue
        result.findings.append(
            fail(
                rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_dir=store.data_dir,
                table=TABLE_QUIKCLID,
                field="MPHASE",
                record_id=idx,
                key_value=key,
                policy_number=pol,
                message=(
                    f"Relationship for policy '{pol}' uses phase {phase}, but no matching "
                    f"rider exists in QuikRidr."
                ),
                expected="(MPOLICY, MPHASE) exists in QuikRidr when MPHASE is not 0",
                actual=f"No rider match for phase {phase}",
                failure_category="MISSING_REFERENCE",
                reference_table=TABLE_QUIKRIDR,
                reference_field="MPHASE",
                reference_match_count="0",
            )
        )
    return finalize(result)


def run_dg_quikclid_004(store: GovernanceDataStore, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKCLID_004
    clid, missing = _require_clid(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = base_result(rule)
    rows = clid.rows
    result.records_evaluated = len(rows)

    for idx, row in enumerate(rows, start=1):
        key = _relationship_key(row)
        pol = policy_key_from_row(row)
        relation = _relation_code(row)
        if relation == "INSD":
            result.passed_count += 1
            continue
        phase = parse_phase(field_value(row, "MPHASE"))
        if phase == 0:
            result.passed_count += 1
            continue
        shown = "" if phase is None else str(phase)
        result.findings.append(
            fail(
                rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_dir=store.data_dir,
                table=TABLE_QUIKCLID,
                field="MPHASE",
                record_id=idx,
                key_value=key,
                policy_number=pol,
                message=(
                    f"Non-insured relationship '{relation}' for policy '{pol}' uses "
                    f"MPHASE={shown}; converted output must use phase 0."
                ),
                expected="Non-INSD relationships use MPHASE 0",
                actual=f"MPHASE={shown}",
                failure_category="INVALID_PHASE",
            )
        )
    return finalize(result)


def run_dg_quikclid_005(store: GovernanceDataStore, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKCLID_005
    clid, missing = _require_clid(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    ridr = store.get(TABLE_QUIKRIDR)
    phase_index = build_ridr_phase_index(ridr.rows) if ridr is not None else None
    result = base_result(rule)
    rows = clid.rows
    result.records_evaluated = len(rows)
    cnbc_reported = False

    for idx, row in enumerate(rows, start=1):
        key = _relationship_key(row)
        pol = policy_key_from_row(row)
        relation = _relation_code(row)
        if relation != "INSD":
            result.passed_count += 1
            continue
        phase = parse_phase(field_value(row, "MPHASE"))
        if phase_index is None:
            if not cnbc_reported:
                result.findings.append(
                    fail(
                        rule,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_dir=store.data_dir,
                        table=TABLE_QUIKCLID,
                        field="MPHASE",
                        record_id=idx,
                        key_value=key,
                        policy_number=pol,
                        message=(
                            "Insured relationship rider alignment could not be checked "
                            "because QuikRidr was not loaded."
                        ),
                        expected="INSD (MPOLICY, MPHASE) exists in QuikRidr",
                        actual="Could Not Be Checked — QuikRidr unavailable",
                        status=STATUS_ERROR,
                        failure_category="COULD_NOT_BE_CHECKED",
                        reference_table=TABLE_QUIKRIDR,
                        reference_field="MPHASE",
                    )
                )
                cnbc_reported = True
            continue
        if phase is None:
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKCLID,
                    field="MPHASE",
                    record_id=idx,
                    key_value=key,
                    policy_number=pol,
                    message=(
                        f"Insured relationship for policy '{pol}' has unreadable MPHASE."
                    ),
                    expected="INSD (MPOLICY, MPHASE) exists in QuikRidr",
                    actual="Unreadable MPHASE",
                    failure_category="UNREADABLE_VALUE",
                )
            )
            continue
        matches = phase_index.get((pol, phase), [])
        if len(matches) == 1:
            result.passed_count += 1
            continue
        if len(matches) == 0:
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKCLID,
                    field="MPHASE",
                    record_id=idx,
                    key_value=key,
                    policy_number=pol,
                    message=(
                        f"Insured relationship for policy '{pol}' phase {phase} has no "
                        f"matching rider in QuikRidr."
                    ),
                    expected="INSD (MPOLICY, MPHASE) exists in QuikRidr",
                    actual="No rider match",
                    failure_category="MISSING_REFERENCE",
                    reference_table=TABLE_QUIKRIDR,
                    reference_field="MPHASE",
                    reference_match_count="0",
                )
            )
            continue
        result.findings.append(
            fail(
                rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_dir=store.data_dir,
                table=TABLE_QUIKCLID,
                field="MPHASE",
                record_id=idx,
                key_value=key,
                policy_number=pol,
                message=(
                    f"Insured relationship for policy '{pol}' phase {phase} matches "
                    f"{len(matches)} riders in QuikRidr."
                ),
                expected="Exactly one INSD rider match on (MPOLICY, MPHASE)",
                actual=f"{len(matches)} rider matches",
                failure_category="AMBIGUOUS_REFERENCE",
                reference_table=TABLE_QUIKRIDR,
                reference_field="MPHASE",
                reference_match_count=str(len(matches)),
            )
        )
    return finalize(result)


def run_dg_quikclid_006(store: GovernanceDataStore, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKCLID_006
    clid, missing = _require_clid(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = base_result(rule)
    rows = clid.rows
    result.records_evaluated = len(rows)

    for idx, row in enumerate(rows, start=1):
        key = _relationship_key(row)
        pol = policy_key_from_row(row)
        relation, orig, is_null = norm_char(field_value(row, "MRELATION"))
        if is_null or relation == "":
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKCLID,
                    field="MRELATION",
                    record_id=idx,
                    key_value=key,
                    policy_number=pol,
                    message="A QuikClid record has a blank relationship code.",
                    expected="MRELATION is a populated approved relationship code",
                    actual="Blank or null MRELATION",
                    failure_category="BLANK_VALUE",
                )
            )
            continue
        if is_approved("MRELATION", relation):
            result.passed_count += 1
            continue
        result.findings.append(
            fail(
                rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_dir=store.data_dir,
                table=TABLE_QUIKCLID,
                field="MRELATION",
                record_id=idx,
                key_value=key,
                policy_number=pol,
                message=(
                    f"Relationship for policy '{pol}' uses unapproved code "
                    f"'{orig or relation}'."
                ),
                expected="MRELATION is in the approved relationship-code list",
                actual=f"Unapproved code '{orig or relation}'",
                failure_category="UNAPPROVED_CODE",
            )
        )
    return finalize(result)
