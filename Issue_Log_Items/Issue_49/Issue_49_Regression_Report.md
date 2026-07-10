# Issue #49 — Regression Report

**Issue:** #49 — QuikMstr Active Phase Status  
**Framework stage:** Stage 7 — Regression  
**Engine:** **v57.70**  
**Date:** 2026-07-10  
**Result:** **PASS**

---

## Scope of rebatch

| Table | Action |
|-------|--------|
| `quikmstr` | Reconverted from PPOLC under v57.70 |
| `quikridr` | Reconverted from PPBEN under v57.70 (inherit follows new `MSTATUS`) |
| Other tables | Not rebatched in this validation slice |

Script: `Issue_Log_Items/Issue_49/_rebatch_quikmstr_quikridr.py`  
Log: `QLA_Migration/Logs/_issue49_quikmstr_quikridr_rebatch_log.txt`

---

## Comparison vs pre-v57.70 baseline

| Check | Baseline | After | Pass? |
|-------|----------|-------|-------|
| `quikmstr` row count | 5,083 | 5,083 | Yes |
| `quikridr` row count | 6,934 | 6,934 | Yes |
| `MSTATUS` value changes | — | **35** | Yes (expected) |
| Change set | — | Exact match to `evidence/issue49_override_candidates.csv` | Yes |
| Transition | — | All **54 → 22** | Yes |
| Non-candidate `MSTATUS` | — | **0** unexpected changes | Yes |

---

## Guardrails

| Guard | Result |
|-------|--------|
| Issue #13 traces (`010516211C`, `011101663C`, …) | Unchanged / PASS |
| Preserve NFO samples (`018187C`=45, `010380550C`=41) | PASS |
| No blank `MSTATUS` introduced | PASS (5,083 populated) |
| Candidate-only blast radius | PASS |

---

## Note on failed first rebatch attempt

An initial single-table run incorrectly reused PPOLC + quikplan rulebook and produced blank outputs. Baselines were **restored** from `evidence/*_pre_v5770_baseline.csv` before the corrected rebatch. No lasting Output corruption.

---

**Stage 7 verdict:** **PASS**
