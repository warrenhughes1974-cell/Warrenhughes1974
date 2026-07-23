# Issue #2 — Implementation Notes

**Issue:** #2 — 11 Character Policy Number  
**Engine:** `APP_VERSION` **v58.29**  
**Date:** 2026-07-23  
**Status:** In Development → Validation (full batch required)

---

## Change summary

Replaced LifePRO→QLA policy identity:

| Before | After |
|--------|-------|
| Master_Crosswalk strip-9 + `C` (e.g. `010143726C`) | Keep source + append `C` (e.g. `9010143726C`) |
| `format_qladmin_mpolicy` width **10** (#25) | Width **11**, right-justified |

---

## Files changed

| File | Change |
|------|--------|
| `qla_core/normalize_utils.py` | Issue #2 formatter |
| `app.py` / `QLA_Migration/app.py` | Skip policy CW on MPOLICY; claims/prmh; v58.29 |
| `qla_core/quikplan_converter.py` | Skip MPOLICY CW |
| `qla_core/quikmemo_converter.py` | Source + C; CW membership only |
| `qla_core/quikmemo_dbf_generator.py` | MEMOKEY C(11) + rjust rewrite |
| `qla_core/quikloan_converter.py` | Source + C |
| `qla_core/quikbenh_loan_history_converter.py` | Source + C |
| `qla_core/quikisrr_loader.py` | Shared formatter |
| `qla_core/reinsurance_lookups.py` | Source + C |
| `qla_core/balancing.py` | Source + C |
| `qla_core/issue78_quikclmp_recovery.py` | Reverse = strip trailing C |
| `tools/validators/validate_mpolicy_width.py` | Width 11 / Issue #2 samples |
| `QLA_Migration/_validate_issue2_mpolicy.py` | Issue validator |

---

## Trace (formatter)

| LifePRO | QLA MPOLICY |
|---------|-------------|
| `9010143726` | `9010143726C` |
| `901222DC` | `  901222DCC` |
| `9014059` | `   9014059C` |
| `9014100C` | `  9014100CC` |

---

## Validation

1. Full conversion batch (`tools/batch_tests/run_full_batch_test.py`)
2. `python QLA_Migration/_validate_issue2_mpolicy.py`
3. Publish affected tables to `Output/Test_Validation/` on PASS
