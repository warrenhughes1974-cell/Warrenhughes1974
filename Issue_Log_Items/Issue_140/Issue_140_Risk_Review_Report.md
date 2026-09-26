# Issue #140 — Risk Review Report

**Issue:** #140 — Attained-age rate grids stored on the wrong axis
**Date:** 2026-08-09
**Framework stage:** Stage 4 Risk
**Code changed:** None
**Scope under review:** `QuikGps` (97 plans) + `QuikDbs` (10 plans) only

---

## 1. Blast radius

| Dimension | Extent |
|---|---|
| Tables rewritten | 2 of 23 emitted rate tables |
| Plans touched | 107 plan/table pairs (97 `QuikGps` + 10 `QuikDbs`) |
| Rows rewritten | ~13,580 → ~1,936 (same values, ten per row instead of one) |
| Policy tables touched | **None** — `quikmstr`, `quikridr`, `quikclnt`, `quikbenf` etc. untouched |
| `quikplan` fields touched | `VARGP`, `VARDB` only, and only to hold them at `3` |
| Schema changes | **None** — no field added, removed, reordered, retyped or resized |
| Production code files | 6 modules + 3 validators + `APP_VERSION` |

Nothing outside the rate package changes. No policy-level values move.

---

## 2. Risk register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Slot axis is not what QLAdmin reads, and screens stay blank | Low–Medium | High — wasted rebuild | Help §7.94 + p538 var codes + reference `QuikDbs`/`QUIKQXS` + the Issue Age `00` on the live screen all agree. Proof step 10 loads `1658CS` before any handoff. Kill switch reverts in one run. |
| R2 | `VARGP`/`VARDB` silently downgrade `3` → `1` | **High if unmitigated** | High — swaps one wrong screen for another | Manifest-driven classification, plus a fail-safe that leaves codes untouched when the manifest is missing. Validator check 5 asserts all 107 stay at `3`. |
| R3 | #138's one-year offset silently lost | Low | High — premiums a year off again | Offset lives in the loader, upstream of placement, and is proven against `quikridr.MPREM`. Validator rewritten to the slot axis and must still PASS. |
| R4 | Zero-fill hides a genuine gap (a plan with no rates looks like a plan of zeros) | Medium | Medium | Fill only *below* the highest populated slot, never above; plans with no real factor rows keep `VARGP=4` through the existing A7 path |
| R5 | Age cap at 99 collides more than before | Low | Low | Cap behaviour unchanged; `130JEB` `SEQ` 100–117 collapse exactly as today. Existing collision audit still fires. |
| R6 | Row-count drop mistaken for data loss in review | Medium | Low | Expected and documented (§6 of Planning); validation is value-for-value, not row-count |
| R7 | `Test_Validation/` reload leaves DBFs mixed old/new | Medium | Medium | `QuikGps` and `QuikDbs` must be re-appended together via the Desktop DBF Append Tool; no partial reload of one table |
| R8 | Regression on untouched tables | Low | High | Check 8 asserts `QuikCvs`, `QuikTvs`, `QuikDvs`, `QuikNps`, `QuikNff`, `QuikCoi`, `QuikGcoi` byte-identical |
| R9 | A7 override not approved before ship | — | Governance | Gated: Development does not start until Warren approves |

---

## 3. What makes this safer than it sounds

1. **The pivot does not change.** `build_factor_grid` already keys on `AGE` and `CNTL` separately and
   merges multiple column indexes into one row. The new placement is bijective over ages 0–99, so no
   value can land on another value.
2. **Rate keys and plan dropdowns cannot move.** `QuikPl*` tables are built from grid keys with `AGE`
   and `CNTL` stripped, so Issue #118's underwriting work is untouchable by this change.
3. **The values themselves never change.** Only the cell each value occupies changes. Validation is a
   value-for-value reconstruction against the pre-change grid.
4. **Two independent oracles.** `quikridr.MPREM` from LifePRO, and the QLAdmin screen itself.
5. **Single-env revert.** `QLA_ATTAINED_AGE_SLOT_AXIS=0`.

---

## 4. What I am least sure about

R1 is the honest residual. The Help documents the column axis as *duration/year* for every table and
never describes the physical layout of an attained-age grid. The conclusion that `VARGP=3` reinterprets
that axis as attained age is drawn from three consistent signals — the variation-code definition, the
reference `QuikDbs` storing a non-issue-age series at `AGE='00'` with `CNTL` paging, and the live screen
holding Issue Age at `00` — but it is inference, not a documented sentence.

Mitigation is sequencing, not certainty: build it, load `1658CS` and `1L14SC`, look at the screen, and
only then run the full batch and hand anything over.

---

## 5. Go / No-Go

**GO — on the reduced scope, conditional on two approvals.**

| Condition | Needed from Warren |
|---|---|
| A7 override | Variation-code authority moves from grid shape to emit manifest for attained-age plans |
| Reduced scope | `QuikNff`, `QuikCoi`, `QuikGcoi` deferred to a follow-up issue |

**NO-GO** for `QuikNff`, `QuikCoi`, `QuikGcoi` in this change: no plan-level variation code exists to
tell QLAdmin the axis meaning, and `QuikNff` already carries both encodings on 8 plans.

---

## 6. Recommended sequencing

1. Development on `QuikGps` + `QuikDbs`, engine v58.90, kill switch defaulted on
2. Rate re-emit only (not a full batch), archive prior `rates/` first
3. Validation checks 1–9
4. **Load `1658CS` + `1L14SC` into QLAdmin and confirm the premium screens populate**
5. Only after the screen is right: full batch, regression, release gate, DBF append
6. Closure updates the guide rows for A7 and #138 in the same commit

Steps 1–4 are cheap and reversible. Step 5 is the expensive one and should not start until the screen
is proven.

---

## 7. Stop

Risk review complete. **Awaiting "Approved for Development"** plus the two decisions in §5.
