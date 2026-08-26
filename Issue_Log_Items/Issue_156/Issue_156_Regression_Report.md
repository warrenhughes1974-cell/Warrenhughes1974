# Issue #156 — Regression Report

**Issue:** #156 — Add Source Policy Number to User Defined  
**Framework stage:** Regression Agent  
**Engine version:** v59.02  
**Baseline:** Pre-#156 five-column `quikspec` (MPOLICY, VANISH, VANISHDT, RESSTATE, RESRVCAT)  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-08-26  
**Verdict:** **PASS**

---

## 1. Scope of Change

| Component | Expected impact |
|-----------|-----------------|
| quikspec.SOR_POL | New column; LifePRO source policy number |
| Other quikspec fields | Unchanged |
| Other tables | Unchanged |

---

## 2. Row Count Comparison

| Table | After | OK? |
|-------|------:|-----|
| quikspec | 5,083 | PASS — same policy population |
| quikmstr / quikridr / others | not rewritten | PASS |

---

## 3. Non-Target Field Diff

| Table | Column | Result |
|-------|--------|--------|
| quikspec | VANISH | PASS — #145 validator |
| quikspec | VANISHDT | PASS — still blank |
| quikspec | RESSTATE | PASS — resident-state smoke |
| quikspec | RESRVCAT | PASS — #141 validator |
| quikspec | MPOLICY | PASS — still Issue #2 keys |

---

## 4. Prior Issue Fix Regression

| Issue ID | Guide check / validator | Result |
|----------|-------------------------|--------|
| #141 | `python QLA_Migration/_validate_issue141_resrvcat.py` | PASS |
| #145 | `python QLA_Migration/_validate_issue145_vanish.py` | PASS |
| #132 / RESSTATE | `python tools/validators/validate_quikspec_resident_state.py` | PASS |
| #2 | MPOLICY still source + C | PASS |

---

## 5. Schema Integrity

| Check | Result |
|-------|--------|
| First five columns unchanged | PASS |
| SOR_POL after RESRVCAT | PASS |
| Template C(10) | PASS — client change 2026-08-26 |

---

## 6. Verdict

**PASS.** Ready for Closure.
