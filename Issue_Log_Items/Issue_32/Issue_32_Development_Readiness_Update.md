# Issue #32 — Development Readiness Update

**Issue:** #32 — Policy Loan Conversion  
**Gate verdict:** **CONDITIONAL PASS — Development Authorized**  
**Generated:** 2026-06-29  
**Engine baseline:** v57.39 → target **v57.40** (surgical bump on integration)

---

## 1. Readiness Summary

| Area | Ready? | Notes |
|------|:------:|-------|
| Source authority (PLOAN) | ✅ | Confirmed |
| Field mapping approved | ✅ | v1.2 mapping sheet |
| MLOANINT scale | ✅ | AS_PERCENT |
| MLOANPRIN / MLOANBAL | ✅ | Both LOAN_BALANCE |
| MLOANACCR | ✅ | 0.00 — QLAdmin calculates |
| MLOANIDT / MLOANDATE | ✅ | ACCRUAL_DATE |
| MLOANINTX | ⚠️ | Plan lookup + fallback A |
| MLOANBILL | ✅ | 0.00 |
| Converter module exists | ✅ | Phase L1 staging |
| UAT criteria defined | ✅ | See §4 |
| Production emit enabled | ❌ | Remains gated post-UAT |

**Overall:** **READY for Development Agent** under conditional assumptions.

---

## 2. Development Scope (Authorized)

### In scope

1. Update `plan_governance/config/quikloan_derivation_rules.json` per approved mapping  
2. Update `qla_core/quikloan_converter.py` surgically:
   - `AS_PERCENT` for MLOANINT (may already exist — wire config)
   - `MLOANACCR = 0.00` always
   - `MLOANIDT` precedence: ACCRUAL_DATE first
   - `MLOANINTX` from QuikPlan join with A/R validation + default `A`
3. Re-run `plan_analysis/phase_l1_quikloan/quikloan_runner.py` — refresh QA CSVs  
4. Add/update validator(s) for approved mapping invariants  
5. Bump `app.py` version if batch integration touched  
6. Produce `Issue_32_Implementation_Report.md` + validation evidence  

### Out of scope

- LifePRO UI interest calculation  
- Default production batch emit (`QLA_ENABLE_QUIKLOAN_EMIT=1`) without UAT PASS  
- QuikPlan LOANINTX CSV fix (separate issue — log warning only)  
- Zero-balance loan emit (528 held) — deferred OD-32D  
- PACTG / Loan History  
- Protected issues #21D–#28, #31  

---

## 3. Config Diff Preview

| Key | Current (v1.0) | Approved (v1.2) |
|-----|----------------|-----------------|
| `mloanint_scale` | UNRESOLVED_REVIEW | **AS_PERCENT** |
| `mloanprin_source` | LOAN_BALANCE | LOAN_BALANCE |
| `mloanbal_source` | LOAN_BALANCE | LOAN_BALANCE |
| `mloanaccr_source` | ACCRUED_INT_AMT | **ZERO_AT_CONVERSION** |
| `mloanintx_source` | UNRESOLVED | **QUIKPLAN_LOANINTX** |
| `mloanintx_default` | "" | **A** |
| `mloanidt_precedence` | LAST_REPAY, CAPITALIZED | **ACCRUAL_DATE**, LAST_REPAY, CAPITALIZED |
| `mloandate_source` | ACCRUAL_DATE | ACCRUAL_DATE |
| `mloanbill_default` | 0.00 | 0.00 |
| `emit_zero_balance_loans` | false | false |

---

## 4. UAT Acceptance Criteria

### Primary trace — 9010331768 / 010331768C

| Check | Expected CSV emit | Post-load QLAdmin (client UAT) |
|-------|-------------------|--------------------------------|
| MLOANPRIN | 3707.11 | Gross principal visible |
| MLOANBAL | 3707.11 | QLAdmin may show net after calc |
| MLOANINT | 5.00 | 5% display |
| MLOANINTX | A | Advance timing |
| MLOANACCR | 0.00 | QLAdmin calculates (~18.19 unearned/advance semantics) |
| MLOANDATE | 20250725 | 07/25/2025 |
| MLOANIDT | 20250725 | Last accrued |

### Fleet validators (automated)

| Validator | Rule |
|-----------|------|
| Row count | ~384 emit candidates (±1 for edge cases) |
| Duplicate MPOLICY | 0 |
| MLOANACCR | All 0.00 |
| MLOANINT | .0500 policies → 5.00; .0740 → 7.40 |
| MLOANINTX | All A or R; expect mostly A |
| MLOANIDT/MLOANDATE | Non-blank except known exceptions |
| quikmstr existence | 100% MPOLICY match |

### Secondary traces

| Policy | MPOLICY | Focus |
|--------|---------|-------|
| 9010346921 | 010346921C | .0500 rate |
| 9010391004 | 010391004C | Active .0500 |
| 9010381745 | 010381745C | Prior blank LAST_REPAY — ACCRUAL_DATE should populate IDT |

---

## 5. Known Exceptions

| Policy | Issue | Handling |
|--------|-------|----------|
| 9011190668 | Phase L1 `MISSING_MLOANDATE` | Investigate accrual parse; hold from emit until resolved |
| QuikPlan LOANINTX=`22` | Invalid plan CSV | Fallback `A` + trace warning |

---

## 6. Risk Register (Post-Gate)

| Risk | Level | Mitigation |
|------|-------|------------|
| QLAdmin does not calc interest as expected | Medium | UAT on 9010331768 before batch enable |
| Wrong MLOANINTX if plan uses arrears | Low–Medium | Plan lookup + future QuikPlan fix |
| Gross vs net balance confusion | Low | Document in release notes; UAT |
| Enabling emit too early | Medium | Keep env gates until UAT PASS |

---

## 7. Deliverables Checklist (Development Agent)

- [ ] `quikloan_derivation_rules.json` updated  
- [ ] `quikloan_converter.py` updated (surgical)  
- [ ] Phase L1 QA CSVs refreshed  
- [ ] Validator(s) added/passing  
- [ ] `app.py` version bump (if applicable)  
- [ ] `Issue_32_Implementation_Report.md`  
- [ ] `Issue_32_Validation_Evidence.json`  
- [ ] Release note snippet for v57.40  

---

## 8. Go / No-Go

| Decision | Status |
|----------|--------|
| **Development Agent** | **GO** — Conditional PASS |
| **Production emit** | **NO-GO** — until UAT PASS |
| **Full gate PASS** | Pending client UAT on interest calculation |

---

**Next:** `Issue_32_Next_Stage_Prompt.md` — Development Agent prompt.
