"""Tests for chk_quikrates."""

import pandas as pd

from data_governance.rules.chk_quikrates import check_quikrates


def test_rate007_invalid_state():
    data = {
        "quikplan.csv": pd.DataFrame([{"PLAN": "LIFE01"}]),
        "quikqxs.csv": pd.DataFrame([{"MORT": "CSO"}]),
        "quikplcv.csv": pd.DataFrame([{
            "PLAN": "LIFE01", "MORT": "CSO", "ETIMORT": "CSO",
            "GENDER": "0", "UWCLASS": "00", "BAND": "00", "ISSUEST": "ZZ",
            "EFFDATE": "2000-01-01",
        }]),
    }
    findings = check_quikrates(data)
    assert any(f.rule_id == "RATE-007" for f in findings)


def test_rate001_mort_missing():
    data = {
        "quikplan.csv": pd.DataFrame([{"PLAN": "LIFE01"}]),
        "quikqxs.csv": pd.DataFrame([{"MORT": "CSO"}]),
        "quikplcv.csv": pd.DataFrame([{
            "PLAN": "LIFE01", "MORT": "NOPE", "ISSUEST": "00", "EFFDATE": "2000-01-01",
        }]),
    }
    findings = check_quikrates(data)
    assert any(f.rule_id == "RATE-001" for f in findings)
