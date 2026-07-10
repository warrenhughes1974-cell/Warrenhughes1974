"""Tests for chk_quikclnt."""

import pandas as pd

from data_governance.rules.chk_quikclnt import check_quikclnt


def test_clnt_001_duplicate_client_id():
    data = {"quikclnt.csv": pd.DataFrame([
        {"MCLIENTID": "C1", "MTYPE": "I", "MLNAME": "Smith", "MSEX": "M", "MLANGUAGE": "E"},
        {"MCLIENTID": "C1", "MTYPE": "I", "MLNAME": "Smith", "MSEX": "M", "MLANGUAGE": "E"},
    ])}
    assert any(f.rule_id == "CLNT-001" for f in check_quikclnt(data))


def test_clnt_002_blank_mtype():
    data = {"quikclnt.csv": pd.DataFrame([
        {"MCLIENTID": "C1", "MTYPE": "", "MLNAME": "Smith", "MSEX": "M"},
    ])}
    assert any(f.rule_id == "CLNT-002" for f in check_quikclnt(data))


def test_clnt_003_mtaxidtype_default():
    data = {"quikclnt.csv": pd.DataFrame([
        {"MCLIENTID": "C1", "MTYPE": "I", "MLNAME": "Smith", "MTAXIDTYPE": "E", "MSEX": "M"},
    ])}
    assert any(f.rule_id == "CLNT-003" for f in check_quikclnt(data))


def test_clnt_004_blank_lastname():
    data = {"quikclnt.csv": pd.DataFrame([
        {"MCLIENTID": "C1", "MTYPE": "I", "MLNAME": "", "MFNAME": "A", "MSEX": "M"},
    ])}
    assert any(f.rule_id == "CLNT-004" for f in check_quikclnt(data))


def test_clnt_005_all_contact_fields_blank():
    data = {"quikclnt.csv": pd.DataFrame([{
        "MCLIENTID": "C1", "MTYPE": "I", "MLNAME": "", "MFNAME": "",
        "MADDR1": "", "MCITY": "", "MSTATE": "", "MZIP": "", "MSEX": "M",
    }])}
    assert any(f.rule_id == "CLNT-005" for f in check_quikclnt(data))


def test_clnt_006_invalid_mdob():
    data = {"quikclnt.csv": pd.DataFrame([
        {"MCLIENTID": "C1", "MTYPE": "I", "MLNAME": "Smith", "MDOB": "1800-01-01", "MSEX": "M"},
    ])}
    assert any(f.rule_id == "CLNT-006" for f in check_quikclnt(data))


def test_clnt_007_invalid_msex():
    data = {"quikclnt.csv": pd.DataFrame([
        {"MCLIENTID": "C1", "MTYPE": "I", "MLNAME": "Smith", "MSEX": "X"},
    ])}
    assert any(f.rule_id == "CLNT-007" for f in check_quikclnt(data))


def test_clnt_008_mlanguage_default():
    data = {"quikclnt.csv": pd.DataFrame([
        {"MCLIENTID": "C1", "MTYPE": "I", "MLNAME": "Smith", "MSEX": "M", "MLANGUAGE": "S"},
    ])}
    assert any(f.rule_id == "CLNT-008" for f in check_quikclnt(data))
