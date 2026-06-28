# Release Note — v57.38 / Issue #21J Rollback

**Version:** v57.38  
**Date:** 2026-06-28  
**Type:** Rollback

---

## Summary

**Rolls back** the Issue #21J QUIKMEMO `[CONVERSION]` modal premium factor memo introduced in v57.37. Quikmemo output returns to Issue #21M-FU behavior (PNOTE + PENSE only).

---

## What changed in v57.38

- Removed `append_issue21j_conversion_memos()` and all Issue #21J memo generation code
- `quikmemo.csv` row count: 5,083 → **4,380**
- No `[CONVERSION]` segments in QUIKMEMO output
- Removed Issue #21J deployment note from `QLA_Migration/RUN_GUIDE.md`

---

## What did NOT change

- Premium conversion (`MODE_PREMIUM` → `MMODEPREM`)
- QUIKPLAN modal factors (100 / 51 / 26.5 / 9.25 / 9.25)
- Rating logic, rulebooks, crosswalks
- Issue #21D, #21M, #26, #28, and other protected issue behavior

---

## Superseded

- **v57.37** Issue #21J memo feature — **withdrawn**
- `Issue_21J_Release_Note.md` — superseded by this document

---

## Issue #21J disposition

Planning Correction confirmed LifePRO policy-level Premium Quote modal factors are **not in source extracts**. The memo provided no incremental value beyond quikplan. Issue #21J tracking status remains **AWAITING CLIENT** for any future business decision on runtime premium display.

---

## Upgrade path

Run full batch at v57.38. Quikmemo regenerates to 4,380 PNOTE/PENSE-derived rows automatically.
