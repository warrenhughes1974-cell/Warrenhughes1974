# Issue L14 — Validation Report

**Issue:** L14 — Cash Value Duration Off-by-One (QuikCvs)  
**Framework stage:** Validation  
**Date:** 2026-08-06  
**Engine:** v58.82  
**Result:** **PASS**

## Commands

```text
python Issue_Log_Items/Issue_L14/validate_issue_l14_quikcvs_duration.py
python Issue_Log_Items/Issue_98/validate_issue98_quikcvs_endpoint.py
python -m pytest tests/test_cv_l14_duration_identity.py -q
```

## Golds

| Check | Expected | Result |
|-------|----------|--------|
| `1L14SC` F/69 NS Dur2 | 14.73 | PASS |
| `1L14SC` F/69 NS Dur3 | 52.91 | PASS |
| `1L14SC` F/69 NS Dur31 | 1000 | PASS |
| `1L14SC` F/45 NS Dur2 | 8.37 | PASS |
| `1L14SC` F/45 NS Dur54 | 1000 | PASS |
| #98 `17085M` M/14 | Dur3=.06; terminal 1000 | PASS (regression) |

## Notes

Rates-only re-emit. Policy tables not rebatched. DBF pack must use Append Tool APPEND (not recreate).
