# Issue #168 — Implementation Notes (L14 only)

**Issue:** #168 — L14 reserve/value class-key replication  
**Framework stage:** Development (completed 2026-09-14)  
**Engine / APP_VERSION:** unchanged (Output-apply only)

## What the change did

QLAdmin looks up reserve and cash-value factors by plan **and** underwriting class. For plan `1L14SC`, LifePRO uses one reserve grid for every class, but our load only stored that grid under class `NT`. Policies coded `PQ`, `PR`, or `ST` found no row and valued at $0.

The apply script copied every existing `NT` row onto `PQ`, `PR`, and `ST`. The numbers did not change. Only the class label on the copy changed.

## Tables written

`QuikTvs`, `QuikNps`, `QuikCvs`, `QuikNff`, `QuikPlTv`, `QuikPlCv`, `QuikPlDb`, `QuikPlDv` — 3,972 rows added. Existing `NT` rows were not edited.

## Not touched

`QuikGps`, `QuikPlGp`, `QuikPlUw`, `quikridr`, `quikplan` (`*VARY*` flags), L05/L01 plans, `app.py`.

## Script

`Issue_Log_Items/Issue_168/tools/apply_issue168_l14_reserve_class_replication.py`

Backup: `QLA_Migration/Archive/issue168_l14_20260915_010022/`
