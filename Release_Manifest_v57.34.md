# Release Manifest — v57.34

| Field | Value |
|-------|-------|
| **Version** | v57.34 |
| **Release date** | 2026-06-27 |
| **Git commit (working tree at cut)** | `e009fed740451c6ddbee35c6ab0fd2bf829a9764` |
| **Prior version** | v57.33 |

---

## Issue Numbers Included

| Issue | Version introduced | In v57.34 release |
|-------|-------------------|-------------------|
| #25 MPOLICY padding | v57.30 | Yes |
| #26 MPREM mapping | v57.31 | Yes |
| #21B Bill Day | v57.22 | Yes |
| #21C Policy Fees | v57.22 | Yes |
| #21H Banking ABA | v57.22 | Yes (ABA only) |
| #21M QUIKMEMO pipeline | v57.32–33 | Yes |
| #21M-FU MEMOKEY merge | v57.34 | Yes (primary) |

**Excluded from release closure:** #21K (Client UAT HOLD), #21A, #21D–21G, #21I, #21J, #21H target-field, deferred claims (147).

---

## Files Modified (Engine & Core)

### Version bump

| File | Change |
|------|--------|
| `app.py` | v57.34 header, GUI title, banner, startup log |
| `QLA_Migration/app.py` | Same as root |

### Issue #21M / #21M-FU

| File | Change |
|------|--------|
| `qla_core/quikmemo_converter.py` | PNOTE+PENSE merge; `_merge_segments_by_memokey()` |
| `qla_core/quikmemo_dbf_generator.py` | DBF writer; MEMOKEY padding preserved |
| `qla_core/run_logging.py` | Output hygiene skip for `*_uat_dbf/` |
| `app.py` / `QLA_Migration/app.py` | quikmemo batch integration |

### Issue #25 / #26

| File | Change |
|------|--------|
| `qla_core/normalize_utils.py` | `format_qladmin_mpolicy()` 10-char left-pad |
| `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv` | MPREM rulebook mapping |
| `app.py` / `QLA_Migration/app.py` | MPREM fallback logic |

### Issue #21B / #21C / #21H

| File | Change |
|------|--------|
| `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv` | Bill day, fees, banking rules |
| `app.py` / `QLA_Migration/app.py` | MANNLFEE, ABA recovery |

### Validators (new / updated)

| File | Purpose |
|------|---------|
| `QLA_Migration/_validate_issue21m_quikmemo.py` | 21M-FU population + integrity |
| `QLA_Migration/_validate_issue21m_dbf_packaging.py` | DBF/DBT co-location |
| `QLA_Migration/_validate_issue26_mprem.py` | MPREM mapping |
| `QLA_Migration/_validate_mpolicy_width.py` | MPOLICY width (#25) |

### Companion tooling (21K — not engine closure)

| File | Purpose |
|------|---------|
| `qladmin_core/qladmin_units_schema.py` | Six-table MUNIT N(*,5) specs |
| `qladmin_core/qladmin_dbf_layout.py` | DBF widen/migrate helpers |
| `qladmin_core/quikridr_dbf_writer.py` | CSV → QUIKRIDR.DBF N(10,5) |
| `qladmin_core/issue21k_units_migration.py` | CLI migration |
| `QLA_Migration/_validate_issue21k_munit.py` | Staging validation |
| `QLA_Migration/_validate_issue21k_fleet.py` | Fleet MUNIT validation |

### Issue log artifacts (documentation)

| Path | Purpose |
|------|---------|
| `Issue_Log_Items/Issue_21M/` | 21M / 21M-FU stage reports |
| `Issue_Log_Items/Issue_26/` | MPREM research & risk |
| `Issue_Log_Items/Issue_21/Issue_21K_*.md` | 21K framework reports (open) |
| `Release_Notes/v57.34_Release_Notes.md` | This release |

---

## New Artifacts (Deploy Outputs)

| Artifact | Location | Rows / size |
|----------|----------|-------------|
| quikmemo.csv | `QLA_Migration/Output/quikmemo.csv` | 4,380 rows |
| quikmemo.dbf | `QLA_Migration/Output/quikmemo_uat_dbf/quikmemo.dbf` | 4,380 rows, 92,078 bytes |
| quikmemo.dbt | `QLA_Migration/Output/quikmemo_uat_dbf/quikmemo.dbt` | 5,486,148 bytes |
| Integrity samples | `QLA_Migration/Output/_issue21m_fu_integrity_samples.csv` | Audit |

---

## Database / Schema Changes

| Component | Change | Notes |
|-----------|--------|-------|
| **Conversion engine** | No QLAdmin schema change | CSV/DBF emit only |
| **QUIKMEMO** | New table population | 4,380 rows; memo field via DBT |
| **21K (client-side)** | MUNIT N(10,3) → N(10,5) on 6 tables | **Not executed** — client production migration required |

Tables affected by 21K migration (when client executes):

- QUIKPOLX, QUIKRIDR, QUIKPLAN, QUIKPRMH, QUIKDVDP, QUIKLOAN

---

## Deployment Sequence

1. **Backup** current QLAdmin data directory and conversion Output folder.
2. **Deploy** engine v57.34 (`app.py`, `qla_core/*`, rulebooks).
3. **Run** full batch migration (`run_converter.bat` or `_run_full_batch_test.py`).
4. **Validate** with four regression scripts (all PASS at cut).
5. **Deploy QUIKMEMO** — copy `quikmemo_uat_dbf/quikmemo.dbf` + `quikmemo.dbt` **together** to QLAdmin data path.
6. **Do not** copy `Reports/quikmemo.dbt` (orphan stale sidecar).
7. **Client UAT** — Memo tab on `010335038C`; bill day / fees / ABA on trace policies.
8. **Optional (21K)** — run `qladmin_core/issue21k_units_migration.py --migrate-dir` then `--reload-quikridr` on client environment.

---

## Rollback Considerations

| Scenario | Rollback action |
|----------|-----------------|
| Engine regression | Restore prior `app.py` v57.33 + `qla_core/` snapshot; re-run batch |
| QUIKMEMO display issues | Restore prior quikmemo.dbf/dbt pair (pre-FU: 29,279 rows) or remove table |
| MPREM / MPOLICY | Revert to v57.29 engine + rulebooks; re-run batch |
| 21K migration (if executed) | Restore pre-migration DBF backups; MUNIT widen is one-way without backup |

**Safe rollback point:** Git commit at v57.33 tag/state before v57.34 deploy.

---

## Regression Validation (2026-06-27)

| Validator | Result |
|-----------|--------|
| `_validate_issue21m_quikmemo.py` | **PASS** |
| `_validate_issue21m_dbf_packaging.py` | **PASS** |
| `_validate_issue26_mprem.py` | **PASS** |
| `_validate_mpolicy_width.py` | **PASS** |

Row counts unchanged: quikmstr 5,083 · quikridr 7,002 · quikprmh 205,577 · quikplan 141 · quikclid 46,753 · quikclnt 13,846.

---

## Files Explicitly Excluded from Release Bundle

Research artifacts, scratch outputs, and temporary files **not** part of production deploy:

- Root and `Issue_Log_Items/` `*.docx` policy screenshots
- `Issue_Log_Items/Issue_21/_tmp_docx_extract/`
- `Issue_Log_Items/Issue_21/~$*.docx` (Word lock files)
- `claims_analysis/` governance CSV refreshes (analytical outputs, not engine)
- `plan_analysis/`, `plan_governance/` dry-run artifacts
- Orphan `Reports/quikmemo.dbt`

---

*v57.34 Release Manifest — prepared 2026-06-27.*
