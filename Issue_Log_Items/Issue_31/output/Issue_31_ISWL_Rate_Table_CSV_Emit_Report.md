# Issue #31 — ISWL Rate Table CSV Emit Report

**Date:** 2026-06-30  
**Scope:** PR-1 through PR-4 test-ready CSV package  
**Output location:** `QLA_Migration/Output/rates/`

---

## A. Emit Command Used

```text
python plan_analysis/phase_r5_rate_loader/rate_loader_emit.py --csv-only
```

**Working directory:** repository root  
**Exit code:** 0  
**Gate:** `blocker_count=0` — emit proceeded

---

## B. Config Confirmation

### `rate_loader_config.json` (validator authority)

| Phase | Block | Status |
|-------|-------|--------|
| Phase 1 | `iswl_phase1` | Present (`quikcvs_vargp: 2`) |
| Phase 2 | `iswl_phase2` | `quikgps_enabled: true` |
| Phase 3 | `iswl_phase3` | `quikcoi_enabled: true` |
| Phase 4 | `iswl_phase4` | `quikgcoi_enabled: true` |

### Emit script config

`rate_loader_emit.py` reads **`rate_loader_config.example.json`** by default (hard-coded `CONFIG` constant). That file is **aligned** with `rate_loader_config.json` for all four ISWL phases — same paths, same phase enable flags, same MPLAN allowlists.

### Output path

Confirmed: **`QLA_Migration/Output/rates/`** (default `--csv-dir`)

### Not sourced from archive

Emit writes fresh pipeline output. **Not** copied from `QLA_Migration/Archive/rates/`.

| File | Archive (stale) | Emitted (current) |
|------|----------------:|------------------:|
| QuikGps.csv | 11,947 | **12,567** |
| QuikCoi.csv | — | **792** (new) |
| QuikGcoi.csv | — | **198** (new) |
| QuikCvs.csv | 25,717 | **25,717** (same total; ISWL from Rate_Table) |

---

## C. CSV Files Created

Required files — **all present:**

| File | Path |
|------|------|
| QuikCvs.csv | `QLA_Migration/Output/rates/QuikCvs.csv` |
| QuikGps.csv | `QLA_Migration/Output/rates/QuikGps.csv` |
| QuikCoi.csv | `QLA_Migration/Output/rates/QuikCoi.csv` |
| QuikGcoi.csv | `QLA_Migration/Output/rates/QuikGcoi.csv` |

Additional companion CSVs in same folder (key/member tables for CV/GPS/DB families only): `QuikPlCv.csv`, `QuikPlGp.csv`, etc. — see `rate_csv_manifest.csv`.

**Not valid deliverables:** `QuikPlCoi.csv`, `QuikPlGcoi.csv` — quarantined 2026-07-02 (see `output/quarantine_invalid_artifacts/`). COI/GCOI use factor tables `QuikCoi.csv` / `QuikGcoi.csv` only per QLAdmin Help §7.73 / §7.93.

---

## C1. Output Naming Correction (2026-07-02)

| Item | Detail |
|------|--------|
| **Defect** | Pipeline emitted invalid key-table files `QuikPlCoi.csv`, `QuikPlGcoi.csv` |
| **Cause** | `KEY_TABLE` in `rate_dbf_schema.py` mapped QuikCoi/QuikGcoi to QuikPl* companions (CV/GPS pattern incorrectly generalized) |
| **Fix** | Removed COI/GCOI from `KEY_TABLE`; skip key-row emit for those factor tables |
| **Validation** | V-COI-08 / V-GCOI-05 + `validate_coi_gcoi_output_filenames()` |
| **Row counts** | Unchanged — QuikCoi 792, QuikGcoi 198 |

---

## D. Row Counts

| CSV | Total rows | ISWL rows |
|-----|----------:|----------:|
| QuikCvs.csv | 25,717 | 7,789 |
| QuikGps.csv | 12,567 | 948 |
| QuikCoi.csv | 792 | 792 |
| QuikGcoi.csv | 198 | 198 |

Manifest: `QLA_Migration/Output/rates/rate_csv_manifest.csv`

---

## E. ISWL Content Confirmation

### QuikCvs — 8/8 ISWL MPLANs

| MPLAN | Rows |
|-------|-----:|
| 1658C1 | 1,947 |
| 1658CS | 979 |
| 1659C2 | 1,045 |
| 1659CR | 1,045 |
| 1659CS | 997 |
| 1659SR | 1,047 |
| 1669SR | 264 |
| 1679CS | 465 |

### QuikGps — 4 ISWL BP MPLANs

| MPLAN | Rows |
|-------|-----:|
| 1658CS | 294 |
| 1659CS | 152 |
| 1669SR | 172 |
| 1679CS | 330 |

### QuikCoi — 2 ISWL U6 MPLANs (792 total)

| MPLAN | Rows |
|-------|-----:|
| 1658CS | 396 |
| 1679CS | 396 |

### QuikGcoi — 1 ISWL U5 MPLAN (198 total)

| MPLAN | Rows |
|-------|-----:|
| 1679CS | 198 |

All expected ISWL MPLANs present; no missing plans.

---

## F. Validator Results (post-emit)

| Validator | Result | Blockers | emit_ready |
|-----------|--------|----------|------------|
| `iswl_quikcvs_reconcile.py` | **PASS** | 0 | true |
| `iswl_quikgps_reconcile.py` | **PASS** | 0 | true |
| `iswl_quikcoi_reconcile.py` | **PASS** | 0 | true |
| `iswl_quikgcoi_reconcile.py` | **PASS** | 0 | true |

- Non-ISWL regression: **clean** (all phases)
- Phase 1 through Phase 4: **all PASS**

---

## G. Warnings / Issues

Non-blocking emit warnings (from `emit_summary.json`):

| ID | Count | Severity | Notes |
|----|------:|----------|-------|
| V10 | 260 | WARNING | Precision reduced (CHAR field formatting) |
| V15 | 116 | WARNING | Deferred actuarial assumption dependencies |
| AGE_CAPPED_TO_99 | 312 | WARNING | Audited AGE cap rule |
| AGE_CAP_COLLISION_RESOLVED | 23 | WARNING | Cap vs genuine AGE 99 collisions resolved |

**Blockers:** 0  
**V03 duplicate-cell collisions:** 0

**Note:** Emit script uses `rate_loader_config.example.json`; validators use `rate_loader_config.json`. Both are ISWL-aligned today; consider syncing `CONFIG` constant to `rate_loader_config.json` in a future maintenance pass (out of scope for this emit).

**Not in this package:** QUIKUINT, QUIKISSC, expenses, DBF emit, `app.py` integration.

---

## H. Final Recommendation

### **READY FOR TESTING**

The ISWL-enabled CSV test package is emitted to `QLA_Migration/Output/rates/` with all four required factor tables, expected row counts, confirmed ISWL MPLAN coverage, and clean post-emit validation. Warnings are audited and non-blocking.
