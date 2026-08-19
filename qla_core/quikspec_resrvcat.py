"""Issue 141: quikspec.RESRVCAT from PCOVR.PRODUCT_TYPE via PPBEN BENEFIT_SEQ=1.

Do not copy quikplan.PRODUCT (ISWL overlay is ISWLFE). Traditional seq-1 is BA;
ISWL seq-1 is BF. Emit PRODUCT_TYPE as-is (including L).
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from qla_core.lifepro_source_resolver import resolve_table_source
from qla_core.normalize_utils import format_qladmin_mpolicy, normalize

RESRVCAT_FIELD = "RESRVCAT"


def _iter_extract_rows(path: str) -> Iterable[dict[str, str]]:
    with Path(path).open(newline="", encoding="latin1", errors="replace") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            return
        cols = {str(c).replace("\ufeff", "").strip().upper(): c for c in reader.fieldnames}
        for row in reader:
            first_vals = [str(row.get(reader.fieldnames[i], "") or "") for i in range(min(3, len(reader.fieldnames)))]
            if any("---" in v for v in first_vals):
                continue
            yield {k: str(row.get(src, "") or "") for k, src in cols.items()}


def _compact(val: str) -> str:
    return " ".join(normalize(val).split())


def _policy_lookup_keys(pol: str) -> list[str]:
    """Match Output MPOLICY (often stripped) and format_qladmin_mpolicy keys."""
    raw = str(pol or "").strip()
    n = normalize(raw)
    keys: list[str] = []
    for item in (
        raw,
        n,
        n + "C" if n and not n.endswith("C") else "",
        format_qladmin_mpolicy(n[:-1] if n.endswith("C") else n),
        format_qladmin_mpolicy(n[:-1] if n.endswith("C") else n).strip(),
        format_qladmin_mpolicy(n),
        format_qladmin_mpolicy(n).strip(),
    ):
        if item and item not in keys:
            keys.append(item)
    return keys


def load_pcovr_product_types(src_dir: str) -> dict[str, str]:
    path, _label = resolve_table_source(src_dir, "quikplan")
    if not path or not Path(path).is_file():
        raise FileNotFoundError(f"PCOVR extract not found under {src_dir}")
    out: dict[str, str] = {}
    saw_cov = False
    saw_pt = False
    for row in _iter_extract_rows(path):
        if "COVERAGE_ID" in row:
            saw_cov = True
        if "PRODUCT_TYPE" in row:
            saw_pt = True
        cov = _compact(row.get("COVERAGE_ID", ""))
        if not cov or set(cov) <= set("-"):
            continue
        pt = str(row.get("PRODUCT_TYPE", "") or "").strip()
        if cov not in out:
            out[cov] = pt
    if not saw_cov or not saw_pt:
        raise ValueError(f"PCOVR missing COVERAGE_ID/PRODUCT_TYPE: {path}")
    return out


def load_ppben_seq1_plans(src_dir: str) -> dict[str, str]:
    path, _label = resolve_table_source(src_dir, "quikridr")
    if not path or not Path(path).is_file():
        raise FileNotFoundError(f"PPBEN extract not found under {src_dir}")
    out: dict[str, str] = {}
    saw = set()
    for row in _iter_extract_rows(path):
        saw.update(row.keys())
        seq = str(row.get("BENEFIT_SEQ", "") or "").strip()
        if seq not in ("1", "1.0"):
            continue
        pol = normalize(row.get("POLICY_NUMBER", ""))
        if not pol or set(pol) <= set("-"):
            continue
        plan = _compact(row.get("PLAN_CODE", ""))
        for key in _policy_lookup_keys(pol):
            if key not in out:
                out[key] = plan
    needed = {"POLICY_NUMBER", "BENEFIT_SEQ", "PLAN_CODE"}
    if not needed.issubset(saw):
        raise ValueError(f"PPBEN missing {needed - saw}: {path}")
    return out


def apply_quikspec_resrvcat(
    df: pd.DataFrame,
    src_dir: str,
    log=None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fill RESRVCAT on an already-mapped quikspec frame. Other columns unchanged."""
    stats = {"filled": 0, "blank": 0, "rows": 0, "source_dir": str(src_dir)}
    if df is None or df.empty:
        return df, stats
    out = df.copy()
    if RESRVCAT_FIELD not in out.columns:
        out[RESRVCAT_FIELD] = ""
    cov_pt = load_pcovr_product_types(src_dir)
    seq1 = load_ppben_seq1_plans(src_dir)
    for idx in out.index:
        stats["rows"] += 1
        mpolicy = str(out.at[idx, "MPOLICY"] if "MPOLICY" in out.columns else "").strip()
        plan = ""
        for key in _policy_lookup_keys(mpolicy):
            if key in seq1:
                plan = seq1[key]
                break
        pt = cov_pt.get(plan, "") if plan else ""
        out.at[idx, RESRVCAT_FIELD] = pt
        if pt:
            stats["filled"] += 1
        else:
            stats["blank"] += 1
    if log is not None:
        try:
            log(
                f"Issue 141: RESRVCAT filled={stats['filled']} "
                f"blank={stats['blank']} rows={stats['rows']}"
            )
        except Exception:
            pass
    return out, stats
