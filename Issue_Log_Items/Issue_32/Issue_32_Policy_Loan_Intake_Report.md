# Issue #32 — Policy Loan Conversion Intake Report

**Issue ID:** 32  
**Title:** Policy Loan Conversion (PLOAN → QuikLoan)  
**Status:** Planning Complete — **No-Go for Development**  
**Framework stage:** Intake + Planning  
**Generated:** 2026-06-29  
**Engine version:** v57.39  
**Code changes:** None (research / planning only)

---

## 1. Objective

Research how to convert LifePRO policy loan data from `PLOAN` into QLAdmin `QuikLoan`, determine current implementation state, profile source data, and produce a field-mapping proposal with open business questions for SME review.

---

## 2. Executive Conclusion

| Question | Answer |
|----------|--------|
| Does policy loan conversion already exist? | **Partial** — Phase L1 **staging-only** pipeline exists; **not** default production emit |
| Is `PLOAN` the correct authoritative source? | **Yes** — designated primary source; `PACTG` is reconciliation-only |
| Which `PLOAN` rows are in scope (staging default)? | **Latest snapshot per policy** where `LOAN_BALANCE ≠ 0` → **384 emit candidates** |
| Can Development proceed? | **No** — client / BA confirmation required on principal, interest scale, interest type, dates, zero-balance policy, and STATUS/TYPE gating |

---

## 3. Existing Implementation Review

### 3.1 Production converter (`app.py` v57.39)

| Component | Location | Status |
|-----------|----------|--------|
| QuikLoan table slot | `app.py` — batch loop `t_id.lower() == "quikloan"` | **Gated off** unless `QLA_ENABLE_QUIKLOAN_EMIT=1` |
| Output CSV write | `QLA_QUIKLOAN_WRITE_OUTPUT=1` | **Gated off** by default |
| Converter module | `qla_core/quikloan_converter.py` | **Implemented** (Phase L1 staging) |
| Derivation rules | `plan_governance/config/quikloan_derivation_rules.json` | **Configured** |
| Schema | `qla_core/schema_constants.py` → `QUIKLOAN_SCHEMA` | **9 fields** |
| Source resolver | `qla_core/lifepro_source_resolver.py` → `quikloan` / `PLOAN` | **Registered** (required=False) |
| Phase L1 runner | `plan_analysis/phase_l1_quikloan/quikloan_runner.py` | **Operational** |
| Phase L1 design doc | `plan_analysis/phase_l1_quikloan/QUIKLOAN_ANALYSIS_PLOAN_PRIMARY.md` | **Complete** |

**Verdict:** Conversion logic exists as **isolated staging** introduced in app v57.9+. It does **not** participate in default full-batch migration output. Legacy Loyal2QL opened `quikloan` but never `:Append()` — no legacy load pattern to preserve.

### 3.2 Search hits summary

| Search term | Finding |
|-------------|---------|
| `QuikLoan` / `quikloan` | Schema, converter, app gated hook, Phase L1 artifacts, release manifest reference |
| `MLOANPRIN` … `MLOANBILL` | Mapped in `quikloan_converter.py`; QA CSVs under `plan_analysis/phase_l1_quikloan/` |
| `PLOAN` | Source extract + converter input; not used elsewhere for balances |
| `LOAN_BALANCE` / `ACCRUED_INT_AMT` / `INTEREST_RATE` | Primary mapping sources in derivation rules |

### 3.3 Related but out-of-scope domains

| Domain | Relationship |
|--------|--------------|
| `PACTG` 04xx Borrowed Money | Loan **transaction** history — held from QUIKCLMS (Phase 22C); **not** used for QuikLoan balance derivation |
| `QuikPlSt.MLOANINT` | Plan/state loan-rate override — separate from policy-level QuikLoan |
| Claims semantic governance | 3,851 pseudo-claim rows flagged; recommends separate QuikLoan workstream |

---

## 4. Source Data Inventory

| Item | Value |
|------|-------|
| Authoritative extract | `QLA_Migration/Source/PLOAN_LoanInformation_Extract_20260530.csv` |
| Legacy alias | `PLOAN.csv` (not present; resolver accepts dated extract pattern) |
| Crosswalk | `QLA_Migration/Mapping/Master_Crosswalk.csv` |
| quikmstr reference | `QLA_Migration/Output/quikmstr.csv` (for policy existence validation) |

---

## 5. PLOAN Profile Summary (2026-06-29 refresh)

Full detail: `Issue_32_PLOAN_Source_Profile.md`

| Metric | Count / Value |
|--------|---------------|
| Total raw rows | 93,858 |
| Valid data rows | 93,857 |
| Excluded separator rows | 1 |
| Unique policies | 913 |
| Rows with `LOAN_BALANCE > 0` (all history) | 93,036 |
| Rows with `ACCRUED_INT_AMT > 0` | **0** |
| Rows with `ORIG_LOAN_AMOUNT > 0` | 93,190 |
| Rows with `SPEC_CLS_LOAN_BAL > 0` | **0** |
| Blank / invalid policy rows | 1 |
| Policies with multiple PLOAN rows | **913 (100%)** |
| Rows per policy (median / max) | 45 / 871 |
| Latest-row non-zero balance policies | 385 |
| Latest-row zero balance policies | 528 |
| Total active `LOAN_BALANCE` (latest, non-zero) | **$1,554,200.67** |
| Policies in `quikmstr` (crosswalk-mapped) | **913 / 913 (100%)** |
| Phase L1 emit candidates (default rules) | **384** |
| Held zero-balance | 528 |
| Blocked missing `MLOANDATE` | 1 (`9011190668` → `011190668C`) |

---

## 6. Multi-Row / Grain Decision

`PLOAN` is a **history table** — every policy has multiple accrual snapshots (TYPE_CODE `R` = regular accrual, `A` = adjustment; STATUS_CODE `H` = history, `A` = active, `R` = repaid-related).

**QLAdmin constraint:** `QuikLoan` index `QuikLoan.ntx` key = `MPOLICY` → **one loan row per policy**.

**Staging selection rule (existing):** Sort by `ACCRUAL_DATE`, `LAST_CHG_DATE`, `LAST_CHG_TIME`; take **last row per `POLICY_NUMBER`**.

Example trace — policy `9010331768`: 88 history rows; latest row `20250725` STATUS `A`, balance `$3,707.11` selected.

---

## 7. Proposed Mapping (Staging Baseline — Not Final)

Detail: `Issue_32_QuikLoan_Field_Mapping_Proposal.md`

| QuikLoan | Staging source | Confidence |
|----------|----------------|------------|
| MPOLICY | `POLICY_NUMBER` + Master_Crosswalk | **High** |
| MLOANPRIN | `LOAN_BALANCE` (config) | **Low** — BA must confirm vs `ORIG_LOAN_AMOUNT` |
| MLOANBAL | `LOAN_BALANCE` | **High** |
| MLOANINT | `INTEREST_RATE` | **Medium** — decimal vs percent scale unresolved |
| MLOANINTX | blank (config) | **Low** — `INTEREST_TYPE=F` does not map to A/R |
| MLOANIDT | `LAST_REPAY_DATE` → `CAPITALIZED_DATE` | **Medium** — 12 emit rows blank IDT |
| MLOANDATE | `ACCRUAL_DATE` | **High** — required for emit |
| MLOANACCR | `ACCRUED_INT_AMT` | **High** (always 0.00 in extract) |
| MLOANBILL | config default `0.00` | **Low** — no PLOAN source |

**Schema note:** QLAdmin Help and this repo use field name **`MLOANIDT`** (interest paid-to date). Some intake templates label this **`MLOANDT`** — same semantic slot, different name. Implementation follows `QUIKLOAN_SCHEMA`.

---

## 8. Open Business Questions

Full list: `Issue_32_Policy_Loan_Open_Questions.md` (10 items — all require SME input before production emit).

---

## 9. Impact and Risk

| Document | Purpose |
|----------|---------|
| `Issue_32_Policy_Loan_Impact_Analysis.md` | Fleet counts, financial totals, downstream effects |
| `Issue_32_Policy_Loan_Risk_Assessment.md` | No-Go rationale and regression risks |

---

## 10. Validation Strategy (Planned)

At implementation stage, validate:

1. Row count: emit candidates = unique non-zero latest policies minus date/policy blocks  
2. Policy count: 1:1 `MPOLICY` — no duplicates (confirmed: **0 duplicates** in staging emit)  
3. Balance totals: Σ `MLOANBAL` vs Σ latest `LOAN_BALANCE` for active policies  
4. Accrued interest totals: Σ `MLOANACCR` (currently $0.00 fleet-wide)  
5. Interest rate population: 100% populated in staging emit  
6. Date population: `MLOANDATE` required; `MLOANIDT` 12 blanks acceptable only if BA confirms  
7. Policy existence: all mapped policies in `quikmstr` (**100% pass**)  
8. Sample traces: minimum 5 policies across STATUS/TYPE/rate mix  
9. Re-run Phase L1 QA CSV suite under `plan_analysis/phase_l1_quikloan/`

---

## 11. Protected Issues

No changes made to Issues #21D, #21J, #21K, #21M, #21M-FU, #25, #26, #27, #28, or #31.

---

## 12. Routing

| Next stage | Agent |
|------------|-------|
| **Dependency Gate + Ownership Decision** | See `Issue_32_Next_Stage_Prompt.md` |
| Development Agent | **Blocked** until BA/SME gate PASS |

---

## 13. Artifact Index

| File | Purpose |
|------|---------|
| `Issue_32_Policy_Loan_Intake_Report.md` | This document |
| `Issue_32_PLOAN_Source_Profile.md` | Detailed source profiling |
| `Issue_32_QuikLoan_Field_Mapping_Proposal.md` | Field-level mapping |
| `Issue_32_Policy_Loan_Open_Questions.md` | SME question list |
| `Issue_32_Policy_Loan_Impact_Analysis.md` | Fleet impact |
| `Issue_32_Policy_Loan_Risk_Assessment.md` | Risk / No-Go |
| `Issue_32_Next_Stage_Prompt.md` | Cursor-ready next prompt |
| `Issue_32_Profile_Stats.json` | Machine-readable profile stats |

**Repo reference artifacts (unchanged):**

- `plan_analysis/phase_l1_quikloan/*` — refreshed 2026-06-29  
- `qla_core/quikloan_converter.py`  
- `plan_governance/config/quikloan_derivation_rules.json`

---

**Stop point:** Planning complete. Await Dependency Gate / Ownership Decision. No implementation.
