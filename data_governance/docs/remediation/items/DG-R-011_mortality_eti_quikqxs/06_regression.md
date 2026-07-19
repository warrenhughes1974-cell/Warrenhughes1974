# DG-R-011 — Regression

**Date:** 2026-07-19

| Guard | Result |
|-------|--------|
| No QuikPlCv / QuikPlTv / QuikQxs DBF writes | **Pass** |
| DG-PLANVALUES-003 (blank PLAN still fails) | Untouched (`allow_blank` default False) |
| Missing/unknown MORT/ETIMORT still FAIL | **Pass** (unit test) |
| Conversion mortality crosswalk blank-safe | Unchanged |

**CLOSED** — open DG-R-012 next (advisory 027/028).
