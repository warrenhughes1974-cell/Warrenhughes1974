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


# Issue #2: QLAdmin policy keys are source POLICY_NUMBER + trailing C, width 11.
QLADMIN_MPOLICY_WIDTH = 11


def format_qladmin_mpolicy(val) -> str:
    """Issue #2: keep source policy number, append C, right-justify to 11 characters.

    Supersedes Issue #25 (10-char pad after strip-9 crosswalk).
    - Identity: normalize(source); append 'C' unless already present
    - Reject sentinel / over-length keys (blank emit)
    - Width: left-pad with spaces to exactly 11 (CSV→DBF right-justify)
    """
    if pd.isna(val) or str(val).strip().lower() in ["nan", "none", ""]:
        return ""
    core = normalize(val)
    if not core:
        return ""
    # Placeholder / garbage keys (e.g. extract sentinel '-------------')
    if core.replace("-", "") == "" or core.startswith("----"):
        return ""
    # Idempotent: already a final Issue #2 key (exactly width 11, trailing C)
    if len(core) == QLADMIN_MPOLICY_WIDTH and core.endswith("C"):
        return core
    # Always append C to the source policy number (Warren 2026-07-23)
    core = core + "C"
    if len(core) > QLADMIN_MPOLICY_WIDTH:
        return ""
    return core.rjust(QLADMIN_MPOLICY_WIDTH)


# LifePRO NAME_ID is Character(11), right-justified with leading spaces.
# QLAdmin DBF templates often use C(12) for the same keys — Append Tool must
# rjust to the template field length after strip (see build_full_dbf_append_package).
QLADMIN_MCLIENTID_WIDTH = 11
CLIENT_ID_TARGET_FIELDS = frozenset({
    "MCLIENTID",
    "MPRIMID",
    "MOWNRID",
    "MPAYRID",
    "MASGNID",
    "MBENPID",
    "MBENCID",
    "MBENFID",  # quikbenf beneficiary client id
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
