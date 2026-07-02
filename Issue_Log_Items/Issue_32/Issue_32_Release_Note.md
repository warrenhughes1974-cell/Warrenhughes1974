# Issue #32 — Release Note (v57.40)

**Version:** v57.40  
**Release date:** 2026-06-29  
**Prior version:** v57.39  
**Primary issue:** **#32 — Policy Loan Conversion (QuikLoan)**  
**Engine:** `app.py` / `QLA_Migration/app.py`

---

## Summary

Release **v57.40** implements approved QuikLoan mapping v1.2: LifePRO `PLOAN` → QLAdmin `QuikLoan` with gross loan balance carry, AS_PERCENT interest rates, zero accrued interest at conversion (QLAdmin calculates), and QuikPlan-based MLOANINTX with fallback to Advance (`A`).

**Production emit remains opt-in** via environment flags until UAT confirms QLAdmin interest calculation.

---

## Issue #32 — Primary change

| Metric | Value |
|--------|------:|
| PLOAN policies (latest row) | 913 |
| QuikLoan emit rows | **384** |
| Zero-balance excluded | 528 |
| Blocked (missing date) | 1 |
| Duplicate MPOLICY | 0 |

### Mapping (v1.2)

| Field | Rule |
|-------|------|
| MLOANPRIN / MLOANBAL | `PLOAN.LOAN_BALANCE` (gross) |
| MLOANINT | `INTEREST_RATE × 100` |
| MLOANINTX | QuikPlan LOANINTX if A/R; else `A` |
| MLOANIDT / MLOANDATE | `ACCRUAL_DATE` |
| MLOANACCR / MLOANBILL | `0.00` |

### Trace policy validated

`9010331768` → `010331768C`: MLOANPRIN/BAL=3707.11, MLOANINT=5.00, MLOANINTX=A, dates=20250725

---

## Enable QuikLoan emit (controlled)

```powershell
$env:QLA_ENABLE_QUIKLOAN_EMIT = "1"
$env:QLA_QUIKLOAN_WRITE_OUTPUT = "1"   # optional — writes quikloan.csv
```

Or run standalone:

```powershell
python plan_analysis/phase_l1_quikloan/quikloan_runner.py
```

**Default batch behavior unchanged** when flags are not set.

---

## Engine and core files

| File | Change |
|------|--------|
| `app.py` | v57.40; QuikLoan batch wiring + quikplan/quikmstr paths |
| `QLA_Migration/app.py` | Mirror |
| `qla_core/quikloan_converter.py` | v1.2 mapping + audit outputs |
| `plan_governance/config/quikloan_derivation_rules.json` | v1.2 rules |
| `tools/validators/validate_quikloan_issue32.py` | New validator |

---

## Preserved issues

| ID | Status |
|----|--------|
| #27 SL suppression | Preserved |
| #21D ISWL MDEPINT | Preserved |
| #21J memo rollback | Preserved |
| #21K MUNIT precision | Preserved (closed) |
| #21M / #21M-FU memos | Preserved |
| #25 MPOLICY padding | Preserved |
| #26 MPREM | Preserved |
| #28 PLAN authority | Preserved |
| #31 | Preserved |

---

## Known data notes

- QuikPlan staged UAT has invalid `LOANINTX=22` for all plans → fleet uses fallback `A` (913 policies audited)
- Policy `9011190668` blocked: missing ACCRUAL_DATE on latest row
- Zero-balance loan emit deferred (528 policies)

---

## Validation

Development validator: `python tools/validators/validate_quikloan_issue32.py` → **PASS**

Formal Validation Agent and Regression Agent pending.

**UAT required:** QLAdmin loan interest display for policy `010331768C` before production enablement.

---

## Documentation

| File | Purpose |
|------|---------|
| `Issue_Log_Items/Issue_32/Issue_32_Development_Report.md` | Development summary |
| `Issue_Log_Items/Issue_32/Issue_32_QuikLoan_Audit_Report.md` | Audit outputs |
| `Issue_Log_Items/Issue_32/Issue_32_Next_Stage_Prompt.md` | Validation Agent prompt |
