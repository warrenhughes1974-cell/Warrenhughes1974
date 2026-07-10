"""Category 11 — Riders (quikridr) checks."""

from __future__ import annotations

from data_governance.governance_config import CRITICAL, HIGH, AuditFinding, make_finding
from data_governance.rules._helpers import col, get_df, parse_date, plan_codes, policy_set, s, to_float


def check_quikridr(data: dict) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    df = get_df(data, "quikridr", "quikridr.csv")
    if df is None or df.empty:
        return findings

    mstr = get_df(data, "quikmstr", "quikmstr.csv")
    valid_pols = policy_set(mstr) if mstr is not None else None
    plan = get_df(data, "quikplan", "quikplan.csv")
    valid_plans = plan_codes(plan) if plan is not None else None

    iss_map: dict[str, object] = {}
    if mstr is not None:
        pc = col(mstr, "MPOLICY")
        ic = col(mstr, "MISSDT")
        if pc and ic:
            for _, row in mstr.iterrows():
                p = s(row.get(pc))
                d = parse_date(row.get(ic))
                if p and d:
                    iss_map[p] = d

    pol_c = col(df, "MPOLICY")
    phase_c = col(df, "MPHASE")
    rid_c = col(df, "MRIDRID")
    plan_c = col(df, "MPLAN")
    dob_c = col(df, "MPHDOB")

    # DUP-002
    if pol_c and phase_c:
        seen: dict[tuple[str, str], int] = {}
        for _, row in df.iterrows():
            key = (s(row.get(pol_c)), s(row.get(phase_c)))
            if key[0]:
                seen[key] = seen.get(key, 0) + 1
        for (p, ph), n in seen.items():
            if n > 1:
                findings.append(
                    make_finding(
                        rule_id="DUP-002",
                        rule_category="Rider",
                        severity=CRITICAL,
                        source_file="quikridr.csv",
                        description="MPOLICY + MPHASE must be unique.",
                        reason=(
                            f"quikridr has {n} records for MPOLICY='{p}' "
                            f"MPHASE='{ph}'. This combination must be unique."
                        ),
                        field_name="MPOLICY+MPHASE",
                        expected="unique",
                        actual=str(n),
                        affected_keys=[f"{p}|{ph}"],
                        affected_count=n,
                    )
                )

    # DUP-003
    if rid_c:
        rid_counts: dict[str, int] = {}
        for _, row in df.iterrows():
            r = s(row.get(rid_c))
            if r:
                rid_counts[r] = rid_counts.get(r, 0) + 1
        for r, n in rid_counts.items():
            if n > 1:
                findings.append(
                    make_finding(
                        rule_id="DUP-003",
                        rule_category="Rider",
                        severity=CRITICAL,
                        source_file="quikridr.csv",
                        description="MRIDRID must be unique.",
                        reason=f"MRIDRID='{r}' appears {n} times in quikridr. Rider IDs must be unique.",
                        field_name="MRIDRID",
                        expected="unique",
                        actual=str(n),
                        affected_keys=[r],
                        affected_count=n,
                    )
                )

    phases_by_pol: dict[str, set[int]] = {}
    for _, row in df.iterrows():
        pol = s(row.get(pol_c)) if pol_c else ""
        ph = s(row.get(phase_c)) if phase_c else ""
        ph_val = int(to_float(ph, 0) or 0)
        if pol:
            phases_by_pol.setdefault(pol, set()).add(ph_val)

        # REF-001
        if pol and valid_pols is not None and pol not in valid_pols:
            findings.append(
                make_finding(
                    rule_id="REF-001",
                    rule_category="Rider",
                    severity=CRITICAL,
                    source_file="quikridr.csv",
                    description="Every MPOLICY in quikridr must exist in quikmstr.",
                    reason=(
                        f"Rider record for MPOLICY='{pol}' MPHASE='{ph}' "
                        f"has no matching policy in quikmstr. Orphan rider."
                    ),
                    field_name="MPOLICY",
                    expected="policy in quikmstr",
                    actual=pol,
                    affected_keys=[pol],
                    affected_count=1,
                )
            )

        # REQ-002
        if rid_c and not s(row.get(rid_c)):
            findings.append(
                make_finding(
                    rule_id="REQ-002",
                    rule_category="Rider",
                    severity=CRITICAL,
                    source_file="quikridr.csv",
                    description="MRIDRID must not be blank.",
                    reason=(
                        f"quikridr row MPOLICY='{pol}' MPHASE='{ph}' "
                        f"has blank MRIDRID. This field is required."
                    ),
                    field_name="MRIDRID",
                    expected="populated",
                    actual="",
                    affected_keys=[pol],
                    affected_count=1,
                )
            )

        # REQ-003
        if phase_c and (not ph or ph_val == 0):
            findings.append(
                make_finding(
                    rule_id="REQ-003",
                    rule_category="Rider",
                    severity=CRITICAL,
                    source_file="quikridr.csv",
                    description="MPHASE must not be blank or zero.",
                    reason=(
                        f"quikridr row MPOLICY='{pol}' has MPHASE='{ph}'. "
                        f"MPHASE must be populated and non-zero."
                    ),
                    field_name="MPHASE",
                    expected="> 0",
                    actual=ph,
                    affected_keys=[pol],
                    affected_count=1,
                )
            )

        # REF-011
        if plan_c and valid_plans is not None:
            mp = s(row.get(plan_c))
            if mp and mp not in valid_plans:
                findings.append(
                    make_finding(
                        rule_id="REF-011",
                        rule_category="Rider",
                        severity=HIGH,
                        source_file="quikridr.csv",
                        description="Rider MPLAN must exist in quikplan.",
                        reason=(
                            f"quikridr MPOLICY='{pol}' MPHASE='{ph}' has "
                            f"MPLAN='{mp}' which does not exist in quikplan."
                        ),
                        field_name="MPLAN",
                        expected="plan in quikplan",
                        actual=mp,
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )

        # DT-003
        if dob_c and pol in iss_map:
            dob_raw = s(row.get(dob_c))
            dob = parse_date(dob_raw)
            if dob and dob > iss_map[pol]:
                findings.append(
                    make_finding(
                        rule_id="DT-003",
                        rule_category="Rider",
                        severity=CRITICAL,
                        source_file="quikridr.csv",
                        description="Insured DOB cannot be after policy issue date.",
                        reason=(
                            f"quikridr MPOLICY='{pol}' MPHASE='{ph}' has "
                            f"MPHDOB='{dob_raw}' which is after MISSDT='{iss_map[pol]}'. Insured "
                            f"cannot be born after the policy was issued."
                        ),
                        field_name="MPHDOB",
                        expected=f"<= {iss_map[pol]}",
                        actual=dob_raw,
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )

    for pol, phases in phases_by_pol.items():
        has_base = 1 in phases
        has_supp = any(p > 1 for p in phases)
        if not has_base:
            findings.append(
                make_finding(
                    rule_id="RDR-002",
                    rule_category="Rider",
                    severity=HIGH,
                    source_file="quikridr.csv",
                    description="Every policy in quikridr must have MPHASE=1 base coverage.",
                    reason=(
                        f"Policy '{pol}' has rider records but none with "
                        f"MPHASE=1. Every policy must have a base coverage record."
                    ),
                    field_name="MPHASE",
                    expected="1",
                    actual=str(sorted(phases)),
                    affected_keys=[pol],
                    affected_count=1,
                )
            )
        if has_supp and not has_base:
            supp = sorted(p for p in phases if p > 1)
            findings.append(
                make_finding(
                    rule_id="RDR-003",
                    rule_category="Rider",
                    severity=HIGH,
                    source_file="quikridr.csv",
                    description="Supplemental riders require a base MPHASE=1 row.",
                    reason=(
                        f"Policy '{pol}' has supplemental rider MPHASE='{supp[0]}' "
                        f"but no base coverage rider (MPHASE=1) exists."
                    ),
                    field_name="MPHASE",
                    expected="base + supplemental",
                    actual=str(sorted(phases)),
                    affected_keys=[pol],
                    affected_count=1,
                )
            )

    return findings
