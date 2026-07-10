# Issue #49 — Regression Report

**Issue:** #49 — QuikMstr Active Phase Status  
**Framework stage:** Stage 7 — Regression  
**Engine:** **v57.71**  
**Date:** 2026-07-10  
**Result:** **PASS**

---

## Scope of rebatch

| Table | Action |
|-------|--------|
| `quikmstr` | Reconverted from PPOLC under v57.71 |
| `quikridr` | Reconverted from PPBEN under v57.71 (phase-1 inherit uses provisional MSTATUS) |
| Other tables | Not rebatched in this validation slice |

Script: `Issue_Log_Items/Issue_49/_rebatch_quikmstr_quikridr.py`  
Log: `QLA_Migration/Logs/_issue49_quikmstr_quikridr_rebatch_log.txt`  
Partial UAT package: `QLA_Migration/Output/Test_Validation/`

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
| Override candidate phase-1 `MPHSTAT` | baseline | **unchanged** on all 35 | Yes (v57.71) |

---

## Guardrails

| Guard | Result |
|-------|--------|
| Issue #13 traces (`010516211C`, `011101663C`, …) | Unchanged / PASS |
| Preserve NFO samples (`018187C`=45, `010380550C`=41) | PASS |
| No blank `MSTATUS` introduced | PASS (5,083 populated) |
| Candidate-only blast radius | PASS |
| `01ML8007C` shape | MSTATUS=22, phase1=54, phase2=22 — PASS |

---

## Validator

```powershell
python tools/validators/validate_issue49_mstatus.py --publish-test-validation
```

Checks: simulated override count (35), output MSTATUS match, preserve traces, non-candidate MSTATUS unchanged, phase-1 MPHSTAT unchanged, row counts.

---

## Note on failed first rebatch attempt

An initial single-table run incorrectly reused PPOLC + quikplan rulebook and produced blank outputs. Baselines were **restored** from `evidence/*_pre_v5770_baseline.csv` before the corrected rebatch. No lasting Output corruption.

**v57.70 gap:** Phase-1 `MPHSTAT` flipped on override candidates until v57.71 provisional inherit fix. Regression now asserts phase-1 unchanged.

---

**Stage 7 verdict:** **PASS**
