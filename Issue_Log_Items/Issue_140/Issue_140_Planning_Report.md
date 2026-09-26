# Issue #140 — Planning Report

**Issue:** #140 — Attained-age rate grids stored on the wrong axis
**Date:** 2026-08-09
**Framework stage:** Stage 2 Planning
**Code changed:** None
**Target engine:** v58.90

---

## 1. Objective

Store attained-age rate series the way QLAdmin reads them, so gross premium screens populate.

## 2. Authority — QLAdmin Help field definitions

Every factor table is defined the same way. Extracted from `docs/claims_conversion_reference/QLAdmin_Help.pdf`:

| Section | Table | Index key | `AGE` | `CNTL` | Column n |
|---|---|---|---|---|---|
| 7.94 (p779) | `QuikGps` | `PLAN + AGE + CNTL` | Issue age | Duration control | "Gross premium **year n+(cntl\*10)**" |
| 7.82 (p767) | `QuikDbs` | `PLAN + AGE + CNTL` | Issue age | Duration control | "Death benefit **year n+(cntl\*10)**" |
| 7.157 (p848) | `QuikNff` | `PLAN + AGE + CNTL` | Issue age | Duration control | "Nonforfeiture **year n+(cntl\*10)**" |
| 7.158 (p849) | `QuikNps` | `PLAN + AGE + CNTL` | Issue age | Duration control | "Net premium **year n+(cntl\*10)**" |
| 7.92 (p777) | `QuikGcoi` | `PLAN + AGE + CNTL` | Issue age | Control | "Guaranteed COI, **duration n**" |
| 7.72 (p753) | `QuikCoi` | `PLAN + GENDER + UWCLASS + BAND + ISSCNTRY + ISSUEST` | Issue age | Duration control | "COI **duration n**" |

Plan-level variation codes (Help p538–539, and `QuikPlan` field list):

> `Var GP Code` / `Var DB Code`: `0` Level, `1` Vary by Policy Year Only, `2` Vary by Issue Age and
> Policy Year, **`3` Vary by Attained Age**, `4` not on file.

### The key conclusion

The column axis is **always the year/duration axis**. An attained-age table is not a different physical
layout — it is the same layout, and **`VARGP`/`VARDB` = 3 is the instruction that tells QLAdmin to read
that axis as attained age**, with the issue-age key held at `00`. That is exactly what the screenshot
shows: Issue Age list `00`, values panel labelled **Age**.

**Only `QuikGps` and `QuikDbs` have such a code.** `QuikNff`, `QuikNps`, `QuikCoi` and `QuikGcoi` have
no per-plan switch, so QLAdmin has no way to be told their column axis means attained age.

---

## 3. Scope

### In scope — has an explicit attained-age variation code

| Table | Var code | Plans | Source | Loader |
|---|---|---:|---|---|
| `QuikGps` | `VARGP=3` | **97** | `PAAGERAT` `TYPE=PR` | `paagerat_pr_loader.transform_paagerat_pr` (+ `shared_rate_candidate_loader`) |
| `QuikDbs` | `VARDB=3` | **10** | `PAAGERAT` `TYPE=DB` | `paagerat_db_loader.transform_paagerat_db` |

`QuikGps` `5L01MA` is **excluded**: it is a PDAGE issue-age × duration plan (`VARGP=2`) that happens to
have one single-duration row. Scope is decided by source path, never by row shape.

### Deferred — no variation code, and evidence is contradictory

| Table | Plans | Why deferred |
|---|---:|---|
| `QuikNff` | 6 pure + **8 mixed** | No `VARNF` code exists. Worse, 8 plans already carry **both** encodings: on `1658C1`, `F/ST` + `M/ST` come from PAAGERAT as attained-age scalars while `F/NT` + `M/NT` come from PDAGE as issue-age × duration grids. On `1L10SO`, `M/PR` + `M/SM` are scalars against six duration-based segments. Flipping only the PAAGERAT rows puts two incompatible meanings in one table for one plan with nothing to distinguish them. |
| `QuikCoi` | 2 | No variation code. Index key does not even include `AGE`. Storing attained age on the year axis would be read as duration. |
| `QuikGcoi` | 1 | Same as `QuikCoi`. |

### Confirmed out of scope

`QuikNps` (`1L17SP` is a real PDAGE issue-age grid), `QuikCvs`, `QuikDvs`, `QuikTvs`, and the 12
`QuikGps` plans on the PDAGE path.

---

## 4. Design

### 4.1 One shared placement helper

Add to `qla_core/rate_dbf_schema.py`, next to `duration_to_cntl_col`:

```python
ATTAINED_AGE_KEY = "00"

def attained_age_to_age_cntl_col(attained_age: int):
    """Attained-age series -> (AGE key, CNTL page, column index).

    Help 7.94/7.82: column n holds slot n+(cntl*10) and AGE is the issue-age key.
    An attained-age grid has no issue-age axis, so AGE stays 00 and the age itself
    is the slot QLAdmin reads once VARGP/VARDB = 3.
    """
    cntl, col = duration_to_cntl_col(attained_age)
    return ATTAINED_AGE_KEY, cntl, col
```

### 4.2 Call sites

Two functions carry every in-scope row:

| File | Line | Today | After |
|---|---|---|---|
| `qla_core/paagerat_pr_loader.py` | 152, 158–159 | `age2 = str(age_int).zfill(2)`; `cntl, col_idx = S.duration_to_cntl_col(0)` | `age2, cntl, col_idx = S.attained_age_to_age_cntl_col(age_int)` |
| `qla_core/shared_rate_candidate_loader.py` | 289–290 | same | same |

`transform_paagerat_attained_age` already serves `PR`, `NF` and `DB`, so the new placement must be
**opt-in per caller** (a `slot_axis: bool = False` parameter), switched on only for `PR` and `DB`. `NF`
keeps today's behaviour until `QuikNff` is resolved. `paagerat_ul_coi_loader.py` is not touched.

The yielded `ql_duration` becomes the slot (the attained age) so the lineage and audit CSVs stay
truthful; `attained_age_seq` and `original_age` are unchanged.

### 4.3 Zero-fill to slot 0

Help p556: *"Rates must begin starting with age 00 and duration 00 and up. If there are no rates for
the lower ages, use 0.00."*

`1L14SC` premiums start at attained age 45, so pages `00`–`04` would not exist. Every grid we have that
displays correctly (`QuikTvs`, `QuikCvs`, reference `QuikDbs`) starts its slot axis at `CNTL='00'`.
Plan: after the grid is built, fill unset slots below the highest populated slot with `0.00` for
in-scope plan/table pairs, so pages run `00`…`max`. This mirrors the existing TV0 blank-fill pass
(`rate_pipeline.py:474–476`).

### 4.4 Age cap unchanged

`S.MAX_AGE = 99` still applies. `130JEB` loses `PAAGERAT` `SEQ` 100–117 exactly as it does today, so
this change introduces no new loss. The Help's compact import defines decades out to `12` (years
120–121), so raising the cap is possible — deliberately **not** done here; logged as a follow-up.

### 4.5 Variation-code classifier (mandatory, same change set)

`classify_factor_grid` (`quikplan_rate_variation_flags.py:1168–1178`) infers the code from grid shape.
After the flip, an attained-age grid looks like "one age, many slots" and would be classified `1`
(policy year) instead of `3`. Shape can no longer distinguish it, so the fact must be carried, not
inferred:

1. Rate emit writes an audit manifest of what it actually emitted as attained-age:
   `QLA_Migration/Reports/attained_age_grid_manifest.json` → `{"QuikGps": [plans…], "QuikDbs": [plans…]}`.
   Reports/, not Output/, per the Output folder policy.
2. `apply_variation_codes_from_emitted_rates` gains an optional `attained_age_plans` argument. Plans in
   that set are forced to `CODE_ATTAINED_AGE`; everything else keeps today's inference.
3. Fail-safe: if the manifest is missing, leave the plan's existing `VARGP`/`VARDB` untouched rather
   than reclassify it. A missing manifest must never silently downgrade 107 plans.

### 4.6 Kill switch

`QLA_ATTAINED_AGE_SLOT_AXIS=0` reverts to the current layout without a code revert, matching the
`QLA_SUPPRESS_POLICY_FEES` precedent from Issue #139. Default is on.

---

## 5. Files to touch

| File | Change | Risk |
|---|---|---|
| `qla_core/rate_dbf_schema.py` | Add `ATTAINED_AGE_KEY`, `attained_age_to_age_cntl_col` | Low — additive |
| `qla_core/paagerat_pr_loader.py` | `slot_axis` parameter; `PR` opts in | Medium |
| `qla_core/paagerat_db_loader.py` | Opt `DB` in | Low |
| `qla_core/shared_rate_candidate_loader.py` | Same placement for shared `PR` | Medium |
| `qla_core/rate_pipeline.py` | Zero-fill pass + write manifest | Medium |
| `qla_core/quikplan_rate_variation_flags.py` | `attained_age_plans` argument + fail-safe | Medium |
| `tools/validators/validate_issue138_rate_age_alignment.py` | Read the slot axis | Low |
| `tools/validators/validate_issueA7_variation_codes.py` | Expect `3` for the manifest set | Low |
| `tools/validators/validate_issue74_vardb.py` | Same for `QuikDbs` | Low |
| `app.py` + `QLA_Migration/app.py` | `APP_VERSION` → v58.90 | Low |

Not touched: `rate_factor_loader.build_factor_grid`, `grid_to_factor_rows`, `rate_key_setup`,
`rate_member_setup`, `rate_dbf_writer`. The pivot already handles the new placement, and key/member
tables strip `AGE` and `CNTL`.

---

## 6. Expected Output deltas

| Table | Plans | Rows now | Rows projected | Note |
|---|---:|---:|---:|---|
| `QuikGps` | 97 | 12,970 | ~1,864 | one row per segmentation per decade instead of one per age |
| `QuikDbs` | 10 | 610 | ~72 | same |

Row counts falling ~85% is the expected signature of the fix, not data loss — the same values move from
12,970 single-cell rows into ~1,864 ten-cell rows. Validation must prove value-for-value equivalence,
not row counts.

---

## 7. Validation plan

| # | Check |
|---|---|
| 1 | **New** `validate_issue140_attained_age_axis.py`: for every in-scope plan, `AGE == '00'` on all rows; `CNTL` pages run from `00`; the reconstructed series `{cntl*10+n: value}` equals the pre-change `{AGE: col0}` series value-for-value |
| 2 | `validate_issue138_rate_age_alignment.py` rewritten to the slot axis, still **PASS** — #138's offset was proven against `quikridr.MPREM`, which is layout-independent |
| 3 | `1658CS` F/ST: slot 38 → `CNTL='03'`, `GP8 = .35`; slot 39 → `GP9 = .37`; slot 40 → `CNTL='04'`, `GP0 = .38` |
| 4 | `1L14SC` M/NT: policy `9011206462C` issue age 64, LifePRO premium `63.24` → `CNTL='06'`, `GP4 = 63.24` |
| 5 | `validate_issueA7_variation_codes.py`: `VARGP=3` still on all 97, `VARDB=3` on all 10 — no silent downgrade to `1` |
| 6 | `validate_issue74_vardb.py` PASS; no `VARDB=4` residual |
| 7 | Rate emit: 0 blockers; `rate_validation` V03/V08/V09 clean (`AGE='00'` is valid; slot mapping is bijective so no duplicate keys) |
| 8 | Untouched tables byte-identical: `QuikCvs`, `QuikTvs`, `QuikDvs`, `QuikNps`, `QuikNff`, `QuikCoi`, `QuikGcoi` |
| 9 | Regression: #106, L14, #98, accountability all still PASS |
| 10 | **Screen proof** — load `1658CS` and `1L14SC` into QLAdmin and confirm Gross Premiums populate before the package is handed to anyone |

Check 10 is the one that actually closes this issue. Everything above it proves we built what we
intended; only the screen proves we intended the right thing.

---

## 8. Rollback

1. `QLA_ATTAINED_AGE_SLOT_AXIS=0` — immediate revert with no code change.
2. Archive `Output/rates/` to `QLA_Migration/Archive/rates_pre_issue140_<timestamp>/` before re-emit.
3. Single-commit revert; no schema, field-order or length changes anywhere.

## 9. Explicitly not in this change

- `QuikNff`, `QuikCoi`, `QuikGcoi` (see §3)
- Raising `MAX_AGE` above 99
- Any change to issue-age × duration tables
- Any unfolding of attained-age series into issue-age × duration grids

---

## 10. Verdict

Design is surgical: one additive helper, two loader call sites opted in per type code, one zero-fill
pass, one classifier argument. **Proceed to Dependency Gate.**
