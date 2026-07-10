"""Governance rule modules package."""

from .chk_source_files import check_source_files
from .chk_schema import check_schema
from .chk_crosswalk import check_crosswalk
from .chk_quikcomp import check_quikcomp
from .chk_quikplan import check_quikplan
from .chk_quikrates import check_quikrates
from .chk_quikactg_chrt import check_quikactg_chrt
from .chk_quiklist import check_quiklist
from .chk_quikdate import check_quikdate
from .chk_dates import check_global_dates, check_global_date_sweep
from .chk_quikmstr import check_quikmstr
from .chk_quikridr import check_quikridr
from .chk_quikprmh import check_quikprmh
from .chk_quikclms import check_quikclms
from .chk_quikloan import check_quikloan
from .chk_quikclnt import check_quikclnt
from .chk_quikclid import check_quikclid
from .chk_reconciliation import check_reconciliation

# Ordered check pipeline — never skip a step
CHECK_PIPELINE = [
    ("Source File Presence", check_source_files),
    ("Schema Integrity", check_schema),
    ("Crosswalk Integrity", check_crosswalk),
    ("QUIKCOMP", check_quikcomp),
    ("QUIKPLAN", check_quikplan),
    ("Rate/Mortality Tables", check_quikrates),
    ("QUIKACTG + QUIKCHRT", check_quikactg_chrt),
    ("QUIKLIST", check_quiklist),
    ("QUIKDATE", check_quikdate),
    ("Policy Master", check_quikmstr),
    ("Riders", check_quikridr),
    ("Premium History", check_quikprmh),
    ("Claims", check_quikclms),
    ("Loans", check_quikloan),
    ("Clients", check_quikclnt),
    ("Client-Policy Links", check_quikclid),
    ("Count Reconciliation", check_reconciliation),
    ("Global Date Sweep", check_global_dates),
]

__all__ = [
    "CHECK_PIPELINE",
    "check_source_files",
    "check_schema",
    "check_crosswalk",
    "check_quikcomp",
    "check_quikplan",
    "check_quikrates",
    "check_quikactg_chrt",
    "check_quiklist",
    "check_quikdate",
    "check_global_dates",
    "check_global_date_sweep",
    "check_quikmstr",
    "check_quikridr",
    "check_quikprmh",
    "check_quikclms",
    "check_quikloan",
    "check_quikclnt",
    "check_quikclid",
    "check_reconciliation",
]
