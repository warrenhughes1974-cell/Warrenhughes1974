# Stage 2A Dry-Run Migration Report

**Generated:** 2026-07-12T14:50:48Z  
**Source:** `C:\Users\warren\Documents\GitHub\Warrenhughes1974\CFIC_Rates`  
**Destination:** `C:\Users\warren\Documents\GitHub\Warrenhughes1974\Citizens_Product_Rate_Conversion`  
**Stage:** 2A — Dry-run only (no files copied)

## Summary

| Metric | Value |
|--------|------:|
| Total source files | 503 |
| Total source directories | 181 |
| Total source bytes | 3,209,385,809 |
| Files that would copy (Stage 2B) | 379 |
| Files that would not copy | 124 |
| Estimated Stage 2B copy size | 2,914,153,468 bytes (2.91 GB) |
| COPY_APPROVED = YES | **0** (all NO) |
| Source assets copied in Stage 2A | **0** |

## Counts by Extension

| Extension | Count |
|-----------|------:|
| `.csv` | 180 |
| `.pdf` | 96 |
| `.png` | 73 |
| `.txt` | 59 |
| `.py` | 22 |
| `.zip` | 22 |
| `.md` | 19 |
| `.pt1` | 10 |
| `.pyc` | 7 |
| `.cpy` | 4 |
| `.dbf` | 3 |
| `.xlsx` | 3 |
| `.mdb` | 2 |
| `(no ext)` | 1 |
| `.dat` | 1 |
| `.json` | 1 |

## Counts by Category

| Category | Count |
|----------|------:|
| Generated output | 246 |
| Temporary files | 122 |
| Archive files | 31 |
| Documentation | 21 |
| Scripts | 21 |
| CSV files | 18 |
| Rate files | 15 |
| Validation reports | 12 |
| PDFs | 7 |
| Database extracts | 4 |
| Mapping files | 2 |
| Source data files | 2 |
| Configuration files | 1 |
| Crosswalks | 1 |

## Counts by Migration Action

| Action | Count |
|--------|------:|
| COPY | 245 |
| COPY_TO_ARCHIVE | 125 |
| EXCLUDE_GENERATED | 114 |
| EXCLUDE_TEMPORARY | 8 |
| COPY_AND_RENAME | 6 |
| COPY_TO_QUARANTINE | 3 |
| DO_NOT_MIGRATE | 1 |
| DUPLICATE_REVIEW | 1 |

## Counts by Classification Confidence

| Confidence | Count |
|------------|------:|
| HIGH | 321 |
| MEDIUM | 182 |

## Proposed Destination Buckets

| Bucket | File count |
|--------|----------:|
| Original source (`source/`) | 37 |
| Working mappings (`mappings/working/`) | 3 |
| Archive | 254 |
| Quarantine | 3 |
| Exclusion (generated/temp/do not migrate) | 123 |
| Review required / unknown purpose | 0 |

## Duplicate Groups

- SHA-256 duplicate groups: **5**
- See `duplicate_file_report.csv`

## Collision Risks

- Case-collision rows: **0**
- Filename-collision rows: **152**
- High path-length risk: **0**
- See `path_collision_report.csv`

## Sensitive-Data Risks

- Files flagged: **2**
- See `sensitive_data_review.csv`

## Hardcoded Paths

- Files with absolute path references: **2**
- See `hardcoded_path_report.csv`

## CSO References

- Files with CSO reference indicators: **14**
- Note: Mostly documentation pattern references; not CSO plan mappings.

## qla_core Dependencies

- Files referencing qla_core: **11**
- See `enterprise_dependency_report.csv`

## QLA_Migration References

- Files referencing QLA_Migration: **13**

## Unknown Authority / Purpose

- Unknown authority: **0**
- Review-required or unknown action: **0**

## Largest Proposed Copy Items

| Size (bytes) | Relative path | Action |
|-------------:|---------------|--------|
| 278,330,287 | `CFIC_Cash_Values/MultipleCashValueFiles.zip` | COPY_TO_QUARANTINE |
| 248,861,719 | `CFIC_Cash_Values/PLP_CV.zip` | COPY |
| 238,171,788 | `CFIC_Cash_Values/RW8_CV.zip` | COPY |
| 228,707,250 | `CFIC_Cash_Values/ABMS_CV.zip` | COPY |
| 227,656,627 | `CFIC_Cash_Values/ABFS_CV.zip` | COPY |
| 198,471,450 | `CFIC_Cash_Values/P7MS_CV.zip` | COPY |
| 197,924,925 | `CFIC_Cash_Values/P7FS_CV.zip` | COPY |
| 171,168,193 | `CFIC_Cash_Values/ABMN_CV.zip` | COPY |
| 170,804,111 | `CFIC_Cash_Values/ABFN_CV.zip` | COPY |
| 156,726,624 | `CFIC_Cash_Values/802M_CV.zip` | COPY |
| 140,924,178 | `CFIC_Cash_Values/P7FN_CV.zip` | COPY |
| 138,585,368 | `CFIC_Cash_Values/P7MN_CV.zip` | COPY |
| 115,058,169 | `CFIC_Cash_Values/R28G_CV.zip` | COPY |
| 102,441,586 | `CFIC_Cash_Values/R68G_CV.zip` | COPY |
| 87,356,407 | `CFIC_Cash_Values/PLP6_CV.zip` | COPY |

## Migration Blockers (Stage 2B)

1. `COPY_APPROVED = NO` on all 503 inventory rows
2. Duplicate groups require review before copy
3. Quarantine items (3) require authority decision
4. Working mappings not approved for `mappings/approved/`
5. Enterprise Engine path not retargeted (`qla_core` dependency)
6. OBQ business gates from legacy issues remain open

## Open Decisions

- 308 vs 301 plan count reconciliation
- Source authority for legacy SourceData dump
- `cifianu1.dbf` scope
- Cash-value ZIP storage (Git LFS vs external)
- OCR/green-sheet path: archive-only vs continued investment

## Stage 2B Copy Projection

| Action group | Count |
|--------------|------:|
| Would COPY (all copy actions) | 379 |
| Would EXCLUDE / DO_NOT_MIGRATE | 123 |
| Would REVIEW / DUPLICATE_REVIEW / UNKNOWN | 1 |

## Confirmations

- [x] `COPY_APPROVED` is **NO** for every row in `migration_inventory.csv`
- [x] No source assets were copied during Stage 2A
- [x] CFIC_Rates was read only

## Source Integrity (Post-Scan)

- Source unchanged: **True**
- Files added during Stage 2A: 0
- Files missing after Stage 2A: 0
- mtime changes: 0
