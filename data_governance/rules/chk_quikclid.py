"""Category 16 — Client-policy links (quikclid) checks."""

from __future__ import annotations

from data_governance.constants.valid_codes import RELATION_CODES_PHASE_ZERO
from data_governance.governance_config import CRITICAL, AuditFinding, make_finding
from data_governance.rules._helpers import client_ids, col, get_df, policy_set, s, to_float


def check_quikclid(data: dict) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    df = get_df(data, "quikclid", "quikclid.csv")
    if df is None or df.empty:
        return findings

    clnt = get_df(data, "quikclnt", "quikclnt.csv")
    mstr = get_df(data, "quikmstr", "quikmstr.csv")
    ridr = get_df(data, "quikridr", "quikridr.csv")

    valid_clients = client_ids(clnt) if clnt is not None else None
    valid_pols = policy_set(mstr) if mstr is not None else None

    # (policy, phase) -> MRIDRID
    rider_mrid: dict[tuple[str, str], str] = {}
    rider_keys: set[tuple[str, str]] = set()
    if ridr is not None:
        pc = col(ridr, "MPOLICY")
        phc = col(ridr, "MPHASE")
        ridc = col(ridr, "MRIDRID")
        if pc and phc:
            for _, row in ridr.iterrows():
                p = s(row.get(pc))
                ph = s(row.get(phc))
                if p:
                    rider_keys.add((p, ph))
                    if ridc:
                        rider_mrid[(p, ph)] = s(row.get(ridc))
                        # also store int-normalized phase key
                        ph_n = str(int(to_float(ph, 0) or 0))
                        rider_keys.add((p, ph_n))
                        rider_mrid[(p, ph_n)] = s(row.get(ridc))

    id_c = col(df, "MCLIENTID")
    pol_c = col(df, "MPOLICY")
    phase_c = col(df, "MPHASE")
    rel_c = col(df, "MRELATION")

    for _, row in df.iterrows():
        cid = s(row.get(id_c)) if id_c else ""
        pol = s(row.get(pol_c)) if pol_c else ""
        phase = s(row.get(phase_c)) if phase_c else "0"
        rel = s(row.get(rel_c)).upper() if rel_c else ""
        ph_val = to_float(phase, 0) or 0
        ph_norm = str(int(ph_val))

        if cid and valid_clients is not None and cid not in valid_clients:
            findings.append(
                make_finding(
                    rule_id="CLID-001",
                    rule_category="Client Link",
                    severity=CRITICAL,
                    source_file="quikclid.csv",
                    description="MCLIENTID in quikclid must exist in quikclnt.",
                    reason=(
                        f"quikclid record links MCLIENTID='{cid}' which "
                        f"does not exist in quikclnt."
                    ),
                    field_name="MCLIENTID",
                    expected="client in QUIKCLNT",
                    actual=cid,
                    affected_keys=[cid],
                    affected_count=1,
                )
            )

        if pol and valid_pols is not None and pol not in valid_pols:
            findings.append(
                make_finding(
                    rule_id="CLID-002",
                    rule_category="Client Link",
                    severity=CRITICAL,
                    source_file="quikclid.csv",
                    description="MPOLICY in quikclid must exist in quikmstr.",
                    reason=(
                        f"quikclid record links MPOLICY='{pol}' which "
                        f"does not exist in quikmstr."
                    ),
                    field_name="MPOLICY",
                    expected="policy in quikmstr",
                    actual=pol,
                    affected_keys=[pol],
                    affected_count=1,
                )
            )

        if ph_val != 0 and pol and ridr is not None:
            if (pol, phase) not in rider_keys and (pol, ph_norm) not in rider_keys:
                findings.append(
                    make_finding(
                        rule_id="CLID-003",
                        rule_category="Client Link",
                        severity=CRITICAL,
                        source_file="quikclid.csv",
                        description="Non-zero MPHASE must exist in quikridr.",
                        reason=(
                            f"quikclid record has MPOLICY='{pol}' MPHASE='{phase}' "
                            f"(non-zero) but this combination does not exist in quikridr."
                        ),
                        field_name="MPHASE",
                        expected="phase in quikridr",
                        actual=phase,
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )

        if rel in RELATION_CODES_PHASE_ZERO and ph_val != 0:
            findings.append(
                make_finding(
                    rule_id="CLID-004",
                    rule_category="Client Link",
                    severity=CRITICAL,
                    source_file="quikclid.csv",
                    description="OWNR/OWNC/PAYR/PRIM/ASGN/BENP/BENC require MPHASE=0.",
                    reason=(
                        f"quikclid MCLIENTID='{cid}' MPOLICY='{pol}' has "
                        f"MRELATION='{rel}' with MPHASE='{phase}'. Relation code "
                        f"'{rel}' requires MPHASE=0."
                    ),
                    field_name="MPHASE",
                    expected="0",
                    actual=phase,
                    affected_keys=[pol],
                    affected_count=1,
                )
            )

        if rel == "INSD" and cid and pol and ridr is not None:
            rid = rider_mrid.get((pol, phase)) or rider_mrid.get((pol, ph_norm), "")
            if rid and cid != rid:
                findings.append(
                    make_finding(
                        rule_id="CLID-005",
                        rule_category="Client Link",
                        severity=CRITICAL,
                        source_file="quikclid.csv",
                        description="INSD MCLIENTID must match quikridr MRIDRID for policy+phase.",
                        reason=(
                            f"quikclid MCLIENTID='{cid}' MPOLICY='{pol}' "
                            f"MPHASE='{phase}' has MRELATION=INSD but does not match "
                            f"the MRIDRID on the corresponding quikridr record "
                            f"(quikridr MRIDRID='{rid}')."
                        ),
                        field_name="MCLIENTID",
                        expected=rid,
                        actual=cid,
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )

        # CLID-006 — any non-INSD relation must have MPHASE=0
        if rel and rel != "INSD" and ph_val != 0:
            # Avoid duplicate with CLID-004 for the phase-zero relation set
            if rel not in RELATION_CODES_PHASE_ZERO:
                findings.append(
                    make_finding(
                        rule_id="CLID-006",
                        rule_category="Client Link",
                        severity=CRITICAL,
                        source_file="quikclid.csv",
                        description="Non-INSD relations must always use MPHASE=0.",
                        reason=(
                            f"quikclid MCLIENTID='{cid}' MPOLICY='{pol}' has "
                            f"MRELATION='{rel}' (not INSD) with MPHASE='{phase}'. "
                            f"Non-insured relation codes must always use MPHASE=0."
                        ),
                        field_name="MPHASE",
                        expected="0",
                        actual=phase,
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )
            else:
                # Also emit CLID-006 for the named phase-zero codes (spec requires both)
                findings.append(
                    make_finding(
                        rule_id="CLID-006",
                        rule_category="Client Link",
                        severity=CRITICAL,
                        source_file="quikclid.csv",
                        description="Non-INSD relations must always use MPHASE=0.",
                        reason=(
                            f"quikclid MCLIENTID='{cid}' MPOLICY='{pol}' has "
                            f"MRELATION='{rel}' (not INSD) with MPHASE='{phase}'. "
                            f"Non-insured relation codes must always use MPHASE=0."
                        ),
                        field_name="MPHASE",
                        expected="0",
                        actual=phase,
                        affected_keys=[pol],
                        affected_count=1,
                    )
                )

    return findings
