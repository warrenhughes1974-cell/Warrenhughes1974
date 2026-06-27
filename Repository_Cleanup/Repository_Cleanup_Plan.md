# Repository Cleanup — Plan

**Generated:** 2026-06-27  
**Phase:** 2 — Plan only (no execution)  
**Prerequisite:** `Repository_Cleanup_Inventory.md`  
**Approval required:** Yes — do not execute Phase 3 until reviewed.

---

## 1. Goals

1. Separate **production engine** files from **validators**, **research**, and **scratch**.
2. Co-locate **issue-specific scripts** with their Issue Log folders.
3. Promote **reusable validators** to `tools/validators/`.
4. Preserve **all issue evidence** and **release documentation**.
5. Avoid breaking **app.py imports**, **batch launcher**, or **report path references**.

---

## 2. Proposed folder structure (target)

```text
tools/
  validators/          # Reusable post-conversion validators
  research/            # (optional) cross-issue research if not issue-bound
  risk_reviews/        # (optional) or keep under Issue_Log_Items/*/scripts/
  investigations/      # Cross-issue one-off utilities
  batch_tests/         # Headless batch runners
  release_tools/       # PS1 sync/validate packaging scripts

Issue_Log_Items/
  Issue_21/
    scripts/
    evidence/
    reports/
  Issue_21M/
    scripts/
    evidence/
    reports/
  Issue_25/
    scripts/
    evidence/
    reports/
  Issue_26/
    scripts/
    evidence/
    reports/

_archive/
  old_research/
  superseded_scripts/
  scratch/

Release_Notes/         # unchanged
Repository_Cleanup/    # this cleanup effort
```

**Production engine (unchanged locations):**

```text
app.py
QLA_Migration/app.py
qla_core/
qladmin_core/
QLA_Migration/Configs/
QLA_Migration/Mapping/
QLA_Migration/Source/
QLA_Migration/Output/
QLA_Migration/run_converter.bat
validate_output.py      # KEEP — app.py imports at repo root
validation/
validation_config/
```

---

## 3. Files to keep in place

| Path | Reason |
|------|--------|
| `app.py`, `QLA_Migration/app.py` | Production engine |
| `qla_core/`, `qladmin_core/` | Production modules |
| `QLA_Migration/Configs/`, `Mapping/`, `Source/`, `Output/` | Runtime paths in UI and scripts |
| `QLA_Migration/run_converter.bat` | Production launcher |
| `validate_output.py` | **Direct import in app.py** (`import validate_output as vo`) |
| `validation/` package | Enterprise validator wrapper |
| `validation_config/` | Referenced by validate_output and engine |
| `Release_Notes/`, `Release_Manifest_v57.34.md` | Release artifacts (path refs updated in Phase 4) |
| `AGENTS.md`, `SANITIZE_GUIDE.md` | Workspace / ops docs |
| `QLA_Migration/RUN_GUIDE.md` | Operational runbook (update script paths only) |
| `claims_analysis/`, `plan_analysis/`, `plan_governance/` | Separate subsystems — out of scope for this cleanup pass |

---

## 4. Files to move

### Phase 3A — Create directories (no file moves yet)

Create empty structure:

```text
tools/validators/
tools/batch_tests/
tools/investigations/
tools/release_tools/
Issue_Log_Items/Issue_21/scripts/
Issue_Log_Items/Issue_21/evidence/
Issue_Log_Items/Issue_21/reports/
Issue_Log_Items/Issue_21M/scripts/
Issue_Log_Items/Issue_21M/evidence/
Issue_Log_Items/Issue_21M/reports/
Issue_Log_Items/Issue_25/scripts/
Issue_Log_Items/Issue_25/reports/
Issue_Log_Items/Issue_26/scripts/
Issue_Log_Items/Issue_26/evidence/
Issue_Log_Items/Issue_26/reports/
_archive/old_research/
_archive/superseded_scripts/
_archive/scratch/
```

### Phase 3B — Reusable validators → `tools/validators/`

| From | To |
|------|-----|
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

**Required code change (path only, not business logic):** Update `PROJECT_ROOT` resolution in each moved script:

```python
# Before (QLA_Migration/_validate_*.py):
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# After (tools/validators/*.py):
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
```

**Backward compatibility (recommended):** Leave thin wrapper stubs at old paths:

```python
# QLA_Migration/_validate_issue21m_quikmemo.py (stub after move)
"""Deprecated path — use tools/validators/validate_issue21m_quikmemo.py"""
import runpy, sys
sys.exit(runpy.run_path("tools/validators/validate_issue21m_quikmemo.py", run_name="__main__") or 0)
```

This avoids breaking historical report commands until Phase 4 reference updates land.

### Phase 3C — Batch tests → `tools/batch_tests/`

| From | To |
|------|-----|
| `QLA_Migration/_run_full_batch_test.py` | `tools/batch_tests/run_full_batch_test.py` |

**Required change:** Replace hardcoded `BASE` with:

```python
BASE = Path(__file__).resolve().parent.parent.parent
MIG = BASE / "QLA_Migration"
```

Leave stub at `QLA_Migration/_run_full_batch_test.py` for backward compatibility.

### Phase 3D — Issue-specific scripts → issue folders

| From | To |
|------|-----|
| `QLA_Migration/_research_issue21m_quikmemo.py` | `Issue_Log_Items/Issue_21M/scripts/research_issue21m_quikmemo.py` |
| `QLA_Migration/_risk_review_issue21m_quikmemo.py` | `Issue_Log_Items/Issue_21M/scripts/risk_review_issue21m_quikmemo.py` |
| `QLA_Migration/_research_issue21k_munit.py` | `Issue_Log_Items/Issue_21/scripts/research_issue21k_munit.py` |
| `QLA_Migration/_risk_review_issue21k_munit.py` | `Issue_Log_Items/Issue_21/scripts/risk_review_issue21k_munit.py` |
| `QLA_Migration/_research_issue26_ppu.py` | `Issue_Log_Items/Issue_26/scripts/research_issue26_ppu.py` |
| `QLA_Migration/_risk_review_issue26_mprem.py` | `Issue_Log_Items/Issue_26/scripts/risk_review_issue26_mprem.py` |
| `QLA_Migration/_investigate_mpolicy_keys.py` | `Issue_Log_Items/Issue_25/scripts/investigate_mpolicy_keys.py` |
| `Issue_Log_Items/Issue_21/reconciliation/build_aba_reconciliation.py` | `Issue_Log_Items/Issue_21/scripts/build_aba_reconciliation.py` |

### Phase 3E — Cross-issue investigations → `tools/investigations/`

| From | To |
|------|-----|
| `QLA_Migration/analyze_data_lineage.py` | `tools/investigations/analyze_data_lineage.py` |

### Phase 3F — Release tools → `tools/release_tools/`

| From | To |
|------|-----|
| `QLA_Migration/Tools/sync_current_to_source.ps1` | `tools/release_tools/sync_current_to_source.ps1` |
| `QLA_Migration/Tools/validate_source_package.ps1` | `tools/release_tools/validate_source_package.ps1` |

### Phase 3G — Issue evidence / reports reorganization (no script logic changes)

| From | To |
|------|-----|
| `Issue_Log_Items/Issue_21M/*.md` | `Issue_Log_Items/Issue_21M/reports/` |
| `Issue_Log_Items/Issue_21M/*.csv`, `*_stdout.txt` | `Issue_Log_Items/Issue_21M/evidence/` |
| `Issue_Log_Items/Issue_26/*.md` | `Issue_Log_Items/Issue_26/reports/` |
| `Issue_Log_Items/Issue_26/*.csv` | `Issue_Log_Items/Issue_26/evidence/` |
| `Issue_Log_Items/Issue_21/Issue_21K_*`, `Issue_21_*Analysis*` etc. | `Issue_Log_Items/Issue_21/reports/` |
| `Issue_Log_Items/Issue_21/reconciliation/*.csv` | `Issue_Log_Items/Issue_21/evidence/` |
| `Issue_Log_Items/Issue_21/*.docx` | `Issue_Log_Items/Issue_21/evidence/` |
| `QLA_Migration/Issue_Log_Items/Issue_25/*.md` | `Issue_Log_Items/Issue_25/reports/` |
| Root `*.docx` (policy screenshots) | `Issue_Log_Items/Issue_21/evidence/` (dedupe first) |

**Tracking sheets:** Keep `Issue_21_Tracking_Sheet.md` and `Issue_Log_Master_Tracking_Sheet.md` at current paths or move to `Issue_Log_Items/` root — **REVIEW** before move (high visibility).

---

## 5. Files to archive

| From | To | Reason |
|------|-----|--------|
| `QLA_Migration/discovery_iswl_analysis.py` | `_archive/old_research/discovery_iswl_analysis.py` | Discovery-only; superseded by ISWL reports |
| `QLA_Migration/ISWL_*.md` | `_archive/old_research/` | Discovery reports |
| `QLA_Migration/ROLLBACK_v57.26_insured_owner.md` | `_archive/superseded_scripts/` | Point-in-time rollback note |
| `QLA_Migration/Bank does not go into quikclid-----.txt` | `_archive/scratch/` | Informal scratch note |
| `Issue_Log_Items/Issue_21/_tmp_docx_extract/` | `_archive/scratch/Issue_21/_tmp_docx_extract/` | Docx extraction temp images |
| Root `*-prem.csv` (11 files) | `_archive/scratch/root_premium_csv/` | Duplicates of `PFSA Rates/` |

---

## 6. Files to delete (explicit temporary only)

| Path | Reason |
|------|--------|
| `Issue_Log_Items/Issue_21/~$0713704C - LifePRO.docx` | Word lock file |
| `Issue_Log_Items/Issue_21/~$0818663C - QLAdmin.docx` | Word lock file |

**No other deletions** in this plan. Root/master CSV duplicates require diff review before delete.

---

## 7. Import and path risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Validators use `parent.parent` for repo root | **High** | Update to `parent.parent.parent` OR add `tools/_repo_root.py` helper |
| `_run_full_batch_test.py` hardcoded Windows path | **High** | Parameterize repo root; stub at old path |
| `app.py` imports `validate_output` at repo root | **Critical** | **Do not move** `validate_output.py` without app import change |
| Issue research scripts write CSV next to script | Medium | Update output paths in scripts (path-only change) |
| Historical markdown cites `QLA_Migration/_validate_*` | Medium | Phase 4 reference updates + optional stubs |
| `run_converter.bat` does not reference `_validate_*` | Low | No bat change needed |
| Git history / commit links to old paths | Low | Accept; add redirect stubs |

---

## 8. Scripts referenced by reports (must update or stub)

| Script | Primary references |
|--------|-------------------|
| `validate_issue21m_quikmemo.py` | `Release_Notes/v57.34_Release_Notes.md`, `Release_Manifest_v57.34.md`, `Issue_21M_*` reports |
| `validate_issue21m_dbf_packaging.py` | Same |
| `validate_issue26_mprem.py` | Release docs, Issue 21M regression, Issue 26 reports |
| `validate_mpolicy_width.py` | Release manifest, Issue 25 report |
| `run_full_batch_test.py` | Master tracking, RUN_GUIDE, Issue 21M validation |
| `research_issue21m_quikmemo.py` | Issue 21M planning report |
| `investigate_mpolicy_keys.py` | Issue 25 investigation report |
| `research_issue21k_munit.py` | Issue 21K planning/intake |
| `risk_review_issue21k_munit.py` | Issue 21K risk report |

**Phase 4 update list:**

- `Release_Notes/v57.34_Release_Notes.md`
- `Release_Manifest_v57.34.md`
- `Issue_Log_Items/Issue_Log_Master_Tracking_Sheet.md`
- `QLA_Migration/RUN_GUIDE.md`
- `AI_Agents/Framework.md`, `Validation_Agent.md`, `Regression_Agent.md`, `Planning_Agent.md`, `Risk_Agent.md`
- `AI_Agents/Templates/*.md`
- Active Issue 21M / 21K / 26 reports (path lines only — do not rewrite evidence tables)

**Do not rewrite:** Validator stdout captures in `Issue_Log_Items/Issue_21M/evidence/` — historical record.

---

## 9. Permanent tools vs issue-only artifacts

| Permanent tool (→ `tools/validators/`) | Issue-only artifact (→ `Issue_Log_Items/*/scripts/`) |
|----------------------------------------|------------------------------------------------------|
| `validate_issue21m_quikmemo.py` | `research_issue21m_quikmemo.py` |
| `validate_issue21m_dbf_packaging.py` | `risk_review_issue21m_quikmemo.py` |
| `validate_issue26_mprem.py` | `research_issue26_ppu.py` |
| `validate_mpolicy_width.py` | `risk_review_issue26_mprem.py` |
| `validate_issue21k_munit.py` | `research_issue21k_munit.py` |
| `validate_issue21k_fleet.py` | `risk_review_issue21k_munit.py` |
| `validate_issue21.py` | `investigate_mpolicy_keys.py` |
| `validate_beneficiary_split.py` | `build_aba_reconciliation.py` |
| `validate_insured_owner_golden.py` | |
| `validate_quikclnt_mclientid.py` | |
| `test_lifepro_source_resolution.py` | |
| `run_full_batch_test.py` (batch_tests) | |
| `analyze_data_lineage.py` (investigations) | |
| **`validate_output.py` — KEEP AT ROOT** | |

---

## 10. Execution order (Phase 3 — after approval)

1. Create target directories.
2. Move issue scripts to `Issue_Log_Items/*/scripts/`; fix `PROJECT_ROOT`.
3. Move validators to `tools/validators/`; fix `PROJECT_ROOT`.
4. Move batch test; fix hardcoded path.
5. Add backward-compat stubs at old `QLA_Migration/_*.py` paths.
6. Reorganize issue evidence/reports into subfolders.
7. Archive scratch and discovery files.
8. Delete Word lock files only.
9. Phase 4 — update path references in active docs.
10. Phase 5 — smoke tests:
    - `python -m py_compile app.py`
    - `python -m py_compile QLA_Migration/app.py`
    - `python tools/validators/validate_mpolicy_width.py` (or via stub)
    - `python -c "import app; import validate_output"`
    - Confirm `run_converter.bat` still launches

---

## 11. Out of scope (this cleanup pass)

- Moving or refactoring `claims_analysis/**` phase runners
- Moving `plan_analysis/**` internal `_*.py` helpers
- Consolidating duplicate root `Master_Crosswalk.csv` (requires diff review)
- Modifying conversion logic, rulebooks, or DBF writers
- Git commit (await separate approval after execution report)

---

## 12. Approval checklist

Before executing Phase 3, confirm:

- [ ] Target folder structure approved
- [ ] Backward-compat stubs at old validator paths — **yes / no**
- [ ] Root premium CSV archive — **yes / no**
- [ ] Delete Word lock files — **yes / no**
- [ ] Move `validate_output.py` — **must remain NO**
- [ ] Reorganize Issue_21M reports into `reports/` subfolder — **yes / no**
- [ ] Dedupe root vs Issue_21 docx copies — **yes / no**

---

*Phase 2 complete. Awaiting review before Phase 3 execution and `Repository_Cleanup_Execution_Report.md`.*
