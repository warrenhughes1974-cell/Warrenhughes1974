"""Tests for chk_quikmstr (POL-018+)."""

import pandas as pd

from data_governance.rules.chk_quikmstr import check_quikmstr


def _base_pol(**extra):
    row = {
        "MPOLICY": "P12345678C", "MSTATUS": "22", "MSTATDATE": "2020-01-01",
        "MISSDT": "2019-06-15", "MPAIDTO": "2020-01-01", "MBILLTO": "2020-01-01",
        "MBILLFRM": "1", "MMODE": "12", "MISSUEST": "TX",
        "MOWNRID": "", "MASGNID": "", "MPAYRID": "", "MOWNCID": "",
        "MBENPID": "", "MBENCID": "", "MAPPDATE": "2019-01-01",
        "MISSCNTRY": "0000", "MISSCLASS": "00", "MRESSTATE": "",
    }
    row.update(extra)
    return row


def test_pol001_duplicate():
    data = {"quikmstr.csv": pd.DataFrame([_base_pol(), _base_pol()])}
    assert any(f.rule_id == "POL-001" for f in check_quikmstr(data))


def test_pol008_paidto_before_issue():
    data = {"quikmstr.csv": pd.DataFrame([_base_pol(MPAIDTO="2018-01-01")])}
    findings = check_quikmstr(data)
    assert any(f.rule_id == "POL-008" for f in findings)


def test_pol_018_mownerid_not_in_quikclnt():
    data = {
        "quikclnt.csv": pd.DataFrame([{"MCLIENTID": "C1"}]),
        "quikmstr.csv": pd.DataFrame([_base_pol(MOWNRID="MISSING")]),
    }
    findings = check_quikmstr(data)
    assert any(f.rule_id == "POL-018" and "MOWNERID" in f.reason for f in findings)


def test_pol_019_massigid_not_in_quikclnt():
    data = {
        "quikclnt.csv": pd.DataFrame([{"MCLIENTID": "C1"}]),
        "quikmstr.csv": pd.DataFrame([_base_pol(MASGNID="MISSING")]),
    }
    assert any(f.rule_id == "POL-019" for f in check_quikmstr(data))


def test_pol_020_mpayerid_not_in_quikclnt():
    data = {
        "quikclnt.csv": pd.DataFrame([{"MCLIENTID": "C1"}]),
        "quikmstr.csv": pd.DataFrame([_base_pol(MPAYRID="MISSING")]),
    }
    assert any(f.rule_id == "POL-020" for f in check_quikmstr(data))


def test_pol_021_mowncid_not_in_quikclnt():
    data = {
        "quikclnt.csv": pd.DataFrame([{"MCLIENTID": "C1"}]),
        "quikmstr.csv": pd.DataFrame([_base_pol(MOWNCID="MISSING")]),
    }
    assert any(f.rule_id == "POL-021" for f in check_quikmstr(data))


def test_pol_022_mbenpid_must_be_empty():
    data = {"quikmstr.csv": pd.DataFrame([_base_pol(MBENPID="X")])}
    assert any(f.rule_id == "POL-022" for f in check_quikmstr(data))


def test_pol_023_mbencid_must_be_empty():
    data = {"quikmstr.csv": pd.DataFrame([_base_pol(MBENCID="X")])}
    assert any(f.rule_id == "POL-023" for f in check_quikmstr(data))


def test_pol_024_mappdate_after_missdt():
    data = {"quikmstr.csv": pd.DataFrame([_base_pol(MAPPDATE="2020-01-01")])}
    assert any(f.rule_id == "POL-024" for f in check_quikmstr(data))


def test_pol_025_misscntry_default():
    data = {"quikmstr.csv": pd.DataFrame([_base_pol(MISSCNTRY="0001")])}
    assert any(f.rule_id == "POL-025" for f in check_quikmstr(data))


def test_pol_026_missclass_default():
    data = {"quikmstr.csv": pd.DataFrame([_base_pol(MISSCLASS="01")])}
    assert any(f.rule_id == "POL-026" for f in check_quikmstr(data))


def test_pol_027_mresstate_info_flag():
    data = {"quikmstr.csv": pd.DataFrame([_base_pol(MRESSTATE="TX")])}
    findings = check_quikmstr(data)
    assert any(f.rule_id == "POL-027" and f.severity == "Info" for f in findings)
