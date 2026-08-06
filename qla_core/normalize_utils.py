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


# Client IDs (NAME_ID / MCLIENTID and linked keys): emit as C(12), left-padded.
# Rule (Warren 2026-08-05): if LifePRO value is numeric → string with zero decimals;
# trim; left-pad with spaces to 12. Append Tool still rjusts to DBF field length after strip.
QLADMIN_MCLIENTID_WIDTH = 12
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


def _client_id_core_string(val) -> str:
    """Normalize a LifePRO/client ID to a trimmed string (zero decimals if numeric)."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    if isinstance(val, bool):
        return ""
    if isinstance(val, int):
        return str(val)
    if isinstance(val, float):
        if pd.isna(val):
            return ""
        return f"{val:.0f}"

    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "null"):
        return ""
    # Numeric string (including "590235.0" / "5.90235E+5") → zero-decimal digits
    try:
        as_f = float(s.replace(",", ""))
    except ValueError:
        return s.strip()
    if pd.isna(as_f):
        return ""
    return f"{as_f:.0f}"


def format_qladmin_mclientid(val, width: int = QLADMIN_MCLIENTID_WIDTH) -> str:
    """Client ID for QLAdmin tables: trim, numeric→zero decimals, left-pad to width (12)."""
    core = _client_id_core_string(val)
    if not core:
        return ""
    core = core.strip()
    if not core:
        return ""
    if len(core) > width:
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
