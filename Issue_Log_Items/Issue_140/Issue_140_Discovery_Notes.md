# Issue #140 — Discovery Notes (Search & Discuss)

**Issue:** #140 — Attained-age rate grids stored on the wrong axis (gross premiums blank in QLAdmin)
**Date:** 2026-08-09
**Framework stage:** Stage 0 Discovery (G-D)
**Related:** #138 (age offset — the deferred "Still open" item 2), Issue A7 (VARGP/VARDB derivation)
**Code:** None
**Scope agreed with Warren:** all affected rate tables (`QuikGps`, `QuikCoi`, `QuikGcoi`, `QuikDbs`, `QuikNff`, `QuikNps`)

---

## Client / user ask

> "Why did we not change the gross premium rates. They still aren't loading and are blank."

Screenshot evidence: `evidence/QLAdmin_1658CS_GrossPrems_blank_20260809.png` — plan `1658CS`, screen titled
**Gross Premiums - Values Vary by Attained Age**, Gender `F`, UW Class `ST`, Band `00`, Country `0000`,
State `00`, Effective `01/01/1900`. Every value renders `0.00` for ages 38 onward.

---

## Verdict

The rates are present and numerically correct. The **storage layout** is wrong.

Issue #138 corrected *which age* each rate belongs to (LifePRO `SEQ` is 1-based, so it shifted the axis
down one year). It did **not** change *how* the grid is written. That was recorded at the time as
`Issue_138_Resolution_Summary.md` → "Still open" item 2, "Attained-age storage axis … is unresolved and
is **not** changed here." That deferred item is the cause of the blank screen.

---

## How QLAdmin actually stores a rate grid

Confirmed against real QLAdmin reference tables in `plan_analysis/source_data/reference_dbf/`:

| Reference table | Plan | `AGE` | `CNTL` | Values live in |
|---|---|---|---|---|
| `QuikDbs.dbf` | `1GRDWL` | `00` | `00`,`01`,`02`,… | `DB0`–`DB9` |
| `QuikCvs.dbf` | `1TSTWL` | `41`, `46` (real issue ages) | `00`–`08` | `CV0`–`CV9` |

The series always runs **across the ten factor columns with `CNTL` paging**. `AGE` is the *issue-age key*
only, and is `00` when the grid does not vary by issue age.

Schema inventory agrees: `plan_analysis/phase_r2_rate_physical_structure/rate_dbf_physical_structure_inventory.csv`

- `AGE` — "Issue age (or 00 when grid varies by policy-year/duration only)"
- `CNTL` — "Duration page: column n = duration (CNTL*10 + n). CONFIRMED"

**Slot index = `CNTL × 10 + n`.**

---

## What we emit today

`1658CS` gross premiums: **388 rows**, one per attained age 15–85, `CNTL` always `00`, value only ever in `GP0`.

There is **no `AGE='00'` row at all**. The QLAdmin screen shows an Issue Age list containing only `00`,
selected — it is reading the row keyed `AGE='00'` and pulling the age series out of `GP0`–`GP9` across
`CNTL` pages. Nothing is there, so every cell reads `0.00`.

### Contrast with a table that displays correctly

Warren confirmed Terminal Reserves render fine on the same plan.

| Table (same plan `1658CS`) | Rows | Distinct AGE | CNTL pages | Factor columns used |
|---|---:|---:|---|---|
| `QuikTvs` (displays) | 1,031 | 76 | `00`–`05` | `0`–`9` |
| `QuikGps` (blank) | 388 | 71 | `00` only | `0` only |

---

## Scope — plans stored one-row-per-age with the value only in column 0

| Table | Plans in table | Affected | Examples |
|---|---:|---:|---|
| `QuikGps` | 109 | **97** | `1658CS`, `1L14SC`, `1L10SO`, `130JEB`, `1659C2` |
| `QuikDbs` | 23 | **10** | `130JEB`, `1970JB`, `542STR`, `578STR`, `719CDT` |
| `QuikNff` | 23 | **6** | `1658CS`, `1668SP`, `1679CS`, `1SALMI`, `1SALML` |
| `QuikCoi` | 2 | **2** | `1658CS`, `1679CS` |
| `QuikGcoi` | 1 | **1** | `1679CS` |
| `QuikNps` | 76 | **1** | `1L17SP` |
| `QuikCvs` / `QuikDvs` / `QuikTvs` | 48 / 21 / 84 | **0** | already correctly shaped |

All 97 affected `QuikGps` plans are exactly the plans carrying `VARGP=3`.

---

## Shape of the fix (not implemented)

For an attained-age grid, write `AGE='00'` and place the rate for attained age *A* at
`CNTL = A // 10`, column `<prefix>(A % 10)`.

Worked example — `1658CS` F/ST, current values age 38 = `.35`, 39 = `.37`, 40 = `.38`:

| Attained age | Target CNTL | Target column | Value |
|---:|---|---|---|
| 38 | `03` | `GP8` | `.35` |
| 39 | `03` | `GP9` | `.37` |
| 40 | `04` | `GP0` | `.38` |

This lines up with the ages the QLAdmin screen is displaying.

---

## Coupling risk to flag before Development

`qla_core/quikplan_rate_variation_flags.py` → `classify_factor_grid()` derives `VARGP` from the emitted
grid (Issue A7). After restructuring, an attained-age grid presents as **one age with many duration
slots**, which that function classifies as `1` (varies by policy year). Left alone it would silently
downgrade all 97 plans from `3` to `1` and trade one wrong screen for another. The classifier has to be
handled in the same change set.

Also to confirm during Planning:

1. Whether `VARGP=3` remains the right code once the grid is on the `AGE='00'` axis, or whether QLAdmin
   expects a different code for that shape.
2. Whether the 5 flat-rate ADB rider plans and the 18 ISWL/banded plans from #138 behave the same way.
3. Whether `#138`'s one-year offset is still correct once values move onto the slot axis — the offset was
   proven against `quikridr.MPREM`, which is independent of layout, so it should hold, but it must be
   re-proven after the move.

---

## Prior-fix conflict check

No Closed row in `Completed_Issues_Release_Validation_Guide.md` is contradicted. Row **A7** (VARGP/VARDB
derived from emitted grids) is *extended*, not reversed — the codes stay data-derived, but the classifier
must recognise the corrected attained-age shape. Row **#138** stays valid; this issue completes the item
it deferred.

---

## Stop

Discovery complete. No code changed. Awaiting **"Proceed to Intake"**.
