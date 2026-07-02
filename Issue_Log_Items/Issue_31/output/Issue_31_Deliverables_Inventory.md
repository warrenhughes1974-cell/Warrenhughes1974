# Issue #31 — Deliverables Inventory

**Date:** 2026-06-30  
**Scope:** PR-1 through PR-4, validation, CSV emit, research closeout

---

## 1. Core implementation (`qla_core/`)

| File | PR | Purpose |
|------|-----|---------|
| `rate_dbf_schema.py` | 3–4 | QuikCoi, QuikGcoi factor schema; QX CHAR(10); no QuikPlCoi/QuikPlGcoi key mapping |
| `rate_factor_loader.py` | 1–4 | ISWL helpers; `quikcvs_keys_by_plan`, `quikcoi_keys_by_plan`, `quikgcoi_keys_by_plan` |
| `rate_pipeline.py` | 2–4 | BP/U6/U5 streams; paagerat status tracking |
| `rate_validation.py` | 2–4 | TYPE_FAMILY; ISWL_BP/COI/GCOI MPLAN sets |
| `paagerat_pr_loader.py` | 2–4 | VARGP=3 plan union; BP suppress |
| `paagerat_bp_loader.py` | 2 | PAAGERAT BP → QuikGps |
| `paagerat_ul_coi_loader.py` | 3–4 | Shared U5/U6 attained-age scalar loader |

---

## 2. Configuration

| File | Purpose |
|------|---------|
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | ISWL phases 1–4 enabled; validator authority |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.example.json` | Synced template; emit script default |
| `plan_analysis/phase_r5_rate_loader/emit_manifest.csv` | Last emit manifest |
| `plan_analysis/phase_r5_rate_loader/emit_summary.json` | Last emit summary |

---

## 3. Validators (`tools/validators/`)

| File | Phase | Checks |
|------|-------|--------|
| `iswl_common.py` | All | Shared paths, constants, output dirs |
| `iswl_psegt_cv_gate.py` | 1 | V-CVS-01 PSEGT CV 8/8 |
| `iswl_quikcvs_reconcile.py` | 1 | V-CVS-02–04, V-X-01, V-X-03 |
| `iswl_quikcvs_parity.py` | 1 | V-CVS-05 PDAGE parity |
| `iswl_quikgps_reconcile.py` | 2 | V-GPS-01–04 |
| `iswl_quikcoi_reconcile.py` | 3 | V-COI-01–08; output filename package check |
| `iswl_quikgcoi_reconcile.py` | 4 | V-GCOI-01–05; output filename package check |

---

## 4. Validation artifacts (`Issue_Log_Items/Issue_31/output/`)

### Phase 1 — QUIKCVS

| File |
|------|
| `Phase1_QUIKCVS/iswl_quikcvs_reconcile_summary.json` |
| `Phase1_QUIKCVS/iswl_quikcvs_keys_by_mplan.csv` |
| `Phase1_QUIKCVS/iswl_psegt_cv_gate_report.csv` |
| `Phase1_QUIKCVS/iswl_quikcvs_parity_report.md` |
| `Phase1_QUIKCVS/iswl_quikcvs_parity_by_coverage.csv` |

### Phase 2 — QUIKGPS

| File |
|------|
| `Phase2_QUIKGPS/iswl_quikgps_reconcile_summary.json` |
| `Phase2_QUIKGPS/iswl_quikgps_keys_by_mplan.csv` |

### Phase 3 — QUIKCOI

| File |
|------|
| `Phase3_QUIKCOI/iswl_quikcoi_reconcile_summary.json` |
| `Phase3_QUIKCOI/iswl_quikcoi_keys_by_mplan.csv` |

### Phase 4 — QUIKGCOI

| File |
|------|
| `Phase4_QUIKGCOI/iswl_quikgcoi_reconcile_summary.json` |
| `Phase4_QUIKGCOI/iswl_quikgcoi_keys_by_mplan.csv` |

### Regression baselines

| File |
|------|
| `baselines/iswl_quikcvs_regression_baseline.json` |
| `baselines/iswl_quikgps_regression_baseline.json` |
| `baselines/iswl_quikcoi_regression_baseline.json` |
| `baselines/iswl_quikgcoi_regression_baseline.json` |

### Pipeline dry-run

| File |
|------|
| `pipeline/dryrun_validation_issues.csv` |
| `pipeline/dryrun_summary.json` |
| `pipeline/age_cap_audit.csv` |
| `pipeline/age_cap_collision_audit.csv` |

### Closeout / review reports

| File |
|------|
| `Issue_31_Final_ISWL_Rate_Table_Validation_Review.md` |
| `Issue_31_ISWL_Rate_Table_CSV_Emit_Report.md` |
| `Issue_31_ISWL_Rate_Table_Implementation_Completion_Report.md` |
| `Issue_31_Deliverables_Inventory.md` (this file) |

---

## 5. Implementation notes (`Issue_Log_Items/Issue_31/`)

| File |
|------|
| `Issue_31_Phase1_QUIKCVS_Implementation_Notes.md` |
| `Issue_31_Phase2_QUIKGPS_Implementation_Notes.md` |
| `Issue_31_Phase3_QUIKCOI_Implementation_Notes.md` |
| `Issue_31_Phase4_QUIKGCOI_Implementation_Notes.md` |

---

## 6. Research & pre-implementation (Issue #31 origin)

| File | Purpose |
|------|---------|
| `Issue_31_Extract_Validation_Report.md` | PSEGT/PDINT/PDINTTBL extract validation |
| `Issue_31_PSEGT_PDINT_Followup_Report.md` | Segment follow-up |
| `Issue_31_Resolution_Recommendation.md` | Source dependency resolution |
| `Issue_31_Resolution_Status.md` | Issue status (updated at closeout) |
| `docs/research/ISWL_Segment_Trace/*` | Segment trace research |
| `docs/research/ISWL_Implementation/*` | Blueprint, table design, validation strategy, dev order |
| `tools/research/iswl_issue31_followup_20260629.py` | Extract validation script |

---

## 7. CSV test package (`QLA_Migration/Output/rates/`)

### Required ISWL factor tables

| File | Rows |
|------|-----:|
| `QuikCvs.csv` | 25,717 |
| `QuikGps.csv` | 12,567 |
| `QuikCoi.csv` | 792 |
| `QuikGcoi.csv` | 198 |

### Companion tables (same emit — CV/GPS/DB families only)

| File | Rows |
|------|-----:|
| `QuikPlCv.csv` | 70 |
| `QuikPlGp.csv` | 205 |
| `QuikPlNb.csv`, `QuikPlSt.csv`, `QuikPlUw.csv`, `QuikPlBd.csv`, `QuikPlGd.csv` | member/dimension |
| `QuikDbs.csv`, `QuikDvs.csv`, `QuikNps.csv`, `QuikTvs.csv` | non-ISWL fleet tables |
| `rate_csv_manifest.csv` | emit manifest |

**Removed from package (2026-07-02):** `QuikPlCoi.csv`, `QuikPlGcoi.csv` — quarantined under `output/quarantine_invalid_artifacts/`.

---

## 8. Source inputs (external / not generated)

| Path | Used by |
|------|---------|
| `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv` | QUIKCVS |
| `plan_analysis/source_data/rates/PAAGERAT_AttainedAge_Rates_Extract_20260428.csv` | QUIKGPS, QUIKCOI, QUIKGCOI |
| `QLA_Migration/Source/PSEGT_Segment_Extract_20260629.csv` | Segment gates |
| `QLA_Migration/Source/PDAGE_AgeDuration_Rates_Extract_20260530.csv` | Parity study (non-authoritative) |

---

## 9. Legacy / superseded paths

The following may exist from earlier runs before output-folder consolidation; **`output/` is authoritative**:

- `Issue_Log_Items/Issue_31/Phase1_QUIKCVS/` (duplicate)
- `Issue_Log_Items/Issue_31/Phase2_QUIKGPS/` (duplicate)
- `Issue_Log_Items/Issue_31/Phase3_QUIKCOI/` (duplicate)
- `Issue_Log_Items/Issue_31/Phase4_QUIKGCOI/` (duplicate)
- `QLA_Migration/Archive/rates/` — pre-ISWL stale emit (do not use for UAT)
