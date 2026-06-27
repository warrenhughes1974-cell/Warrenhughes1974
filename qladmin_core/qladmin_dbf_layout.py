"""Shared DBF layout helpers for QLAdmin Core (Issue 21K)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import dbf
import pandas as pd


def layout_to_dbf_spec(layout: list[dict[str, Any]]) -> str:
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
        elif ftype == "DATE":
            parts.append(f"{name} D")
        elif ftype == "LOGICAL":
            parts.append(f"{name} L")
        elif ftype == "MEMO":
            parts.append(f"{name} M")
        else:
            parts.append(f"{name} C({length})")
    return "; ".join(parts)


def _strip_val(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def _parse_date(value: Any) -> date | None:
    s = _strip_val(value)
    if not s or s.lower() in {"nan", "none", "null", "0"}:
        return None
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"):
        try:
            dt = datetime.strptime(s[:10], fmt)
            return date(dt.year, dt.month, dt.day)
        except ValueError:
            continue
    digits = "".join(ch for ch in s if ch.isdigit())
    if len(digits) >= 8:
        try:
            dt = datetime.strptime(digits[:8], "%Y%m%d")
            return date(dt.year, dt.month, dt.day)
        except ValueError:
            pass
    return None


def csv_value_for_field(raw: Any, fld: dict[str, Any], *, preserve_mpolicy_padding: bool = False) -> Any:
    """Coerce CSV string to Python value for dbf append."""
    ftype = fld["type"].upper()
    name = fld["field"]
    raw_s = _strip_val(raw)

    if ftype == "CHARACTER":
        if not raw_s:
            return None
        length = int(fld.get("length", 10))
        if preserve_mpolicy_padding and name == "MPOLICY":
            return raw_s if len(raw_s) <= length else raw_s[:length]
        return raw_s[:length]

    if ftype == "DATE":
        return _parse_date(raw_s)

    if ftype == "NUMERIC":
        if not raw_s:
            return None
        try:
            return float(raw_s.replace(",", ""))
        except ValueError:
            return None

    if ftype == "LOGICAL":
        if raw_s.upper() in {"T", "Y", "TRUE", "1"}:
            return True
        if raw_s.upper() in {"F", "N", "FALSE", "0"}:
            return False
        return None

    return raw_s[: int(fld.get("length", 10))] if raw_s else None


def _structure_parts(spec: str | list) -> list[str]:
    if isinstance(spec, list):
        return [str(p).strip() for p in spec if str(p).strip()]
    return [p.strip() for p in str(spec).split(";") if p.strip()]


def widen_units_field_in_spec(spec: str | list, field_name: str = "MUNIT", new_decimals: int = 5) -> str:
    """Return DBF spec with ``field_name`` decimal count updated (length preserved)."""
    import re

    parts = _structure_parts(spec)
    out = []
    pattern = re.compile(rf"^{field_name}\s+N\((\d+),(\d+)\)$", re.I)
    for part in parts:
        m = pattern.match(part)
        if m:
            length = m.group(1)
            out.append(f"{field_name} N({length},{new_decimals})")
        else:
            out.append(part)
    return "; ".join(out)


def read_table_spec(dbf_path: str) -> list[str]:
    table = dbf.Table(dbf_path)
    table.open()
    try:
        spec = table.structure()
        return _structure_parts(spec)
    finally:
        table.close()


def migrate_dbf_widen_units(
    source_path: str,
    target_path: str,
    *,
    field_name: str = "MUNIT",
    new_decimals: int = 5,
) -> dict[str, Any]:
    """Copy DBF rows to a new file with widened units-field decimal precision."""
    src = dbf.Table(source_path)
    src.open()
    try:
        old_spec = src.structure()
        new_spec = widen_units_field_in_spec(old_spec, field_name, new_decimals)
        rows = [tuple(rec) for rec in src]
    finally:
        src.close()

    if old_spec == new_spec:
        raise ValueError(f"{source_path}: {field_name} already at {new_decimals} decimals or field missing")

    import os

    if os.path.exists(target_path):
        os.remove(target_path)

    dst = dbf.Table(target_path, new_spec)
    dst.open(mode=dbf.READ_WRITE)
    try:
        for row in rows:
            dst.append(row)
    finally:
        dst.close()

    return {
        "source": source_path,
        "target": target_path,
        "rows": len(rows),
        "spec_before": old_spec,
        "spec_after": new_spec,
    }
