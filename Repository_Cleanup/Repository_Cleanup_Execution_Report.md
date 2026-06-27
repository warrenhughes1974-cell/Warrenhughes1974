# Repository Cleanup — Execution Report

**Executed:** 2026-06-27  
**Phases completed:** 3 (moves/stubs), 4 (reference updates), 5 (smoke tests)  
**Git commit:** Not created (awaiting review)

---

## 1. Summary

Repository cleanup reorganized **21 Python scripts** from `QLA_Migration/` into `tools/` and `Issue_Log_Items/*/scripts/`, created **20 backward-compatibility stubs** at legacy paths, reorganized **Issue #21M / #21 / #26** reports and evidence, and archived scratch duplicates. **No conversion logic, rulebooks, engine behavior, or release version changes were made.**

---

## 2. Files moved

### Validators → `tools/validators/`

| New path |
|----------|
| `tools/validators/validate_issue21m_quikmemo.py` |
| `tools/validators/validate_issue21m_dbf_packaging.py` |
| `tools/validators/validate_issue26_mprem.py` |
| `tools/validators/validate_mpolicy_width.py` |
| `tools/validators/validate_issue21k_munit.py` |
| `tools/validators/validate_issue21k_fleet.py` |
| `tools/validators/validate_issue21.py` |
| `tools/validators/validate_beneficiary_split.py` |
| `tools/validators/validate_insured_owner_golden.py` |
| `tools/validators/validate_quikclnt_mclientid.py` |
| `tools/validators/test_lifepro_source_resolution.py` |

### Batch / investigations / release tools

| New path |
|----------|
| `tools/batch_tests/run_full_batch_test.py` |
| `tools/investigations/analyze_data_lineage.py` |
| `tools/release_tools/sync_current_to_source.ps1` |
| `tools/release_tools/validate_source_package.ps1` |

### Issue-specific scripts

| New path |
|----------|
| `Issue_Log_Items/Issue_21M/scripts/research_issue21m_quikmemo.py` |
| `Issue_Log_Items/Issue_21M/scripts/risk_review_issue21m_quikmemo.py` |
| `Issue_Log_Items/Issue_21/scripts/research_issue21k_munit.py` |
| `Issue_Log_Items/Issue_21/scripts/risk_review_issue21k_munit.py` |
| `Issue_Log_Items/Issue_21/scripts/build_aba_reconciliation.py` |
| `Issue_Log_Items/Issue_26/scripts/research_issue26_ppu.py` |
| `Issue_Log_Items/Issue_26/scripts/risk_review_issue26_mprem.py` |
| `Issue_Log_Items/Issue_25/scripts/investigate_mpolicy_keys.py` |

### Issue reports → `reports/`

| Destination | Count |
|-------------|------:|
| `Issue_Log_Items/Issue_21M/reports/` | 16 markdown reports |
| `Issue_Log_Items/Issue_21/reports/` | 14 reports (21K + analysis) |
| `Issue_Log_Items/Issue_26/reports/` | 3 reports |
| `Issue_Log_Items/Issue_25/reports/MPOLICY_Key_Investigation_Report.md` | 1 |

### Issue evidence → `evidence/`

| Destination | Count |
|-------------|------:|
| `Issue_Log_Items/Issue_21M/evidence/` | 24 CSV/TXT files |
| `Issue_Log_Items/Issue_26/evidence/` | 2 CSV files |
| `Issue_Log_Items/Issue_21/evidence/` | 3 reconciliation CSVs + 9 docx + 1 xlsx + additional docx |

---

## 3. Files archived

| Archive path | Contents |
|--------------|----------|
| `_archive/old_research/discovery_iswl_analysis.py` | ISWL discovery script |
| `_archive/old_research/ISWL_Discovery_Summary.md` | ISWL summary |
| `_archive/old_research/ISWL_Source_Data_Discovery_Report.md` | ISWL report |
| `_archive/superseded_scripts/ROLLBACK_v57.26_insured_owner.md` | Rollback note |
| `_archive/scratch/QLA_Migration/Bank_does_not_go_into_quikclid.txt` | Scratch note |
| `_archive/scratch/Issue_21/_tmp_docx_extract/` | 43 PNG extraction temps |
| `_archive/scratch/root_premium_csv/` | 12 root duplicate premium CSVs |
| `_archive/scratch/root_docx_duplicates/` | 9 root policy docx duplicates |

---

## 4. Files deleted

| Path | Reason |
|------|--------|
| `Issue_Log_Items/Issue_21/~$0713704C - LifePRO.docx` | Word lock file |
| `Issue_Log_Items/Issue_21/~$0818663C - QLAdmin.docx` | Word lock file |
| `~$0391876C - LifePRO.docx` (root) | Word lock file |
| Duplicate reports at `Issue_Log_Items/Issue_21/` root (3 md) | Copies already in `reports/` |
| `Issue_Log_Items/Issue_21/reconciliation/` (empty after move) | Superseded by `scripts/` + `evidence/` |

**No client evidence `.docx` files were deleted.**

---

## 5. Stubs created (legacy `QLA_Migration/_*.py`)

Each stub delegates to the new canonical path via `subprocess` (preserves argv).

| Stub | Target |
|------|--------|
| `QLA_Migration/_validate_issue21m_quikmemo.py` | `tools/validators/validate_issue21m_quikmemo.py` |
| `QLA_Migration/_validate_issue21m_dbf_packaging.py` | `tools/validators/validate_issue21m_dbf_packaging.py` |
| `QLA_Migration/_validate_issue26_mprem.py` | `tools/validators/validate_issue26_mprem.py` |
| `QLA_Migration/_validate_mpolicy_width.py` | `tools/validators/validate_mpolicy_width.py` |
| `QLA_Migration/_validate_issue21k_munit.py` | `tools/validators/validate_issue21k_munit.py` |
| `QLA_Migration/_validate_issue21k_fleet.py` | `tools/validators/validate_issue21k_fleet.py` |
| `QLA_Migration/_validate_issue21.py` | `tools/validators/validate_issue21.py` |
| `QLA_Migration/_validate_beneficiary_split.py` | `tools/validators/validate_beneficiary_split.py` |
| `QLA_Migration/_validate_insured_owner_golden.py` | `tools/validators/validate_insured_owner_golden.py` |
| `QLA_Migration/_validate_quikclnt_mclientid.py` | `tools/validators/validate_quikclnt_mclientid.py` |
| `QLA_Migration/_test_lifepro_source_resolution.py` | `tools/validators/test_lifepro_source_resolution.py` |
| `QLA_Migration/_run_full_batch_test.py` | `tools/batch_tests/run_full_batch_test.py` |
| `QLA_Migration/analyze_data_lineage.py` | `tools/investigations/analyze_data_lineage.py` |
| `QLA_Migration/_research_issue21m_quikmemo.py` | `Issue_Log_Items/Issue_21M/scripts/...` |
| `QLA_Migration/_risk_review_issue21m_quikmemo.py` | `Issue_Log_Items/Issue_21M/scripts/...` |
| `QLA_Migration/_research_issue21k_munit.py` | `Issue_Log_Items/Issue_21/scripts/...` |
| `QLA_Migration/_risk_review_issue21k_munit.py` | `Issue_Log_Items/Issue_21/scripts/...` |
| `QLA_Migration/_research_issue26_ppu.py` | `Issue_Log_Items/Issue_26/scripts/...` |
| `QLA_Migration/_risk_review_issue26_mprem.py` | `Issue_Log_Items/Issue_26/scripts/...` |
| `QLA_Migration/_investigate_mpolicy_keys.py` | `Issue_Log_Items/Issue_25/scripts/...` |

---

## 6. Files left in place (production)

| Path | Reason |
|------|--------|
| `app.py`, `QLA_Migration/app.py` | Production engine |
| `validate_output.py` | Runtime import by app |
| `qla_core/`, `qladmin_core/` | Production modules |
| `QLA_Migration/run_converter.bat` | Production launcher |
| `QLA_Migration/Configs/`, `Mapping/`, `Source/`, `Output/` | Runtime paths |
| `validation/`, `validation_config/` | Validation framework |
| `claims_analysis/`, `plan_analysis/` | Out of scope |

---

## 7. References updated

| File | Change |
|------|--------|
| `Release_Notes/v57.34_Release_Notes.md` | Added canonical `tools/validators/` paths; stubs noted |
| `Release_Manifest_v57.34.md` | Validator table + batch test path + regression table |
| `Issue_Log_Items/Issue_Log_Master_Tracking_Sheet.md` | Batch test path |
| `AI_Agents/Framework.md` | Script location pattern |
| `Issue_Log_Items/Issue_21/scripts/research_issue21k_munit.py` | Output path → `reports/` |

**Not updated (historical evidence preserved):** Issue 21M validator stdout captures, archived issue report body text, AI_Agents templates (still show legacy paths; stubs remain valid).

---

## 8. Smoke test results

| Test | Result |
|------|--------|
| `python -m py_compile app.py` | **PASS** |
| `python -m py_compile QLA_Migration/app.py` | **PASS** |
| `import app; import validate_output` | **PASS** |
| `python QLA_Migration/_validate_issue21m_quikmemo.py` (stub) | **PASS** |
| `python QLA_Migration/_validate_issue21m_dbf_packaging.py` (stub) | **PASS** |
| `python QLA_Migration/_validate_issue26_mprem.py` (stub) | **PASS** |
| `python QLA_Migration/_validate_mpolicy_width.py` (stub) | **PASS** |
| `python QLA_Migration/_validate_issue21k_munit.py` (stub) | **FAIL** — missing staging DBF (environment; not cleanup regression) |

---

## 9. Warnings / failures

| Item | Severity | Detail |
|------|----------|--------|
| Locked docx during move | Warning | `Issue_Log_Items/Issue_21/010713704C - LifePRO.docx` — duplicate kept at issue root; canonical copy in `evidence/` |
| Locked docx during move | Warning | `Issue_Log_Items/Issue_21/010818663C - QLAdmin.docx` — copied to `evidence/`; source copy may remain until file unlocked |
| Root `010391876C - LifePRO.docx` | Warning | Copied to archive; source locked — manual delete when Word releases lock |
| `#21K` validator | Info | FAIL expected without `Output/qladmin_issue21k/QUIKRIDR.DBF` — not caused by cleanup |
| Partial first run | Info | `_execute_phase3.py` interrupted on locked file; completed via `_complete_phase3.py` |

---

## 10. Remaining manual review items

1. **Remove duplicate** `Issue_Log_Items/Issue_21/010713704C - LifePRO.docx` after closing Word/lock.
2. **Remove duplicate** `Issue_Log_Items/Issue_21/010818663C - QLAdmin.docx` if still present after unlock.
3. **Remove locked root** `010391876C - LifePRO.docx` if still present (archive copy exists).
4. **Update AI_Agents templates** (`Templates/*.md`) to reference `tools/validators/` when convenient.
5. **Optional:** Update historical Issue 21M report path lines (reports moved to `reports/` subfolder).
6. **Review** root `Master_Crosswalk.csv`, `Sync_Rulebook_*.csv`, `Value_Map.json` vs `QLA_Migration/` copies (out of scope — not moved).
7. **Git commit** cleanup when approved.

---

## 11. Executor artifacts

| File | Purpose |
|------|---------|
| `Repository_Cleanup/_execute_phase3.py` | Primary move executor |
| `Repository_Cleanup/_complete_phase3.py` | Completion pass (locked files) |
| `Repository_Cleanup/_phase3_complete_log.txt` | Move log |

---

*Phase 3–5 complete. No git commit created.*
