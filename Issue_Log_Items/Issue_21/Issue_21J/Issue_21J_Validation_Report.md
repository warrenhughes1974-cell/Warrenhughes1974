# Issue #21J — Validation Report (G5)

**Issue:** Modal Premium Factors  
**Date:** 2026-07-04  
**Engine:** v57.46  
**Stage:** Validation Agent — **PASS**

---

## Scope

Validate plan-level modal factor overlay on `quikplan`, PAC GL85 policy overrides on `quikmstr`, fleet-wide `[CONVERSION]` memos on `quikmemo`, and preservation of Issues #25 / #26.

---

## Batch

Full headless batch via `tools/batch_tests/run_full_batch_test.py` at v57.45; PAC overrides refreshed post-batch with v57.46 billing-form fix (`MBILLFRM=2` = PAC).

---

## Results

| Check | Result |
|-------|--------|
| `validate_issue21j_modal_factors.py` | **PASS** |
| quikplan factors (141 plans) | **PASS** — e.g. `1659C2` 52.5 / 27.0 / 9.1999 / 8.8018 |
| PAC GL85 overrides | **PASS** — 4 quarterly `MQTRL=25`, 8 semiannual `MSEMI=50` |
| quikmemo grain | **PASS** — 5,083 rows = 5,083 `[CONVERSION]` segments |
| #26 MPREM / MMODEPREM | **PASS** — `010713704C` MPREM 20.07680, MMODEPREM 43.91 |
| #25 MPOLICY width | **PASS** |

---

## Trace policies

| Policy | MPLAN | MMODEPREM | 21J note |
|--------|-------|-----------|----------|
| 010713704C | 1659C2 | 43.91 | Plan factors + memo |
| 010560185C | 170858 | 15.00 | MQTRL=25 + PAC memo |
| 010818663C | 1659C2 | — | Plan factors only |

---

**G5 status:** PASS — proceed to G6 Regression.
