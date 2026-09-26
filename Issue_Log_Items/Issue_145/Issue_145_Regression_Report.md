# Issue 145 — Regression Report

**Issue:** 145 — Vanish Flag (VB)  
**Framework stage:** Regression Agent  
**Engine version:** v59.00  
**Baseline:** Current full Output before Issue 145 overlay; active 20260630 source package  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-08-19  
**Verdict:** **PASS — with unrelated #26 validator limitation documented below**

---

## 1. Scope of Change

| Component | Expected impact |
|-----------|-----------------|
| `quikspec.VANISH` | 636 VB policies change F→T; 4,447 remain F |
| `quikspec.VANISHDT` | No change; remains blank |
| `quikspec.RESSTATE` / `RESRVCAT` | No change |
| Other tables | No change |

## 2. Row Count Comparison

| Table | Before | After | Delta | OK? |
|-------|-------:|------:|------:|-----|
| quikmstr | N/A | 5,083 | 0 expected | PASS |
| quikridr | N/A | 6,934 | 0 expected | PASS |
| quikprmh | N/A | 211,709 | 0 expected | PASS |
| quikplan | N/A | 141 | 0 expected | PASS |
| quikclid | N/A | 32,285 | 0 expected | PASS |
| quikclnt | N/A | 13,598 | 0 expected | PASS |
| quikspec | 5,083 | 5,083 | 0 | PASS |

## 3. Non-Target Field Diff

| Table | Column | Rows changed | OK? |
|-------|--------|-------------:|-----|
| quikspec | VANISH | 636 intentional F→T | PASS |
| quikspec | VANISHDT | 0 | PASS |
| quikspec | RESSTATE | 0 | PASS |
| quikspec | RESRVCAT | 0 | PASS |
| Other tables | All columns | Not touched by Issue 145 | PASS |

## 4. Prior Issue Fix Regression

| Check | Result |
|-------|--------|
| Issue #2 MPOLICY width-11 | **PASS** — all 331,647 checked values width 11 |
| Issue #26 MPREM mapping | **Environmental limitation** — legacy validator hard-codes missing 20260530 PPBEN/PPOLC files; active package is 20260630. No Issue 145 table or MPREM code was changed. |
| Issue #141 RESRVCAT | **PASS** — 5,083 filled, 0 blank, 0 mismatches |
| Issue #132 RESSTATE | **PASS** — 0 mismatches |
| Issue #139 ISWL fee suppression | **PASS** |
| Issue #75 Bank Acct | **PASS** |

## 5. Schema Integrity

| Check | Result |
|-------|--------|
| QuikSpec field order | PASS — `MPOLICY, VANISH, VANISHDT, RESSTATE, RESRVCAT` |
| Duplicate MPOLICY | PASS — 0 |
| QuikSpec row count | PASS — 5,083 |
| VANISH values | PASS — only T/F |
| VANISHDT populated | PASS — 0 |
| Python compilation | PASS |

## 6. Batch / Fleet Checks

| Check | Result |
|-------|--------|
| Full batch completed after v59.00 | No — Output was surgically enriched; full batch still required before final release handoff |
| Release smoke suite | PASS — `RELEASE_OK` |
| Issue 145 validator | PASS — 636 T / 4,447 F / 0 missing joins |
| Issue 141 and resident-state validators | PASS |

## 7. Failures / Limitations

| # | Description | Blast radius | Action |
|---|-------------|--------------|--------|
| 1 | `_validate_issue26_mprem.py` requires absent 20260530 extracts | Unrelated legacy check | Use active-date source-aware #26 validation or document the extract limitation; do not alter Issue 145 |
| 2 | Full batch was not run after v59.00 | Release proof, not current Output correctness | Run full batch before Closure / client handoff |
| 3 | Issue 145 smoke is not yet in `SMOKE_JOBS` | Closure gate | Add fail-closed smoke before marking Closed |

## 8. Recommendation

- [x] Regression behavior: **PASS**
- [ ] Mark Closed yet
- [x] Advance to **Closure preparation / Ready for Client UAT**, after full-batch proof and Issue 145 smoke registration

---

## Appendix

- Issue 145 validator: `QLA_Migration/_validate_issue145_vanish.py`
- Validation report: `Issue_145_Validation_Report.md`
- Test Validation: `QLA_Migration/Output/Test_Validation/quikspec.csv`
