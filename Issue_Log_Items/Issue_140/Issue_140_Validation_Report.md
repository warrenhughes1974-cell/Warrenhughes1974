# Issue #140 — Validation Report

**Issue:** #140 — Attained-age rate grids stored on the wrong axis
**Date:** 2026-08-09
**Framework stage:** Stage 6 Validation
**Engine:** v58.90
**Valuation date:** `QLA_VALUATION_DATE=20260630` (midyear package)
**Scope:** `QuikGps` (97 plans) + `QuikDbs` (10 plans)
**Result:** **PASS** — pending the QLAdmin screen check

---

## 1. What changed

Attained-age series now sit where QLAdmin reads them: `AGE='00'` with the attained age
as the slot (`CNTL = age // 10`, column `age % 10`), zero-filled from slot 0, and the
plan's `VARGP`/`VARDB` held at `3` so QLAdmin reads that axis as attained age.

| File | Change |
|---|---|
| `qla_core/rate_dbf_schema.py` | `ATTAINED_AGE_KEY`, `attained_age_to_age_cntl_col()` |
| `qla_core/paagerat_pr_loader.py` | `slot_axis` opt-in; `PR` opts in; `QLA_ATTAINED_AGE_SLOT_AXIS` kill switch |
| `qla_core/paagerat_db_loader.py` | `DB` opts in |
| `qla_core/shared_rate_candidate_loader.py` | shared `PR` rides the same axis as its donor |
| `qla_core/attained_age_grid_fill.py` | **new** — zero-fill to slot 0, emit manifest read/write |
| `qla_core/rate_pipeline.py` | collects the slot-axis plan set, runs the fill, writes the manifest |
| `qla_core/rate_emit.py` | reports the manifest in the run messages |
| `qla_core/quikplan_rate_variation_flags.py` | manifest-driven code `3` + slot-axis fail-safe |
| `tools/validators/validate_issue140_attained_age_axis.py` | **new** |
| `tools/validators/validate_issue138_rate_age_alignment.py` | reads the slot axis |
| `tools/validators/validate_issueA7_variation_codes.py` | manifest-aware |
| `tools/validators/validate_issue74_vardb.py` | manifest-aware |
| `tools/validators/validate_release_closed_issues.py` | v1.3 — adds the #140 smoke |
| `app.py`, `QLA_Migration/app.py` | `APP_VERSION` v58.89 → v58.90 |

`QuikNff`, `QuikCoi` and `QuikGcoi` were deliberately **not** opted in (Warren, 2026-08-09).

---

## 2. Emit

Run through `qla_core.rate_emit.run_rate_emit` — the production path the batch uses, not
the R5 script. That matters: the R5 script skips the Issue #118 fold of policy
`MUWCLASS` into `QuikPlUw`, and a first pass through it cost 32 `QuikPlUw` rows. Caught
by the table-comparison check below and re-emitted correctly.

```text
status: SUCCESS   blockers: 0   tables: 23   csv rows: 179,969
Issue #118 QuikPlUw: added 32 policy MUWCLASS membership row(s)
Issue #140 attained-age slot axis: 107 plan/table pair(s)
```

Manifest written to `QLA_Migration/Reports/rates/attained_age_grid_manifest.json`:
`QuikGps` 97 plans, `QuikDbs` 10 plans — exactly the planned scope.

---

## 3. Checks

| # | Check | Result |
|---|---|---|
| 1 | `validate_issue140_attained_age_axis.py` — AGE key, CNTL continuity, variation code, zero-fill | **PASS** |
| 2 | `validate_issue138_rate_age_alignment.py` on the slot axis | **PASS** |
| 3 | `1658CS` F/ST slots 38/39/40 | `.35` / `.37` / `.38` — **match** |
| 4 | `1L14SC` M/NT slot 64 (policy `9011206462C`, LifePRO `63.24`) | `63.24` — **match** |
| 5 | `validate_issueA7_variation_codes.py` | **PASS** — `VARGP=3` on 97, `VARDB=3` on 10 |
| 6 | `validate_issue74_vardb.py` | **PASS** — no `VARDB=4` residual |
| 7 | Rate emit blockers | **0** |
| 8 | Untouched tables byte-identical | **PASS** — 21 unchanged, only `QuikGps` + `QuikDbs` moved |
| 9 | Release gate `validate_release_closed_issues.py` v1.3 | **RELEASE_OK**, accountability no GAPs |
| 10 | QLAdmin screen | **outstanding — Warren** |

### Check 2 is the strongest evidence

The #138 validator matches emitted rates against `quikridr.MPREM`, which carries LifePRO
`ANN_PREM_PER_UNIT` and is independent of how we store the grid. Reading the new layout
it finds **27 aligned plans against 6 before**, and untestable plans fall from 39 to 17.
The rates did not change — the validator can simply find them now, at the ages LifePRO
says they belong to. If the slot axis were wrong, this number would have gone down.

### Row counts

| Table | Before | After |
|---|---:|---:|
| `QuikGps` | 13,386 | 2,220 |
| `QuikDbs` | 2,514 | 1,976 |

The same values, repacked ten to a row instead of one. Check 3, check 4 and check 2
prove value-for-value equivalence.

---

## 4. Distribution after the change

| Field | Distribution |
|---|---|
| `VARGP` | `1`: 11, `2`: 1, `3`: **97**, `4`: 32 |
| `VARDB` | `0`: 118, `1`: 5, `2`: **8**, `3`: **10** |

The R7B quikplan pass reported **0 plans changed** — the manifest held every attained-age
plan at `3` and nothing was downgraded to `1`, which was the main risk in the design
(R2 in the risk register).

---

## 5. Published for reload

- `QLA_Migration/Output/Test_Validation/rates/QuikGps.csv`
- `QLA_Migration/Output/Test_Validation/rates/QuikDbs.csv`
- `QLA_Migration/Output/Test_Validation/quikplan.csv`

Both rate tables must be appended together with `quikplan`; the variation code and the
grid layout only make sense as a pair.

---

## 6. Rollback

- Kill switch: `QLA_ATTAINED_AGE_SLOT_AXIS=0`, then re-emit
- Archive: `QLA_Migration/Archive/rates_pre_issue140_20260809T201326Z/` (23 tables)

---

## 7. Outstanding

The one check that actually closes this issue is the screen. Load `1658CS` and `1L14SC`
and confirm Gross Premiums populate. Everything above proves we built what we intended;
only QLAdmin proves we intended the right thing.

Not started, by design: full policy batch, regression, DBF append, Closure.
