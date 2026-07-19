# Data Governance Remediation Tracker

**Started:** 2026-07-18  
**Control tower session:** active  
**Data region (audited folder):** `Q:\CSO\CSO_Test_6_30_2026` _(confirmed; `6_30_2025` was wrong folder name)_  
**Backup (DG-R-001):** prior backup path no longer present under `Q:\CSO`  
**Backup (DG-R-003):** `Q:\CSO\CSO_Test_6_30_2026_backup_DG-R-003_20260718`  
**Baseline report:** user-pasted findings (Group Billing / Plan Setup / Plan Values / Processing Dates)

| Item ID | Title | Status | Decision summary | Folder |
|---------|-------|--------|------------------|--------|
| DG-R-001 | Company codes G / V missing | **CLOSED** | Deleted QuikList GTEST01/TERMG/TEST1; remapped QuikChrt G/V→C (71) | [items/DG-R-001_company_codes_G_V](items/DG-R-001_company_codes_G_V/) |
| DG-R-002 | Test QuikList groups defaults | **DEFERRED (N/A)** | Groups deleted under DG-R-001; no defaults to fix | — |
| DG-R-003 | QuikDate prior-month-end | **CLOSED** | Live PAC/DIR/REIN→2026-06-30; conversion emit `quikdate.csv` @ v58.07; DG-QUIKDATE 001–006 PASS | [items/DG-R-003_quikdate_prior_month_end](items/DG-R-003_quikdate_prior_month_end/) |
| DG-R-004 | MNAICLOB NAPLAN → N | QUEUED | — | — |
| DG-R-005 | HCOMMIP / HRIGPKEY logicals | QUEUED | — | — |
| DG-R-006 | Closed PLANVALOPT still on | QUEUED | — | — |
| DG-R-007 | Age-1 LOAGE must be zero | QUEUED | — | — |
| DG-R-008 | Blank plan + orphan plan values | QUEUED | — | — |
| DG-R-009 | Targeted QuikPlan exceptions | QUEUED | — | — |
| DG-R-010 | Missing Death Benefit setup/values | QUEUED | — | — |
| DG-R-011 | Mortality / ETI missing in QuikQxs | QUEUED | — | — |
| DG-R-012 | Advisory warnings 027/028 | QUEUED | — | — |

## Active item

None. Next queued: **DG-R-004** (MNAICLOB NAPLAN → N). Say `Examine DG-R-004` to continue.

## Future code note (from DG-R-001 discussion)

If QuikList rows again reference `MCOMP` not in QuikComp: **detect and hold** (governance FAIL + conversion hold list), do **not** auto-delete groups in production emit. Optional later: explicit remediation script with dry-run + approve list.

## Closed log

| Item | Closed | Notes |
|------|--------|-------|
| DG-R-001 | 2026-07-18 | List delete 3; Chrt remap 71; rules 002/032 PASS. Residual: quikgrpimp TERMG×3; NTX may need reindex |
| DG-R-002 | 2026-07-18 | DEFERRED N/A — groups removed in 001 |
| DG-R-003 | 2026-07-18 | Live QuikDate PAC/DIR/REIN→2026-06-30; DG-QUIKDATE-001..006 PASS; emit quikdate.csv via qla_core/quikdate_converter.py; APP_VERSION v58.07 |
