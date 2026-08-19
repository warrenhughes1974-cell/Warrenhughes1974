# Issue #141 — Regression Report

**Issue:** #141 — Reserve Category  
**Framework stage:** Regression Agent  
**Engine version:** v58.97  
**Baseline:** Pre-141 Output on the same 2026-06-30 package (only `quikspec` gained `RESRVCAT`; no committed before snapshot — Output is gitignored)  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-08-19  
**Verdict:** **PASS**

---

## 1. Scope of Change (expected)

| Component | Expected impact | Observed |
|-----------|-----------------|----------|
| quikspec.RESRVCAT | New column on all 5,083 rows | **Met** — 5,083 filled, 0 blank |
| quikspec VANISH / VANISHDT / RESSTATE | Unchanged | **Met** |
| Other tables | No row-count change | **Met** |
| QuikPlan ISWLFE (#99) | Untouched | **Met** |

---

## 2. Row Count Comparison

| Table | After | Expected | Delta | OK? |
|-------|------:|---------:|------:|-----|
| quikmstr | 5,083 | 5,083 | 0 | Yes |
| quikridr | 6,934 | 6,934 | 0 | Yes |
| quikprmh | 211,709 | present | 0 (not rewritten) | Yes |
| quikplan | 141 | 141 | 0 | Yes |
| quikclid | 32,285 | present | 0 | Yes |
| quikclnt | 13,598 | present | 0 | Yes |
| quikspec | 5,083 | 5,083 | 0 rows; +1 column | Yes |
| quiklist | 6 | 6 | 0 | Yes |

---

## 3. Non-Target Field Diff (affected tables)

| Table | Column | Rows changed | OK? |
|-------|--------|-------------:|-----|
| quikspec | VANISH | 0 (all still F) | Yes |
| quikspec | VANISHDT | 0 | Yes |
| quikspec | RESSTATE | 0 (resident-state validator 0 mismatches) | Yes |
| quikspec | MPOLICY | 0 | Yes |
| quikplan | HLOB / PRODUCT / MKTG on 8 ISWL plans | 0 (still ISWLFE) | Yes |

---

## 4. Prior Issue Fix Regression

Catalog: `Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md`

### Issue #25 / #2 — Policy key width

| Check | Result |
|-------|--------|
| `python QLA_Migration/_validate_issue2_mpolicy.py` | **PASS** — 331,647 MPOLICY fields width 11 |
| Sample keys (9010143726C / 901222DCC) | Present |

### Issue #26 — MPREM mapping

| Check | Result |
|-------|--------|
| `validate_issue26_mprem.py` | **SKIP / environmental** — script still points at 20260530 extracts, not this cut |
| Spot-check MPREM | **PASS** — 9010722550C = 8.71966 (#137); 9010367131C = 9.12000 (#26); 9010143726C = 18.78000 |

### Other Closed rows overlapping this change

| Issue ID | Guide check / validator | Result |
|----------|-------------------------|--------|
| #132 / RESSTATE | `validate_quikspec_resident_state.py` | **PASS** — 0 mismatches |
| #145 VANISH | Traces still VANISH=F | **PASS** |
| #99 ISWLFE | Eight ISWL plans HLOB+PRODUCT+MKTG | **PASS** |
| #141 itself | `_validate_issue141_resrvcat.py` | **PASS** — 5083/5083, 0 ISWLFE |

---

## 5. Schema Integrity (AGENTS.md)

| Check | Result |
|-------|--------|
| Field order | `MPOLICY, VANISH, VANISHDT, RESSTATE, RESRVCAT` | PASS |
| No new blank MRIDRID | N/A (quikspec has no MRIDRID) | N/A |
| QLA formatting | MPOLICY #2 preserved | PASS |

---

## 6. Batch / Fleet Checks

| Check | Result |
|-------|--------|
| Full batch completed | No — surgical quikspec enrich on current Output (v58.97 hook will emit on next full batch) |
| Issue 141 validator on full Output | **PASS** |
| QuikSpec resident-state smoke | **PASS** |
| Audit log anomalies | None for this issue |

---

## 7. Failures (if any)

None that belong to Issue 141. #26 fleet script FAIL is a stale extract-date pin, not an Output regression.

---

## 8. Recommendation

- [x] Advance to **Closure Agent**
- [ ] Return to **Development Agent**
