# Issue 21F — Implementation Notes (v57.73)

**Date:** 2026-07-11  
**Engine:** v57.73  
**Authority:** `Issue_21F_Development_Authorization.md`

## What changed

### Conversion Adjustment rows on `quikprmh`

After PACTG payment-history rows are materialized (batch only), the engine appends **one additive row** per eligible non-ISWL policy when LifePRO four-component total exceeds the sum of existing `quikprmh.PREMIUM` rows.

**Marker literals (audit):**

| Field | Value |
|-------|--------|
| `DATEPAID` | `20171231` |
| `MPOSTDATE` | `20171231` |
| `MSOURCE` | `CONV_ADJ` |
| `USER_ID` | `QLA21F` |
| `MBATCH` | `21F-ADJ` |
| `RENEWAL` | `0` |

**LifePRO total formula (v57.73 — typed aggregation):**

| Component | Rule |
|-----------|------|
| Base | Sum `PREMIUMS_PAID` on **BA/BF** rows only (OR excluded) |
| PUA | Sum `PU_PREMIUMS_PAID` on PU rows |
| Supplemental | Sum `SU_PREMIUMS_PAID` on SU rows (negatives included) |
| Substandard | Sum `SL_PREMIUMS_PAID` on SL rows |

**Excluded:** ISWL (`TYPE_CODE=BF`); negative gaps (exception report only).

**Idempotency (v57.73):** Strip all existing CONV_ADJ rows at start of each pass, then rebuild. Re-run produces identical output (no duplicate rows, UAT report stays correct).

**OPENING_BALANCE:** Policies with no prior history (`hist_total <= 0`) and positive adjustment get STATUS `OPENING_BALANCE` in validation report (359 policies in current batch).

## v57.73 fix pass (from Validation FAIL)

1. Validation report math — LOADED/OPENING show ADJUSTMENT, FINAL_TOTAL = LifePRO, REMAINING_VARIANCE = 0  
2. BA/BF-only base — removed ~13 OR-bleed policies from load set  
3. SU sum rule — multi-SU and negative SU handled by sum, not max  
4. Validator extended — fails if report variance ≠ 0 for loaded policies  

## Files

| File | Role |
|------|------|
| `qla_core/issue21f_premium_adjustment.py` | Totals, eligibility, row build, reports |
| `app.py` / `QLA_Migration/app.py` | Wire after quikprmh DataFrame build (batch) |
| `tools/validators/validate_issue21f_premium_adjustment.py` | Golden + report reconcile |
| `Issue_Log_Items/Issue_21/Issue_21F/_rebatch_quikprmh_21f.py` | Offline rebatch helper |

## Reports (not in Output)

- `QLA_Migration/Reports/issue21f_premium_adjustment_validation.csv`
- `QLA_Migration/Reports/issue21f_premium_adjustment_exceptions.csv`

## Batch stats (v57.73 rebatch)

| Metric | Value |
|--------|------:|
| CONV_ADJ rows loaded | 2,609 |
| OPENING_BALANCE | 359 |
| ISWL excluded | 2,348 |
| Negative exceptions | 3 |
| History rows (unchanged) | 206,861 |

## Validate

```powershell
python tools/validators/validate_issue21f_premium_adjustment.py --before QLA_Migration/Archive/quikprmh_pre_21f_v57.72.csv --publish-test-validation
python Issue_Log_Items/Issue_21/Issue_21F/_validate_issue21f_deep_audit.py
```
