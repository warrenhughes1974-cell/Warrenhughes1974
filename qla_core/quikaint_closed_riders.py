"""
Issue #51 — closed MIR/DAR annuity interest stubs for QuikAint (Help §7.31).

A-prefix riders A60MIR / A96DAR require QuikAint rows for QLAdmin Projected Values.
Authority: PPBEN.FV_GUAR_RATE=.00 on all in-force MIR/DAR riders.
"""
from __future__ import annotations

import os

from qla_core import rate_dbf_writer as W

CLOSED_RIDER_MPLANS = ("A60MIR", "A96DAR")
STUB_MEFFDATE = "19000101"
STUB_RATE = "0.0000"


def build_issue51_quikaint_rows() -> list[dict]:
    """Return exactly two closed-product QuikAint stub rows."""
    return [
        {
            "MPLAN": mplan,
            "MEFFDATE": STUB_MEFFDATE,
            "MINTRATE": STUB_RATE,
            "MINTRATE1": STUB_RATE,
        }
        for mplan in CLOSED_RIDER_MPLANS
    ]


def emit_issue51_quikaint(
    rates_dir: str,
    *,
    overwrite: bool = True,
    emit_csv: bool = True,
    emit_dbf: bool = False,
) -> dict:
    """
    Write QuikAint stub rows to rates_dir.

    Returns a manifest entry dict compatible with rate_emit / rate_csv_manifest.
    """
    os.makedirs(rates_dir, exist_ok=True)
    rows = build_issue51_quikaint_rows()
    n = len(rows)
    path = os.path.join(rates_dir, "QuikAint.csv")
    if emit_csv:
        n = W.write_quikaint_csv(path, rows, overwrite=overwrite)
    if emit_dbf:
        dbf_path = os.path.join(rates_dir, "QuikAint.dbf")
        n = W.write_quikaint_table(dbf_path, rows, overwrite=overwrite)
        path = dbf_path
    return {
        "kind": "annuity_interest",
        "table": "QuikAint",
        "format": "dbf" if emit_dbf and not emit_csv else "csv",
        "path": path,
        "rows": n,
    }
