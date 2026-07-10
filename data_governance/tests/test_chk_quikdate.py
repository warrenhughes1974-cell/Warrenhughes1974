"""Tests for chk_quikdate."""

import pandas as pd

from data_governance.rules._helpers import last_day_previous_month
from data_governance.rules.chk_quikdate import check_quikdate


def test_date001_wrong_bill_date():
    data = {
        "quikdate.csv": pd.DataFrame([{
            "PACBILL": "1900-01-01",
            "DIRBILL": last_day_previous_month().isoformat(),
            "REINBILL": last_day_previous_month().isoformat(),
            "ACHFILEID": "0",
            "ESCDATE": "",
        }]),
    }
    findings = check_quikdate(data)
    assert any(f.rule_id == "DATE-001" for f in findings)
