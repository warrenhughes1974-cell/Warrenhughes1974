# Stage 2B Controlled Copy Migration Report

**Project:** Citizens Product and Rate Conversion  
**Date:** 2026-07-12  
**Stage:** 2B — Controlled Classified Copy Migration  
**Source (read-only):** `C:\Users\warren\Documents\GitHub\Warrenhughes1974\CFIC_Rates`  
**Destination:** `C:\Users\warren\Documents\GitHub\Warrenhughes1974\Citizens_Product_Rate_Conversion`

---

## 1. Executive Summary

Stage 2B completed classified copy migration under governance of `manifests/migration_inventory.csv` and approved Decisions 2B-01 through 2B-12. **380 files** were approved and copied or verified with matching SHA-256 hashes. **123 files** were excluded (temporary, generated, or duplicate-without-audit-value). **CFIC_Rates** post-scan integrity: **PASS** (zero source modifications). Git was not initialized. No conversion code was changed or executed.

**Stage verdict: PASS WITH REVIEW ITEMS**

Review items: 123 excluded files remain unmigrated by design; source authority and plan/rate manifests still unset; engine path retargeting deferred.

---

## 2. Stage Verdict

**PASS WITH REVIEW ITEMS**

| PASS criterion | Result |
|----------------|--------|
| No source modifications | PASS |
| No hash failures | PASS (380/380 verified) |
| No unsafe overwrite | PASS (0 collisions) |
| No unapproved copies | PASS |
| Sensitive files only in quarantine | PASS |
| No actual CSO artifact copied | PASS |
| No Enterprise Engine source copied | PASS |

---

## 3. Source Preflight Result

**File:** `manifests/stage2b_preflight.json`

| Check | Result |
|-------|--------|
| CFIC_Rates exists and readable | PASS |
| Destination exists with Stage 2A infrastructure | PASS |
| migration_inventory.csv — 503 rows | PASS |
| All source paths under CFIC_Rates | PASS |
| COPY_APPROVED all NO at Stage 2B entry | PASS |
| Stage 2A post snapshot present | PASS |
| Disk space (~24 GB free) | PASS |

---

## 4. Total Inventory Rows

**503**

---

## 5. Total Approved Rows

**380** (`COPY_APPROVED = YES`)

---

## 6. Active-Source Files Copied

**235** files to active controlled folders (excluding archive and quarantine)

Includes:
- `source/original/` — DBFs, cash-value ZIPs, Access archives, PDFs, extracts
- `mappings/working/` — crosswalk and requirements catalog
- `staging/` — reserve grids, plans, PDF/green-sheet pilots
- `discovery/`, `docs/`, `conversion/orchestration/`, `issues/`, `tools/`

---

## 7. Working-Mapping Files Copied

**3** files under `mappings/working/`:
- `Citizens_Plan_Crosswalk.xlsx` (renamed from Crosswak)
- `Citizens_Plan_Rate_Requirements_Catalog.xlsx`
- `business_inputs/cfic_rate_key_assumptions.csv`

`mappings/approved/` contains **no** migrated mapping files (headers only from Stage 2A).

---

## 8. Documentation Files Copied

**8+** under `docs/runbooks/`, `docs/source_layout/`, and issue documentation under `issues/closed/legacy_*`

---

## 9. Conversion/Orchestration Files Copied

**5** Python modules under `conversion/orchestration/` (legacy CFIC packaging scripts; `qla_core` imports **not** retargeted)

---

## 10. Validation-Evidence Files Copied

**8** files under `validation/rate_validation/` including legacy evidence and parity CSVs

---

## 11. Draft-Output Files Copied

**10** Quik* CSV files under `output/csv/draft_pre_migration/` with README warning (Decision 2B-09)

---

## 12. Archive Files Copied

**140** files under `archive/legacy_cfic_rates/` including:
- `SourceData_11-18-2024/` (Decision 2B-07 — authority HISTORICAL_PENDING_REVIEW)
- OCR extracts, green-sheet pilot, dev sample paths
- Legacy issue OCR artifacts

---

## 13. Quarantine Files Copied

**5** files:

| File | Destination | Result |
|------|-------------|--------|
| `docs/cifianu1.dbf` | `quarantine/sensitive_review/` | COPIED_TO_SENSITIVE_QUARANTINE |
| `extracted/AgentName.csv` | `quarantine/sensitive_review/` | COPIED_TO_SENSITIVE_QUARANTINE |
| `CFIC_Cash_Values/MultipleCashValueFiles.zip` | `quarantine/duplicate_review/` | COPIED_TO_QUARANTINE |
| `extracted/CFIProposalMakerRev2.mdb` | `quarantine/duplicate_review/` | COPIED_TO_QUARANTINE |
| `Issue_Log/.../cfic_issue03_p7mn_validation.csv` | `quarantine/duplicate_review/` | COPIED_TO_QUARANTINE |

---

## 14. Excluded Temporary/Generated Files

**123** files not copied:

| Reason | Count |
|--------|------:|
| EXCLUDE_GENERATED (dev PNGs, OCR renders, caches) | 114 |
| EXCLUDE_TEMPORARY (`__pycache__`, `.pyc`, Excel lock) | 8 |
| DUPLICATE_EXCLUDED (root `CFIProposalMaker.zip`) | 1 |

Excel lock `~$Citizens_Plan_Crosswak.xlsx` excluded per Decision 2B-04.

---

## 15. Duplicate Canonical Selections

| Group | Canonical | Reason |
|-------|-----------|--------|
| DUP-0002 | `source/CFIProposalMaker.zip` | Authoritative `source/` over root duplicate |
| DUP-0003 | `source/CFIProposalMakerRev2.mdb` | Canonical in `source/original/access/`; extracted copy in quarantine |
| DUP-0004 | `validation/cfic_issue03_p7mn_validation.csv` | Active validation path; Issue_Log copy to duplicate_review |
| DUP-0005 | Both PT1 files | Identical content; distinct archive paths preserved |
| DUP-0001 | None copied | Both dev/sample PDFs EXCLUDE_GENERATED |

---

## 16. Duplicate Exclusions

- Root `CFIProposalMaker.zip` — DO_NOT_MIGRATE (canonical in `source/`)
- Dev/sample/OCR PNG and PDF scratch — EXCLUDE_GENERATED (114 files)

---

## 17. Files Remaining Under Review

**0** — all rows resolved to approved or excluded status.

---

## 18. Blocked Files

**0**

---

## 19. Copy Failures

**0** — all 380 approved files: `COPY_VERIFICATION_STATUS = VERIFIED`

---

## 20. Hash-Verification Results

| Metric | Value |
|--------|------:|
| Approved copies | 380 |
| Hash verified | 380 |
| Hash failures | 0 |
| Destination collisions | 0 |

**Report:** `reports/migration/Stage2B_Copy_Verification_Report.csv`

---

## 21. Destination Collisions

**0** — no destination file existed with different hash; no overwrites.

---

## 22. Sensitive-Data Handling Results

Per Decision 2B-02:
- `cifianu1.dbf` → `quarantine/sensitive_review/` only
- `AgentName.csv` → `quarantine/sensitive_review/` only
- No sensitive file placed in `source/original/` or active folders

---

## 23. qla_core Dependency Findings

- **11** legacy scripts reference `qla_core` (documented in `enterprise_dependency_report.csv` from Stage 2A)
- **No** `qla_core` modules copied into Citizens
- Imports **not** retargeted during Stage 2B
- Scripts **not** executed

---

## 24. CSO-Reference Findings

- CSO references appear only in comments/documentation/packaging-pattern language within copied historical files
- **No** actual CSO mapping, plan code, source data, configuration, or validation artifact discovered or copied
- **0** CSO migration blockers

---

## 25. Source-Integrity Comparison

**File:** `manifests/stage2b_post_source_snapshot.json`

| Metric | Delta |
|--------|------:|
| Files added | 0 |
| Files removed | 0 |
| mtime changes | 0 |
| Total bytes delta | 0 |
| **Integrity** | **PASS** |

---

## 26. Destination-Structure Audit

**File:** `reports/migration/Stage2B_Destination_Structure_Audit.csv`

**0 structural violations** detected:
- No Quik output in `source/original/`
- No populated `mappings/approved/`
- No `qla_core` in destination
- No source binaries in `conversion/`
- No Excel lock file copied
- No nested Git repository

---

## 27. Total Bytes Copied

**2,915,996,668 bytes** (~2.72 GiB) across 380 approved files

---

## 28. Git Not Initialized

Confirmed: `.git` does not exist in `Citizens_Product_Rate_Conversion`. `.gitignore` updated to exclude large cash-value ZIPs pending LFS/external-store decision (Decision 2B-01).

---

## 29. No Conversion Code Changed

Only migration utility (`tools/migration/run_stage2b_migration.py`) added. Legacy orchestration scripts copied as-is; no import retargeting.

---

## 30. No Conversion Executed

No packaging, validation, or QLAdmin publish scripts were run.

---

## 31. Recommended Next Stage

**Stage 3 — Source Inventory and Discovery**

1. Populate `plan_manifest.csv` from tracker (308 plans)
2. Populate `rate_manifest.csv` from requirements catalog
3. Complete `SOURCE_AUTHORITY.md` approvals via DECISION_LOG
4. Data profiling of copied DBFs and staging grids
5. Engine version pin in `config/engine_boundary/`
6. Git initialization (separate gated stage)

---

## 32. Open Decisions

| Item | Status |
|------|--------|
| 308 vs 301 plan reconciliation | Open |
| SourceData archive authority | HISTORICAL_PENDING_REVIEW |
| `cifianu1.dbf` life-rate scope | Quarantined — open |
| Cash-value ZIP Git strategy | Local copy approved; LFS/external TBD |
| OBQ-1/OBQ-2 rate-key assumptions | Open |
| Engine integration model | Documented only |
| Draft Quik output approval | Not production-ready |

---

## Artifacts Produced

| Artifact | Path |
|----------|------|
| Updated inventory | `manifests/migration_inventory.csv` |
| Source manifest | `manifests/source_manifest.csv` (380 rows) |
| Preflight | `manifests/stage2b_preflight.json` |
| Post source snapshot | `manifests/stage2b_post_source_snapshot.json` |
| Copy approval report | `reports/migration/Stage2B_Copy_Approval_Report.md` |
| Copy verification | `reports/migration/Stage2B_Copy_Verification_Report.csv` |
| Destination audit | `reports/migration/Stage2B_Destination_Structure_Audit.csv` |
| README warnings | `archive/legacy_cfic_rates/`, `quarantine/`, `output/csv/draft_pre_migration/` |

---

*Stage 2B execution complete — 2026-07-12*
