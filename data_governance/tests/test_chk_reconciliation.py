"""Tests for chk_reconciliation and engine smoke."""

import os
import tempfile

import pandas as pd

from data_governance.governance_engine import run_governance
from data_governance.rules.chk_reconciliation import check_reconciliation


def test_rcn_001_policy_count_variance():
    data = {
        "_context": {"source_policy_count": 10},
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1"}, {"MPOLICY": "P2"}]),
    }
    findings = check_reconciliation(data)
    assert any(f.rule_id == "RCN-001" and f.severity == "Info" for f in findings)


def test_rcn_002_output_row_counts():
    data = {
        "quikridr.csv": pd.DataFrame([{"MPOLICY": "P1"}]),
        "quikclnt.csv": pd.DataFrame([{"MCLIENTID": "C1"}]),
    }
    findings = check_reconciliation(data)
    assert any(f.rule_id == "RCN-002" for f in findings)


def test_rcn_003_dropped_policy_count():
    data = {
        "Master_Crosswalk.csv": pd.DataFrame([
            {"SOURCE_POLICY": "S1", "MPOLICY": "P1"},
            {"SOURCE_POLICY": "S2", "MPOLICY": "P2"},
            {"SOURCE_POLICY": "S3", "MPOLICY": "P3"},
        ]),
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1"}]),
    }
    findings = check_reconciliation(data)
    assert any(f.rule_id == "RCN-003" and f.affected_count >= 2 for f in findings)


def test_engine_runs_all_checks_and_writes_reports():
    with tempfile.TemporaryDirectory() as td:
        report = run_governance({
            "conversion_id": "TEST-001",
            "output_dir": td,
            "report_dir": td,
            "source_dir": td,
            "required_source_files": [],
            "write_reports": True,
            "dataframes": {
                "quikmstr.csv": pd.DataFrame([{
                    "MPOLICY": "P12345678C", "MSTATUS": "22", "MSTATDATE": "2020-01-01",
                    "MISSDT": "2019-01-01", "MPAIDTO": "2020-01-01", "MBILLTO": "2020-01-01",
                    "MBILLFRM": "1", "MMODE": "12", "MISSUEST": "TX",
                }]),
                "quikplan.csv": pd.DataFrame([{
                    "PLAN": "LIFE01", "PAR": "0", "BASIS": "", "LOAGE": "0", "HIAGE": "99",
                    "RENEW": "N", "PAYYRS": "10", "PAYAGE": "0", "INSYRS": "99", "INSAGE": "0",
                    "DEFICIENCY": "N", "INITVAL": "1000", "LOANINTX": "A",
                }]),
            },
        })
        assert report.conversion_id == "TEST-001"
        assert os.path.isfile(os.path.join(td, "governance_audit.html"))
        html = open(os.path.join(td, "governance_audit.html"), encoding="utf-8").read()
        assert "CONVERSION GOVERNANCE AUDIT" in html
        assert isinstance(report.findings, list)
