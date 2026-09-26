"""Issue 145: quikspec.VANISH from PPOLC.BILLING_REASON=VB.

Logical emit is T/F (length 1), matching the existing False default of F.
VANISHDT stays blank. Do not touch RESSTATE or RESRVCAT.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from qla_core.lifepro_source_resolver import resolve_table_source
from qla_core.normalize_utils import normalize
from qla_core.quikspec_resrvcat import _iter_extract_rows, _policy_lookup_keys

VANISH_FIELD = "VANISH"
VANISH_TRUE = "T"
VANISH_FALSE = "F"


def load_ppolc_billing_reason(src_dir: str) -> dict[str, str]:
    """POLICY_NUMBER lookup keys -> trimmed upper BILLING_REASON."""
    path, _label = resolve_table_source(src_dir, "quikspec")
    if not path or not Path(path).is_file():
        raise FileNotFoundError(f"PPOLC extract not found under {src_dir}")
    out: dict[str, str] = {}
    saw = set()
    for row in _iter_extract_rows(path):
        saw.update(row.keys())
        pol = normalize(row.get("POLICY_NUMBER", ""))
        if not pol or set(pol) <= set("-"):
            continue
        br = str(row.get("BILLING_REASON", "") or "").strip().upper()
        for key in _policy_lookup_keys(pol):
            if key not in out:
                out[key] = br
    needed = {"POLICY_NUMBER", "BILLING_REASON"}
    if not needed.issubset(saw):
        raise ValueError(f"PPOLC missing {needed - saw}: {path}")
    return out


def apply_quikspec_vanish(
    df: pd.DataFrame,
    src_dir: str,
    log=None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Set VANISH T iff PPOLC BILLING_REASON is VB; else F. Other columns unchanged."""
    stats = {
        "true": 0,
        "false": 0,
        "missing": 0,
        "rows": 0,
        "vb_source": 0,
        "source_dir": str(src_dir),
    }
    if df is None or df.empty:
        return df, stats
    out = df.copy()
    if VANISH_FIELD not in out.columns:
        out[VANISH_FIELD] = VANISH_FALSE
    reasons = load_ppolc_billing_reason(src_dir)
    vb_unique = {
        normalize(key).rstrip("C")
        for key, br in reasons.items()
        if br == "VB"
    }
    stats["vb_source"] = len(vb_unique)

    for idx in out.index:
        stats["rows"] += 1
        mpolicy = str(out.at[idx, "MPOLICY"] if "MPOLICY" in out.columns else "").strip()
        br = ""
        found = False
        for key in _policy_lookup_keys(mpolicy):
            if key in reasons:
                br = reasons[key]
                found = True
                break
        vanish = VANISH_TRUE if br == "VB" else VANISH_FALSE
        out.at[idx, VANISH_FIELD] = vanish
        if vanish == VANISH_TRUE:
            stats["true"] += 1
        else:
            stats["false"] += 1
        if not found:
            stats["missing"] += 1
    if log is not None:
        try:
            log(
                f"Issue 145: VANISH T={stats['true']} F={stats['false']} "
                f"missing={stats['missing']} vb_source={stats['vb_source']}"
            )
        except Exception:
            pass
    return out, stats
