# Issue #87 — QuikForge Balancing Feature (Design Proposal, pre-Intake)

**Status:** Design proposal agreed with user 2026-07-19 (pre-Intake context handoff).
**Origin:** User request — new QuikForge UI button for source-to-QLAdmin balancing with one
numbers report plus a companion methodology document, stored in a new Balancing folder.
**This document is input context for the Intake Agent. It is not an Intake deliverable.**

## Goal

Prove that all data received in the LifePRO source files is what lands in the QLAdmin load
package: record counts, dollar control totals, and policy inventory. One consolidated report,
easy to read, with a plain-English companion document explaining each control.

## What to balance (three tiers, ~15–25 controls total)

### Tier 1 — Record counts (does every record land?)

| Control | Source | QLAdmin |
|---|---|---|
| Policies | PPOLC rows | quikmstr rows |
| Coverages/riders | PPBEN convertible rows | quikridr rows |
| Clients (distinct) | RNA distinct people | quikclnt rows |
| Client-policy links | RNA relationship rows | quikclid rows |
| Beneficiaries | RNA beneficiary rows | quikbenf rows |
| Premium history | PACTG premium txns | quikprmh rows |
| Loans | PLOAN active rows | quikloan rows |
| Dividend txns | PACTG dividend txns | quikdvpr rows |

### Tier 2 — Dollar control totals (do the dollars balance?)

| Control | Source | QLAdmin |
|---|---|---|
| Total face amount | PPBEN NUMBER_OF_UNITS × VALUE_PER_UNIT | quikridr MUNIT × MVPU |
| Total modal premium | PPOLC MODE_PREMIUM | quikmstr MMODEPREM |
| Premium history dollars | PACTG premium TRANS_AMOUNT | quikprmh PREMIUM |
| Loan balances | PLOAN LOAN_BALANCE (latest per policy) | quikloan MLOANBAL |
| Dividend accumulations | PPBENTYP ACCUM_DIVIDENDS | quikdvdp MDEPOSIT |
| Dividend transaction dollars | PACTG TRANS_AMOUNT (div txns) | quikdvpr MDIV |
| Beneficiary splits | — | each policy's splits sum to 100% |

### Tier 3 — Policy inventory (nothing lost, nothing invented)

- Every PPOLC policy number appears in quikmstr OR is on a documented exclusion list
  (e.g., BENEFIT_SEQ 99 / UV non-product rows per plan_governance rule).
- quikmstr contains no policy absent from source (two set differences).

## Status model

Each control reports **PASS / EXPLAINED / FAIL**. Expected variances (design-intended
exclusions) are driven by a known-exclusions config so a clean run reads all PASS/EXPLAINED;
FAIL means a real problem.

## Deliverables

New folder `QLA_Migration/Balancing/` (NOT inside `Output/` — Output is load-package
table CSVs only per `.cursor/rules/qla-output-folder.mdc`):

1. **`Balancing_Report_<timestamp>.csv`** — one row per control:
   `CONTROL_ID, TIER, DESCRIPTION, SOURCE_VALUE, QLADMIN_VALUE, VARIANCE, VARIANCE_PCT, STATUS, EXPLANATION`
   Plus `Balancing_Detail_<controlid>_<timestamp>.csv` per FAIL control listing the policy
   numbers driving the variance.
2. **`Balancing_Methodology.md`** — static companion document; one section per control:
   what it proves in plain English, exact source file/field and output table/field summed,
   calculation method, and what legitimate variances look like. Client/auditor-facing.

## Architecture

- New module `qla_core/balancing.py` — pure functions; reads Source CSVs via existing
  `qla_core/lifepro_source_resolver.py` (`resolve_table_source`) and Output `quik*.csv`
  from disk. Independent of converter in-memory state (auditor-style file-to-file check).
- One new UI button "Balancing" in the Operations row next to Governance Audit, same
  threaded pattern (`start_balancing_thread`). Surgical app.py addition (~30 lines);
  bump APP_VERSION in BOTH `app.py` (root) and `QLA_Migration/app.py` (currently v58.13).
- Optional: auto-run balancing at end of Full Batch so every conversion produces a report.
- Known-exclusions config: small CSV (e.g., `QLA_Migration/Configs/balancing_exclusions.csv`)
  mapping control → excluded population → reason (drives EXPLAINED status).

## Existing infrastructure to reuse (from exploration 2026-07-19)

- Row-count audit already in `process_data` (~app.py 6117–6131, 8103–8118):
  SOURCE RECORDS vs QLA OUTPUT vs VARIANCE → `Migration_Audit_Log.txt`.
- Issue #21G premium/basis staging: `qla_core/issue21_open_item_decisions.py`
  (`build_premium_basis_totals`) → `Reports/issue21g_premium_basis_totals.csv`.
- QuikLoan control-total sums in `qla_core/quikloan_converter.py` (~549).
- Money-field mappings: `Configs/Sync_Rulebook_quikridr.csv` (MUNIT/MVPU/MPREM),
  `Sync_Rulebook_quikmstr.csv` (MMODEPREM/MPAIDTO), `Sync_Rulebook_quikprmh.csv` (PREMIUM),
  `Sync_Rulebook_quikdvdp.csv` (MDEPOSIT), `Sync_Rulebook_quikdvpr.csv` (MDIV).
- Distinct from claims-family balancing under `claims_analysis/` — do not conflate.

## Scope guardrails

- Control-total level only; no per-field cell-by-cell comparison (governance audit and
  issue validators already cover that).
- No changes to conversion logic, rulebooks, or output schemas — read-only reporting.
- Preserve Issue #25 MPOLICY padding and Issue #26 MPREM mapping in all comparisons.
