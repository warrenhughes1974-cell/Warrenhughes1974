ISWL U6 Current COI Pull — for Sujitha (2026-07-13)

Purpose: Eric asked whether U6 Curr COI tables provide ISWL expense charges.
Answer: NO — U6 is Current Cost of Insurance, not premium expense or monthly policy fee.

Files:
1. iswl_u6_coi_paagerat_source.csv — 800 raw LifePRO PAAGERAT rows (TYPE_CODE=U6)
2. iswl_u6_coi_source_summary.csv — row counts by LifePRO coverage ID
3. iswl_u6_coi_quikcoi_emitted.csv — 792 emitted QuikCoi rows in current rate package
4. iswl_u6_coi_emitted_summary.csv — emitted row counts by QL plan

Source segments with U6 data:
  - 658 CEN I: 400 rows -> QL plan 1658C1
  - 659 CEN II: 400 rows -> QL plan 1659C2

Emitted QuikCoi plans (conversion allowlist):
  - 1658CS: 396 rows
  - 1679CS: 396 rows

Gap note: 6/8 ISWL MPLANs have PSEGT U6 capability but only 1658CS and 1679CS currently emit in QuikCoi.
Expense charges (separate from U6): 3.5% premium expense + $25/yr monthly policy fee (~$2.08/mo).
See Issue_43_Meeting_Decisions_20260713.md and Issue_23_Meeting_Decisions_20260713.md.
