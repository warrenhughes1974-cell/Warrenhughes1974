"""Read-only LifePRO loaders for Phase 1 reinsurance conversion."""

from __future__ import annotations

import os
import re

import pandas as pd

_PLACEHOLDER_RE = re.compile(r"^[-_\s\.]+$")


def _s(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return str(val).strip()


def normalize_lifepro_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).replace("\ufeff", "").strip().upper() for c in out.columns]
    return out


def read_lifepro_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", low_memory=False, on_bad_lines="skip").fillna("")
    df = normalize_lifepro_columns(df)
    if len(df) and df.iloc[0].astype(str).str.contains("---").any():
        df = df.iloc[1:].reset_index(drop=True)
    return df


def is_valid_data_row(row: pd.Series, key_col: str) -> bool:
    val = _s(row.get(key_col, ""))
    if not val or _PLACEHOLDER_RE.match(val):
        return False
    return True


def load_prod_ptrty(path: str) -> pd.DataFrame:
    df = read_lifepro_csv(path)
    if "TREATY_CODE" not in df.columns:
        return df.iloc[0:0].copy()
    return df[df.apply(lambda r: is_valid_data_row(r, "TREATY_CODE"), axis=1)].reset_index(drop=True)


def load_prein(path: str) -> pd.DataFrame:
    df = read_lifepro_csv(path)
    if "POLICY_NUMBER" not in df.columns:
        return df.iloc[0:0].copy()
    return df[df.apply(lambda r: is_valid_data_row(r, "POLICY_NUMBER"), axis=1)].reset_index(drop=True)


def load_preintrt(path: str) -> pd.DataFrame:
    df = read_lifepro_csv(path)
    if "POLICY_NUMBER" not in df.columns:
        return df.iloc[0:0].copy()
    return df[df.apply(lambda r: is_valid_data_row(r, "POLICY_NUMBER"), axis=1)].reset_index(drop=True)


def prein_join_key(row: pd.Series) -> tuple[str, str, str, str]:
    return (
        _s(row.get("POLICY_NUMBER", "")),
        _normalize_benefit_seq(row.get("BENEFIT_SEQ", "")),
        _s(row.get("EFFECTIVE_DATE", "")),
        _s(row.get("RECORD_SEQUENCE", "")),
    )


def _normalize_benefit_seq(val) -> str:
    s = _s(val).replace(".0", "")
    if not s:
        return ""
    if s.isdigit():
        return str(int(s))
    return s


def build_prein_index(prein_df: pd.DataFrame) -> dict[tuple[str, str, str, str], pd.Series]:
    index: dict[tuple[str, str, str, str], pd.Series] = {}
    for _, row in prein_df.iterrows():
        index[prein_join_key(row)] = row
    return index


def _effective_sort_key(val) -> str:
    s = _s(val)
    digits = "".join(ch for ch in s if ch.isdigit())
    return digits if len(digits) == 8 else "00000000"


def _record_sort_key(val) -> float:
    s = _s(val).replace(",", "")
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def select_canonical_preintrt_rows(
    preintrt_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    One canonical PREINTRT row per POLICY_NUMBER / BENEFIT_SEQ / TREATY_CODE.

    QuikRmst grain is policy / phase / treaty. LifePRO stores multiple historical
    treaty allocation rows per key; keep the latest EFFECTIVE_DATE (then RECORD_SEQUENCE).
    Superseded rows are returned for audit only — stored values are not summed.
    """
    if preintrt_df.empty:
        return preintrt_df.copy(), preintrt_df.iloc[0:0].copy()

    work = preintrt_df.copy()
    work["_EFFECTIVE_SORT"] = work["EFFECTIVE_DATE"].map(_effective_sort_key)
    work["_RECORD_SORT"] = work["RECORD_SEQUENCE"].map(_record_sort_key)
    work = work.sort_values(
        ["POLICY_NUMBER", "BENEFIT_SEQ", "TREATY_CODE", "_EFFECTIVE_SORT", "_RECORD_SORT"],
        kind="mergesort",
    )
    canonical = work.drop_duplicates(
        ["POLICY_NUMBER", "BENEFIT_SEQ", "TREATY_CODE"],
        keep="last",
    ).drop(columns=["_EFFECTIVE_SORT", "_RECORD_SORT"])
    superseded = work[~work.index.isin(canonical.index)].drop(
        columns=["_EFFECTIVE_SORT", "_RECORD_SORT"],
    )
    return canonical.reset_index(drop=True), superseded.reset_index(drop=True)


def default_config_path(filename: str) -> str:
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "plan_governance", "config", filename)
    )
