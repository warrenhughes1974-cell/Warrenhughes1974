# Data Governance Remediation Tracker

**Started:** 2026-07-18  
**Control tower session:** active  
**Data region (audited folder):** `Q:\CSO\CSO_Test_6_30_2026` _(confirmed; `6_30_2025` was wrong folder name)_  
**Backup (DG-R-001):** prior backup path no longer present under `Q:\CSO`  
**Backup (DG-R-003):** `Q:\CSO\CSO_Test_6_30_2026_backup_DG-R-003_20260718`  
**Backup (DG-R-005):** `Q:\CSO\CSO_Test_6_30_2026_backup_DG-R-005_20260718`  
**Backup (DG-R-008):** `Q:\CSO\CSO_Test_6_30_2026_backup_DG-R-008_20260718`  
**Backup (DG-R-009):** `Q:\CSO\CSO_Test_6_30_2026_backup_DG-R-009_20260718`  
**Baseline report:** user-pasted findings (Group Billing / Plan Setup / Plan Values / Processing Dates)

| Item ID | Title | Status | Decision summary | Folder |
|---------|-------|--------|------------------|--------|
| DG-R-001 | Company codes G / V missing | **CLOSED** | Deleted QuikList GTEST01/TERMG/TEST1; remapped QuikChrt G/Vâ†’C (71) | [items/DG-R-001_company_codes_G_V](items/DG-R-001_company_codes_G_V/) |
| DG-R-002 | Test QuikList groups defaults | **DEFERRED (N/A)** | Groups deleted under DG-R-001; no defaults to fix | â€” |
| DG-R-003 | QuikDate prior-month-end | **CLOSED** | Live PAC/DIR/REINâ†’2026-06-30; conversion emit `quikdate.csv` @ v58.07; DG-QUIKDATE 001â€“006 PASS | [items/DG-R-003_quikdate_prior_month_end](items/DG-R-003_quikdate_prior_month_end/) |
| DG-R-004 | MNAICLOB default (N vs NAPLAN) | **CLOSED** | R1: DG-QUIKPLAN-024 â†’ NAPLAN; no QuikPlan data rewrite; 142/142 PASS | [items/DG-R-004_mnaiclob_default_n](items/DG-R-004_mnaiclob_default_n/) |
| DG-R-005 | HCOMMIP / HRIGPKEY logicals | **CLOSED** | Option A: CSO QuikPlan â†’ False Ã—142; Sync_Rulebook Default_Value=`F` (empty source â†’ F; preserve mapped T); see CONVERSION_SYSTEM_DEFAULTS.md | [items/DG-R-005_hcommip_hrigpkey](items/DG-R-005_hcommip_hrigpkey/) |
| DG-R-006 | Closed PLANVALOPT still on | **CLOSED** | Retired DG-QUIKPLAN-022 (no DBF writes); PVO independent of BACTIVE; Data_Goverence.txt corrected | [items/DG-R-006_closed_planvalopt](items/DG-R-006_closed_planvalopt/) |
| DG-R-007 | Age-1 LOAGE must be zero | **CLOSED** | R1: revised DG-QUIKPLAN-008 (drop LOAGE=0; keep LOAGE < HIAGE); no DBF writes; residual blank 0/0 -> DG-R-008 | [items/DG-R-007_loage_age1](items/DG-R-007_loage_age1/) |
| DG-R-008 | Blank plan + orphan plan values | **CLOSED** | Option A: deleted 9 blank-PLAN shells on CSO (QuikPlan+8 QuikPl*); 001/002/003/008 PASS; WPA orphans OOS; backup …_backup_DG-R-008_20260718 | [items/DG-R-008_blank_plan_orphans](items/DG-R-008_blank_plan_orphans/) |
| DG-R-009 | Targeted QuikPlan exceptions | **CLOSED** | SP: 6 plans PAYYRS=1 + modals 0; conversion v58.10 + single_premium_plans.csv; residuals: JPO×2, BASIS×2, 1970PA hold; RRULE WPA OOS | [items/DG-R-009_targeted_quikplan_exceptions](items/DG-R-009_targeted_quikplan_exceptions/) |
| DG-R-010 | Missing Death Benefit setup/values | **CLOSED** | R1: revised DG-QUIKPLAN-026 (require QuikDbs/QuikPlDb only when VARDB ∈ {1,2,3}); no DBF writes; CSO 40/40 PASS | [items/DG-R-010_death_benefit_setup](items/DG-R-010_death_benefit_setup/) |
| DG-R-011 | Mortality / ETI missing in QuikQxs | **CLOSED** | R1: revised DG-PLANVALUES-001/002 (skip blank/null; validate QuikQxs only when populated); no DBF writes; CSO 245/245 + 102/102 PASS | [items/DG-R-011_mortality_eti_quikqxs](items/DG-R-011_mortality_eti_quikqxs/) |
| DG-R-012 | Advisory warnings 027/028 | **CLOSED** | R1: revised 028 (Aint+Aexp+(Aing\|Ainf)); accepted 027 as audit; no DBF writes; CSO 028 residual A60MIR/A96DAR WARN | [items/DG-R-012_advisory_027_028](items/DG-R-012_advisory_027_028/) |

## Active item

None. Remediation queue **complete** (DG-R-001 … DG-R-012).

## Conversion system defaults

See [CONVERSION_SYSTEM_DEFAULTS.md](CONVERSION_SYSTEM_DEFAULTS.md) â€” rulebook/emit defaults so remediation is not DBF-only. DG-R-005: `HCOMMIP`/`HRIGPKEY` Default_Value=`F` in Sync_Rulebook_quikplan.csv.

## Future code note (from DG-R-001 discussion)

If QuikList rows again reference `MCOMP` not in QuikComp: **detect and hold** (governance FAIL + conversion hold list), do **not** auto-delete groups in production emit. Optional later: explicit remediation script with dry-run + approve list.

## Closed log

| Item | Closed | Notes |
|------|--------|-------|
| DG-R-001 | 2026-07-18 | List delete 3; Chrt remap 71; rules 002/032 PASS. Residual: quikgrpimp TERMGÃ—3; NTX may need reindex |
| DG-R-002 | 2026-07-18 | DEFERRED N/A â€” groups removed in 001 |
| DG-R-003 | 2026-07-18 | Live QuikDate PAC/DIR/REINâ†’2026-06-30; DG-QUIKDATE-001..006 PASS; emit quikdate.csv via qla_core/quikdate_converter.py; APP_VERSION v58.07 |
| DG-R-004 | 2026-07-18 | Rule DG-QUIKPLAN-024 â†’ NAPLAN (catalog/impl/tests/docs); no QuikPlan DBF writes; CSO 142/142 PASS; Sync_Rulebook already NAPLAN |
| DG-R-005 | 2026-07-18 | CSO QuikPlan HCOMMIP/HRIGPKEY â†’ `.F.` Ã—142 (0 MEDS); backup `â€¦_backup_DG-R-005_20260718`; DG-QUIKPLAN-030 142/142 PASS; follow-up: Sync_Rulebook Default_Value=`F` + CONVERSION_SYSTEM_DEFAULTS.md |
| DG-R-006 | 2026-07-18 | Retired DG-QUIKPLAN-022 from catalog/registry/runner/tests/docs; no QuikPlan data rewrite; Data_Goverence.txt notes PVO independent of BACTIVE |
| DG-R-007 | 2026-07-18 | Revised DG-QUIKPLAN-008: drop LOAGE must-be-0; keep LOAGE < HIAGE; no QuikPlan data rewrite; CSO 141/142 pass (1 blank 0/0 residual) |
| DG-R-008 | 2026-07-18 | Deleted 9 blank-PLAN shells on CSO (QuikPlan 142→141 + 8 QuikPl*); DG-QUIKPLAN-001/002/008 + DG-PLANVALUES-003 PASS; WPA orphans deferred |
| DG-R-009 | 2026-07-18 | SPWL×6 PAYYRS=1/PAYAGE=0 + modal 0; conversion apply_single_premium_payment_settings @ v58.10; residuals JPO/BASIS/1970PA |
| DG-R-010 | 2026-07-19 | Revised DG-QUIKPLAN-026: QuikDbs/QuikPlDb only when VARDB 1/2/3; no DBF writes; CSO 40/40 PASS |
| DG-R-011 | 2026-07-19 | Revised DG-PLANVALUES-001/002: skip blank/null MORT/ETIMORT; no DBF writes; CSO 245/245 + 102/102 PASS |
| DG-R-012 | 2026-07-19 | Revised 028 Aing/Ainf OR; accepted 027 advisory; no DBF writes; residual A60MIR/A96DAR |
