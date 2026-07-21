"""Pull ISWL U6 Current COI tables for Sujitha handoff."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "Issue_Log_Items/Issue_43/evidence"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PAAGERAT = ROOT / "plan_analysis/source_data/rates/PAAGERAT_AttainedAge_Rates_Extract_20260428.csv"
QUIKCOI = ROOT / "QLA_Migration/Output/rates/QuikCoi.csv"

ISWL_COVERAGE = {
    "658 CEN I": "1658C1",
    "658 CEN SD": "1658CS",
    "659 CEN II": "1659C2",
    "659 CEN SR": "1659CR",
    "659 CEN SD": "1659CS",
    "659 SR GD": "1659SR",
    "669 SR GD": "1669SR",
    "679 CEN SD": "1679CS",
}

pa = pd.read_csv(PAAGERAT, dtype=str, low_memory=False).fillna("")
pa.columns = [c.strip().upper() for c in pa.columns]
u6 = pa[pa["TYPE_CODE"].astype(str).str.strip() == "U6"].copy()
u6["COVERAGE_ID_NORM"] = u6["COVERAGE_ID"].astype(str).str.strip()
u6["SOURCE"] = "PAAGERAT_AttainedAge_Rates_Extract_20260428.csv"
u6["SEGMENT_TYPE"] = "U6_Current_COI"
u6.to_csv(OUT_DIR / "iswl_u6_coi_paagerat_source.csv", index=False)

cov_summary = (
    u6.groupby("COVERAGE_ID_NORM", dropna=False)
    .size()
    .reset_index(name="ROW_COUNT")
    .sort_values("COVERAGE_ID_NORM")
)
cov_summary["QL_PLAN_CODE"] = cov_summary["COVERAGE_ID_NORM"].map(ISWL_COVERAGE)
cov_summary["NOTES"] = "U6 = Current COI Rates Segment (Product Book); NOT expense charge"
cov_summary.to_csv(OUT_DIR / "iswl_u6_coi_source_summary.csv", index=False)

qc = pd.read_csv(QUIKCOI, dtype=str).fillna("")
qc.columns = [c.strip().upper() for c in qc.columns]
qc["SOURCE"] = "QLA_Migration/Output/rates/QuikCoi.csv"
qc["SEGMENT_TYPE"] = "U6_Current_COI_Emitted"
qc.to_csv(OUT_DIR / "iswl_u6_coi_quikcoi_emitted.csv", index=False)

emit_summary = (
    qc.groupby("PLAN", dropna=False)
    .size()
    .reset_index(name="ROW_COUNT")
    .sort_values("PLAN")
)
emit_summary["NOTES"] = "Emitted from PAAGERAT U6 via segment resolution (1658CS, 1679CS only)"
emit_summary.to_csv(OUT_DIR / "iswl_u6_coi_emitted_summary.csv", index=False)

source_lines = "\n".join(
    f"  - {r.COVERAGE_ID_NORM}: {r.ROW_COUNT} rows -> QL plan {r.QL_PLAN_CODE}"
    for _, r in cov_summary.iterrows()
)
emit_lines = "\n".join(
    f"  - {r.PLAN}: {r.ROW_COUNT} rows" for _, r in emit_summary.iterrows()
)

manifest = f"""ISWL U6 Current COI Pull — for Sujitha (2026-07-13)

Purpose: Eric asked whether U6 Curr COI tables provide ISWL expense charges.
Answer: NO — U6 is Current Cost of Insurance, not premium expense or monthly policy fee.

Files:
1. iswl_u6_coi_paagerat_source.csv — {len(u6)} raw LifePRO PAAGERAT rows (TYPE_CODE=U6)
2. iswl_u6_coi_source_summary.csv — row counts by LifePRO coverage ID
3. iswl_u6_coi_quikcoi_emitted.csv — {len(qc)} emitted QuikCoi rows in current rate package
4. iswl_u6_coi_emitted_summary.csv — emitted row counts by QL plan

Source segments with U6 data:
{source_lines}

Emitted QuikCoi plans (conversion allowlist):
{emit_lines}

Gap note: 6/8 ISWL MPLANs have PSEGT U6 capability but only 1658CS and 1679CS currently emit in QuikCoi.
Expense charges (separate from U6): 3.5% premium expense + $25/yr monthly policy fee (~$2.08/mo).
See Issue_43_Meeting_Decisions_20260713.md and Issue_23_Meeting_Decisions_20260713.md.
"""
(OUT_DIR / "iswl_u6_coi_README.txt").write_text(manifest, encoding="utf-8")

print(f"U6 source rows: {len(u6)}")
print(f"QuikCoi rows: {len(qc)}")
for p in sorted(OUT_DIR.glob("iswl_u6*")):
    print(p.name, p.stat().st_size)
