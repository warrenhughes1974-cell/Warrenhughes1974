# Issue #32 — Files Modified

**Version:** v57.40  
**Date:** 2026-06-29  
**Issue:** Policy Loan Conversion (PLOAN → QuikLoan)

---

## Modified files

| File | Type | Description |
|------|------|-------------|
| `plan_governance/config/quikloan_derivation_rules.json` | Modified | Bumped to v1.2: `AS_PERCENT`, `ZERO_AT_CONVERSION`, `QUIKPLAN_LOANINTX`, default `A`, ACCRUAL_DATE-first MLOANIDT |
| `qla_core/quikloan_converter.py` | Modified | v1.2 mapping: MLOANACCR=0, MLOANINTX plan lookup, quikmstr orphan audit, `mloanintx_fallback_audit.csv`, trace columns |
| `plan_analysis/phase_l1_quikloan/quikloan_runner.py` | Modified | Issue #32 runner; passes `quikplan_path` and `quikmstr_path` to converter |
| `app.py` | Modified | v57.40 header/UI/log strings; QuikLoan batch branch wires quikplan/quikmstr paths (still env-gated) |
| `QLA_Migration/app.py` | Modified | Mirror v57.40 QuikLoan batch branch and version strings |

---

## New files

| File | Type | Description |
|------|------|-------------|
| `tools/validators/validate_quikloan_issue32.py` | New | Issue #32 fleet + trace validator (17 checks) |

---

## Refreshed QA / audit outputs (generated)

| File | Rows | Purpose |
|------|-----:|---------|
| `plan_analysis/phase_l1_quikloan/quikloan_emit_candidates.csv` | 384 | Included emit policies |
| `plan_analysis/phase_l1_quikloan/quikloan_emit_exceptions.csv` | 529 | Zero-balance held + blocked |
| `plan_analysis/phase_l1_quikloan/mloanintx_fallback_audit.csv` | 913 | MLOANINTX fallback to A |
| `plan_analysis/phase_l1_quikloan/quikmstr_orphan_audit.csv` | 0 | MPOLICY not in quikmstr |
| `plan_analysis/phase_l1_quikloan/quikloan_mapping_trace.csv` | 913 | Full mapping trace |
| `plan_analysis/phase_l1_quikloan/zero_balance_loan_policies.csv` | 528 | Zero-balance latest policies |
| `plan_analysis/phase_l1_quikloan/missing_invalid_dates.csv` | 1 | Blocked date policy |
| `plan_analysis/phase_l1_quikloan/ploan_profile_summary.txt` | — | Fleet profile stats |

---

## Files explicitly NOT modified

- `QLA_Migration/Mapping/Master_Crosswalk.csv`
- `QLA_Migration/Configs/Sync_Rulebook_*.csv`
- `qla_core/quikridr_converter.py` / SL suppression (#27)
- `qla_core/quikmemo_converter.py` (#21M, #21J)
- `qla_core/cso_mortality_crosswalk.py` (#21D)
- `qla_core/sl_benefit_governance.py` (#27)
- Issue #21K schema migration tooling
- Premium / MODE_PREMIUM / quikplan core mapping logic

---

## Version consistency

| Location | Version |
|----------|---------|
| `app.py` header + UI | v57.40 |
| `QLA_Migration/app.py` header | v57.40 |
| `quikloan_derivation_rules.json` | 1.2 |
| `Release_Notes/v57.40_Release_Notes.md` | v57.40 |
