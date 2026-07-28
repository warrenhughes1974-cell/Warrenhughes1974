# Issue #121 — Implementation Notes

**Issue:** #121 — Annual Renewable Term must not emit ETI  
**Date:** 2026-07-28  
**App version:** **v58.44**  
**Status:** Development complete — Validation PASS

---

## Change summary

On ART-family policies (`667 ART` / `646 ART` / `667 ART CR` → `5667AT` / `5646AT` / `57ATCR`), `PAID_UP_TYPE` **LE** or **ET** no longer forces `PUT_*` → `MSTATUS` 44 (ETI). Status uses `CONTRACT_CODE` + `CONTRACT_REASON` instead (same path as blank PUT).

---

## Files changed

| File | Change |
|------|--------|
| `qla_core/issue121_art_no_eti.py` | **New** — ART plan sets, PUT suppress helper, PPBEN ART policy cache |
| `app.py` / `QLA_Migration/app.py` | v58.44; load ART cache with #49 PPBEN load; MSTATUS interceptor guard; log |
| `tools/validators/validate_issue121_art_no_eti.py` | **New** — zero ART ETI; traces; non-ART ETI preserved |
| `Issue_Log_Items/Issue_121/_rebatch_quikmstr_quikridr.py` | Headless rebatch |

---

## Before → after (Output rebatch)

| Metric | Before | After |
|--------|-------:|------:|
| ART family policies | 197 | 197 |
| ART `MSTATUS` 44 | **90** | **0** |
| ART `MPHSTAT` 44 | 90 | **0** |
| ART `MSTATUS` 22 | 11 | 96 |
| ART `MSTATUS` 54 | 71+2 | 78 |
| Non-ART ETI (control) | — | 120 (preserved) |

### Trace

| MPOLICY | Plan | Before | After |
|---------|------|--------|-------|
| 9010764158C | 5667AT | 44 | **22** |
| 9010780202C | 5667AT | 44 | **22** |
| 9010761450C | 5667AT | 44 | **54** |
| 9010516211C | 5646AT | 54 | 54 |
| 9010916282C | 57ATCR | 54 | 54 |

---

## Rollback

1. Revert interceptor `#121` branch and ART cache load in both `app.py` copies.  
2. Remove `qla_core/issue121_art_no_eti.py` import.  
3. Set `APP_VERSION` back to v58.43.  
4. Rebatch `quikmstr` + `quikridr`.

---

## Validation

```text
python tools/validators/validate_issue121_art_no_eti.py --publish-test-validation
→ PASS
```

Published `quikmstr.csv` + `quikridr.csv` to `QLA_Migration/Output/Test_Validation/`.
