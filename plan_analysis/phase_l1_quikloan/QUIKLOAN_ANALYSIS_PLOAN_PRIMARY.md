# QuikLoan Phase L1 — PLOAN-Primary Design

**Version:** app v57.9 (staging only)  
**Date:** 2026-06-01  
**Status:** Phase A/B — profiling, candidate generation, QA reporting (not default production emit)

---

## Design summary

| Topic | Decision |
|-------|----------|
| **Primary source** | `QLA_Migration/Source/PLOAN.csv` (alias: `PLOAN_LoanInformation_Extract_20260427.csv`) |
| **PACTG role** | Reconciliation and audit only — **not** used to derive QuikLoan balances |
| **Grain** | One QuikLoan row per `MPOLICY` (latest valid PLOAN snapshot per policy) |
| **Legacy Loyal2QL** | `quikloan` was opened and `:Zap()` but never `:Append()` — no legacy load pattern |
| **Reference DBF** | `QUIKLOAN.DBF` — 9 fields, structure reference only |

---

## Target QuikLoan schema

Field order (matches `QUIKLOAN_SCHEMA` / DBF):

| Field | DBF type | Phase L1 source / note |
|-------|----------|------------------------|
| MPOLICY | C(10) | `POLICY_NUMBER` + Master_Crosswalk when available |
| MLOANPRIN | N(10,2) | Staging: `LOAN_BALANCE` — **BA must confirm** vs `ORIG_LOAN_AMOUNT` |
| MLOANBAL | N(10,2) | Latest `LOAN_BALANCE` |
| MLOANINT | N(5,2) | `INTEREST_RATE` — scale **unresolved** (see QA report) |
| MLOANINTX | C(1) | **Unresolved** — do not map `INTEREST_TYPE=F` to A/R |
| MLOANIDT | D(8) | Precedence: `LAST_REPAY_DATE`, then `CAPITALIZED_DATE` |
| MLOANDATE | D(8) | `ACCRUAL_DATE` (required for emit) |
| MLOANACCR | N(10,2) | `ACCRUED_INT_AMT` (profile: all 0.00) |
| MLOANBILL | N(10,2) | No PLOAN source — config default `0.00` only |

---

## Latest-row selection logic

1. Load PLOAN; trim headers/values.
2. Exclude invalid rows: blank/dash `POLICY_NUMBER`, non-numeric `LOAN_BALANCE`, separators.
3. Parse dates: `ACCRUAL_DATE`, `LAST_CHG_DATE`, `LAST_REPAY_DATE`, `CAPITALIZED_DATE`, `INT_START_DATE`.
4. Sort per policy by: `ACCRUAL_DATE`, `LAST_CHG_DATE`, `LAST_CHG_TIME` (config-driven).
5. Take last row per `POLICY_NUMBER`.
6. Classify: `ACTIVE_CANDIDATE` if `LOAN_BALANCE <> 0`; else `ZERO_BALANCE_HOLD`.

Config: `plan_governance/config/quikloan_derivation_rules.json`

---

## Field mapping recommendations (staging)

- **Emit default:** non-zero latest balance only (`emit_zero_balance_loans: false`).
- **MLOANINT:** preserve raw decimal interpretation under `mloanint_scale: UNRESOLVED_REVIEW`; review `interest_rate_format_review.csv`.
- **MLOANINTX:** leave blank; document `INTEREST_TYPE` / `INT_METHOD` in `unresolved_mloanintx.csv`.
- **MLOANBILL:** config default; document in `unresolved_mloanbill.csv`.
- **Principal check:** `ORIG_LOAN_AMOUNT + LOAN_AMT_ADDED = LOAN_BALANCE` matched 100% in profile — still flag MLOANPRIN definition for BA.

---

## QA reports produced

Written under `plan_analysis/phase_l1_quikloan/`:

| # | File |
|---|------|
| 1 | `QUIKLOAN_ANALYSIS_PLOAN_PRIMARY.md` (this document) |
| 2 | `ploan_profile_summary.txt` |
| 3 | `ploan_latest_row_selection.csv` |
| 4 | `quikloan_emit_candidates.csv` |
| 5 | `zero_balance_loan_policies.csv` |
| 6 | `missing_invalid_dates.csv` |
| 7 | `missing_interest_rate.csv` |
| 8 | `unresolved_mloanintx.csv` |
| 9 | `unresolved_mloanbill.csv` |
| 10 | `interest_rate_format_review.csv` |
| 11 | `mloanprin_vs_balance_exceptions.csv` |
| 12 | `quikloan_emit_exceptions.csv` |
| 13 | `quikloan_mapping_trace.csv` (audit trace) |
| 14 | `pactg_ploan_reconciliation.csv` (optional; config `pactg_reconciliation_enabled`) |

---

## Implementation limits

- **Not** final production QuikLoan emit.
- **No** automatic `QLA_Migration/Output/quikloan.csv` unless `QLA_QUIKLOAN_WRITE_OUTPUT=1`.
- **GUI/batch:** QuikLoan runs only when `QLA_ENABLE_QUIKLOAN_EMIT=1`.
- **Unchanged:** claims orchestration, quikprmh, quikactg, quikdvdp, PACTG transaction processing, Master_Crosswalk core behavior.
- **Modules:** `qla_core/quikloan_converter.py`, `plan_analysis/phase_l1_quikloan/quikloan_runner.py`.

### Run headless staging

```text
python plan_analysis/phase_l1_quikloan/quikloan_runner.py
```

---

## Open BA questions

1. Load only `LOAN_BALANCE <> 0`, or also zero-balance historical loans?
2. Is `MLOANPRIN` current balance, original principal, or another field?
3. Should `.0500` load as `0.05` or `5.00` in QLAdmin `MLOANINT`?
4. Where does QLAdmin `MLOANINTX` A/R come from?
5. Should `INTEREST_TYPE=F` remain unmapped (fixed rate)?
6. Should `MLOANIDT` use `LAST_REPAY_DATE`, `CAPITALIZED_DATE`, or other?
7. Is `MLOANBILL` required for go-live; what source owns it?
8. Should `STATUS_CODE` / `TYPE_CODE` gate emit?
9. Is PLOAN-only authority acceptable when no PACTG loan transactions exist?
10. Is snapshot-only sufficient, or is loan history loading required later?

---

## PLOAN profile (last runner execution: 2026-06-01)

| Metric | Count |
|--------|------:|
| Raw rows | 93,502 |
| Valid rows | 93,501 |
| Excluded separator | 1 |
| Unique policies (latest) | 912 |
| Latest non-zero balance | 389 |
| Latest zero balance | 523 |
| **Emit candidates** (default rules) | **388** |
| Held zero balance | 523 |
| Blocked missing MLOANDATE | 1 |
- `ACCRUED_INT_AMT` = 0.00 across extract
- `INTEREST_RATE` commonly `.0500`, `.0740`
- `INTEREST_TYPE` = F (fixed — not QLAdmin A/R)

*Re-run `quikloan_runner.py` to refresh counts from current extract.*
