"""Tests for GDATE-001 global date sweep."""

from datetime import date, timedelta

import pandas as pd

from data_governance.rules._helpers import max_allowed_date
from data_governance.rules.chk_dates import check_global_dates


def test_gdate_001_date_before_1900():
    data = {"quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1", "MISSDT": "1800-01-01"}])}
    findings = check_global_dates(data)
    assert any(f.rule_id == "GDATE-001" for f in findings)


def test_gdate_001_date_after_today_plus_12_months():
    far = (max_allowed_date() + timedelta(days=60)).isoformat()
    data = {"quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1", "MISSDT": far}])}
    findings = check_global_dates(data)
    assert any(f.rule_id == "GDATE-001" for f in findings)


def test_gdate_001_valid_dates_pass():
    data = {"quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1", "MISSDT": "2000-01-01"}])}
    findings = check_global_dates(data)
    assert not any(f.rule_id == "GDATE-001" for f in findings)


def test_gdate_001_non_date_columns_skipped():
    data = {"quikmstr.csv": pd.DataFrame([{"MPOLICY": "P1", "MSTATUS": "not-a-date", "DESCR": "hello"}])}
    findings = check_global_dates(data)
    assert findings == []
