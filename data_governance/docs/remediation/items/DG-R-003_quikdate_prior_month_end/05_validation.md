# DG-R-003 — Validation

**Date:** 2026-07-18  
**Data region:** `Q:\CSO\CSO_Test_6_30_2026`  
**Overall:** Target rules **Passed** (DG-QUIKDATE-001..006)

---

## Command run

From repo root:

```bash
python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2026" --output "data_governance/docs/remediation/items/DG-R-003_quikdate_prior_month_end/validation_out" --item DG-QUIKDATE
```

---

## Results

| Rule | Status | Records | Passed | Failed |
|------|--------|--------:|-------:|-------:|
| DG-QUIKDATE-001 (PACBILL prior month-end) | **PASS** | 1 | 1 | 0 |
| DG-QUIKDATE-002 (DIRBILL prior month-end) | **PASS** | 1 | 1 | 0 |
| DG-QUIKDATE-003 (REINBILL prior month-end) | **PASS** | 1 | 1 | 0 |
| DG-QUIKDATE-004 (ACHFILEID = 0) | **PASS** | 1 | 1 | 0 |
| DG-QUIKDATE-005 (ACHFILEID2 = A) | **PASS** | 1 | 1 | 0 |
| DG-QUIKDATE-006 (ESC_DATE blank) | **PASS** | 1 | 1 | 0 |

| Metric | Value |
|--------|-------|
| Overall result | **Passed** |
| Records checked | 6 |
| Problems found | 0 |
| Percentage passed | 100.00% |
| Source modified | False |
| Expected prior-month-end (July 2026 run) | **2026-06-30** |

---

## Run folder

`validation_out/DG-20260718_185125_518008/`

---

## Conversion emit unit test

```bash
python -m pytest data_governance/tests/test_quikdate_converter_emit.py -q
```

Result: **2 passed**
