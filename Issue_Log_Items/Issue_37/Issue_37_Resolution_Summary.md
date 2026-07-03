# Issue #37 — Resolution Summary

**Issue:** #37 — Age/Duration Rate Placement — CV / QuikCvs (fleet-wide)  
**Framework stage:** Closure Agent (G7)  
**Final status:** **Closed**  
**Engine version:** **v57.43**  
**Closed date:** 2026-07-03  
**Owner:** Conversion + Client (LifePRO screenshot authority)

---

## Production Readiness (G7 gate)

Before closing, confirm the following for network batch runs:

| Check | Status |
|-------|--------|
| `QLA_Migration/app.py` version **v57.43** (Issue #37 change note) | **Done** |
| Rate fix in `qla_core` (R5 pipeline — no manual patch) | **Done** |
| `GENERATE RATE TABLES` / batch emits corrected **QuikCvs.csv** | **Done** — `Output/rates/QuikCvs.csv` (26,031 rows) |
| G5 validation PASS (8/8 proof ages) | **Done** |
| G6 regression PASS (#25 / #26 preserved) | **Done** |
| Issue #31 QuikCvs baseline rebaselined | **Done** |

**Network batch:** Pull this commit, run the suite at **v57.43**. Use **GENERATE RATE TABLES** (or full UAT batch with rate phase enabled) to refresh `Output/rates/QuikCvs.csv` before QLAdmin load.

---

## Problem Statement

Client reported that **Cash Value (CV)** age/duration rates for **960 PO / QLAdmin plan 1960PO** had **correct numeric values** but **wrong duration column placement** versus LifePRO (example: Male issue age 22 — LifePRO first rate at Duration 4, QLAdmin showed Duration 1). Investigation confirmed the same loader behavior affected **all CV products** (~36 plans).

---

## Root Cause

**Category:** Mapping error (rate pipeline)

Phase R5 mapped LifePRO extract `DURATION` directly to QLAdmin slots via `duration − 1` with **no LifePRO-style grid** (leading zero durations, variable start offset by issue age, maturity extension to `100 − issue_age`).

---

## Resolution

Implemented a **CV-only grid builder** in `qla_core/rate_factor_loader.py` (Issue #37). Rate **values** are unchanged; only **placement** and grid extent change. **`app.py` bumped to v57.43** so network batch runs trace this release.

### Files changed

| File | Change |
|------|--------|
| `qla_core/rate_factor_loader.py` | CV LifePRO grid remap + truncate past maturity |
| `qla_core/rate_pipeline.py` | Pre-scan CV slice fnz |
| `QLA_Migration/app.py` / `app.py` | **v57.43** — Issue #37 release note |
| `QLA_Migration/Output/rates/QuikCvs.csv` | Re-emitted fleet CV table |
| `Issue_Log_Items/Issue_31/.../iswl_quikcvs_regression_baseline.json` | Rebaselined post-#37 |
| `QLA_Migration/_validate_issue37_*.py` | Validation scripts |

### Engine changes

- CV: `lp_duration = source_d + lp_first − fnz`; QL slot = `lp_duration − 1`; drop rows past `100 − issue_age`
- Non-CV rate families: unchanged (`duration − 1`)

---

## Evidence

| Artifact | Path |
|----------|------|
| Risk review | `Issue_Log_Items/Issue_37/Issue_37_Risk_Review_Report.md` |
| Implementation | `Issue_Log_Items/Issue_37/Issue_37_Implementation_Notes.md` |
| Validation | `Issue_Log_Items/Issue_37/Issue_37_Validation_Report.md` — **PASS** |
| Regression | `Issue_Log_Items/Issue_37/Issue_37_Regression_Report.md` — **PASS** |
| Proof matrix | `Issue_Log_Items/Issue_37/evidence/g5_validation_matrix.csv` |

---

## Trace Policy Confirmation

| Policy | Client expected | Emitted | Match |
|--------|-----------------|---------|-------|
| 1960PO M/22 first rate | 8.32 @ Duration **4** | 8.32 @ LP dur 4 | **Yes** |
| 1960PO M/22 last rate | 1000 @ Duration **78** | 1000 @ LP dur 78 | **Yes** |
| 960 PO proof ages (8) | LifePRO screenshots | G5 matrix | **Yes** |

---

## Explicitly Not Changed

- [x] `app.py` plan converter logic (QuikPlan path)
- [x] Issue #25 MPOLICY 10-char padding
- [x] Issue #26 MPREM / MMODPREM
- [x] QuikNps, QuikGps, QuikDbs, QuikTvs, QuikDvs rate tables (row counts stable)
- [x] quikplan, quikridr, quikmstr, quikprmh row counts

---

## Fleet Impact

| Metric | Value |
|--------|------:|
| QuikCvs rows | 26,031 (+6,578 vs pre-fix) |
| CV products | 36 |
| Other table row deltas | **0** |

---

## Client UAT

| Item | Status |
|------|--------|
| QLAdmin screen verification | Recommended — **1960PO / CV / M / age 22** |
| Engineering validation | **PASS** (G5 + G6) |

---

## Residual Risks / Follow-ups

| Item | Owner | Notes |
|------|-------|-------|
| 1L10OD multi-COVERAGE_ID → PLAN collision | Backlog | Pre-existing; out of #37 scope |
| PCOVR MAX_BEN ≠ 100 (12 products) | SME | G3 override to maturity 100 accepted |

---

## Rollback

1. Revert commit (or restore prior `QuikCvs.csv` + `rate_factor_loader.py` / `rate_pipeline.py`)
2. Restore Issue #31 baseline JSON if needed
3. Re-run `rate_loader_emit.py --csv-only` at prior loader version

---

## Issue Log Entry (paste-ready)

> **Issue #37 — Age/Duration CV Rate Placement — CLOSED (2026-07-03).** Client reported correct CV values with wrong duration columns vs LifePRO (960PO/1960PO anchor). **Fix:** CV-only LifePRO grid in R5 loader; maturity `100 − issue_age`; **v57.43**. **Evidence:** G5/G6 PASS; 8/8 proof ages; #25/#26 preserved. **Production:** `app.py` v57.43 + `Output/rates/QuikCvs.csv`; run GENERATE RATE TABLES on network batch. **Follow-ups:** 1L10OD multi-coverage collision (backlog).

---

## Framework Checklist

- [x] Intake
- [x] Planning
- [x] Dependency Gate PASS
- [x] Risk Conditional Go
- [x] Development
- [x] Validation PASS
- [x] Regression PASS
- [x] Closure + production readiness verified
