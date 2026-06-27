# Repository Cleanup — Inventory

**Generated:** 2026-06-27  
**Phase:** 1 — Inventory only (no moves executed)  
**Scope:** Research scripts, validators, investigations, batch tests, scratch/temp files, and related documentation in repo root and `QLA_Migration/`.

---

## Classification legend

| Code | Classification |
|------|----------------|
| **PE** | Production engine file |
| **VAL** | Validator |
| **RES** | Issue-specific research script |
| **RISK** | Risk / simulation script |
| **INV** | One-off investigation script |
| **REL** | Release artifact |
| **DOC** | Documentation |
| **TMP** | Temporary / scratch |
| **UNK** | Unknown — requires review |

## Recommendation legend

| Rec | Meaning |
|-----|---------|
| **KEEP** | Leave in current location |
| **MOVE** | Relocate per proposed structure |
| **ARCHIVE** | Move to `_archive/` |
| **REVIEW** | Manual decision before action |
| **DELETE** | Only if clearly ephemeral (listed explicitly in plan) |

---

## A. Production engine — keep in place

These are **not** cleanup targets. Listed for boundary clarity.

| Path | Class | Issue | Rec | Notes |
|------|-------|-------|-----|-------|
| `app.py` | PE | — | KEEP | Root conversion engine v57.34 |
| `QLA_Migration/app.py` | PE | — | KEEP | Migration bundle engine |
| `qla_core/` | PE | — | KEEP | Core conversion modules |
| `qladmin_core/` | PE | 21K | KEEP | QLAdmin-side migration tooling (companion) |
| `QLA_Migration/Configs/` | PE | — | KEEP | Rulebooks |
| `QLA_Migration/Mapping/` | PE | — | KEEP | Crosswalk / translations |
| `QLA_Migration/Source/` | PE | — | KEEP | LifePRO extracts |
| `QLA_Migration/Output/` | PE | — | KEEP | Conversion output (runtime) |
| `QLA_Migration/run_converter.bat` | PE | — | KEEP | Production launcher |
| `validation_config/` | PE | — | KEEP | Schema manifest + validation config |
| `claims_analysis/config/` | PE | — | KEEP | Claims orchestration rules (referenced by app) |

---

## B. QLA_Migration — scripts and utilities

### B.1 Validators (`_validate_*.py`)

| Path | Class | Issue | Rec | Proposed destination |
|------|-------|-------|-----|----------------------|
| `QLA_Migration/_validate_issue21m_quikmemo.py` | VAL | 21M, 21M-FU | MOVE | `tools/validators/validate_issue21m_quikmemo.py` |
| `QLA_Migration/_validate_issue21m_dbf_packaging.py` | VAL | 21M | MOVE | `tools/validators/validate_issue21m_dbf_packaging.py` |
| `QLA_Migration/_validate_issue26_mprem.py` | VAL | 26 | MOVE | `tools/validators/validate_issue26_mprem.py` |
| `QLA_Migration/_validate_mpolicy_width.py` | VAL | 25 | MOVE | `tools/validators/validate_mpolicy_width.py` |
| `QLA_Migration/_validate_issue21k_munit.py` | VAL | 21K | MOVE | `tools/validators/validate_issue21k_munit.py` |
| `QLA_Migration/_validate_issue21k_fleet.py` | VAL | 21K | MOVE | `tools/validators/validate_issue21k_fleet.py` |
| `QLA_Migration/_validate_issue21.py` | VAL | 21B/C/H | MOVE | `tools/validators/validate_issue21.py` |
| `QLA_Migration/_validate_beneficiary_split.py` | VAL | 21I | MOVE | `tools/validators/validate_beneficiary_split.py` |
| `QLA_Migration/_validate_insured_owner_golden.py` | VAL | — | MOVE | `tools/validators/validate_insured_owner_golden.py` |
| `QLA_Migration/_validate_quikclnt_mclientid.py` | VAL | — | MOVE | `tools/validators/validate_quikclnt_mclientid.py` |

**Path risk:** All use `Path(__file__).resolve().parent.parent` → repo root. After move to `tools/validators/`, must use `.parent.parent.parent` or a shared `repo_root()` helper.

**Reference density:** High — cited in `Release_Manifest_v57.34.md`, `Release_Notes/v57.34_Release_Notes.md`, all Issue 21M/26 reports, `AI_Agents/*.md`.

---

### B.2 Research scripts (`_research_*.py`)

| Path | Class | Issue | Rec | Proposed destination |
|------|-------|-------|-----|----------------------|
| `QLA_Migration/_research_issue21m_quikmemo.py` | RES | 21M | MOVE | `Issue_Log_Items/Issue_21M/scripts/research_issue21m_quikmemo.py` |
| `QLA_Migration/_research_issue21k_munit.py` | RES | 21K | MOVE | `Issue_Log_Items/Issue_21/scripts/research_issue21k_munit.py` |
| `QLA_Migration/_research_issue26_ppu.py` | RES | 26 | MOVE | `Issue_Log_Items/Issue_26/scripts/research_issue26_ppu.py` |

**Path risk:** Same `parent.parent` pattern as validators. Issue-folder placement keeps artifacts co-located with reports.

---

### B.3 Risk review scripts (`_risk_review_*.py`)

| Path | Class | Issue | Rec | Proposed destination |
|------|-------|-------|-----|----------------------|
| `QLA_Migration/_risk_review_issue21m_quikmemo.py` | RISK | 21M | MOVE | `Issue_Log_Items/Issue_21M/scripts/risk_review_issue21m_quikmemo.py` |
| `QLA_Migration/_risk_review_issue21k_munit.py` | RISK | 21K | MOVE | `Issue_Log_Items/Issue_21/scripts/risk_review_issue21k_munit.py` |
| `QLA_Migration/_risk_review_issue26_mprem.py` | RISK | 26 | MOVE | `Issue_Log_Items/Issue_26/scripts/risk_review_issue26_mprem.py` |

**Reference density:** Medium — reports cite script names and `--write-report` outputs.

---

### B.4 Investigation scripts (`_investigate_*.py`)

| Path | Class | Issue | Rec | Proposed destination |
|------|-------|-------|-----|----------------------|
| `QLA_Migration/_investigate_mpolicy_keys.py` | INV | 25 | MOVE | `Issue_Log_Items/Issue_25/scripts/investigate_mpolicy_keys.py` |

**Note:** Report currently at `QLA_Migration/Issue_Log_Items/Issue_25/` — consolidate under `Issue_Log_Items/Issue_25/reports/`.

---

### B.5 Batch / test launchers (`_run_*test*.py`, `*_test.py`)

| Path | Class | Issue | Rec | Proposed destination |
|------|-------|-------|-----|----------------------|
| `QLA_Migration/_run_full_batch_test.py` | VAL | — | MOVE | `tools/batch_tests/run_full_batch_test.py` |
| `QLA_Migration/_test_lifepro_source_resolution.py` | VAL | 21M | MOVE | `tools/validators/test_lifepro_source_resolution.py` |

**Path risk (critical):** `_run_full_batch_test.py` hardcodes `BASE = r"C:\Users\warren\Documents\GitHub\Warrenhughes1974"`. Must parameterize to repo root before or during move.

**Reference density:** High — master tracking sheet, RUN_GUIDE, Issue 21M validation reports.

---

### B.6 Analysis utilities

| Path | Class | Issue | Rec | Proposed destination |
|------|-------|-------|-----|----------------------|
| `QLA_Migration/analyze_data_lineage.py` | INV | — | MOVE | `tools/investigations/analyze_data_lineage.py` |
| `QLA_Migration/discovery_iswl_analysis.py` | RES | ISWL | MOVE | `_archive/old_research/discovery_iswl_analysis.py` |

**Note:** `discovery_iswl_analysis.py` marked "NOT FOR PRODUCTION USE" — archive candidate after reports extracted.

---

### B.7 QLA_Migration PowerShell tools

| Path | Class | Issue | Rec | Proposed destination |
|------|-------|-------|-----|----------------------|
| `QLA_Migration/Tools/sync_current_to_source.ps1` | DOC | — | MOVE | `tools/release_tools/sync_current_to_source.ps1` |
| `QLA_Migration/Tools/validate_source_package.ps1` | VAL | — | MOVE | `tools/release_tools/validate_source_package.ps1` |

---

### B.8 QLA_Migration text notes (scratch / documentation)

| Path | Class | Issue | Rec | Proposed destination |
|------|-------|-------|-----|----------------------|
| `QLA_Migration/Bank does not go into quikclid-----.txt` | TMP | 21H | ARCHIVE | `_archive/scratch/QLA_Migration/Bank_does_not_go_into_quikclid.txt` |
| `QLA_Migration/Config_Rules.txt` | DOC | — | REVIEW | `docs/QLA_Migration/Config_Rules.txt` or KEEP |
| `QLA_Migration/Data_Goverence.txt` | DOC | — | REVIEW | `docs/QLA_Migration/Data_Governance.txt` (rename typo) |
| `QLA_Migration/QLAdmin_Converted_Tables.txt` | DOC | — | MOVE | `docs/QLA_Migration/QLAdmin_Converted_Tables.txt` |

---

### B.9 QLA_Migration markdown (documentation)

| Path | Class | Issue | Rec | Proposed destination |
|------|-------|-------|-----|----------------------|
| `QLA_Migration/RUN_GUIDE.md` | DOC | — | KEEP | Keep — operational runbook tied to launcher |
| `QLA_Migration/ISWL_Discovery_Summary.md` | DOC | ISWL | MOVE | `Issue_Log_Items/ISWL/reports/` or `_archive/old_research/` |
| `QLA_Migration/ISWL_Source_Data_Discovery_Report.md` | DOC | ISWL | MOVE | Same as above |
| `QLA_Migration/ROLLBACK_v57.26_insured_owner.md` | DOC | — | ARCHIVE | `_archive/superseded_scripts/ROLLBACK_v57.26_insured_owner.md` |

---

### B.10 Duplicate issue log path

| Path | Class | Issue | Rec | Proposed destination |
|------|-------|-------|-----|----------------------|
| `QLA_Migration/Issue_Log_Items/Issue_25/MPOLICY_Key_Investigation_Report.md` | DOC | 25 | MOVE | `Issue_Log_Items/Issue_25/reports/MPOLICY_Key_Investigation_Report.md` |

---

## C. Repository root — scripts and utilities

| Path | Class | Issue | Rec | Proposed destination |
|------|-------|-------|-----|----------------------|
| `validate_output.py` | VAL | — | **KEEP** | **Do not move** — imported directly by `app.py` and `QLA_Migration/app.py` |
| `validation/` package | VAL | — | KEEP | Enterprise validation layer; imports `validate_output` |
| `app.py` | PE | — | KEEP | See §A |
| `AGENTS.md` | DOC | — | KEEP | Workspace rules |
| `SANITIZE_GUIDE.md` | DOC | — | KEEP | Sanitizer documentation |

---

## D. Root-level orphan / scratch files

| Path | Class | Issue | Rec | Proposed destination |
|------|-------|-------|-----|----------------------|
| `010391876C - LifePRO.docx` (×8 policies, root) | TMP | 21 | MOVE | `Issue_Log_Items/Issue_21/evidence/` (dedupe with Issue_21 copies) |
| `010713704C - QLAdmin.docx`, `010818663C - QLAdmin.docx` (root) | TMP | 21 | MOVE | `Issue_Log_Items/Issue_21/evidence/` |
| `10-pay-prem.csv`, `20-pay-prem.csv` | TMP | — | ARCHIVE | `_archive/scratch/root_premium_csv/` |
| `adb-prem.csv`, `iswl-prem.csv`, `spul-prem.csv`, `term-*.csv`, `ul-prem.csv`, `wp-prem.csv`, `yrt-prem.csv` | TMP | rates | ARCHIVE | `_archive/scratch/root_premium_csv/` (canonical copies in `PFSA Rates/`) |
| `3877_001_page1_sample.csv` | TMP | — | REVIEW | `_archive/scratch/` or issue evidence |
| `Master_Crosswalk.csv`, `Master_Value_Translation.csv` (root) | UNK | — | REVIEW | Likely stale duplicates of `QLA_Migration/Mapping/` — do not delete without diff |
| `Sync_Rulebook_quikclmp.csv`, `Sync_Rulebook_quikclms.csv` (root) | UNK | — | REVIEW | Compare to `QLA_Migration/Configs/` copies |
| `Value_Map.json` (root) | UNK | — | REVIEW | Compare to migration config usage |

---

## E. Issue_Log_Items — scripts, evidence, temp

### E.1 Issue #21

| Path | Class | Issue | Rec | Proposed destination |
|------|-------|-------|-----|----------------------|
| `Issue_Log_Items/Issue_21/reconciliation/build_aba_reconciliation.py` | INV | 21H | MOVE | `Issue_Log_Items/Issue_21/scripts/build_aba_reconciliation.py` |
| `Issue_Log_Items/Issue_21/reconciliation/*.csv` | DOC | 21H | MOVE | `Issue_Log_Items/Issue_21/evidence/` |
| `Issue_Log_Items/Issue_21/*.docx` | DOC | 21 | MOVE | `Issue_Log_Items/Issue_21/evidence/` |
| `Issue_Log_Items/Issue_21/Issue_21.xlsx` | DOC | 21 | MOVE | `Issue_Log_Items/Issue_21/evidence/` |
| `Issue_Log_Items/Issue_21/_tmp_docx_extract/` (43 PNG) | TMP | 21 | ARCHIVE | `_archive/scratch/Issue_21/_tmp_docx_extract/` |
| `Issue_Log_Items/Issue_21/~$*.docx` | TMP | — | DELETE | Word lock files — ephemeral |
| `Issue_Log_Items/Issue_21/Issue_21K_*.md/csv/json` | DOC | 21K | MOVE | `Issue_Log_Items/Issue_21/reports/` (rename folder split optional) |
| `Issue_Log_Items/Issue_21/Issue_21_*.md` (analysis/plan) | DOC | 21 | MOVE | `Issue_Log_Items/Issue_21/reports/` |
| `Issue_Log_Items/Issue_21/Issue_21_Tracking_Sheet.*` | DOC | 21 | KEEP | Tracking stays at issue root or `reports/` |

### E.2 Issue #21M

| Path | Class | Issue | Rec | Proposed destination |
|------|-------|-------|-----|----------------------|
| `Issue_Log_Items/Issue_21M/*.md` | DOC | 21M | MOVE | `Issue_Log_Items/Issue_21M/reports/` |
| `Issue_Log_Items/Issue_21M/*.csv` | DOC | 21M | MOVE | `Issue_Log_Items/Issue_21M/evidence/` |
| `Issue_Log_Items/Issue_21M/_validate_issue21m_*_stdout.txt` | DOC | 21M | MOVE | `Issue_Log_Items/Issue_21M/evidence/` |

### E.3 Issue #26

| Path | Class | Issue | Rec | Proposed destination |
|------|-------|-------|-----|----------------------|
| `Issue_Log_Items/Issue_26/*.md` | DOC | 26 | MOVE | `Issue_Log_Items/Issue_26/reports/` |
| `Issue_Log_Items/Issue_26/*.csv` | DOC | 26 | MOVE | `Issue_Log_Items/Issue_26/evidence/` |

---

## F. Release artifacts (v57.34)

| Path | Class | Issue | Rec | Proposed destination |
|------|-------|-------|-----|----------------------|
| `Release_Notes/v57.34_Release_Notes.md` | REL | v57.34 | KEEP | `Release_Notes/` (update paths in Phase 4 only) |
| `Release_Manifest_v57.34.md` | REL | v57.34 | KEEP | Repo root or `Release_Notes/` — REVIEW preference |

---

## G. AI framework documentation

| Path | Class | Issue | Rec | Proposed destination |
|------|-------|-------|-----|----------------------|
| `AI_Agents/*.md` | DOC | — | KEEP | `AI_Agents/` — update path examples in Phase 4 |
| `AI_Agents/Templates/*.md` | DOC | — | KEEP | Templates reference `QLA_Migration/_validate_*` paths |

---

## H. Adjacent packages (out of scope for move — documented)

| Path | Class | Rec | Notes |
|------|-------|-----|-------|
| `QLA_Data_Sanitizer/` | PE | KEEP | Separate sanitizer app |
| `claims_analysis/**` (phase runners) | INV | KEEP | Claims pipeline — own phase structure |
| `plan_analysis/**` | INV | KEEP | Plan/rate analysis — own phase structure |
| `PFSA Rates/reconciliation/reconcile_rates.py` | INV | REVIEW | Rate reconciliation — not QLA_Migration clutter |
| `plan_analysis/**/_*.py` | INV | KEEP | Internal phase helpers — separate cleanup effort |

---

## I. Summary counts

| Category | Count (in scope) |
|----------|------------------|
| Validators in `QLA_Migration/` | 10 |
| Research scripts | 3 |
| Risk review scripts | 3 |
| Investigation scripts | 2 (+ 1 in Issue_21/reconciliation) |
| Batch/test launchers | 2 |
| Analysis utilities | 2 |
| QLA_Migration scratch `.txt` | 4 |
| Root orphan premium CSVs | 11 |
| Root policy `.docx` | 10 |
| Temp `_tmp_docx_extract/` images | 43 |
| Word lock files | 2 |

---

## J. High-reference scripts (do not move without Phase 4 updates)

| Script | Referenced in |
|--------|---------------|
| `_validate_issue21m_quikmemo.py` | Release notes, manifest, 15+ Issue 21M reports, AI_Agents |
| `_validate_issue26_mprem.py` | Release notes, manifest, Issue 26/21M regression reports |
| `_validate_mpolicy_width.py` | Release manifest, Issue 25 report, AI_Agents Framework |
| `_run_full_batch_test.py` | Master tracking, RUN_GUIDE, Issue 21M validation |
| `_research_issue21m_quikmemo.py` | Issue 21M planning report |
| `_investigate_mpolicy_keys.py` | Issue 25 investigation report |
| `validate_output.py` | **app.py runtime import** — KEEP at root |

---

*Phase 1 complete. Await approval of `Repository_Cleanup_Plan.md` before any moves.*
