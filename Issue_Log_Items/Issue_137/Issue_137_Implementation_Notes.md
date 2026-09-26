# Issue #137 — Implementation Notes

**Issue:** #137 — Names-tab Modalized Annual Premium  
**Engine:** v58.80  
**Date:** 2026-08-05  

## Change

Blank `ANN_PREM_PER_UNIT` → `quikridr.MPREM` fallback no longer uses crude payments-per-year (`×12/×4/×2`). It uses:

```text
MPREM = MODE_PREMIUM ÷ (modal_factor% / 100) ÷ NUMBER_OF_UNITS
```

Mode / bill-form factor selection matches Discovery (monthly DIR→MTHD, PAC→MTHB, etc.). If the plan factor is missing, keep the old crude annualization and count it.

Populated ANN (#26) is unchanged. `MMODEPREM` is unchanged.

## Files

| File | Change |
|------|--------|
| `qla_core/modal_premium_factors.py` | `blank_ann_annual_ppu`, factor helpers |
| `app.py` / `QLA_Migration/app.py` | v58.80 interceptor + BILLING_FORM / factor caches |
| `Sync_Rulebook_quikridr.csv` | Comment only |
| `tools/validators/validate_issue137_modalized_mprem.py` | Gold + fleet blank-ANN |
| `tools/validators/validate_issue88_mprem_unit_fallback.py` | Expect modalized blank path |
| `Issue_137/tools/apply_issue137_modalized_mprem.py` | Surgical Output apply |

## Output apply

`python Issue_Log_Items/Issue_137/tools/apply_issue137_modalized_mprem.py`  
→ updated **1,027** MPREM values; published `Output/Test_Validation/quikridr.csv`.

Gold `9010722550C`: MPREM **8.71966** × 50 = **435.98** (was 481.32).
