"""Normalization utilities extracted from app.py (Phase P2A)."""

from __future__ import annotations

import re

import pandas as pd


def normalize(val) -> str:
    if pd.isna(val) or str(val).strip().lower() in ["nan", "none", ""]:
        return ""
    s = str(val).strip().upper()
    if s.endswith(".0"):
        s = s[:-2]
    return s


def format_qladmin_mpolicy(val) -> str:
    """Fixed-width QLAdmin MPOLICY: left-pad with spaces to exactly 10 characters."""
    if pd.isna(val) or str(val).strip().lower() in ["nan", "none", ""]:
        return ""
    core = normalize(val)
    if not core:
        return ""
    if len(core) >= 10:
        return core
    return core.rjust(10)


# LifePRO NAME_ID is Character(11), right-justified with leading spaces.
QLADMIN_MCLIENTID_WIDTH = 11
CLIENT_ID_TARGET_FIELDS = frozenset({
    "MCLIENTID",
    "MPRIMID",
    "MOWNRID",
    "MPAYRID",
    "MASGNID",
    "MBENPID",
    "MBENCID",
    "MCID",
    "MOWNCID",
    "MRIDRID",
})


def format_qladmin_mclientid(val, width: int = QLADMIN_MCLIENTID_WIDTH) -> str:
    """Fixed-width QLAdmin client ID: left-pad with spaces (right-justified)."""
    if pd.isna(val) or str(val).strip().lower() in ["nan", "none", ""]:
        return ""
    core = normalize(val)
    if not core:
        return ""
    if len(core) >= width:
        return core
    return core.rjust(width)


def extract_day(date_str) -> str:
    d = re.sub(r"[^0-9/]", "", str(date_str))
    if len(d) == 8:
        return d[-2:]
    if "/" in d:
        parts = d.split("/")
        if len(parts) >= 2:
            return parts[1].zfill(2)
    return ""


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(col).replace("\ufeff", "").strip().upper() for col in out.columns]
    return out
