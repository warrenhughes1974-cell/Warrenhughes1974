# Issue #110 — Intake Summary

**Issue:** #110 — `MDIVOPT` (dividend option) empty fleet-wide
**Date:** 2026-07-25
**Framework stage:** Intake → Development (expedited)
**Status:** In Development — `v58.34`
**Owner:** Conversion (Warren)
**Priority:** High
**Parent:** Spun out of #108 track 108F
**Related:** #2 (root cause), #21A, #108, #109

---

## Symptom

`quikmstr.MDIVOPT` is `0` on **all 5,083 policies**. The dividend option is being dropped for the entire book.

## Evidence

Measured against `QLA_Migration/Output/quikmstr.csv` at v58.31:

| Value | Policies |
|---|---:|
| `0` | 5,083 |
| anything else | 0 |

`MDIVOPT` is enriched from the PPBENTYP cache at `app.py:7702–7705`, on the same enrich-on-zero branch as `MNFOPT`:

```python
if t_f in ['MNFOPT', 'MDIVOPT'] and val in ["", "0", "0.0"] and t_id.lower() == "quikmstr":
    ...
    legacy_id = reverse_cw_map.get(pol_id, pol_id)
```

`reverse_cw_map` is built from the retired `Master_Crosswalk.csv` `New_Value` column and resolves **0 of 5,083** live keys after the Issue #2 key change, so the lookup never succeeds and the rulebook default of `0` survives to emit.

## Root cause

Identical to #108 track 108F and #109: Issue #2 (v58.29, 2026-07-23) adopted source + `C` at width 11 and superseded Issue #25's strip-9 crosswalk, but this enrichment path still resolves through the retired crosswalk column.

## Why separate from #108F

Same one-line repoint, but a different field, a different source column, and a different validation surface. `MDIVOPT` is not a non-forfeiture field and does not belong in #108's NFO scope.

**Coupling to be decided before v58.33:** because both fields sit on the same branch, repointing the key for 108F will change `MDIVOPT` at the same time unless the fix is deliberately gated to `MNFOPT` only. Options are to scope #110 into the v58.33 release intentionally, or to gate the repoint and ship #110 separately.

## Affected tables

`quikmstr.MDIVOPT`.

## In scope

- Confirm the PPBENTYP source column and value translation (`DV_*` prefix) still map correctly
- Size the affected population from PPBENTYP
- Repoint the cache key

## Out of scope

- `MNFOPT` (#108F)
- The Issue #71 provisional cache (#109)
- `quikdvdp` / `quikdvpr` dividend accumulation tables

## Immediate blockers

None for diagnosis. One decision required: whether #110 ships with v58.33 or separately.

## Intake disposition

**Expedited to Development by the user on 2026-07-25** (Omaha data deadline), shipping as `v58.34` immediately after v58.33 rather than waiting for a separate Planning and Risk pass.

### Pre-implementation checks completed in place of Planning

**Translation coverage.** `Master_Value_Translation.csv` carries all 11 `DV_*` entries, covering every raw value present in the extract: `DV_0`→0, `DV_1`→1, `DV_2`→2, `DV_3`→3, `DV_4`→4, `DV_5`→5, `DV_6`→0, `DV_7`→0, `DV_8`→0, `DV_9`→0, `DV_RU`→0.

**Recoverable population.** PPBENTYP sequence-1 rows carry these `DIVIDEND` values:

| Raw | Rows | Translates to |
|---|---:|---|
| (blank) | 2,502 | not cached |
| `9` | 1,610 | 0 |
| `4` | 479 | **4** |
| `3` | 292 | **3** |
| `0` | 153 | 0 |
| `1` | 33 | **1** |
| `2` | 7 | **2** |
| `6` | 7 | 0 |

2,581 policies have a usable value, matching the `DIVIDEND` cache size logged during the v58.33 batch. **811 policies should receive a non-zero `MDIVOPT`**; the remaining 1,770 cached values legitimately translate to 0.

**Ordering.** The enrichment at `app.py:7767` runs before the `DV_` translation at `app.py:7959`, so recovered raw values are translated normally.

### Risk accepted

Blast radius is one field on one table. The change is the same three-line fallback added for `MNFOPT` in v58.33, and the crosswalk paths are retained as fallbacks so no policy that was already resolving can regress. Verification is a field-by-field diff against the v58.33 output, which must show `MDIVOPT` as the only column that moved.
