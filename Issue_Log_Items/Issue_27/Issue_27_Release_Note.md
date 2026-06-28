# Issue #27 — Release Note (v57.39)

**Version:** v57.39  
**Date:** 2026-06-28  
**Type:** Bug fix — conversion defect

---

## What changed

LifePRO benefit type **SL (Substandard Life)** is no longer emitted as a separate `quikridr` coverage phase. SL represents substandard rating metadata in LifePRO, not an additional death benefit. QLAdmin handles substandard life through its product rating structure.

## Impact

- **68 quikridr rows removed** (7,002 → 6,934)
- **46 policies** no longer show duplicate face amount on Coverage tab
- **67 policies** with SL benefits — base coverage and PUA phases preserved
- **No change** to `quikmstr.MMODEPREM`, product setup, rulebooks, or crosswalks

## Example

Policy `010448806C` now shows **2** coverage rows (Base + PUA) instead of **3** (duplicate SL row removed).

## Audit

Suppressed SL rows logged to `Issue_Log_Items/Issue_27/Issue_27_SL_Suppression_Audit.csv` including `SL_TABLE_CODE` where populated in LifePRO.

## Rollback

Remove `SL` from the quikridr benefit-type filter in `app.py` (restore v57.38 behavior).

---

**Engine version:** v57.39
