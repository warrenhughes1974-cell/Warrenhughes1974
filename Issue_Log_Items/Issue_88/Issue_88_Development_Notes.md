# Issue #88 — Development Notes

**Engine:** v58.23  
**Model:** Cursor Grok 4.5 (one-time Development override 2026-07-21)  
**Commit:** none (user will validate first)

## Change

Blank `ANN_PREM_PER_UNIT` fallback for `quikridr.MPREM`:

`MPREM = MODE_PREMIUM × ann_factor(BILLING_MODE) / NUMBER_OF_UNITS`

Factors: 12→1, 6→2, 3→4, 1→12 (default annual if mode missing).  
Populated ANN path unchanged (#26).  
`quikmstr.MMODEPREM` untouched.

## Files touched

- `app.py` / `QLA_Migration/app.py` — interceptor + PPOLC BILLING_MODE cache
- `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv` — comment only
- `tools/validators/validate_issue88_mprem_unit_fallback.py`
- `Issue_Log_Items/Issue_88/_rebatch_quikridr.py`

## Validation (local)

- Rebatch quikridr: PASS (log `QLA_Migration/Logs/_issue88_quikridr_rebatch_log.txt`)
- Validator: **PASS** — `010779727C` MPREM=5.8615; MMODEPREM=2930.75; #26 traces unchanged; 0 mismatches / 6934 joined
- Published: `QLA_Migration/Output/Test_Validation/quikridr.csv`

## UAT for user

1. Reload `Test_Validation/quikridr.csv` (or full Output quikridr)
2. Policy `010779727C`: Prem/Unit ≈ 5.86; Mode Prem still 2,930.75
3. Re-run valuation when ready — Mode Prem should not be ~1.465M
