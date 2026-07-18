"""Shared fixtures for QLAdmin Data Governance tests."""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta

import pytest

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)


def _prior_month_end_today() -> date:
    return date.today().replace(day=1) - timedelta(days=1)


@pytest.fixture
def clean_company_tables():
    pme = _prior_month_end_today()
    return {
        "QuikComp": [
            {"MCOMP": "A", "MNAME": "Company A"},
            {"MCOMP": "B", "MNAME": "Company B"},
        ],
        "QuikAgts": [
            {"MAGENT": "10001", "MAGTNAME": "Agent One", "MCOMP": "A"},
            {"MAGENT": "10002", "MAGTNAME": "Agent Two", "MCOMP": "A"},
            {"MAGENT": "10003", "MAGTNAME": "Agent Three", "MCOMP": "B"},
        ],
        "QuikMstr": [
            {"MPOLICY": "123456789A"},
            {"MPOLICY": "987654321B"},
        ],
        "QuikActg": [
            {"MCOMP": "A", "MPLAN": "PLAN01"},
            {"MCOMP": "A", "MPLAN": "PLAN02"},
            {"MCOMP": "B", "MPLAN": "PLAN01"},
        ],
        "QuikList": [
            {
                "MGROUP": "12345678",
                "MCOMP": "A",
                "MBILLNAME": "Acme Group",
                "MSORT": "N",
                "MLAPSEL": 0,
                "MLAPSEH": 0,
                "MSTATUS": "A",
                "MBILLDAY": 0,
                "MBILLMODE": 0,
            },
            {
                "MGROUP": "87654321",
                "MCOMP": "B",
                "MBILLNAME": "Beta Group",
                "MSORT": "n",
                "MLAPSEL": "0",
                "MLAPSEH": "000",
                "MSTATUS": "a",
                "MBILLDAY": 0.0,
                "MBILLMODE": "0",
            },
        ],
        "QuikDate": [
            {
                "PACBILL": pme,
                "DIRBILL": pme,
                "REINBILL": pme,
                "ACHFILEID": 0,
                "ACHFILEID2": "A",
                "ESC_DATE": None,
            }
        ],
        "QuikQxs": [
            {"MORT": "80"},
            {"MORT": "81"},
        ],
        "QuikPlan": [
            {"PLAN": "PLAN01"},
            {"PLAN": "PLAN02"},
        ],
        "QuikPlGd": [
            {"PLAN": "PLAN01", "GDCODE": "M"},
            {"PLAN": "PLAN01", "GDCODE": "F"},
        ],
        "QuikPlUw": [
            {"PLAN": "PLAN01", "UWCODE": "01"},
        ],
        "QuikPlBd": [
            {"PLAN": "PLAN01", "BDCODE": "01"},
        ],
        "QuikPlCv": [
            {
                "PLAN": "PLAN01",
                "GENDER": "0",
                "UWCLASS": "00",
                "BAND": "00",
                "ISSUEST": "TX",
                "EFFDATE": date(2020, 1, 1),
                "MORT": "80",
                "ETIMORT": "81",
            }
        ],
        "QuikPlTv": [
            {
                "PLAN": "PLAN01",
                "GENDER": "0",
                "UWCLASS": "00",
                "BAND": "00",
                "ISSUEST": "00",
                "EFFDATE": date(2020, 6, 15),
                "MORT": "80",
            }
        ],
        "QuikPlGp": [
            {
                "PLAN": "PLAN01",
                "GENDER": "0",
                "UWCLASS": "00",
                "BAND": "00",
                "ISSUEST": "CA",
                "EFFDATE": date(2019, 3, 1),
            }
        ],
        "QuikPlDb": [
            {
                "PLAN": "PLAN01",
                "GENDER": "M",
                "UWCLASS": "01",
                "BAND": "01",
                "ISSUEST": "NY",
                "EFFDATE": date(1900, 1, 1),
            }
        ],
        "QuikPlDv": [
            {
                "PLAN": "PLAN02",
                "GENDER": "0",
                "UWCLASS": "00",
                "BAND": "00",
                "ISSUEST": "dc",
                "EFFDATE": date(2021, 12, 31),
            }
        ],
    }
