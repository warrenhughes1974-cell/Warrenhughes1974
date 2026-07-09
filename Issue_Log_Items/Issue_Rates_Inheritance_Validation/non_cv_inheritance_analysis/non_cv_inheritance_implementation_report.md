# Non-CV Inherited Rate Implementation Report

**Date:** 2026-07-07  
**Status:** CLOSED — implementation complete, validation PASS  
**Issue:** First-pass non-CV inherited/shared rate resolution (`Issue_Rates_Inheritance_Validation`)

---

## Summary

First-pass non-CV inherited/shared rate resolution has been implemented per approved scope in `approved_first_pass_scope.csv`. A manifest-driven loader (`qla_core/rate_inheritance_loader.py`) emits inherited `NP`, `RV`, `DV`, and `DB` rows from approved source segments under issuing plan codes.

**Total inherited non-CV `IN_SCOPE` cells emitted:** **375,840**  
**Source-to-output mismatches:** **0**  
**Inherited-plan grid collisions:** **0**

All 24 approved manifest entries produced output. All four requested validation commands passed. Issue #40 CV inheritance, direct `Rate_Table` conversion, PAAGERAT precedence logic, PUA non-CV rates, and `PR` / `QuikGps` inheritance were not changed by this implementation.

---

## Files Changed

| File | Change |
|------|--------|
| `qla_core/rate_inheritance_loader.py` | **New** — manifest builder and `transform_inherited_rates()` for approved non-CV types |
| `qla_core/rate_pipeline.py` | Wired non-CV inheritance stream after direct transform and Issue #40 CV, before PAAGERAT |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | Added `non_cv_rate_inheritance` config block (enabled) |
| `QLA_Migration/_validate_non_cv_inherited_rates.py` | **New** — source-to-output parity validator |

**Preserved unchanged:**

- `qla_core/cv_inheritance_loader.py` — Issue #40 CV inheritance
- `qla_core/rate_factor_loader.py` — direct `Rate_Table` transform
- PAAGERAT loaders and precedence logic

---

## Approved Scope Implemented

Manifest source: `approved_first_pass_scope.csv` (`Include In First Pass = Yes`)

| Rate Type | Target Table | Approved Plans |
|-----------|--------------|----------------|
| `NP` | `QuikNps` | `1666AI`, `1668SP`, `1669SR`, `1679CS`, `170588`, `17085M`, `1L10OD`, `1L10PR`, `1L10SO` |
| `RV` | `QuikTvs` | `1666AI`, `1668SP`, `1669SR`, `1679CS`, `170588`, `17085M`, `1L10OD`, `1L10PR`, `1L10SO`, `1SALMI`, `1SALML` |
| `DV` | `QuikDvs` | `170588`, `17085M` (from `170858` / `670 GL85-8`) |
| `DB` | `QuikDbs` | `1669SR`, `7687J3` |

**Manifest entries:** 24 plan/rate-type rows across 12 issuing plans.

---

## Explicit Exclusions

The following were intentionally excluded from this first pass and were not emitted by the non-CV inheritance loader:

| Exclusion | Items | Reason |
|-----------|-------|--------|
| PUA non-CV | `261PUA`, `265PUA`, `280PUA` | Requires separate actuarial approval |
| `PR` / `QuikGps` | All gross-premium inherited candidates | Excluded to avoid premium source conflicts |
| PAAGERAT precedence | 301 source/output conflicts | Separate workstream; not inherited-rate gaps |
| Unlisted inherited rates | Any row not in `approved_first_pass_scope.csv` with `Include In First Pass = Yes` | Manifest-gated scope only |

**Confirmed by validation:**

- PUA non-CV rows were **not** emitted (11 excluded manifest rows checked)
- Inherited `PR` / `QuikGps` rows from this loader: **0**
- PAAGERAT precedence logic was **not** included or changed

---

## Pipeline Placement

```
transform_source (direct Rate_Table)
  → transform_inherited_cv (Issue #40)
  → transform_inherited_rates (non-CV first pass)   ← NEW
  → PAAGERAT loaders (PR/BP/U6/U5)
```

Rollback: set `non_cv_rate_inheritance.enabled = false` in `rate_loader_config.json`.

---

## Row Counts by Plan / Rate Type / Table

The non-CV inherited loader emitted **375,840** `IN_SCOPE` source cells from the approved manifest. The table below lists source cells checked/emitted and final factor-grid key counts by plan/rate/table.

| Issuing Plan | Rate Type | Target Table | Source Plan | Source Segments | Source Cells Emitted | Factor Grid Keys | Mismatches |
|---|---:|---|---|---|---:|---:|---:|
| 1666AI | NP | QuikNps | 1666WL | 666 WL | 9,890 | 1,064 | 0 |
| 1666AI | RV | QuikTvs | 1666WL | 666 WL | 9,890 | 1,064 | 0 |
| 1668SP | NP | QuikNps | 1659C2 | 659 CEN II | 19,780 | 2,128 | 0 |
| 1668SP | RV | QuikTvs | 1659C2 | 659 CEN II | 19,780 | 2,128 | 0 |
| 1669SR | DB | QuikDbs | 1659SR | 659 SR GD | 100 | 10 | 0 |
| 1669SR | NP | QuikNps | 1659C2 | 659 CEN II; 659 CEN SR; 659 SR GD; L14 | 22,666 | 2,456 | 0 |
| 1669SR | RV | QuikTvs | 1659C2 | 659 CEN II; 659 CEN SR; 659 SR GD; L14 | 22,654 | 2,456 | 0 |
| 1679CS | NP | QuikNps | 1659C2 | 659 CEN II; L14 | 22,666 | 2,456 | 0 |
| 1679CS | RV | QuikTvs | 1659C2 | 659 CEN II; L14 | 22,654 | 2,456 | 0 |
| 170588 | DV | QuikDvs | 170858 | 670 GL85-8 | 7,126 | 770 | 0 |
| 170588 | NP | QuikNps | 170858 | 670 GL85-8 | 6,988 | 770 | 0 |
| 170588 | RV | QuikTvs | 170858 | 670 GL85-8 | 9,230 | 986 | 0 |
| 17085M | DV | QuikDvs | 170858 | 670 GL85-8 | 7,126 | 770 | 0 |
| 17085M | NP | QuikNps | 170858 | 670 GL85-8 | 6,988 | 770 | 0 |
| 17085M | RV | QuikTvs | 170858 | 670 GL85-8 | 9,230 | 986 | 0 |
| 1L10OD | NP | QuikNps | 1L1095 | L10 LP95 | 27,606 | 3,000 | 0 |
| 1L10OD | RV | QuikTvs | 1L1095 | L10 LP95 | 28,908 | 3,096 | 0 |
| 1L10PR | NP | QuikNps | 1L1095 | L10 LP95 | 27,606 | 3,000 | 0 |
| 1L10PR | RV | QuikTvs | 1L1095 | L10 LP95 | 28,908 | 3,096 | 0 |
| 1L10SO | NP | QuikNps | 1L1095 | L10 LP95; L10 LP95SR | 27,606 | 3,000 | 0 |
| 1L10SO | RV | QuikTvs | 1L1095 | L10 LP95; L10 LP95SR | 28,908 | 3,096 | 0 |
| 1SALMI | RV | QuikTvs | 1SALOL | SAL OL | 4,750 | 508 | 0 |
| 1SALML | RV | QuikTvs | 1SALOL | SAL OL | 4,750 | 508 | 0 |
| 7687J3 | DB | QuikDbs | 7686S3 | 686S 30MRG | 30 | 3 | 0 |

**Parity confirmation:** All 24 plan/rate rows — **0 mismatches**.

---

## Validation Command Results

All requested validation commands completed with exit code `0` (2026-07-07).

| Command | Result |
|---------|--------|
| `python QLA_Migration/_validate_non_cv_inherited_rates.py` | **PASS** |
| `python QLA_Migration/_validate_issue40_inherited_cv_source_parity.py` | **PASS** |
| `python QLA_Migration/_validate_issue37_quikcvs_placement.py` | **PASS** |
| `python QLA_Migration/_validate_issue41_quikcvs_endpoint.py` | **PASS** |

### Non-CV Validator Checks

| Check | Result |
|-------|--------|
| 24 manifest entries loaded | PASS |
| Source-to-output parity (merged segment order) | PASS — **0 mismatches** across all plan/type rows |
| Inherited-plan grid collisions | PASS — **0** |
| Anchor points | **72 / 72** PASS |
| PUA excluded plans | PASS — no unexpected output |
| Inherited `PR` / `QuikGps` from loader | PASS — **0** rows |
| Direct owner plan keys preserved | PASS (sampled) |
| Direct `Rate_Table` transform count | PASS — 774,400 direct `IN_SCOPE` cells still reconcile |
| Pipeline `IN_SCOPE` total | 1,262,713 |

### Regression Validation Results

| Command | Result | Notes |
|---------|--------|-------|
| `_validate_non_cv_inherited_rates.py` | PASS | 24 manifest entries, 375,840 inherited `IN_SCOPE` cells, 0 mismatches, 0 inherited collisions |
| `_validate_issue40_inherited_cv_source_parity.py` | PASS | Issue #40 CV parity preserved; 101,793 inherited CV `IN_SCOPE` rows, 0 mismatches |
| `_validate_issue37_quikcvs_placement.py` | PASS | QuikCvs placement proof cases passed |
| `_validate_issue41_quikcvs_endpoint.py` | PASS | 5/5 endpoint examples passed; failures list empty |

---

## Evidence Artifacts

Written under `non_cv_inheritance_analysis/evidence/`:

- `non_cv_inherited_rate_parity_summary.json`
- `non_cv_inherited_rate_plan_counts.csv`
- `non_cv_inherited_rate_anchor_points.csv`

Related analysis and planning artifacts:

- `approved_first_pass_scope.csv`
- `implementation_plan_non_cv_inheritance.md`
- `non_cv_inheritance_analysis_report.md`

---

## Remaining Unrelated Blocker (Pre-Existing)

Regression validators report **1 unrelated pipeline blocker** that predates this implementation:

| ID | Severity | Table | Detail |
|----|----------|-------|--------|
| `V-UINT-PDINT` | BLOCKER | `QuikUint` | `PDINTTBL` extract missing or not configured |

This blocker is outside the scope of non-CV inherited rate resolution. It does not affect non-CV inheritance parity results and was **not introduced** by this implementation. Issue #37 and Issue #40 validators still pass their targeted proof cases despite this unrelated blocker.

---

## Risks and Deferred Items

- Multi-segment manifest rows merge with **manifest segment order first-wins** when owner segments share grid keys with differing values (e.g. `1669SR` NP/RV uses `659 CEN II` before `659 CEN SR` / `659 SR GD` / `L14`).
- PAAGERAT precedence logic unchanged; `PR` remains excluded to avoid premium source conflicts.
- PUA non-CV inheritance (`261PUA`, `265PUA`, `280PUA`) deferred pending actuarial approval.
- Config-gated rollback remains the primary safety mechanism.

---

## Final Implementation Status

| Item | Status |
|------|--------|
| Approved first-pass scope implemented | **COMPLETE** |
| Source-to-output parity | **PASS — 0 mismatches** |
| Inherited collisions | **PASS — 0** |
| Issue #40 CV regression | **PASS** |
| Issue #37 / #41 CV regression | **PASS** |
| PUA non-CV untouched | **CONFIRMED** |
| `PR` / `QuikGps` untouched | **CONFIRMED** |
| PAAGERAT precedence untouched | **CONFIRMED** |
| Unrelated `V-UINT-PDINT` blocker | **PRE-EXISTING — outside this issue** |

**Recommendation:** Close first-pass non-CV inherited rate resolution. Track PUA non-CV, `PR` inheritance, and PAAGERAT precedence as separate follow-on items.
