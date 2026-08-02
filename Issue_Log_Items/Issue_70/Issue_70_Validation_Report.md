# Issue #70 — Validation Report

**Issue:** #70 — QuikPlan `LOANINTX` from `PCOVR.LOAN_ADV_ARREARS` (`0`/`N`→`A`, `1`→`R`)  
**Framework stage:** Validation Agent (Stage 6)  
**Engine version:** **v58.50**  
**Validation script:** `tools/validators/validate_issue70_loanintx.py` v1.0 (wrapper `QLA_Migration/_validate_issue70_loanintx.py`)  
**Output directory:** `QLA_Migration/Output/`  
**Before snapshot:** `Issue_Log_Items/Issue_70/evidence/quikplan_before_v5850_rebatch.csv` / `quikloan_before_v5850_rebatch.csv`  
**Evidence summary:** `Issue_Log_Items/Issue_70/evidence/issue70_validation_summary.json`  
**Generated:** 2026-08-02  
**Verdict:** **PASS**

**Status note:** Validation only — no production-code changes; issue tracking status not updated; Regression/Closure not run.

---

## Commands Run

```text
# 1) Focused unit tests
python Issue_Log_Items/Issue_70/test_issue70_loanintx_map.py -v
# Result: OK — 4 tests (codebook, normalize preserves R, convert row arrears, blank audit)

# 2) Pre-rebatch Output validator (expected FAIL — stale 141×A)
python QLA_Migration/_validate_issue70_loanintx.py
# Result: FAIL — A=141 R=0; SAL traces A≠R

# 3) Full UAT re-batch (required; prior concurrent batch was v58.49)
$env:QLA_FORCE_PPOLC_EXTRACT='PPOLC_PolicyMaster_Extract_20260630.csv'
python tools/batch_tests/run_full_batch_test.py
# Result: exit 0; APP_VERSION=v58.50; Source=PPOLC_PolicyMaster_Extract_20260630.csv
# Log: QLA_Migration/Logs/_full_batch_test_log.txt
# Batch line: Issue #70 LOANINTX emit: A=137 R=4

# 4) Full Output validator + Test_Validation publish
python QLA_Migration/_validate_issue70_loanintx.py
python QLA_Migration/_validate_issue70_loanintx.py --publish-test-validation
# Result: PASS; published Output/Test_Validation/quikplan.csv

# 5) Static checks
python -m py_compile qla_core/quikplan_converter.py tools/validators/validate_issue70_loanintx.py QLA_Migration/_validate_issue70_loanintx.py Issue_Log_Items/Issue_70/test_issue70_loanintx_map.py
# IDE lints on changed Issue #70 paths: no issues reported
```

---

## 1. Trace Plan Results

| Plan | Field | Expected | Actual (post v58.50 batch) | Result |
|------|-------|----------|----------------------------|--------|
| `1SALOL` | `LOANINTX` | R | R | **PASS** |
| `1SALML` | `LOANINTX` | R | R | **PASS** |
| `1SALMI` | `LOANINTX` | R | R | **PASS** |
| `9SLADB` | `LOANINTX` | R | R | **PASS** |
| `1960PO` | `LOANINTX` | A | A | **PASS** |

PCOVR source-fidelity mismatches: **0**.

---

## 2. Acceptance Criteria (Risk / Implementation)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Fleet `LOANINTX` = **137 A / 4 R** on 141 plans | **PASS** |
| 2 | Arrears set exactly `{1SALOL,1SALML,1SALMI,9SLADB}` | **PASS** |
| 3 | Blank/unknown → A fail-safe (unit + no invalid values in Output) | **PASS** |
| 4 | `SKIP_TRANSLATION` retained (no A→22 mistranslation) | **PASS** (unit + Output values only A/R) |
| 5 | QuikLoan `MLOANINTX`: no current SAL / R-plan loan flips | **PASS** (see §4) |
| 6 | Validator PASS against **full** `QLA_Migration/Output/` | **PASS** |

---

## 3. Source Alignment

| Check | Result |
|-------|--------|
| `PCOVR.LOAN_ADV_ARREARS` → QuikPlan `LOANINTX` codebook | **PASS** (0 mismatches vs extract+crosswalk) |
| Fallback blank/unknown → A | **PASS** (unit tests; batch emit A=137 R=4) |
| Rulebook `Source_Field=LOAN_ADV_ARREARS`, `SKIP_TRANSLATION` | Present in `Sync_Rulebook_quikplan.csv` |

---

## 4. QuikLoan / Untouched Behavior

| Check | Before | After | Result |
|-------|-------:|------:|--------|
| `quikloan.csv` row count | 356 | 356 | Match |
| `MLOANINTX` distribution | 356×A | 356×A | Match |
| `MLOANINTX` flips on common loan keys | — | **0** | **PASS** |
| Loan rows on R plans (`1SAL*`, `9SLADB`) | 0 | 0 | **PASS** (no SAL loan population to inherit R) |
| Control sample `9010331768*` | A | A | **PASS** |

QuikLoan algorithm (`resolve_mloanintx`) not modified; no active R-plan loans in current emit.

---

## 5. Row Counts / Schema

| Table | Count | Notes |
|-------|------:|-------|
| `quikplan.csv` | 141 | Same plan set before/after; 79 columns unchanged |
| `quikloan.csv` | 356 | Unchanged row count / keys |

Schema/format: column order preserved; `LOANINTX` values restricted to `A`/`R`.

---

## 6. Impact Summary (before → after re-batch)

| Metric | Value |
|--------|------:|
| Plans with **only** `LOANINTX` change | **4** (`1SALOL`,`1SALML`,`1SALMI`,`9SLADB`: A→R) |
| Plans with other field diffs vs before snapshot | **7** — `PLANVALOPT` Y→N on `121PUA`,`165PUA`,`170PUA`,`185PUA`,`1970PA`,`1OLPUA`,`1POPUA` |
| QuikLoan `MLOANINTX` flips | **0** |

**Note for Regression:** The 7 `PLANVALOPT` flips are **outside Issue #70 codebook scope** (collateral full-batch product rebuild). Issue #70 intended delta is the 4 `LOANINTX` A→R plans only. Regression Agent should confirm whether `PLANVALOPT` Y→N is expected from concurrent product/rate logic or residual drift.

---

## 7. Failures

None for Issue #70 acceptance criteria.

---

## 8. Issue A conversion checklist (post re-batch)

Appended to `Issue_Log_Items/Issue_A/Issue_A_Conversion_Checklist.md` (run 2026-08-02 / v58.50). OPEN IDs evaluated:

| ID | Result | Evidence |
|----|--------|----------|
| A2 | **BLOCKED** | All 141 `DEFICIENCY=N`; awaiting CSO |
| A5 | **OPEN** | `BASIS` blank on 141/141; Valuation_Setup / Issue #80 |
| A7 | **OPEN** | `VARGP=4` on 141/141; awaiting Eric (Item 09); examples `920ADB`,`965ADB`,`1659C2` class |
| A8c | **OPEN** | Annuity `A60MIR`/`A96DAR` `DEPINT`/`LOANINT`=0.00; SME scope |
| A8d | **OPEN** | No schg column on QuikPlan schema; awaiting Eric |
| A9a | **OPEN** | Prefix-9 `PLANTYPE` blank 56/56 (e.g. `920ADB`,`9665WP`,`9SLADB`); awaiting Eric field confirm |

Implemented CLOSED checks spot-checked OK where applicable (A1 SP factors; A8a/A8b PAR/VARDB=0; A9b PAR=0 on 9*; A10 QuikUwpo 5 distinct UWCODE; A4 rates blank-PLAN=0).

---

## 9. Output folder hygiene (`qla-output-folder.mdc`)

**Limitation — not cleaned this session:** Auto-review blocked relocating non-table artifacts. Output root still contains non-load files/dirs after the v58.50 batch:

- `claims_*validation*.csv`, `claims_review_hold_manifest.csv`, `cso_mortality_crosswalk_qa.csv`, `variation_code_audit.csv` → should move to `QLA_Migration/Reports/`
- `claims_uat_dbf/`, `claims_uat_staging/` → should move to `QLA_Migration/Staging/`

Load tables + `rates/` + `Test_Validation/` are present. **Does not change Issue #70 PASS**, but handoff package is not yet Output-root clean.

---

## 10. Recommendation

- [x] **Advance to Regression Agent** (Issue #70 Validation **PASS** on full Output)
- [ ] Return to Development — not required for #70 LOANINTX
- [ ] Do **not** mark Closed / run Closure until Regression + G7 accountability

**Regression focus:** Confirm only the 4 SAL `LOANINTX` deltas vs intended; investigate/document the 7 `PLANVALOPT` collateral changes; optional Output hygiene cleanup before client package.

---

## Appendix — Validator stdout (PASS)

```text
validate_issue70_loanintx.py v1.0
output: ...\QLA_Migration\Output
rows: 141
LOANINTX counts: {'A': 137, 'R': 4}
trace:
  1SALOL: LOANINTX=R expected=R [OK]
  1SALML: LOANINTX=R expected=R [OK]
  1SALMI: LOANINTX=R expected=R [OK]
  9SLADB: LOANINTX=R expected=R [OK]
  1960PO: LOANINTX=A expected=A [OK]
PCOVR fidelity mismatches (first pass): 0
QuikLoan sample 9010331768*: MLOANINTX=A
PASS
published: ...\Output\Test_Validation\quikplan.csv
```
