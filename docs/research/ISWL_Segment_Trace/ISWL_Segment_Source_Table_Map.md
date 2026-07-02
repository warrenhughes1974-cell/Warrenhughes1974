# ISWL Segment Source Table Map

**Date:** 2026-06-30 (updated after Issue #31 extracts)  
**Prior version:** 2026-06-28 — PSEGT/PDINT marked MISSING

## Hierarchy files

| Table | Path | Status | Role |
|-------|------|--------|------|
| PPRDF | May ZIP only | Partial | No ISWL-named products; hierarchy starts at PCOMP |
| PCOMP | `plan_analysis/PCOMP.csv` | In repo | Components / riders (`PRODUCT_ID` = coverage id for ISWL) |
| PCOVR | `QLA_Migration/Source/PCOVR_Coverage_Extract_20260530.csv` | In repo | Coverage metadata |
| PCOVRSGT | `plan_analysis/source_data/coverage/PCOVRSGT.csv` | In repo | Segment slots → `SEGT_ID` (56 slots × 8 ISWL coverages) |
| **PSEGT** | `QLA_Migration/Source/PSEGT_Segment_Extract_20260629.csv` | **Received** | `(SEGMENT_ID, SEGT_TYPE)` — multiple types per segment ID |
| **PDINT** | `QLA_Migration/Source/PDINT_DeclaredInterestRates_Extract_20260629.csv` | **Received** | Interest declaration rules |
| **PDINTTBL** | `QLA_Migration/Source/PDINTTBL_DeclaredInterestRates_Extract_20260629.csv` | **Received** | Interest rate schedules |

## Mandatory trace chain (now complete for PSEGT-mapped codes)

```text
PCOMP → PCOVR → PCOVRSGT.SEGT_ID → PSEGT.SEGT_TYPE → rate table / PDINT
```

**Hub segments for ISWL:** `659 CEN II` (full UL type set), `658 CEN I` (U6/BP/CV/NC), `658 CEN SD`, `679 CEN SD`, `L14` (LN).

## Segment types → authoritative source (ISWL — 8/8 coverages via PSEGT)

| Product Book code | PSEGT coverage | Primary rate / data source | PAAGERAT parent rows (approx) |
|-------------------|----------------|----------------------------|-------------------------------|
| **CV** | 8/8 | PDAGE + Rate_Table (`TYPE_CODE=CV`) | N/A (parent COVERAGE_ID) |
| **U6** | 8/8 | PAAGERAT (`SEGT_ID` 658 CEN I / 659 CEN II) | 2/8 parents (658 CEN SD, 679 CEN SD) |
| **U5** | 8/8 | PAAGERAT | 1/8 (679 CEN SD) |
| **BP** | 8/8 | PAAGERAT | 4/8 |
| **A1** | 8/8 | PDINT/PDINTTBL (`IDENT=CENII`, etc.) | — |
| **G1** | 8/8 | PDINT (sparse) / PSEGT only | — |
| **LN** | 8/8 | PDINT (sparse) / `L14` segment | — |
| **SR** / **SL** | 8/8 | PSEGT on 659 CEN II; rate pointer TBD | SL: 26 rows (659 CEN II) |
| **UF** | 8/8 | PSEGT on 659 CEN II; 13 PAAGERAT rows | 1/8 |
| **U1/U2/U3/G2/G3/GF** | **0/8** | Not in PSEGT for ISWL | — |
| **NC** | 8/8 | PAAGERAT — **not QUIKCOI** (net premium credited) | — |

## PAAGERAT resolution chain (repo)

`PAAGERAT.COVERAGE_ID` = `PCOVRSGT.SEGT_ID` → parent `PCOVR.COVERAGE_ID` → MPLAN crosswalk (`qla_core/rate_segment_resolution.py`).

## PDINT interest linkage

| IDENT | Inferred segment | TYPE | Current rate (PDINTTBL) |
|-------|------------------|------|-------------------------|
| CENII | 659 CEN II | A1 | 4.50% from 2002-01-01 |
| IBA01 | IBA01 45 | C1 | (see extract) |

---

*Machine bundle: `iswl_segment_trace_bundle_20260629.json`*
