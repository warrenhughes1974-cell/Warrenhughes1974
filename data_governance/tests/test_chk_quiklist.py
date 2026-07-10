"""Tests for chk_quiklist."""

import pandas as pd

from data_governance.rules.chk_quiklist import check_quiklist


def test_list001_duplicate_group():
    data = {
        "quikcomp.csv": pd.DataFrame([{"MCOMP": "C"}]),
        "quiklist.csv": pd.DataFrame([
            {"MGROUP": "G1", "MCOMP": "C", "MBILLNAME": "A", "MSORT": "N",
             "MLAPSEL": "0", "MLASPEH": "0", "MSTATUS": "A", "MBILLDAY": "0", "MBILLMODE": "0"},
            {"MGROUP": "G1", "MCOMP": "C", "MBILLNAME": "B", "MSORT": "N",
             "MLAPSEL": "0", "MLASPEH": "0", "MSTATUS": "A", "MBILLDAY": "0", "MBILLMODE": "0"},
        ]),
    }
    findings = check_quiklist(data)
    assert any(f.rule_id == "LIST-001" for f in findings)


def test_list003_missing_billname():
    data = {
        "quikcomp.csv": pd.DataFrame([{"MCOMP": "C"}]),
        "quiklist.csv": pd.DataFrame([
            {"MGROUP": "G1", "MCOMP": "C", "MBILLNAME": "", "MSORT": "N",
             "MLAPSEL": "0", "MLASPEH": "0", "MSTATUS": "A", "MBILLDAY": "0", "MBILLMODE": "0"},
        ]),
    }
    findings = check_quiklist(data)
    assert any(f.rule_id == "LIST-003" for f in findings)
