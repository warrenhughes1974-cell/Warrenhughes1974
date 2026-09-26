# Issue #140 — Dependency Gate

**Issue:** #140 — Attained-age rate grids stored on the wrong axis
**Date:** 2026-08-09
**Framework stage:** Stage 3 Dependency Gate
**Code changed:** None

---

## G1 — Inputs and environment

| Requirement | Status | Evidence |
|---|---|---|
| LifePRO `PAAGERAT` extract present | **PASS** | drives the current 97 + 10 in-scope plans in `Output/rates/` |
| Segment resolution chain (`PCOVRSGT` → `PCOVR` → crosswalk) | **PASS** | unchanged; #140 touches placement only, not resolution |
| QLAdmin table authority | **PASS** | Help §7.94, §7.82, §7.92, §7.72, §7.157, §7.158; import format p556–557 |
| Real QLAdmin reference tables | **PASS** | `plan_analysis/source_data/reference_dbf/` — `QuikDbs.dbf`, `QuikCvs.dbf`, `QUIKQXS.DBF` |
| Valuation date | **PASS** | `QLA_VALUATION_DATE=20260630` (midyear package) |
| Independent value check | **PASS** | `quikridr.MPREM` (LifePRO `ANN_PREM_PER_UNIT`, Issue #88) is layout-independent |

**G1: PASS**

---

## G2 — Conflict with Closed / guide rows

Checked against `Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md`.

### A7 — "Var GP / Var DB codes match the loaded rates" — **DIRECT CONFLICT**

The Closed row states the derivation rule as:

> "rates on one age axis only = **3 attained age**; rates across durations with a single age = **1 policy year**"

After #140, attained-age plans present as *rates across durations with a single age*, which that rule
classifies as `1`. The shape-based rule can no longer distinguish an attained-age grid from a
policy-year grid, so **A7's stated method is materially overridden**: authority for these plans moves
from grid shape to an explicit emit manifest.

The *outcome* A7 exists to protect is preserved — `VARGP`/`VARDB` still describe the grid QLAdmin
reads, and `1L14SC` stays `VARGP=3`. Only the inference mechanism changes.

**Per `.cursor/rules/completed-issues-release-guide.mdc` and Framework rule 13, this requires Warren's
written approval before implementation.** Not agent-waivable.

### #138 — "Gross premiums filed one year high" — **METHOD TEXT SUPERSEDED, SUBSTANCE INTACT**

The guide row's validation method reads "a policy issued at `MAGE` must find its own premium at grid
age `MAGE`". After #140 the premium is found at **slot** `MAGE`, not at grid `AGE`. The one-year offset
itself is unchanged and still correct, because it was proven against `quikridr.MPREM`, which does not
depend on layout.

#140 is the completion of #138's own deferred item, not a reversal. The guide row's "Output tables" and
"How" text must be updated in the same change set, and `validate_issue138_rate_age_alignment.py`
rewritten to read the slot axis while continuing to assert the same business fact.

### #74 — "Var DB Code 4 → 0 only" — **NO CONFLICT**

The enduring rule (no `VARDB=4` residual) still holds. The 10 in-scope `QuikDbs` plans stay at `VARDB=3`;
only the reason they are 3 changes. `validate_issue74_vardb.py` needs the manifest awareness.

### No conflict

| Row | Why unaffected |
|---|---|
| #106 RV duration | `QuikTvs` — untouched |
| #98 CV endpoint | `QuikCvs` — untouched |
| L14 CV duration | `QuikCvs` — untouched |
| #42 missing rate rows | PDAGE miss-fill into `QuikNps`/`QuikTvs` — untouched |
| #88 / #26 `MPREM` | `quikridr` — untouched, and used as the independent check |
| #118 UW remap | segmentation dimension, orthogonal to the age/slot axis |
| #139 fee suppression | `quikridr`/`quikmstr` — untouched |

**G2: CONDITIONAL PASS — blocked on Warren's approval of the A7 override.**

---

## G3 — Reversibility and proof

| Requirement | Status | Detail |
|---|---|---|
| Kill switch | **PASS** | `QLA_ATTAINED_AGE_SLOT_AXIS=0` reverts without a code revert |
| Archive before re-emit | **PASS** | `Archive/rates_pre_issue140_<timestamp>/`, same pattern as #138 |
| Schema safety | **PASS** | no field added, removed, reordered, retyped or resized; `AGE`/`CNTL` stay C2 |
| Assembler safety | **PASS** | grouping key already treats `AGE` and `CNTL` independently (`rate_factor_loader.py:315–316`); `A → (A//10, A%10)` is bijective over 0–99, so no key collisions |
| Key/member tables safe | **PASS** | `QuikPl*` strip `AGE` and `CNTL` (`rate_key_setup.py:100–101`, `rate_member_setup.py:26–31`) — dropdowns and rate keys cannot move |
| Rate validation gates | **PASS** | V08 accepts `AGE='00'`; V09 accepts any numeric `CNTL`; V03 safe given bijection |
| Existing validator coverage | **PARTIAL** | #138 and A7 validators must be updated in the same set, or they fail on correct data |
| Independent oracle | **PASS** | `quikridr.MPREM` |
| Final proof available | **PASS** | load `1658CS` / `1L14SC` and read the screen |

**G3: PASS**

---

## Scope gate — three tables do not clear

| Table | Verdict | Reason |
|---|---|---|
| `QuikGps` | **CLEAR** | `VARGP=3` exists and is documented as "Vary by Attained Age" |
| `QuikDbs` | **CLEAR** | `VARDB=3` likewise |
| `QuikNff` | **BLOCKED** | No variation code exists. 8 plans already carry both encodings — `1658C1` has `F/ST`+`M/ST` as PAAGERAT scalars and `F/NT`+`M/NT` as PDAGE duration grids; `1L10SO` has `M/PR`+`M/SM` as scalars against six duration segments. Flipping half a table with no switch to tell QLAdmin which half is which is not a safe change. |
| `QuikCoi` | **BLOCKED** | No variation code; index key (§7.72) does not include `AGE`; columns are documented as duration |
| `QuikGcoi` | **BLOCKED** | Same |

Warren approved "all affected tables" during Discovery on the basis that all six shared one defect.
The Help review and the mixed-encoding finding show that is not true. **This needs his re-decision.**

---

## Verdict

**CONDITIONAL PASS** for `QuikGps` (97 plans) and `QuikDbs` (10 plans), pending two explicit decisions
from Warren:

1. Approve the **A7 override** (variation-code authority moves from grid shape to emit manifest).
2. Confirm the **reduced scope** — `QuikNff`, `QuikCoi`, `QuikGcoi` deferred to a follow-up.

**BLOCKED** for `QuikNff`, `QuikCoi`, `QuikGcoi`.

Proceed to Risk on the reduced scope.
