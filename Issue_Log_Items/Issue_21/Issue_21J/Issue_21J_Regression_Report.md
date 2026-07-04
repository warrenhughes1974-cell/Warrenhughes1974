# Issue #21J — Regression Report (G6)

**Issue:** Modal Premium Factors  
**Date:** 2026-07-04  
**Engine:** v57.46  
**Stage:** Regression Agent — **PASS**

---

## Protected issues

| Issue | Result |
|-------|--------|
| #21J modal factors | **PASS** |
| #21M / #21M-FU quikmemo | **PASS** (baselines updated to 5,083 rows) |
| #21M DBF packaging | **PASS** |
| #25 MPOLICY padding | **PASS** |
| #26 MPREM / MMODEPREM | **PASS** |
| #38 MDEPOSIT | **PASS** (unchanged by 21J) |

---

## Row count regression

| Table | Count | Baseline | Status |
|-------|------:|---------:|--------|
| quikmstr | 5,083 | 5,083 | OK |
| quikridr | 6,934 | 6,934 | OK |
| quikprmh | 205,577 | 205,577 | OK |
| quikplan | 141 | 141 | OK |
| quikclid | 46,753 | 46,753 | OK |
| quikclnt | 13,514 | 13,514 | OK |
| quikmemo | 5,083 | 5,083 (21J) | OK — intentional increase from 4,380 |

---

## Intended vs unintended change

| Surface | Intended | Unintended |
|---------|----------|------------|
| quikplan ANNL–MTHB | 141 plans updated from client mapping | None |
| quikmstr MSEMI/MQTRL | 12 PAC GL85 policies | None |
| quikmemo MEMOTEXT | `[CONVERSION]` prepended fleet-wide | PNOTE/ENS segment counts unchanged |
| quikridr / quikprmh / MMODEPREM | No change | Verified |

---

## Validator baseline updates (G6)

- `validate_issue21m_quikmemo.py` v2.2 — 5,083 rows, 34,362 segments, `[CONVERSION]` order rules
- `validate_issue21m_dbf_packaging.py` — 5,083 rows; accepts `[CONVERSION]` prefix
- `validate_issue21j_modal_factors.py` — new

---

**G6 status:** PASS — proceed to G7 Closure.
