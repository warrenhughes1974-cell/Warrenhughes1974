# Issue #145B — Regression Report

**Issue:** #145B — Vanish 0561s Out of ISRR  
**Framework stage:** Regression Agent  
**Engine version:** v59.01  
**Baseline:** apply audit before-counts in `issue145b_apply_summary.json`  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-08-23  
**Verdict:** **PASS**

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|-----------|-----------------|
| QuikIsrr / PS- clms / phase-0 clmp / type-8 benh | VB 0561 rows removed (−3,452 each) |
| quikmstr / quikridr / quikspec / quikprmh | No change |
| #146 leftovers | Unchanged |

---

## 2. Row Count Comparison

| Table | Before | After | Delta | OK? |
|-------|-------:|------:|------:|-----|
| quikmstr | 5083 | 5083 | 0 | Yes |
| quikridr | 6934 | 6934 | 0 | Yes |
| quikprmh | 211709 | 211709 | 0 | Yes |
| quikplan | 141 | 141 | 0 | Yes |
| quikclid | 32285 | 32285 | 0 | Yes |
| quikclnt | 13598 | 13598 | 0 | Yes |
| quikspec | 5083 | 5083 | 0 | Yes |
| QuikIsrr | 3657 | 205 | −3452 | Yes |
| quikclms | 6044 | 2592 | −3452 | Yes |
| quikclmp | 6536 | 3084 | −3452 | Yes |
| quikbenh | 45012 | 41560 | −3452 | Yes |

---

## 3. Non-Target Field Diff (affected tables)

| Table | Column | Rows changed | OK? |
|-------|--------|-------------:|-----|
| quikridr | MUNIT golds | 0 | Yes |
| quikspec | VANISH | 0 (still T=636) | Yes |
| quikbenh | types 10/11/12 | 0 (4118 / 14156 / 19135) | Yes |
| leftover QuikIsrr | #146 amounts | 0 | Yes |

---

## 4. Prior Issue Fix Regression

### Issue #25 / #2 — Policy key width

| Check | Result |
|-------|--------|
| `QLA_Migration/_validate_issue2_mpolicy.py` | **PASS** (317,839 keys width 11) |
| QuikIsrr leftover keys | width 11 |

### Issue #26 — MPREM mapping

| Check | Result |
|-------|--------|
| `validate_issue26_mprem.py` | **WARN** — script still looks for 20260530 extracts (pre-existing; not this issue) |
| quikridr row count | Unchanged 6934 |

### Other Closed rows overlapping this change

| Issue ID | Guide check / validator | Result |
|----------|-------------------------|--------|
| 145 | `_validate_issue145_vanish.py` | **PASS** T=636 |
| 139 | fee withhold | **PASS** |
| 54 | loan 10/11/12; type 8 leftover (floor unfrozen from 3657) | **PASS** after class-A validator update |
| 134 | claim memos | **PASS** |
| 135 | CSO claims production | **PASS** |

#54’s old exact type-8 count of 3657 was the pre-#145B 0561 companion book, not loan history. Loan types were never touched. The #54 validator now requires leftover type 8 ≥ 1.

---

## 5. Schema Integrity (AGENTS.md)

| Check | Result |
|-------|--------|
| Field order preserved | PASS — tables rewritten with existing headers |
| Field types/lengths preserved | PASS |
| No new blank MRIDRID | N/A |
| QLA formatting rules preserved | PASS (#2) |

---

## 6. Batch / Fleet Checks

| Check | Result |
|-------|--------|
| Full policy batch | No — surgical Output strip + emit filter |
| Issue 145B validator | PASS |
| Emit dry-run leftover | 205 / 50 / $75,119.87; 3452 VB excluded; 0 leak |

---

## 7. Failures (if any)

None remaining. Stale #54 type-8 floor corrected. #26 extract-date miss is environmental.

---

## 8. Recommendation

- [x] Advance to **Closure Agent**
- [ ] Return to **Development Agent**

---

## Appendix

- Apply audit: `Issue_Log_Items/Issue_145B/evidence/issue145b_apply_summary.json`
