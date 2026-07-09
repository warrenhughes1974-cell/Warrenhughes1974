# Issue #41 — Implementation Notes

**Issue:** CV Age/Duration Endpoint Off by One  
**Date:** 2026-07-06  
**Status:** Implemented — validation PASS; client UAT pending  
**Scope:** QuikCvs / CV duration-index mapping only

---

## Change summary

Issue #41 changes the CV-only duration mapping introduced by Issue #37 so QLAdmin duration index reaches the **attained age 100** endpoint.

Prior behavior:

```text
ql_duration = lp_duration - 1
```

Corrected behavior:

```text
ql_duration = lp_duration
```

The LifePRO first-duration offset from Issue #37 is preserved. Non-CV rate families still use the existing `source_duration_to_ql()` path.

---

## Files changed

| File | Change |
|------|--------|
| `qla_core/rate_factor_loader.py` | CV remap now returns the LifePRO policy duration index directly, keeping the age-100 endpoint in QLAdmin. |
| `QLA_Migration/_validate_issue37_quikcvs_placement.py` | Updated proof mapping to the Issue #41 endpoint convention. |
| `QLA_Migration/_validate_issue37_g5_matrix.py` | Added `1960PO` M/26 proof case and updated emitted CSV anchor from `CV3` to `CV4` for M/22 first value. |
| `QLA_Migration/_validate_issue41_quikcvs_endpoint.py` | New source-vs-QLA validator with client anchor and multi-plan examples. |
| `QLA_Migration/Output/rates/QuikCvs.csv` | Regenerated from corrected CV grid only; 26,495 rows. |

---

## Regression boundaries

Unchanged:

- `quikplan`, `quikridr`, `quikmstr`, and policy conversion logic
- Non-CV rate families (`QuikNps`, `QuikGps`, `QuikDbs`, `QuikDvs`, `QuikTvs`)
- Product crosswalks and inherited-CV logic from Issue #40
- Rate values themselves

Known blocker outside Issue #41:

| Blocker | Impact |
|---------|--------|
| `V-UINT-PDINT` / missing `PDINTTBL` for `QuikUint` | Full guarded R5 emit still reports one blocker. Issue #41 regenerated only `QuikCvs.csv` from the corrected validated grid. |

---

## Validation commands

```powershell
python "QLA_Migration\_validate_issue37_quikcvs_placement.py"
python "QLA_Migration\_validate_issue41_quikcvs_endpoint.py"
python "QLA_Migration\_validate_issue37_g5_matrix.py"
```

All Issue #41 / CV placement checks passed. Full guarded emit remains blocked by the unrelated `QuikUint` dependency.

---

## Next steps

1. Client reloads the regenerated `QLA_Migration/Output/rates/QuikCvs.csv` into QLAdmin.
2. Client verifies `1960PO` / CV / Male / issue age `26` / band `01` / UW class `00`.
3. Confirm QLAdmin screen shows:
   - `784.65` at duration `57`
   - terminal `1000.00` through attained age `100`
4. Resolve or temporarily scope out the unrelated `QuikUint` blocker before running the full guarded rate emit.
