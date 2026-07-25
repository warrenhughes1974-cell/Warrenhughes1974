# Issue #113 — Intake Summary

**Issue:** #113 — Multi-source rate extracts (load from all dated PAAGE / PAAGERAT / PDAGE files)
**Date:** 2026-07-25
**Framework stage:** Intake → Development (delivered same day)
**Status:** Closed
**Owner:** Warren
**Assigned:** Warren
**Priority:** Go-No Go
**Related:** #42 (PDAGE miss-fill / rate path), rate pipeline R5

---

## Symptom

Rate conversion had to pull from **multiple dated LifePRO extract files** under `QLA_Migration/Source/` for each of three families:

- `PAAGE_AttainedAge_Rates_Extract_*.csv`
- `PAAGERAT_AttainedAge_Rates_Extract_*.csv`
- `PDAGE_AgeDuration_Rates_Extract_*.csv`

The resolver picked **one** hardcoded dated file per family (newest name only). That dropped rate rows that exist only in older dated drops when a newer file did not repeat them. PAAGE was not wired into the path resolver at all.

## Business rule (confirmed)

1. Keep **all three** families in the load path.
2. Newest = **filename** `_YYYYMMDD`, not Windows Date modified.
3. On duplicate natural keys: **newer filename wins**; keys only in older files are kept.

## Affected path

- `qla_core/plan_source_paths.py`
- `qla_core/dated_extract_merge.py` (new)
- `qla_core/rate_pipeline.py` (Issue #42 PDAGE miss-fill + PAAGERAT streams)
- Rate loader configs → staging merged CSVs

## Out of scope

- Inventing rates / changing TYPE_CODE mapping
- Using Windows Date modified
- Broad rate-pipeline redesign beyond discover + merge overlay
