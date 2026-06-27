# Issue 21K — Client UAT / Production Migration Gate Report

**Issue:** 21K — PUA Amount Precision (QLAdmin MUNIT N(*,3) → N(*,5))  
**Framework stage:** Client UAT / Production Migration Gate  
**Generated:** 2026-06-27  
**Prior stage:** Validation Agent — **CONDITIONAL PASS** (repo-level)  
**Code changes this gate:** None (converter untouched)

---

## Executive Summary

| Gate | Status |
|------|--------|
| Production migration (`C:\QLAdmin\Data`) | **NOT EXECUTED** — path not present in validation environment |
| Six-table schema widen | **NOT EXECUTED** (client production) |
| QUIKRIDR production reload | **NOT EXECUTED** (client production) |
| QLAdmin UI UAT (010448806C) | **NOT EXECUTED** — requires live QLAdmin |
| Reindex / search regression | **NOT EXECUTED** |

### **Verdict: HOLD — Client UAT not performed**

### **Closure Agent authorized:** **NO**

Issue 21K **remains open**. Repo-level validation and staging artifacts are ready for client deploy, but **full closure blockers (§ Closure Blockers) are not cleared** in this environment.

---

## 1. Production Migration Results

### 1.1 Environment check (2026-06-27)

| Path | Result |
|------|--------|
| `C:\QLAdmin\Data` (client production) | **Not found** on validation workstation |
| Staging package (repo) | Present — see §1.3 |

**Command not run against production:**

```text
python qladmin_core/issue21k_units_migration.py --migrate-dir "C:\QLAdmin\Data"
```

**Prerequisite not verified:** production DBF backup before migration.

### 1.2 Required six-table migration (client production)

| Table | Expected MUNIT after | Production migrate | Notes |
|-------|----------------------|:------------------:|-------|
| QUIKPOLX | N(11,5) | **PENDING** | Client `--migrate-dir` |
| QUIKRIDR | N(10,5) | **PENDING** | Reload after widen |
| QUIKRVAL | N(10,5) | **PENDING** | Client `--migrate-dir` |
| QUIKVALF | N(10,5) | **PENDING** | Client `--migrate-dir` |
| QUIKVERR | N(7,5) | **PENDING** | Client `--migrate-dir` |
| QUIKTVAL | N(10,5) | **PENDING** | Client `--migrate-dir` |

**Client record when complete:**

| Table | Backup path | Migrate status | Rows | MUNIT spec verified |
|-------|-------------|:--------------:|-----:|---------------------|
| QUIKPOLX | | ☐ | | ☐ N(11,5) |
| QUIKRIDR | | ☐ | | ☐ N(10,5) |
| QUIKRVAL | | ☐ | | ☐ N(10,5) |
| QUIKVALF | | ☐ | | ☐ N(10,5) |
| QUIKVERR | | ☐ | | ☐ N(7,5) |
| QUIKTVAL | | ☐ | | ☐ N(10,5) |

### 1.3 Staging / repo migration (reference only — not production)

Prior Validation Agent run against **staging** path `QLA_Migration/Output/qladmin_issue21k`:

| Table | Result |
|-------|--------|
| QUIKPOLX | SKIPPED — no source DBF |
| QUIKRIDR | **MIGRATED** (7,002 rows; backup `QUIKRIDR_before_3dp.DBF`) |
| QUIKRVAL | SKIPPED |
| QUIKVALF | SKIPPED |
| QUIKVERR | SKIPPED |
| QUIKTVAL | SKIPPED |

**Deploy candidate (staging reload, not client production):**

| Artifact | Path |
|----------|------|
| QUIKRIDR.DBF (N10,5) | `QLA_Migration/Output/qladmin_issue21k/QUIKRIDR.DBF` |
| Manifest | `QLA_Migration/Output/qladmin_issue21k/issue21k_schema_migration_manifest.json` |
| Source CSV | `QLA_Migration/Output/quikridr.csv` |

---

## 2. Tables Migrated

**Production:** **0 / 6** tables migrated in client environment (gate not run).

**Staging:** **1 / 6** (QUIKRIDR only) — sufficient for repo validation, **insufficient for issue closure**.

---

## 3. Reindex Results

| Check | Production | Staging |
|-------|:----------:|:-------:|
| `QuikRdr.ntx` (QUIKRIDR) rebuilt | **PENDING** | **PENDING** |
| Valuation table indexes (RVAL/VALF/TVAL/VERR) | **PENDING** | N/A |
| Reindex completes without error | **PENDING** | **PENDING** |
| Policy search by number (010448806C) | **PENDING** | **PENDING** |

**Client sign-off:** _____________________ Date: ___________

---

## 4. Policy 010448806C — UI Validation

**Primary acceptance criterion:** Accumulated PUA face **$5,752.96** (LifePRO source).

| Check | Expected | Production UAT | Result |
|-------|----------|:--------------:|:------:|
| Stored MUNIT (DBF) | **5.75296** | Not tested in QLAdmin | **PENDING** |
| Stored MVPU | **1000.00** | Not tested in QLAdmin | **PENDING** |
| Calculated face (MUNIT × MVPU) | **$5,752.96** | Not tested in QLAdmin | **PENDING** |
| **Coverage tab — PUA face display** | **$5,752.96** | Not tested | **PENDING** |
| Prior incorrect display | $5,752.00 | — | Regression target |
| Rider / phase 2 row (`1708PA`) | Visible, correct | Not tested | **PENDING** |
| Runtime errors on open policy | None | Not tested | **PENDING** |

**Repo staging DBF (storage layer only — not QLAdmin UI):**

| Field | Staging value | Match? |
|-------|-------------:|:------:|
| MUNIT | 5.75296 | **PASS** |
| MVPU | 1000.00 | **PASS** |
| Face | $5,752.96 | **PASS** |

Storage is correct in staging; **QLAdmin display confirmation still required**.

---

## 5. Report / Valuation Validation

| Screen / function | Truncation check | Production UAT |
|-------------------|------------------|:--------------:|
| Policy inquiry / Coverage | Must show $5,752.96 | **PENDING** |
| Reports listing PUA / face amounts | No 3 dp unit truncate | **PENDING** |
| Valuation extract (QUIKRVAL / QUIKVALF / QUIKTVAL) | MUNIT N(*,5) in use | **PENDING** |
| Valuation error (QUIKVERR) | MUNIT N(7,5) in use | **PENDING** |
| Dividend / PUA accumulation screens | Cents preserved | **PENDING** |

**Sample policies for extended UAT (recommended):**

| Policy | Phase | Plan | Expected face |
|--------|------:|------|-------------:|
| 010448806C | 2 | 1708PA | $5,752.96 |
| 010615191C | 2 | 1708PA | $3,745.99 |
| 010510671C | 1 | 2665ST | $6,034.59 |

---

## 6. Defects

| ID | Layer | Description | Severity | Owner | Status |
|----|-------|-------------|----------|-------|--------|
| — | Environment | Client production path `C:\QLAdmin\Data` not available for automated gate | Info | Client / IT | **Open** |
| — | Migration | Five of six production tables not migrated in client environment | Blocker | Client / New Era | **Open** |
| — | UAT | QLAdmin UI not exercised for 010448806C | Blocker | Client UAT | **Open** |

**No new conversion or schema defects identified in repo retest.**

---

## 7. Closure Blocker Status

| # | Blocker | Cleared? |
|---|---------|:--------:|
| 1 | All six production tables at approved MUNIT precision | **NO** |
| 2 | QUIKRIDR reloaded with five-decimal MUNIT | **NO** (production) |
| 3 | QLAdmin UI shows **$5,752.96** for **010448806C** | **NO** |
| 4 | Reports/valuation do not re-truncate | **NO** |
| 5 | Reindex and search pass | **NO** |

---

## 8. PASS / FAIL Recommendation

| Scope | Recommendation |
|-------|----------------|
| **Client production migration + UAT** | **FAIL / HOLD** — not executed |
| **Repo staging package (QUIKRIDR N10,5)** | **PASS** — ready to deploy to client UAT environment |
| **Issue 21K closure** | **FAIL / HOLD** |

### If client UAT passes (future update to this report)

Set all §4–§5 checks to PASS, six-table migration complete, reindex signed off → change verdict to **PASS** and authorize **Closure Agent**.

### If client UAT fails (routing)

| Failure layer | Return to |
|---------------|-----------|
| Stored MUNIT still 5.752 in DBF after reload | Client load / migration tooling — verify `--migrate-dir` + reload |
| DBF stores 5.75296 but UI shows $5,752.00 | New Era / QLAdmin display formatter |
| Valuation tables still N(*,3) | Complete remaining five-table migration |
| Conversion CSV wrong (unlikely) | Development Agent (conversion) — only if repo regression |

---

## 9. Closure Agent Authorization

| Question | Answer |
|----------|--------|
| **Closure Agent authorized?** | **NO** |
| **Reason** | Client production migration and QLAdmin UI UAT not completed |
| **Next action** | Client executes § Required Client Migration and § Required QLAdmin UAT; update this report with results |

---

## 10. Client Execution Checklist

1. **Backup** all six production DBFs (+ index sidecars).
2. Run:
   ```powershell
   cd C:\Users\warren\Documents\GitHub\Warrenhughes1974
   python qladmin_core\issue21k_units_migration.py --migrate-dir "C:\QLAdmin\Data" --out-dir "C:\QLAdmin\Staging\issue21k"
   ```
3. Verify manifest: six tables **MIGRATED** (not SKIPPED).
4. Deploy / reload **QUIKRIDR** from `QLA_Migration\Output\quikridr.csv` or staged `QUIKRIDR.DBF`.
5. **Reindex** QUIKRIDR (`QuikRdr.ntx`) and valuation tables as applicable.
6. Open policy **010448806C** in QLAdmin — confirm PUA face **$5,752.96**.
7. Spot-check reports and valuation for truncation.
8. Update this report §1–§5 with PASS/FAIL and sign-off.
9. If all PASS → run **Closure Agent**.

---

## Related Artifacts

| Document | Path |
|----------|------|
| Validation report | `Issue_Log_Items/Issue_21/Issue_21K_Validation_Report.md` |
| Development report | `Issue_Log_Items/Issue_21/Issue_21K_Development_Report.md` |
| Validation evidence | `Issue_Log_Items/Issue_21/Issue_21K_Validation_Evidence.json` |
| Migration CLI | `qladmin_core/issue21k_units_migration.py` |

---

**Stop point:** Client UAT / Production Migration Gate documented. **Closure Agent not authorized** until client completes checklist and this report is updated to **PASS**.
