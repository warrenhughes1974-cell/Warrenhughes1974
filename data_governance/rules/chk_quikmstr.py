"""Category 10 — Policy master (quikmstr) checks."""

from __future__ import annotations

from data_governance.constants.valid_codes import VALID_MSTATUS_CODES
from data_governance.constants.valid_states import VALID_US_STATES
from data_governance.governance_config import ADVISORY, CRITICAL, HIGH, INFO, AuditFinding, make_finding
from data_governance.rules._helpers import (
    client_ids,
    col,
    get_df,
    parse_date,
    s,
    to_float,
    unique_values,
)


def check_quikmstr(data: dict) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    df = get_df(data, "quikmstr", "quikmstr.csv")
    if df is None or df.empty:
        return findings

    clnt = get_df(data, "quikclnt", "quikclnt.csv")
    valid_clients = client_ids(clnt)
    lst = get_df(data, "quiklist", "quiklist.csv")
    groups = set()
    if lst is not None:
        gc = col(lst, "MGROUP", "GROUP", "GROUPNO", "MGRP")
        if gc:
            groups = unique_values(lst[gc])

    pol_c = col(df, "MPOLICY")
    if not pol_c:
        return findings

    # POL-001 duplicates
    counts: dict[str, int] = {}
    for _, row in df.iterrows():
        p = s(row.get(pol_c))
        if p:
            counts[p] = counts.get(p, 0) + 1
    for p, n in counts.items():
        if n > 1:
            findings.append(
                make_finding(
                    rule_id="POL-001",
                    rule_category="Policy Master",
                    severity=CRITICAL,
                    source_file="quikmstr.csv",
                    description="MPOLICY values must be unique.",
                    reason=f"MPOLICY '{p}' appears {n} times in quikmstr. Policy numbers must be unique.",
                    field_name="MPOLICY",
                    expected="unique",
                    actual=str(n),
                    affected_keys=[p],
                    affected_count=n,
                )
            )

    # Spec field name -> (rule_id, actual column aliases on quikmstr)
    client_fields = (
        ("POL-017", "MPRIMID", ("MPRIMID",), "MPRIMID"),
        ("POL-018", "MOWNERID", ("MOWNRID", "MOWNERID"), "MOWNERID"),
        ("POL-019", "MASSIGID", ("MASGNID", "MASSIGID"), "MASSIGID"),
        ("POL-020", "MPAYERID", ("MPAYRID", "MPAYERID"), "MPAYERID"),
        ("POL-021", "MOWNCID", ("MOWNCID",), "MOWNCID"),
    )

    for idx, row in df.iterrows():
        pol = s(row.get(pol_c))
        rownum = idx if isinstance(idx, int) else 0

        # POL-002
        if not pol:
            findings.append(
                make_finding(
                    rule_id="POL-002",
                    rule_category="Policy Master",
                    severity=CRITICAL,
                    source_file="quikmstr.csv",
                    description="MPOLICY must be populated on every row.",
                    reason=f"Row {rownum} in quikmstr has a blank or null MPOLICY. Every policy record must have a policy number.",
                    field_name="MPOLICY",
                    expected="populated",
                    actual="",
                    affected_keys=[str(rownum)],
                    affected_count=1,
                )
            )
            continue

        # POL-003 MPLAN
        mplan_c = col(df, "MPLAN", "PLAN")
        # MPLAN may not be on quikmstr schema — skip if absent
        if mplan_c and not s(row.get(mplan_c)):
            findings.append(
                make_finding(
                    rule_id="POL-003",
                    rule_category="Policy Master",
                    severity=CRITICAL,
                    source_file="quikmstr.csv",
                    description="MPLAN must be populated.",
                    reason=f"Policy '{pol}' has no MPLAN value.",
                    field_name="MPLAN",
                    expected="populated",
                    actual="",
                    affected_keys=[pol],
                    affected_count=1,
                )
            )

        # POL-004 MSTATUS
        st_c = col(df, "MSTATUS")
        if st_c:
            st = s(row.get(st_c))
            if not st or st not in VALID_MSTATUS_CODES:
                findings.append(
                    make_finding(
                        rule_id="POL-004",
                        rule_category="Policy Master",
                        severity=CRITICAL,
                        source_file="quikmstr.csv",
                        description="MSTATUS must be a recognized status code.",
                        reason=(
                            f"Policy '{pol}' has MSTATUS='{st}' which is not a recognized status code."
                        ),
                        field_name="MSTATUS",
                        expected="valid status code",
                        actual=st,
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )

        # POL-005 / POL-007 MSTATDATE
        msd_c = col(df, "MSTATDATE")
        if msd_c:
            raw = s(row.get(msd_c))
            if not raw:
                findings.append(
                    make_finding(
                        rule_id="POL-007",
                        rule_category="Policy Master",
                        severity=CRITICAL,
                        source_file="quikmstr.csv",
                        description="MSTATDATE must be populated.",
                        reason=f"Policy '{pol}' MSTATDATE is blank.",
                        field_name="MSTATDATE",
                        expected="populated date",
                        actual="",
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )
            elif parse_date(raw) is None:
                findings.append(
                    make_finding(
                        rule_id="POL-005",
                        rule_category="Policy Master",
                        severity=CRITICAL,
                        source_file="quikmstr.csv",
                        description="MSTATDATE must be a valid date.",
                        reason=f"Policy '{pol}' has invalid or blank MSTATDATE='{raw}'.",
                        field_name="MSTATDATE",
                        expected="valid date",
                        actual=raw,
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )

        # POL-006 MISSDT
        iss_c = col(df, "MISSDT")
        iss_d = None
        if iss_c:
            raw = s(row.get(iss_c))
            iss_d = parse_date(raw)
            if not raw or iss_d is None:
                findings.append(
                    make_finding(
                        rule_id="POL-006",
                        rule_category="Policy Master",
                        severity=CRITICAL,
                        source_file="quikmstr.csv",
                        description="MISSDT (issue date) must be populated and valid.",
                        reason=f"Policy '{pol}' has invalid or blank MISSDT='{raw}'.",
                        field_name="MISSDT",
                        expected="valid date",
                        actual=raw,
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )

        # POL-008 MPAIDTO >= MISSDT
        paid_c = col(df, "MPAIDTO")
        paid_d = parse_date(row.get(paid_c)) if paid_c else None
        if iss_d and paid_d and paid_d < iss_d:
            findings.append(
                make_finding(
                    rule_id="POL-008",
                    rule_category="Policy Master",
                    severity=HIGH,
                    source_file="quikmstr.csv",
                    description="MPAIDTO must be >= MISSDT.",
                    reason=(
                        f"Policy '{pol}' has MPAIDTO='{s(row.get(paid_c))}' which is before "
                        f"MISSDT='{s(row.get(iss_c))}'. Paid-to date cannot precede issue date."
                    ),
                    field_name="MPAIDTO",
                    expected=f">= {s(row.get(iss_c))}",
                    actual=s(row.get(paid_c)),
                    affected_keys=[pol],
                    affected_count=1,
                )
            )

        # POL-009 MBILLTO
        bill_c = col(df, "MBILLTO")
        bill_d = parse_date(row.get(bill_c)) if bill_c else None
        if bill_d and iss_d and bill_d < iss_d:
            findings.append(
                make_finding(
                    rule_id="POL-009",
                    rule_category="Policy Master",
                    severity=HIGH,
                    source_file="quikmstr.csv",
                    description="MBILLTO must be >= MISSDT.",
                    reason=(
                        f"Policy '{pol}' MBILLTO='{s(row.get(bill_c))}' is before "
                        f"MISSDT='{s(row.get(iss_c))}'."
                    ),
                    field_name="MBILLTO",
                    expected=f">= {s(row.get(iss_c))}",
                    actual=s(row.get(bill_c)),
                    affected_keys=[pol],
                    affected_count=1,
                )
            )
        if bill_d and paid_d and bill_d < paid_d:
            findings.append(
                make_finding(
                    rule_id="POL-009",
                    rule_category="Policy Master",
                    severity=HIGH,
                    source_file="quikmstr.csv",
                    description="MBILLTO should not be < MPAIDTO.",
                    reason=(
                        f"Policy '{pol}' MBILLTO='{s(row.get(bill_c))}' is before "
                        f"MPAIDTO='{s(row.get(paid_c))}'."
                    ),
                    field_name="MBILLTO",
                    expected=f">= {s(row.get(paid_c))}",
                    actual=s(row.get(bill_c)),
                    affected_keys=[pol],
                    affected_count=1,
                )
            )

        # POL-010 MNFOPT
        nf_c = col(df, "MNFOPT")
        if nf_c:
            nf = s(row.get(nf_c))
            if nf and to_float(nf, 0) != 0:
                findings.append(
                    make_finding(
                        rule_id="POL-010",
                        rule_category="Policy Master",
                        severity=ADVISORY,
                        source_file="quikmstr.csv",
                        description="MNFOPT should default to 0.",
                        reason=f"Policy '{pol}' MNFOPT='{nf}', expected default 0.",
                        field_name="MNFOPT",
                        expected="0",
                        actual=nf,
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )

        # POL-011 MBILLFRM
        bf_c = col(df, "MBILLFRM")
        bf = s(row.get(bf_c)) if bf_c else ""
        if bf_c and not bf:
            findings.append(
                make_finding(
                    rule_id="POL-011",
                    rule_category="Policy Master",
                    severity=CRITICAL,
                    source_file="quikmstr.csv",
                    description="MBILLFRM must be populated.",
                    reason=f"Policy '{pol}' has blank MBILLFRM. This field is required.",
                    field_name="MBILLFRM",
                    expected="populated",
                    actual="",
                    affected_keys=[pol],
                    affected_count=1,
                )
            )

        # POL-012 MBILLDAY
        bd_c = col(df, "MBILLDAY")
        if bd_c and iss_d:
            expected_day = str(iss_d.day)
            actual_day = s(row.get(bd_c))
            if actual_day and actual_day.lstrip("0") != expected_day and actual_day != expected_day:
                # allow 01 vs 1
                if to_float(actual_day) != float(iss_d.day):
                    findings.append(
                        make_finding(
                            rule_id="POL-012",
                            rule_category="Policy Master",
                            severity=ADVISORY,
                            source_file="quikmstr.csv",
                            description="MBILLDAY defaults to day number from MISSDT.",
                            reason=(
                                f"Policy '{pol}' MBILLDAY='{actual_day}', expected day "
                                f"from MISSDT which is '{expected_day}'."
                            ),
                            field_name="MBILLDAY",
                            expected=expected_day,
                            actual=actual_day,
                            affected_keys=[pol],
                            affected_count=1,
                        )
                    )

        # POL-013 PAC bank
        if bf in ("2", "2.0") or to_float(bf) == 2:
            bank_c = col(df, "MBANKNO")
            if bank_c and not s(row.get(bank_c)):
                findings.append(
                    make_finding(
                        rule_id="POL-013",
                        rule_category="Policy Master",
                        severity=HIGH,
                        source_file="quikmstr.csv",
                        description="PAC billing requires MBANKNO.",
                        reason=(
                            f"Policy '{pol}' has MBILLFRM=2 (PAC) but MBANKNO is blank. "
                            f"Bank number required for PAC billing."
                        ),
                        field_name="MBANKNO",
                        expected="populated",
                        actual="",
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )

        # POL-014 MMODE
        mode_c = col(df, "MMODE")
        if mode_c and not s(row.get(mode_c)):
            findings.append(
                make_finding(
                    rule_id="POL-014",
                    rule_category="Policy Master",
                    severity=CRITICAL,
                    source_file="quikmstr.csv",
                    description="MMODE must be populated.",
                    reason=f"Policy '{pol}' has no MMODE value.",
                    field_name="MMODE",
                    expected="populated",
                    actual="",
                    affected_keys=[pol],
                    affected_count=1,
                )
            )

        # POL-015 MISSUEST
        st_iss = col(df, "MISSUEST")
        if st_iss:
            stv = s(row.get(st_iss)).upper()
            if not stv or stv not in VALID_US_STATES:
                findings.append(
                    make_finding(
                        rule_id="POL-015",
                        rule_category="Policy Master",
                        severity=CRITICAL,
                        source_file="quikmstr.csv",
                        description="MISSUEST must be a valid state abbreviation.",
                        reason=(
                            f"Policy '{pol}' has MISSUEST='{stv}' which is not a valid state abbreviation."
                        ),
                        field_name="MISSUEST",
                        expected="valid US state",
                        actual=stv,
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )

        # POL-016 MGROUP
        grp_c = col(df, "MGROUP")
        if grp_c:
            grp = s(row.get(grp_c))
            if grp and groups and grp not in groups:
                findings.append(
                    make_finding(
                        rule_id="POL-016",
                        rule_category="Policy Master",
                        severity=HIGH,
                        source_file="quikmstr.csv",
                        description="Populated MGROUP must exist in QUIKLIST.",
                        reason=f"Policy '{pol}' has MGROUP='{grp}' which does not exist in QUIKLIST.",
                        field_name="MGROUP",
                        expected="group in QUIKLIST",
                        actual=grp,
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )

        # POL-017..021 client FK fields
        for rule_id, display_name, aliases, _ in client_fields:
            fcol = col(df, *aliases)
            if not fcol:
                continue
            cid = s(row.get(fcol))
            if cid and clnt is not None and cid not in valid_clients:
                findings.append(
                    make_finding(
                        rule_id=rule_id,
                        rule_category="Policy Master",
                        severity=CRITICAL,
                        source_file="quikmstr.csv",
                        description=f"If {display_name} is populated, it must exist in QUIKCLNT.",
                        reason=f"Policy '{pol}' {display_name}='{cid}' not found in QUIKCLNT.",
                        field_name=display_name,
                        expected="client in QUIKCLNT",
                        actual=cid,
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )

        # POL-022 / POL-023 MBENPID / MBENCID must be empty
        for fname, rule_id in (("MBENPID", "POL-022"), ("MBENCID", "POL-023")):
            fcol = col(df, fname)
            if fcol and s(row.get(fcol)):
                val = s(row.get(fcol))
                findings.append(
                    make_finding(
                        rule_id=rule_id,
                        rule_category="Policy Master",
                        severity=CRITICAL,
                        source_file="quikmstr.csv",
                        description=f"{fname} must be empty on every quikmstr row.",
                        reason=(
                            f"Policy '{pol}' has {fname}='{val}'. This field "
                            f"must always be empty on the policy master record."
                        ),
                        field_name=fname,
                        expected="",
                        actual=val,
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )

        # POL-024 MAPPDATE <= issue
        app_c = col(df, "MAPPDATE")
        if app_c and iss_d:
            app_raw = s(row.get(app_c))
            app_d = parse_date(app_raw)
            iss_raw = s(row.get(iss_c)) if iss_c else ""
            if app_d and app_d > iss_d:
                findings.append(
                    make_finding(
                        rule_id="POL-024",
                        rule_category="Policy Master",
                        severity=HIGH,
                        source_file="quikmstr.csv",
                        description="MAPPDATE must be <= MISSDT.",
                        reason=(
                            f"Policy '{pol}' MAPPDATE='{app_raw}' is after "
                            f"MISSDT='{iss_raw}'. Application date must be on or before "
                            f"issue date."
                        ),
                        field_name="MAPPDATE",
                        expected=f"<= {iss_raw}",
                        actual=app_raw,
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )

        # POL-025 MISSCNTRY default 0000
        cn_c = col(df, "MISSCNTRY")
        if cn_c:
            cn = s(row.get(cn_c))
            if cn and cn != "0000":
                findings.append(
                    make_finding(
                        rule_id="POL-025",
                        rule_category="Policy Master",
                        severity=ADVISORY,
                        source_file="quikmstr.csv",
                        description="MISSCNTRY defaults to 0000.",
                        reason=f"Policy '{pol}' MISSCNTRY='{cn}', expected '0000'.",
                        field_name="MISSCNTRY",
                        expected="0000",
                        actual=cn,
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )

        # POL-026 MISSCLASS default 00
        mc_c = col(df, "MISSCLASS")
        if mc_c:
            mc = s(row.get(mc_c))
            if mc and mc != "00":
                findings.append(
                    make_finding(
                        rule_id="POL-026",
                        rule_category="Policy Master",
                        severity=ADVISORY,
                        source_file="quikmstr.csv",
                        description="MISSCLASS defaults to 00.",
                        reason=f"Policy '{pol}' MISSCLASS='{mc}', expected '00'.",
                        field_name="MISSCLASS",
                        expected="00",
                        actual=mc,
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )

        # POL-027 MRESSTATE info flag (reviewer confirmation — not an error)
        res_c = col(df, "MRESSTATE")
        if res_c:
            res = s(row.get(res_c))
            if res:
                findings.append(
                    make_finding(
                        rule_id="POL-027",
                        rule_category="Policy Master",
                        severity=INFO,
                        source_file="quikmstr.csv",
                        description="MRESSTATE populated — confirm whether resident state should be set.",
                        reason=(
                            f"Policy '{pol}' has MRESSTATE='{res}'. Confirm "
                            f"whether resident state should be populated for this batch."
                        ),
                        field_name="MRESSTATE",
                        expected="(reviewer confirmation)",
                        actual=res,
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )

    return findings
