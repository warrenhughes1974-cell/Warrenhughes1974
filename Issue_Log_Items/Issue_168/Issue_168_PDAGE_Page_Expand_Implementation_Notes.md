# Issue #168 — PDAGE page expansion (L05 and the same load)

**Framework stage:** Development  
**Approved:** Warren, 2026-09-22, in chat ("go through our development process and fix these").  
**Supersedes:** the 2026-09-14 planning note that L05 had no source row. The factor is on the PDAGE page; the load was keeping only VALUE1.  
**Engine:** v59.21

## What changed

PDAGE `DURATION` is a page. `VALUE1` through `VALUE10` are the ten policy years on that page. Year = (page − 1) × 10 + column.

Miss-fill used to write one row per page, using `VALUE1` and the page number as the year. It now writes one row per nonzero value, with the real policy year. Net premium still shifts one year earlier on the way into QuikNps (year 32 lands on CNTL 03, NP1). Reserve and dividend years stay on the same year as LifePRO.

When that terminal grid is all zeros, equal-class collapse folds it to class `00`. Admin does not read `00` for a Standard or Preferred policy, and it will not use the net premium without a terminal row at the policy's class. After that collapse, a zero terminal row is put back on each net-premium class. `5667AT` is left to the existing Issue #169 patch. Plans that already have a nonzero terminal factor are not copied.

## Before / after — 9011097650

Plan `5L0510`, issue age 28, female, class ST, generation 19000101. 50 units. LifePRO year 32 factor 15.59. Net premium 779.50. Reserve 389.75.

| | CNTL 00 | Year 32 |
|---|---|---|
| Before | NP0 1.38, NP1 3.87, NP2 7.21, NP3 15.59, NP4 40.86, NP5 78.19 | blank (those numbers are page 1 through page 6, first column only) |
| After | NP0 1.38, NP1 1.44 (years 1 and 2) | CNTL 03 NP1 = 15.59 |

A QuikTvs row at the same age, sex, and class is required even though every terminal factor is zero.

## Files

- `qla_core/pdage_missfill.py`
- `qla_core/rate_emit.py`
- `app.py` and `QLA_Migration/app.py` (v59.21)
- `tests/test_pdage_missfill_page_expand.py`
- `tools/validators/validate_issue168_pdage_page_expand.py`

## Emit (2026-09-22)

Rate tables regenerated from the 8/31 extracts (`v59.21`). Validator PASS: `5L0510` age 28 F ST, CNTL 00 NP0 = 1.38, NP1 = 1.44, CNTL 03 NP1 = 15.59, and a QuikTvs row exists at that class.

Zero terminal rows were also restored on `5L0110`, `5L075Y`, `5CDT10`, `542STR`, `543CTR`, `7619PU`, and `7SDT10`. L14 class copies and the 667 ART terminal rows were re-checked PASS. The 1995 substitution grids still match PDAGE (633,044 cells).

QLAdmin has not been revalued, so the five L05 dollar reserves are not on a new QuikValf yet.

## Not this change

L14 class copies, 667 ART, and the 1995 substitution generations. Those already expand pages or are patched after the load. L14 stays in the April rate file, so miss-fill does not touch it.
