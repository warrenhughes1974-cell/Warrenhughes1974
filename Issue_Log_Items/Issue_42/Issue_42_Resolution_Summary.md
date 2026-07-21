# Issue #42 — Resolution Summary

**Issue:** #42 — Missing Rate Extract Rows (L01/L10)  
**Framework stage:** Closure Agent (G7)  
**Final status:** **Closed**  
**Engine version:** **v57.97** (originally closed v57.79; source refresh 2026-07-17)  
**Closed date:** 2026-07-14 (refresh closeout 2026-07-17)  
**Owner:** Conversion (Warren) · **Reporter:** Client UAT / CSO rate extracts

---

## Resolution (issue log — paste-ready)

**Resolution:** PDAGE miss-fill merged into the rate pipeline with PCOVRSGT segment resolution so resolvable age/duration NP/RV rows (including L01 10Y → 5L0110) load to QuikNps/QuikTvs; L10 LP9595 staged for inheritance. **Addendum 2026-07-17 (v57.97):** loader wired to PDAGE/PAAGERAT 20260714; rates re-emitted; L17 CV and 960 LP85-8 CV now present; residual 0824 P DTH / L10 GPO OL NP still absent. See `Issue_42_20260714_Source_Refresh_Closeout.md`.

> Copy the line above into tracking sheets and client readouts. Long-form detail follows.

---

## Problem Statement

Client UAT showed **NP** grids missing for **L01 10Y** and **L10 LP9595** (and related segments). April `Rate_Table` / `PAAGERAT` extracts had zero rows for those coverage IDs. This was a **source extract gap**, not a QLA converter mapping defect.

CSO delivered updated extracts on **2026-07-13**:

- `PDAGE_AgeDuration_Rates_Extract_20260713.csv`
- `PAAGERAT_AttainedAge_Rates_Extract_20260713.csv`
- `PAAGE_AttainedAge_Rates_Extract_20260713.csv`

Key finding: Issue #42 rows exist in **PDAGE**, not in `Rate_Table_Extract_Txt.txt`. The default loader reads Rate_Table only.

---

## Root Cause

**Category:** [x] Source extract defect  [x] Scope gap (loader)  [ ] Mapping error  [ ] Client definition

Age/duration NP/RV rates for several segment IDs were present in PDAGE but absent from Rate_Table. The R5 pipeline did not merge PDAGE miss-fill rows or resolve segment-only IDs via PCOVRSGT → crosswalk before emit.

---

## Resolution (detail)

Implemented PDAGE miss-fill in `qla_core/pdage_missfill.py` and wired into `qla_core/rate_pipeline.py` / `qla_core/rate_factor_loader.py`:

1. Copy Rate_Table staging; append ~68,675 PDAGE rows for keys missing from Rate_Table.
2. Skip append when parent policy form already has direct Rate_Table rows (avoids L10 LP95 vs L10 LP9595 collision on `1L1095`).
3. Segment-only IDs resolve via PCOVRSGT → crosswalk.
4. Unmappable PDAGE rows skipped (e.g. L17 `SEX=1`).

Validation anchor: PDAGE `L01 10Y` NP F/51/dur2 = **16.42** → QuikNps `5L0110` NP1=**16.42** ✓

### Files changed

| File | Change |
|------|--------|
| `qla_core/pdage_missfill.py` | **New** — PDAGE→Rate_Table merge + staging cache |
| `qla_core/rate_pipeline.py` | PDAGE merge, segment resolver, summary fields |
| `qla_core/rate_factor_loader.py` | Segment resolve; reject unmapped SEX/BAND/UWCLS |
| `qla_core/plan_source_paths.py` | Prefer PAAGERAT/PDAGE 20260713 |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | `issue42_pdage_missfill.enabled=true` |
| `app.py` / `QLA_Migration/app.py` | **v57.79** |
| `QLA_Migration/_validate_issue42_pdage_missfill.py` | Validation script |
| `QLA_Migration/_emit_issue42_rate_csvs.py` | Targeted QuikNps/Tvs/PlTv emit |
| `Issue_Log_Items/Issue_42/_regression_issue42.py` | Regression script |

### Rulebook changes

None.

---

## Evidence

| Artifact | Path |
|----------|------|
| Intake | `Issue_42_Intake_Summary.md` |
| Planning | `Issue_42_Planning_Report.md` |
| Dependency Gate | `Issue_42_Dependency_Gate.md` |
| Implementation | `Issue_42_Implementation_Notes.md` |
| Validation | `Issue_42_Validation_Report.md` — **PASS** |
| Regression | `Issue_42_Regression_Report.md` — **PASS** |
| Staging merge | `QLA_Migration/Staging/rate_table_pdage_missfill_merged.csv` |
| Evidence CSVs | `evidence/issue42_*.csv` |

---

## Focus plan emit counts (post-fix)

| Segment | Plan | QuikNps | QuikTvs |
|---------|------|--------:|--------:|
| L01 10Y | 5L0110 | 424 | 424 |
| L10 LP9595 | 1L10OD | 3,000 | 3,096 |
| 960 LP85-8 | 196085 | 284 | 284 |
| L17 | 1L17SP | 38 | 38 |

**L10 LP9595 note:** `1L1095`/`1L10OD`/`1L10PR` grids unchanged vs baseline — parent `L10 LP95` already filled via inheritance; LP9595 staged but first-wins after LP95.

---

## Still not loadable (documented for CSO)

| Gap | Notes |
|-----|-------|
| `L17` CV, `960 LP85-8` CV | Absent from PDAGE — CSO still pursuing |
| `0824 P DTH` NP, `L10 GPO OL` NP | **CLOSED 2026-07-20** — Eric: NP not applicable (PPBEN Status **T** / Reason **EX**) |
| L17 joint `SEX=1` rows | Unmappable encoding |
| `667 ART 95` | No PCOVRSGT parent mapping |

---

## Explicitly Not Changed

- [x] Policy `quik*.csv` tables (0 row delta in regression)
- [x] Non-candidate QuikNps/Tvs plans (54/58 unchanged)
- [x] QuikCvs / QuikGps / other rate families (regression: 0 delta vs prior emit)
- [x] Issue #25 MPOLICY padding — **PASS**
- [x] Issue #26 quikridr.MPREM — env N/A; spot-check **PASS**

---

## Production Readiness + Rate Package (G7)

| Check | Status |
|-------|--------|
| Validators PASS (G5 + G6) | **PASS** |
| `app.py` version bumped | **v57.79** (both copies) |
| Full rate CSV emit | **2026-07-14** — all Quik* rate tables to `Output/rates/` + `Test_Validation/rates/` |
| QuikUint full emit | **Waived** — `PDINTTBL_DeclaredInterestRates_Extract_20260629.csv` missing from Source; QuikUint remains empty until CSO restores PDINT extracts |
| Git commit + push | **Pending** — user has not requested |

---

## Client UAT

| Item | Status |
|------|--------|
| Load full rate package from `Output/rates/` or `Test_Validation/rates/` | **Ready** |
| Verify L01 10Y NP on plan `5L0110` | **Pending** |
| Verify L10 LP9595 RV/NP inheritance behavior | **Pending** |
| Client sign-off | Pending |

---

## Rollback

1. Set `issue42_pdage_missfill.enabled=false` in `rate_loader_config.json`.
2. Revert `qla_core/pdage_missfill.py` and pipeline hooks.
3. Re-emit rates from Rate_Table-only staging.
4. Restore `APP_VERSION` to prior release in both `app.py` copies.

---

## Issue Log Entry (paste-ready)

> **Issue #42 — Missing Rate Extract Rows (L01/L10) — Closed (2026-07-14).**  
> **Resolution:** PDAGE 20260713 miss-fill merged into rate pipeline with PCOVRSGT segment resolution so resolvable age/duration NP/RV rows (including L01 10Y → 5L0110) load to QuikNps/QuikTvs; L10 LP9595 staged for inheritance; residual L17/LP85-8 CV still require CSO source.  
> **Evidence:** G5/G6 PASS; anchor 16.42 NP verified; non-candidate plans unchanged. **UAT:** Full rate package in `Output/rates/` and `Test_Validation/rates/`. **Follow-ups:** L17/LP85-8 CV from CSO; QuikUint when PDINTTBL restored.

---

## Framework Checklist

- [x] Intake (G0)
- [x] Planning (G1)
- [x] Dependency Gate PASS (G2)
- [x] Risk (G3)
- [x] Development v57.79 (G4)
- [x] Validation PASS (G5)
- [x] Regression PASS (G6)
- [x] Closure — **`Resolution:`** one-line + long-form summary (G7)
- [ ] Git commit + push — **pending user request**
