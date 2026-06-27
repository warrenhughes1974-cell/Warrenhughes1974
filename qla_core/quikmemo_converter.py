"""Issue 21M — QUIKMEMO from LifePRO PNOTE + PENSE dual-source merge."""

from __future__ import annotations

import hashlib
from typing import Any

import pandas as pd

from qla_core.normalize_utils import format_qladmin_mpolicy

QUIKMEMO_SCHEMA = ["MEMOKEY", "MEMOTEXT"]

# Issue 21M-FU: one QUIKMEMO row per MEMOKEY (production grain)
MEMO_SEGMENT_SEPARATOR = "\n---\n"

PNOTE_LINE_COLS = ["LINE_1", "LINE_2", "LINE_3", "LINE_4"]
PENSE_LINE_COLS = ["LINE_1", "LINE_2", "LINE_3"]


def _read_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", low_memory=False, on_bad_lines="skip").fillna("")
    df.columns = [str(c).replace("\ufeff", "").strip().upper() for c in df.columns]
    if len(df) and df.iloc[0].astype(str).str.contains("---").any():
        df = df.iloc[1:].reset_index(drop=True)
    return df


def _strip(val: Any) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return str(val).strip()


def _text_blob(row: pd.Series, cols: list[str]) -> str:
    parts = [_strip(row.get(c, "")) for c in cols]
    return "\n".join(p for p in parts if p)


def _is_blank_text(text: str) -> bool:
    return not text or not text.strip()


def _parse_pnote_date(raw: str) -> tuple[str, str]:
    """Return (display_date, user_or_nameid). MMDDYYYY -> YYYY-MM-DD; else raw is user."""
    raw = _strip(raw)
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[4:8]}-{raw[0:2]}-{raw[2:4]}", ""
    return raw if raw else "", raw


def _parse_pense_date(raw: str) -> str:
    raw = _strip(raw)
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw


def _format_time_hhmmss(raw: str) -> str:
    raw = _strip(raw)
    if len(raw) == 6 and raw.isdigit():
        return f"{raw[0:2]}:{raw[2:4]}:{raw[4:6]}"
    return raw


def _sort_int(raw: str) -> int:
    raw = _strip(raw)
    if raw.isdigit():
        return int(raw)
    try:
        return int(float(raw))
    except (ValueError, TypeError):
        return 0


def _format_pnote_memotext(row: pd.Series) -> str:
    date_disp, user_from_nameid = _parse_pnote_date(row.get("DATE_OR_NAMEID", ""))
    time_disp = _format_time_hhmmss(row.get("TIME_OR_UW_REQ_SEQ", ""))
    ben_seq = _strip(row.get("BENEFIT_SEQ", ""))
    seq = _strip(row.get("RECORD_SEQ", ""))
    user = user_from_nameid or "-"
    lines = [
        "[PNOTE]",
        f"Date: {date_disp}",
        f"Time: {time_disp}",
        f"User: {user}",
    ]
    if seq:
        lines.append(f"Seq: {seq}")
    if ben_seq:
        lines.append(f"BenSeq: {ben_seq}")
    body = _text_blob(row, PNOTE_LINE_COLS)
    if body:
        lines.append(body)
    return "\n".join(lines)


def _format_pense_memotext(row: pd.Series) -> str:
    date_disp = _parse_pense_date(row.get("EVENT_DATE", ""))
    time_disp = "-"
    event = _strip(row.get("EVENT_CODE", ""))
    user = _strip(row.get("ORG_OPER_ID", "")) or "-"
    seq = _strip(row.get("EVENT_SEQUENCE", ""))
    lines = [
        "[ENS]",
        f"Date: {date_disp}",
        f"Time: {time_disp}",
        f"Event: {event}",
        f"User: {user}",
    ]
    if seq:
        lines.append(f"Seq: {seq}")
    body = _text_blob(row, PENSE_LINE_COLS)
    if body:
        lines.append(body)
    return "\n".join(lines)


def _exact_dup_key(source: str, lp: str, row: pd.Series, text: str, kind: str) -> str:
    if kind == "PNOTE":
        parts = [
            source, lp,
            _strip(row.get("DATE_OR_NAMEID", "")),
            _strip(row.get("TIME_OR_UW_REQ_SEQ", "")),
            _strip(row.get("RECORD_SEQ", "")),
            text,
        ]
    else:
        parts = [
            source, lp,
            _strip(row.get("EVENT_DATE", "")),
            _strip(row.get("EVENT_SEQUENCE", "")),
            text,
        ]
    return hashlib.md5("|".join(parts).encode()).hexdigest()


def _pnote_sort_key(row: pd.Series) -> tuple[int, int, int]:
    raw_date = _strip(row.get("DATE_OR_NAMEID", ""))
    date_int = _sort_int(raw_date[4:8] + raw_date[0:4] if len(raw_date) == 8 and raw_date.isdigit() else raw_date)
    return (date_int, _sort_int(row.get("TIME_OR_UW_REQ_SEQ", "")), _sort_int(row.get("RECORD_SEQ", "")))


def _pense_sort_key(row: pd.Series) -> tuple[int, int]:
    return (_sort_int(row.get("EVENT_DATE", "")), _sort_int(row.get("EVENT_SEQUENCE", "")))


def _merge_segments_by_memokey(memo_df: pd.DataFrame) -> pd.DataFrame:
    """Collapse sorted segments to one row per MEMOKEY (Issue 21M-FU)."""
    merged_rows: list[dict[str, str]] = []
    for memokey, group in memo_df.groupby("MEMOKEY", sort=False):
        merged_rows.append({
            "MEMOKEY": memokey,
            "MEMOTEXT": MEMO_SEGMENT_SEPARATOR.join(group["MEMOTEXT"].tolist()),
        })
    return pd.DataFrame(merged_rows, columns=QUIKMEMO_SCHEMA)


def convert_quikmemo_from_pnote_pense(
    pnote_path: str | None,
    pense_path: str | None,
    cw_map: dict[str, str],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """
    Merge PNOTE + PENSE into QUIKMEMO rows.

    Returns (output_df, orphan_log_df, stats).
    """
    stats: dict[str, Any] = {
        "pnote_source_rows": 0,
        "pense_source_rows": 0,
        "skipped_blank_pnote": 0,
        "skipped_blank_pense": 0,
        "skipped_non_p_ens": 0,
        "skipped_orphan": 0,
        "skipped_exact_dup": 0,
        "emitted_pnote": 0,
        "emitted_pense": 0,
        "segment_rows": 0,
        "emitted_rows": 0,
    }
    orphan_rows: list[dict[str, str]] = []
    memo_records: list[dict[str, Any]] = []
    seen_exact: set[str] = set()

    def _emit(source: str, lp: str, row: pd.Series, memotext: str, sort_key: tuple, src_order: int) -> None:
        nonlocal stats
        qla = cw_map.get(lp, "")
        if not qla:
            stats["skipped_orphan"] += 1
            orphan_rows.append({
                "SOURCE": source,
                "LP": lp,
                "REASON": "no_crosswalk",
            })
            return
        dup_key = _exact_dup_key(source, lp, row, memotext, source)
        if dup_key in seen_exact:
            stats["skipped_exact_dup"] += 1
            return
        seen_exact.add(dup_key)
        memokey = format_qladmin_mpolicy(qla)
        memo_records.append({
            "MEMOKEY": memokey,
            "MEMOTEXT": memotext,
            "_sort_a": sort_key[0] if len(sort_key) > 0 else 0,
            "_sort_b": sort_key[1] if len(sort_key) > 1 else 0,
            "_sort_c": sort_key[2] if len(sort_key) > 2 else 0,
            "_src_order": src_order,
            "_source": source,
        })
        if source == "PNOTE":
            stats["emitted_pnote"] += 1
        else:
            stats["emitted_pense"] += 1

    if pnote_path:
        pnote = _read_csv(pnote_path)
        stats["pnote_source_rows"] = len(pnote)
        for _, row in pnote.iterrows():
            text = _text_blob(row, PNOTE_LINE_COLS)
            if _is_blank_text(text):
                stats["skipped_blank_pnote"] += 1
                continue
            lp = _strip(row.get("POLICY_NUMBER", ""))
            if not lp:
                stats["skipped_blank_pnote"] += 1
                continue
            memotext = _format_pnote_memotext(row)
            _emit("PNOTE", lp, row, memotext, _pnote_sort_key(row), 0)

    if pense_path:
        pense = _read_csv(pense_path)
        stats["pense_source_rows"] = len(pense)
        for _, row in pense.iterrows():
            ens_type = _strip(row.get("ENS_KEY_TYPE", "")).upper()
            if ens_type != "P":
                stats["skipped_non_p_ens"] += 1
                continue
            text = _text_blob(row, PENSE_LINE_COLS)
            if _is_blank_text(text):
                stats["skipped_blank_pense"] += 1
                continue
            lp = _strip(row.get("POLICY_NUMBER", ""))
            if not lp:
                stats["skipped_blank_pense"] += 1
                continue
            memotext = _format_pense_memotext(row)
            _emit("PENSE", lp, row, memotext, _pense_sort_key(row), 1)

    if not memo_records:
        out = pd.DataFrame(columns=QUIKMEMO_SCHEMA)
        orphan_df = pd.DataFrame(orphan_rows)
        stats["emitted_rows"] = 0
        return out, orphan_df, stats

    memo_df = pd.DataFrame(memo_records)
    memo_df = memo_df.sort_values(
        ["MEMOKEY", "_sort_a", "_sort_b", "_sort_c", "_src_order"],
        ascending=[True, False, False, False, True],
    )

    stats["segment_rows"] = len(memo_df)
    out = _merge_segments_by_memokey(memo_df)
    stats["emitted_rows"] = len(out)
    orphan_df = pd.DataFrame(orphan_rows)
    return out, orphan_df, stats
