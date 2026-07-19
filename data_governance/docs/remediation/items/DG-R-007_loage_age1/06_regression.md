# DG-R-007 — Regression

**Date:** 2026-07-18

| Guard | Result |
|-------|--------|
| No QuikPlan DBF writes | **Pass** |
| DG-R-004 NAPLAN / DG-R-005 logicals / DG-R-006 022 retired | Untouched by this change |
| Conversion MIN_ISSUE_AGE→LOAGE | Unchanged |
| Rule still catches LOAGE ≥ HIAGE | **Pass** (blank 0/0 fails) |

**CLOSED** — open DG-R-008 next.
