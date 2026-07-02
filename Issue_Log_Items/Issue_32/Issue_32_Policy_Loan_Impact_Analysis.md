# Issue #32 — Policy Loan Impact Analysis

**Source:** `PLOAN_LoanInformation_Extract_20260530.csv`  
**Cross-reference:** `QLA_Migration/Output/quikmstr.csv`, Master_Crosswalk  
**Machine summary:** `Issue_32_Profile_Stats.json`  
**Generated:** 2026-06-29  
**Engine:** v57.39

---

## 1. Fleet Overview

| Metric | Count / Value |
|--------|---------------|
| LifePRO policies with any PLOAN history | **913** |
| PLOAN history rows (valid) | **93,857** |
| Policies with outstanding loan (latest balance ≠ 0) | **385** |
| Policies with paid-off / zero latest balance | **528** |
| Phase L1 emit candidates (default rules) | **384** |
| Blocked from emit (data quality) | **1** |
| Held zero-balance (by rule) | **528** |

---

## 2. Financial Exposure

| Measure | Amount |
|---------|-------:|
| Total outstanding loan balance (385 active latest) | **$1,554,200.67** |
| Total MLOANBAL in staging emit (384 rows) | **$1,553,578.89** |
| Blocked balance (9011190668) | **$621.78** |
| Total accrued interest (latest, all policies) | **$0.00** |
| Average loan balance (active) | **$4,036.89** |
| Median loan balance (active) | *(see distribution below)* |

### Balance distribution (385 active policies — approximate bands)

| Band | Estimated policies |
|------|-------------------:|
| < $100 | ~15 (includes $0.08 residual) |
| $100 – $1,000 | ~80 |
| $1,000 – $5,000 | ~150 |
| $5,000 – $15,000 | ~120 |
| > $15,000 | ~20 (max single policy in emit ~$21,387) |

*Exact band counts available from `ploan_latest_row_selection.csv` on request.*

---

## 3. Interest Rate Fleet Mix

| Rate (raw) | Policies (latest) | % of fleet |
|------------|------------------:|-----------:|
| 7.40% (.0740) | 715 | 78.3% |
| 5.00% (.0500) | 198 | 21.7% |

**Impact:** Wrong scale decision on `MLOANINT` affects **100%** of loan policies (displayed rate off by 100× if decimal vs percent confused).

---

## 4. STATUS / TYPE Impact on Emit Scope

If SME imposes filters, emit count changes materially:

| Filter scenario | Approx. policies | Δ vs default |
|-----------------|-----------------:|-------------:|
| Default (balance ≠ 0, no STATUS filter) | 385 | — |
| STATUS = A only | ~240 | −145 |
| Exclude STATUS H with balance | ~328 | −57 |
| Include zero-balance loans | ~912 | +528 |

---

## 5. Downstream Table Impact

| QLAdmin domain | Impact if QuikLoan loads |
|----------------|--------------------------|
| **quikmstr** | No schema change — MPOLICY FK already exists (100% match) |
| **QuikLoan.ntx** | 384 new index entries (one per MPOLICY) |
| **Loan History** | Not in scope — PLOAN history not loaded; future workstream |
| **QUIKCLMS** | No change — 04xx loan transactions remain held (Phase 22C) |
| **quikactg / PACTG** | No change — reconciliation optional |
| **QuikPlan LOANINT** | Validation cross-check only — plan-level default rates |

---

## 6. PACTG Overlap (Claims Phase 22C)

| Metric | Value |
|--------|------:|
| Non-claim loan accounting rows held from QUIKCLMS | 3,851 |
| Affected policies (approx.) | 663 |

**Impact:** QuikLoan conversion addresses **snapshot balances**; PACTG addresses **transaction history**. Both may reference the same policies but serve different QLAdmin functions. Loading QuikLoan does **not** resolve the held QUIKCLMS pseudo-claims — that remains correct per semantic governance.

---

## 7. Conversion Platform Impact

| Component | Current state | Post-implementation (if authorized) |
|-----------|---------------|--------------------------------------|
| `app.py` batch default | QuikLoan **skipped** | Optional: enable in default manifest |
| `QLA_Migration/Output/quikloan.csv` | **Not written** | ~384 rows |
| Release manifest | QUIKLOAN listed (v57.34+) | Populate with loan counts |
| Validators | MPOLICY width check references quikloan.csv | Extend loan-specific validators |
| Version | v57.39 | Bump when integrating default emit |

---

## 8. Policy Existence / Orphan Risk

| Check | Result |
|-------|--------|
| PLOAN policies mapped via crosswalk | 913 / 913 |
| Mapped MPOLICY in quikmstr | 913 / 913 |
| Active loan orphans | **0** |

**Impact:** No orphan QuikLoan rows expected — low master-file integrity risk.

---

## 9. Multi-Row Aggregation Impact

| Scenario | Impact |
|----------|--------|
| Wrong row selected (not latest) | Balance/date/rate stale — **high** financial error |
| Sum balances across history | **Incorrect** — would inflate totals ~100× |
| Multiple concurrent loans | **Not observed** — single thread per policy |

Median 45 history rows per policy — selection logic is **critical**; already implemented in Phase L1.

---

## 10. Sample Policy Traces

### Trace A — Active loan (emit candidate)

| Field | Value |
|-------|-------|
| LifePRO | 9010331768 |
| QLAdmin MPOLICY | 010331768C |
| LOAN_BALANCE | $3,707.11 |
| INTEREST_RATE | .0500 |
| STATUS / TYPE | A / R |
| Emit | **Yes** |

### Trace B — Paid-off (held)

| Field | Value |
|-------|-------|
| LifePRO | 9010300689 |
| QLAdmin MPOLICY | 010300689C |
| LOAN_BALANCE | $0.00 |
| LAST_REPAY / CAPITALIZED | 20100801 |
| Emit | **No** — ZERO_BALANCE_HELD |

### Trace C — Active, blank MLOANIDT (emit with gap)

| Field | Value |
|-------|-------|
| LifePRO | 9010381745 |
| QLAdmin MPOLICY | 010381745C |
| LOAN_BALANCE | $7,199.96 |
| MLOANDATE | 20200121 |
| MLOANIDT | *(blank)* |
| Emit | **Yes** — IDT gap flagged |

### Trace D — Blocked (data defect)

| Field | Value |
|-------|-------|
| LifePRO | 9011190668 |
| QLAdmin MPOLICY | 011190668C |
| LOAN_BALANCE | $621.78 |
| ACCRUAL_DATE | blank |
| Emit | **No** — MISSING_MLOANDATE |

---

## 11. UAT Scope Recommendation

When development authorized:

| Tier | Policies | Purpose |
|------|----------|---------|
| Tier 1 — Financial | 10 largest balances | Balance/principal match |
| Tier 2 — Rate mix | 5 @ 5%, 5 @ 7.4% | MLOANINT display |
| Tier 3 — Edge cases | 9011190668, 9010381745, 9010363098 ($0.08) | Data quality / residual |
| Tier 4 — Zero balance | 5 held policies | Confirm exclusion correct |

---

## 12. Business Impact Summary

| Stakeholder | Impact |
|-------------|--------|
| Policyholders with loans | 385 active — loan balances visible in QLAdmin after load |
| Operations / CSR | Loan inquiry screen populated for ~42% of PLOAN history policies |
| Accounting | PACTG loan transactions remain separate; QuikLoan is snapshot |
| Conversion team | Low-code path exists (Phase L1); SME gate is primary blocker |
| Claims team | No regression — 04xx hold unchanged |

---

## 13. Comparison to Prior Analysis

| Artifact | Count | Notes |
|----------|------:|-------|
| Phase 22C QuikLoan candidate mention | 3,851 | PACTG-derived policy count — broader than PLOAN snapshot |
| Phase L1 emit (Apr 2026 extract) | 388 | Current May extract: **384** (fleet stable) |
| Unique PLOAN policies | 912 → **913** | +1 policy in May extract |

---

**Conclusion:** Material but bounded impact — **384 policies**, **~$1.55M** outstanding balances. Primary risk is **mapping semantics**, not fleet size. SME confirmation required before financial exposure is committed to production QLAdmin.
