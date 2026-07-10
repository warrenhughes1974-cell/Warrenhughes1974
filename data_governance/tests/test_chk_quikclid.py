"""Tests for chk_quikclid."""

import pandas as pd

from data_governance.rules.chk_quikclid import check_quikclid


def test_clid_001_client_not_in_quikclnt():
    data = {
        "quikclnt.csv": pd.DataFrame([{"MCLIENTID": "C1"}]),
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1"}]),
        "quikclid.csv": pd.DataFrame([
            {"MCLIENTID": "MISSING", "MPOLICY": "P1", "MPHASE": "0", "MRELATION": "OWNR"},
        ]),
    }
    assert any(f.rule_id == "CLID-001" for f in check_quikclid(data))


def test_clid_002_policy_not_in_quikmstr():
    data = {
        "quikclnt.csv": pd.DataFrame([{"MCLIENTID": "C1"}]),
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1"}]),
        "quikclid.csv": pd.DataFrame([
            {"MCLIENTID": "C1", "MPOLICY": "ORPHAN", "MPHASE": "0", "MRELATION": "OWNR"},
        ]),
    }
    assert any(f.rule_id == "CLID-002" for f in check_quikclid(data))


def test_clid_003_phase_not_in_quikridr():
    data = {
        "quikclnt.csv": pd.DataFrame([{"MCLIENTID": "C1"}]),
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1"}]),
        "quikridr.csv": pd.DataFrame([{"MPOLICY": "P1", "MPHASE": "1", "MRIDRID": "R1"}]),
        "quikclid.csv": pd.DataFrame([
            {"MCLIENTID": "C1", "MPOLICY": "P1", "MPHASE": "9", "MRELATION": "INSD"},
        ]),
    }
    assert any(f.rule_id == "CLID-003" for f in check_quikclid(data))


def test_clid_004_relation_requires_phase_zero():
    data = {
        "quikclnt.csv": pd.DataFrame([{"MCLIENTID": "C1"}]),
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1"}]),
        "quikridr.csv": pd.DataFrame([{"MPOLICY": "P1", "MPHASE": "1", "MRIDRID": "R1"}]),
        "quikclid.csv": pd.DataFrame([
            {"MCLIENTID": "C1", "MPOLICY": "P1", "MPHASE": "1", "MRELATION": "OWNR"},
        ]),
    }
    assert any(f.rule_id == "CLID-004" for f in check_quikclid(data))


def test_clid_005_insd_mridrid_mismatch():
    data = {
        "quikclnt.csv": pd.DataFrame([{"MCLIENTID": "C1"}, {"MCLIENTID": "R1"}]),
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1"}]),
        "quikridr.csv": pd.DataFrame([{"MPOLICY": "P1", "MPHASE": "1", "MRIDRID": "R1"}]),
        "quikclid.csv": pd.DataFrame([
            {"MCLIENTID": "C1", "MPOLICY": "P1", "MPHASE": "1", "MRELATION": "INSD"},
        ]),
    }
    assert any(f.rule_id == "CLID-005" for f in check_quikclid(data))


def test_clid_006_non_insd_must_have_phase_zero():
    data = {
        "quikclnt.csv": pd.DataFrame([{"MCLIENTID": "C1"}]),
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1"}]),
        "quikridr.csv": pd.DataFrame([{"MPOLICY": "P1", "MPHASE": "1", "MRIDRID": "R1"}]),
        "quikclid.csv": pd.DataFrame([
            {"MCLIENTID": "C1", "MPOLICY": "P1", "MPHASE": "1", "MRELATION": "OWNR"},
        ]),
    }
    assert any(f.rule_id == "CLID-006" for f in check_quikclid(data))
