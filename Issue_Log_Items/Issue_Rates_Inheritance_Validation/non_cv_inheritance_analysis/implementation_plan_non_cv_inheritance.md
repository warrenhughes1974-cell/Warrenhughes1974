# Implementation Plan — Non-CV Inherited/Shared Rate Resolution

**Date:** 2026-07-07  
**Status:** Planning only — awaiting approval before code changes  
**Code status:** No converter code changed  
**Output status:** No QLAdmin rate output files modified  

---

## Summary

The first-pass implementation should extend the proven Issue #40 inherited-rate model beyond `CV`, but only for a controlled, approved subset of non-CV rate types.

Recommended implementation:

- Add a new manifest-driven non-CV inherited-rate loader.
- Wire it after direct `Rate_Table` conversion and after current Issue #40 CV inheritance, but before PAAGERAT loaders.
- Preserve existing direct `Rate_Table` behavior exactly.
- Preserve existing Issue #40 CV behavior exactly.
- Exclude `PR` / `QuikGps`.
- Exclude all PUA non-CV candidates.
- Do not address PAAGERAT precedence conflicts in this fix.

First-pass include count: **24 plan/type rows**.

---

## Approved First-Pass Scope

The approved planning scope is captured in:

`approved_first_pass_scope.csv`

Rows marked `Include In First Pass = Yes` should be implemented only after final approval.

Included rate types:

| Rate Type | Target Table | Included Rows | Scope |
|-----------|--------------|--------------:|-------|
| `NP` | `QuikNps` | 12 | Non-PUA likely-yes candidates |
| `RV` | `QuikTvs` | 14 | Non-PUA likely-yes candidates |
| `DV` | `QuikDvs` | 2 | GL85 variants only: `17085M`, `170588` from `170858` |
| `DB` | `QuikDbs` | 2 | Non-PUA likely-yes candidates: `1669SR`, `7687J3` |

Included issuing plans:

- `1666AI`
- `1668SP`
- `1669SR`
- `1679CS`
- `170588`
- `17085M`
- `1L10OD`
- `1L10PR`
- `1L10SO`
- `1SALMI`
- `1SALML`
- `7687J3`

Included source/owner examples:

- `17085M` / `170588` inherit from `170858` / `670 GL85-8`
- `1668SP` inherits from `1659C2` / `659 CEN II`
- `1666AI` inherits from `1666WL` / `666 WL`
- `1SALMI` / `1SALML` inherit from `1SALOL` / `SAL OL`
- `1L10OD`, `1L10PR`, `1L10SO` inherit from L10 owner plans per manifest decisions
- `7687J3` inherits `DB` from `7686S3` / `686S 30MRG`

---

## Explicitly Excluded Items

Excluded from first pass:

| Category | Excluded Items | Reason |
|----------|----------------|--------|
| PUA non-CV | `261PUA`, `265PUA`, `280PUA` for `NP/RV/DV/DB` | Current evidence only approved PUA CV inheritance; non-CV rider behavior requires actuarial approval |
| Gross premium | `PR` / `QuikGps`, including `265PUA PR` | Gross premium overlaps PAAGERAT/direct premium source precedence |
| PAAGERAT conflicts | 301 `PR/BP/U5/U6` conflicts | Separate source-precedence workstream |
| Unapproved auto-discovery | Any plan/type not listed as `Yes` in `approved_first_pass_scope.csv` | Avoid implicit inheritance beyond approved scope |

---

## Files Reviewed

| File | Finding |
|------|---------|
| `qla_core/cv_inheritance_loader.py` | CV-only manifest builder and transform; filters `typ != "CV"` |
| `qla_core/rate_pipeline.py` | Direct `Rate_Table` stream runs first, then inherited CV, then PAAGERAT streams |
| `qla_core/rate_factor_loader.py` | Direct transform maps type, segmentation, age, duration, and value; grid builder catches collisions |
| `qla_core/rate_dbf_schema.py` | Defines type-to-table routing, field prefixes, duration paging, and formatting |
| `non_cv_gap_decision_matrix.csv` | Source/output evidence for 35 non-CV candidates |
| `proposed_non_cv_inheritance_fix.md` | Prior proposal to create manifest-driven non-CV inherited-rate support |
| `paagerat_precedence_questions.md` | Confirms PAAGERAT conflicts should stay separate |

---

## Files Proposed For Change

Implementation files:

| File | Change |
|------|--------|
| `qla_core/rate_pipeline.py` | Load non-CV inheritance manifest/config and stream approved inherited rows |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | Add enabled flag and manifest path for non-CV inheritance |
| `qla_core/rate_emit.py` | Surface non-CV inheritance verification counts/status in app rate-generation logs |

Validation/reporting files:

| File | Change |
|------|--------|
| `QLA_Migration/_validate_non_cv_inherited_rates.py` | New 100% source-to-output parity validator |
| `Issue_Log_Items/Issue_Rates_Inheritance_Validation/non_cv_inheritance_analysis/` | Store implementation validation evidence after approval |

---

## Proposed New Files

Recommended new converter module:

| File | Purpose |
|------|---------|
| `qla_core/rate_inheritance_loader.py` | Generic manifest-driven inherited `Rate_Table` loader for approved non-CV rate types |

Recommended manifest:

| File | Purpose |
|------|---------|
| `Issue_Log_Items/Issue_Rates_Inheritance_Validation/non_cv_inheritance_analysis/approved_first_pass_scope.csv` | Planning scope; can be copied or referenced as implementation manifest after approval |

Production config should reference an approved manifest path, not scan all PCOVRSGT candidates automatically.

---

## Proposed Logic

Create `qla_core/rate_inheritance_loader.py` with these responsibilities:

1. Load approved manifest rows.
2. Accept only rows where `Include In First Pass = Yes`.
3. Validate approved rate type is one of:
   - `NP`
   - `RV`
   - `DV`
   - `DB`
4. Reject/ignore:
   - `CV` (current Issue #40 loader owns CV)
   - `PR`
   - PUA excluded rows
   - any row not explicitly approved
5. Build owner-to-entry map keyed by source segment / rate-owner coverage.
6. Stream matching `Rate_Table` rows from source owner coverage under issuing `PLAN`.
7. Use existing non-CV transforms:
   - `S.TYPE_TO_TABLE[typ]`
   - `S.map_sex()`
   - `S.map_band()`
   - `S.map_uwclass()`
   - `S.source_duration_to_ql()`
   - `S.duration_to_cntl_col()`
8. Preserve lineage:
   - issuing plan
   - issuing coverage if available
   - source segment / rate-owner coverage
   - rate type
   - source line number
   - source value
9. Yield rows into the existing factor grid with `source = "INHERITED_RATE"`.

Do not use `cv_remap_ql_duration()` for non-CV.

---

## Manifest / Decision Matrix Gating Approach

Use `approved_first_pass_scope.csv` as the authoritative planning matrix.

Implementation should require all of these conditions:

1. `Include In First Pass = Yes`
2. Rate type in approved set: `NP`, `RV`, `DV`, `DB`
3. Source segment has source rows for that type
4. Issuing plan has no direct rows for that type before inheritance
5. The row is not a PUA non-CV row
6. The row is not `PR`

Recommended config block:

```json
"non_cv_rate_inheritance": {
  "enabled": true,
  "manifest_csv": "Issue_Log_Items/Issue_Rates_Inheritance_Validation/non_cv_inheritance_analysis/approved_first_pass_scope.csv",
  "approved_types": ["NP", "RV", "DV", "DB"]
}
```

This keeps the behavior auditable and reversible.

---

## Rate-Type-Specific Handling

### NP / QuikNps

Use direct non-CV duration mapping:

```text
ql_duration = source_duration - 1
```

Target table:

```text
NP -> QuikNps
```

Rate key table is handled by existing pipeline:

```text
QuikNps -> QuikPlTv
```

### RV / QuikTvs

Use direct non-CV duration mapping:

```text
ql_duration = source_duration - 1
```

Target table:

```text
RV -> QuikTvs
```

Rate key table is handled by existing pipeline:

```text
QuikTvs -> QuikPlTv
```

### DV / QuikDvs

First pass only:

- `17085M` from `170858` / `670 GL85-8`
- `170588` from `170858` / `670 GL85-8`

Use direct non-CV duration mapping:

```text
ql_duration = source_duration - 1
```

Target table:

```text
DV -> QuikDvs
```

### DB / QuikDbs

First pass only:

- `1669SR`
- `7687J3`

Use direct non-CV duration mapping:

```text
ql_duration = source_duration - 1
```

Target table:

```text
DB -> QuikDbs
```

---

## Why PR Is Excluded

`PR` / `QuikGps` is excluded because it overlaps with the separate PAAGERAT source-precedence issue.

Evidence:

- There are 301 PAAGERAT conflicts.
- 285 of those are `PR`.
- Existing output already contains premium values in many conflict cases.
- A `PR` inheritance implementation could overwrite or duplicate premium logic before the authoritative source is known.

Recommended path:

Resolve PAAGERAT precedence first, then revisit inherited `PR`.

---

## Why PUA Non-CV Is Excluded

PUA plans are excluded from first pass because Issue #40 approval covered CV inheritance only.

Excluded plans:

- `261PUA`
- `265PUA`
- `280PUA`

Excluded non-CV types:

- `NP`
- `RV`
- `DV`
- `DB`
- `PR`

Reason:

PUA riders may have different mechanics for reserves, premiums, dividends, and benefits than their source/parent plans. Source rows exist, but source existence alone is not enough to emit them safely.

---

## How Existing CV Behavior Will Be Preserved

CV should remain owned by `qla_core/cv_inheritance_loader.py`.

Preservation rules:

- Do not change `cv_inheritance_loader.py` in the first non-CV implementation unless absolutely necessary.
- Do not alter `cv_remap_ql_duration()`.
- Do not alter Issue #40 manifest behavior.
- Do not change `QuikCvs` direct or inherited transform.
- Run Issue #40 validator after implementation.

Expected regression command:

```powershell
python "QLA_Migration\_validate_issue40_inherited_cv_source_parity.py"
```

---

## How Direct Rate_Table Behavior Will Be Preserved

Direct `Rate_Table` behavior should remain first in the stream.

Implementation rules:

- Do not alter `rate_factor_loader.transform_source()`.
- Do not alter direct `Coverage_ID -> PLAN` crosswalk behavior.
- Do not mutate direct source rows.
- Do not emit inherited rows when the issuing coverage has direct rows for that type.
- Let existing collision handling surface duplicate direct/inherited conflicts.

Expected regression:

- Direct source-to-output parity must remain 100%.
- Any inherited emit causing duplicate cells should fail validation before handoff.

---

## Duplicate / Overwrite Risk

Main duplicate risk:

- Approved inherited row targets a plan/type/key that already exists from direct `Rate_Table`.

Mitigation:

1. Manifest loader checks issuing coverage has no direct rows for the approved type.
2. Pipeline grid collision detection remains active.
3. Validator reports collisions by plan/type/source.
4. No inherited row should overwrite a direct row silently.

PAAGERAT risk:

- Since non-CV inherited rows will stream before PAAGERAT, PAAGERAT may conflict with inherited rows if `PR` or premium-related types are included.
- First pass excludes `PR`, `U5`, `U6`, and `BP`, so this risk is avoided.

---

## Validation Plan

Create a new validator:

```powershell
python "QLA_Migration\_validate_non_cv_inherited_rates.py"
```

Validator requirements:

1. Load approved first-pass manifest.
2. Run pipeline in memory.
3. For each approved row:
   - source segment
   - source plan
   - issuing plan
   - rate type
   - expected source rows
   - emitted output rows
4. Validate every source cell maps to output:
   - `PLAN`
   - table
   - age
   - duration / `CNTL` / column
   - gender
   - band
   - underwriting class
   - formatted value
5. Validate owner/source plan unchanged.
6. Validate no new duplicate-cell blockers.
7. Write:
   - `non_cv_inherited_rate_parity_summary.json`
   - `non_cv_inherited_rate_plan_counts.csv`
   - `non_cv_inherited_rate_anchor_points.csv`
   - `non_cv_inherited_rate_collision_audit.csv`

Regression commands after implementation:

```powershell
python "QLA_Migration\_validate_non_cv_inherited_rates.py"
python "QLA_Migration\_validate_issue40_inherited_cv_source_parity.py"
python "QLA_Migration\_validate_issue37_quikcvs_placement.py"
python "QLA_Migration\_validate_issue41_quikcvs_endpoint.py"
```

Also run app rate generation:

```powershell
python "QLA_Migration\_emit_issue40_rate_package.py"
```

or launch app v57.55+ and click **GENERATE RATE TABLES**.

---

## Regression Plan

Required before client handoff:

| Regression | Expected |
|------------|----------|
| Direct Rate_Table parity | Still 100% |
| Issue #40 inherited CV parity | Still 100% |
| Issue #37 CV placement | PASS |
| Issue #41 CV endpoint | PASS |
| Non-CV inherited parity | 100% for approved rows |
| Direct owner plans | No row/value regressions |
| PUA non-CV | No emitted rows |
| PR / QuikGps | No changes from this fix |
| PAAGERAT conflicts | Count may remain unchanged; not part of this fix |
| Output folder hygiene | `QLA_Migration/Output/rates/` contains rate CSV tables only |

---

## Rollback Plan

Rollback should be config-gated:

1. Set `non_cv_rate_inheritance.enabled = false`.
2. Re-run rate generation.
3. Confirm approved non-CV inherited rows disappear.
4. Confirm direct rates and Issue #40 CV remain.
5. Compare row counts to pre-change baseline.

No direct conversion logic should need to be reverted if implementation is done as a separate stream.

---

## Open Business Questions

Before implementation:

1. Confirm that all 24 `approved_first_pass_scope.csv` `Yes` rows are approved for emit.
2. Confirm GL85 variants `17085M` and `170588` inherit `DV` from `170858`.
3. Confirm `1669SR` and `7687J3` should inherit `DB`.
4. Confirm L10 multi-owner source selection for `NP/RV`; current CSV references multiple source plans for some rows.
5. Confirm whether any PUA non-CV rows should be separately approved later.
6. Confirm PR remains excluded until PAAGERAT precedence is settled.

---

## Final Recommendation

Proceed to code only after explicit approval of `approved_first_pass_scope.csv`.

Recommended implementation is a new `qla_core/rate_inheritance_loader.py` module with manifest-gated `NP/RV/DV/DB` inheritance. This is safer than modifying the CV-specific loader because it preserves Issue #40 behavior and avoids applying CV duration logic to non-CV rate families.

Do not include PUA non-CV or `PR` in the first implementation.

Do not change PAAGERAT precedence in this fix.

