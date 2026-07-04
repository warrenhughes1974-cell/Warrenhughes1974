# Issue #13 — Implementation Notes

**Issue:** Incorrect QL Status (Option A)  
**Engine:** v57.48  
**Date:** 2026-07-04  
**Framework stage:** Development (G4)

---

## Change summary

When `CONTRACT_CODE = T`, `quikmstr.MSTATUS` is derived from **`CONTRACT_CODE` + `CONTRACT_REASON`** only. `PAID_UP_TYPE` is ignored for terminated contracts. Non-terminated contracts retain PAID_UP_TYPE-first logic.

---

## Files changed

| File | Change |
|------|--------|
| `app.py` | MSTATUS interceptor + v57.48 |
| `QLA_Migration/app.py` | Mirror |
| `plan_analysis/status_analysis/status_analysis_runner.py` | `derive_mstatus_from_source_fields()` parity |
| `tools/validators/validate_issue13_mstatus.py` | New validator |

---

## Before / after trace

| Policy | Before | After |
|--------|-------:|------:|
| 010516211C | 44 | **54** |
| 011101663C | 41 | **56** |
| 010397318C | 45 | **53** |
| 010464590C | 45 | **53** |
| 010784054C | 56 | 56 |

Fleet impact (simulated): **607** policies change MSTATUS.

---

## Validation

```powershell
python tools/batch_tests/run_full_batch_test.py
python tools/validators/validate_issue13_mstatus.py
```

**G5 result (2026-07-04):** PASS — 5/5 trace policies, 0 fleet mismatches, 607-policy change population confirmed, `010516211C` quikridr MPHSTAT=54.

---

## Rollback

Revert MSTATUS interceptor block in `app.py` / `QLA_Migration/app.py` to PAID_UP_TYPE-first logic (v57.47).
