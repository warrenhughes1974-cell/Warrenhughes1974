# Issue #32 — Regression Risk Assessment

**Issue:** #32 Policy Loan Conversion  
**Engine:** v57.40  
**Date:** 2026-06-29  
**Stage:** Development (pre-Regression Agent)

---

## 1. Risk summary

| Risk level | Count | Notes |
|------------|------:|-------|
| **Low** | 4 | Default-off emit; isolated module; no schema drift |
| **Medium** | 2 | MLOANINTX data quality; blocked date policy |
| **High** | 0 | No high-risk changes identified |

**Overall regression posture:** **Low** — QuikLoan path is env-gated and does not alter existing table emit unless explicitly enabled.

---

## 2. Blast radius analysis

### Isolated by design

| Control | Effect |
|---------|--------|
| `QLA_ENABLE_QUIKLOAN_EMIT` default off | Batch migration unchanged for standard runs |
| `QLA_QUIKLOAN_WRITE_OUTPUT` default off | No `quikloan.csv` unless explicit |
| Separate converter module | `qla_core/quikloan_converter.py` only |
| PLOAN not used elsewhere | No cross-table coupling |

### Files touched vs protected paths

| Area | Modified? | Risk |
|------|:---------:|------|
| quikridr / SL (#27) | No | None |
| quikmemo (#21M, #21J) | No | None |
| ISWL / MDEPINT (#21D) | No | None |
| MUNIT precision (#21K) | No | None |
| MPOLICY padding (#25) | No | None |
| MPREM (#26) | No | None |
| PLAN authority (#28) | No | None |
| Issue #31 logic | No | None |
| Master_Crosswalk | No | None — read-only use |
| Rulebooks | No | None |

---

## 3. Specific regression scenarios

### R-32-01: Accidental production QuikLoan emit

| Attribute | Value |
|-----------|-------|
| Likelihood | Low |
| Impact | Medium |
| Mitigation | Dual env flags; batch logs skip message when disabled |
| Residual | Low |

### R-32-02: MLOANBAL net vs gross

| Attribute | Value |
|-----------|-------|
| Likelihood | Low (implemented correctly) |
| Impact | High if wrong |
| Mitigation | v1.2 rule enforced; trace 9010331768 validates gross 3707.11 |
| Residual | Low |

### R-32-03: MLOANACCR non-zero leak

| Attribute | Value |
|-----------|-------|
| Likelihood | Low |
| Impact | High — QLAdmin double-count risk |
| Mitigation | `ZERO_AT_CONVERSION`; validator checks all 384 rows |
| Residual | Low |

### R-32-04: MLOANINT scale error (0.05 vs 5.00)

| Attribute | Value |
|-----------|-------|
| Likelihood | Low |
| Impact | High |
| Mitigation | AS_PERCENT in rules + validator rate check |
| Residual | Low |

### R-32-05: MLOANINTX incorrect Advance/Arrears

| Attribute | Value |
|-----------|-------|
| Likelihood | Medium (plan data) |
| Impact | Medium — wrong interest timing in QLAdmin |
| Mitigation | All policies fallback A until QuikPlan LOANINTX fixed; audit trail |
| Residual | Medium — **UAT required** |

### R-32-06: Duplicate MPOLICY rows

| Attribute | Value |
|-----------|-------|
| Likelihood | Low |
| Impact | High |
| Mitigation | Latest-row selection; validator duplicate check |
| Residual | Low |

### R-32-07: Orphan QuikLoan without quikmstr

| Attribute | Value |
|-----------|-------|
| Likelihood | Low |
| Impact | Medium |
| Mitigation | quikmstr orphan audit — 0 rows in May 2026 fleet |
| Residual | Low |

### R-32-08: Blocked active loan (9011190668)

| Attribute | Value |
|-----------|-------|
| Likelihood | Certain (1 policy) |
| Impact | Low |
| Mitigation | Documented in audit; SME may decide date imputation later |
| Residual | Low |

---

## 4. Protected issue preservation

No code paths modified for Issues **#21D, #21J, #21K, #21M, #21M-FU, #25, #26, #27, #28, #31**.

Validation Agent should re-run protected-issue validators at v57.40 baseline to confirm row counts unchanged when QuikLoan emit is **disabled** (default).

---

## 5. Recommended Regression Agent checks

1. Full batch run **without** QuikLoan flags — confirm quikmstr/quikridr/quikplan/quikmemo row counts match v57.39 baseline
2. Batch run **with** `QLA_ENABLE_QUIKLOAN_EMIT=1` only — confirm other outputs unchanged
3. Batch run with both flags — confirm `quikloan.csv` schema matches `QUIKLOAN_SCHEMA`
4. Re-run `validate_quikloan_issue32.py`
5. Spot-check protected-issue validators (#27 SL count, #21M memo count, etc.)

---

## 6. Production release gate

| Gate | Status |
|------|--------|
| Development complete | ✅ |
| Validation Agent | Pending |
| Regression Agent | Pending |
| QLAdmin interest UAT (9010331768) | Pending |
| Enable default emit | **NO-GO** |

---

**Assessment:** Safe to proceed to Validation Agent. Production emit remains gated pending UAT on QLAdmin loan interest calculation.
