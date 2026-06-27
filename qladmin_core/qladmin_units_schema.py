"""QLAdmin units-field (MUNIT) precision schema — Issue 21K.

Source: QLAdmin Help.pdf §7.203–7.234 (QuikRidr, QuikPolx, QuikRval, QuikTval, QuikValf, QuikVerr).
Authorized change: units field decimal precision 3 → 5 (field length unchanged per table).
"""

from __future__ import annotations

from typing import Any

UNITS_FIELD = "MUNIT"
UNITS_DECIMALS_BEFORE = 3
UNITS_DECIMALS_AFTER = 5

# Six tables in coordinated Issue 21K release (QLAdmin Help table names).
ISSUE_21K_TABLES: tuple[str, ...] = (
    "QUIKPOLX",
    "QUIKRIDR",
    "QUIKRVAL",
    "QUIKVALF",
    "QUIKVERR",
    "QUIKTVAL",
)

# MUNIT numeric width per table (Help); decimals widened 3 → 5 (QuikPolx/QuikVerr keep length).
TABLE_MUNIT_WIDTH: dict[str, int] = {
    "QUIKPOLX": 11,
    "QUIKRIDR": 10,
    "QUIKRVAL": 10,
    "QUIKVALF": 10,
    "QUIKVERR": 7,
    "QUIKTVAL": 10,
}


def munit_spec(table: str, *, after: bool = True) -> str:
    """Return dbf spec fragment for MUNIT, e.g. ``MUNIT N(10,5)``."""
    width = TABLE_MUNIT_WIDTH[table.upper()]
    decimals = UNITS_DECIMALS_AFTER if after else UNITS_DECIMALS_BEFORE
    return f"{UNITS_FIELD} N({width},{decimals})"


def schema_before_after(table: str) -> tuple[str, str]:
    before = f"{UNITS_FIELD} N({TABLE_MUNIT_WIDTH[table.upper()]},{UNITS_DECIMALS_BEFORE})"
    after = f"{UNITS_FIELD} N({TABLE_MUNIT_WIDTH[table.upper()]},{UNITS_DECIMALS_AFTER})"
    return before, after


# QUIKRIDR — Coverage Information Master (Help §7.203). Column order fixed.
QUIKRIDR_DBF_LAYOUT: list[dict[str, Any]] = [
    {"field": "MPOLICY", "type": "CHARACTER", "length": 10, "decimals": 0},
    {"field": "MPHASE", "type": "NUMERIC", "length": 2, "decimals": 0},
    {"field": "MPHSTAT", "type": "CHARACTER", "length": 2, "decimals": 0},
    {"field": "MLASTANN", "type": "NUMERIC", "length": 3, "decimals": 0},
    {"field": "MANNSTAT", "type": "CHARACTER", "length": 1, "decimals": 0},
    {"field": "MPHDOB", "type": "DATE", "length": 8, "decimals": 0},
    {"field": "MSEX", "type": "CHARACTER", "length": 1, "decimals": 0},
    {"field": "MPLAN", "type": "CHARACTER", "length": 6, "decimals": 0},
    {"field": "MPAR", "type": "CHARACTER", "length": 1, "decimals": 0},
    {"field": "MEFFDATE", "type": "DATE", "length": 8, "decimals": 0},
    {"field": "MEXPRY", "type": "DATE", "length": 8, "decimals": 0},
    {"field": "MPAYUP", "type": "DATE", "length": 8, "decimals": 0},
    {"field": "MAGE", "type": "NUMERIC", "length": 3, "decimals": 0},
    {"field": "MUNIT", "type": "NUMERIC", "length": 10, "decimals": UNITS_DECIMALS_AFTER},
    {"field": "MVPU", "type": "NUMERIC", "length": 8, "decimals": 2},
    {"field": "MPREM", "type": "NUMERIC", "length": 10, "decimals": 2},
    {"field": "MANNLFEE", "type": "NUMERIC", "length": 8, "decimals": 4},
    {"field": "MSEMIFEE", "type": "NUMERIC", "length": 8, "decimals": 4},
    {"field": "MQTRLFEE", "type": "NUMERIC", "length": 8, "decimals": 4},
    {"field": "MMTHDFEE", "type": "NUMERIC", "length": 8, "decimals": 4},
    {"field": "MMTHBFEE", "type": "NUMERIC", "length": 8, "decimals": 4},
    {"field": "MRRULE", "type": "CHARACTER", "length": 1, "decimals": 0},
    {"field": "MCOMMID", "type": "CHARACTER", "length": 4, "decimals": 0},
    {"field": "MCV0", "type": "NUMERIC", "length": 10, "decimals": 5},
    {"field": "MCV1", "type": "NUMERIC", "length": 10, "decimals": 5},
    {"field": "MCV2", "type": "NUMERIC", "length": 10, "decimals": 5},
    {"field": "MSAVEAGE", "type": "NUMERIC", "length": 3, "decimals": 0},
    {"field": "MSAVEUNIT", "type": "NUMERIC", "length": 10, "decimals": 3},
    {"field": "MSAVEVPU", "type": "NUMERIC", "length": 7, "decimals": 2},
    {"field": "MSAVEPREM", "type": "NUMERIC", "length": 10, "decimals": 2},
    {"field": "MRIDRID", "type": "CHARACTER", "length": 12, "decimals": 0},
    {"field": "MSSN", "type": "CHARACTER", "length": 11, "decimals": 0},
    {"field": "MUWCLASS", "type": "CHARACTER", "length": 2, "decimals": 0},
    {"field": "MBAND", "type": "CHARACTER", "length": 2, "decimals": 0},
    {"field": "MSAVESTAT", "type": "CHARACTER", "length": 2, "decimals": 0},
    {"field": "MCOMMPREM", "type": "NUMERIC", "length": 10, "decimals": 2},
    {"field": "MSPCODE", "type": "CHARACTER", "length": 4, "decimals": 0},
    {"field": "MLOCKTYP", "type": "CHARACTER", "length": 1, "decimals": 0},
    {"field": "MLOCKDT", "type": "DATE", "length": 8, "decimals": 0},
    {"field": "MUNLCKDT", "type": "DATE", "length": 8, "decimals": 0},
]

# Pre-change layout snapshot (MUNIT N(10,3) only — for before/after documentation).
QUIKRIDR_DBF_LAYOUT_BEFORE: list[dict[str, Any]] = [
    dict(fld, decimals=UNITS_DECIMALS_BEFORE) if fld["field"] == UNITS_FIELD else dict(fld)
    for fld in QUIKRIDR_DBF_LAYOUT
]
