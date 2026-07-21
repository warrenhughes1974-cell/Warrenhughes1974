# Issue #58 — Implementation Notes

**Issue:** #58 — Premium Mode Amounts Incorrect  
**Engine version:** **v57.80**  
**Date:** 2026-07-13  
**Framework stage:** Development (G4)

---

## Change summary

Post-emit enrichment after Issue #36 plan-factor copy and PAC overrides:

1. `apply_modal_policy_fees_to_quikridr(ridr_df, mstr_df)` in `qla_core/modal_premium_factors.py`
2. Base phase (`MPHASE` 1 / 01) only; skip `MANNLFEE ≤ 0`
3. `M*FEE = MANNLFEE × (post-PAC quikmstr factor / 100)` · 4 decimal places
4. Rewrites `quikridr.csv` after `quikmstr.csv` factor enrichment

---

## Files changed

| File | Change |
|------|--------|
| `qla_core/modal_premium_factors.py` | `apply_modal_policy_fees_to_quikridr` |
| `app.py` / `QLA_Migration/app.py` | Wire + log; **v57.80** |
| `tools/validators/validate_issue58_quikridr_modal_fees.py` | New validator |

---

## Untouched

- `MANNLFEE` (#21C), `MPREM` / `MMODEPREM` (#26), `quikmstr` factor copy (#36), PAC overrides (#21J)
- `quikplan` ANNLFEE…MTHBFEE defaults
- Rider phases > 1

---

## Trace (unit test on baseline + factors)

| Policy | MQTRLFEE | MMTHDFEE | Names Q / Mth (sim) |
|--------|----------|----------|---------------------|
| 010367131C | 2.7666 | 0.9396 | 15.90 / 5.40 |
| 010560185C | 2.6100 (PAC Q) | 0.9396 | — |

---

## Validation

```text
python tools/validators/validate_issue58_quikridr_modal_fees.py
```

Requires full batch so `quikmstr` factors are populated (not stale Output).

---

## Regression notes

- 4,457 base rows gain modal fee fields when `MANNLFEE > 0`
- ISWL Names-tab UAT still recommended (Conditional Go OBQ-1)
