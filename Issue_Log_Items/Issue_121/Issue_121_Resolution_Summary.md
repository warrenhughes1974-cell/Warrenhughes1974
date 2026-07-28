# Issue #121 — Resolution Summary

**Issue:** #121 — Annual Renewable Term must not emit ETI  
**Status:** Closed  
**Engine:** v58.44  
**Closed:** 2026-07-28  
**Accountability:** **IN_DATA** (`#121` spot-check + validator PASS)

---

```text
Resolution: Annual Renewable Term plans (5667AT, 5646AT, 57ATCR) no longer convert to Extended Term status; LifePRO LE/ET paid-up codes now follow the contract status instead. Examples fixed: 9010764158C and 9010764248C (44→Active 22), 9010761450C (44→Lapsed 54).
```

---

## What changed

- MSTATUS interceptor suppresses `PUT_LE` / `PUT_ET` on ART-family policies.
- Status uses `CONTRACT_CODE` + `CONTRACT_REASON` (Active → 22, Lapsed → 54, etc.).
- Phase-1 `MPHSTAT` follows (0 ART ETI after rebatch).
- Global `ST_PUT_LE → 44` unchanged for permanent products.

## Evidence

| Gate | Result |
|------|--------|
| Validation | **PASS** |
| Regression | **PASS** |
| Issue validator | **PASS** |
| Accountability `#121` | **IN_DATA** |
| Test_Validation publish | `quikmstr.csv`, `quikridr.csv` |

## Rollback

Revert v58.44 interceptor + `qla_core/issue121_art_no_eti.py`; rebatch quikmstr/quikridr.
