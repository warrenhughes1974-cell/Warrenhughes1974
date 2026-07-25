# Issue #105 — Implementation Notes

**Issue:** #105 — QuikRidr MPAR for participating products  
**Date:** 2026-07-24  
**Release:** v58.30  
**Status:** Implemented v58.30 — Validation PASS

---

## Change summary

`quikridr.MPAR` is set from **product** `quikplan.PAR` by the row’s `MPLAN`:

| Condition | MPAR |
|-----------|------|
| `quikplan.PAR(MPLAN) == 1` | `1` (participating / True) |
| Otherwise / unknown plan | `0` |

PPBENTYP `PAR_TYPE` is no longer authority for this flag (still loaded for log continuity only).

---

## Code touched

| File | Change |
|------|--------|
| `app.py` / `QLA_Migration/app.py` | Load product PAR map from Output `quikplan.csv` on quikridr emit; set MPAR from map; bump **v58.30** |
| `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv` | Note on MPAR authority |
| `tools/validators/validate_issue105_mpar.py` | Issue validator |
| `QLA_Migration/_validate_issue105_mpar.py` | Wrapper |
| `tools/validators/validate_issue_log_accountability.py` | Register `#105` job + spot-check |

---

## Output impact (current full Output)

| Metric | Value |
|--------|------:|
| Rows `MPAR` `0 → 1` | 2,895 |
| Rows remaining `MPAR=0` | 4,039 |
| Total `quikridr` rows | 6,934 (unchanged) |

---

## Trace (after)

| MPOLICY | MPHASE | MPLAN | MPAR | Plan PAR |
|---------|--------|-------|------|----------|
| 9010143726C | 1 | 221END | **1** | 1 |
| 9010148272C | 1 | 221END | **1** | 1 |
| 9010382520C | 1 | 196065 | **1** | 1 |
| 9010391228C | 1 | 1970JB | 0 | 0 |

---

## UAT reload

Partial reload: `QLA_Migration/Output/Test_Validation/quikridr.csv`
