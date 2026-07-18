"""Approved table inventories for DG-QUIKPLAN cross-table rules."""

from __future__ import annotations

from data_governance.config.settings import (
    TABLE_QUIKACTG,
    TABLE_QUIKAGTS,
    TABLE_QUIKAINT,
    TABLE_QUIKAING,
    TABLE_QUIKAEXP,
    TABLE_QUIKAINF,
    TABLE_QUIKCHRT,
    TABLE_QUIKCOMM,
    TABLE_QUIKCVS,
    TABLE_QUIKDBS,
    TABLE_QUIKDATE,
    TABLE_QUIKGPS,
    TABLE_QUIKISSC,
    TABLE_QUIKLIST,
    TABLE_QUIKNFF,
    TABLE_QUIKNPS,
    TABLE_QUIKPLBD,
    TABLE_QUIKPLCV,
    TABLE_QUIKPLDB,
    TABLE_QUIKPLDV,
    TABLE_QUIKPLGD,
    TABLE_QUIKPLGP,
    TABLE_QUIKPLNB,
    TABLE_QUIKPLST,
    TABLE_QUIKPLTV,
    TABLE_QUIKPLUW,
    TABLE_QUIKTVS,
    TABLE_QUIKUINT,
)

# (logical_table, plan_field, friendly_name)
RATE_KEY_TABLES: tuple[tuple[str, str, str], ...] = (
    (TABLE_QUIKGPS, "PLAN", "Gross Premium Setup"),
    (TABLE_QUIKCVS, "PLAN", "Cash Value Setup"),
    (TABLE_QUIKDBS, "PLAN", "Death Benefit Setup"),
    (TABLE_QUIKNPS, "PLAN", "Net Premium Setup"),
    (TABLE_QUIKTVS, "PLAN", "Terminal Reserve Setup"),
    (TABLE_QUIKNFF, "PLAN", "Nonforfeiture Factor Setup"),
    (TABLE_QUIKPLGP, "PLAN", "Gross Premium Plan Values"),
    (TABLE_QUIKPLCV, "PLAN", "Cash Value Plan Values"),
    (TABLE_QUIKPLDB, "PLAN", "Death Benefit Plan Values"),
    (TABLE_QUIKPLDV, "PLAN", "Dividend Plan Values"),
    (TABLE_QUIKPLTV, "PLAN", "Tabular Plan Values"),
    (TABLE_QUIKPLGD, "PLAN", "Gender Setup"),
    (TABLE_QUIKPLUW, "PLAN", "Underwriting Class Setup"),
    (TABLE_QUIKPLBD, "PLAN", "Band Setup"),
    (TABLE_QUIKPLST, "PLAN", "State Setup"),
    (TABLE_QUIKPLNB, "PLAN", "New Business Setup"),
    (TABLE_QUIKUINT, "MPLAN", "Universal Life Interest Setup"),
    (TABLE_QUIKAINT, "MPLAN", "Annuity Interest Setup"),
    (TABLE_QUIKAING, "MPLAN", "Annuity Guarantee Setup"),
    (TABLE_QUIKAEXP, "MPLAN", "Annuity Expense Setup"),
    (TABLE_QUIKAINF, "MPLAN", "Annuity Information Setup"),
    (TABLE_QUIKISSC, "PLAN", "Issue Charge Setup"),
)

# (table, company_field)
COMPANY_BEARING_TABLES: tuple[tuple[str, str], ...] = (
    (TABLE_QUIKAGTS, "MCOMP"),
    (TABLE_QUIKACTG, "MCOMP"),
    (TABLE_QUIKLIST, "MCOMP"),
    (TABLE_QUIKCHRT, "MCOMP"),
)

# (table, date_field)
DATE_FIELDS: tuple[tuple[str, str], ...] = (
    (TABLE_QUIKPLCV, "EFFDATE"),
    (TABLE_QUIKPLTV, "EFFDATE"),
    (TABLE_QUIKPLGP, "EFFDATE"),
    (TABLE_QUIKPLDB, "EFFDATE"),
    (TABLE_QUIKPLDV, "EFFDATE"),
    (TABLE_QUIKPLNB, "EFFDATE"),
    (TABLE_QUIKDATE, "PACBILL"),
    (TABLE_QUIKDATE, "DIRBILL"),
    (TABLE_QUIKDATE, "REINBILL"),
    (TABLE_QUIKCOMM, "EFFDATE"),
    (TABLE_QUIKAINT, "MEFFDATE"),
    (TABLE_QUIKUINT, "MEFFDATE"),
)

TRADITIONAL_VALUE_TABLES: tuple[tuple[str, str], ...] = (
    (TABLE_QUIKPLCV, "Cash Value Plan Values"),
    (TABLE_QUIKPLTV, "Tabular Plan Values"),
    (TABLE_QUIKCVS, "Cash Value Setup"),
    (TABLE_QUIKTVS, "Terminal Reserve Setup"),
    (TABLE_QUIKNPS, "Net Premium Setup"),
)

ANNUITY_SUPPORT_TABLES: tuple[tuple[str, str], ...] = (
    (TABLE_QUIKAINT, "Annuity Interest Setup"),
    (TABLE_QUIKAING, "Annuity Guarantee Setup"),
    (TABLE_QUIKAEXP, "Annuity Expense Setup"),
    (TABLE_QUIKAINF, "Annuity Information Setup"),
)
