# Test and Validation Readiness

**Stage:** 3 — Assessment only (no golden files created)

## Current Coverage

| Area | Status |
|------|--------|
| Unit tests | **None** found under `tests/` |
| Integration tests | **None** automated |
| Regression fixtures | Draft Quik* + P7MN validation CSV only |
| Golden files | **Not established** |
| Reconciliation framework | **Not implemented** (design only) |
| Row-count checks | Partial (emit_summary / manifests) |
| Hash checks | Strong for **migration** (Stage 2B); not for conversion runs |
| Dimension checks | Informal in validators |
| Duplicate-key checks | `reserve_grid_collisions.txt` historical |
| Effective-date checks | **Not found** |
| Precision checks | Mentions of CHAR(7) warnings in legacy notes |
| Source-to-output traceability | Partial via issue evidence |

## Existing Validation Evidence (Historical)

- `validation/rate_validation/` — Issue 01/02/03 evidence CSVs
- P7MN Access checkpoint validation (reserve wave)
- PDF PermaLife7 pilot validation (gross premium)

## Initial Golden-File Plan Set (Recommended — Not Created)

| Candidate | Rationale |
|-----------|-----------|
| P7MN / P7FN / P7FS / P7MS | PermaLife 7 quad — richest validation history |
| Traditional WL (e.g. 802 family) | Traditional whole life |
| Term (e.g. TenYearTerm / CP* term forms) | Term product |
| PLP / PLP6 | Permanent product with large CV archive |
| Participating WL (if identifiable in tracker) | Dividend path later |
| Non-participating WL | Contrast |
| Graded benefit (GDB if confirmed) | Special benefit shape |
| Plan with riders (Five/Ten Year Term Rider Access tables) | Rider premiums |
| Plan with multiple rate eras | When effective dating exists |
| Substandard / rated (0D0G-type tracker rows) | Substandard factors |
| Unusual age/duration (juvenile PermaLife Access) | Dimension edge |

**Interest-sensitive / UL:** include only if Citizens inventory confirms presence — do not invent.

## Recommended Stage 4 Validation Issues

- CIT-VAL-001 Test framework scaffold
- CIT-VAL-002 Golden-file framework
- CIT-VAL-003 Reconciliation framework
- CIT-VAL-004 Precision / duplicate / dimension checks
