# Issue #75 — Regression Report (REOPEN — PPCOM recovery)

**Issue:** #75 — Bank Acct / `MBANKNO` via PPCOM  
**Framework stage:** Regression Agent (G6)  
**Date:** 2026-07-25  
**Engine:** v58.35  
**Model:** Cursor Grok 4.5 (locked)  
**Verdict:** **PASS**

---

## Baseline

| Artifact | Path |
|----------|------|
| Before | `evidence/quikmstr_before_issue75_v5835_20260725_133245.csv` |
| After | `QLA_Migration/Output/quikmstr.csv` |

---

## Row counts

| Table | Before | After | Delta |
|-------|-------:|------:|------:|
| quikmstr | 5,083 | 5,083 | 0 |
| quikridr | — | 6,934 | n/a (untouched by apply) |
| quikprmh | — | 209,480 | n/a |
| quikplan | — | 141 | n/a |
| quikclid | — | 32,285 | n/a |
| quikclnt | — | 13,597 | n/a |

Policy set identical (0 only-before / 0 only-after). Field schema identical.

---

## Non-target field diff (quikmstr)

| Column | Rows changed |
|--------|-------------:|
| `MBANKNO` | **954** |
| All other columns | **0** |

Intentional `MBANKNO` only. No premium, status, bill-form, or ID drift.

---

## Fleet impact (bank draft)

| Metric | Before | After |
|--------|-------:|------:|
| `MBILLFRM=2` | 2,132 | 2,132 |
| Filled QLA-safe | 1,222 | **2,081** |
| Blank | 910 | **51** |
| Invalid filled | 0 | **0** |

---

## Prior-fix / trace checks

| Check | Result |
|-------|--------|
| 9010713704C `MBANKNO` | Unchanged `104000016/47374579` |
| 9010161748C | Filled `091303855/0000002000581` |
| 9010157076C | Filled `104910135/212919` |
| 9010348734C | Filled `081518113/208787` |
| Issue #26 MPREM | Not in scope; quikridr not modified |
| Issue #2 MPOLICY keys | Unchanged (apply touched `MBANKNO` only) |

---

## Gate (G6)

- [x] Row counts stable
- [x] Unrelated fields unchanged
- [x] Prior banking regression guard held
- [x] Schema intact
- [x] Issue validator PASS

**PASS → Closure**
