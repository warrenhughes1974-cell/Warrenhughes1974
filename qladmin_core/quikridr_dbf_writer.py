"""Write QUIKRIDR.DBF from conversion quikridr.csv — Issue 21K N(10,5) MUNIT."""

from __future__ import annotations

import os
from typing import Any

import dbf
import pandas as pd

from qladmin_core.qladmin_dbf_layout import csv_value_for_field, layout_to_dbf_spec
from qladmin_core.qladmin_units_schema import QUIKRIDR_DBF_LAYOUT, UNITS_DECIMALS_AFTER


def write_quikridr_dbf(csv_path: str, dbf_path: str) -> dict[str, Any]:
    """Build QUIKRIDR.DBF from emitted CSV using QLAdmin Help layout (MUNIT N(10,5))."""
    df = pd.read_csv(csv_path, dtype=str).fillna("")
    df.columns = [str(c).strip().upper() for c in df.columns]

    layout = QUIKRIDR_DBF_LAYOUT
    missing = [f["field"] for f in layout if f["field"] not in df.columns]
    if missing:
        raise ValueError(f"quikridr.csv missing columns {missing}")

    row_values = []
    for _, row in df.iterrows():
        vals = tuple(
            csv_value_for_field(row.get(f["field"], ""), f, preserve_mpolicy_padding=True)
            for f in layout
        )
        row_values.append(vals)

    spec = layout_to_dbf_spec(layout)
    if os.path.exists(dbf_path):
        os.remove(dbf_path)

    table = dbf.Table(dbf_path, spec)
    table.open(mode=dbf.READ_WRITE)
    for vals in row_values:
        table.append(vals)
    table.close()

    return {
        "csv_rows": len(df),
        "dbf_rows": len(row_values),
        "dbf_path": dbf_path,
        "munit_decimals": UNITS_DECIMALS_AFTER,
        "dbf_spec": spec,
    }


def read_quikridr_munit(
    dbf_path: str,
    mpolicy: str,
    mphase: int | str,
    *,
    mplan: str | None = None,
) -> dict[str, Any] | None:
    """Read one QUIKRIDR row by policy + phase (optional plan filter)."""
    phase_s = str(int(str(mphase).strip() or "0"))
    table = dbf.Table(dbf_path)
    table.open()
    try:
        for rec in table:
            pol = str(rec.mpolicy).strip()
            ph = str(int(float(rec.mphase)))
            plan = str(rec.mplan).strip()
            if pol != mpolicy.strip() or ph != phase_s:
                continue
            if mplan is not None and plan != mplan.strip():
                continue
            munit = float(rec.munit)
            mvpu = float(rec.mvpu)
            return {
                "MPOLICY": pol,
                "MPHASE": ph,
                "MPLAN": plan,
                "MUNIT": munit,
                "MVPU": mvpu,
                "face": round(munit * mvpu, 2),
            }
    finally:
        table.close()
    return None
