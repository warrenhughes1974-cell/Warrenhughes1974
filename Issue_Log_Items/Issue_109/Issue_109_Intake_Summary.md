# Issue #109 — Intake Summary

**Issue:** #109 — Issue #71 phase-1 provisional status cache is inert
**Date:** 2026-07-25
**Framework stage:** Intake complete (G0)
**Status:** Open — Planning
**Owner:** Conversion (Warren)
**Priority:** Medium
**Parent:** Spun out of #108 track 108F
**Related:** #2 (root cause), #49, #71, #108

---

## Symptom

The Issue #71 provisional status cache never populates. Phase-1 `MPHSTAT` therefore falls back to `_qm_status_cache`, which holds the **post-Issue-#49** policy status — precisely the behaviour Issue #71 was written to prevent. Issue #71 is marked **closed**.

## Evidence

`app.py:7867` builds the cache key by routing the source policy number through the forward crosswalk and then re-formatting it:

```python
_prov_pol = self.normalize(self._format_qladmin_mpolicy(cw_map.get(_lp, _lp)))
```

Since Issue #2 (v58.29, 2026-07-23), `cw_map` returns the **retired** 10-character value (`010143726C`), which `format_qladmin_mpolicy` then treats as un-suffixed and appends a second `C` to, producing `010143726CC`.

| Measure | Result |
|---|---:|
| Provisional-cache keys built | 5,194 |
| Overlap with emitted `MPOLICY` | **0** |

Verified empirically against `QLA_Migration/Output/quikmstr.csv` at v58.31.

## Root cause

Same as #108 track 108F: Issue #2 replaced the strip-9 crosswalk with source + `C` at width 11 and superseded Issue #25, but two code paths still resolve keys through the retired crosswalk columns. Issue #2 realigned the identity paths it knew about (claims, prmh, loan, benh, isrr, memo) and missed this one.

## Why separate from #108

Different population, different validator, and a different regression surface (`MSTATUS`/`MPHSTAT` interaction rather than `MNFOPT`). Folding it into #108 would blur the NFO scope and complicate #108's regression attribution.

## Affected tables

`quikridr.MPHSTAT` (phase 1) — magnitude not yet measured; that is the Planning task.

## In scope

- Repoint the provisional cache key to the emitted `MPOLICY` identity
- Quantify how many phase-1 rows currently inherit a post-#49 status that #71 intended to block
- Re-verify Issue #71's original assertions

## Out of scope

- Issue #49's override logic itself
- The `MNFOPT`/`MDIVOPT` enrichment path (#108F, #110)

## Immediate blockers

None. Root cause is confirmed and the fix location is known.

## Intake disposition

Open. Planning should measure the affected phase-1 population before sizing the fix. Note this is a **closed-issue regression**, so Closure will need to re-validate Issue #71 as well.
