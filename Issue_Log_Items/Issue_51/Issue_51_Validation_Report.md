# Issue #51 — Validation Report

**Issue:** #51 — Missing Interest Table (A60MIR / A96DAR) — Projected Values Crash Loop  
**Framework stage:** Validation Agent  
**Engine version:** v57.76  
**Validation script:** `tools/validators/validate_issue51_quikaint.py` / `QLA_Migration/_validate_issue51_quikaint.py`  
**Output directory:** `QLA_Migration/Output/`  
**Before snapshot:** N/A (new table file)  
**Generated:** 2026-07-11  
**Model:** Cursor Grok 4.5 (locked Validation stage)  
**Verdict:** **PASS**

---

## Commands Run

```powershell
python tools/validators/validate_issue51_quikaint.py
$env:PYTHONPATH = "<repo>"; python Issue_Log_Items/Issue_51/scripts/validate_regression_spotcheck_issue51.py
```

Validator exit code: **0**

---

## 1. Trace Policy Results

| Policy | Phase | Field | Expected | Actual | Result |
|--------|------:|-------|----------|--------|--------|
| 010348734C | 2 | QuikAint A60MIR | Present @ 0.0000 | Present @ 0.0000 | **PASS** |
| 010335095C | 2 | QuikAint A60MIR | Present @ 0.0000 | Present @ 0.0000 | **PASS** |
| 010510671C | 4 | QuikAint A96DAR | Present @ 0.0000 | Present @ 0.0000 | **PASS** |
| 010511203C | 2 | QuikAint A96DAR | Present @ 0.0000 | Present @ 0.0000 | **PASS** |
| 010538650C | 2 | QuikAint A96DAR | Present @ 0.0000 | Present @ 0.0000 | **PASS** |
| 010549966C | 2 | QuikAint A96DAR | Present @ 0.0000 | Present @ 0.0000 | **PASS** |

Evidence: `evidence/issue51_validation_checklist.csv`

---

## 2. Acceptance Criteria (from Risk checklist)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | QuikAint contains A60MIR and A96DAR @ 0.0000 | **PASS** |
| 2 | QuikUint does not contain A60MIR/A96DAR | **PASS** |
| 3 | quikridr still has 6 MPHSTAT=56 MIR/DAR rows | **PASS** |
| 4 | rate_csv_manifest lists QuikAint | **PASS** |
| 5 | Schema Help §7.31 field order | **PASS** (`MPLAN,MEFFDATE,MINTRATE,MINTRATE1`) |
| 6 | Partial UAT copy in Test_Validation/rates | **PASS** |
| 7 | Client UAT Projected Values (no endless loop) | **Pending client** — conversion evidence complete |

---

## 3. Source Alignment

| Check | Result |
|-------|--------|
| PPBEN FV_GUAR_RATE=.00 → QuikAint 0.0000 | **PASS** |
| Crosswalk plans A60MIR / A96DAR | **PASS** |
| Orphan policies | N/A (plan-level table) |

---

## 4. Untouched Fields Confirmed

| Field / table | Check | Result |
|---------------|-------|--------|
| quikridr MIR/DAR rows | Count 6, all status 56 | **PASS** |
| QuikUint | 0 MIR/DAR rows | **PASS** |
| MPOLICY width (#25) | Example `010348734C` len=10 | **PASS** |
| quikridr.MPREM (#26) | A60MIR sample still populated (9.20000) | **PASS** (spot) |
| quikdvdp / #21D | Not modified in this change set | **PASS** (scope) |

---

## 5. Row Counts

| Table | Count | Notes |
|-------|------:|-------|
| rates/QuikAint | 2 | Intentional new |
| rates/QuikUint | 0 | Unchanged |
| quikridr (MIR/DAR) | 6 | Unchanged |
| quikmstr | 5083 | Untouched |
| quikridr (all) | 6934 | Untouched |
| quikplan | 141 | Untouched |

---

## 6. Impact Summary

| Metric | Value |
|--------|------:|
| QuikAint rows added | 2 |
| Policy table rows changed | 0 |
| QuikUint pollution | 0 |

---

## 7. Failures

None.

---

## 8. Verdict

**PASS** — Ready for Regression.

**Note:** Final UAT proof that the QLAdmin endless loop is cleared requires loading `QuikAint.csv` into the client rate package and retesting Projected Values on `010348734C`. Conversion-side acceptance criteria are met.
