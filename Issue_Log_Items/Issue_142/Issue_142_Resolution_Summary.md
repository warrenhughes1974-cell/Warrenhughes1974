# Issue 142 — Resolution Summary

**Closed:** 2026-08-29 (engine v59.04)
**Short name:** SL Policies — Bring in the SL Rider on Active Policies

## What was fixed

Active Substandard Life (SL) rating rows now load into QLAdmin as their own rider phase under new plan code **9SUBLF** ("SUBSTANDARD LIFE PREMIUM RIDER") with **value-per-unit zero**, so the extra rating premium is visible on the policy without duplicating the insured amount. This narrows the Issue #27 blanket SL suppression to non-active SL rows only (Warren-approved override 2026-08-29).

- All **22** active (STATUS_CODE=A) SL rows emit; the **8** premium-bearing red-font policies carry source `ANN_PREM_PER_UNIT` as MPREM.
- Outlier 9010782078C (mode premium $8.05, 0 units) emits with MPREM 0 as agreed.
- The 46 terminated/non-active SL rows remain suppressed with the Issue #27 audit trail.
- 9SUBLF seeded in quikplan (PAR=0, VARDB=0, VARGP=4 no-rate-table, supplemental 9* pattern) and identity-mapped in both product catalog crosswalks.

## G7 gate

| Requirement | Status |
|---|---|
| Issue validator PASS on full Output | PASS — `python tools/validators/validate_issue142_sl_rider.py` |
| Accountability IN_DATA for #142 | IN_DATA (run 2026-08-29; 70 IN_DATA / 14 WARN / 4 GAP, all GAPs pre-existing, none on 142 tables) |
| Test_Validation published | quikplan.csv + quikridr.csv |
| Completed Issues guide row + high-risk smoke row | Added 2026-08-29 |
| SMOKE_JOBS registered + `--smoke-only` PASS on the job | `#142 SL rider 9SUBLF` PASS |
| DBF Append package rebuilt | 43/43 APPEND OK, Desktop output 2026-08-29 |

## Known pre-existing exceptions (not waived, not 142)

- `--smoke-only` overall RELEASE_BLOCKED solely on **#59 MSTATUS allowlist** (quikmstr drift from the 8/28 batch; quikmstr untouched by 142). Review before next release handoff.
- Accountability GAPs #76 / #114 / #59:010521213C / #135 pre-existing on non-142 tables.

## Files

- Engine: `app.py` + `QLA_Migration/app.py` v59.04; `qla_core/issue142_sl_rider.py`; `qla_core/sl_benefit_governance.py`; `qla_core/quikplan_converter.py`
- Mapping: `QLA_Migration/Mapping/product_catalog_crosswalk.csv`; `plan_governance/product_catalog_crosswalk.csv`
- Validators: `tools/validators/validate_issue142_sl_rider.py` (new); `validate_issue55_munit_floor.py` + `validate_issue70_loanintx.py` made 9SUBLF-aware (class A stale counts); registered in `validate_release_closed_issues.py` SMOKE_JOBS and `validate_issue_log_accountability.py`
- Reports: `Issue_142_Validation_Report.md`, `Issue_142_Regression_Report.md`, evidence under `Issue_Log_Items/Issue_142/evidence/`
