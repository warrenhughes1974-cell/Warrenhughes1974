"""Re-emit QuikIswl only for Issue 173. Does not stamp MISWL or rebuild plan/rates."""
import os
from pathlib import Path

os.environ["QLA_VALUATION_DATE"] = "20260630"

from qla_core.quikiswl_loader import (
    OUTPUT_FILENAME,
    _load_pfndr_by_mpolicy,
    _load_pfndrdet_history,
    build_quikiswl_history_rows,
    load_iswl_policy_meta,
    write_issue155_exceptions,
    write_quikiswl_csv,
)

out = Path("QLA_Migration/Output")
policy_meta, _meta = load_iswl_policy_meta(out / "quikmstr.csv", out / "quikridr.csv")
pfndr = _load_pfndr_by_mpolicy("20260630")
cv_by_pol, flows_by_pol = _load_pfndrdet_history("20260630")
rows, exceptions, exc_counts = build_quikiswl_history_rows(
    policy_meta, pfndr, cv_by_pol, flows_by_pol, "20260630"
)
n = write_quikiswl_csv(rows, out / OUTPUT_FILENAME)
exc_path = write_issue155_exceptions(exceptions, "20260630")
print("rows", n, "policies", len({r["MPOLICY"] for r in rows}))
print("exceptions", exc_counts)
print("exception_file", exc_path)
