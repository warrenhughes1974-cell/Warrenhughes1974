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
