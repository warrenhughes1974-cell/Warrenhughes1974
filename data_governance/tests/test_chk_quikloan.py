"""Tests for chk_quikloan."""

import pandas as pd

from data_governance.rules.chk_quikloan import check_quikloan


def test_loan_002_duplicate_mpolicy():
    data = {
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1"}]),
        "quikloan.csv": pd.DataFrame([
            {"MPOLICY": "P1", "MLOANDATE": "2020-01-01"},
            {"MPOLICY": "P1", "MLOANDATE": "2020-02-01"},
        ]),
    }
    assert any(f.rule_id == "LOAN-002" for f in check_quikloan(data))


def test_loan_005_missing_mloandate():
    data = {
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1"}]),
        "quikloan.csv": pd.DataFrame([{"MPOLICY": "P1", "MLOANDATE": ""}]),
    }
    assert any(f.rule_id == "LOAN-005" for f in check_quikloan(data))


def test_rcn_004_loan_count_reconciliation():
    data = {
        "PLOAN.csv": pd.DataFrame([
            {"POLICY_NUMBER": "P1", "LOAN_BALANCE": "100"},
            {"POLICY_NUMBER": "P2", "LOAN_BALANCE": "50"},
        ]),
        "quikloan.csv": pd.DataFrame([{"MPOLICY": "P1", "MLOANDATE": "2020-01-01"}]),
    }
    findings = check_quikloan(data)
    assert any(f.rule_id == "RCN-004" and f.severity == "Info" for f in findings)
