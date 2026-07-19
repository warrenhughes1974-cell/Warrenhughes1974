# DG-R-005 — Validation

**Date:** 2026-07-18  
**Data region:** `Q:\CSO\CSO_Test_6_30_2026`  
**Overall:** Target rule **Passed** (DG-QUIKPLAN-030)

---

## Command run

From repo root:

```bash
python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2026" --output "c:\Users\warren\Documents\GitHub\Warrenhughes1974\data_governance\docs\remediation\items\DG-R-005_hcommip_hrigpkey\validation_out" --rule DG-QUIKPLAN-030
```

---

## Results

| Rule | Status | Records | Passed | Failed |
|------|--------|--------:|-------:|-------:|
| DG-QUIKPLAN-030 (MEDS plan flags) | **PASS** | 142 | 142 | 0 |

| Metric | Value |
|--------|-------|
| Overall result | **Passed** |
| Records checked | 142 |
| Problems found | 0 |
| Percentage passed | 100.00% |
| Source modified | False |

---

## Post-check (logical decode / raw)

| Check | Result |
|-------|--------|
| `decode_logical(HCOMMIP)` | **False** × 142 |
| `decode_logical(HRIGPKEY)` | **False** × 142 |
| Raw HCOMMIP bytes | **`F`** × 142 |
| Raw HRIGPKEY bytes | **`F`** × 142 |
| MEDS rows | 0 (none expected True) |

---

## Run folder

`validation_out/DG-20260718_191349_142458/`
