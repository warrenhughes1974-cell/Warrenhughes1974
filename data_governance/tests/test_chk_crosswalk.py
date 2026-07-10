"""Tests for chk_crosswalk."""

import pandas as pd

from data_governance.rules.chk_crosswalk import check_crosswalk


def test_cw001_one_source_many_mpolicy():
    df = pd.DataFrame([
        {"SOURCE_POLICY": "S1", "MPOLICY": "P1"},
        {"SOURCE_POLICY": "S1", "MPOLICY": "P2"},
    ])
    findings = check_crosswalk({"Master_Crosswalk.csv": df})
    assert any(f.rule_id == "CW-001" for f in findings)


def test_cw002_many_source_one_mpolicy():
    df = pd.DataFrame([
        {"SOURCE_POLICY": "S1", "MPOLICY": "P1"},
        {"SOURCE_POLICY": "S2", "MPOLICY": "P1"},
    ])
    findings = check_crosswalk({"Master_Crosswalk.csv": df})
    assert any(f.rule_id == "CW-002" for f in findings)


def test_crosswalk_clean():
    df = pd.DataFrame([
        {"SOURCE_POLICY": "S1", "MPOLICY": "P1"},
        {"SOURCE_POLICY": "S2", "MPOLICY": "P2"},
    ])
    findings = check_crosswalk({"Master_Crosswalk.csv": df})
    assert findings == []
