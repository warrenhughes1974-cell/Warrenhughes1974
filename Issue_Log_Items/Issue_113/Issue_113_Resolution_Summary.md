# Issue #113 — Resolution Summary

**Date:** 2026-07-25
**Status:** Closed
**Release note:** rate path merge (no `app.py` version bump — `qla_core` only)

## What was wrong

The converter had to load rates from multiple dated Source files, but the path resolver returned a single file per family. Unique rows present only in older extracts were lost; PAAGE was unused.

## What changed

1. **Discover** all dated `PAAGE_*` / `PAAGERAT_*` / `PDAGE_*` under `QLA_Migration/Source/` by filename `YYYYMMDD`.
2. **Merge** per family into staging (`QLA_Migration/Staging/{family}_dated_merged.csv`): newer filename overwrites the same natural key; older-only keys survive.
3. **Wire** `paage_extract()` / `paagerat_extract()` / `pdage_extract()` and `rate_pipeline.run()` to the merged paths; log files scanned and overlay counts each rate run.
4. Unit/smoke tests: older-only key kept; collision takes newer filename; filename date beats disk mtime.

## Evidence (Source smoke 2026-07-25)

| Family   | Dated files        | Merged rows | Older keys skipped (overlays) |
|----------|--------------------|------------:|------------------------------:|
| PAAGE    | 20260630→20260714  |         527 |                           931 |
| PAAGERAT | 20260630→20260714  |      31,653 |                        57,956 |
| PDAGE    | 20260630→20260714  |     352,395 |                       696,514 |

Tests: `qla_core/tests/test_dated_extract_merge.py` — 4 passed.

## G7 note

This issue owns the **rate extract load path**, not a `quik*.csv` policy table. Closure is against merge smoke + unit tests. Full rate re-emit remains the usual R5 / Issue #42 batch path when rates are regenerated for UAT.

## Related

- `Issue_113_Intake_Summary.md`
- `qla_core/dated_extract_merge.py`
- `qla_core/plan_source_paths.py`
- `qla_core/rate_pipeline.py`
