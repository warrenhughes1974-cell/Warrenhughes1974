# Issue #88 — Intake Summary

**Issue:** #88 — ISWL QuikIssc / QuikUint empty in batch CSV package (delivery defects D1 + D2)  
**Framework stage:** Intake Agent (G0)  
**Status:** Intake Complete → Planning (Pre-Risk Auto-Chain)  
**Generated:** 2026-07-21  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Conversion (Warren)  
**Priority:** High — blocks Sujitha ISWL CSO UAT (surrender charges + credited interest)  
**Code changes:** None at Intake  

**Opened from:** Sujitha email 2026-07-20 (ISWL CSO setup) + source/repo review logged in `Issue_Log_Items/Issue_ISWL/Issue_ISWL_Open_Business_Questions.md` (defects D1, D2).

---

## 1. Symptom in plain English

Sujitha reported that QUIKISSC (ISWL surrender charges) looked incomplete — specifically that plans **1659CR**, **1659SR**, and **1669SR** had no surrender-charge data.

Repo review shows a stronger failure: the **entire** delivered `QuikIssc.csv` in `QLA_Migration/Output/rates/` is **header-only (0 data rows)** for all eight ISWL plans. The same package also shipped **`QuikUint.csv` with 0 rows** (ISWL credited interest).

This is **not** a LifePRO source gap for surrender charges. The QuikIssc loader still builds **8 valid rows** from hub `659 CEN II` SL rates (verified 2026-07-21). The data is generated but not written into the batch CSV package.

---

## 2. Evidence

| Artifact | Finding |
|----------|---------|
| Delivered QuikIssc | `QLA_Migration/Output/rates/QuikIssc.csv` — header only (~187 bytes, 2026-07-19) |
| Delivered QuikUint | `QLA_Migration/Output/rates/QuikUint.csv` — header only |
| Manifest | `rate_csv_manifest.csv` shows `QuikIssc` / `QuikUint` with **0 rows** |
| Last batch blockers | `plan_analysis/phase_r5_rate_loader/dryrun_validation_issues.csv` → `V-UINT-PDINT` BLOCKER (PDINTTBL missing) |
| Loader smoke test | `quikissc_loader.load_quikissc_from_config` → **8 rows**, 0 blockers (2026-07-21) |
| Uint smoke test | `quikuint_loader.load_quikuint_from_config` → **0 rows**, `BLOCKER_NO_PDINTTBL` |
| Config paths | `rate_loader_config.json` points `pdint_*` / `psegt_csv` at `*_20260629.csv` — **files absent** |
| Source present | `PDINT*_20260630.csv`, `PSEGT*_20260630.csv` **exist** |
| Phase6 approved keys | `Issue_33/.../iswl_quikissc_keys_by_mplan.csv` — all 8 plans incl. 1659CR/SR, 1669SR |
| CLI emitter pattern | `rate_loader_emit.py` lines 92–101 **do** write QuikIssc/QuikUint CSV |
| Batch emitter gap | `qla_core/rate_emit.py` CSV branch writes Uwpo + QuikAint but **not** QuikIssc/QuikUint (DBF branch has both) |
| Parent log | `Issue_ISWL` OBQ-4 (answered — delivery defect), D1, D2 |

Example plans (ISWL fleet): `1658C1`, `1658CS`, `1659C2`, `1659CR`, `1659CS`, `1659SR`, `1669SR`, `1679CS`.

---

## 3. Suspected domain

**Rate package emit / config path defect** (not conversion mapping, not Sujitha plan-setup logic).

1. **D1 — CSV emit gap:** `qla_core/rate_emit.py` `run_rate_emit` CSV path omits `write_quikissc_csv` / `write_quikuint_csv`.  
2. **D2 — Stale config:** PDINT / PDINTTBL / PSEGT paths still name 20260629 extracts that are not in Source; 20260630 files are present. Partial-emit whitelist allows batch to succeed with empty QuikUint.

---

## 4. In scope / out of scope

### In scope

- Surgical CSV write for QuikIssc + QuikUint in `qla_core/rate_emit.py` (mirror DBF branch / R5 CLI)  
- Repoint `pdint_extract`, `pdinttbl_extract`, and `psegt_csv` in `rate_loader_config.json` (and example if needed) to existing 20260630 Source files  
- Re-emit rate CSVs; publish corrected `QuikIssc.csv` / `QuikUint.csv` to `Output/Test_Validation/rates/` on validation PASS  
- Validation via existing `tools/validators/iswl_quikissc_reconcile.py` and `iswl_quikuint_reconcile.py`  
- Document redelivery note for Sujitha  

### Out of scope (remain on Issue_ISWL OBQs)

- COI per-$1,000 basis confirmation (OBQ-6)  
- Expanding COI/GCOI fleet beyond allowlist (OBQ-7 / OBQ-8)  
- Guideline premium / quikspec conversion (OBQ-9)  
- Loan credited-interest decode (OBQ-10)  
- Female QuikIssc companion rows (OBQ-3 residual — waiting on Sujitha)  
- D3 COI re-baseline vs 7/13 PAAGERAT refresh (separate validation follow-up; not required to unblock QuikIssc/QuikUint delivery)

### Explicitly not changing

- QuikIssc / QuikUint loader business rules (hub SL schedule, AGE=0, M-only; CENII A1 union_merge)  
- Allowlists for COI/GCOI/GPS  
- Policy conversion tables / Sync_Rulebooks  
- Architecture redesign of rate pipeline  

---

## 5. Severity / blast radius

| Dimension | Assessment |
|-----------|------------|
| Severity | **High** — ISWL surrender + credited interest tables empty in client-facing package |
| Blast radius | Rate CSV emit path only; factor/key/member tables already emit correctly |
| Rollback | Revert `rate_emit.py` + config path edits; prior empty CSVs remain recoverable from Archive if needed |
| Client impact | Sujitha cannot UAT ISWL surrender / interest setup until redelivered |

---

## 6. Artifacts required before Development

| Artifact | Purpose |
|----------|---------|
| Planning Report | Confirm exact edit sites + expected row counts |
| Dependency Gate | Confirm Source files + validators present |
| Risk Review | Go/No-Go; partial-emit interaction |
| Implementation Notes | Diff + APP_VERSION if app path touched (likely **no** app.py change if only `qla_core/rate_emit.py` + config) |
| Validation / Regression | QuikIssc 8 rows; QuikUint non-empty for 8 MPLANs; unrelated rate tables unchanged |

---

## 7. Gate G0 checklist

| Check | Result |
|-------|--------|
| Issue ID assigned | **#88** |
| Symptom clear | Yes — empty QuikIssc/QuikUint in batch CSV |
| Evidence attached | Yes |
| In/out of scope set | Yes |
| Owner / priority | Warren / High |
| Code at Intake | None |

**G0:** **PASS** → continue Pre-Risk Auto-Chain to Planning.
