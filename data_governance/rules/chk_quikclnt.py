"""Category 15 — Clients (quikclnt) checks."""

from __future__ import annotations

from data_governance.constants.valid_codes import VALID_SEX_CODES
from data_governance.governance_config import ADVISORY, CRITICAL, HIGH, AuditFinding, make_finding
from data_governance.rules._helpers import col, date_out_of_range, get_df, parse_date, s


def check_quikclnt(data: dict) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    df = get_df(data, "quikclnt", "quikclnt.csv")
    if df is None or df.empty:
        return findings

    id_c = col(df, "MCLIENTID")
    if not id_c:
        return findings

    counts: dict[str, int] = {}
    for _, row in df.iterrows():
        cid = s(row.get(id_c))
        if cid:
            counts[cid] = counts.get(cid, 0) + 1
    for cid, n in counts.items():
        if n > 1:
            findings.append(
                make_finding(
                    rule_id="CLNT-001",
                    rule_category="Client",
                    severity=CRITICAL,
                    source_file="quikclnt.csv",
                    description="No duplicate client IDs in quikclnt.",
                    reason=(
                        f"Client ID '{cid}' appears {n} times in quikclnt. "
                        f"Client IDs must be unique."
                    ),
                    field_name="MCLIENTID",
                    expected="unique",
                    actual=str(n),
                    affected_keys=[cid],
                    affected_count=n,
                )
            )

    type_c = col(df, "MTYPE")
    tax_c = col(df, "MTAXIDTYPE")
    lname_c = col(df, "MLNAME", "LASTNAME")
    fname_c = col(df, "MFNAME")
    addr_c = col(df, "MADDR1")
    city_c = col(df, "MCITY")
    state_c = col(df, "MSTATE")
    zip_c = col(df, "MZIP")
    dob_c = col(df, "MDOB")
    sex_c = col(df, "MSEX")
    lang_c = col(df, "MLANGUAGE")

    for _, row in df.iterrows():
        cid = s(row.get(id_c))

        if type_c and not s(row.get(type_c)):
            findings.append(
                make_finding(
                    rule_id="CLNT-002",
                    rule_category="Client",
                    severity=CRITICAL,
                    source_file="quikclnt.csv",
                    description="MTYPE must be populated.",
                    reason=f"Client '{cid}' has blank MTYPE. Default is 'I' for individual.",
                    field_name="MTYPE",
                    expected="I",
                    actual="",
                    affected_keys=[cid],
                    affected_count=1,
                )
            )

        if tax_c:
            tax = s(row.get(tax_c))
            if tax and tax != "S":
                findings.append(
                    make_finding(
                        rule_id="CLNT-003",
                        rule_category="Client",
                        severity=ADVISORY,
                        source_file="quikclnt.csv",
                        description="MTAXIDTYPE defaults to S.",
                        reason=f"Client '{cid}' has MTAXIDTYPE='{tax}', expected default 'S'.",
                        field_name="MTAXIDTYPE",
                        expected="S",
                        actual=tax,
                        affected_keys=[cid],
                        affected_count=1,
                    )
                )

        if lname_c and not s(row.get(lname_c)):
            findings.append(
                make_finding(
                    rule_id="CLNT-004",
                    rule_category="Client",
                    severity=CRITICAL,
                    source_file="quikclnt.csv",
                    description="LASTNAME must be populated on every client record.",
                    reason=f"Client '{cid}' has no LASTNAME. This field is required.",
                    field_name="MLNAME",
                    expected="populated",
                    actual="",
                    affected_keys=[cid],
                    affected_count=1,
                )
            )

        blanks = all(
            not s(row.get(c)) if c else True
            for c in (addr_c, lname_c, fname_c, city_c, state_c, zip_c)
        )
        if blanks:
            findings.append(
                make_finding(
                    rule_id="CLNT-005",
                    rule_category="Client",
                    severity=HIGH,
                    source_file="quikclnt.csv",
                    description="Client has no contact information.",
                    reason=(
                        f"Client '{cid}' has no address or name fields "
                        f"populated (MADDR1, MLNAME, MFNAME, MCITY, MSTATE, MZIP "
                        f"are all blank). Client has no contact information."
                    ),
                    field_name="address/name",
                    expected="at least one populated",
                    actual="all blank",
                    affected_keys=[cid],
                    affected_count=1,
                )
            )

        if dob_c:
            raw = s(row.get(dob_c))
            if raw:
                d = parse_date(raw)
                if d is None or date_out_of_range(d):
                    findings.append(
                        make_finding(
                            rule_id="CLNT-006",
                            rule_category="Client",
                            severity=HIGH,
                            source_file="quikclnt.csv",
                            description="MDOB must be a valid date within allowed range.",
                            reason=(
                                f"Client '{cid}' has MDOB='{raw}' which is "
                                f"not a valid date or is outside the allowed date range."
                            ),
                            field_name="MDOB",
                            expected="valid date in range",
                            actual=raw,
                            affected_keys=[cid],
                            affected_count=1,
                        )
                    )

        if sex_c:
            sex = s(row.get(sex_c)).upper()
            if sex and sex not in VALID_SEX_CODES:
                findings.append(
                    make_finding(
                        rule_id="CLNT-007",
                        rule_category="Client",
                        severity=HIGH,
                        source_file="quikclnt.csv",
                        description="MSEX must be M or F.",
                        reason=f"Client '{cid}' has MSEX='{sex}'. Must be 'M' or 'F'.",
                        field_name="MSEX",
                        expected="M or F",
                        actual=sex,
                        affected_keys=[cid],
                        affected_count=1,
                    )
                )

        if lang_c:
            lang = s(row.get(lang_c))
            if lang and lang != "E":
                findings.append(
                    make_finding(
                        rule_id="CLNT-008",
                        rule_category="Client",
                        severity=ADVISORY,
                        source_file="quikclnt.csv",
                        description="MLANGUAGE defaults to E.",
                        reason=f"Client '{cid}' has MLANGUAGE='{lang}', expected default 'E'.",
                        field_name="MLANGUAGE",
                        expected="E",
                        actual=lang,
                        affected_keys=[cid],
                        affected_count=1,
                    )
                )

    return findings
