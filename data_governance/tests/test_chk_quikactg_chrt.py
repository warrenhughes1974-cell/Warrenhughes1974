"""Tests for chk_quikactg_chrt."""

import pandas as pd

from data_governance.rules.chk_quikactg_chrt import check_quikactg_chrt


def test_actg001_duplicate_key():
    data = {
        "quikcomp.csv": pd.DataFrame([{"MCOMP": "C"}]),
        "quikactg.csv": pd.DataFrame([
            {"MCOMP": "C", "MPLAN": "MASTER", "MPREM1ST": "100"},
            {"MCOMP": "C", "MPLAN": "MASTER", "MPREM1ST": "100"},
        ]),
    }
    findings = check_quikactg_chrt(data)
    assert any(f.rule_id == "ACTG-001" for f in findings)


def test_actg002_bad_company():
    data = {
        "quikcomp.csv": pd.DataFrame([{"MCOMP": "C"}]),
        "quikactg.csv": pd.DataFrame([{"MCOMP": "X", "MPLAN": "P1", "MPREM1ST": "1"}]),
    }
    findings = check_quikactg_chrt(data)
    assert any(f.rule_id == "ACTG-002" for f in findings)
