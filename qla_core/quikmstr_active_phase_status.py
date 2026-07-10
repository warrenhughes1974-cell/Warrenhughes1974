"""
Issue #49 — QuikMstr active-phase status selection.

QLAdmin manual: status 0–49 = active; status >= 50 = inactive.

When the first phase display status is inactive (>= 50) and a later phase is
active (0–49), quikmstr.MSTATUS uses that first later active phase status.
Otherwise the provisional Issue #13 / ST_* MSTATUS is preserved.

Display status for phase 1 mirrors the existing phase-1 MPHSTAT inherit rule
(app.py BASE PHASE TERMINAL STATUS SYNCHRONIZATION): if provisional MSTATUS is
not in {"", "11", "22", "ACTIVE"}, phase 1 displays provisional MSTATUS;
later phases use bare-letter STATUS_CODE translation only.
"""

from __future__ import annotations

import os
from typing import Callable, Dict, List, Optional, Sequence, Tuple

# Mirror app.py phase-1 inherit block list (do not widen to full 0–49 here).
PHASE1_INHERIT_BLOCK = frozenset({"", "11", "22", "ACTIVE"})

PhaseRow = Tuple[int, int, str]  # (benefit_seq, source_row_order, status_code)


def parse_status_int(raw) -> Optional[int]:
    """Return integer status or None if blank/nonnumeric."""
    s = str(raw or "").strip().upper()
    if s.endswith(".0") and s[:-2].replace("-", "").isdigit():
        s = s[:-2]
    if not s or s in {"NAN", "NONE", "NULL"}:
        return None
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def is_active_status(status_num: Optional[int]) -> bool:
    """QLAdmin manual: 0 through 49 inclusive are active."""
    return status_num is not None and 0 <= status_num <= 49


def is_inactive_status(status_num: Optional[int]) -> bool:
    """QLAdmin manual: 50 and above are inactive."""
    return status_num is not None and status_num >= 50


def translate_phase_status_code(status_code: str, bare_status_map: Dict[str, str]) -> str:
    """Apply bare-letter MPHSTAT-style translation (no ST_ prefix)."""
    code = str(status_code or "").strip().upper()
    if code.endswith(".0"):
        code = code[:-2]
    if not code or code in {"NAN", "NONE", "NULL"} or set(code) <= {"-"}:
        return ""
    mapped = bare_status_map.get(code, "")
    if mapped:
        return str(mapped).strip()
    # Already numeric?
    if parse_status_int(code) is not None:
        return str(parse_status_int(code))
    return code


def simulate_display_phase_statuses(
    provisional_mstatus: str,
    phases: Sequence[PhaseRow],
    bare_status_map: Dict[str, str],
) -> List[str]:
    """
    Build ordered display statuses for phases.

    phases: sorted (benefit_seq, row_order, STATUS_CODE) ascending.
    """
    provisional = str(provisional_mstatus or "").strip().upper()
    if provisional.endswith(".0"):
        provisional = provisional[:-2]

    display: List[str] = []
    for idx, (_seq, _ord, status_code) in enumerate(phases):
        translated = translate_phase_status_code(status_code, bare_status_map)
        if idx == 0:
            if provisional not in PHASE1_INHERIT_BLOCK and parse_status_int(provisional) is not None:
                display.append(provisional)
            else:
                display.append(translated)
        else:
            display.append(translated)
    return display


def select_mstatus_from_active_phase(
    provisional_mstatus: str,
    phases: Sequence[PhaseRow],
    bare_status_map: Dict[str, str],
) -> Tuple[str, bool]:
    """
    Return (final_mstatus, overridden).

    If first display phase is inactive (>=50), use first later active (0–49).
    Otherwise preserve provisional_mstatus.
    """
    provisional = str(provisional_mstatus or "").strip()
    if provisional.endswith(".0") and provisional[:-2].replace("-", "").isdigit():
        provisional = provisional[:-2]

    if not phases:
        return provisional, False

    display = simulate_display_phase_statuses(provisional, phases, bare_status_map)
    first_num = parse_status_int(display[0]) if display else None
    if not is_inactive_status(first_num):
        return provisional, False

    for status in display[1:]:
        n = parse_status_int(status)
        if is_active_status(n):
            return str(n), True

    return provisional, False


def build_ppben_phase_cache(
    ppben_path: str,
    normalize_fn: Callable[[str], str],
) -> Dict[str, List[PhaseRow]]:
    """
    Map normalized LifePRO POLICY_NUMBER -> ordered phase rows
    (benefit_seq, source_row_order, STATUS_CODE).

    Aligns with quikridr emit filters: drop BENEFIT_TYPE UV/FV/SL and
    non-numeric / <1 BENEFIT_SEQ so selection matches QLAdmin phases.
    """
    import pandas as pd

    if not ppben_path or not os.path.exists(ppben_path):
        return {}

    df = pd.read_csv(
        ppben_path, encoding="latin1", low_memory=False, dtype=str, on_bad_lines="skip"
    ).fillna("")
    df.columns = [str(c).strip().upper() for c in df.columns]
    if "POLICY_NUMBER" not in df.columns or "BENEFIT_SEQ" not in df.columns:
        return {}
    if "STATUS_CODE" not in df.columns:
        return {}

    # Drop separator / junk rows
    df = df[~df.iloc[:, 0].astype(str).str.contains("---", regex=False)]

    # Match quikridr BENEFIT_TYPE filter (app.py QUIKRIDR BENEFIT TYPE FILTER)
    if "BENEFIT_TYPE" in df.columns:
        bt = df["BENEFIT_TYPE"].astype(str).str.strip().str.upper()
        df = df[~bt.isin(["UV", "FV", "SL"])]

    cache: Dict[str, List[PhaseRow]] = {}
    for row_ord, (_, row) in enumerate(df.iterrows()):
        pol = normalize_fn(row.get("POLICY_NUMBER", ""))
        if not pol:
            continue
        seq_raw = str(row.get("BENEFIT_SEQ", "")).strip()
        if seq_raw.endswith(".0"):
            seq_raw = seq_raw[:-2]
        if not seq_raw.isdigit() or int(seq_raw) < 1:
            continue
        seq = int(seq_raw)
        status_code = str(row.get("STATUS_CODE", "")).strip()
        cache.setdefault(pol, []).append((seq, row_ord, status_code))

    for pol, rows in cache.items():
        rows.sort(key=lambda t: (t[0], t[1]))
    return cache


def bare_status_map_from_trans_map(trans_map: Dict[str, str]) -> Dict[str, str]:
    """
    Extract letter->numeric status entries used for MPHSTAT (no ST_ prefix).

    Prefer short alphabetic keys that map to numeric results.
    """
    out: Dict[str, str] = {}
    for k, v in (trans_map or {}).items():
        key = str(k or "").strip().upper()
        val = str(v or "").strip()
        if not key or key.startswith(("ST_", "BF_", "PM_", "DV_", "NF_", "AG_", "PAR_")):
            continue
        if parse_status_int(val) is None:
            continue
        # Single-letter / short status codes (A, T, P, …)
        if len(key) <= 3 and key.isalpha():
            out[key] = str(parse_status_int(val))
    # Ensure common defaults if translation file incomplete
    defaults = {"A": "22", "T": "56", "P": "41", "S": "55", "D": "53", "L": "54", "W": "32", "I": "10"}
    for k, v in defaults.items():
        out.setdefault(k, v)
    return out
