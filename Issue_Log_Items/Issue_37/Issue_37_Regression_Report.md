# Issue #37 — Regression Report

**Issue:** Age/Duration Rate Placement — CV / QuikCvs (fleet-wide)  
**Framework stage:** Regression Agent (G6)  
**Baseline:** Issue #31 QuikCvs baseline (pre-#37) + current `QLA_Migration/Output/` plan tables  
**Output directory:** `QLA_Migration/Output/` + `QLA_Migration/Output/rates/`  
**Generated:** 2026-07-03  
**Verdict:** **PASS**

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|-----------|-----------------|
| **QuikCvs.csv** | Duration placement / grid extension only — values preserved |
| **Rate loader code** | `rate_factor_loader.py`, `rate_pipeline.py` (CV branch only) |
| **Plan converter (`app.py`)** | No change |
| **All other rate tables** | No row count change |
| **All plan/claims tables** | No row count change |

---

## 2. Row Count Comparison

| Table | Before | After | Delta | OK? |
|-------|-------:|------:|------:|-----|
| **QuikCvs** | ~19,453 | **26,031** | +6,578 | **Yes** (intentional) |
| QuikNps | 26,650 | 26,650 | 0 | **PASS** |
| QuikGps | 12,567 | 12,567 | 0 | **PASS** |
| QuikTvs | 26,097 | 26,097 | 0 | **PASS** |
| QuikDbs | 1,380 | 1,380 | 0 | **PASS** |
| QuikDvs | 3,978 | 3,978 | 0 | **PASS** |
| quikplan | 141 | 141 | 0 | **PASS** |
| quikridr | 6,934 | 6,934 | 0 | **PASS** |
| quikmstr | 5,083 | 5,083 | 0 | **PASS** |
| quikprmh | 205,577 | 205,577 | 0 | **PASS** |
| quikclid | 46,753 | 46,753 | 0 | **PASS** |
| quikclnt | 13,514 | 13,514 | 0 | **PASS** |

Evidence: `Issue_Log_Items/Issue_37/evidence/g6_regression_row_counts.csv`

**1960PO QuikCvs keys:** 991 → **985** (truncate under maturity-100 rule; placement validated in G5).

---

## 3. Non-Target Field Diff

| Table | Check | Result |
|-------|-------|--------|
| QuikNps / QuikGps / QuikTvs / QuikDbs / QuikDvs | Pipeline path unchanged (`source_duration_to_ql`) | **PASS** |
| quikplan / quikridr / quikmstr | Not re-emitted by rate loader; git diff empty | **PASS** |
| QuikPlCv / rate-key tables | Row counts stable (70 QuikPlCv keys) | **PASS** |

---

## 4. Prior Issue Fix Regression

### Issue #25 — MPOLICY padding

| Check | Result |
|-------|--------|
| `validate_mpolicy_width.py` | **PASS** — 286,770 fields, all width 10 |
| Sample padded policies | **PASS** — cross-table consistency |

### Issue #26 — MPREM mapping

| Check | Result |
|-------|--------|
| `validate_issue26_mprem.py` | **PASS** |
| Trace policies (13.20 / 10.96 / 9.12) | **PASS** |
| MMODPREM vs PPOLC | **4954/4954 PASS** |
| MVPU / MUNIT | **6669/6669 PASS** |

---

## 5. Schema Integrity

| Check | Result |
|-------|--------|
| QuikCvs field order / CHAR(7) factors | **PASS** — same schema; more CNTL pages |
| Pipeline blockers | **0** |
| V03 grid collisions | **0** |
| `app.py` not modified | **PASS** |

---

## 6. Batch / Fleet Checks

| Check | Result |
|-------|--------|
| Issue #37 placement validator | **PASS** |
| Issue #37 G5 proof matrix (8/8) | **PASS** |
| `iswl_quikcvs_reconcile.py` | **PASS** (post-rebaseline) |
| Issue #31 baseline rebaselined | **PASS** — `iswl_quikcvs_regression_baseline.json` updated |

**Rebaseline command run:**
```bash
python tools/validators/iswl_quikcvs_reconcile.py --write-baseline
```

---

## 7. Failures

None.

---

## 8. Recommendation

- [x] Advance to **Closure Agent (G7)** / **Ready for Client UAT**
- [ ] Return to Development — not required

**Client UAT focus:** Reload `QuikCvs.csv` in QLAdmin; confirm **1960PO / CV / Male / age 22** — Duration **4 = 8.32**, Duration **78 = 1000**.

---

## Appendix

- G5 validation: `Issue_37_Validation_Report.md`
- G5 proof matrix: `evidence/g5_validation_matrix.csv`
- Updated baseline: `Issue_Log_Items/Issue_31/output/baselines/iswl_quikcvs_regression_baseline.json`
