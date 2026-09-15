# Issue #168 — Validation Report

**Issue:** #168 — L14 reserve/value class-key replication (L05 out of scope)  
**Framework stage:** Validation Agent  
**Engine version:** unchanged (Output-apply; no `APP_VERSION` bump)  
**Validation script:** `tools/validators/validate_issue168_l14_reserve_class_replication.py`  
**Output directory:** `QLA_Migration/Output/`  
**Before snapshot:** `QLA_Migration/Archive/issue168_l14_20260915_010022/`  
**Generated:** 2026-09-15  
**Verdict:** **HOLD — rate-table acceptance PASS; reserve-outcome proof pending QLAdmin valuation**

Validation of the eight rate/option tables meets the Development acceptance criteria. Trace-policy **reserves** cannot be proven until Warren loads the updated tables and produces a new `QuikValf`. Do not Close on this report.

---

## Commands Run

```text
python tools/validators/validate_issue168_l14_reserve_class_replication.py
python Issue_Log_Items/Issue_168/tools/verify_issue168_applied.py
python Issue_Log_Items/Issue_168/tools/validate_issue168_nt_unchanged.py
python tools/validators/validate_issue136_pvo_flags.py
python tools/validators/validate_issue159_muwclass_plan_aware.py
python Issue_Log_Items/Issue_L14/validate_issue_l14_quikcvs_duration.py
python tools/validators/validate_newest_plan_rates_kept.py
```

---

## 1. Trace Policy Results

Rate-key proof is in place. Dollar reserves are **not** proven (current `docs/Valuation/QuikValf.dbf` is the 9/2 run, before this apply).

| Policy | Class | Field | Expected after load | Actual today | Result |
|--------|-------|-------|---------------------|--------------|--------|
| 9011227604C | PQ | MRESERVE | 9,895.80 (same as NT 9011226092C) | Not revalued | HOLD |
| 9011258186C | PQ | MRESERVE | 9,543.45 | Not revalued | HOLD |
| 9011208194C | ST | MRESERVE | LifePRO 3,121.45 | Not revalued | HOLD |
| 9011236347C | PR | MRESERVE | LifePRO 8,644.71 | Not revalued | HOLD |
| 9011226092C | NT | MRESERVE | Unchanged 9,895.80 | Not revalued | HOLD (control) |
| Any 5L0510 | PR/ST | rate tables | Untouched | Untouched | PASS |

---

## 2. Acceptance Criteria (from Risk checklist)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | `1L14SC` NT rows unchanged | **PASS** — archive vs current, all 8 tables |
| 2 | PQ/PR/ST rows present and value-identical to NT | **PASS** — 0 missing, 0 mismatches |
| 3 | `QuikGps` row count and values unchanged | **PASS** — 68 rows; golds NT GP5=21.12 vs PQ GP5=15.24 |
| 4 | L05 (`5L0510`, `9L05WP`) not touched | **PASS** |
| 5 | `quikridr.MUWCLASS` unchanged | **PASS** — #159 validator PASS; apply script did not write `quikridr` |
| 6 | `validate_issue136_pvo_flags.py` | **PASS** |
| 7 | `validate_issue159_muwclass_plan_aware.py` | **PASS** |
| 8 | `validate_issue168_l14_reserve_class_replication.py` | **PASS** |
| 9 | Existing L14 QuikCvs duration smoke | **PASS** |
| 10 | Newest plan/rate hash package | **PASS** (same-cut 20260831) |
| 11 | Trace-policy reserves match LifePRO | **HOLD** — needs new QuikValf |

---

## 3. Source Alignment

| Check | Result |
|-------|--------|
| LifePRO class-invariant reserve → four class keys | PASS — copies of the one real NT grid |
| No invented factors | PASS — NT archive rows == current NT rows |
| Premium still class-varying | PASS — 8 of 16 shared NT/PQ QuikGps keys differ |

---

## 4. Untouched Fields Confirmed

| Field / table | Check | Result |
|---------------|-------|--------|
| `QuikGps` / `QuikPlGp` | Golds + SHA intent | PASS |
| `QuikPlUw` | `1L14SC` still NT/PQ/PR/ST | PASS |
| `quikridr.MUWCLASS` | #159 PASS | PASS |
| `quikplan` `*VARY*` | #136 PASS | PASS |
| L05 / L01 plans | Not in apply list | PASS |
| `app.py` | Not modified | PASS |

---

## 5. Row Counts (`1L14SC` only)

| Table | NT (unchanged) | Added (PQ+PR+ST) | After per class |
|-------|---------------:|-----------------:|-----------------|
| QuikTvs | 332 | 996 | 332 × 4 |
| QuikNps | 328 | 984 | 328 × 4 |
| QuikCvs | 332 | 996 | 332 × 4 |
| QuikNff | 324 | 972 | 324 × 4 |
| QuikPlTv | 2 | 6 | 2 × 4 |
| QuikPlCv | 2 | 6 | 2 × 4 |
| QuikPlDb | 2 | 6 | 2 × 4 |
| QuikPlDv | 2 | 6 | 2 × 4 |
| **Total added** | | **3,972** | |

Other-plan row counts on those tables: unchanged at apply time.

---

## 6. Impact Summary

| Metric | Value |
|--------|------:|
| Existing rows altered | 0 |
| Rows added | 3,972 |
| Engine / mapping code changed | 0 |

---

## 7. Failures (if any)

| # | Description | Severity | Return to Dev? |
|---|-------------|----------|----------------|
| 1 | Policy-level MRESERVE not yet proven in a post-fix QuikValf | Blocks Closure only | No |

---

## 8. Recommendation

- [x] Rate-table Validation **PASS**
- [ ] Do **not** advance to Closure until a post-load QuikValf confirms the HOLD policies
- [ ] Next process step: publish the 8 tables through Desktop DBF Append, run QLAdmin valuation, then re-open Validation for the reserve-outcome check

---

## Appendix

- Evidence: `Issue_Log_Items/Issue_168/evidence/issue168_l14_reserve_class_replication.csv`
- Test_Validation copies: `QLA_Migration/Output/Test_Validation/rates/`
- Rollback: copy `QLA_Migration/Archive/issue168_l14_20260915_010022/*.csv` back to `Output/rates/`
