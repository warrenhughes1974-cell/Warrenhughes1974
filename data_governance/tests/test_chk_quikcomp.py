"""Tests for chk_quikcomp."""

import pandas as pd

from data_governance.rules.chk_quikcomp import check_quikcomp


def test_comp001_duplicate_company():
    data = {
        "quikcomp.csv": pd.DataFrame([{"MCOMP": "C"}, {"MCOMP": "C"}]),
    }
    findings = check_quikcomp(data)
    assert any(f.rule_id == "COMP-001" for f in findings)


def test_comp004_policy_length():
    data = {
        "quikcomp.csv": pd.DataFrame([{"MCOMP": "C"}]),
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "SHORT"}]),
    }
    findings = check_quikcomp(data)
    assert any(f.rule_id == "COMP-004" for f in findings)
