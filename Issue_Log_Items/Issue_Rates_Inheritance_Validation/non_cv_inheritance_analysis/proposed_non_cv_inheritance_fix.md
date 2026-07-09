# Proposed Non-CV Inheritance Fix

**Status:** Proposal only  
**Code status:** Not implemented  

---

## Files Likely Needing Changes

Likely implementation files:

| File | Proposed role |
|------|---------------|
| `qla_core/rate_inheritance_loader.py` | New generalized inherited-rate loader for approved non-CV rate types |
| `qla_core/cv_inheritance_loader.py` | Leave intact or delegate CV path after parity is proven |
| `qla_core/rate_pipeline.py` | Wire approved inherited non-CV stream after direct `Rate_Table` transform, before PAAGERAT loaders |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | Add manifest/config block for approved inherited non-CV scope |
| `qla_core/rate_validation.py` | Add warning/report for unresolved inherited-rate candidates |
| `qla_core/rate_emit.py` | Include inherited non-CV verification status in app output |

Likely validation files:

| File | Proposed role |
|------|---------------|
| `QLA_Migration/_validate_non_cv_inherited_rates.py` | 100% source-to-output parity validator |
| `Issue_Log_Items/Issue_Rates_Inheritance_Validation/non_cv_inheritance_analysis/` | Evidence and closure artifacts |

---

## Proposed Logic

The non-CV inherited-rate loader should follow the proven Issue #40 CV model, but be manifest-driven by type.

For each approved manifest row:

1. Read issuing coverage and issuing plan.
2. Confirm issuing coverage has no direct `Rate_Table` rows for the approved type.
3. Confirm source/rate-owner coverage has rows for the approved type.
4. Emit source rows under the issuing `PLAN`.
5. Use existing schema routing:
   - `NP` → `QuikNps`
   - `RV` → `QuikTvs`
   - `DV` → `QuikDvs`
   - `DB` → `QuikDbs`
   - `PR` → `QuikGps` only after PAAGERAT precedence is settled
6. Reuse existing segmentation mappings:
   - gender
   - band
   - underwriting class
   - issue age
   - country/state
   - effective date
7. Reuse existing non-CV duration behavior:
   - `source_duration_to_ql(duration)` = LifePRO duration minus 1
8. Let the existing grid builder catch duplicate cells.

Important:

- Do not infer non-CV inheritance automatically from PCOVRSGT at runtime.
- Require an approved manifest for every plan/type/source relationship.
- Keep current Issue #40 CV validation unchanged.

---

## Should This Reuse Issue #40 CV Resolver?

Yes for structure, no for CV-specific duration logic.

Reusable concepts:

- manifest-driven scope
- issuing coverage has no direct source rows
- rate owner has source rows
- multi-owner selection based on approved/declared rule
- emit under issuing `PLAN`
- source lineage fields for validation

Do not reuse blindly:

- `cv_remap_ql_duration()` is CV-specific and should not be applied to NP/RV/DV/DB/PR unless separately proven.
- CV maturity truncation should remain CV-specific.

Best design:

- Keep a shared manifest/resolution helper.
- Implement rate-type-specific row transforms.
- Keep CV path exactly as-is until non-CV validation is proven.

---

## Rate-Type-Specific Exceptions

### Include in first implementation only after approval

Recommended first scope:

- `NP` for non-PUA plans
- `RV` for non-PUA plans
- `DV` for explicitly approved dividend plans, starting with GL85 variants if approved
- `DB` for explicitly approved non-PUA plans

### Exclude from first implementation

- `PR` / `QuikGps`

Reason:

Gross premium has known PAAGERAT conflicts and source precedence questions. Do not solve gross premium inheritance in the same change as NP/RV/DV/DB.

### PUA exception

For `261PUA`, `265PUA`, and `280PUA`, keep non-CV rows out of scope unless actuarial confirms that PUA riders should inherit parent:

- `NP`
- `RV`
- `DV`
- `DB`
- `PR`

Current evidence only approved PUA CV inheritance.

---

## Test Plan

For every approved plan/type/source relationship:

1. Build manifest from approved scope.
2. Run rate pipeline in memory.
3. Validate source row count equals emitted inherited row count after any documented exclusions.
4. Validate 100% source-to-output cell parity:
   - plan
   - type/table
   - gender
   - issue age
   - duration/CNTL/column
   - band
   - underwriting class
   - value formatting
5. Validate issuing plan now has factor rows and rate-key/member rows.
6. Validate rate-owner plan row count and values unchanged.
7. Validate no new duplicate-cell blockers.
8. Validate Issue #40 CV still passes.
9. Validate Issue #37/#41 CV duration still passes.
10. Validate generated `QuikPlxx` key rows exist for each newly emitted table family.

Suggested validator output:

- `non_cv_inherited_rate_parity_summary.json`
- `non_cv_inherited_rate_anchor_points.csv`
- `non_cv_inherited_rate_plan_counts.csv`
- `non_cv_inherited_rate_collision_audit.csv`

---

## Regression Plan

Required regression checks:

- Direct `Rate_Table` source-to-output parity remains 100%.
- Issue #40 inherited CV source-to-output parity remains 100%.
- `QuikCvs.csv` row counts for approved CV plans remain expected.
- Existing direct owner plans unchanged.
- No non-approved plan/type emits inherited rows.
- `QuikPlCv`, `QuikPlTv`, `QuikPlDv`, `QuikPlDb`, `QuikPlGp` key generation remains schema-valid.
- Member tables `QuikPlGd/Uw/Bd/St/Nb` include new segment combinations only when new factor rows require them.

---

## Rollback Plan

Rollback should be simple and scoped:

1. Disable non-CV inheritance config flag.
2. Re-run `GENERATE RATE TABLES`.
3. Confirm only direct rates + Issue #40 CV inheritance remain.
4. Compare row counts to pre-change baseline.

Implementation should not overwrite or alter direct source conversion logic. It should add a separate stream that can be disabled in config.

---

## Required Approval Before Coding

Business/actuarial must approve:

1. Which plan/type/source rows are in scope.
2. Whether PUA non-CV inheritance is valid.
3. Whether GL85 variants inherit `NP`, `RV`, and `DV` from `670 GL85-8`.
4. Whether `DB` inheritance is valid for `1669SR` and `7687J3`.
5. Whether `PR` should remain out of scope until PAAGERAT precedence is resolved.

