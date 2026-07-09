# Issue #40 — Risk Review Report

**Issue:** #40 — Inherited Cash Value Rate Load  
**Framework stage:** Risk Agent (G3)  
**Status:** Conditional Go — Ready for Development after project lead acknowledgement  
**Fallback simulated:** Documentation-only risk review; implementation simulation required in Development validator  
**Generated:** 2026-07-06  
**Agent/script:** Risk Agent — read-only review

**Status note:** Risk analysis only — no production code changes made in this stage.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Development may proceed with a **CV-only, PCOVRSGT-aware inherited-rate emit** for the approved Issue #40 candidate list, provided the implementation is manifest-driven, preserves existing direct plan emits, and passes the 100% source-to-QLA validation matrix.

This is not a low-risk change because it affects actuarial rate loads. The risk is acceptable only if the loader emits inherited rows under the issuing plan without changing the source values, duration-grid logic, or existing rate-owner plan output.

---

## 1. Current vs Proposed Mapping

| Area | Current | Proposed | Change? |
|------|---------|----------|---------|
| `17085M` CV rates | No `QuikCvs` rows | Emit inherited `670 GL85-8` CV rows under `PLAN=17085M` | **Yes** |
| Fleet inherited-CV plans | 10 candidate plans have 0 current `QuikCvs` rows | Emit approved rate-owner CV rows under issuing plan | **Yes** |
| Source values | `Rate_Table` CV rows remain authoritative | Values copied from source transform only, not hand-edited | No source change |
| Duration placement | Issue #37 / #41 CV grid rules | Same rules applied to inherited rows | No logic change intended |
| Direct rate-owner plans | Existing rows under `170858`, `170588`, `1L1095`, etc. | Must remain unchanged | No |
| Product plan crosswalk | `670 GL85-M` remains `17085M` | Unchanged | No |
| RV/NP/DV | Not part of Issue #40 | Deferred | No |

---

## 2. Related Fields / Tables Untouched

| Target | Role | Touched? |
|--------|------|----------|
| `quikplan.csv` | Plan catalog / assumptions | **No**, except possible CV variation flag review if already missing |
| `quikridr.csv` | Policy rider plan references | **No** |
| `quikmstr.csv` | Policy master | **No** |
| `quikprmh.csv` | Premium history | **No** |
| `QuikNps.csv` | Net premium rates | **No** |
| `QuikGps.csv` | Gross premium rates | **No** |
| `QuikDbs.csv` | Death benefit rates | **No** |
| `QuikDvs.csv` | Dividend rates | **No** |
| `QuikTvs.csv` | Terminal reserve rates | **No** |
| `QuikCvs.csv` | Cash value rates | **Yes — targeted inherited-plan additions only** |
| `QuikPlCv.csv` | Cash value rate keys | **Yes — new issuing-plan keys only** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `qla_core/rate_factor_loader.py` | Current direct `Rate_Table.COVERAGE_ID -> PLAN` mapping and CV grid transform |
| `qla_core/rate_pipeline.py` | Rate pipeline orchestration and `SegmentResolver` setup |
| `qla_core/rate_segment_resolution.py` | Existing PCOVRSGT / PCOVR resolver, currently used for PAAGERAT paths |
| `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv` | Authoritative CV source values |
| `plan_analysis/source_data/coverage/PCOVRSGT.csv` | Inheritance segments / rate-owner slots |
| `plan_analysis/source_data/coverage/PCOVR.csv` | Product metadata including pay age |
| `Issue_Log_Items/Issue_40/Issue_40_Fleet_CV_Inheritance_Audit.csv` | Approved candidate population |
| `Issue_Log_Items/Issue_40/Issue_40_Intake_Source_Gap_Evidence.csv` | Current gap counts |
| `Issue_Log_Items/Issue_40/Issue_40_Intake_Validation_Matrix.md` | G5 acceptance criteria |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| Approved inherited-CV candidate plans | 10 |
| Issued policies affected, excluding zero-issued `261PUA` | ~1,145 |
| `17085M` issued policies | 212 |
| Candidate plans with direct source CV rows | 0 |
| Candidate plans with current `QuikCvs` rows | 0 |
| Rate-owner source CV rows for `670 GL85-8` | 9,121 |
| Current `170858` QuikCvs rows | 1,002 |
| Current `17085M` QuikCvs rows | 0 |

### Candidate Breakdown

| Priority | Plan | Coverage | Issued policies | Rate owner coverage | Current issuing-plan rows |
|----------|------|----------|----------------:|---------------------|--------------------------:|
| High | `1L10SO` | `L10 SR OLD` | 449 | `L10 PRE97`; `L10 LP95` | 0 |
| High | `17085M` | `670 GL85-M` | 212 | `670 GL85-8` | 0 |
| High | `1668SP` | `668 SPWL` | 160 | `659 CEN II` | 0 |
| High | `1L10SR` | `L10 LP95SR` | 159 | `L10 LP95`; `L10 PRE97` | 0 |
| High | `1SALMI` | `SAL MULTPL` | 153 | `SAL OL` | 0 |
| High | `1SALML` | `SAL ML` | 152 | `SAL OL` | 0 |
| Medium | `1666AI` | `897 666` | 8 | `666 WL` | 0 |
| Medium | `280PUA` | `980 PUA` | 3 | `980 END65` | 0 |
| Medium | `265PUA` | `665 PUA` | 1 | `665 STME95` | 0 |
| Low | `261PUA` | `961 PUA` | 0 | `961 ME65` | 0 |

---

## 5. Fallback Recommendation

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| A — Manifest-driven PCOVRSGT-aware CV inheritance emit | Candidate plans only | **Recommended** |
| B — Static copy of existing `QuikCvs` rows from rate-owner plan to issuing plan | Candidate plans only | Reject as primary; source lineage weaker and duplicate logic risk |
| C — GL85-only patch | `17085M` only | Accept only if user narrows scope; leaves approved fleet gaps |
| D — Change plan crosswalk to point policies at rate-owner plan | Policy tables | Reject; breaks plan identity and prior fixes |
| E — Emit RV/NP/DV inheritance too | Larger rate package | Defer; outside CV-only approval |

**Recommended fallback if validation fails:** stop emit for the failing plan only, preserve direct rate-owner output, and produce a failed-plan evidence CSV. Do not ship partial inherited rows for a plan unless all mandatory checks pass.

---

## 6. Trace Policies

| Policy | Plan | Before | Proposed | Pass condition |
|--------|------|--------|----------|----------------|
| `010367438C` | `17085M` | No plan CV rows | `17085M` has inherited CV rows from `670 GL85-8` | QLAdmin CV calculation proceeds |
| `010615191C` | `17085M` | No plan CV rows | Same | QLAdmin CV calculation proceeds |
| `010464869C` | `17085M` | No plan CV rows | Same | QLAdmin CV calculation proceeds |

Trace policy validation is not enough by itself; it supplements the full source-to-QLA grid proof.

---

## 7. Largest Intended Changes

This issue adds cash value rate rows for plans that currently have zero rows. The largest user-facing changes are by issued policy population:

| Rank | Plan | Issued policies | Intended change |
|-----:|------|----------------:|-----------------|
| 1 | `1L10SO` | 449 | Add inherited CV rows |
| 2 | `17085M` | 212 | Add inherited CV rows |
| 3 | `1668SP` | 160 | Add inherited CV rows |
| 4 | `1L10SR` | 159 | Add inherited CV rows |
| 5 | `1SALMI` | 153 | Add inherited CV rows |
| 6 | `1SALML` | 152 | Add inherited CV rows |

---

## 8. Material Calculation Impact

**Intentional impact:** QLAdmin will be able to calculate/display cash values on approved plans that currently have no `QuikCvs` rows.

**Not intended:** Changing policy values, changing rate-owner plan values, changing premiums, changing plan identity, or changing duration placement logic.

Main calculation risk is selecting the wrong rate-owner segment for multi-owner plans (`1L10SO`, `1L10SR`). These must be controlled by an explicit inheritance manifest and validation output that names the source coverage used for each emitted plan.

---

## 9. Prior Fix Preservation

| Check | Required result |
|-------|-----------------|
| Issue #25 MPOLICY padding | PASS — no policy key formatting change |
| Issue #26 MPREM / MMODPREM | PASS — no premium mapping change |
| Issue #37 CV placement | PASS — inherited rows use existing grid builder |
| Issue #41 age-100 endpoint | PASS — inherited rows land at corrected QL duration index |
| Issue #21J GL85 modal factors | PASS — `17085M` plan identity unchanged |
| Issue #31 QuikCvs baseline | Rebaseline intentional added inherited keys only |

---

## 10. Regression Testing Checklist

- [ ] `17085M` has `QuikCvs` rows after emit; before count was 0.
- [ ] `170858` row count and values unchanged.
- [ ] Every emitted `17085M` CV cell traces to `Rate_Table[670 GL85-8, TYPE=CV]`.
- [ ] Every approved fleet candidate passes `Issue_40_Intake_Validation_Matrix.md`.
- [ ] Issue #41 validator passes after inherited emit.
- [ ] Issue #37 G5 matrix passes after inherited emit.
- [ ] Non-CV rate table row counts unchanged.
- [ ] `quikplan.PLAN` for `670 GL85-M` remains `17085M`.
- [ ] `QuikPlCv` keys exist for all newly emitted issuing plans.
- [ ] Client UAT verifies at least two `17085M` policies.

---

## 11. Recommended Development Agent Task

1. Build a small, explicit CV inheritance manifest from the approved Issue #40 candidates:
   - issuing coverage
   - issuing plan
   - approved rate-owner coverage(s)
   - source-selection rule for multi-owner cases
2. Extend the rate pipeline so Rate_Table CV rows can be emitted under configured issuing plans in addition to their direct rate-owner plan.
3. Preserve current direct emit behavior; never remove or rewrite existing rate-owner rows.
4. Apply the existing Issue #37/#41 CV duration grid logic unchanged.
5. Emit / regenerate `QuikCvs.csv` and `QuikPlCv.csv`.
6. Add `QLA_Migration/_validate_issue40_inherited_cv_source_parity.py`.
7. Produce G5 evidence CSVs showing 100% source-to-QLA parity per approved plan.

Do **not** change:

- `quikridr` plan assignment
- `quikplan` plan codes
- non-CV rate families
- Issue #37/#41 duration formulas
- modal premium overrides

Version bump: required only if `app.py` or the production batch rate path versioning is touched. If changes remain in `qla_core/rate_*` and rate emit scripts only, document the rate package refresh instead.

---

## G3 Decision

**Conditional Go to Development** with the scope and controls above.

Development may begin after project lead acknowledgement of this Risk Review. If Development discovers any source-to-QLA mismatch, stop and return to Risk/Planning with the failed-plan evidence.
