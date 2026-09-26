# Issue L14 — Planning Report

**Issue:** L14 — Cash Value Duration Off-by-One (QuikCvs)  
**Framework stage:** Planning Agent  
**Status:** Planning Complete  
**Generated:** 2026-08-06  
**Agent:** Cursor Grok 4.5 (read-only research)

---

## 1. Executive Finding

L14 CV factors in QuikCvs are shifted one duration late because `cv_remap_ql_duration` applies the #37/#98 first-duration matrix (`source + first − fnz`) to a coverage whose Rate_Table `DURATION` already matches LifePRO screen labels. For L14 F/69: `first=3`, `fnz=2` → every cell +1; Dur31=`1000` maps to 32 and is truncated by `100 − age`.

**Recommended direction:** Coverage-scoped identity for `COVERAGE_ID=L14` only (`ql_duration = source_duration`), leaving GL85/PO remap unchanged. Add L14 validator + release smoke.

---

## 2. Confirmed LifePRO Source

| Source | File | Notes |
|--------|------|-------|
| Rate_Table CV (annual) | `QLA_Migration/Source/Rate_Table_Extract_Txt.txt` | L14 F/69: Dur2=`14.73` … Dur31=`1000` (31 rows) |
| PDAGE (paged) | `PDAGE_AgeDuration_Rates_Extract_20260630.csv` | Same series as VALUE1..10 pages; emit path uses Rate_Table annual rows for L14 |

### Key fields

| Field | Role |
|-------|------|
| COVERAGE_ID | `L14` → plan `1L14SC` (Master_Crosswalk) |
| TYPE_CODE | `CV` → QuikCvs |
| DURATION | LifePRO year label (identity target for L14) |
| VALUE | Factor |

---

## 3. QLAdmin Target

| Table | Fields |
|-------|--------|
| `Output/rates/QuikCvs.csv` | PLAN, AGE, CNTL, CV0–CV9, GENDER, UWCLASS, BAND |

Paging: `duration_to_cntl_col(ql_duration)` — identity Dur2 → CNTL 00 / CV2.

---

## 4. Mapping Change

| Path | Current | Proposed | Change? |
|------|---------|----------|---------|
| L14 CV ql_duration | `source + first − fnz` (+1 late) | `source` (identity) | **Yes** |
| GL85 / other CV | `cv_remap_ql_duration` (#98) | unchanged | **No** |
| RV QuikTvs (#106) | identity | unchanged | **No** |

Touch points:

- `qla_core/rate_factor_loader.py` — `cv_remap_ql_duration` (+ callers pass coverage)
- `qla_core/cv_inheritance_loader.py` / `pdage_missfill.py` — same remap helper
- New `Issue_Log_Items/Issue_L14/validate_issue_l14_quikcvs_duration.py`
- Release smoke + guide row

---

## 5. Acceptance criteria

1. `1L14SC` F/69 NS: Dur2=`14.73`, Dur3=`52.91`, Dur31=`1000`.  
2. Second slice e.g. F/45: Dur2=`8.37`, terminal `1000` at LifePRO last dur.  
3. #98 validator PASS (`17085M` M/14).  
4. Release smoke includes L14.  
5. Rates re-emitted; DBFs via Append Tool APPEND only.

---

## 6. Out of scope

#118 UW, reinsurance, policy rebatch, global first-duration rewrite.
