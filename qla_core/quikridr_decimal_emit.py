"""Issue #55 — quikridr decimal emit: MUNIT sub-mill floor + leading-zero formatting."""

from __future__ import annotations

from qladmin_core.qladmin_units_schema import QUIKRIDR_DBF_LAYOUT

MUNIT_FLOOR_THRESHOLD = 0.001

QUIKRIDR_DECIMAL_FIELDS: dict[str, int] = {
    fld["field"]: int(fld["decimals"])
    for fld in QUIKRIDR_DBF_LAYOUT
    if fld.get("type") == "NUMERIC" and int(fld.get("decimals", 0)) > 0
}


def _blank(val) -> bool:
    if val is None:
        return True
    s = str(val).strip()
    return s == "" or s.lower() in ("nan", "none")


def _parse_decimal(val) -> float | None:
    try:
        return float(str(val).replace(",", "").strip() or 0)
    except (ValueError, TypeError):
        return None


def format_quikridr_decimal_field(field: str, val) -> str:
    """Format one quikridr numeric decimal field for QLAdmin CSV/DBF load."""
    if _blank(val):
        return ""

    raw = str(val).strip().replace(",", "")

    # Issue #26: preserve MPREM numeric string; only fix leading-dot corruption.
    if field == "MPREM":
        return f"0{raw}" if raw.startswith(".") else raw

    decimals = QUIKRIDR_DECIMAL_FIELDS.get(field)
    if decimals is None:
        return raw

    num = _parse_decimal(raw)
    if num is None:
        return raw

    if field == "MUNIT" and 0 < num < MUNIT_FLOOR_THRESHOLD:
        num = 0.0

    return f"{num:.{decimals}f}"


def apply_quikridr_decimal_emit(row_data: dict) -> None:
    """In-place post-map emit hook for quikridr decimal fields (Issue #55)."""
    for field in QUIKRIDR_DECIMAL_FIELDS:
        if field in row_data:
            row_data[field] = format_quikridr_decimal_field(field, row_data[field])
