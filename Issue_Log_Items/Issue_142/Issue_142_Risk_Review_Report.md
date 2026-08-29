# Issue 142 — Risk Review Report

**Date:** 2026-08-29 · **Recommendation: GO** (with the mitigations below)

## Risk table

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Insured-amount duplication if a 9SUBLF row emits with MVPU ≠ 0 | Low | High (the exact defect this issue exists to avoid) | Fail-closed smoke check 3: **every** 9SUBLF row MVPU = 0; INITVAL = 0.00 on the plan so edits cannot re-introduce value; validation asserts total amount insured unchanged on all 22 policies |
| R2 | Regression on non-SL rows (blast radius of the app.py quikridr edit) | Low | High | Edit is a partition of already-isolated SL rows inside the existing filter block; regression compare requires byte-identical non-SL quikridr rows and untouched quikmstr |
| R3 | QLAdmin behavior with zero-VPU premium-bearing phases | Low | Medium | Direct in-book precedent: 25 existing rows (9FTRWP/9CTRWP) with MUNIT>0, MVPU=0, MPREM>0 already load and run through valuation |
| R4 | Modal premium display off vs LifePRO (single factor set vs per-form factors 0.0833–0.088 / 0.25–0.27) | Certain (by design) | Low | Warren accepted rounding (decision 4); Eric states riders do not bill (decision 3); annual per-unit premium is exact |
| R5 | Valuation file now shows 22 new 9SUBLF phases | Certain (by design) | Low | This is the requested outcome (visibility everywhere); zero insured amount, zero reserve (no rates, VPU 0); note in resolution for Eric's next valuation compare |
| R6 | MPLAN authority governance error if catalog/quikplan ordering wrong | Low | Medium | Catalog identity entry + quikplan seed land in same commit; batch emits quikplan before quikridr; validator confirms no new GOVERNANCE_ERROR traces |
| R7 | quikuwpo missing 9SUBLF × UW class rows (A11 dupe/missing check) | Medium | Low | UW classes on the 22 rows are 0/S/B/P; validation runs the A11 check; add generator rows only if the generic path misses them |
| R8 | Weakening Issue #27 lets unwanted SL rows leak in a future extract | Low | Medium | Suppression stays fail-closed for non-active SL rows; smoke count-floor (≥22) plus MVPU=0 guard runs on every release via SMOKE_JOBS |
| R9 | 9010987095 premium double-count with its 976659 waiver rider | Low (Eric: not billing) | Low | Decision 3 — assume no billing; anchor explicitly listed in validation report for Eric's UAT |

## Blast radius

- **Tables written:** quikridr (+22 rows), quikplan (+1 row), product catalog (+1 mapping row),
  possibly quikuwpo (+≤4 rows). Nothing else.
- **Code touched:** app.py quikridr SL block (partition + 2 column transforms),
  `qla_core/sl_benefit_governance.py` (active predicate + docstring),
  quikplan seed step, APP_VERSION bump ×2, new validator script.
- **Not touched:** schemas, field order/types, rate values, quikmstr, billing, crosswalks
  other than the one additive catalog row.

## Go / No-Go

**GO.** All five scope decisions locked by Warren (2026-08-29), dependency gate CLEAR,
Issue #27 override approved in writing, rollback is a single-commit revert.

**Awaiting explicit Development approval before any production code.**
