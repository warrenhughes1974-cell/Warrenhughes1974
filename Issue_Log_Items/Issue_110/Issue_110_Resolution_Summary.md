# Issue #110 — Resolution Summary (Closure)

**Date:** 2026-07-25
**Release:** v58.34
**Table:** `quikmstr.MDIVOPT`

## What was wrong

`MDIVOPT` was 0 on all 5,083 policies — the dividend option was dropped for the entire book.

The enrichment resolves its PPBENTYP cache key through `reverse_cw_map`, which is built from
the `New_Value` column of `Master_Crosswalk.csv`. Issue #2 (v58.29) changed `MPOLICY` to
source + `C` at width 11 and retired the Issue #25 strip-9 convention, but the crosswalk was
never rebuilt, so every lookup missed. Same root cause as #108F, on the adjacent field.

## What changed

The cache lookup now tries the raw source `POLICY_NUMBER` first — the key the cache is
actually built on — keeping the crosswalk paths as fallbacks (`app.py` ~7811).

## Evidence

811 dividend elections recovered:

| MDIVOPT | Policies |
|---|---|
| 4 | 479 |
| 3 | 292 |
| 1 | 33 |
| 2 | 7 |
| 0 | 4,272 |

The 4,272 remaining zeros are legitimate: policies with no source value, plus values that
translate to 0 through `DV_6`–`DV_9`/`DV_RU`.

`MDIVOPT` is the only `quikmstr` column that moved. `MNFOPT` is unchanged and `quikridr` is
byte-identical to v58.33.

## G7 gate

| Requirement | Status |
|---|---|
| Issue validator PASS on full `QLA_Migration/Output/` | PASS |
| Accountability `IN_DATA` | IN_DATA |
| Affected table published to `Output/Test_Validation/` | `quikmstr.csv` |

`tools/validators/validate_issue110_mdivopt.py` was written for this issue. It does not
trust the emitted values — it rebuilds the expected election from PPBENTYP the way `app.py`
builds the cache (BENEFIT_SEQ 1, `DIVIDEND` column, `DV_*` translation) and requires an
exact match:

```text
validate_issue110_mdivopt v1.0
  source: PPBENTYP_BenefitType_Extract_20260630.csv
  rows=5083 nonzero_elections=811
  source reconciliation: checked=5083 mismatched=0
PASS
```

All 5,083 policies reconcile to source, so the recovered values are correct and not merely
non-zero. The validator resolves the extract by newest match rather than a hardcoded date,
which is what stranded several sibling validators.

## Process note

The user expedited this from Intake straight to Development on 2026-07-25 for the Omaha
deadline. Planning and Risk checks were done inline and recorded in the intake summary.

## Related

- `Issue_110_Intake_Summary.md`
- `Issue_110_Implementation_Notes.md`
- `Issue_Log_Items/Issue_108/` — #108F, same root cause
