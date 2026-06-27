# Issue 21M-FU — Implementation Summary

**Issue:** Merge QUIKMEMO to one row per `MEMOKEY`  
**Framework stage:** Development Agent (Stage 5)  
**Generated:** 2026-06-24  
**Scope:** Surgical — `qla_core/quikmemo_converter.py` only

---

## Files Modified

| File | Change |
|------|--------|
| `qla_core/quikmemo_converter.py` | Added `MEMO_SEGMENT_SEPARATOR`, `_merge_segments_by_memokey()`; merge after existing sort; `segment_rows` stat |

**Not modified:** `app.py`, `QLA_Migration/app.py`, DBF generator, rulebooks, packaging, MPREM/MPOLICY logic.

---

## Code Changes

1. **`MEMO_SEGMENT_SEPARATOR = "\n---\n"`** — inter-segment delimiter (interim until production DBT verified).
2. **`_merge_segments_by_memokey()`** — groups sorted segments by `MEMOKEY`; joins `MEMOTEXT` with separator; preserves `MEMOKEY` verbatim (Issue #25).
3. **Post-sort merge** — existing sort keys unchanged (`_sort_a/_b/_c` desc, `_src_order` asc); merge runs after sort, before return.
4. **Stats** — `segment_rows` = pre-merge count (29,279); `emitted_pnote` / `emitted_pense` = segment counts; `emitted_rows` = post-merge (4,380).

---

## Before / After Row Counts

| Metric | Before (v57.33) | After (21M-FU) |
|--------|----------------:|---------------:|
| QUIKMEMO rows | 29,279 | **4,380** |
| Unique `MEMOKEY` | 4,380 | **4,380** |
| Duplicate `MEMOKEY` groups | 3,466 | **0** |
| Max rows per `MEMOKEY` | 207 | **1** |
| PNOTE segments | 6,003 | 6,003 (in merged blobs) |
| PENSE segments | 23,276 | 23,276 (in merged blobs) |
| `segment_rows` | — | 29,279 |

---

## Validation Results (Development-run)

| Check | Result |
|-------|--------|
| CSV generation | PASS — `QLA_Migration/Output/quikmemo.csv` (4,380 rows) |
| DBF generation | PASS — `quikmemo_uat_dbf/quikmemo.dbf` (4,380 rows) |
| DBT generation | PASS — `quikmemo.dbt` (5,486,148 bytes) |
| Duplicate `MEMOKEY` | **0** |
| `MEMOKEY` width = 10 | **0 violations** |
| `MEMOKEY` ⊆ `quikmstr.MPOLICY` | **0 orphans** |
| Policy `010335038C` | **1 row**; both PNOTE texts present; 1 `\n---\n` separator |
| DBF/DBT co-located | PASS — `quikmemo_uat_dbf/` |

---

## Regression — Issues #25 and #26

| Check | Result |
|-------|--------|
| `quikmstr.MPOLICY` width = 10 | PASS (0 violations) |
| `quikridr.MPREM` column present | PASS (unchanged) |
| `quikmstr` rows | 5,083 (unchanged) |
| `quikridr` rows | 7,002 (unchanged) |
| `quikprmh` rows | 205,577 (unchanged) |
| `quikplan` rows | 141 (unchanged) |
| `quikclid` rows | 46,753 (unchanged) |
| `quikclnt` rows | 13,846 (unchanged) |

---

## Assumptions

1. **Separator `\n---\n`** is interim per Risk Agent until `QUIKMEMO_ex.DBT` is supplied.
2. **`[PNOTE]` / `[ENS]` headers** retained per segment inside merged blob.
3. **Sort order** unchanged from pre-FU converter; merge preserves sorted segment order within each `MEMOKEY`.
4. **`groupby("MEMOKEY", sort=False)`** preserves post-sort row order within each key group.
5. **Engine version** not bumped in `app.py` per Development scope restriction (converter module only); Validation Agent may bump if required by release policy.

---

## Next Stage

**Validation Agent** — full batch + updated `_validate_issue21m_quikmemo.py` expected counts (4,380 rows, duplicate-key check).
