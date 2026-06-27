# Issue 21K — PUA Amount Precision — Validation Report

**Issue:** 21K — QLAdmin Core MUNIT precision  
**Framework stage:** Validation Agent (Stage 6)  
**Generated:** 2026-06-24  
**Scope:** QLAdmin Core only — **no LifePRO conversion engine changes**  
**Evidence:** `Issue_Log_Items/Issue_21/Issue_21K_Validation_Evidence.json`

---

## Executive Verdict

| Layer | Result |
|-------|--------|
| Schema registry (6 tables) | **PASS** |
| QUIKRIDR physical DBF schema + reload | **PASS** |
| Precision + fleet (CSV ↔ DBF) | **PASS** |
| QLAdmin application UAT | **PENDING** (not available in repo) |
| Production migration (6 tables) | **PARTIAL** (1/6 DBF in workspace) |

### **Overall: CONDITIONAL PASS**

**Repo-level QLAdmin Core validation passes.** Regression may proceed on the **QUIKRIDR N(10,5) reload package** only.

**Full Issue 21K closure remains blocked** until:

1. Client runs `--migrate-dir` on production data for **QUIKPOLX, QUIKRVAL, QUIKVALF, QUIKVERR, QUIKTVAL**
2. QLAdmin **UI UAT** confirms display/report/valuation precision (policy **010448806C** minimum)

---

## Commands Run

```powershell
python QLA_Migration\_validate_issue21k_munit.py
python QLA_Migration\_validate_issue21k_fleet.py
python qladmin_core\issue21k_units_migration.py --migrate-dir "QLA_Migration\Output\qladmin_issue21k"
```

| Script | Exit code |
|--------|:---------:|
| `_validate_issue21k_munit.py` | **0** |
| `_validate_issue21k_fleet.py` | **0** |

---

## 1. Schema Validation

### 1.1 Approved precision registry (all six tables)

| Table | Expected MUNIT | Registry | Physical DBF in repo |
|-------|----------------|:--------:|:--------------------:|
| QUIKPOLX | **N(11,5)** | **PASS** | Not present — migrate at deploy |
| QUIKRIDR | **N(10,5)** | **PASS** | **PASS** — verified in structure |
| QUIKRVAL | **N(10,5)** | **PASS** | Not present |
| QUIKVALF | **N(10,5)** | **PASS** | Not present |
| QUIKVERR | **N(7,5)** | **PASS** | Not present |
| QUIKTVAL | **N(10,5)** | **PASS** | Not present |

Source: `qladmin_core/qladmin_units_schema.py`, manifest `QLA_Migration/Output/qladmin_issue21k/issue21k_schema_migration_manifest.json`

### 1.2 QUIKRIDR physical structure (executed)

Verified in `QUIKRIDR.DBF`:

```text
MUNIT N(10,5)
```

**Field order:** **PASS** — 40 fields match QLAdmin Help §7.203 layout (`field_order_match: true`).

**Non-MUNIT fields unchanged:** **PASS** — e.g. `MSAVEUNIT N(10,3)`, `MVPU N(8,2)`, `MPREM N(10,2)`.

**Conversion engine:** **PASS** — `app.py` / rulebooks contain no Issue 21K edits.

---

## 2. Reload Validation

| Check | Expected | Actual | Result |
|-------|----------|--------|:------:|
| Reload completed | Yes | `--reload-quikridr` output present | **PASS** |
| Source CSV | `quikridr.csv` | 7,002 rows | **PASS** |
| Output DBF | `qladmin_issue21k/QUIKRIDR.DBF` | 7,002 rows | **PASS** |
| Records lost | 0 | CSV 7002 = DBF 7002 | **PASS** |
| Duplicate keys `(MPOLICY, MPHASE)` | 0 | CSV 0 / DBF 0 | **PASS** |
| DBF readable / no corruption | Yes | Full fleet read + append test OK | **PASS** |

---

## 3. Precision Validation

### 3.1 Primary example — 010448806C (PUA)

| Field | Expected | Stored (DBF) | Result |
|-------|----------|-------------:|:------:|
| MPOLICY | 010448806C | 010448806C | **PASS** |
| MPHASE | 2 | 2 | **PASS** |
| MPLAN | 1708PA | 1708PA | **PASS** |
| **MUNIT** | **5.75296** | **5.75296** | **PASS** |
| **MVPU** | **1000.00** | **1000.00** | **PASS** |
| **Face** | **$5,752.96** | **$5,752.96** | **PASS** |
| Truncation to 3 dp | Must not occur | 5.75296 preserved | **PASS** |

### 3.2 Additional sampled policies

| Policy | Phase | Plan | MUNIT | Face | Result |
|--------|------:|------|------:|-----:|:------:|
| 010615191C | 2 | 1708PA | 3.74599 | $3,745.99 | **PASS** |
| 010367438C | 2 | 1708PA | 2.46499 | $2,464.99 | **PASS** |
| 010510671C | 1 | 2665ST | 1.15296 | $6,034.59 | **PASS** |

---

## 4. Fleet Validation

| Metric | Expected | Actual | Result |
|--------|----------|--------|:------:|
| Sub-mill MUNIT rows preserved (CSV → DBF) | 1,068 | **1,068 / 1,068** | **PASS** |
| Fractional-cent face rows correct | 1,070 | **1,070 / 1,070** | **PASS** |
| MUNIT mismatch rows | 0 | **0** | **PASS** |
| MVPU mismatch rows | 0 | **0** | **PASS** |
| Rows avoiding ≥$0.01 loss vs N(10,3) truncate | 1,067 | **1,067** | **PASS** |

No precision loss introduced during CSV → DBF reload.

---

## 5. QLAdmin Application Validation

| Screen / function | Result | Notes |
|-------------------|:------:|-------|
| Coverage tab (PUA face) | **PENDING** | Requires live QLAdmin + deployed DBF |
| Rider screen | **PENDING** | Same |
| Policy inquiry | **PENDING** | Same |
| Reports | **PENDING** | Same |
| Valuation screens | **PENDING** | QUIKRVAL/QUIKVALF/QUIKTVAL not in repo |
| Error screens (QUIKVERR) | **PENDING** | Not in repo |
| Display truncation check | **PENDING** | Storage validated; UI not testable here |
| Runtime errors | **PENDING** | Client UAT |

**Not a validation failure of Development** — environment limitation. Client must confirm **$5,752.96** on Coverage tab for **010448806C** after deploy.

---

## 6. Regression Validation

| Check | Result | Evidence |
|-------|:------:|----------|
| Existing 3-decimal values unchanged | **PASS** | Rows like `5.77800` round-trip unchanged |
| `MUNIT × MVPU` calculations | **PASS** | 1,070 fractional-cent faces |
| DBF structure / field order | **PASS** | Help layout match |
| Import path (CSV → DBF writer) | **PASS** | 0 mismatches |
| Duplicate-key integrity | **PASS** | 0 duplicates |
| Issue #25 MPOLICY padding | **PASS** | Preserved on reload |
| Issue #26 MPREM | **PASS** | Untouched (conversion scope) |
| Reindex process | **PENDING** | Client executes `QuikRdr.ntx` after deploy |
| Search functionality | **PENDING** | QLAdmin UAT |

---

## 7. Production Migration Validation

Executed:

```text
python qladmin_core/issue21k_units_migration.py --migrate-dir "QLA_Migration/Output/qladmin_issue21k"
```

| Table | Result |
|-------|--------|
| QUIKPOLX | **SKIPPED** — source DBF not in workspace |
| QUIKRIDR | **MIGRATED** — widen-units copy succeeded (7,002 rows) |
| QUIKRVAL | **SKIPPED** |
| QUIKVALF | **SKIPPED** |
| QUIKVERR | **SKIPPED** |
| QUIKTVAL | **SKIPPED** |

Post-migration fleet validation: **PASS** (re-run confirmed).

**Client action:** Run `--migrate-dir` against production QLAdmin data directory for remaining five tables; reindex; re-validate.

---

## 8. Artifacts

| Artifact | Path |
|----------|------|
| Reloaded DBF | `QLA_Migration/Output/qladmin_issue21k/QUIKRIDR.DBF` |
| Migration manifest | `QLA_Migration/Output/qladmin_issue21k/issue21k_schema_migration_manifest.json` |
| Validation evidence (JSON) | `Issue_Log_Items/Issue_21/Issue_21K_Validation_Evidence.json` |
| Trace sample | `Issue_Log_Items/Issue_21/Issue_21K_MUNIT_Precision_Trace.csv` |

---

## 9. PASS / FAIL Recommendation

| Gate | Status |
|------|--------|
| **QLAdmin Core technical validation** | **PASS** |
| **Regression & Deployment (QUIKRIDR package)** | **GO** — conditional on client deploy process |
| **Issue 21K full closure** | **HOLD** — QLAdmin UI UAT + 5-table production migration pending |

### Return-to-Development triggers

**None** — no defects found in repo validation.

---

## 10. Stop Point

Validation Agent complete for **in-repo / QUIKRIDR scope**.

**Do not treat Issue 21K as fully closed** until client QLAdmin UAT passes.

**Next stage:** Regression Agent may validate **QUIKRIDR deploy package** integrity; full Regression & Deployment waits on client application sign-off per §5 and §7.
