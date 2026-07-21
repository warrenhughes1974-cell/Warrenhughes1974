# Issue #88 — Planning Report

**Issue:** #88 — ISWL QuikIssc / QuikUint empty in batch CSV package (D1 + D2)  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning Complete → Dependency Gate  
**Generated:** 2026-07-21  
**Model:** Cursor Grok 4.5 (locked)  
**Code changes:** None  

---

## 1. Executive Finding

Two independent defects empty the ISWL surrender-charge and credited-interest tables in the **batch CSV** package. **D1** is a missing write in `qla_core/rate_emit.py` (CSV branch never calls QuikIssc/QuikUint writers even when loaders return rows). **D2** is stale config pointing PDINT/PDINTTBL/PSEGT at missing `*_20260629.csv` files while `*_20260630.csv` exists — causing `V-UINT-PDINT` and 0 QuikUint rows. QuikIssc loader itself is healthy (8 rows from hub SL). Recommended fix is surgical: add the two CSV writes (mirror R5 CLI / DBF branch) and repoint three config paths. No loader logic, allowlist, or schema changes. Ready for Dependency Gate.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source | File | In Source? | Role |
|--------|------|:----------:|------|
| Rate_Table SL | `QLA_Migration/Source/Rate_Table_Extract_Txt.txt` | Yes | Hub `659 CEN II` SL → QuikIssc (14 durations) |
| PDINT | `PDINT_DeclaredInterestRates_Extract_20260630.csv` | Yes | ISWL credited interest (A1 / CENII) |
| PDINTTBL | `PDINTTBL_DeclaredInterestRates_Extract_20260630.csv` | Yes | Interest tier tables |
| PSEGT | `PSEGT_Segment_Extract_20260630.csv` | Yes | Segment resolve for uint/issc validators |
| Stale config targets | `*_20260629.csv` for PDINT/PDINTTBL/PSEGT | **No** | Cause of D2 |

### Available source fields (QuikIssc)

| Field | Source | Notes |
|-------|--------|-------|
| SCHG01–14 | Rate_Table VALUE by DURATION 1–14 | Percent literals; SCHG15–20 blank |
| PLAN | ISWL MPLAN allowlist (8) | Hub schedule replicated |
| AGE / GENDER / UWCLASS / BAND | Constants AGE=0, M, SM, 01 | SME-approved Issue #33 |

### Available source fields (QuikUint)

| Field | Source | Notes |
|-------|--------|-------|
| MPLAN | ISWL allowlist (8) | Phase5 config |
| MEFFDATE / MGTDRATE / MCURRATE | PDINT + PDINTTBL CENII A1 | union_merge rules already coded |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Fields (relevant) | Schema source |
|-------|-------------------|---------------|
| QuikIssc | PLAN, AGE, GENDER, UWCLASS, BAND, ISSCNTRY, ISSUEST, SCHG01–SCHG20 | `rate_dbf_schema.quikissc_fields()` / Help §7.144 |
| QuikUint | MPLAN, MEFFDATE, MGTDRATE, MCURRATE | `rate_dbf_schema.quikuint_fields()` / Help §7.223 |

**Repo population paths:**

| Location | Role |
|----------|------|
| `qla_core/quikissc_loader.py` | Build QuikIssc rows (working) |
| `qla_core/quikuint_loader.py` | Build QuikUint rows (blocked by D2) |
| `qla_core/rate_pipeline.py` | Loads both into `PipelineResult` |
| `qla_core/rate_emit.py` | **Bug site** — CSV omit; DBF OK |
| `plan_analysis/phase_r5_rate_loader/rate_loader_emit.py` | Correct CSV pattern to copy |
| `qla_core/rate_dbf_writer.py` | `write_quikissc_csv` / `write_quikuint_csv` already exist |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | **D2 path fix site** |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | Field | QLAdmin target | Transformation | Change this issue? |
|----------------|-------|----------------|----------------|--------------------|
| Rate_Table SL hub | DURATION/VALUE | QuikIssc.SCHG01–14 | Existing loader pivot | **No** (emit only) |
| PDINT/PDINTTBL | CENII A1 tiers | QuikUint.* | Existing loader | **No** (config path only) |
| N/A | N/A | CSV file on disk | Call existing writers from `rate_emit.py` | **Yes** |

### Fields / tables that must remain unchanged

| Target | Touch this issue? |
|--------|-------------------|
| QuikCoi / QuikGcoi / QuikGps / QuikCvs / factor tables | **No** |
| QuikIssc loader key rules (AGE=0, M-only, 8 MPLANs) | **No** |
| QuikUint merge rules | **No** |
| Policy conversion (`quikmstr`, etc.) | **No** |
| Sync_Rulebooks | **No** |

---

## 5. Open Client Questions

None blocking Development for D1/D2.

Soft / parallel (tracked on Issue_ISWL, not this issue):

1. OBQ-3 — Does QLAdmin need explicit Female QuikIssc rows? (Sujitha)  
2. OBQ-6–10 — COI basis, COI/GCOI fleet, GLP, loan credited rate  

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| QuikIssc SCHG | Percent literals to 4 decimals (existing) |
| QuikIssc AGE | `0` all-age (existing) |
| QuikUint rates | Existing loader formatting |
| Empty file guard | After fix: fail validation if QuikIssc rows ≠ 8 when phase6 enabled |

---

## 7. Proposed Surgical Fix Plan

### Fix A — D1 (`qla_core/rate_emit.py`)

In `run_rate_emit`, CSV branch (after QuikUwpo / QuikAint writes, before `_write_csv_manifest`):

```python
if res.quikuint_rows:
    path = os.path.join(csv_dir, "QuikUint.csv")
    n = W.write_quikuint_csv(path, res.quikuint_rows, overwrite=True)
    manifest.append({"kind": "interest", "table": "QuikUint", "path": path, "rows": n})
if res.quikissc_rows:
    path = os.path.join(csv_dir, "QuikIssc.csv")
    n = W.write_quikissc_csv(path, res.quikissc_rows, overwrite=True)
    manifest.append({"kind": "surrender", "table": "QuikIssc", "path": path, "rows": n})
```

Mirror existing DBF branch (~lines 107–114) and R5 CLI `_write_csv_manifest` (~lines 92–101).

**Optional hardening (same issue if Risk agrees):** when `quikissc_enabled` and `len(res.quikissc_rows)==0` after a successful gate, log a hard warning; do **not** invent rows.

### Fix B — D2 (`rate_loader_config.json`)

| Key | From (broken) | To (present) |
|-----|---------------|--------------|
| `psegt_csv` | `...PSEGT_..._20260629.csv` | `...PSEGT_..._20260630.csv` |
| `pdint_extract` | `...PDINT_..._20260629.csv` | `...PDINT_..._20260630.csv` |
| `pdinttbl_extract` | `...PDINTTBL_..._20260629.csv` | `...PDINTTBL_..._20260630.csv` |

Also update `rate_loader_config.example.json` if it still cites 20260629.

### Fix C — Redeliver (post Validation)

1. Re-run rate emit (CSV)  
2. Confirm QuikIssc = 8 rows; QuikUint ≥ 1 row per 8 MPLANs (or documented tier count from Phase5 baseline)  
3. Copy modified rate CSVs to `QLA_Migration/Output/Test_Validation/rates/`  
4. Notify Sujitha  

### APP_VERSION

- If only `qla_core/rate_emit.py` + config: **no** `app.py` bump required (batch already calls `rate_emit.run_rate_emit`).  
- If Development also changes `app.py` logging/UI: bump both `app.py` copies per AGENTS.md.

---

## 8. Validation / Regression Plan (for later stages)

| Check | Pass criteria |
|-------|---------------|
| V-ISSC | `iswl_quikissc_reconcile.py` PASS; 8 plans; SCHG01–14 populated; AGE=0 |
| V-UINT | `iswl_quikuint_reconcile.py` PASS; no `BLOCKER_NO_PDINTTBL` |
| Package | `Output/rates/QuikIssc.csv` and `QuikUint.csv` non-header-only |
| Manifest | `rate_csv_manifest.csv` row counts match files |
| Regression | QuikCoi/Gcoi/Gps/Cvs row counts unchanged vs pre-fix snapshot |
| Partial emit | `V-UINT-PDINT` no longer fires with corrected paths |

---

## 9. Risks / blast radius

| Risk | Mitigation |
|------|------------|
| Overwrite intentional empty QuikIssc | Unlikely — empty was defect; Phase6 evidence is 8 rows |
| Wrong PDINT date file | Use 20260630 (present); document in Implementation Notes |
| Partial emit still hides future path errors | Optional Risk recommendation: do not whitelist UINT/ISSC blockers for silent empty CSV |

---

## 10. Go / No-Go for Dependency Gate

**Go.** All source files for the fix exist; writers already exist; edit sites are known; no client answers required for D1/D2.

**G1:** **PASS**
