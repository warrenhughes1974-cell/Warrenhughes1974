# Issue #76 — Implementation Notes

**Issue:** ETI/RPU phase-1 pay-up + duration for CV anniversary dates  
**Version:** v57.93  
**Date:** 2026-07-15  
**Model:** Composer 2.5 (Development)

---

## Change summary

Post-map hook on phase-1 `quikridr` rows: when `quikmstr.MSTATUS` is **44** or **45**, set `MPAYUP` = `MPAIDTO` and `MLASTANN` = **run-year − pay-up year**. Runs after `_apply_quikridr_mlastann` and before emit. Uses `quikmstr.csv` status/paid-to cache (quikmstr must convert first in rebatch).

Issue **#60** PUA deferred rows are unchanged (phase > 1).

---

## Files changed

| File | Change |
|------|--------|
| `app.py` | `APP_VERSION` v57.93; `_apply_issue76_eti_rpu_phase1_payup_mlastann`; `_qm_paidto_cache`; call + log |
| `QLA_Migration/app.py` | Mirror |
| `tools/validators/validate_issue76_eti_rpu_payup.py` | New |
| `Issue_Log_Items/Issue_76/scripts/rebatch_issue76_quikridr.py` | New |

**Not changed:** rulebooks, `quikmstr`, rates.

---

## Before / after trace (expected)

| Policy | Phase | MPAYUP before | MPAYUP after | MLASTANN before | MLASTANN after |
|--------|------:|---------------|--------------|-----------------|----------------|
| 010407670C | 1 | 20270201 | **20121001** | 53 | **14** |
| 010407670C | 2 | 19720201 | 19720201 | 53 | 53 |
| 010367131C | 1 | (unchanged) | (unchanged) | issue-based | issue-based |

**Expected fleet:** 400 policies adjusted; 223 MPAYUP changes.

---

## Rebatch + validation

```bash
python Issue_Log_Items/Issue_76/scripts/rebatch_issue76_quikridr.py
python tools/validators/validate_issue76_eti_rpu_payup.py --publish-test-validation
```

Publish on PASS: `Output/Test_Validation/quikridr.csv`

---

## UAT

Reload `Test_Validation/quikridr.csv` → Data Admin on `010407670C` → Rebuild CV → CV dates should anchor near paid-to anniversary (~2026), not 2080.
