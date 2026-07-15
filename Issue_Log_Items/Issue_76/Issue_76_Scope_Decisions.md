# Issue #76 — Scope Decisions

**Locked for Planning / Risk:** 2026-07-15  
**Authority:** User answers (1=A, 2=A, 3=A) + YE UAT screenshots on `010407670C`

| ID | Decision |
|----|----------|
| **SD-76-1** | For policies with final `quikmstr.MSTATUS` ∈ {**44**, **45**}, set phase-1 `quikridr.MPAYUP` = `quikmstr.MPAIDTO` (paid-to date). |
| **SD-76-2** | For those same phase-1 rows, set `MLASTANN` = **current system year − year(MPAYUP)** (calendar-year duration). Screenshot proof: 2026 − 2012 = **14**. |
| **SD-76-3** | Apply **only** to **MPHASE=1**. Do not change later phases under this issue. |
| **SD-76-4** | Preserve Issue **#60** PUA inheritance (`MPAYUP=MEFFDATE` on PUA product rows). #76 must not overwrite PUA rows. |
| **SD-76-5** | Do not change LifePRO contractual `PAY_UP_DATE` mapping for non-44/45 policies (keep `PAY_UP_DATE→MPAYUP`). |
| **SD-76-6** | Do not invent `MCV0/1/2` amounts — leave traditional blank; client runs Data Admin + Rebuild CV after reload. |
| **SD-76-7** | Do not change `MEFFDATE`, `MAGE`, `MEXPRY`, `MUNIT`, `MPREM`, `MNFOPT` (#72), rates, or BAND. |
| **SD-76-8** | **Current year source (Planning default):** use conversion **run date** year (`datetime.now().year`), matching screenshot `t=14` on 2026-07-15. If YE package must freeze to `QLA_VALUATION_DATE` year (2025 → duration 13), Risk/Dev may add env override — flag as OBQ-76-1. |
| **SD-76-9** | Development only after G1+G2+G3; surgical engine hook; bump `APP_VERSION` both `app.py` copies. |
