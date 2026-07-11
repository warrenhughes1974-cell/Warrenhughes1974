# Issue 21F — Regression Report

**Issue:** #21F — Truncated Premium History (conversion premium adjustment)  
**Framework stage:** Regression Agent (G6)  
**Date:** 2026-07-11  
**Agent / model:** Regression · **Cursor Grok 4.5** (locked)  
**Prerequisite:** Validation **PASS** (v57.73)  
**Engine:** v57.73  
**Verdict:** **PASS** — ready for Closure

---

## Scope

Compared:

- Before: `QLA_Migration/Archive/quikprmh_pre_21f_v57.72.csv` (206,861 rows, no CONV_ADJ)  
- After: `QLA_Migration/Output/quikprmh.csv` (209,470 rows)

Intentional change only: **+2,609** CONV_ADJ rows (v57.73 BA/BF-only base; down from 2,622 in v57.72). No other table rewrite on this offline rebatch path.

Script: `Issue_Log_Items/Issue_21/Issue_21F/_regression_issue21f.py` (exit 0)

---

## Row counts

| Table | Rows (current Output) | vs prior Regression baseline | Expected vs 21F |
|-------|----------------------:|-----------------------------:|-----------------|
| quikprmh | **209,470** | intentional +2,609 adj | 206,861 + 2,609 |
| quikmstr | 5,083 | unchanged | Untouched by 21F |
| quikridr | 6,934 | unchanged | Untouched |
| quikplan | 141 | unchanged | Untouched |
| quikclid | 34,449 | unchanged | Untouched |
| quikclnt | 13,597 | unchanged | Untouched |
| quikbenf | 5,916 | unchanged | Untouched |

**History rows:** 206,861 before = 206,861 after (excluding CONV_ADJ) — **equals PASS** (all schema columns).

---

## Fields confirmed unchanged

| Surface | Result |
|---------|--------|
| Pre-existing `quikprmh` payment rows (all columns) | **Unchanged** |
| History `MSOURCE` / `USER_ID` not polluted with CONV_ADJ / QLA21F | **PASS** |
| `quikprmh` schema order | **PASS** |
| Detail DATEPAID floor on history | min **20170101** (unchanged) |
| Other quik* tables (this run) | Not regenerated; no 21F code path touches them |

---

## Prior issue fixes

| Issue | Check | Result |
|-------|--------|--------|
| **#25** MPOLICY padding | All CONV_ADJ + history MPOLICY len=10 | **PASS** |
| **#26** MPREM | `quikridr.MPREM` column present; 21F does not write quikridr | **PASS** (spot) |

---

## Fleet impact (intentional)

| Metric | Value |
|--------|------:|
| CONV_ADJ rows | 2,609 |
| Adjustment $ sum | $19,970,810.97 |
| ISWL excluded | 2,348 |
| Negatives loaded | 0 |
| OPENING_BALANCE (report) | 359 |

---

## Gate Criteria (G6)

| Criterion | Result |
|-----------|--------|
| Row counts stable except intentional target | **PASS** |
| Unrelated fields unchanged | **PASS** |
| #25 / #26 preservation | **PASS** |
| Schema integrity | **PASS** |
| Advance to Closure? | **YES** |

---

## Note

v57.72 Regression had PASS on non-target surfaces but Closure was blocked by Validation FAIL. v57.73 cleared Validation; this re-run confirms history/other tables remain clean with the corrected load set.
