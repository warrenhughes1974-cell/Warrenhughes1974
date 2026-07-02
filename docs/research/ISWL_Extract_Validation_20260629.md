# ISWL Extract Validation — 20260629 (Issue #31)

**Date:** 2026-06-30  
**Location:** `QLA_Migration/Source/`  
**Mode:** Research only

---

## Summary

| Extract | Rows | Distinct keys | Key fields | Quality |
|---------|-----:|--------------|------------|---------|
| PSEGT_Segment_Extract_20260629.csv | 696 | 221 SEGMENT_ID | SEGMENT_ID, SEGT_TYPE, SEGT_DATA | Clean; 1 separator row excluded |
| PDINT_DeclaredInterestRates_Extract_20260629.csv | 10 | 8 IDENT | IDENT, TYPE_CODE, EFF_DATE, date range | A1/C1/C3 only |
| PDINTTBL_DeclaredInterestRates_Extract_20260629.csv | 37 | 8 IDENT | DECLARED_RATE, START/END_DATE | Rate schedules |

---

## PSEGT relationships

- **Grain:** one row per `(SEGMENT_ID, SEGT_TYPE)` capability.
- **Join:** `PCOVRSGT.SEGT_ID` = `PSEGT.SEGMENT_ID` → all SEGT_TYPE values for that segment instance.
- **ISWL join rate:** 185 / 191 active PCOVRSGT slots (96.9%).
- **Cross-coverage refs:** Common (e.g. `658 CEN I` slots reference `659 CEN II` segment dictionary).

---

## PDINT highlight

**CENII + A1:** PDINTTBL shows **4.50%** from 2002-01-01 — consistent with Issue #21D ISWL MDEPINT / CSO crosswalk.

**Inferred link:** CENII IDENT → `659 CEN II` PSEGT segment dictionary (PCOVRSGT slots reference `IBA01 45`, `659 CEN II`, etc.).

---

## Machine-readable outputs

| File | Purpose |
|------|---------|
| `docs/research/ISWL_Segment_Trace/iswl_segment_trace_bundle_20260629.json` | Full bundle |
| `docs/research/iswl_psegt_target_matrix_20260629.json` | Coverage-native type matrix |
| `docs/research/ISWL_Segment_Trace/ISWL_Segment_Trace_Matrix_20260629.csv` | Code × coverage matrix |
| `docs/research/ISWL_Segment_Trace/ISWL_Hierarchy_Trace_20260629.csv` | Slot-level trace |

---

See `Issue_Log_Items/Issue_31/Issue_31_PSEGT_PDINT_Followup_Report.md` for QLA target status and resolution recommendation.
