"""Issue #84 Track A — header MPAID/PDDATE backfill from claim-keyed payees."""

from __future__ import annotations

import pandas as pd

from qla_core.issue84_track_a_header_backfill import (
    backfill_quikclms_headers_from_payees,
)


def _clms(**overrides):
    row = {
        "MPOLICY": "010391359C",
        "MPHASE": "1",
        "CLAIMNUM": "010391359C00001",
        "CLAIMSTAT": "2",
        "MPAID": "0.00",
        "PDDATE": "",
    }
    row.update(overrides)
    return pd.DataFrame([row])


def _clmp(**overrides):
    row = {
        "MPOLICY": "010391359C",
        "MPHASE": "1",
        "MAMOUNT": "1260.06",
        "MPMTDATE": "20211119",
        "MCHKDATE": "20211119",
    }
    row.update(overrides)
    return pd.DataFrame([row])


def test_backfill_mpaid_and_pddate_from_payees():
    clms_after, audit = backfill_quikclms_headers_from_payees(_clms(), _clmp())
    assert len(audit) == 1
    assert clms_after.iloc[0]["MPAID"] == "1260.06"
    assert clms_after.iloc[0]["PDDATE"] == "20211119"
    assert clms_after.iloc[0]["CLAIMSTAT"] == "2"


def test_preserves_nonzero_mpaid():
    clms_after, audit = backfill_quikclms_headers_from_payees(
        _clms(MPAID="3213.59", PDDATE="20200101"),
        _clmp(),
    )
    assert audit.empty
    assert clms_after.iloc[0]["MPAID"] == "3213.59"


def test_claim_key_is_policy_plus_phase():
    clms = pd.DataFrame(
        [
            {"MPOLICY": "POL001A", "MPHASE": "1", "CLAIMNUM": "A1", "CLAIMSTAT": "2", "MPAID": "0", "PDDATE": ""},
            {"MPOLICY": "POL001A", "MPHASE": "2", "CLAIMNUM": "A2", "CLAIMSTAT": "99", "MPAID": "0", "PDDATE": ""},
        ]
    )
    clmp = pd.DataFrame(
        [
            {"MPOLICY": "POL001A", "MPHASE": "1", "MAMOUNT": "100.00", "MPMTDATE": "20200101"},
            {"MPOLICY": "POL001A", "MPHASE": "2", "MAMOUNT": "200.00", "MPMTDATE": "20200202"},
        ]
    )
    clms_after, audit = backfill_quikclms_headers_from_payees(clms, clmp)
    assert len(audit) == 2
    by_phase = {row["mphase"]: row for _, row in audit.iterrows()}
    assert clms_after.loc[clms_after["MPHASE"] == "1", "MPAID"].iloc[0] == "100.00"
    assert clms_after.loc[clms_after["MPHASE"] == "2", "MPAID"].iloc[0] == "200.00"
    assert by_phase["1"]["after_mpaid"] == "100.00"
    assert by_phase["2"]["after_mpaid"] == "200.00"
