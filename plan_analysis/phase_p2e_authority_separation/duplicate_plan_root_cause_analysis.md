# Duplicate PLAN 9DIS25 — Root Cause Analysis

**Date:** 2026-05-26 09:27:40
**Phase:** P2E

## Executive Conclusion

Duplicate PLAN `9DIS25` is **NOT** caused by Policy Form Crosswalk duplication.
The business crosswalk assigns **unique** QL Plan Codes per LifePRO COVERAGE_ID:

| COVERAGE_ID | Policy Form Crosswalk ql_plan_code |
|-------------|-----------------------------------|
| DISCHO2475 | 9DIS24 |
| DISCHO247C | 9DS24C |
| DISCHO25 | 9DIS25 |
| DISCHO247B | 9DS24B |

**Root cause:** Legacy **Master_Crosswalk product mapping collision** — multiple distinct
LifePRO COVERAGE_IDs mapped to the same QL PLAN code `9DIS25`, while the conversion engine
correctly emits **one quikplan row per source COVERAGE_ID**.

## Evidence Chain

1. **Baseline output:** 2 rows with PLAN=`9DIS25` (rows 99 and 101, 0-indexed 98 and 100)
2. **Source lineage:** Two active source COVERAGE_IDs produce the duplicate:

   - `DISCHO2475`: source_rows=1, Master_Crosswalk -> `9DIS25`
   - `DISCHO247C`: source_rows=1, Master_Crosswalk -> `9DIS25`

3. **Differentiated output fields:** The two emitted rows differ in PCOMP-driven fields:

| PLAN | MINUNIT | MAXUNIT |
|------|---------|---------|
| 9DIS25 | 1 | 1 |
| 9DIS25 | 0 | 99 |

4. **Rulebook:** Single PLAN rule (`COVERAGE_ID` -> `PLAN`) — no duplicate append logic.
5. **Emit logic:** One output row per source row — no duplicate append.
6. **Transform collision:** Master_Crosswalk overrides distinct COVERAGE_IDs to identical PLAN.

## Ruled Out

- Policy Form Crosswalk duplication (9DIS25 appears once, on DISCHO25 only)
- Source COVERAGE_ID duplication (`drop_duplicates` on COVERAGE_ID — 133 unique)
- Rulebook duplicate target rows for PLAN
- Subprocess double-emit or append logic

## Recommended Remediation (Business Review — Not Auto-Applied)

1. Assign distinct QL Plan Codes per LifePRO coverage (as Policy Form Crosswalk already defines:
   `9DIS24` for DISCHO2475, `9DS24C` for DISCHO247C).
2. Migrate PLAN authority to `product_catalog_crosswalk.csv` with business-approved codes.
3. Enable `CROSSWALK_OVERLAY=1` only after staged validation — not globally in P2E.
4. Do **not** suppress duplicate rows — resolve mapping collision at source.
