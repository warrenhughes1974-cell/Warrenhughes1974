# Issue #44 — Planning Report

**Issue:** #44 — ETI/RPU QuikLoan Balance Clear (stale PLOAN latest-row)  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning complete — Phase A + Phase B **approved by project lead 2026-07-09**  
**Generated:** 2026-07-09  
**Agent:** Planning Agent (read-only analysis)

---

## 1. Executive finding

BA reported ETI policies (`MSTATUS`/`MPHSTAT` = **44**) with non-zero `quikloan.MLOANBAL`. Business rule (approved): **loan balance must be cleared on RPU or ETI**.

Two defects / gaps:

| Phase | Finding | Fix |
|-------|---------|-----|
| **A** | Same-day PLOAN clear (`.00`) loses latest-row tie-break because `LAST_CHG_TIME` (HHMMSS) is fed to `parse_ploan_date` | Sort time as HHMMSS string/int — never as a date |
| **B** | Even with correct latest row, a policy can remain ETI with open PLOAN (e.g. 011226579C) | Suppress QuikLoan emit when `quikmstr.MSTATUS` ∈ {44, 45} |

Status mapping itself is **correct** (`PAID_UP_TYPE=ET` → `PUT_ET` → 44). Do not change Issue #13 / MSTATUS logic.

---

## 2. Confirmed LifePRO sources

| Source | File | Fields used |
|--------|------|-------------|
| Loan history | `PLOAN_LoanInformation_Extract_*.csv` | `POLICY_NUMBER`, `LOAN_BALANCE`, `ACCRUAL_DATE`, `LAST_CHG_DATE`, `LAST_CHG_TIME`, `INTEREST_RATE` |
| Policy master | `PPOLC_PolicyMaster_Extract_*.csv` | `PAID_UP_TYPE`, `TOTAL_LOAN_COUNT`, `CONTRACT_CODE` |
| Status (converted) | `Output/quikmstr.csv` | `MPOLICY`, `MSTATUS` (44=ETI, 45=RPU) |

Grain: QuikLoan = **one row per policy** from **latest** PLOAN snapshot (Issue #32).

---

## 3. Confirmed QLAdmin targets

| Table | Field | Rule |
|-------|-------|------|
| `quikloan` | `MLOANBAL` / `MLOANPRIN` | From latest `PLOAN.LOAN_BALANCE` (gross); zero-balance held (`emit_zero_balance_loans=false`) |
| `quikloan` | (row presence) | Phase B: **no emit** when policy MSTATUS is ETI/RPU |
| `quikmstr` / `quikridr` | `MSTATUS` / `MPHSTAT` | **Unchanged** |

---

## 4. Proposed mapping / logic changes

### Phase A — latest-row sort

**Current:** `latest_row_sort` = `ACCRUAL_DATE`, `LAST_CHG_DATE`, `LAST_CHG_TIME`.  
For `LAST_CHG_TIME`, converter builds `_LAST_CHG_TIME_TS` via `parse_ploan_date`. HHMMSS values like `212541` become fake dates; `212540` often becomes `NaT`. Ascending sort + `tail(1)` then picks the **pre-clear** balance.

**Proposed:** Treat `LAST_CHG_TIME` as a **time key** (strip + zero-pad to 6 digits / numeric), never `parse_ploan_date`. Keep date columns on timestamp sort.

**Emit interaction:** With correct `.00` latest row → `_LATEST_BALANCE_CLASS=ZERO_BALANCE_HOLD` → existing hold → **no QuikLoan row** (desired clear).

### Phase B — ETI/RPU suppress

**Proposed:** After map + before/within emit validation, if `quikmstr.MSTATUS` ∈ {`44`,`45`} for the mapped `MPOLICY`, hold with reason `ETI_RPU_STATUS_HOLD` (do not emit QuikLoan row).

Requires `quikmstr_path` (already passed from `app.py` QuikLoan path). If quikmstr missing, log warning and skip Phase B only (Phase A still applies).

---

## 5. Open client questions

| # | Question | Disposition |
|---|----------|-------------|
| Q1 | Clear loan on ETI/RPU? | **Approved** — Phase A + B |
| Q2 | Suppress even if PLOAN still open? | **Approved** — Phase B |
| Q3 | Emit zero-balance row vs omit row? | Keep Issue #32 default: **omit** (`emit_zero_balance_loans=false`) |

---

## 6. Formatting / fallback

- MPOLICY: existing crosswalk + `format_qladmin_mpolicy` (#25) — unchanged  
- Interest scale AS_PERCENT — unchanged  
- MLOANACCR = 0 at conversion — unchanged  
- Phase B hold is **status-based**, not balance-based  

---

## 7. Estimated impact (pre-dev simulation)

| Metric | Approx |
|--------|-------:|
| BA sample policies | 6 ETI with loan |
| Phase A flips (latest → zero) | ~30 policies |
| Phase A BA sample fixed | 5 of 6 |
| Phase B needed for remaining sample | 011226579C (open PLOAN) |
| Fleet ETI (44) / RPU (45) | ~206 / ~194 |
| Current ETI with QuikLoan row | 6 |

---

## 8. Sample traces (before)

| Policy | MSTATUS | PLOAN clear exists | Emitted MLOANBAL | After Phase A | After A+B |
|--------|---------|--------------------|------------------|---------------|-----------|
| 010391876C | 44 | Yes (.00) | 1544.26 | No row | No row |
| 010404602C | 44 | Yes | 1088.59 | No row | No row |
| 010456751C | 44 | Yes | 534.89 | No row | No row |
| 010510671C | 44 | Yes | 7050.43 | No row | No row |
| 010525250C | 44 | Yes | 1401.12 | No row | No row |
| 011226579C | 44 | No (1236.48 open) | 1236.48 | Still 1236.48 | **No row** |

---

## 9. Explicitly not changed

- `quikmstr.MSTATUS` / Issue #13 termination precedence  
- `quikplan.LOANINT` (v57.58 product setup)  
- Issue #25 MPOLICY padding / #26 MPREM  
- Non-loan tables; QuikLoan field mapping other than selection + status hold  

---

## 10. Risks and unknowns

| Risk | Mitigation |
|------|------------|
| Time sort changes non-ETI loans | Validate non-ETI emit set delta; only same-day time ties should flip |
| Phase B drops legitimate open loans on ETI | **Accepted** — BA approved |
| quikmstr not loaded when QuikLoan runs | Require quikmstr path; warn if absent |
| RPU (45) currently 0 QuikLoan hits | Phase B still applies for future safety |

---

## 11. Recommended Development task (surgical)

1. Fix `select_latest_ploan_row_per_policy` — HHMMSS sort for `LAST_CHG_TIME`.  
2. Add ETI/RPU hold in emit validation using `quikmstr` status map.  
3. Config note in `quikloan_derivation_rules.json`.  
4. Bump `APP_VERSION` both `app.py` files → **v57.59**.  
5. Validator / evidence for BA 6 + fleet audit CSV under `Issue_44/`.  

**Do not implement in Planning** — Development after G2 + G3.
