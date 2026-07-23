# Issue #96 — Implementation Notes

**Issue:** CSO valuation cannot use SAL MULTPL / L17 RV rates (PVO + QuikPl* wiring)  
**App version:** v58.26  
**Date:** 2026-07-22  
**Stage:** Development (approved) → Validation next

---

## Durable changes

| Area | Change |
|------|--------|
| `plan_analysis/source_data/rates/CSO_Valuation_Setup.csv` | Added `1SALMI` with same PlCv/PlTv codes as `1SALOL` (O1/Q1/4 CV; O1/4/1 TV) |
| `qla_core/quikplan_rate_variation_flags.py` | `apply_factor_table_pvo_enablement` — when `QuikTvs`/`QuikCvs` rows exist for a plan, set `PLANVALOPT=Y` + `GDVARYTV`/`BDVARYTV` and/or `GDVARYCV`/`BDVARYCV`; skip A-prefix |
| Same | `apply_annuity_a8e_pvo_clear` after factor enablement so post-rate R7B refresh cannot leave annuity `PLANVALOPT=Y` |
| `app.py` + `QLA_Migration/app.py` | After rate loader SUCCESS/PARTIAL, call `integrate_quikplan_file` on Output `quikplan.csv` |
| Version | `APP_VERSION` → **v58.26** (both app.py copies) |

## Not changed

- QuikTvs factor values (Track 1 inheritance unchanged)
- Track 2 RV (L01/L05/L07/667 ART) — still held
- Claims / ridr / mstr / Issue #95 QuikUint

## Validator

```text
python Issue_Log_Items/Issue_96/validate_issue96_cso_pvo.py
```

Checks eight focus plans PVO + QuikTvs counts, `1SALMI` Pl* codes vs `1SALOL`, L17 child grids, and A8e annuity PVO=N.

## Regression risk

- Post-rate integrate rewrites `quikplan.csv` variation flags only (schema preserved).
- Annuity clear is mandatory on that path (Issue A A8e).
- Next full rate emit must include CSO setup row for `1SALMI` (already in CSV).
