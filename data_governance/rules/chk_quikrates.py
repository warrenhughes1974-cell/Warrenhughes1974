"""Category 6 — Rate / mortality table checks."""

from __future__ import annotations

from datetime import date

from data_governance.constants.valid_states import VALID_ISSUE_STATES
from data_governance.governance_config import CRITICAL, HIGH, AuditFinding, make_finding
from data_governance.rules._helpers import (
    col,
    get_df,
    max_allowed_date,
    parse_date,
    plan_codes,
    s,
    unique_values,
)

RATE_TABLES = ("quikplcv", "quikpltv", "quikplgp", "quikpldb", "quikpldv")


def check_quikrates(data: dict) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    today = date.today()
    max_dt = max_allowed_date(today)

    qxs = get_df(data, "quikqxs", "quikqxs.csv")
    mort_ids: set[str] = set()
    if qxs is not None:
        for name in ("MORT", "MORTID", "TABLE", "QXSID", "MQXS"):
            c = col(qxs, name)
            if c:
                mort_ids = unique_values(qxs[c])
                break

    plan_df = get_df(data, "quikplan", "quikplan.csv")
    valid_plans = plan_codes(plan_df)

    plgd = get_df(data, "quikplgd", "quikplgd.csv")
    genders = unique_values(plgd[col(plgd, "GENDER", "MGENDER", "SEX")]) if plgd is not None and col(plgd, "GENDER", "MGENDER", "SEX") else set()

    pluw = get_df(data, "quikpluw", "quikpluw.csv")
    uw_vals = unique_values(pluw[col(pluw, "UWCLASS", "MUWCLASS")]) if pluw is not None and col(pluw, "UWCLASS", "MUWCLASS") else set()

    plvd = get_df(data, "quikplvd", "quikplvd.csv")
    bands = unique_values(plvd[col(plvd, "BAND", "MBAND")]) if plvd is not None and col(plvd, "BAND", "MBAND") else set()

    for tname in RATE_TABLES:
        tdf = get_df(data, tname, f"{tname}.csv")
        if tdf is None or tdf.empty:
            continue
        fname = f"{tname}.csv"
        pcol = col(tdf, "PLAN", "MPLAN")
        mort_c = col(tdf, "MORT")
        eti_c = col(tdf, "ETIMORT")
        gen_c = col(tdf, "GENDER", "SEX")
        uw_c = col(tdf, "UWCLASS")
        band_c = col(tdf, "BAND")
        st_c = col(tdf, "ISSUEST", "STATE")
        eff_c = col(tdf, "EFFDATE", "MEFFDATE")

        for idx, row in tdf.iterrows():
            pcode = s(row.get(pcol)) if pcol else ""

            # RATE-001
            if mort_c and mort_ids:
                mort = s(row.get(mort_c))
                if mort and mort not in mort_ids:
                    findings.append(
                        make_finding(
                            rule_id="RATE-001",
                            rule_category="Rates",
                            severity=CRITICAL,
                            source_file=fname,
                            description="MORT must exist in QUIKQXS.",
                            reason=(
                                f"Table '{tname.upper()}' plan '{pcode}' has MORT='{mort}' "
                                f"which does not exist in QUIKQXS mortality table."
                            ),
                            field_name="MORT",
                            expected="MORT in QUIKQXS",
                            actual=mort,
                            affected_keys=[pcode or mort],
                            affected_count=1,
                        )
                    )

            # RATE-002
            if eti_c and mort_ids:
                eti = s(row.get(eti_c))
                if eti and eti not in mort_ids:
                    findings.append(
                        make_finding(
                            rule_id="RATE-002",
                            rule_category="Rates",
                            severity=CRITICAL,
                            source_file=fname,
                            description="ETIMORT must exist in QUIKQXS.",
                            reason=(
                                f"Table '{tname.upper()}' plan '{pcode}' has ETIMORT='{eti}' "
                                f"which does not exist in QUIKQXS."
                            ),
                            field_name="ETIMORT",
                            expected="ETIMORT in QUIKQXS",
                            actual=eti,
                            affected_keys=[pcode or eti],
                            affected_count=1,
                        )
                    )

            # RATE-003
            if pcol and valid_plans and pcode and pcode not in valid_plans:
                findings.append(
                    make_finding(
                        rule_id="RATE-003",
                        rule_category="Rates",
                        severity=CRITICAL,
                        source_file=fname,
                        description="PLAN in rate tables must exist in QUIKPLAN.",
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

            # RATE-004
            if gen_c:
                g = s(row.get(gen_c))
                if g and g not in ("0",) and g not in genders:
                    # If plgd not loaded, only flag non-zero when we have gender set; if empty set skip FK
                    if genders or g not in ("0", "M", "F", "1", "2"):
                        if not genders or g not in genders:
                            findings.append(
                                make_finding(
                                    rule_id="RATE-004",
                                    rule_category="Rates",
                                    severity=CRITICAL,
                                    source_file=fname,
                                    description="GENDER must be 0 or exist in QUIKPLGD.",
                                    reason=(
                                        f"Table '{tname.upper()}' row has GENDER='{g}' which is "
                                        f"not 0 and not found in QUIKPLGD."
                                    ),
                                    field_name="GENDER",
                                    expected="0 or QUIKPLGD",
                                    actual=g,
                                    affected_keys=[pcode or g],
                                    affected_count=1,
                                )
                            )

            # RATE-005
            if uw_c:
                uw = s(row.get(uw_c))
                if uw and uw != "00" and (uw_vals and uw not in uw_vals):
                    findings.append(
                        make_finding(
                            rule_id="RATE-005",
                            rule_category="Rates",
                            severity=CRITICAL,
                            source_file=fname,
                            description="UWCLASS must be 00 or exist in QUIKPLUW.",
                            reason=(
                                f"Table '{tname.upper()}' row has UWCLASS='{uw}' which is "
                                f"not '00' and not found in QUIKPLUW."
                            ),
                            field_name="UWCLASS",
                            expected="00 or QUIKPLUW",
                            actual=uw,
                            affected_keys=[pcode or uw],
                            affected_count=1,
                        )
                    )

            # RATE-006
            if band_c:
                band = s(row.get(band_c))
                if band and band != "00" and (bands and band not in bands):
                    findings.append(
                        make_finding(
                            rule_id="RATE-006",
                            rule_category="Rates",
                            severity=CRITICAL,
                            source_file=fname,
                            description="BAND must be 00 or exist in QUIKPLVD.",
                            reason=(
                                f"Table '{tname.upper()}' row has BAND='{band}' which is "
                                f"not '00' and not found in QUIKPLVD."
                            ),
                            field_name="BAND",
                            expected="00 or QUIKPLVD",
                            actual=band,
                            affected_keys=[pcode or band],
                            affected_count=1,
                        )
                    )

            # RATE-007
            if st_c:
                st = s(row.get(st_c)).upper()
                if st and st not in VALID_ISSUE_STATES:
                    findings.append(
                        make_finding(
                            rule_id="RATE-007",
                            rule_category="Rates",
                            severity=CRITICAL,
                            source_file=fname,
                            description="ISSUEST must be 00 or a valid US state abbreviation.",
                            reason=(
                                f"Table '{tname.upper()}' row has ISSUEST='{st}' which is "
                                f"not '00' and not a valid state abbreviation."
                            ),
                            field_name="ISSUEST",
                            expected="00 or valid state",
                            actual=st,
                            affected_keys=[pcode or st],
                            affected_count=1,
                        )
                    )

            # RATE-008
            if eff_c:
                raw = s(row.get(eff_c))
                d = parse_date(raw)
                if raw and (d is None or d < date(1900, 1, 1) or d > max_dt):
                    findings.append(
                        make_finding(
                            rule_id="RATE-008",
                            rule_category="Rates",
                            severity=HIGH,
                            source_file=fname,
                            description="EFFDATE must be within 01/01/1900 to today+12 months.",
                            reason=(
                                f"Table '{tname.upper()}' row has EFFDATE='{raw}' which is "
                                f"outside the valid range of 01/01/1900 to {max_dt.isoformat()}."
                            ),
                            field_name="EFFDATE",
                            expected=f"1900-01-01 to {max_dt.isoformat()}",
                            actual=raw,
                            affected_keys=[pcode or raw],
                            affected_count=1,
                        )
                    )

    return findings
