"""Tests for chk_quikridr."""

import pandas as pd

from data_governance.rules.chk_quikridr import check_quikridr


def test_ref_001_orphan_rider():
    data = {
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1", "MISSDT": "2010-01-01"}]),
        "quikridr.csv": pd.DataFrame([{
            "MPOLICY": "ORPHAN", "MPHASE": "1", "MRIDRID": "R1", "MPLAN": "LIFE01",
            "MPHDOB": "1980-01-01",
        }]),
        "quikplan.csv": pd.DataFrame([{"PLAN": "LIFE01"}]),
    }
    assert any(f.rule_id == "REF-001" for f in check_quikridr(data))


def test_req_002_blank_mridrid():
    data = {
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1", "MISSDT": "2010-01-01"}]),
        "quikridr.csv": pd.DataFrame([{
            "MPOLICY": "P1", "MPHASE": "1", "MRIDRID": "", "MPLAN": "LIFE01",
        }]),
        "quikplan.csv": pd.DataFrame([{"PLAN": "LIFE01"}]),
    }
    assert any(f.rule_id == "REQ-002" for f in check_quikridr(data))


def test_req_003_blank_or_zero_mphase():
    data = {
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1", "MISSDT": "2010-01-01"}]),
        "quikridr.csv": pd.DataFrame([{
            "MPOLICY": "P1", "MPHASE": "0", "MRIDRID": "R1", "MPLAN": "LIFE01",
        }]),
        "quikplan.csv": pd.DataFrame([{"PLAN": "LIFE01"}]),
    }
    assert any(f.rule_id == "REQ-003" for f in check_quikridr(data))


def test_rdr_002_missing_base_coverage():
    data = {
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1", "MISSDT": "2010-01-01"}]),
        "quikridr.csv": pd.DataFrame([{
            "MPOLICY": "P1", "MPHASE": "2", "MRIDRID": "R1", "MPLAN": "LIFE01",
        }]),
        "quikplan.csv": pd.DataFrame([{"PLAN": "LIFE01"}]),
    }
    findings = check_quikridr(data)
    assert any(f.rule_id == "RDR-002" for f in findings)
    assert any(f.rule_id == "RDR-003" for f in findings)


def test_rdr_003_supplemental_without_base():
    test_rdr_002_missing_base_coverage()


def test_dup_002_duplicate_policy_phase():
    data = {
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1", "MISSDT": "2010-01-01"}]),
        "quikridr.csv": pd.DataFrame([
            {"MPOLICY": "P1", "MPHASE": "1", "MRIDRID": "R1", "MPLAN": "LIFE01"},
            {"MPOLICY": "P1", "MPHASE": "1", "MRIDRID": "R2", "MPLAN": "LIFE01"},
        ]),
        "quikplan.csv": pd.DataFrame([{"PLAN": "LIFE01"}]),
    }
    assert any(f.rule_id == "DUP-002" for f in check_quikridr(data))


def test_dup_003_duplicate_mridrid():
    data = {
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1", "MISSDT": "2010-01-01"}]),
        "quikridr.csv": pd.DataFrame([
            {"MPOLICY": "P1", "MPHASE": "1", "MRIDRID": "R1", "MPLAN": "LIFE01"},
            {"MPOLICY": "P1", "MPHASE": "2", "MRIDRID": "R1", "MPLAN": "LIFE01"},
        ]),
        "quikplan.csv": pd.DataFrame([{"PLAN": "LIFE01"}]),
    }
    assert any(f.rule_id == "DUP-003" for f in check_quikridr(data))


def test_ref_011_mplan_not_in_quikplan():
    data = {
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1", "MISSDT": "2010-01-01"}]),
        "quikridr.csv": pd.DataFrame([{
            "MPOLICY": "P1", "MPHASE": "1", "MRIDRID": "R1", "MPLAN": "NOPE01",
        }]),
        "quikplan.csv": pd.DataFrame([{"PLAN": "LIFE01"}]),
    }
    assert any(f.rule_id == "REF-011" for f in check_quikridr(data))


def test_dt_003_dob_after_issue_date():
    data = {
        "quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1", "MISSDT": "2010-01-01"}]),
        "quikridr.csv": pd.DataFrame([{
            "MPOLICY": "P1", "MPHASE": "1", "MRIDRID": "R1", "MPLAN": "LIFE01",
            "MPHDOB": "2015-01-01",
        }]),
        "quikplan.csv": pd.DataFrame([{"PLAN": "LIFE01"}]),
    }
    assert any(f.rule_id == "DT-003" for f in check_quikridr(data))
