# Issue 173 — Validation Report

**Issue:** 173 — ISWL negative fund balances  
**Framework stage:** Validation Agent  
**Engine version:** unchanged (`app.py` not modified)  
**Validation script:** `tools/validators/validate_issue155_iswl_seed.py` v2.1  
**Output directory:** `QLA_Migration/Output/`  
**Before snapshot:** prior QuikIswl last row 0.00 on the 247 negative funds  
**Generated:** 2026-09-25  
**Verdict:** **PASS**

---

## Commands Run

```text
python Issue_Log_Items/Issue_173/tools/_emit_quikiswl_173.py
set QLA_VALUATION_DATE=20260630
python tools/validators/validate_issue155_iswl_seed.py
```

---

## 1. Trace Policy Results

| Policy | Phase | Field | Expected | Actual | Result |
|---|---|---|---|---|---|
| 9010779727C | last history row | MACCTBAL / MCASHVAL | −172,395.45 | −172,395.45 | PASS |
| 9010737619C | last history row | MACCTBAL / MCASHVAL | −718,363.35 | −718,363.35 | PASS |
| 9010735781C | last history row | MACCTBAL / MCASHVAL | −121,065.25 | −121,065.25 | PASS |
| 9010713704C | last history row | MACCTBAL | 45,551.94 | 45,551.94 | PASS |
| 9010713705C | last history row | MACCTBAL | 26,251.74 | 26,251.74 | PASS |
| 9010713707C | last history row | MACCTBAL | 8,146.88 | 8,146.88 | PASS |

---

## 2. Acceptance Criteria (from Risk checklist)

| # | Criterion | Result |
|---|---|---|
| 1 | 247 ending-negative policies store the signed fund | PASS — validator last-row tie mismatch_policies=0, and NEGATIVE_SIGNED = 247 |
| 2 | 1,997 non-negative policies still tie | PASS — same tie check |
| 3 | Row count 545,150 and 2,244 policies | PASS |
| 4 | Control policies 704 / 705 / 707 unchanged | PASS |
| 5 | #155 validator no longer in the always-on smoke list | PASS — removed from `SMOKE_JOBS` |
| 6 | quikplan and rates not rebuilt | PASS — emit wrote QuikIswl and the exception report only |
| 7 | MRESERVE not changed | PASS — QuikValf not written |

---

## 3. Source Alignment

Last `MACCTBAL` equals PFNDR `FUND_BALANCE`, including negatives, for every policy that has a PFNDR row and a history. Confirmed by `last_row_pfndr_balance` mismatch 0.

---

## 4. What was not run

Regression and Closure were not started. `Output/Test_Validation/` was not published. The Desktop DBF append was not run. QuikValf on the 6/30 test company is unchanged until valuation is run again.

## Gate G5

Met for Validation. Status moves to Ready for Regression. Not Closed.
