# Issue #49 — Implementation Notes

**Issue:** #49 — QuikMstr Active Phase Status  
**Framework stage:** Stage 5 — Development  
**Engine:** **v57.70**  
**Date:** 2026-07-10  

---

## Change summary

When the first **QLAdmin-display** phase status is inactive (**≥ 50**) and a later emitted phase is active (**0–49**), `quikmstr.MSTATUS` is set to that first later active status. Otherwise Issue #13 / PPOLC behavior is unchanged.

## Files changed

| File | Change |
|------|--------|
| `qla_core/quikmstr_active_phase_status.py` | **New** — phase cache, display simulation, selection |
| `app.py` | v57.70; PPBEN cache on quikmstr; post–Issue #13 override |
| `QLA_Migration/app.py` | Same (must stay in sync) |
| `tools/validators/validate_issue49_mstatus.py` | **New** — simulate + optional output checks |

## Algorithm (as coded)

1. Issue #13 composite + `ST_*` → provisional `MSTATUS`.
2. Load PPBEN phases for the policy, **excluding** `BENEFIT_TYPE` ∈ `{UV, FV, SL}` (same as quikridr emit).
3. Simulate display statuses: phase 1 inherits provisional when not in `{11, 22, ACTIVE}`; later phases use bare-letter map.
4. If phase 1 ≥ 50, set `MSTATUS` to first later status in 0–49; else keep provisional.

## Validation (Development)

```text
python tools/validators/validate_issue49_mstatus.py --simulate-only
→ PASS — 35 overrides, all 54→22, matches evidence candidates
```

Output emit checks require a **quikmstr rebatch** under v57.70 (current Output is still pre-#49).

## Rollback

Revert the Issue #49 blocks in both `app.py` files, delete/ignore the helper + validator, restore `APP_VERSION` to v57.69.

## Next

Stage 6 — Validation (after quikmstr/full batch), then Stage 7 Regression.
