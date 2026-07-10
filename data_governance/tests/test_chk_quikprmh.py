"""Tests for chk_quikprmh."""

import pandas as pd

from data_governance.rules.chk_quikprmh import check_quikprmh


def test_ref_002_orphan_premium_history():
    data = {
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1"}]),
        "quikprmh.csv": pd.DataFrame([{"MPOLICY": "ORPHAN", "DATEPAID": "2020-01-01", "MSOURCE": "100"}]),
    }
    assert any(f.rule_id == "REF-002" for f in check_quikprmh(data))


def test_prm_009_loan_codes_present():
    data = {
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1"}]),
        "quikprmh.csv": pd.DataFrame([{"MPOLICY": "P1", "DATEPAID": "2020-01-01", "MSOURCE": "412"}]),
    }
    assert any(f.rule_id == "PRM-009" for f in check_quikprmh(data))


def test_prm_010_blank_datepaid():
    data = {
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1"}]),
        "quikprmh.csv": pd.DataFrame([{"MPOLICY": "P1", "DATEPAID": "", "MSOURCE": "100"}]),
    }
    assert any(f.rule_id == "PRM-010" for f in check_quikprmh(data))
