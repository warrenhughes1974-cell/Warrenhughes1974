# DG-R-010 — Regression

**Date:** 2026-07-19

| Guard | Result |
|-------|--------|
| No QuikDbs / QuikPlDb / QuikPlan DBF writes | **Pass** |
| DG-QUIKPLAN-025 (VARGP ≠ 4) | Untouched |
| Sync_Rulebook VARDB default 0 | Unchanged |
| Rule still fails when VARDB 1/2/3 missing tables | **Pass** (unit test) |

**CLOSED** — open DG-R-011 next (Mortality / ETI / QuikQxs).
