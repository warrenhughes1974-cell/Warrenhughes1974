"""Generate QUIKMEMO DBF + FPT from emitted quikmemo.csv (Issue 21M)."""

from __future__ import annotations

import os
from typing import Any

import dbf
import pandas as pd

QUIKMEMO_DBF_LAYOUT = [
    {"field": "MEMOKEY", "type": "CHARACTER", "length": 10, "decimals": 0},
    {"field": "MEMOTEXT", "type": "MEMO", "length": 10, "decimals": 0},
]


def _strip_val(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value)


def layout_to_dbf_spec(layout: list[dict]) -> str:
    parts = []
    for fld in layout:
        name = fld["field"]
        ftype = fld["type"].upper()
        length = int(fld.get("length", 10))
        decimals = int(fld.get("decimals", 0))
        if ftype == "CHARACTER":
            parts.append(f"{name} C({length})")
        elif ftype == "NUMERIC":
            parts.append(f"{name} N({length},{decimals})")
        elif ftype == "MEMO":
            parts.append(f"{name} M")
        else:
            parts.append(f"{name} C({length})")
    return "; ".join(parts)


def _memokey_for_dbf(raw: Any, length: int = 10) -> str | None:
    """Preserve Issue #25 left-padding — do not strip MEMOKEY."""
    s = _strip_val(raw)
    if not s:
        return None
    if len(s) > length:
        return s[:length]
    if len(s) < length:
        return s.ljust(length)
    return s


def _rewrite_dbf_memokey_bytes(dbf_path: str, memokeys: list[str], length: int = 10) -> int:
    """
    Issue #50 UAT: Python `dbf` library strips leading spaces on CHARACTER append,
    storing right-padded keys (e.g. b'018495BC  '). QLAdmin SEEK uses left-padded
    MPOLICY (e.g. b'  018495BC') → Memo tab blank. Patch MEMOKEY bytes after write.
    """
    import struct

    with open(dbf_path, "rb") as f:
        data = bytearray(f.read())
    header_len = struct.unpack_from("<H", data, 8)[0]
    rec_len = struct.unpack_from("<H", data, 10)[0]
    num_recs = struct.unpack_from("<I", data, 4)[0]
    if num_recs != len(memokeys):
        raise ValueError(
            f"MEMOKEY rewrite count mismatch: dbf={num_recs} csv={len(memokeys)}"
        )
    for i, key in enumerate(memokeys):
        raw = key.encode("latin-1", errors="replace")
        if len(raw) > length:
            raw = raw[:length]
        elif len(raw) < length:
            raw = raw.ljust(length)
        off = header_len + i * rec_len + 1  # skip delete flag
        data[off : off + length] = raw
    with open(dbf_path, "wb") as f:
        f.write(data)
    return num_recs


def csv_row_to_dbf_values(row: pd.Series, layout: list[dict]) -> tuple:
    values = []
    for fld in layout:
        name = fld["field"]
        ftype = fld["type"].upper()
        raw = row.get(name, row.get(name.lower(), ""))
        if ftype == "CHARACTER":
            if name == "MEMOKEY":
                val = _memokey_for_dbf(raw, int(fld.get("length", 10)))
            else:
                s = _strip_val(raw)
                val = s[: int(fld.get("length", 10))] if s else None
        elif ftype == "MEMO":
            s = _strip_val(raw)
            val = s if s else None
        else:
            s = _strip_val(raw)
            val = s[: int(fld.get("length", 10))] if s else None
        values.append(val)
    return tuple(values)


def write_quikmemo_dbf(csv_path: str, dbf_path: str) -> dict[str, Any]:
    """Write QUIKMEMO DBF (+ FPT sidecar) from quikmemo.csv. Returns summary dict."""
    df = pd.read_csv(csv_path, dtype=str).fillna("")
    df.columns = [str(c).strip().upper() for c in df.columns]
    missing = [f["field"] for f in QUIKMEMO_DBF_LAYOUT if f["field"] not in df.columns]
    if missing:
        raise ValueError(f"quikmemo.csv missing columns {missing}")

    row_values = [csv_row_to_dbf_values(row, QUIKMEMO_DBF_LAYOUT) for _, row in df.iterrows()]
    spec = layout_to_dbf_spec(QUIKMEMO_DBF_LAYOUT)
    if os.path.exists(dbf_path):
        os.remove(dbf_path)
    fpt_path = os.path.splitext(dbf_path)[0] + ".fpt"
    dbt_path = os.path.splitext(dbf_path)[0] + ".dbt"
    for sidecar in (fpt_path, dbf_path + "t", dbt_path):
        if os.path.isfile(sidecar):
            os.remove(sidecar)

    table = dbf.Table(dbf_path, spec)
    table.open(mode=dbf.READ_WRITE)
    for vals in row_values:
        table.append(vals)
    table.close()

    # Preserve Issue #25 left-padded MEMOKEY bytes (dbf lib right-pads / strips lead spaces)
    memokeys = [_memokey_for_dbf(row.get("MEMOKEY", ""), 10) or "" for _, row in df.iterrows()]
    _rewrite_dbf_memokey_bytes(dbf_path, memokeys, 10)

    sidecar_written = (
        os.path.isfile(fpt_path)
        or os.path.isfile(dbf_path + "t")
        or os.path.isfile(dbt_path)
    )

    return {
        "csv_rows": len(df),
        "dbf_rows": len(row_values),
        "dbf_path": dbf_path,
        "memo_sidecar": dbt_path if os.path.isfile(dbt_path) else (fpt_path if os.path.isfile(fpt_path) else ""),
        "fpt_exists": sidecar_written,
    }
