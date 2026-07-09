# Non-CV Inheritance Analysis Report

**Date:** 2026-07-07  
**Mode:** Analysis only  
**Scope:** Non-CV inherited/shared rate candidates identified by `Issue_Rates_Inheritance_Validation`  
**Code status:** No converter code changed

---

## Summary

The prior validation proved that direct `Rate_Table` conversion and Issue #40 inherited `CV` conversion are working:

- Direct `Rate_Table` cells: **770,524 / 770,524 matched**
- Issue #40 inherited CV cells: **101,793 / 101,793 matched**
- Screenshot anchors: **8 / 8 matched**

The remaining question is whether the same PCOVRSGT-based inheritance pattern should apply to non-CV rate types.

This pass reviewed the 35 non-CV candidates from `evidence/inherited_rate_candidate_summary.csv`, counted source rows by active rate-owner segment, checked current output rows by issuing plan/table, and classified each row.

Result:

| Classification | Count | Meaning |
|----------------|------:|---------|
| **Likely Yes** | 24 | Strong evidence of true non-CV inherited/shared rate gap; business approval still required |
| **Pending** | 10 | Source-backed, but PUA/rider behavior or rate-type applicability is not confirmed |
| **No / Pending** | 1 | PUA gross premium inheritance is not currently supported by evidence |

By type:

| Rate Type | Count |
|-----------|------:|
| `NP` / `QuikNps` | 12 |
| `RV` / `QuikTvs` | 14 |
| `DV` / `QuikDvs` | 5 |
| `DB` / `QuikDbs` | 3 |
| `PR` / `QuikGps` | 1 |

The clean inherited-rate work should stay separate from PAAGERAT precedence conflicts.

---

## Scope

Reviewed files:

- `Issue_Log_Items/Issue_Rates_Inheritance_Validation/rate_inheritance_validation_report.md`
- `Issue_Log_Items/Issue_Rates_Inheritance_Validation/rate_source_trace_matrix.csv`
- `Issue_Log_Items/Issue_Rates_Inheritance_Validation/proposed_changes.md`
- `Issue_Log_Items/Issue_Rates_Inheritance_Validation/evidence/rate_validation_summary.json`
- `Issue_Log_Items/Issue_Rates_Inheritance_Validation/evidence/inherited_rate_candidate_summary.csv`
- `Issue_Log_Items/Issue_40/Issue_40_Fleet_CV_Inheritance_Audit.csv`
- `qla_core/cv_inheritance_loader.py`
- `qla_core/rate_pipeline.py`
- `qla_core/rate_factor_loader.py`

Reviewed rate types:

- `NP` → `QuikNps`
- `RV` → `QuikTvs`
- `DV` → `QuikDvs`
- `DB` → `QuikDbs`
- `PR` → `QuikGps`

---

## Prior Validation Findings Reviewed

The prior pass established:

- Direct `Rate_Table` rows resolve correctly through `Coverage_ID -> PLAN`.
- Issue #40 inherited `CV` rows resolve correctly through an approved manifest.
- The missing non-CV rows are not source extraction failures. Source rows exist on active PCOVRSGT owner segments.
- Current output rows for issuing plans are zero for the 35 non-CV candidate rows.
- PAAGERAT conflicts are a separate source precedence problem, not the same as missing inherited non-CV output.

---

## Issue #40 CV Inheritance Behavior

Current inherited CV behavior:

1. Read approved Issue #40 fleet audit rows.
2. For each issuing coverage, confirm there are no direct `CV` rows.
3. Find active PCOVRSGT segment IDs for the issuing coverage.
4. Keep candidate rate-owner coverages that have `CV` rows in `Rate_Table`.
5. Select owner:
   - single owner: use it,
   - multiple owners: choose the candidate with the most active PCOVRSGT slots.
6. Stream owner `CV` source rows under the issuing `PLAN`.
7. Reuse existing CV duration mapping, segmentation mapping, age capping, and QLAdmin formatting.

Current limitation:

`qla_core/cv_inheritance_loader.py` filters to `typ != "CV"` and therefore cannot emit `NP`, `RV`, `DV`, `DB`, or `PR`.

---

## Non-CV Gap Analysis By Rate Type

### NP / Net Premium / QuikNps

Findings:

- 12 candidate gaps.
- All have active PCOVRSGT rate-owner segments with source `NP` rows.
- Issuing plans have zero `QuikNps` rows today.

Assessment:

For non-PUA/base plans, `NP` is likely a true conversion gap if QLAdmin needs net premiums for valuation/reserve behavior. These should be approved for inherited emit unless business says the issuing plan intentionally does not use net premium rates.

PUA rows are pending because Issue #40 only approved CV behavior for PUA riders.

### RV / Reserves / Terminal Reserves / QuikTvs

Findings:

- 14 candidate gaps.
- Source `RV` rows exist on active inherited/shared rate-owner segments.
- Issuing plans have zero `QuikTvs` rows today.

Assessment:

`RV` is the strongest candidate for extension because reserves are typically paired with valuation behavior. For non-PUA/base plans, these are likely true gaps. For PUA plans, actuarial approval is required before inheriting parent reserve tables.

### DV / Dividends / QuikDvs

Findings:

- 5 candidate gaps.
- Source `DV` rows exist on active owner segments.
- A LifePRO screenshot anchor for `670 GL85-8` `DV` matched current direct output for owner plan `170858`.
- Issuing variants `17085M` and `170588` have zero `QuikDvs` rows while pointing to `670 GL85-8`.

Assessment:

For GL85 variants, `DV` looks like a likely true inherited-rate gap, but dividend applicability is plan-behavior dependent. Business/actuarial must confirm whether pay-age variants should share dividend factors from `670 GL85-8`.

PUA `DV` gaps remain pending.

### DB / Death Benefits / QuikDbs

Findings:

- 3 candidate gaps:
  - `1669SR` from `659 SR GD`
  - `7687J3` from `686S 30MRG`
  - `265PUA` from `665 STME95`
- Source `DB` rows exist, output rows are zero.

Assessment:

`1669SR` and `7687J3` look like likely true gaps because active owner segments have death benefit rates and issuing plans have none. `265PUA` should stay pending because it is a PUA rider and Issue #40 only approved PUA CV behavior.

### PR / Gross Premium / QuikGps

Findings:

- 1 candidate gap:
  - `265PUA` from `665 STME95`
- Source `PR` rows exist, output rows are zero.

Assessment:

Do **not** include `PR` in the first inherited-rate fix. Gross premium is entangled with PAAGERAT/direct premium precedence and PUA premium mechanics. This should remain pending until business decides which premium source is authoritative.

---

## Plan-By-Plan Findings

### Likely true gaps, pending approval

| Plan | Types | Rationale |
|------|-------|-----------|
| `17085M` | NP, DV, RV | GL85-M shares `670 GL85-8` CV by approved Issue #40 logic; active owner also has NP/DV/RV rows and issuing plan has none |
| `170588` | NP, DV, RV | GL85 related coverage points to `670 GL85-8`; source rows exist, output rows absent |
| `1668SP` | NP, RV | SPWL points to `659 CEN II`; source rows exist, output rows absent |
| `1669SR` | DB, NP, RV | Active owner slots include CEN/SR/L14 rate-bearing segments; output rows absent |
| `1679CS` | NP, RV | Active owner slots include `659 CEN II` and `L14`; output rows absent |
| `1666AI` | NP, RV | Additional insured plan points to `666 WL`; source rows exist, output rows absent |
| `1L10OD` | NP, RV | Active owner `L10 LP95`; source rows exist, output rows absent |
| `1L10PR` | NP, RV | Active owner `L10 LP95`; source rows exist, output rows absent |
| `1L10SO` | NP, RV | Active owner slots include `L10 LP95` / `L10 LP95SR`; output rows absent |
| `1SALMI` | RV | Active owner `SAL OL`; source rows exist, output rows absent |
| `1SALML` | RV | Active owner `SAL OL`; source rows exist, output rows absent |
| `7687J3` | DB | Active owner `686S 30MRG`; source rows exist, output rows absent |

### Pending / likely intentional until approval

| Plan | Types | Rationale |
|------|-------|-----------|
| `261PUA` | NP, DV, RV | PUA rider; no issued dependency count in Issue #40; only CV inheritance was approved |
| `265PUA` | DB, NP, DV, RV | PUA rider; only 1 issued policy in Issue #40 audit; CV approved, non-CV not proven |
| `280PUA` | NP, DV, RV | PUA rider; 3 issued policies; CV approved, non-CV not proven |
| `265PUA` | PR | PUA gross premium inheritance is not supported by current evidence |

---

## True Gaps vs Intentional Omissions

Likely true gaps:

- Non-PUA `NP` and `RV` gaps for plans with active inherited source rows.
- GL85 `DV` gaps for `17085M` / `170588`, if dividend factors follow the same inherited table as owner `170858`.
- Non-PUA `DB` gaps for `1669SR` and `7687J3`.

Likely intentional or not yet proven:

- PUA non-CV rows (`261PUA`, `265PUA`, `280PUA`) until actuarial confirms parent NP/RV/DV/DB usage.
- `PR` for `265PUA`, because PUA premium behavior may not be a normal gross premium inheritance case.

Not enough evidence to mark any non-CV gap as safe to ignore permanently. The correct status is: **business decision required**.

---

## PAAGERAT Conflict Separation

PAAGERAT conflicts are separate from non-CV inherited-rate gaps.

Non-CV inherited gaps:

- Source: `Rate_Table_Extract_20260427.csv`
- Relationship evidence: PCOVRSGT active owner segments
- Symptom: issuing plan has zero output rows
- Proposed fix class: manifest-driven inherited emit

PAAGERAT conflicts:

- Source: `PAAGERAT_AttainedAge_Rates_Extract_20260428.csv`
- Relationship evidence: segment resolver already maps to plan
- Symptom: output row exists, but value differs because another source path populated the same key
- Proposed fix class: precedence/source-of-truth decision

Do not combine these fixes. The non-CV inherited-rate work can proceed with manifest approval without resolving PAAGERAT precedence, except for `PR`, which should remain out of scope until PAAGERAT rules are settled.

---

## Risk Assessment

| Risk | Severity | Notes |
|------|----------|-------|
| Missing non-CV valuation/reserve rates | High | `NP`/`RV` gaps affect plans with source-backed active owner rows and zero output |
| Incorrectly emitting PUA non-CV rates | Medium | PUA source rows exist on parent/owner plans, but rider behavior is not confirmed |
| Incorrectly emitting dividends | High | `DV` may be plan-feature dependent; GL85 looks likely but needs confirmation |
| Incorrectly emitting gross premiums | High | `PR` overlaps PAAGERAT/direct premium source precedence |
| Combining PAAGERAT and inheritance fixes | High | Could mask source precedence errors under inheritance work |
| Overgeneralizing from CV | High | CV approval does not automatically approve NP/RV/DV/DB/PR |

---

## Recommended Business Decisions

1. Confirm whether non-PUA plans with active PCOVRSGT owner rows should inherit:
   - `NP`
   - `RV`
   - `DV`
   - `DB`
2. Confirm whether PUA plans should inherit any non-CV rate types:
   - `NP`
   - `RV`
   - `DV`
   - `DB`
   - `PR`
3. Confirm whether `17085M` and `170588` should inherit `DV`, `NP`, and `RV` from `170858` / `670 GL85-8`.
4. Confirm multi-owner selection rules for non-CV L10 and CEN cases. CV currently uses PCOVRSGT slot count; non-CV may need type-specific owner selection.
5. Confirm whether `PR` should be excluded from inherited `Rate_Table` logic until PAAGERAT precedence is resolved.

---

## Recommended Implementation Approach

Do not directly expand `cv_inheritance_loader.py` in place. Create a generalized inherited rate module that reuses the proven Issue #40 patterns while keeping CV behavior unchanged.

Recommended first implementation scope, if approved:

- Include `NP` and `RV` for non-PUA base/coverage plans.
- Include `DV` only for GL85 variants and other explicitly approved dividend plans.
- Include `DB` only for explicitly approved non-PUA plans (`1669SR`, `7687J3` initially).
- Exclude `PR` from first pass.
- Exclude PUA non-CV until actuarial confirms rider behavior.

Required validation:

- 100% source-to-output parity for every approved inherited row.
- Row/key count reconciliation by plan/type/table.
- Direct owner plan unchanged.
- Existing Issue #40 CV validation still passes.
- Existing Issue #37/#41 CV duration validation still passes.
- No new factor-grid collisions.

---

## Clear Statement

No converter code was changed during this analysis. No rate output files were modified during this analysis step. The only files created are analysis deliverables under:

`Issue_Log_Items/Issue_Rates_Inheritance_Validation/non_cv_inheritance_analysis/`

