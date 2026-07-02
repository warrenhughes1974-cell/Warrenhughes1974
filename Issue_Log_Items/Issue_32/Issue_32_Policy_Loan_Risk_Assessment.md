# Issue #32 — Policy Loan Risk Assessment

**Issue:** #32 — Policy Loan Conversion (PLOAN → QuikLoan)  
**Generated:** 2026-06-29  
**Verdict:** **No-Go for Development** — SME / BA confirmation required

---

## Risk Summary

| Category | Level | Notes |
|----------|-------|-------|
| Wrong principal mapping (MLOANPRIN) | **High** | Staging sets PRIN=BAL — may misstate QLAdmin loan screen |
| Interest rate scale error (MLOANINT) | **High** | 100× error if decimal vs percent wrong |
| Interest type mapping (MLOANINTX) | **High** | All source = F; no valid A/R mapping |
| Premature production emit | **High** | Gates exist but integration could bypass with env flags |
| Zero-balance policy omission | **Medium** | 528 paid-off loans excluded — may be wrong for CSR history |
| STATUS H with balance | **Medium** | 57 policies — may emit stale or incorrect snapshots |
| Date field gaps | **Medium** | 12 blank MLOANIDT; 1 blocked MLOANDATE |
| History vs snapshot scope | **Medium** | Loan History not converted — incomplete loan story |
| quikmstr orphan rows | **Low** | 0 orphans in current fleet |
| Regression on protected issues | **Low** | Isolated module — if surgical integration |
| PACTG / QUIKCLMS confusion | **Medium** | Loading QuikLoan may be mistaken as resolving 04xx holds |

---

## Technical Risks

### R1 — MLOANPRIN equals balance (staging default)

| Attribute | Detail |
|-----------|--------|
| Description | Phase L1 maps MLOANPRIN = LOAN_BALANCE, not inception principal |
| Likelihood | **Certain** if config unchanged |
| Impact | QLAdmin "Loan principal" may show current balance instead of original loan amount |
| Mitigation | SME sign-off on Q4; update `quikloan_derivation_rules.json` before emit |

### R2 — MLOANINT scale ambiguity

| Attribute | Detail |
|-----------|--------|
| Description | `.0500` could mean 5% stored as 0.05 or 5.00 in N(5,2) |
| Likelihood | **High** without BA decision |
| Impact | Displayed rate 0.05% vs 5.00% — CSR and billing errors |
| Mitigation | Compare sample policies to QLAdmin reference DBF or plan LOANINT; set `mloanint_scale` explicitly |

### R3 — MLOANINTX blank or wrong

| Attribute | Detail |
|-----------|--------|
| Description | LifePRO INTEREST_TYPE=F does not map to QLAdmin A/R |
| Likelihood | **Certain** if forced mapping without SME |
| Impact | Interest timing calculations wrong in QLAdmin |
| Mitigation | Leave blank until plan-default rule approved; do not map F→A/R silently |

### R4 — Latest-row selection error

| Attribute | Detail |
|-----------|--------|
| Description | Wrong sort key selects non-current history row |
| Likelihood | **Low** — logic tested; 100% ORIG+ADDED=BAL check passes |
| Impact | Wrong balance on loan screen |
| Mitigation | Sample traces in UAT; compare to LifePRO inquiry screen |

### R5 — Environment flag bypass

| Attribute | Detail |
|-----------|--------|
| Description | `QLA_ENABLE_QUIKLOAN_EMIT=1` + `QLA_QUIKLOAN_WRITE_OUTPUT=1` emits staging mapping |
| Likelihood | **Medium** in dev/UAT environments |
| Impact | Premature quikloan.csv with unresolved fields |
| Mitigation | Keep gates; require SME sign-off checklist before enabling in production batch |

### R6 — Data quality outliers

| Attribute | Detail |
|-----------|--------|
| Description | ACCRUAL_DATE max 2218; blank accrual on 9011190668 |
| Likelihood | **Low** frequency, **high** severity per row |
| Impact | Invalid dates in QLAdmin or blocked emit |
| Mitigation | Data team review; hard validation on date ranges |

### R7 — Zero accrued interest

| Attribute | Detail |
|-----------|--------|
| Description | ACCRUED_INT_AMT = 0 fleet-wide; interest capitalized into balance |
| Likelihood | **Certain** in current extract |
| Impact | MLOANACCR always 0 — may mismatch QLAdmin expectations if accrual tracked separately |
| Mitigation | SME confirms LifePRO capitalization model vs QLAdmin accrual display |

---

## Business / Operational Risks

### B1 — Paid-off loans invisible in QLAdmin

528 zero-balance policies held. If CSR expects loan history on paid-off policies, exclusion creates support gaps.

### B2 — Incomplete loan story (snapshot only)

PLOAN history (93K rows) not loaded. QuikLoan shows **current state only** — no payment/capitalization history unless future Loan History workstream.

### B3 — Confusion with Phase 22C holds

3,851 PACTG loan transactions held from QUIKCLMS. Stakeholders may expect QuikLoan load to "fix" claims data — it will not.

---

## Regression Risks (Protected Issues)

| Issue | Risk if QuikLoan integrated carelessly |
|-------|----------------------------------------|
| #21D–#21K | **Low** — separate tables |
| #25–#28 | **Low** — no shared logic |
| #31 | **Low** — no overlap identified |
| Claims / PACTG | **Medium** — ensure QuikLoan path does not alter QUIKCLMS emit |

**Mitigation:** Surgical integration per AGENTS.md — enable quikloan table only; no app.py wholesale changes; version bump with isolated diff.

---

## Rollback Safety

| Control | Status |
|---------|--------|
| Default batch skips QuikLoan | **Yes** |
| Output CSV gated | **Yes** |
| Staging reports preserved | **Yes** — `plan_analysis/phase_l1_quikloan/` |
| Config-driven mapping | **Yes** — `quikloan_derivation_rules.json` |
| No production DBF writes in converter | **Yes** |

Rollback: disable env flags; remove `quikloan.csv` from output; no impact on other tables.

---

## Go / No-Go Criteria

### No-Go (current state)

- [ ] MLOANPRIN definition unsigned  
- [ ] MLOANINT scale unsigned  
- [ ] MLOANINTX rule unsigned  
- [ ] Zero-balance emit policy unsigned  
- [ ] STATUS filter unsigned  

### Go (Development authorized when)

- [ ] Written SME mapping sheet approved  
- [ ] `quikloan_derivation_rules.json` updated with signed values  
- [ ] Sample policy UAT plan agreed (minimum 4 traces)  
- [ ] Data quality disposition on 9011190668 and date outliers  
- [ ] Ownership Decision: PLOAN authoritative vs PACTG reconciliation scope  

---

## Risk Rating Matrix

| Risk ID | Likelihood | Impact | Priority |
|---------|------------|--------|----------|
| R1 MLOANPRIN | High | High | **P1** |
| R2 MLOANINT scale | High | High | **P1** |
| R3 MLOANINTX | High | High | **P1** |
| R5 Flag bypass | Medium | High | **P2** |
| B1 Zero-balance | Medium | Medium | **P2** |
| R6 Data quality | Low | High | **P2** |
| R4 Row selection | Low | High | **P3** |
| B3 PACTG confusion | Medium | Low | **P3** |

---

## Recommendation

**Hold Development.** Proceed to **Dependency Gate / Ownership Decision** agent to collect SME answers documented in `Issue_32_Policy_Loan_Open_Questions.md`.

Phase L1 staging provides a **safe analysis baseline** — do not promote to default production emit until P1 risks are closed.

---

**Verdict:** **No-Go** — planning complete; implementation blocked on business confirmation.
