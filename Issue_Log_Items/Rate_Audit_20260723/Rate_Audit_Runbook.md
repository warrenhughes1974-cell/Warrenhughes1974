# Rate Audit Runbook

**Purpose:** Prove rate correctness from LifePRO source extracts to the generated QLAdmin load package, then to the post-load QLAdmin export.

This audit is intentionally separate from `QLA_Migration/Output/`. It writes evidence only under `Issue_Log_Items/Rate_Audit_20260723/`.

---

## What This Audit Checks

1. **Source inventory**
   - Rate_Table, PDAGE, PAAGERAT, PDINT, PDINTTBL
   - PCOVR/PCOVRSGT/PSEGT and policy-form crosswalks
   - CSO valuation/crosswalk assumptions
   - CV and non-CV inheritance manifests
   - Shared-rate candidate manifests
   - Parallel/out-of-main-pipeline items like `QuikAing`

2. **Expected package build**
   - Runs the existing `qla_core.rate_pipeline` in an audit sandbox.
   - Redirects PDAGE staging to the audit evidence folder.
   - Builds expected rows for factor, key, member, interest, surrender, and UW-class tables.

3. **Generated package parity**
   - Compares expected rows to `QLA_Migration/Output/rates/`.
   - Checks schema, missing rows, extra rows, duplicate keys, and cell mismatches.

4. **QLAdmin loaded-data parity**
   - Optional until QLAdmin export files are available.
   - Compares `Output/rates` to a post-load export directory containing CSV or DBF files.

5. **Family controls**
   - CV #98 GL85 anchor checks.
   - Pipeline blockers.
   - QuikUint dependency.
   - Forbidden COI/GCOI companion key files.
   - Manifest row-count consistency.
   - Test_Validation drift.
   - QuikAing scope warning.

---

## Commands

Run source-to-package audit:

```powershell
python Issue_Log_Items\Rate_Audit_20260723\scripts\run_rate_audit.py
```

Run with post-load QLAdmin export:

```powershell
python Issue_Log_Items\Rate_Audit_20260723\scripts\run_rate_audit.py --qla-export C:\path\to\QLAdmin\rate_export
```

Skip the large cell ledger for quick debug only:

```powershell
python Issue_Log_Items\Rate_Audit_20260723\scripts\run_rate_audit.py --skip-cell-ledger
```

Do not use `--skip-cell-ledger` for final acceptance.

---

## Evidence Outputs

| File | Meaning |
|------|---------|
| `evidence/source_inventory.csv` | All configured source authorities and whether present |
| `evidence/rate_table_inventory.csv` | Expected vs Output vs QLAdmin export row presence |
| `evidence/canonical_expected_rows.csv` | One expected row per QLAdmin output row |
| `evidence/canonical_expected_cells.csv` | One expected value per non-key target cell |
| `evidence/package_table_summary.csv` | Source/pipeline expected rows vs `Output/rates` |
| `evidence/package_mismatches.csv` | Missing/extra/mismatched Output cells |
| `evidence/qla_table_summary.csv` | Output vs post-load QLAdmin export |
| `evidence/qla_mismatches.csv` | Missing/extra/mismatched QLAdmin export cells |
| `evidence/family_controls.csv` | Rate-family acceptance controls |
| `evidence/dryrun_validation_issues.csv` | Existing pipeline validation warnings/blockers |
| `reports/Rate_Audit_Executive_Summary.md` | Human-readable audit readout |

---

## Acceptance Rules

- **Source-to-package must pass** before client handoff.
- **QLAdmin export parity must pass** before saying the rates are loaded correctly in QLAdmin.
- `Output/Test_Validation/rates/` is not audit authority unless regenerated and manifest-clean.
- Warnings can be accepted only with an explicit documented business decision.
- Failures should become separate issue-log items unless they are corrected immediately under an approved issue.

