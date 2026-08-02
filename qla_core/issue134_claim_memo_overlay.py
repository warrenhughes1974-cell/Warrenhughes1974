"""Issue #134 — overlay PNOTE FILE_TYPE=B notes onto quikclms.MEMOTEXT (Claims Tab).

Runs after Issue #79 CLAIMSTAT remap (and other post-emit steps that read lineage
from MEMOTEXT). Does not invent claim rows. Does not touch quikclmp or money fields.
"""

from __future__ import annotations

import os
from typing import Any

import pandas as pd

from qla_core.normalize_utils import format_qladmin_mpolicy
from qla_core.quikmemo_converter import (
    MEMO_SEGMENT_SEPARATOR,
    PNOTE_LINE_COLS,
    _is_blank_text,
    _pnote_sort_key,
    _read_pnote_csv,
    _strip,
    _text_blob,
    format_pnote_b_claim_memotext,
)

# Issue #135 header-only marker — preserve when replacing MEMOTEXT with PNOTE-B
_CSO_NO_PACTG_MARKER = "CSO_CONTROLLED_NO_PACTG_HISTORY"


def _preserve_cso_no_pactg_marker(old_memo: str, new_memo: str) -> str:
    old = _strip(old_memo)
    new = _strip(new_memo)
    if _CSO_NO_PACTG_MARKER in old and _CSO_NO_PACTG_MARKER not in new:
        if new:
            return f"{new}\n---\n{_CSO_NO_PACTG_MARKER}"
        return _CSO_NO_PACTG_MARKER
    return new_memo


def _is_death_claim_row(row: pd.Series) -> bool:
    """Identify life death-claim headers without requiring health QuikHcmm."""
    memo = _strip(row.get("MEMOTEXT", ""))
    if "DEATH_CLAIM" in memo:
        return True
    if "[PNOTE-B]" in memo:
        return True
    # Post-#79: death claims use CLAIMSTAT 1 (open) or 2 (paid in full)
    if _strip(row.get("CLAIMSTAT", "")) in ("1", "2"):
        return True
    return False


def _sort_key_tuple(row: pd.Series) -> tuple:
    return _pnote_sort_key(row)


def load_pnote_b_memos_by_mpolicy(pnote_path: str) -> dict[str, str]:
    """Return {MPOLICY: merged [PNOTE-B] text} for non-blank FILE_TYPE=B rows."""
    pnote = _read_pnote_csv(pnote_path)
    buckets: dict[str, list[tuple[tuple, str]]] = {}
    for _, row in pnote.iterrows():
        if _strip(row.get("FILE_TYPE", "")).upper() != "B":
            continue
        text = _text_blob(row, PNOTE_LINE_COLS)
        if _is_blank_text(text):
            continue
        lp = _strip(row.get("POLICY_NUMBER", ""))
        if not lp:
            continue
        mpolicy = format_qladmin_mpolicy(lp)
        if not mpolicy:
            continue
        buckets.setdefault(mpolicy, []).append((_sort_key_tuple(row), format_pnote_b_claim_memotext(row)))

    merged: dict[str, str] = {}
    for mpolicy, items in buckets.items():
        # Newest first (same direction as quikmemo segment sort)
        items.sort(key=lambda x: x[0], reverse=True)
        merged[mpolicy] = MEMO_SEGMENT_SEPARATOR.join(t for _, t in items)
    return merged


def apply_issue134_claim_memos(
    clms_df: pd.DataFrame,
    pnote_path: str,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """
    Replace MEMOTEXT on death-claim quikclms rows when PNOTE B notes exist.

    Returns (updated_clms, orphan_audit_df, stats).
    """
    stats: dict[str, Any] = {
        "pnote_b_policies": 0,
        "rows_updated": 0,
        "policies_updated": 0,
        "orphan_b_policies": 0,
        "death_rows_seen": 0,
    }
    if not pnote_path or not os.path.isfile(pnote_path):
        stats["reason"] = "missing_pnote"
        return clms_df, pd.DataFrame(), stats

    b_memos = load_pnote_b_memos_by_mpolicy(pnote_path)
    stats["pnote_b_policies"] = len(b_memos)

    clms = clms_df.copy().fillna("")
    if "MEMOTEXT" not in clms.columns or "MPOLICY" not in clms.columns:
        stats["reason"] = "missing_columns"
        return clms, pd.DataFrame(), stats

    death_mask = clms.apply(_is_death_claim_row, axis=1)
    stats["death_rows_seen"] = int(death_mask.sum())
    death_policies = set(clms.loc[death_mask, "MPOLICY"].astype(str).str.strip())

    orphan_rows: list[dict[str, str]] = []
    for mpolicy in sorted(b_memos.keys()):
        if mpolicy not in death_policies:
            orphan_rows.append(
                {
                    "MPOLICY": mpolicy,
                    "REASON": "no_death_claim_row",
                }
            )
    stats["orphan_b_policies"] = len(orphan_rows)

    updated_policies: set[str] = set()
    new_memos: list[str] = []
    for _, row in clms.iterrows():
        mpolicy = _strip(row.get("MPOLICY", ""))
        memo = _strip(row.get("MEMOTEXT", ""))
        if mpolicy in b_memos and _is_death_claim_row(row):
            new_text = _preserve_cso_no_pactg_marker(memo, b_memos[mpolicy])
            if memo != new_text:
                stats["rows_updated"] += 1
                updated_policies.add(mpolicy)
            new_memos.append(new_text)
        else:
            new_memos.append(row.get("MEMOTEXT", ""))

    clms["MEMOTEXT"] = new_memos
    stats["policies_updated"] = len(updated_policies)
    orphan_df = pd.DataFrame(orphan_rows)
    return clms, orphan_df, stats


def write_issue134_orphan_audit(orphan_df: pd.DataFrame, reports_dir: str) -> str:
    os.makedirs(reports_dir, exist_ok=True)
    path = os.path.normpath(os.path.join(reports_dir, "issue134_pnote_b_orphan_audit.csv"))
    orphan_df.to_csv(path, index=False, encoding="utf-8")
    return path
