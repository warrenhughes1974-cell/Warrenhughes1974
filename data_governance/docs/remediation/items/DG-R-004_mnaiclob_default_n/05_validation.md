# DG-R-004 — Validation

**Date:** 2026-07-18  
**Data region:** `Q:\CSO\CSO_Test_6_30_2026`  
**Overall:** Target rule **Passed** (DG-QUIKPLAN-024)

---

## Command run

From repo root:

```bash
python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2026" --output "c:\Users\warren\Documents\GitHub\Warrenhughes1974\data_governance\docs\remediation\items\DG-R-004_mnaiclob_default_n\validation_out" --rule DG-QUIKPLAN-024
```

---

## Results

| Rule | Status | Records | Passed | Failed |
|------|--------|--------:|-------:|-------:|
| DG-QUIKPLAN-024 (MNAICLOB = NAPLAN) | **PASS** | 142 | 142 | 0 |

| Metric | Value |
|--------|-------|
| Overall result | **Passed** |
| Records checked | 142 |
| Problems found | 0 |
| Percentage passed | 100.00% |
| Source modified | False |

---

## Run folder

`validation_out/DG-20260718_190940_097704/`

---

## Unit tests

```bash
python -m pytest data_governance/tests/test_dg_quikplan.py -q
```

Result: **8 passed**
