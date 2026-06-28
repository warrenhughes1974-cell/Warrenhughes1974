"""
Issue #27 — Substandard Life (SL) benefit row governance for quikridr emit.

SL (Substandard Life) is rating metadata in LifePRO, not a separate death benefit.
Rows with BENEFIT_TYPE = SL must not emit to quikridr.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

import pandas as pd

SL_BENEFIT_TYPE = "SL"
SL_SUPPRESSION_REASON = "Issue #27"

AUDIT_COLUMNS = [
    "POLICY_NUMBER",
    "QLA_POLICY_NUMBER",
    "BENEFIT_SEQ",
    "PLAN",
    "FACE_AMOUNT",
    "PREMIUM",
    "SL_TABLE_CODE",
    "SUPPRESSION_REASON",
]


def default_audit_path() -> Path:
    """Repository-relative path for the SL suppression audit CSV."""
    root = Path(__file__).resolve().parents[1]
    return root / "Issue_Log_Items" / "Issue_27" / "Issue_27_SL_Suppression_Audit.csv"


def resolve_ppbentyp_path(src_dir: str) -> str:
    """Resolve LifePRO PPBENTYP extract (BenefitType) for SL table code lookup."""
    if not src_dir:
        return ""
    try:
        from qla_core.lifepro_source_resolver import find_newest_matching

        path = find_newest_matching(
            src_dir, [r"^PPBENTYP[_ ]BenefitType[_ ]Extract.*\.csv$"]
        )
        if path:
            return path
    except Exception:
        pass
    legacy = os.path.join(src_dir, "PPBENTYP.csv")
    return legacy if os.path.isfile(legacy) else ""


def load_sl_table_code_cache(
    ppbentyp_path: str,
    normalize_fn: Callable[[str], str] | None = None,
) -> dict[tuple[str, str], str]:
    """Load PPBENTYP SL_TABLE_CODE keyed by (normalized policy, benefit seq)."""
    cache: dict[tuple[str, str], str] = {}
    if not ppbentyp_path or not os.path.isfile(ppbentyp_path):
        return cache
    norm = normalize_fn or (lambda x: str(x).strip())
    try:
        df = pd.read_csv(
            ppbentyp_path, encoding="latin1", low_memory=False, dtype=str, on_bad_lines="skip"
        ).fillna("")
        df.columns = [str(c).strip().upper() for c in df.columns]
        if "POLICY_NUMBER" not in df.columns or "BENEFIT_SEQ" not in df.columns:
            return cache
        code_col = "SL_TABLE_CODE" if "SL_TABLE_CODE" in df.columns else None
        if not code_col:
            return cache
        type_col = "TYPE_CODE" if "TYPE_CODE" in df.columns else None
        for _, r in df.iterrows():
            if type_col and str(r.get(type_col, "")).strip().upper() not in ("", "SL"):
                continue
            pol_raw = str(r.get("POLICY_NUMBER", "")).strip()
            pol = norm(pol_raw)
            seq = str(r.get("BENEFIT_SEQ", "")).strip().replace(".0", "")
            code = str(r.get(code_col, "")).strip()
            if pol and seq and code:
                cache[(pol, seq)] = code
                if pol_raw and pol_raw != pol:
                    cache[(pol_raw, seq)] = code
    except Exception:
        return cache
    return cache


def _face_amount(units: str, vpu: str) -> str:
    try:
        u = float(str(units).strip() or 0)
        v = float(str(vpu).strip() or 0)
        return f"{round(u * v, 2):.2f}"
    except (ValueError, TypeError):
        return "0.00"


def build_sl_suppression_audit_rows(
    sl_source: pd.DataFrame,
    *,
    sl_table_cache: dict[tuple[str, str], str] | None = None,
    cw_map: dict[str, str] | None = None,
    normalize_fn: Callable[[str], str] | None = None,
) -> list[dict[str, str]]:
    """Build audit records for each SL row before quikridr suppression."""
    if sl_source is None or sl_source.empty:
        return []
    norm = normalize_fn or (lambda x: str(x).strip())
    cw = cw_map or {}
    table_cache = sl_table_cache or {}
    rows: list[dict[str, str]] = []
    for _, r in sl_source.iterrows():
        lp = norm(r.get("POLICY_NUMBER", ""))
        seq = str(r.get("BENEFIT_SEQ", "")).strip().replace(".0", "")
        qla = cw.get(lp, lp)
        table_code = table_cache.get((lp, seq), table_cache.get((str(r.get("POLICY_NUMBER", "")).strip(), seq), ""))
        rows.append(
            {
                "POLICY_NUMBER": lp,
                "QLA_POLICY_NUMBER": qla,
                "BENEFIT_SEQ": seq,
                "PLAN": str(r.get("PLAN_CODE", "")).strip(),
                "FACE_AMOUNT": _face_amount(r.get("NUMBER_OF_UNITS", ""), r.get("VALUE_PER_UNIT", "")),
                "PREMIUM": str(r.get("MODE_PREMIUM", "")).strip(),
                "SL_TABLE_CODE": table_code,
                "SUPPRESSION_REASON": SL_SUPPRESSION_REASON,
            }
        )
    return rows


def write_sl_suppression_audit(
    audit_rows: list[dict[str, str]],
    audit_path: Path | str | None = None,
) -> str:
    """Write suppression audit CSV; returns absolute path string."""
    path = Path(audit_path) if audit_path else default_audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(audit_rows, columns=AUDIT_COLUMNS)
    df.to_csv(path, index=False, encoding="latin1")
    return str(path.resolve())
