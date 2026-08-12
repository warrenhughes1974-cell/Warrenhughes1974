# Issue 104 — Validated Advance Loan Pilot Cohort

**Status:** Controlled pilot for QLAdmin testing (not a universal loan rule)  
**Engine:** v58.93  
**Flag:** `QLA_ISSUE104_VALIDATED_LOAN_BACKOUT` (default `1`; set `0` to rollback)

## Rule

For allowlisted policies with `VALIDATION_STATUS` in `{EXACT, ROUNDING}` only:

1. Runtime Check 1: `ORIG_LOAN_AMOUNT + LOAN_AMT_ADDED ≈ LOAN_BALANCE` (≤ $0.02)
2. Runtime Check 2: `LOAN_BALANCE × (1 − INTEREST_RATE) ≈ ORIG_LOAN_AMOUNT` (≤ $0.02)

When both pass:

`MLOANPRIN = MLOANBAL = round(LOAN_BALANCE × (1 − rate), 2)`

All other loans keep existing `LOAN_BALANCE` → `MLOANPRIN` / `MLOANBAL`.

## Allowlist

`Issue_Log_Items/Issue_104/Issue_104_Validated_Advance_Loans.csv`

## Smoke

`python tools/validators/validate_issue104_loan_pilot.py`  
(wired into `tools/batch_tests/run_full_batch_test.py`)

## 07/31 baseline (validation only — not hardcoded at runtime)

| Population | Count | Treatment |
| ---------- | ----: | --------- |
| Proven pilot | 176 | Backed-out |
| Close | 13 | Gross unchanged |
| Fail | 164 | Gross unchanged |
| Total loans | 353 | |

Dollar baseline (recalculated from batch): gross $709,531.44; adjusted $661,094.71; removed $48,436.73.

Anchor: `9010331768C` → `3331.46` / `3331.46` (gross `3506.80` @ 5.00%, `MLOANINTX=A`, `MLOANACCR=0.00`).
