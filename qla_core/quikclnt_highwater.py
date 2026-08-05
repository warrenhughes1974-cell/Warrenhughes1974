"""
TEMPORARY — QLAdmin new-client ID high-water row on quikclnt.

QLAdmin appears to assign New Client IDs from the last physical quikclnt
record (+1), not max(MCLIENTID)+1. Converted LifePRO NAME_IDs occupy low
ranges (e.g. 12480), so manual adds collide (John Doe → First Choice).

This module appends one sentinel row at EOF whose MCLIENTID is
max(existing)+1 (right-justified), so the next UI-assigned ID is high and free.

Disable / remove:
  set QLA_QUIKCLNT_HIGHWATER=0
  or delete this hook from app.py after Robert confirms real next-ID behavior
  or after sequential client-ID remap ships.

Sentinel identity: MLNAME == HIGHWATER_MLNAME (stripped for re-runs).
"""
from __future__ import annotations

import os
from typing import Any

import pandas as pd

from qla_core.normalize_utils import format_qladmin_mclientid

HIGHWATER_MLNAME = "ZZZ CONVERSION HIGHWATER"
HIGHWATER_MFNAME = "TEMP"
ENV_FLAG = "QLA_QUIKCLNT_HIGHWATER"


def highwater_enabled() -> bool:
    raw = (os.environ.get(ENV_FLAG) or "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def _max_client_id(df: pd.DataFrame) -> int:
    mx = 0
    if "MCLIENTID" not in df.columns:
        return mx
    for raw in df["MCLIENTID"].astype(str):
        core = raw.strip()
        if core.isdigit():
            mx = max(mx, int(core))
    return mx


def apply_quikclnt_highwater(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Ensure exactly one high-water sentinel is the last physical row.
    Returns (df, stats).
    """
    stats: dict[str, Any] = {
        "enabled": highwater_enabled(),
        "applied": False,
        "removed_prior": 0,
        "highwater_id": "",
        "max_prior": 0,
    }
    if df is None or df.empty:
        stats["skip"] = "empty"
        return df, stats
    if not highwater_enabled():
        stats["skip"] = "disabled"
        return df, stats

    out = df.copy()
    for col in out.columns:
        out[col] = out[col].astype(str).fillna("")

    if "MLNAME" in out.columns:
        mask = out["MLNAME"].astype(str).str.strip().str.upper() == HIGHWATER_MLNAME
        stats["removed_prior"] = int(mask.sum())
        out = out.loc[~mask].copy()

    max_prior = _max_client_id(out)
    stats["max_prior"] = max_prior
    high_id = max_prior + 1 if max_prior > 0 else 1
    high_fmt = format_qladmin_mclientid(str(high_id))
    stats["highwater_id"] = high_fmt

    row = {c: "" for c in out.columns}
    if "MCLIENTID" in row:
        row["MCLIENTID"] = high_fmt
    if "MTYPE" in row:
        row["MTYPE"] = "I"
    if "MTAXIDTYPE" in row:
        row["MTAXIDTYPE"] = "S"
    if "MFNAME" in row:
        row["MFNAME"] = HIGHWATER_MFNAME
    if "MLNAME" in row:
        row["MLNAME"] = HIGHWATER_MLNAME
    if "MADDR1" in row:
        row["MADDR1"] = "TEMP HIGHWATER - DO NOT USE"
    if "MCITY" in row:
        row["MCITY"] = "OMAHA"
    if "MSTATE" in row:
        row["MSTATE"] = "NE"
    if "MCOUNTRY" in row:
        row["MCOUNTRY"] = "0000"
    if "MLANGUAGE" in row:
        row["MLANGUAGE"] = "E"
    if "MSEX" in row:
        row["MSEX"] = "M"

    out = pd.concat([out, pd.DataFrame([row], columns=out.columns)], ignore_index=True)
    stats["applied"] = True
    stats["row_count"] = len(out)
    return out, stats


def apply_quikclnt_highwater_csv(path: str | os.PathLike[str]) -> dict[str, Any]:
    """Read/write quikclnt.csv in place."""
    p = os.fspath(path)
    df = pd.read_csv(p, dtype=str, encoding="utf-8-sig").fillna("")
    out, stats = apply_quikclnt_highwater(df)
    if stats.get("applied"):
        out.to_csv(p, index=False, encoding="utf-8-sig")
    stats["path"] = p
    return stats
