"""Category 5 — QUIKPLAN plan table checks (largest rule set)."""

from __future__ import annotations

import re

from data_governance.constants.valid_codes import (
    RESERVED_PLAN_SUFFIXES,
    VALID_ANNUITY_BASIS,
)
from data_governance.governance_config import (
    ADVISORY,
    CRITICAL,
    HIGH,
    AuditFinding,
    make_finding,
)
from data_governance.rules._helpers import (
    col,
    company_codes,
    get_df,
    plan_codes,
    s,
    to_float,
    finding_per_key,
)

PLAN_CODE_RE = re.compile(r"^[A-Z0-9]{6}$")

RATE_KEY_TABLES = (
    "quikplcv", "quikpltv", "quikplgp", "quikpldb", "quikpldv",
    "quikgps", "quikdbs", "quikcvs", "quiktvs", "quiknps",
    "quikaint", "quikaing", "quikaexp", "quikainf", "quikuint",
)


def _plan_col(df):
    return col(df, "PLAN", "MPLAN", "PLANCODE")


def _notes_flag(ctx: dict, plan: str, flag: str) -> bool:
    notes = ctx.get("transformation_notes") or {}
    entry = notes.get(plan) or notes.get(plan.upper()) or {}
    if isinstance(entry, dict):
        return bool(entry.get(flag))
    if isinstance(entry, (list, set, frozenset)):
        return flag in entry or flag.upper() in {str(x).upper() for x in entry}
    flags = ctx.get(flag) or ctx.get(f"{flag}_plans") or []
    return plan in flags or plan.upper() in {str(x).upper() for x in flags}


def check_quikplan(data: dict) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    ctx = data.get("_context") or {}
    plan_df = get_df(data, "quikplan", "quikplan.csv")
    if plan_df is None or plan_df.empty:
        return findings

    pcol = _plan_col(plan_df)
    if not pcol:
        return findings

    comp_df = get_df(data, "quikcomp", "quikcomp.csv")
    valid_comp = company_codes(comp_df)
    quikcom = get_df(data, "quikcom", "quikcom.csv")
    comm_ids = plan_codes(quikcom) if quikcom is not None else set()
    # COMMID lookup — QUIKCOM may use COMMID / MCOMMID
    if quikcom is not None:
        for name in ("COMMID", "MCOMMID", "COMID"):
            c = col(quikcom, name)
            if c:
                from data_governance.rules._helpers import unique_values
                comm_ids = unique_values(quikcom[c])
                break

    valid_plans = {s(v) for v in plan_df[pcol] if s(v)}

    # Preload related table plan sets
    related_plans: dict[str, set[str]] = {}
    for tname in RATE_KEY_TABLES:
        tdf = get_df(data, tname, f"{tname}.csv")
        related_plans[tname] = plan_codes(tdf) if tdf is not None else set()

    for _, row in plan_df.iterrows():
        code = s(row.get(pcol))
        if not code:
            findings.append(
                make_finding(
                    rule_id="PLAN-001",
                    rule_category="Plan",
                    severity=CRITICAL,
                    source_file="quikplan.csv",
                    description="Plan code must be exactly 6 uppercase alphanumeric characters.",
                    reason="Plan code is blank. Plan codes must be exactly 6 uppercase alphanumeric characters with no spaces or special characters.",
                    field_name=pcol,
                    expected="^[A-Z0-9]{6}$",
                    actual="",
                    affected_keys=[""],
                    affected_count=1,
                )
            )
            continue

        # PLAN-001
        if not PLAN_CODE_RE.match(code):
            findings.append(
                make_finding(
                    rule_id="PLAN-001",
                    rule_category="Plan",
                    severity=CRITICAL,
                    source_file="quikplan.csv",
                    description="Plan code must be exactly 6 uppercase alphanumeric characters.",
                    reason=(
                        f"Plan code '{code}' is not valid. Plan codes must be exactly 6 "
                        f"uppercase alphanumeric characters with no spaces or special characters."
                    ),
                    field_name=pcol,
                    expected="^[A-Z0-9]{6}$",
                    actual=code,
                    affected_keys=[code],
                    affected_count=1,
                )
            )

        # PLAN-002
        for suffix in RESERVED_PLAN_SUFFIXES:
            if code.endswith(suffix):
                findings.append(
                    make_finding(
                        rule_id="PLAN-002",
                        rule_category="Plan",
                        severity=CRITICAL,
                        source_file="quikplan.csv",
                        description="Plan codes must not end with reserved PUA suffixes.",
                        reason=(
                            f"Plan code '{code}' ends with '{suffix}' which is reserved "
                            f"for PUA plan construction and cannot be used."
                        ),
                        field_name=pcol,
                        expected=f"not ending in {suffix}",
                        actual=code,
                        affected_keys=[code],
                        affected_count=1,
                    )
                )

        # PLAN-003 PAR
        par_c = col(plan_df, "PAR")
        if par_c:
            par = s(row.get(par_c))
            if par not in ("0", "1"):
                findings.append(
                    make_finding(
                        rule_id="PLAN-003",
                        rule_category="Plan",
                        severity=CRITICAL,
                        source_file="quikplan.csv",
                        description="PAR field must be 0 or 1.",
                        reason=f"Plan code '{code}' has PAR value '{par}'. PAR must be 0 or 1.",
                        field_name="PAR",
                        expected="0 or 1",
                        actual=par,
                        affected_keys=[code],
                        affected_count=1,
                    )
                )

        # PLAN-004 BASIS
        basis_c = col(plan_df, "BASIS")
        if basis_c:
            basis = s(row.get(basis_c))
            if code.startswith("A"):
                if basis not in VALID_ANNUITY_BASIS:
                    findings.append(
                        make_finding(
                            rule_id="PLAN-004",
                            rule_category="Plan",
                            severity=CRITICAL,
                            source_file="quikplan.csv",
                            description="Annuity plans require a valid BASIS code.",
                            reason=(
                                f"Plan code '{code}' begins with 'A' and has BASIS '{basis}'. "
                                f"Valid values are NONQ, QUAL, NQIA, QLIA, TXBL (case-sensitive)."
                            ),
                            field_name="BASIS",
                            expected="NONQ|QUAL|NQIA|QLIA|TXBL",
                            actual=basis,
                            affected_keys=[code],
                            affected_count=1,
                        )
                    )
            elif basis:
                findings.append(
                    make_finding(
                        rule_id="PLAN-004",
                        rule_category="Plan",
                        severity=CRITICAL,
                        source_file="quikplan.csv",
                        description="Non-annuity plans must have empty BASIS.",
                        reason=(
                            f"Plan code '{code}' does not begin with 'A' but has BASIS '{basis}'. "
                            f"BASIS must be empty for non-annuity plans."
                        ),
                        field_name="BASIS",
                        expected="",
                        actual=basis,
                        affected_keys=[code],
                        affected_count=1,
                    )
                )

        # PLAN-005 LOANINTX
        lix_c = col(plan_df, "LOANINTX")
        if lix_c:
            lix = s(row.get(lix_c))
            if lix not in ("A", "R"):
                findings.append(
                    make_finding(
                        rule_id="PLAN-005",
                        rule_category="Plan",
                        severity=HIGH,
                        source_file="quikplan.csv",
                        description="LOANINTX must be A or R (default A).",
                        reason=(
                            f"Plan code '{code}' has LOANINTX '{lix}'. "
                            f"Must be 'A' or 'R'. Default is 'A'."
                        ),
                        field_name="LOANINTX",
                        expected="A or R",
                        actual=lix or "(blank)",
                        affected_keys=[code],
                        affected_count=1,
                    )
                )

        # PLAN-006 MYGA DEPINT
        if _notes_flag(ctx, code, "MYGA"):
            dep_c = col(plan_df, "DEPINT")
            if dep_c:
                dep = to_float(row.get(dep_c), 0.0) or 0.0
                if dep <= 0:
                    findings.append(
                        make_finding(
                            rule_id="PLAN-006",
                            rule_category="Plan",
                            severity=ADVISORY,
                            source_file="quikplan.csv",
                            description="MYGA plans should have DEPINT > 0.",
                            reason=(
                                f"Plan code '{code}' is a MYGA plan but DEPINT is '{s(row.get(dep_c))}'. "
                                f"DEPINT should be greater than 0 for MYGA plans."
                            ),
                            field_name="DEPINT",
                            expected="> 0",
                            actual=s(row.get(dep_c)),
                            affected_keys=[code],
                            affected_count=1,
                        )
                    )

        # PLAN-007 LOAGE / HIAGE
        lo_c = col(plan_df, "LOAGE")
        hi_c = col(plan_df, "HIAGE")
        if lo_c:
            lo = to_float(row.get(lo_c))
            if lo is not None and lo != 0:
                findings.append(
                    make_finding(
                        rule_id="PLAN-007",
                        rule_category="Plan",
                        severity=CRITICAL,
                        source_file="quikplan.csv",
                        description="First LOAGE entry must be 0.",
                        reason=(
                            f"Plan code '{code}' LOAGE table — age 1 value is '{s(row.get(lo_c))}', expected 0."
                        ),
                        field_name="LOAGE",
                        expected="0",
                        actual=s(row.get(lo_c)),
                        affected_keys=[code],
                        affected_count=1,
                    )
                )
            if lo_c and hi_c:
                hi = to_float(row.get(hi_c))
                if lo is not None and hi is not None and lo >= hi:
                    findings.append(
                        make_finding(
                            rule_id="PLAN-007",
                            rule_category="Plan",
                            severity=CRITICAL,
                            source_file="quikplan.csv",
                            description="LOAGE must be less than HIAGE.",
                            reason=(
                                f"Plan code '{code}' has LOAGE '{s(row.get(lo_c))}' >= HIAGE "
                                f"'{s(row.get(hi_c))}' which is invalid."
                            ),
                            field_name="LOAGE",
                            expected="LOAGE < HIAGE",
                            actual=f"{s(row.get(lo_c))} >= {s(row.get(hi_c))}",
                            affected_keys=[code],
                            affected_count=1,
                        )
                    )

        # PLAN-008 RENEW
        renew_c = col(plan_df, "RENEW")
        if renew_c:
            renew = s(row.get(renew_c)) or "N"
            if not code.startswith("5") and renew != "N":
                findings.append(
                    make_finding(
                        rule_id="PLAN-008",
                        rule_category="Plan",
                        severity=HIGH,
                        source_file="quikplan.csv",
                        description="Only plans beginning with 5 may have RENEW=Y.",
                        reason=(
                            f"Plan code '{code}' has RENEW='{renew}'. "
                            f"Only plans beginning with '5' may have RENEW='Y'."
                        ),
                        field_name="RENEW",
                        expected="N",
                        actual=renew,
                        affected_keys=[code],
                        affected_count=1,
                    )
                )
            elif code.startswith("5") and renew not in ("N", "Y"):
                findings.append(
                    make_finding(
                        rule_id="PLAN-008",
                        rule_category="Plan",
                        severity=HIGH,
                        source_file="quikplan.csv",
                        description="Plans beginning with 5 may have RENEW N or Y.",
                        reason=(
                            f"Plan code '{code}' has RENEW='{renew}'. "
                            f"Only plans beginning with '5' may have RENEW='Y'."
                        ),
                        field_name="RENEW",
                        expected="N or Y",
                        actual=renew,
                        affected_keys=[code],
                        affected_count=1,
                    )
                )

        # PLAN-009 payment / insurance periods
        payrs_c = col(plan_df, "PAYYRS", "PAYRS")
        payage_c = col(plan_df, "PAYAGE")
        insyrs_c = col(plan_df, "INSYRS")
        insage_c = col(plan_df, "INSAGE")
        if not code.startswith("5"):
            payrs = to_float(row.get(payrs_c), 0.0) if payrs_c else 0.0
            payage = to_float(row.get(payage_c), 0.0) if payage_c else 0.0
            insyrs = to_float(row.get(insyrs_c), 0.0) if insyrs_c else 0.0
            insage = to_float(row.get(insage_c), 0.0) if insage_c else 0.0
            if (payrs or 0) == 0 and (payage or 0) == 0:
                findings.append(
                    make_finding(
                        rule_id="PLAN-009",
                        rule_category="Plan",
                        severity=CRITICAL,
                        source_file="quikplan.csv",
                        description="At least one of PAYRS/PAYAGE must be > 0.",
                        reason=f"Plan '{code}': both PAYRS and PAYAGE are 0. At least one must be greater than 0.",
                        field_name="PAYYRS/PAYAGE",
                        expected="> 0",
                        actual="0/0",
                        affected_keys=[code],
                        affected_count=1,
                    )
                )
            if (insyrs or 0) == 0 and (insage or 0) == 0:
                findings.append(
                    make_finding(
                        rule_id="PLAN-009",
                        rule_category="Plan",
                        severity=CRITICAL,
                        source_file="quikplan.csv",
                        description="At least one of INSYRS/INSAGE must be > 0.",
                        reason=f"Plan '{code}': both INSYRS and INSAGE are 0. At least one must be greater than 0.",
                        field_name="INSYRS/INSAGE",
                        expected="> 0",
                        actual="0/0",
                        affected_keys=[code],
                        affected_count=1,
                    )
                )
        if payage_c:
            payage = to_float(row.get(payage_c))
            if payage is not None and payage > 125:
                findings.append(
                    make_finding(
                        rule_id="PLAN-009",
                        rule_category="Plan",
                        severity=CRITICAL,
                        source_file="quikplan.csv",
                        description="PAYAGE must not exceed 125.",
                        reason=f"Plan '{code}': PAYAGE is {payage}, exceeds maximum of 125.",
                        field_name="PAYAGE",
                        expected="<= 125",
                        actual=str(payage),
                        affected_keys=[code],
                        affected_count=1,
                    )
                )
        if insage_c:
            insage = to_float(row.get(insage_c))
            if insage is not None and insage > 125:
                findings.append(
                    make_finding(
                        rule_id="PLAN-009",
                        rule_category="Plan",
                        severity=CRITICAL,
                        source_file="quikplan.csv",
                        description="INSAGE must not exceed 125.",
                        reason=f"Plan '{code}': INSAGE is {insage}, exceeds maximum of 125.",
                        field_name="INSAGE",
                        expected="<= 125",
                        actual=str(insage),
                        affected_keys=[code],
                        affected_count=1,
                    )
                )

        # PLAN-010 single premium
        if _notes_flag(ctx, code, "SINGLE_PREMIUM") or _notes_flag(ctx, code, "single_premium"):
            checks = [
                ("PAYYRS", col(plan_df, "PAYYRS", "PAYRS"), "1"),
                ("PAYAGE", col(plan_df, "PAYAGE"), "0"),
                ("SEMI", col(plan_df, "SEMI"), "0"),
                ("QTRL", col(plan_df, "QTRL"), "0"),
                ("MTHD", col(plan_df, "MTHD"), "0"),
                ("MTHB", col(plan_df, "MTHB"), "0"),
            ]
            for fname, fcol, expected in checks:
                if not fcol:
                    continue
                actual = s(row.get(fcol))
                if actual != expected:
                    findings.append(
                        make_finding(
                            rule_id="PLAN-010",
                            rule_category="Plan",
                            severity=ADVISORY,
                            source_file="quikplan.csv",
                            description="Single-premium plans have fixed payment field defaults.",
                            reason=(
                                f"Plan '{code}' is single-premium but {fname}={actual}, expected {expected}."
                            ),
                            field_name=fname,
                            expected=expected,
                            actual=actual,
                            affected_keys=[code],
                            affected_count=1,
                        )
                    )

        # PLAN-011 INITVAL
        init_c = col(plan_df, "INITVAL")
        if init_c and not code.startswith("A"):
            init = to_float(row.get(init_c))
            if init is not None and init != 1000:
                findings.append(
                    make_finding(
                        rule_id="PLAN-011",
                        rule_category="Plan",
                        severity=HIGH,
                        source_file="quikplan.csv",
                        description="INITVAL defaults to 1000 for non-annuity plans.",
                        reason=(
                            f"Plan '{code}' has INITVAL={s(row.get(init_c))}. "
                            f"Expected default of 1000 for non-annuity plans."
                        ),
                        field_name="INITVAL",
                        expected="1000",
                        actual=s(row.get(init_c)),
                        affected_keys=[code],
                        affected_count=1,
                    )
                )

        # PLAN-012 COMMID
        comm_c = col(plan_df, "COMMID")
        if comm_c:
            commid = s(row.get(comm_c))
            if commid and quikcom is not None and commid not in comm_ids:
                findings.append(
                    make_finding(
                        rule_id="PLAN-012",
                        rule_category="Plan",
                        severity=ADVISORY,
                        source_file="quikplan.csv",
                        description="Populated COMMID must exist in QUIKCOM.",
                        reason=(
                            f"Plan '{code}' has COMMID='{commid}' which does not exist in QUIKCOM."
                        ),
                        field_name="COMMID",
                        expected="COMMID in QUIKCOM",
                        actual=commid,
                        affected_keys=[code],
                        affected_count=1,
                    )
                )

        # PLAN-013 MAXUNITS >= MINUNIT
        max_c = col(plan_df, "MAXUNIT", "MAXUNITS")
        min_c = col(plan_df, "MINUNIT", "MINUNITS")
        if max_c and min_c:
            mx = to_float(row.get(max_c))
            mn = to_float(row.get(min_c))
            if mx is not None and mn is not None and mx < mn:
                findings.append(
                    make_finding(
                        rule_id="PLAN-013",
                        rule_category="Plan",
                        severity=CRITICAL,
                        source_file="quikplan.csv",
                        description="MAXUNITS must be >= MINUNIT.",
                        reason=(
                            f"Plan '{code}' has MAXUNITS={s(row.get(max_c))} which is less than "
                            f"MINUNIT={s(row.get(min_c))}."
                        ),
                        field_name="MAXUNIT",
                        expected=f">= {s(row.get(min_c))}",
                        actual=s(row.get(max_c)),
                        affected_keys=[code],
                        affected_count=1,
                    )
                )

        # PLAN-014 rounding rule
        rr_c = col(plan_df, "RRULE", "ROUNDING")
        if rr_c and not s(row.get(rr_c)):
            findings.append(
                make_finding(
                    rule_id="PLAN-014",
                    rule_category="Plan",
                    severity=ADVISORY,
                    source_file="quikplan.csv",
                    description="Rounding rule should default to A.",
                    reason=f"Plan '{code}' has no rounding rule. Default is 'A'.",
                    field_name=rr_c,
                    expected="A",
                    actual="",
                    affected_keys=[code],
                    affected_count=1,
                )
            )

        # PLAN-015 AUTONFO
        auto_c = col(plan_df, "AUTONFO")
        if auto_c:
            auto = s(row.get(auto_c))
            if auto and auto not in ("0", "0.0"):
                # advisory if not default 0
                if to_float(auto, 0) != 0:
                    findings.append(
                        make_finding(
                            rule_id="PLAN-015",
                            rule_category="Plan",
                            severity=ADVISORY,
                            source_file="quikplan.csv",
                            description="AUTONFO should default to 0.",
                            reason=f"Plan '{code}' has AUTONFO={auto}. Default is 0.",
                            field_name="AUTONFO",
                            expected="0",
                            actual=auto,
                            affected_keys=[code],
                            affected_count=1,
                        )
                    )

        # PLAN-016 DEFICIENCY
        def_c = col(plan_df, "DEFICIENCY")
        if def_c:
            defv = s(row.get(def_c))
            first = code[0] if code else ""
            if defv != "N" and (first >= "A" or first >= "9"):
                findings.append(
                    make_finding(
                        rule_id="PLAN-016",
                        rule_category="Plan",
                        severity=CRITICAL,
                        source_file="quikplan.csv",
                        description="DEFICIENCY field must always be N.",
                        reason=f"Plan '{code}' has DEFICIENCY='{defv}'. This field must always be 'N'.",
                        field_name="DEFICIENCY",
                        expected="N",
                        actual=defv,
                        affected_keys=[code],
                        affected_count=1,
                    )
                )
            elif defv and defv != "N":
                findings.append(
                    make_finding(
                        rule_id="PLAN-016",
                        rule_category="Plan",
                        severity=CRITICAL,
                        source_file="quikplan.csv",
                        description="DEFICIENCY field must always be N.",
                        reason=f"Plan '{code}' has DEFICIENCY='{defv}'. This field must always be 'N'.",
                        field_name="DEFICIENCY",
                        expected="N",
                        actual=defv,
                        affected_keys=[code],
                        affected_count=1,
                    )
                )

        # PLAN-017 BACTIVE / PLANVALOPT
        ba_c = col(plan_df, "BACTIVE")
        pvo_c = col(plan_df, "PLANVALOPT")
        if ba_c:
            ba = s(row.get(ba_c)).upper()
            if ba == "F" and pvo_c:
                pvo = s(row.get(pvo_c)).upper()
                if pvo not in ("F", "FALSE", "0", "N", ""):
                    findings.append(
                        make_finding(
                            rule_id="PLAN-017",
                            rule_category="Plan",
                            severity=HIGH,
                            source_file="quikplan.csv",
                            description="Inactive plans must have PLANVALOPT false.",
                            reason=(
                                f"Plan '{code}' has BACTIVE=F but PLANVALOPT='{s(row.get(pvo_c))}'. "
                                f"When plan is inactive, PLANVALOPT must also be false."
                            ),
                            field_name="PLANVALOPT",
                            expected="F/false",
                            actual=s(row.get(pvo_c)),
                            affected_keys=[code],
                            affected_count=1,
                        )
                    )

        # PLAN-018 MLAPSE
        ml_c = col(plan_df, "MLAPSE")
        if ml_c and not s(row.get(ml_c)):
            findings.append(
                make_finding(
                    rule_id="PLAN-018",
                    rule_category="Plan",
                    severity=ADVISORY,
                    source_file="quikplan.csv",
                    description="MLAPSE defaults to 0.",
                    reason=f"Plan '{code}' has no MLAPSE value. Default is 0.",
                    field_name="MLAPSE",
                    expected="0",
                    actual="",
                    affected_keys=[code],
                    affected_count=1,
                )
            )

        # PLAN-019 MNAICLOB
        naic_c = col(plan_df, "MNAICLOB")
        if naic_c and not s(row.get(naic_c)):
            findings.append(
                make_finding(
                    rule_id="PLAN-019",
                    rule_category="Plan",
                    severity=ADVISORY,
                    source_file="quikplan.csv",
                    description="MNAICLOB defaults to N.",
                    reason=f"Plan '{code}' has no MNAICLOB value. Default is 'N'.",
                    field_name="MNAICLOB",
                    expected="N",
                    actual="",
                    affected_keys=[code],
                    affected_count=1,
                )
            )

        # PLAN-020 VARGP
        vargp_c = col(plan_df, "VARGP")
        if vargp_c:
            vargp = to_float(row.get(vargp_c))
            if vargp is not None and vargp != 4:
                for tname in ("quikgps", "quikplgp"):
                    if code not in related_plans.get(tname, set()):
                        findings.append(
                            make_finding(
                                rule_id="PLAN-020",
                                rule_category="Plan",
                                severity=HIGH,
                                source_file="quikplan.csv",
                                description="VARGP != 4 requires GPS/PLGP records.",
                                reason=(
                                    f"Plan '{code}' has VARGP={s(row.get(vargp_c))} (not 4) but no "
                                    f"matching record found in {tname.upper()}."
                                ),
                                field_name="VARGP",
                                expected=f"record in {tname.upper()}",
                                actual="missing",
                                affected_keys=[code],
                                affected_count=1,
                            )
                        )

        # PLAN-021 VARDB
        vardb_c = col(plan_df, "VARDB")
        if vardb_c:
            vardb = to_float(row.get(vardb_c))
            if vardb is not None and vardb != 4:
                for tname in ("quikdbs", "quikpldb"):
                    if code not in related_plans.get(tname, set()):
                        findings.append(
                            make_finding(
                                rule_id="PLAN-021",
                                rule_category="Plan",
                                severity=HIGH,
                                source_file="quikplan.csv",
                                description="VARDB != 4 requires DBS/PLDB records.",
                                reason=(
                                    f"Plan '{code}' has VARDB={s(row.get(vardb_c))} (not 4) but no "
                                    f"matching record found in {tname.upper()}."
                                ),
                                field_name="VARDB",
                                expected=f"record in {tname.upper()}",
                                actual="missing",
                                affected_keys=[code],
                                affected_count=1,
                            )
                        )

        # PLAN-022 life plan rate tables
        if code and code[0] < "9":
            life_tables = ("quikplcv", "quikpltv", "quikcvs", "quiktvs", "quiknps")
            missing = [t.upper() for t in life_tables if code not in related_plans.get(t, set())]
            if len(missing) == len(life_tables):
                findings.append(
                    make_finding(
                        rule_id="PLAN-022",
                        rule_category="Plan",
                        severity=ADVISORY,
                        source_file="quikplan.csv",
                        description="Life plans typically have CV/TV/NPS rate records.",
                        reason=(
                            f"Plan '{code}' appears to be a life plan but has no records in "
                            f"{missing}. This may be intentional but should be confirmed."
                        ),
                        field_name="PLAN",
                        expected="rate table records",
                        actual="none",
                        affected_keys=[code],
                        affected_count=1,
                    )
                )

        # PLAN-023 annuity tables
        if code.startswith("A"):
            ann_tables = ("quikaint", "quikaing", "quikaexp", "quikainf")
            missing = [t.upper() for t in ann_tables if code not in related_plans.get(t, set())]
            # Acceptable if only QUIKAING or only QUIKAINF exists — still flag missing as advisory
            if missing:
                findings.append(
                    make_finding(
                        rule_id="PLAN-023",
                        rule_category="Plan",
                        severity=ADVISORY,
                        source_file="quikplan.csv",
                        description="Annuity plans should have interest/expense table records.",
                        reason=f"Annuity plan '{code}' is missing records in: {missing}.",
                        field_name="PLAN",
                        expected="annuity table records",
                        actual=str(missing),
                        affected_keys=[code],
                        affected_count=1,
                    )
                )

        # PLAN-024 UL -> QUIKUINT
        if _notes_flag(ctx, code, "UL") or _notes_flag(ctx, code, "ul"):
            if code not in related_plans.get("quikuint", set()):
                findings.append(
                    make_finding(
                        rule_id="PLAN-024",
                        rule_category="Plan",
                        severity=CRITICAL,
                        source_file="quikplan.csv",
                        description="UL plans must have a QUIKUINT record.",
                        reason=f"Plan '{code}' is a UL plan but no record found in QUIKUINT.",
                        field_name="PLAN",
                        expected="QUIKUINT record",
                        actual="missing",
                        affected_keys=[code],
                        affected_count=1,
                    )
                )

        # PLAN-027 PLANTYPE MEDS
        pt_c = col(plan_df, "PLANTYPE")
        hcomm_c = col(plan_df, "HCOMMIP")
        hrig_c = col(plan_df, "HRIGPKEY")
        if pt_c:
            ptype = s(row.get(pt_c)).upper()
            if ptype == "MEDS":
                for fname, fcol, expected in (("HCOMMIP", hcomm_c, "Y"), ("HRIGPKEY", hrig_c, "Y")):
                    if not fcol:
                        continue
                    actual = s(row.get(fcol)).upper()
                    if actual != expected:
                        findings.append(
                            make_finding(
                                rule_id="PLAN-027",
                                rule_category="Plan",
                                severity=CRITICAL,
                                source_file="quikplan.csv",
                                description="MEDS plans require HCOMMIP and HRIGPKEY = Y.",
                                reason=(
                                    f"Plan '{code}' has PLANTYPE=MEDS but {fname}='{s(row.get(fcol))}'. "
                                    f"Expected 'Y' for MEDS plans."
                                ),
                                field_name=fname,
                                expected=expected,
                                actual=s(row.get(fcol)),
                                affected_keys=[code],
                                affected_count=1,
                            )
                        )
            else:
                for fname, fcol, expected in (("HCOMMIP", hcomm_c, "F"), ("HRIGPKEY", hrig_c, "F")):
                    if not fcol:
                        continue
                    actual = s(row.get(fcol)).upper()
                    if actual and actual != expected:
                        findings.append(
                            make_finding(
                                rule_id="PLAN-027",
                                rule_category="Plan",
                                severity=CRITICAL,
                                source_file="quikplan.csv",
                                description="Non-MEDS plans require HCOMMIP and HRIGPKEY = F.",
                                reason=(
                                    f"Plan '{code}' has PLANTYPE='{ptype}' but {fname}='{s(row.get(fcol))}'. "
                                    f"Expected 'F' for non-MEDS plans."
                                ),
                                field_name=fname,
                                expected=expected,
                                actual=s(row.get(fcol)),
                                affected_keys=[code],
                                affected_count=1,
                            )
                        )

    # PLAN-025 company codes in plan-related tables
    if valid_comp:
        for tname in ("quikplan",) + RATE_KEY_TABLES:
            tdf = get_df(data, tname, f"{tname}.csv")
            if tdf is None or tdf.empty:
                continue
            ccol = col(tdf, "MCOMP", "COMP", "COMPANY", "COMPCODE")
            planc = _plan_col(tdf) or pcol
            if not ccol:
                continue
            for _, row in tdf.iterrows():
                comp = s(row.get(ccol))
                pcode = s(row.get(planc)) if planc in tdf.columns else ""
                if comp and comp not in valid_comp:
                    findings.append(
                        make_finding(
                            rule_id="PLAN-025",
                            rule_category="Plan",
                            severity=CRITICAL,
                            source_file=f"{tname}.csv",
                            description="Company codes in plan-related tables must exist in QUIKCOMP.",
                            reason=(
                                f"Table '{tname.upper()}' plan '{pcode}' has company code "
                                f"'{comp}' not found in QUIKCOMP."
                            ),
                            field_name=ccol,
                            expected="code in QUIKCOMP",
                            actual=comp,
                            affected_keys=[pcode or comp],
                            affected_count=1,
                        )
                    )

    # PLAN-026 rate/key tables reference QUIKPLAN
    for tname in RATE_KEY_TABLES:
        tdf = get_df(data, tname, f"{tname}.csv")
        if tdf is None or tdf.empty:
            continue
        for pcode in plan_codes(tdf):
            if pcode and pcode not in valid_plans:
                findings.append(
                    make_finding(
                        rule_id="PLAN-026",
                        rule_category="Plan",
                        severity=CRITICAL,
                        source_file=f"{tname}.csv",
                        description="Rate/key tables must reference plans in QUIKPLAN.",
                        reason=(
                            f"Rate table '{tname.upper()}' references plan code '{pcode}' "
                            f"which does not exist in QUIKPLAN."
                        ),
                        field_name="PLAN",
                        expected="plan in QUIKPLAN",
                        actual=pcode,
                        affected_keys=[pcode],
                        affected_count=1,
                    )
                )

    return findings
