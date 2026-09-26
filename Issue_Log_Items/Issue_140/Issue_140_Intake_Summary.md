# Issue #140 — Intake Summary

**Issue:** #140 — Attained-age rate grids stored on the wrong axis (gross premiums blank in QLAdmin)
**Date:** 2026-08-09
**Framework stage:** Stage 1 Intake
**Code changed:** None (read-only research; one intake probe under `Issue_Log_Items/Issue_140/`)
**Engine at intake:** v58.89

---

## 1. Statement of the defect

Every gross premium screen in QLAdmin renders `0.00` for plans whose rates come from LifePRO
`PAAGERAT` attained-age series, even though the rates are present in `Output/rates/QuikGps.csv` and
numerically correct after Issue #138.

Anchor: plan `1658CS`, screen **Gross Premiums - Values Vary by Attained Age**, Gender `F`,
UW Class `ST`. Screenshot: `evidence/QLAdmin_1658CS_GrossPrems_blank_20260809.png`.

## 2. Why it was not fixed by #138

Issue #138 corrected *which age* each rate belongs to (LifePRO `SEQ` is a 1-based ordinal, so the axis
moved down one year). It did not change *how* the series is stored, and said so:

> `Issue_138_Resolution_Summary.md` → "Still open" item 2: "Whether attained-age premiums belong on
> that axis instead is unresolved and is **not** changed here."

Issue #140 closes that deferred item.

---

## 3. Authority — how QLAdmin defines these tables

**QLAdmin Help §7.82 `QuikDbs - Death Benefits`** (PDF page 767) is explicit:

| Item | Value |
|---|---|
| Index key | `PLAN + AGE + CNTL` |
| `AGE` | **Issue age** (C2) |
| `CNTL` | **Duration control** (C2) |
| `DB0` … `DB9` | "Death benefit year **0+(cntl\*10)**" … "year **9+(cntl\*10)**" |

**Rate-file import format** (Help pages 556–557) repeats it and adds a loading rule:

> "Rates must begin starting with **age 00 and duration 00 and up**. If there are no rates for the lower
> ages, use `0.00`."

Compact import columns are `AGE`, `CONTROL` ("Decade beginning with 00"), then one value per decade —
`00` = years 0–9, `01` = years 10–19, … `12` = years 120–121.

So the series always runs along the **duration/slot axis** (`CNTL × 10 + n`). `AGE` is the issue-age key.

### Corroborating real QLAdmin data in the repo

| Reference table | Plan | `AGE` | `CNTL` | Values |
|---|---|---|---|---|
| `QuikDbs.dbf` | `1GRDWL` | `00` | `00`–`12` | across `DB0`–`DB9` (graded 250/500/750/1000…) |
| `QuikCvs.dbf` | `1TSTWL` | `41`, `46` | `00`–`08` | across `CV0`–`CV9` |
| `QUIKQXS.DBF` | `1980 CSO Male` | n/a | n/a | age series across `Q000`–`Q121`, index = age |

`QUIKQXS` is the clearest statement of the house convention: an **age-indexed series is spread across
columns**, not down rows.

### What the screenshot adds

In "Values Vary by Attained Age" mode the screen shows an **Issue Age list containing only `00`**,
selected, and a values panel labelled **Age** listing 38, 39, 40 … Because our `1658CS` rows carry
`AGE` 15–85, the list is clearly not built from our data — QLAdmin fixes the issue-age key at `00` for
this mode and reads the age series out of the slot axis. We have no `AGE='00'` row, so every cell is `0.00`.

---

## 4. What we emit today

Attained-age loaders all hard-code the value into slot 0:

| File | Line | Emits |
|---|---|---|
| `qla_core/paagerat_pr_loader.py` | 158–159 | `cntl, col_idx = S.duration_to_cntl_col(0)`; attained age placed in `age` (173) |
| `qla_core/paagerat_ul_coi_loader.py` | 176 | same |
| `qla_core/shared_rate_candidate_loader.py` | 290 | same |

`1658CS` gross premiums: 388 rows, one per age 15–85, `CNTL` always `00`, only `GP0` populated.

Contrast on the same plan with `QuikTvs`, which Warren confirms **does** display: 1,031 rows,
`CNTL` `00`–`05`, all ten columns used.

---

## 5. Confirmed scope

Verified per emit path, not by shape-guessing.

### In scope — genuine attained-age scalar series stored on the wrong axis

| Table | Source | Loader | Affected plans |
|---|---|---|---:|
| `QuikGps` | `PAAGERAT` `TYPE=PR` (+ shared-rate path) | `paagerat_pr_loader.transform_paagerat_pr` | **97** of 109 |
| `QuikDbs` | `PAAGERAT` `TYPE=DB` (Wave 2) | `paagerat_db_loader.transform_paagerat_db` | **10** of 23 |
| `QuikNff` | `PAAGERAT` `TYPE=NF` | `paagerat_pr_loader.transform_paagerat_nf` | **6** of 23 |
| `QuikCoi` | `PAAGERAT` `TYPE=U6` | `paagerat_ul_coi_loader.transform_paagerat_u6` | **2** of 2 |
| `QuikGcoi` | `PAAGERAT` `TYPE=U5` | `paagerat_ul_coi_loader.transform_paagerat_u5` | **1** of 1 |

All five funnel through two shared functions: `transform_paagerat_attained_age`
(`paagerat_pr_loader.py:41`) and `transform_paagerat_ul_scalar` (`paagerat_ul_coi_loader.py:81`).
`PAAGERAT` has **no duration dimension** — one scalar per `(segment, SEX, BAND, UWCLS, SEQ)` — so
nothing is being collapsed; the series is purely age-indexed.

### Out of scope — correct as emitted

| Table | Plan | Why |
|---|---|---|
| `QuikNps` | `1L17SP` | Source is **PDAGE**, `AGE` is a real issue age (0–18, F/M) and only `DURATION=1` carries non-zero values. Legitimate issue-age grid with one duration. `rate_factor_loader.py:242–276`. |
| `QuikCvs`, `QuikDvs`, `QuikTvs` | all | Already use the issue-age × duration-slot layout and display correctly. |
| `QuikGps` | remaining 12 plans | PDAGE / Rate_Table issue-age × duration path. |

This corrects the Discovery note, which listed `QuikNps` as affected on shape alone.

---

## 6. Assembly path (what a loader change would flow through)

| Step | Location |
|---|---|
| Loaders yield `{plan, age, cntl, col, value, gender, uwclass, band, …}` | `qla_core/*_loader.py` |
| Streamed | `rate_pipeline.py:381–452` |
| Pivoted into a grid | `rate_factor_loader.build_factor_grid:292–362` |
| Grouping key | `(PLAN, AGE, CNTL, GENDER, UWCLASS, BAND, ISSCNTRY, ISSUEST, EFFDATE)` — `rate_factor_loader.py:315–316` |
| Cell placement | `grid[key][col] = value` — `rate_factor_loader.py:317–324` |
| Wide rows | `grid_to_factor_rows:365–396` maps `cells[i]` → `{PFX}{i}` |
| CSV | `rate_dbf_writer.emit_all_rate_tables_csv:191–215` |

The grouping key already treats `AGE` and `CNTL` as independent dimensions and merges multiple `col`
values into one row, so emitting `age="00"`, `cntl=A//10`, `col=A%10` assembles correctly with **no
change to the pivot**. The mapping `A → (A//10, A%10)` is bijective for `A` in 0–99, so no collisions.

Rate-key tables (`QuikPlGp`, `QuikPlUw`, etc.) are built from grid keys with `AGE` and `CNTL`
**stripped** (`rate_key_setup.py:100–101`, `rate_member_setup.py:26–31`), so plan dropdowns and rate
keys are unaffected.

---

## 7. Known couplings that break if only the loaders change

| Consumer | Location | Effect |
|---|---|---|
| `VARGP`/`VARDB` derivation (Issue A7) | `quikplan_rate_variation_flags.py:1163`, `1168–1178` | `scan_factor_grid` would see one age and many slots → classify as `1` (policy year) instead of `3` (attained age) on all 116 plan/table pairs |
| `validate_issue138_rate_age_alignment.py` | 44–60, 73–84 | Builds `{AGE: GP0}`; would find nothing |
| `validate_issueA7_variation_codes.py` | 77–78 | Reads the same grid shape |
| `validate_issue74_vardb.py` | 55 | Same, for `QuikDbs` |
| Age-cap audit | `paagerat_pr_loader.py:149–151`, `rate_pipeline.py:711–720` | Cap semantics move from "age" to "slot" |

Unaffected: `QuikCvs`/`QuikTvs` validators (#98, #106, L14, accountability) — they read issue-age
tables that are not being changed.

---

## 8. Open questions carried into Planning

1. Should slot-axis capping still stop at 99, when the Help's compact import defines decades out to
   `12` (years 120–121)? `130JEB` currently loses `SEQ` 100–117 to the age cap.
2. Does the Help's "start at age 00 and duration 00, use `0.00` for lower ages" rule mean we must
   zero-fill slots below the first rated age (e.g. `1L14SC` premiums start at 45 → slots 0–44 = `0.00`)?
3. `VARGP` stays `3` for these plans — confirm on a loaded prototype before fleet-wide handoff.

---

## 9. Intake verdict

Real, well-understood, and localized to two shared transform functions plus the variation-code
classifier. **Proceed to Planning.**
