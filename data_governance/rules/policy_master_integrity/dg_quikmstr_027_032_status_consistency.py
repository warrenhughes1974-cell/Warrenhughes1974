"""DG-QUIKMSTR-027 through 032 — cross-table policy/coverage status consistency.

Issue #108 track G. Robert asked that policy and coverage statuses be crosswalk-driven in
the converter, with consistency checks living here in governance rather than being forced
by rules inside the conversion program. These rules report; they never change data.

Checks 027, 028, 029 and 030 are Robert's four consistency checks. 031 is his follow-up
question about the nonforfeiture election, which became answerable once Issue #108F stopped
forcing MNFOPT from the policy status. 032 guards the Issue #108 field contract.
"""

from __future__ import annotations

from collections import defaultdict

from data_governance.catalog.governance_items_policy_data import (
    RULE_DG_QUIKMSTR_027,
    RULE_DG_QUIKMSTR_028,
    RULE_DG_QUIKMSTR_029,
    RULE_DG_QUIKMSTR_030,
    RULE_DG_QUIKMSTR_031,
    RULE_DG_QUIKMSTR_032,
)
from data_governance.config.settings import TABLE_QUIKMSTR, TABLE_QUIKRIDR
from data_governance.data_access.table_loader import GovernanceDataStore, field_value
from data_governance.models.statuses import STATUS_ERROR, STATUS_WARN
from data_governance.rules.policy_master_integrity.common import (
    base_result,
    fail,
    finalize,
    missing_table,
    norm_policy,
    parse_phase,
    policy_key_from_row,
)

# A coverage or policy is in force below 50 and terminated at 50 or above. Robert wrote the
# rules as "> 50" for terminated; 50 itself is included here because 15 policies carry it and
# leaving it out would create a silent gap. The stricter reading changes nothing today.
TERMINATED_FLOOR = 50
STATUS_ETI = 44
STATUS_RPU = 45
NFO_STATUSES = (STATUS_ETI, STATUS_RPU)
# Below this a policy is considered active for check 030 (Robert: MSTATUS < "44").
ACTIVE_CEILING = 44

# On these plans the phase 1 base carries zero units and the later phase holds the entire
# face amount, so an in-force later phase is the expected structure. Excluded from 029 until
# Issue #108E confirms the source. Removing this set would flag 77 legitimate RPU policies.
ZERO_UNIT_BASE_PLANS = frozenset({"1SALML", "1SALMI"})

NFO_SAVE_FIELDS = ("MSAVEAGE", "MSAVEUNIT", "MSAVEVPU", "MSAVEPREM", "MSAVESTAT")


def _text(raw) -> str:
    if raw is None:
        return ""
    return str(raw).strip()


def _status_int(raw) -> int | None:
    """Status codes are two-digit; tolerate DBF numeric artefacts such as '44.0'."""
    digits = "".join(c for c in _text(raw) if c.isdigit())
    return int(digits) if digits else None


def _coverage_in_force(row) -> bool | None:
    """True in force, False terminated, None when MPHSTAT cannot be read.

    Unreadable is deliberately not folded into either side. Treating it as terminated would
    invent an "active policy with no in-force coverage" failure out of a missing field, and
    treating it as in force would invent the opposite on a terminated policy.
    """
    status = _status_int(field_value(row, "MPHSTAT"))
    if status is None:
        return None
    return status < TERMINATED_FLOOR


def _digits8(raw) -> str:
    digits = "".join(c for c in _text(raw) if c.isdigit())
    return digits[:8] if len(digits) >= 8 else ""


def _is_pua_plan(plan: str) -> bool:
    p = _text(plan).upper()
    return len(p) >= 6 and p.endswith("PA")


def _require_tables(store, rule, *, run_id, run_timestamp):
    """Both tables are mandatory — a cross-table check cannot degrade to one side."""
    for table_name in (TABLE_QUIKMSTR, TABLE_QUIKRIDR):
        if store.get(table_name) is None:
            return None, None, missing_table(
                rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_dir=store.data_dir,
                table_name=table_name,
            )
    return store.get(TABLE_QUIKMSTR), store.get(TABLE_QUIKRIDR), None


def _riders_by_policy(ridr) -> dict[str, list[tuple[int, dict]]]:
    grouped: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    for idx, row in enumerate(ridr.rows, start=1):
        pol, _, is_null = norm_policy(field_value(row, "MPOLICY"))
        if is_null or not pol:
            continue
        grouped[pol].append((idx, row))
    return grouped


def _phase_one(rider_rows) -> tuple[int, dict] | None:
    for idx, row in rider_rows:
        if parse_phase(field_value(row, "MPHASE")) == 1:
            return idx, row
    return None


def _no_coverage_finding(
    rule, *, run_id, run_timestamp, store, idx, pol, message, expected,
    actual="No QuikRidr coverage rows for this policy",
):
    """Coverage rows are required to evaluate these rules; absence is not a silent pass."""
    return fail(
        rule,
        run_id=run_id,
        run_timestamp=run_timestamp,
        data_dir=store.data_dir,
        table=TABLE_QUIKMSTR,
        field="MPOLICY",
        record_id=idx,
        key_value=pol,
        policy_number=pol,
        message=message,
        expected=expected,
        actual=actual,
        status=STATUS_ERROR,
        failure_category="COULD_NOT_BE_CHECKED",
        reference_table=TABLE_QUIKRIDR,
        reference_field="MPOLICY",
        reference_match_count="0",
    )


def run_dg_quikmstr_027(store: GovernanceDataStore, *, run_id, run_timestamp):
    """Terminated policy must not have in-force coverage."""
    rule = RULE_DG_QUIKMSTR_027
    mstr, ridr, missing = _require_tables(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    grouped = _riders_by_policy(ridr)
    result = base_result(rule)

    for idx, row in enumerate(mstr.rows, start=1):
        status = _status_int(field_value(row, "MSTATUS"))
        if status is None or status < TERMINATED_FLOOR:
            continue
        pol = policy_key_from_row(row)
        in_force = [
            (r_idx, r_row)
            for r_idx, r_row in grouped.get(pol, [])
            if _coverage_in_force(r_row) is True
        ]
        if not in_force:
            result.passed_count += 1
            continue
        for r_idx, r_row in in_force:
            phase = parse_phase(field_value(r_row, "MPHASE"))
            plan = _text(field_value(r_row, "MPLAN"))
            cov_status = _text(field_value(r_row, "MPHSTAT"))
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKRIDR,
                    field="MPHSTAT",
                    record_id=r_idx,
                    key_value=pol,
                    policy_number=pol,
                    message=(
                        f"Policy '{pol}' is terminated at status {status} but coverage "
                        f"phase {phase} plan '{plan}' is still in force at {cov_status}."
                    ),
                    expected=f"All coverages terminated (MPHSTAT {TERMINATED_FLOOR} or greater)",
                    actual=cov_status,
                    reference_table=TABLE_QUIKMSTR,
                    reference_field="MSTATUS",
                )
            )
    return finalize(result)


def run_dg_quikmstr_028(store: GovernanceDataStore, *, run_id, run_timestamp):
    """ETI/RPU phase 1 coverage status must match the policy status."""
    rule = RULE_DG_QUIKMSTR_028
    mstr, ridr, missing = _require_tables(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    grouped = _riders_by_policy(ridr)
    result = base_result(rule)

    for idx, row in enumerate(mstr.rows, start=1):
        status = _status_int(field_value(row, "MSTATUS"))
        if status not in NFO_STATUSES:
            continue
        pol = policy_key_from_row(row)
        phase1 = _phase_one(grouped.get(pol, []))
        if phase1 is None:
            result.findings.append(
                _no_coverage_finding(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    store=store,
                    idx=idx,
                    pol=pol,
                    message=(
                        f"Policy '{pol}' is on nonforfeiture at status {status} but has no "
                        "phase 1 coverage row."
                    ),
                    expected="Phase 1 coverage exists and carries the policy status",
                )
            )
            continue
        r_idx, r_row = phase1
        cov_status = _status_int(field_value(r_row, "MPHSTAT"))
        if cov_status == status:
            result.passed_count += 1
            continue
        result.findings.append(
            fail(
                rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_dir=store.data_dir,
                table=TABLE_QUIKRIDR,
                field="MPHSTAT",
                record_id=r_idx,
                key_value=pol,
                policy_number=pol,
                message=(
                    f"Policy '{pol}' is on nonforfeiture at status {status} but phase 1 "
                    f"coverage carries status {_text(field_value(r_row, 'MPHSTAT'))}."
                ),
                expected=f"Phase 1 MPHSTAT equals policy MSTATUS ({status})",
                actual=_text(field_value(r_row, "MPHSTAT")),
                reference_table=TABLE_QUIKMSTR,
                reference_field="MSTATUS",
            )
        )
    return finalize(result)


def run_dg_quikmstr_029(store: GovernanceDataStore, *, run_id, run_timestamp):
    """ETI/RPU policy should not carry other in-force coverages. Advisory."""
    rule = RULE_DG_QUIKMSTR_029
    mstr, ridr, missing = _require_tables(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    grouped = _riders_by_policy(ridr)
    result = base_result(rule)
    excluded = 0

    for idx, row in enumerate(mstr.rows, start=1):
        status = _status_int(field_value(row, "MSTATUS"))
        if status not in NFO_STATUSES:
            continue
        pol = policy_key_from_row(row)
        flagged = False
        for r_idx, r_row in grouped.get(pol, []):
            phase = parse_phase(field_value(r_row, "MPHASE"))
            if phase is None or phase <= 1:
                continue
            if _coverage_in_force(r_row) is not True:
                continue
            plan = _text(field_value(r_row, "MPLAN")).upper()
            if plan in ZERO_UNIT_BASE_PLANS:
                excluded += 1
                continue
            flagged = True
            result.findings.append(
                fail(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    data_dir=store.data_dir,
                    table=TABLE_QUIKRIDR,
                    field="MPHSTAT",
                    record_id=r_idx,
                    key_value=pol,
                    policy_number=pol,
                    message=(
                        f"Policy '{pol}' is on nonforfeiture at status {status} but phase "
                        f"{phase} plan '{plan}' is still in force at "
                        f"{_text(field_value(r_row, 'MPHSTAT'))}. Confirm against the source "
                        "system before terminating."
                    ),
                    expected="Coverages beyond phase 1 terminated on an ETI or RPU policy",
                    actual=_text(field_value(r_row, "MPHSTAT")),
                    status=STATUS_WARN,
                    failure_category="REVIEW_REQUIRED",
                    reference_table=TABLE_QUIKMSTR,
                    reference_field="MSTATUS",
                )
            )
        if not flagged:
            result.passed_count += 1

    result.summary_metrics = {"zero_unit_base_rows_excluded": excluded}
    return finalize(result)


def run_dg_quikmstr_030(store: GovernanceDataStore, *, run_id, run_timestamp):
    """Active policy must have at least one in-force coverage."""
    rule = RULE_DG_QUIKMSTR_030
    mstr, ridr, missing = _require_tables(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    grouped = _riders_by_policy(ridr)
    result = base_result(rule)

    for idx, row in enumerate(mstr.rows, start=1):
        status = _status_int(field_value(row, "MSTATUS"))
        if status is None or status >= ACTIVE_CEILING:
            continue
        pol = policy_key_from_row(row)
        rider_rows = grouped.get(pol, [])
        if not rider_rows:
            result.findings.append(
                _no_coverage_finding(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    store=store,
                    idx=idx,
                    pol=pol,
                    message=(
                        f"Policy '{pol}' is active at status {status} but has no coverage "
                        "rows at all."
                    ),
                    expected="At least one in-force coverage",
                )
            )
            continue
        states = [_coverage_in_force(r_row) for _, r_row in rider_rows]
        if any(state is True for state in states):
            result.passed_count += 1
            continue
        if all(state is None for state in states):
            result.findings.append(
                _no_coverage_finding(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    store=store,
                    idx=idx,
                    pol=pol,
                    message=(
                        f"Policy '{pol}' is active at status {status} but no coverage row "
                        "carries a readable MPHSTAT."
                    ),
                    expected="At least one in-force coverage",
                    actual=f"{len(rider_rows)} coverage row(s) with unreadable MPHSTAT",
                )
            )
            continue
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
                    f"Policy '{pol}' is active at status {status} but all "
                    f"{len(rider_rows)} coverages are terminated."
                ),
                expected=f"At least one coverage with MPHSTAT below {TERMINATED_FLOOR}",
                actual="All coverages terminated",
                reference_table=TABLE_QUIKRIDR,
                reference_field="MPHSTAT",
            )
        )
    return finalize(result)


def run_dg_quikmstr_031(store: GovernanceDataStore, *, run_id, run_timestamp):
    """ETI/RPU election should match the policy status. Advisory."""
    rule = RULE_DG_QUIKMSTR_031
    mstr, _ridr, missing = _require_tables(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    result = base_result(rule)
    expected_election = {STATUS_ETI: "2", STATUS_RPU: "3"}

    for idx, row in enumerate(mstr.rows, start=1):
        status = _status_int(field_value(row, "MSTATUS"))
        if status not in NFO_STATUSES:
            continue
        pol = policy_key_from_row(row)
        want = expected_election[status]
        got = _text(field_value(row, "MNFOPT")).replace(".0", "")
        if got == want:
            result.passed_count += 1
            continue
        label = "ETI" if status == STATUS_ETI else "RPU"
        detail = "no election recorded" if got in ("", "0") else f"election {got}"
        result.findings.append(
            fail(
                rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_dir=store.data_dir,
                table=TABLE_QUIKMSTR,
                field="MNFOPT",
                record_id=idx,
                key_value=pol,
                policy_number=pol,
                message=(
                    f"Policy '{pol}' is on {label} at status {status} but carries {detail}. "
                    "Confirm the election against the source system."
                ),
                expected=f"MNFOPT {want} for status {status} ({label})",
                actual=got or "(blank)",
                status=STATUS_WARN,
                failure_category="REVIEW_REQUIRED",
            )
        )
    return finalize(result)


def run_dg_quikmstr_032(store: GovernanceDataStore, *, run_id, run_timestamp):
    """ETI/RPU field completeness — guards the Issue #108 conversion contract."""
    rule = RULE_DG_QUIKMSTR_032
    mstr, ridr, missing = _require_tables(store, rule, run_id=run_id, run_timestamp=run_timestamp)
    if missing:
        return missing
    grouped = _riders_by_policy(ridr)
    result = base_result(rule)

    def flag(*, record_id, pol, field, message, expected, actual):
        result.findings.append(
            fail(
                rule,
                run_id=run_id,
                run_timestamp=run_timestamp,
                data_dir=store.data_dir,
                table=TABLE_QUIKRIDR,
                field=field,
                record_id=record_id,
                key_value=pol,
                policy_number=pol,
                message=message,
                expected=expected,
                actual=actual,
                reference_table=TABLE_QUIKMSTR,
                reference_field="MSTATUS",
            )
        )

    for idx, row in enumerate(mstr.rows, start=1):
        status = _status_int(field_value(row, "MSTATUS"))
        if status not in NFO_STATUSES:
            continue
        pol = policy_key_from_row(row)
        rider_rows = grouped.get(pol, [])
        phase1 = _phase_one(rider_rows)
        if phase1 is None:
            result.findings.append(
                _no_coverage_finding(
                    rule,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    store=store,
                    idx=idx,
                    pol=pol,
                    message=(
                        f"Policy '{pol}' is on nonforfeiture at status {status} but has no "
                        "phase 1 coverage row to check."
                    ),
                    expected="Phase 1 coverage exists",
                )
            )
            continue

        r_idx, r_row = phase1
        before = len(result.findings)

        paid_to = _digits8(field_value(row, "MPAIDTO"))
        pay_up = _digits8(field_value(r_row, "MPAYUP"))
        if paid_to and pay_up != paid_to:
            flag(
                record_id=r_idx, pol=pol, field="MPAYUP",
                message=(
                    f"Policy '{pol}' phase 1 pay-up date {pay_up or '(blank)'} does not "
                    f"match the policy paid-to date {paid_to}."
                ),
                expected=f"MPAYUP equals MPAIDTO ({paid_to})",
                actual=pay_up or "(blank)",
            )

        age = _text(field_value(r_row, "MAGE")).lstrip("0")
        if not age:
            flag(
                record_id=r_idx, pol=pol, field="MAGE",
                message=(
                    f"Policy '{pol}' phase 1 age is blank or zero. On nonforfeiture it must "
                    "be the attained age at the paid-to date."
                ),
                expected="MAGE populated and nonzero",
                actual=_text(field_value(r_row, "MAGE")) or "(blank)",
            )

        populated_saves = [f for f in NFO_SAVE_FIELDS if _text(field_value(r_row, f))]
        if populated_saves:
            flag(
                record_id=r_idx, pol=pol, field=populated_saves[0],
                message=(
                    f"Policy '{pol}' phase 1 carries populated save fields "
                    f"({', '.join(populated_saves)}). On a converted nonforfeiture policy "
                    "these must be blank, otherwise a reinstatement restores the policy "
                    "back into its ETI or RPU state."
                ),
                expected="All MSAVE* fields blank on an ETI or RPU phase 1 row",
                actual=", ".join(populated_saves),
            )

        if status == STATUS_ETI:
            raw_prem = _text(field_value(r_row, "MPREM"))
            try:
                prem = float(raw_prem or 0)
            except ValueError:
                prem = -1.0
            if prem != 0.0:
                flag(
                    record_id=r_idx, pol=pol, field="MPREM",
                    message=(
                        f"Policy '{pol}' is on extended term but phase 1 premium is "
                        f"{raw_prem}. Extended term is paid up, so the premium is zero."
                    ),
                    expected="MPREM is 0 on an ETI policy",
                    actual=raw_prem or "(blank)",
                )

        for pua_idx, pua_row in rider_rows:
            if not _is_pua_plan(field_value(pua_row, "MPLAN")):
                continue
            if _text(field_value(pua_row, "MPHSTAT")) == "54":
                continue
            flag(
                record_id=pua_idx, pol=pol, field="MPHSTAT",
                message=(
                    f"Policy '{pol}' paid-up addition '{_text(field_value(pua_row, 'MPLAN'))}' "
                    f"carries status {_text(field_value(pua_row, 'MPHSTAT'))}. On ETI or RPU "
                    "the addition folds into the base and its coverage terminates."
                ),
                expected="Paid-up addition coverage terminated at 54",
                actual=_text(field_value(pua_row, "MPHSTAT")),
            )

        if len(result.findings) == before:
            result.passed_count += 1

    return finalize(result)
