"""DG-QUIKMSTR-002 through 026 — Policy Master integrity rules."""

from __future__ import annotations

from datetime import date

from data_governance.catalog.governance_items_policy_data import (
    RULE_DG_QUIKMSTR_002,
    RULE_DG_QUIKMSTR_003,
    RULE_DG_QUIKMSTR_004,
    RULE_DG_QUIKMSTR_005,
    RULE_DG_QUIKMSTR_006,
    RULE_DG_QUIKMSTR_007,
    RULE_DG_QUIKMSTR_008,
    RULE_DG_QUIKMSTR_009,
    RULE_DG_QUIKMSTR_010,
    RULE_DG_QUIKMSTR_011,
    RULE_DG_QUIKMSTR_012,
    RULE_DG_QUIKMSTR_013,
    RULE_DG_QUIKMSTR_014,
    RULE_DG_QUIKMSTR_015,
    RULE_DG_QUIKMSTR_016,
    RULE_DG_QUIKMSTR_017,
    RULE_DG_QUIKMSTR_018,
    RULE_DG_QUIKMSTR_019,
    RULE_DG_QUIKMSTR_020,
    RULE_DG_QUIKMSTR_021,
    RULE_DG_QUIKMSTR_022,
    RULE_DG_QUIKMSTR_023,
    RULE_DG_QUIKMSTR_024,
    RULE_DG_QUIKMSTR_025,
    RULE_DG_QUIKMSTR_026,
)
from data_governance.config.policy_code_authority import is_approved
from data_governance.config.settings import TABLE_QUIKCLNT, TABLE_QUIKLIST, TABLE_QUIKMSTR
from data_governance.data_access.normalization import decode_numeric_zero, format_iso_date
from data_governance.data_access.table_loader import GovernanceDataStore, field_value
from data_governance.models.statuses import STATUS_ERROR
from data_governance.rules.plan_value_integrity.us_states import APPROVED_US_STATE_ABBREVIATIONS
from data_governance.rules.policy_master_integrity.common import (
    base_result,
    build_client_index,
    build_group_index,
    date_in_governance_range,
    decode_date,
    deferred_result,
    fail,
    finalize,
    missing_table,
    norm_char,
    norm_policy,
    policy_key_from_row,
    resolve_run_date,
)


def _require_mstr(store, rule, *, run_id, run_timestamp):
    mstr = store.get(TABLE_QUIKMSTR)
    if mstr is None:
        return None, missing_table(
            rule,
            run_id=run_id,
            run_timestamp=run_timestamp,
            data_dir=store.data_dir,
            table_name=TABLE_QUIKMSTR,
        )
    return mstr, None


def _policy_label(row) -> str:
    pol, _, is_null = norm_policy(field_value(row, "MPOLICY"))
    if is_null or not pol:
        return "(blank)"
    return pol


def _validate_required_date_field(
    *,
    rule,
    store,
    run_id,
    run_timestamp,
    row,
    idx,
    field_name,
    run_date,
):
    """Return (passed, finding_or_none, date_value)."""
    pol = policy_key_from_row(row)
    decoded = decode_date(field_value(row, field_name))
    display = decoded.decoded_display or decoded.original_display

    if decoded.is_null and not decoded.original_display:
        return False, fail(
            rule,
            run_id=run_id,
            run_timestamp=run_timestamp,
            data_dir=store.data_dir,
            table=TABLE_QUIKMSTR,
            field=field_name,
            record_id=idx,
            key_value=pol,
            policy_number=pol,
            message=f"Policy '{_policy_label(row)}' has a null {field_name}.",
            expected=f"{field_name} is a valid date within the approved range",
            actual="Null value",
            failure_category="NULL_VALUE",
        ), None

    if decoded.is_blank:
        return False, fail(
            rule,
            run_id=run_id,
            run_timestamp=run_timestamp,
            data_dir=store.data_dir,
            table=TABLE_QUIKMSTR,
            field=field_name,
            record_id=idx,
            key_value=pol,
            policy_number=pol,
            message=f"Policy '{_policy_label(row)}' has a blank {field_name}.",
            expected=f"{field_name} is a valid date within the approved range",
            actual="Blank value",
            failure_category="BLANK_VALUE",
        ), None

    if decoded.is_unreadable or decoded.date_value is None:
        return False, fail(
            rule,
            run_id=run_id,
            run_timestamp=run_timestamp,
            data_dir=store.data_dir,
            table=TABLE_QUIKMSTR,
            field=field_name,
            record_id=idx,
            key_value=pol,
            policy_number=pol,
            message=(
                f"Policy '{_policy_label(row)}' has an unreadable {field_name} "
                f"value '{display}'."
            ),
            expected=f"{field_name} is a valid date within the approved range",
            actual=f"Unreadable value '{display}'",
            failure_category="INVALID_DATE",
        ), None

    if not date_in_governance_range(decoded.date_value, run_date):
        return False, fail(
            rule,
            run_id=run_id,
            run_timestamp=run_timestamp,
            data_dir=store.data_dir,
            table=TABLE_QUIKMSTR,
            field=field_name,
            record_id=idx,
            key_value=pol,
            policy_number=pol,
            message=(
                f"Policy '{_policy_label(row)}' has {field_name}='{display}' "
                f"outside the approved date range."
            ),
            expected=(
                f"{field_name} between {format_iso_date(date(1900, 1, 1))} and "
                f"{format_iso_date(run_date)} plus 12 calendar months"
            ),
            actual=f"Date '{display}' outside range",
            failure_category="DATE_OUT_OF_RANGE",
        ), None

    return True, None, decoded.date_value


def _run_required_date_rule(store, rule, *, run_id, run_timestamp, field):
    mstr, missing = _require_mstr(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = base_result(rule)
    run_date = resolve_run_date(store, run_timestamp)
    rows = mstr.rows
    result.records_evaluated = len(rows)
    for idx, row in enumerate(rows, start=1):
        ok, finding, _ = _validate_required_date_field(
            rule=rule,
            store=store,
            run_id=run_id,
            run_timestamp=run_timestamp,
            row=row,
            idx=idx,
            field_name=field,
            run_date=run_date,
        )
        if ok:
            result.passed_count += 1
        else:
            result.findings.append(finding)
    return finalize(result)


def run_dg_quikmstr_002(store: GovernanceDataStore, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKMSTR_002
    mstr, missing = _require_mstr(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = base_result(rule)
    rows = mstr.rows
    result.records_evaluated = len(rows)
    for idx, row in enumerate(rows, start=1):
        pol = policy_key_from_row(row)
        norm, orig, is_null = norm_char(field_value(row, "MSTATUS"))
        if is_null or norm == "":
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKMSTR,
                    field="MSTATUS",
                    record_id=idx,
                    key_value=pol,
                    policy_number=pol,
                    message=f"Policy '{_policy_label(row)}' has a blank policy status.",
                    expected="MSTATUS is a populated approved policy-status code",
                    actual="Blank or null MSTATUS",
                    failure_category="BLANK_VALUE",
                )
            )
            continue
        if not is_approved("MSTATUS", norm):
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKMSTR,
                    field="MSTATUS",
                    record_id=idx,
                    key_value=pol,
                    policy_number=pol,
                    message=(
                        f"Policy '{_policy_label(row)}' has unapproved status '{norm}'."
                    ),
                    expected="MSTATUS is in the approved policy-status code list",
                    actual=f"Unapproved status '{orig or norm}'",
                    failure_category="UNAPPROVED_CODE",
                )
            )
            continue
        result.passed_count += 1
    return finalize(result)


def run_dg_quikmstr_003(store: GovernanceDataStore, *, run_id, run_timestamp):
    return _run_required_date_rule(
        store,
        RULE_DG_QUIKMSTR_003,
        run_id=run_id,
        run_timestamp=run_timestamp,
        field="MSTATDATE",
    )


def run_dg_quikmstr_004(store: GovernanceDataStore, *, run_id, run_timestamp):
    return _run_required_date_rule(
        store,
        RULE_DG_QUIKMSTR_004,
        run_id=run_id,
        run_timestamp=run_timestamp,
        field="MISSDT",
    )


def _run_date_compare_rule(
    store,
    rule,
    *,
    run_id,
    run_timestamp,
    left_field,
    right_field,
    require_left=False,
    compare,
):
    mstr, missing = _require_mstr(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = base_result(rule)
    run_date = resolve_run_date(store, run_timestamp)
    rows = mstr.rows
    result.records_evaluated = len(rows)
    for idx, row in enumerate(rows, start=1):
        pol = policy_key_from_row(row)
        left = decode_date(field_value(row, left_field))
        right = decode_date(field_value(row, right_field))

        if require_left and (left.is_null or left.is_blank or left.date_value is None):
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKMSTR,
                    field=left_field,
                    record_id=idx,
                    key_value=pol,
                    policy_number=pol,
                    message=(
                        f"Policy '{_policy_label(row)}' has a missing or invalid "
                        f"{left_field}."
                    ),
                    expected=f"{left_field} is required and valid",
                    actual="Null, blank, or unreadable",
                    failure_category="INVALID_DATE",
                )
            )
            continue

        if left.date_value is None or right.date_value is None:
            result.passed_count += 1
            continue

        if not date_in_governance_range(left.date_value, run_date):
            result.passed_count += 1
            continue

        if compare(left.date_value, right.date_value):
            result.passed_count += 1
            continue

        result.findings.append(
            fail(
                rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_dir=store.data_dir,
                table=TABLE_QUIKMSTR,
                field=left_field,
                record_id=idx,
                key_value=pol,
                policy_number=pol,
                message=(
                    f"Policy '{_policy_label(row)}' has {left_field}="
                    f"'{left.decoded_display}' and {right_field}="
                    f"'{right.decoded_display}' in the wrong order."
                ),
                expected=f"{left_field} satisfies ordering rule against {right_field}",
                actual="Date ordering violation",
                failure_category="DATE_ORDER",
            )
        )
    return finalize(result)


def run_dg_quikmstr_005(store: GovernanceDataStore, *, run_id, run_timestamp):
    return _run_date_compare_rule(
        store,
        RULE_DG_QUIKMSTR_005,
        run_id=run_id,
        run_timestamp=run_timestamp,
        left_field="MPAIDTO",
        right_field="MISSDT",
        require_left=True,
        compare=lambda paid, issue: paid >= issue,
    )


def run_dg_quikmstr_006(store: GovernanceDataStore, *, run_id, run_timestamp):
    return _run_date_compare_rule(
        store,
        RULE_DG_QUIKMSTR_006,
        run_id=run_id,
        run_timestamp=run_timestamp,
        left_field="MBILLTO",
        right_field="MISSDT",
        require_left=True,
        compare=lambda bill, issue: bill >= issue,
    )


def run_dg_quikmstr_007(store: GovernanceDataStore, *, run_id, run_timestamp):
    return _run_date_compare_rule(
        store,
        RULE_DG_QUIKMSTR_007,
        run_id=run_id,
        run_timestamp=run_timestamp,
        left_field="MBILLTO",
        right_field="MPAIDTO",
        require_left=False,
        compare=lambda bill, paid: bill >= paid,
    )


def run_dg_quikmstr_023(store: GovernanceDataStore, *, run_id, run_timestamp):
    return _run_date_compare_rule(
        store,
        RULE_DG_QUIKMSTR_023,
        run_id=run_id,
        run_timestamp=run_timestamp,
        left_field="MAPPDATE",
        right_field="MISSDT",
        require_left=False,
        compare=lambda app, issue: app <= issue,
    )


def _run_default_or_approved_code_rule(
    store,
    rule,
    *,
    run_id,
    run_timestamp,
    field_name,
    default_value,
    authority,
):
    mstr, missing = _require_mstr(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = base_result(rule)
    rows = mstr.rows
    result.records_evaluated = len(rows)
    for idx, row in enumerate(rows, start=1):
        pol = policy_key_from_row(row)
        norm, orig, is_null = norm_char(field_value(row, field_name))
        if is_null or norm == "":
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKMSTR,
                    field=field_name,
                    record_id=idx,
                    key_value=pol,
                    policy_number=pol,
                    message=(
                        f"Policy '{_policy_label(row)}' has blank {field_name}; "
                        f"converted output must default to '{default_value}'."
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
                table=TABLE_QUIKMSTR,
                field=field_name,
                record_id=idx,
                key_value=pol,
                policy_number=pol,
                message=(
                    f"Policy '{_policy_label(row)}' has unapproved {field_name} "
                    f"'{orig or norm}'."
                ),
                expected=f"{field_name} equals '{default_value}' or an approved value",
                actual=f"Unapproved value '{orig or norm}'",
                failure_category="UNAPPROVED_CODE",
            )
        )
    return finalize(result)


def run_dg_quikmstr_008(store: GovernanceDataStore, *, run_id, run_timestamp):
    return _run_default_or_approved_code_rule(
        store,
        RULE_DG_QUIKMSTR_008,
        run_id=run_id,
        run_timestamp=run_timestamp,
        field_name="MNFOPT",
        default_value="0",
        authority="MNFOPT",
    )


def run_dg_quikmstr_024(store: GovernanceDataStore, *, run_id, run_timestamp):
    return _run_default_or_approved_code_rule(
        store,
        RULE_DG_QUIKMSTR_024,
        run_id=run_id,
        run_timestamp=run_timestamp,
        field_name="MISSCNTRY",
        default_value="0000",
        authority="MISSCNTRY",
    )


def run_dg_quikmstr_026(store: GovernanceDataStore, *, run_id, run_timestamp):
    return _run_default_or_approved_code_rule(
        store,
        RULE_DG_QUIKMSTR_026,
        run_id=run_id,
        run_timestamp=run_timestamp,
        field_name="MISSCLASS",
        default_value="00",
        authority="MISSCLASS",
    )


def run_dg_quikmstr_009(store: GovernanceDataStore, *, run_id, run_timestamp):
    return deferred_result(
        RULE_DG_QUIKMSTR_009,
        run_id=run_id,
        run_timestamp=run_timestamp,
        data_dir=store.data_dir,
        note="Dividend option validation deferred pending business direction.",
    )


def run_dg_quikmstr_025(store: GovernanceDataStore, *, run_id, run_timestamp):
    return deferred_result(
        RULE_DG_QUIKMSTR_025,
        run_id=run_id,
        run_timestamp=run_timestamp,
        data_dir=store.data_dir,
        note="Residence state validation deferred pending business direction.",
    )


def run_dg_quikmstr_010(store: GovernanceDataStore, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKMSTR_010
    mstr, missing = _require_mstr(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = base_result(rule)
    rows = mstr.rows
    result.records_evaluated = len(rows)
    for idx, row in enumerate(rows, start=1):
        pol = policy_key_from_row(row)
        norm, orig, is_null = norm_char(field_value(row, "MBILLFRM"))
        if is_null or norm == "":
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKMSTR,
                    field="MBILLFRM",
                    record_id=idx,
                    key_value=pol,
                    policy_number=pol,
                    message=f"Policy '{_policy_label(row)}' has a blank billing form.",
                    expected="MBILLFRM is a populated approved billing-form code",
                    actual="Blank or null",
                    failure_category="BLANK_VALUE",
                )
            )
            continue
        if not is_approved("MBILLFRM", norm, casefold=True):
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKMSTR,
                    field="MBILLFRM",
                    record_id=idx,
                    key_value=pol,
                    policy_number=pol,
                    message=(
                        f"Policy '{_policy_label(row)}' has unapproved billing form "
                        f"'{orig or norm}'."
                    ),
                    expected="MBILLFRM is in the approved billing-form code list",
                    actual=f"Unapproved value '{orig or norm}'",
                    failure_category="UNAPPROVED_CODE",
                )
            )
            continue
        result.passed_count += 1
    return finalize(result)


def run_dg_quikmstr_011(store: GovernanceDataStore, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKMSTR_011
    mstr, missing = _require_mstr(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = base_result(rule)
    rows = mstr.rows
    result.records_evaluated = len(rows)
    for idx, row in enumerate(rows, start=1):
        pol = policy_key_from_row(row)
        billday = decode_numeric_zero(field_value(row, "MBILLDAY"))
        issue = decode_date(field_value(row, "MISSDT"))

        if billday.is_zero or billday.is_blank or billday.is_null:
            if issue.date_value is not None and not issue.is_unreadable:
                result.passed_count += 1
                continue
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKMSTR,
                    field="MBILLDAY",
                    record_id=idx,
                    key_value=pol,
                    policy_number=pol,
                    message=(
                        f"Policy '{_policy_label(row)}' has blank billing day and "
                        f"issue date could not be used for derivation."
                    ),
                    expected="MBILLDAY derived from valid MISSDT or populated 1-31",
                    actual="Could Not Be Checked — invalid or missing MISSDT",
                    status=STATUS_ERROR,
                    failure_category="COULD_NOT_BE_CHECKED",
                )
            )
            continue

        if billday.is_unreadable:
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKMSTR,
                    field="MBILLDAY",
                    record_id=idx,
                    key_value=pol,
                    policy_number=pol,
                    message=(
                        f"Policy '{_policy_label(row)}' has unreadable MBILLDAY "
                        f"'{billday.decoded_display or billday.original_display}'."
                    ),
                    expected="MBILLDAY between 1 and 31",
                    actual="Unreadable value",
                    failure_category="UNREADABLE_VALUE",
                )
            )
            continue

        try:
            day_val = int(billday.decoded_display or billday.original_display.strip())
        except (TypeError, ValueError):
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKMSTR,
                    field="MBILLDAY",
                    record_id=idx,
                    key_value=pol,
                    policy_number=pol,
                    message=f"Policy '{_policy_label(row)}' has invalid MBILLDAY.",
                    expected="MBILLDAY between 1 and 31",
                    actual="Unreadable value",
                    failure_category="UNREADABLE_VALUE",
                )
            )
            continue

        if 1 <= day_val <= 31:
            result.passed_count += 1
            continue

        result.findings.append(
            fail(
                rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_dir=store.data_dir,
                table=TABLE_QUIKMSTR,
                field="MBILLDAY",
                record_id=idx,
                key_value=pol,
                policy_number=pol,
                message=(
                    f"Policy '{_policy_label(row)}' has MBILLDAY='{day_val}' "
                    f"outside the allowed range."
                ),
                expected="MBILLDAY between 1 and 31",
                actual=f"Value {day_val}",
                failure_category="OUT_OF_RANGE",
            )
        )
    return finalize(result)


def run_dg_quikmstr_012(store: GovernanceDataStore, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKMSTR_012
    mstr, missing = _require_mstr(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = base_result(rule)
    rows = mstr.rows
    result.records_evaluated = len(rows)
    for idx, row in enumerate(rows, start=1):
        pol = policy_key_from_row(row)
        billfrm, _, _ = norm_char(field_value(row, "MBILLFRM"))
        if billfrm != "2":
            result.passed_count += 1
            continue
        bank, orig, is_null = norm_char(field_value(row, "MBANKNO"))
        if is_null or bank == "":
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKMSTR,
                    field="MBANKNO",
                    record_id=idx,
                    key_value=pol,
                    policy_number=pol,
                    message=(
                        f"Policy '{_policy_label(row)}' uses bank draft billing but "
                        f"has no bank account number."
                    ),
                    expected="MBANKNO populated when MBILLFRM is 2",
                    actual="Blank or null MBANKNO",
                    failure_category="BLANK_VALUE",
                )
            )
            continue
        result.passed_count += 1
    return finalize(result)


def run_dg_quikmstr_013(store: GovernanceDataStore, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKMSTR_013
    mstr, missing = _require_mstr(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = base_result(rule)
    rows = mstr.rows
    result.records_evaluated = len(rows)
    for idx, row in enumerate(rows, start=1):
        pol = policy_key_from_row(row)
        norm, orig, is_null = norm_char(field_value(row, "MMODE"))
        if is_null or norm == "":
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKMSTR,
                    field="MMODE",
                    record_id=idx,
                    key_value=pol,
                    policy_number=pol,
                    message=f"Policy '{_policy_label(row)}' has a blank payment mode.",
                    expected="MMODE is a populated approved payment-mode code",
                    actual="Blank or null",
                    failure_category="BLANK_VALUE",
                )
            )
            continue
        if not is_approved("MMODE", norm):
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKMSTR,
                    field="MMODE",
                    record_id=idx,
                    key_value=pol,
                    policy_number=pol,
                    message=(
                        f"Policy '{_policy_label(row)}' has unapproved payment mode "
                        f"'{orig or norm}'."
                    ),
                    expected="MMODE is in the approved payment-mode code list",
                    actual=f"Unapproved value '{orig or norm}'",
                    failure_category="UNAPPROVED_CODE",
                )
            )
            continue
        result.passed_count += 1
    return finalize(result)


def run_dg_quikmstr_014(store: GovernanceDataStore, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKMSTR_014
    mstr, missing = _require_mstr(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = base_result(rule)
    rows = mstr.rows
    result.records_evaluated = len(rows)
    for idx, row in enumerate(rows, start=1):
        pol = policy_key_from_row(row)
        norm, orig, is_null = norm_char(field_value(row, "MISSUEST"))
        if is_null or norm == "":
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKMSTR,
                    field="MISSUEST",
                    record_id=idx,
                    key_value=pol,
                    policy_number=pol,
                    message=f"Policy '{_policy_label(row)}' has a blank issue state.",
                    expected="MISSUEST is an approved US state abbreviation",
                    actual="Blank or null",
                    failure_category="BLANK_VALUE",
                )
            )
            continue
        state = norm.upper()
        if state in APPROVED_US_STATE_ABBREVIATIONS:
            result.passed_count += 1
            continue
        result.findings.append(
            fail(
                rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_dir=store.data_dir,
                table=TABLE_QUIKMSTR,
                field="MISSUEST",
                record_id=idx,
                key_value=pol,
                policy_number=pol,
                message=(
                    f"Policy '{_policy_label(row)}' has unapproved issue state "
                    f"'{orig or norm}'."
                ),
                expected="MISSUEST is an approved US state abbreviation",
                actual=f"Unapproved state '{orig or norm}'",
                failure_category="UNAPPROVED_CODE",
            )
        )
    return finalize(result)


def _run_optional_client_ref(
    store,
    rule,
    *,
    run_id,
    run_timestamp,
    field_name,
):
    mstr, missing = _require_mstr(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    clnt = store.get(TABLE_QUIKCLNT)
    client_index = build_client_index(clnt.rows) if clnt is not None else None
    result = base_result(rule)
    rows = mstr.rows
    result.records_evaluated = len(rows)
    cnbc_reported = False

    for idx, row in enumerate(rows, start=1):
        pol = policy_key_from_row(row)
        norm, orig, is_null = norm_char(field_value(row, field_name))
        if is_null or norm == "":
            result.passed_count += 1
            continue
        if client_index is None:
            if not cnbc_reported:
                result.findings.append(
                    fail(
                        rule,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_dir=store.data_dir,
                        table=TABLE_QUIKMSTR,
                        field=field_name,
                        record_id=idx,
                        key_value=pol,
                        policy_number=pol,
                        message=(
                            f"Client references in {field_name} could not be checked "
                            f"because QuikClnt was not loaded."
                        ),
                        expected=f"{field_name} exists in QuikClnt when populated",
                        actual="Could Not Be Checked — QuikClnt unavailable",
                        status=STATUS_ERROR,
                        failure_category="COULD_NOT_BE_CHECKED",
                        reference_table=TABLE_QUIKCLNT,
                        reference_field="MCLIENTID",
                    )
                )
                cnbc_reported = True
            continue
        if norm in client_index:
            result.passed_count += 1
            continue
        result.findings.append(
            fail(
                rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_dir=store.data_dir,
                table=TABLE_QUIKMSTR,
                field=field_name,
                record_id=idx,
                key_value=pol,
                policy_number=pol,
                message=(
                    f"Policy '{_policy_label(row)}' references client '{norm}' "
                    f"that does not exist in QuikClnt."
                ),
                expected=f"{field_name} exists in QuikClnt when populated",
                actual=f"Missing client '{orig or norm}'",
                failure_category="MISSING_REFERENCE",
                reference_table=TABLE_QUIKCLNT,
                reference_field="MCLIENTID",
                reference_match_count="0",
            )
        )
    return finalize(result)


def run_dg_quikmstr_015(store: GovernanceDataStore, *, run_id, run_timestamp):
    rule = RULE_DG_QUIKMSTR_015
    mstr, missing = _require_mstr(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    quiklist = store.get(TABLE_QUIKLIST)
    group_index = build_group_index(quiklist.rows) if quiklist is not None else None
    result = base_result(rule)
    rows = mstr.rows
    result.records_evaluated = len(rows)
    cnbc_reported = False

    for idx, row in enumerate(rows, start=1):
        pol = policy_key_from_row(row)
        norm, orig, is_null = norm_char(field_value(row, "MGROUP"))
        if is_null or norm == "":
            result.passed_count += 1
            continue
        if group_index is None:
            if not cnbc_reported:
                result.findings.append(
                    fail(
                        rule,
                        run_id=run_id,
                        run_timestamp=run_timestamp,
                        data_dir=store.data_dir,
                        table=TABLE_QUIKMSTR,
                        field="MGROUP",
                        record_id=idx,
                        key_value=pol,
                        policy_number=pol,
                        message=(
                            "Group number references could not be checked because "
                            "QuikList was not loaded."
                        ),
                        expected="Populated MGROUP exists in QuikList",
                        actual="Could Not Be Checked — QuikList unavailable",
                        status=STATUS_ERROR,
                        failure_category="COULD_NOT_BE_CHECKED",
                        reference_table=TABLE_QUIKLIST,
                        reference_field="MGROUP",
                    )
                )
                cnbc_reported = True
            continue
        if norm in group_index:
            result.passed_count += 1
            continue
        result.findings.append(
            fail(
                rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_dir=store.data_dir,
                table=TABLE_QUIKMSTR,
                field="MGROUP",
                record_id=idx,
                key_value=pol,
                policy_number=pol,
                message=(
                    f"Policy '{_policy_label(row)}' references group '{norm}' "
                    f"that does not exist in QuikList."
                ),
                expected="Populated MGROUP exists in QuikList",
                actual=f"Missing group '{orig or norm}'",
                failure_category="MISSING_REFERENCE",
                reference_table=TABLE_QUIKLIST,
                reference_field="MGROUP",
                reference_match_count="0",
                group_number=norm,
            )
        )
    return finalize(result)


def run_dg_quikmstr_016(store: GovernanceDataStore, *, run_id, run_timestamp):
    return _run_optional_client_ref(
        store,
        RULE_DG_QUIKMSTR_016,
        run_id=run_id,
        run_timestamp=run_timestamp,
        field_name="MPRIMID",
    )


def run_dg_quikmstr_017(store: GovernanceDataStore, *, run_id, run_timestamp):
    return _run_optional_client_ref(
        store,
        RULE_DG_QUIKMSTR_017,
        run_id=run_id,
        run_timestamp=run_timestamp,
        field_name="MOWNRID",
    )


def run_dg_quikmstr_018(store: GovernanceDataStore, *, run_id, run_timestamp):
    return _run_optional_client_ref(
        store,
        RULE_DG_QUIKMSTR_018,
        run_id=run_id,
        run_timestamp=run_timestamp,
        field_name="MASGNID",
    )


def run_dg_quikmstr_019(store: GovernanceDataStore, *, run_id, run_timestamp):
    return _run_optional_client_ref(
        store,
        RULE_DG_QUIKMSTR_019,
        run_id=run_id,
        run_timestamp=run_timestamp,
        field_name="MPAYRID",
    )


def run_dg_quikmstr_020(store: GovernanceDataStore, *, run_id, run_timestamp):
    return _run_optional_client_ref(
        store,
        RULE_DG_QUIKMSTR_020,
        run_id=run_id,
        run_timestamp=run_timestamp,
        field_name="MOWNCID",
    )


def _run_must_be_blank(store, rule, *, run_id, run_timestamp, field_name):
    mstr, missing = _require_mstr(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = base_result(rule)
    rows = mstr.rows
    result.records_evaluated = len(rows)
    for idx, row in enumerate(rows, start=1):
        pol = policy_key_from_row(row)
        norm, orig, is_null = norm_char(field_value(row, field_name))
        if is_null or norm == "":
            result.passed_count += 1
            continue
        result.findings.append(
            fail(
                rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_dir=store.data_dir,
                table=TABLE_QUIKMSTR,
                field=field_name,
                record_id=idx,
                key_value=pol,
                policy_number=pol,
                message=(
                    f"Policy '{_policy_label(row)}' has populated {field_name} "
                    f"'{orig or norm}'; converted output must be blank."
                ),
                expected=f"{field_name} is blank in converted output",
                actual=f"Populated value '{orig or norm}'",
                failure_category="UNEXPECTED_VALUE",
            )
        )
    return finalize(result)


def run_dg_quikmstr_021(store: GovernanceDataStore, *, run_id, run_timestamp):
    return _run_must_be_blank(
        store,
        RULE_DG_QUIKMSTR_021,
        run_id=run_id,
        run_timestamp=run_timestamp,
        field_name="MBENPID",
    )


def run_dg_quikmstr_022(store: GovernanceDataStore, *, run_id, run_timestamp):
    return _run_must_be_blank(
        store,
        RULE_DG_QUIKMSTR_022,
        run_id=run_id,
        run_timestamp=run_timestamp,
        field_name="MBENCID",
    )
