"""Tests for chk_quikclms."""

import pandas as pd

from data_governance.rules.chk_quikclms import check_quikclms


def test_ref_003_orphan_claim():
    data = {
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1"}]),
        "quikclms.csv": pd.DataFrame([{"MPOLICY": "ORPHAN", "CLAIMNUM": "C1"}]),
    }
    findings = check_quikclms(data)
    assert any(f.rule_id == "REF-003" for f in findings)
    assert any(f.rule_id == "CLM-001" for f in findings)


def test_dup_008_duplicate_claimnum():
    data = {
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1"}]),
        "quikclms.csv": pd.DataFrame([
            {"MPOLICY": "P1", "CLAIMNUM": "C1"},
            {"MPOLICY": "P1", "CLAIMNUM": "C1"},
        ]),
    }
    assert any(f.rule_id == "DUP-008" for f in check_quikclms(data))


def test_clm_006_borrowed_money_only_activity():
    data = {
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1"}]),
        "quikclms.csv": pd.DataFrame([{"MPOLICY": "P1", "CLAIMNUM": "C1"}]),
        "PACTG": pd.DataFrame([
            {"POLICY_NUMBER": "P1", "TRANSACTION_CODE": "412"},
            {"POLICY_NUMBER": "P1", "TRANSACTION_CODE": "413"},
        ]),
    }
    assert any(f.rule_id == "CLM-006" for f in check_quikclms(data))


def test_clm_011_metadata_columns_in_output():
    data = {
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1"}]),
        "quikclms.csv": pd.DataFrame([{"MPOLICY": "P1", "CLAIMNUM": "C1", "governance_status": "HOLD"}]),
    }
    assert any(f.rule_id == "CLM-011" for f in check_quikclms(data))
