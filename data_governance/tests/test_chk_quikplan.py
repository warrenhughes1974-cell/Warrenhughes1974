"""Tests for chk_quikplan."""

import pandas as pd

from data_governance.rules.chk_quikplan import check_quikplan


def test_plan001_invalid_code():
    df = pd.DataFrame([{"PLAN": "bad!", "PAR": "0", "BASIS": "", "LOAGE": "0", "HIAGE": "99",
                        "RENEW": "N", "PAYYRS": "10", "PAYAGE": "0", "INSYRS": "10", "INSAGE": "0",
                        "DEFICIENCY": "N"}])
    findings = check_quikplan({"quikplan.csv": df})
    assert any(f.rule_id == "PLAN-001" for f in findings)


def test_plan002_reserved_suffix():
    df = pd.DataFrame([{"PLAN": "ABCDPA", "PAR": "0", "BASIS": "", "LOAGE": "0", "HIAGE": "99",
                        "RENEW": "N", "PAYYRS": "10", "PAYAGE": "0", "INSYRS": "10", "INSAGE": "0",
                        "DEFICIENCY": "N"}])
    findings = check_quikplan({"quikplan.csv": df})
    assert any(f.rule_id == "PLAN-002" for f in findings)


def test_plan004_annuity_basis():
    df = pd.DataFrame([{"PLAN": "A12345", "PAR": "0", "BASIS": "bad", "LOAGE": "0", "HIAGE": "99",
                        "RENEW": "N", "PAYYRS": "0", "PAYAGE": "0", "INSYRS": "0", "INSAGE": "0",
                        "DEFICIENCY": "N"}])
    findings = check_quikplan({"quikplan.csv": df})
    assert any(f.rule_id == "PLAN-004" for f in findings)
