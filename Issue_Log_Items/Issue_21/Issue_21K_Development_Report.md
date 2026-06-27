# Issue 21K — QLAdmin Core Development Report

**Issue:** 21K — PUA Amount Precision (MUNIT / units field)  
**Framework stage:** Development Agent (Stage 5)  
**Scope:** **QLAdmin DBF schema only** — no LifePRO conversion engine changes  
**Generated:** 2026-06-24  
**Status:** **Development complete** — ready for Validation Agent (QLAdmin UI UAT pending)

---

## 1. Summary

Implemented QLAdmin Core tooling to widen the **MUNIT (units)** field from **`N(*,3)` → `N(*,5)`** across the six authorized tables, reload **QUIKRIDR** from the latest conversion CSV, and validate stored precision for policy **010448806C**.

**Conversion engine (`app.py`, rulebooks): unchanged** — confirmed 0 row delta on `quikridr.csv`.

---

## 2. Tables Modified (Schema Definition)

| Table | MUNIT before (Help) | MUNIT after | Notes |
|-------|---------------------|-------------|-------|
| **QUIKPOLX** | N(11,3) | **N(11,5)** | Help width 11 (not 10) |
| **QUIKRIDR** | N(10,3) | **N(10,5)** | **Reloaded** — 7,002 rows |
| **QUIKRVAL** | N(10,3) | **N(10,5)** | Migrate via `--migrate-dir` |
| **QUIKVALF** | N(10,3) | **N(10,5)** | Migrate via `--migrate-dir` |
| **QUIKVERR** | N(7,3) | **N(7,5)** | Help width 7 |
| **QUIKTVAL** | N(10,3) | **N(10,5)** | Migrate via `--migrate-dir` |

**Not modified (per scope):** `MSAVEUNIT` remains N(10,3); all non-MUNIT fields unchanged.

Schema source: `docs/claims_conversion_reference/QLAdmin_Help.pdf` §7.187–7.234.

---

## 3. Schema Before / After — QUIKRIDR (Executed)

**Before:** `MUNIT N(10,3)`  
**After:** `MUNIT N(10,5)`

Full structure after reload (excerpt):

```text
...
MAGE N(3,0)
MUNIT N(10,5)    ← Issue 21K change
MVPU N(8,2)
MPREM N(10,2)
...
MSAVEUNIT N(10,3)   ← unchanged
```

Manifest: `QLA_Migration/Output/qladmin_issue21k/issue21k_schema_migration_manifest.json`

---

## 4. Reload Confirmation — QUIKRIDR

| Item | Value |
|------|-------|
| Source CSV | `QLA_Migration/Output/quikridr.csv` |
| Output DBF | `QLA_Migration/Output/qladmin_issue21k/QUIKRIDR.DBF` |
| Rows loaded | **7,002** |
| Command | `python qladmin_core/issue21k_units_migration.py --reload-quikridr` |

### Policy 010448806C (PUA trace)

| Field | Stored value | Expected |
|-------|-------------:|----------|
| MPOLICY | 010448806C | ✓ |
| MPHASE | 2 | ✓ |
| MPLAN | 1708PA | ✓ |
| **MUNIT** | **5.75296** | **5.75296** ✓ |
| MVPU | 1000.00 | ✓ |
| **Face (MUNIT × MVPU)** | **$5,752.96** | **$5,752.96** ✓ |

---

## 5. UAT Results (Development-Stage)

| Check | Result | Notes |
|-------|:------:|-------|
| CSV `MUNIT` precision preserved | **PASS** | `_validate_issue21k_munit.py` |
| DBF `MUNIT N(10,5)` structure | **PASS** | Structure list includes `MUNIT N(10,5)` |
| 010448806C stored precision | **PASS** | 5.75296 |
| 010448806C face calculation | **PASS** | $5,752.96 |
| Sample PUA policies (615191C, 367438C) | **PASS** | Face matches trace CSV |
| Row count | **PASS** | 7,002 |
| **QLAdmin UI display** | **PENDING** | Validation Agent / client UAT |
| **Report / valuation screens** | **PENDING** | Requires live QLAdmin environment |
| **Remaining 5 tables in production** | **PENDING** | Run `--migrate-dir` on client data path |

---

## 6. Regression Summary

| Regression check | Result |
|------------------|--------|
| Existing 3-decimal values unchanged after widen-only migration | **PASS** (synthetic N10,3 → N10,5 copy; 5.778 → 5.778) |
| `MUNIT × MVPU` five-decimal precision | **PASS** (5.75296 × 1000 = 5752.96) |
| No DBF corruption / readable structure | **PASS** |
| Field order matches QLAdmin Help §7.203 | **PASS** |
| Conversion CSV unchanged | **PASS** (no engine edits) |
| Issue #25 MPOLICY padding | **PASS** (preserved on reload) |
| Issue #26 MPREM | **PASS** (untouched) |
| Index key definition | **Documented** — `QuikRdr.ntx` on MPOLICY+MPHASE; client reindex after deploy |

---

## 7. Files Added (QLAdmin Core)

| File | Purpose |
|------|---------|
| `qladmin_core/qladmin_units_schema.py` | Six-table MUNIT before/after; QUIKRIDR Help layout |
| `qladmin_core/qladmin_dbf_layout.py` | DBF spec helpers; widen-units migration |
| `qladmin_core/quikridr_dbf_writer.py` | CSV → QUIKRIDR.DBF with N(10,5) MUNIT |
| `qladmin_core/issue21k_units_migration.py` | CLI: reload + optional `--migrate-dir` |
| `QLA_Migration/_validate_issue21k_munit.py` | CSV + DBF precision validation |

**Not modified:** `app.py`, `QLA_Migration/app.py`, rulebooks, conversion outputs (except new `qladmin_issue21k/` package).

---

## 8. Client Deployment Steps

1. **Backup** production DBFs for all six tables.
2. **Widen schema** on QUIKPOLX, QUIKRIDR, QUIKRVAL, QUIKVALF, QUIKVERR, QUIKTVAL:
   ```powershell
   python qladmin_core/issue21k_units_migration.py --migrate-dir "C:\Path\To\QLAdmin\Data" --out-dir "C:\Path\To\Staging\issue21k"
   ```
3. **Reload QUIKRIDR** from latest conversion CSV (or deploy staged `QUIKRIDR.DBF`):
   ```powershell
   python qladmin_core/issue21k_units_migration.py --reload-quikridr
   ```
4. **Reindex** affected tables (`QuikRdr.ntx`, etc.) in QLAdmin.
5. **UAT** policy **010448806C** — PUA face **$5,752.96** on Coverage tab.

---

## 9. GO / NO-GO Recommendation

| Layer | Recommendation |
|-------|----------------|
| **QLAdmin Core implementation (this repo)** | **GO** — schema tooling + QUIKRIDR reload validated |
| **Full six-table production migration** | **CONDITIONAL GO** — execute `--migrate-dir` + reindex on client environment |
| **Issue 21K closure** | **HOLD** until Validation Agent confirms QLAdmin **display** and valuation UAT |

---

## 10. Stop Point

Development Agent complete. **Do not mark Issue 21K closed** until Validation Agent runs QLAdmin UI UAT.

**Next:** Validation Agent — `_validate_issue21k_munit.py` + client QLAdmin screen verification.
