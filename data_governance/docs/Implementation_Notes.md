# QLAdmin Data Governance — Implementation Notes

**Framework:** QLAdmin Data Governance  
**First governance item:** DG-QUIKCOMP — QuikComp Company Code Integrity  
**Date:** 2026-07-18

## Phase 1 inventory — legacy model

### What belonged to the old governance model

Standalone post-conversion audit package under `data_governance/`:

| Area | Paths |
|------|--------|
| Engine / config / reports | `governance_engine.py`, `governance_config.py`, `governance_report.py`, `__init__.py` |
| Rule pipeline (18 categories) | `rules/chk_*.py`, `rules/_helpers.py`, `rules/__init__.py` |
| Constants | `constants/schema_manifests.py`, `valid_codes.py`, `valid_states.py` |
| Tests | `tests/test_chk_*.py`, `tests/test_governance_ui_progress.py`, `tests/conftest.py` |
| Outputs (runtime) | `QLA_Migration/Reports/governance/governance_audit.{html,csv,log}` |
| App entry | `app.py` / `QLA_Migration/app.py` — `run_governance`, UI buttons, post-batch hook |
| Progress plan | `qla_core/run_logging.py` — `STAGE_PLANS["governance_audit"]` |

Historical requirements dump (not part of the executable package): `QLA_Migration/Data_Goverence.txt`.

### What was removed

Entire legacy `data_governance/` tree (engine, 18-category rule pipeline, constants, and old tests). No temporary adapter of the old `run_governance(conversion_context)` / `AuditFinding` / `GovernanceReport` API was retained.

### What was retained (shared / unrelated)

| Retained | Reason |
|----------|--------|
| `plan_governance/` | Conversion-time product/plan authority — different framework |
| `qla_core/non_product_row_governance.py` | Emit-time non-product row classification |
| `qla_core/sl_benefit_governance.py` | Issue #27 SL benefit governance |
| Claims / Citizens / plan_analysis “governance” folders | Domain-specific investigation frameworks |
| App claims KPI “governance” banner helpers | Phase17 UAT metrics — not the Quik* audit package |
| `QLA_Migration/Data_Goverence.txt` | Historical requirements text only |
| `qla_core/run_logging.py` stage plan key | Retained and retargeted wording for the new framework |

### What was replaced

| Old | New |
|-----|-----|
| Monolithic 18-check pipeline | Incremental rule registry under `data_governance` |
| COMP-001 / COMP-002 / COMP-003 (plus COMP-004 length) | DG-QUIKCOMP-001 / 002 / 003 only |
| CSV-only conversion Output reader | QLAdmin data directory loader (DBF or CSV) |
| `governance_audit.{html,csv,log}` | `data_governance_findings.csv`, `data_governance_summary.csv`, `data_governance_report.md` |
| Implicit UI-only entry | CLI `python -m data_governance` + UI wired to new runner |

## Assumptions

1. Input may be conversion `quik*.csv` files or QLAdmin `quik*.dbf` files in the configured data directory.
2. Company-code comparison is case-preserving after trim (no forced upper/lower).
3. Policy company code is the **final non-space character** of normalized `MPOLICY` (supplied business rule, not a QLAdmin manual rule).
4. Source DBF/CSV files are never modified by this framework.

## Removed legacy files (complete list)

- `data_governance/__init__.py` (old)
- `data_governance/governance_engine.py`
- `data_governance/governance_config.py`
- `data_governance/governance_report.py`
- `data_governance/constants/` (all)
- `data_governance/rules/chk_*.py`, `_helpers.py`, `__init__.py` (old pipeline)
- `data_governance/tests/test_chk_*.py`, `test_governance_ui_progress.py`, `conftest.py` (old)

## Existing files modified

- `app.py` (v58.04) — UI / post-batch wired to `run_data_governance`
- `QLA_Migration/app.py` (v58.04) — same wiring
- `qla_core/run_logging.py` — governance stage labels
- `tools/packaging/eng_pkg_001_prechange_baseline.py` — test-suite note

## Confirmation

- No source QuikComp / QuikAgts / QuikMstr DBF or CSV data was modified.
- No temporary adapter of the old API was retained.

## 2026-07-18 enhancement — any data region + DG-QUIKMSTR-001

- Centralized `TableResolver` maps logical tables → case-insensitive DBF/CSV names.
- CLI: `python -m data_governance run --input <region> --output <base> [--item|--rule]`.
- Each run writes `output/<run_id>/` with summary, findings, results CSV, report, JSON, log.
- Source DBFs opened read-only via dbfread (`rb`); `source_files_modified=False` recorded on every run.
- Item 2 rule `DG-QUIKMSTR-001` validates MPOLICY length 4–11 after trim-only normalization.

## 2026-07-18 enhancement — DG-QUIKLIST (Item 4)

- Added QuikList table stem resolution (`TABLE_QUIKLIST`).
- Item 4 rules `DG-QUIKLIST-001` … `DG-QUIKLIST-009` under `rules/group_billing_integrity/`.
- Defaults (MSORT=N, MLAPSEL/MLAPSEH/MBILLDAY/MBILLMODE=0, MSTATUS=A) are business-supplied standards.
- Field name used for health/accident lapse days: **MLAPSEH** (not MLASPEH).
- DG-QUIKLIST-002 reuses `build_company_code_index` from Item 1.

## Standing practice — production-style run after each item

After implementing any new governance item, always run the full suite against the production-style region:

```bash
python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2025" --output "Q:\CSO\Governance_Reports"
```

Open `data_governance_results.csv` from the new run folder. Source DBFs remain read-only.

## 2026-07-18 reporting enhancement — Executive Summary + Validation Guide

- `data_governance_report.md` now starts with an Executive Summary and **Data Conformance Accuracy**.
- Each run also writes `data_governance_validation_guide.md` and `data_governance_validation_manifest.json` from the selected registered rules + actual run results (no separate static duplicate catalog).
- Accuracy = Looked_Fine / Records_Reviewed × 100 when counts reconcile; otherwise Unavailable with a logged warning.
- Validation rule logic was not changed.

## 2026-07-18 enhancement — DG-QUIKDATE (Item 5)

- Schema verified from `QUIKDATE.DBF` — see `docs/QuikDate_Schema_Verification.md`.
- Billing dates: PACBILL, DIRBILL, REINBILL must equal dynamically calculated prior-month-end for the run date.
- Defaults: ACHFILEID=0, ACHFILEID2=A, ESCDATE blank via physical `ESC_DATE`.
- ACHFILEID and ACHFILEID2 are separate fields.

## 2026-07-18 enhancement — DG-PLANVALUES (Item 6)

- Schema verified from CSO plan-value DBFs — see `docs/PlanValues_Schema_Verification.md`.
- Rules `DG-PLANVALUES-001` … `008` under `rules/plan_value_integrity/`.
- Source tables evaluated independently: QuikPlCv, QuikPlTv, QuikPlGp, QuikPlDb, QuikPlDv.
- MORT on Cv/Tv → QuikQxs.MORT; ETIMORT on Cv only → QuikQxs.MORT; PLAN → QuikPlan.PLAN.
- GENDER / UWCLASS / BAND use approved defaults (`0` / `00` / `00`) or composite plan+code lookups.
- Band reference: QuikPlBd.BDCODE (QuikPlVd not present in inspected region).
- ISSUEST: `00` or approved 50-state + DC list; EFFDATE: 1900-01-01 through run date + 12 calendar months.
- Runner does not hard-stop the item when one source/reference table is missing.

## 2026-07-18 enhancement — DG-QUIKPLAN (Item 7)

- Schema verified from CSO QuikPlan and related DBFs — see `docs/QuikPlan_Schema_Verification.md`.
- Rules `DG-QUIKPLAN-001` … `033` under `rules/plan_setup_integrity/`.
- Physical field aliases: PAYRS→PAYYRS, MAXUNITS→MAXUNIT, ROUNDING→RRULE; Commission Setup = QuikComm (QUIKCOMM.DBF).
- MYGA / UL / single-premium classification from optional `config/plan_classification.csv` (no invented classifiers).
- Warnings (`STATUS_WARN`) for INITVAL non-default (015), missing traditional/annuity tables (027/028), out-of-range dates (033).
- Report 1 Plan Setup subsections via `RuleDescription.subsection`; Warnings Found counted separately from Problems Found.
- Runner treats `DG-QUIKPLAN` like `DG-PLANVALUES` for missing optional supporting tables.

### Assumptions documented

1. INSYRS and INSAGE are the insurance-period pair; plans beginning with 5 may have both payment/insurance pairs zero.
2. “Plan begins with less than 9” means first character 0–8 (traditional value-table warnings).
3. Company codes validated against QuikComp (rule 032), not QuikPlan.
4. DEFICIENCY must be N when first character is A–Z or 9.
5. INITVAL defaults to 1000 unless `INITVAL_EXCEPTION=Y` in classification CSV.
6. LOAGE Age 1 = plan-level LOAGE 0 with LOAGE < HIAGE on the QuikPlan row.
7. Out-of-range dates are governance warnings only; source DBFs are never modified.
