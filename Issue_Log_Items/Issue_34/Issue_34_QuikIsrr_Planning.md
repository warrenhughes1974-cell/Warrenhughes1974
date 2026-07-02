# Issue #34 — QuikIsrr (ISWL Partial Surrender) Planning

**Issue:** #34 — ISWL QuikIsrr  
**Date:** 2026-07-01 (updated 2026-07-02 after Decision Review)  
**Mode:** Research and planning only — **no code changes, no QuikIsrr.csv emit**  
**Status:** **READY AFTER SME CONFIRMATION** — final sign-off package issued (2026-07-02)
**Prerequisites:** Issue #33 PR-6 QUIKISSC **CLOSED — APPROVED** (full surrender schedules)

> **2026-07-02 (Final SME Sign-Off Package — CURRENT):** [`Issue_34_Final_SME_Signoff_Package.md`](Issue_34_Final_SME_Signoff_Package.md) — **primary SME action document**. Recommended PR-7 scope: full package (QuikClms + QuikClmp + QuikBenh + QuikIsrr; no audit). Seven approve/correct questions gate development.

> **2026-07-02 (Late SME Scope Reconciliation):** [`Issue_34_Late_SME_Scope_Reconciliation.md`](Issue_34_Late_SME_Scope_Reconciliation.md) — supporting analysis.

> **2026-07-02 (Final Decision Closure — partially superseded):** [`Issue_34_QUIKISRR_Final_Decision_Closure.md`](Issue_34_QUIKISRR_Final_Decision_Closure.md) — candidate rule, population, amounts, dates, and output path remain closed; QuikIsrr-only scope and PFNDR MISWL rule superseded above.

> **2026-07-02 (Companion reconciliation):** Q11 closed QuikIsrr-only — see [`Issue_34_QUIKISRR_Companion_Table_Reconciliation.md`](Issue_34_QUIKISRR_Companion_Table_Reconciliation.md).

> **2026-07-02 (Decision Review):** see [`Issue_34_QUIKISRR_Decision_Review.md`](Issue_34_QUIKISRR_Decision_Review.md). Key corrections: reversal exclusion (61 rows), terminated misread retracted, payout-pair hold retired, governance dispositions.

---

## Executive summary

**QuikIsrr is not a plan/rate-grid table.** Unlike closed `QuikIssc` (8 plan-level schedule rows), `QuikIsrr` is a **policy/transaction table** keyed by **`MPOLICY`**, with one row per partial surrender event.

| Aspect | Assessment |
|--------|------------|
| QLAdmin target | `QuikIsrr` — UL/ISWL partial surrender values |
| Help section | **§7.143** (user brief cited §7.144; §7.144 is **QuikIssc** full surrender charges) |
| Paradigm | Policy transaction emit — **not** `Output/rates/` grid replication |
| Recommended source | **`PACTG_Accounting_Extract`** — debit **`561` / `0561`**, `REVERSAL_CODE ≠ Y` |
| Output | **`QLA_Migration/Output/QuikIsrr.csv`** (not `Output/rates/`) |
| MISWL | **Recommend blank/omitted** (late SME field list omits it; PFNDR match = 2026 snapshot dates; QuikPrmh precedent) — SME to confirm (Q7) |
| PR-7 scope | **Full package recommended** — QuikClms + QuikClmp + QuikBenh + QuikIsrr (no audit) — SME to confirm (Q11) |
| Development readiness | **READY AFTER SME CONFIRMATION** — Q7, Q11, Q15–Q19 outstanding; no source blockers |

**Go/no-go:** **NOT YET GO for PR-7.** Awaiting SME approve/correct on [`Issue_34_Final_SME_Signoff_Package.md`](Issue_34_Final_SME_Signoff_Package.md) Questions 1–7.

---

## 1. QLAdmin target schema (approved planning baseline)

Per Issue #34 intake (QLAdmin Help — partial surrender table):

| Field | Type | Length | Meaning |
|-------|------|--------|---------|
| **MPOLICY** | Character | 10 | Policy number |
| **MSURRDATE** | Date | 8 | Partial surrender date |
| **MSURRAMT** | Numeric | 10.2 | Partial surrender amount |
| **MISWL** | Date | 8 | Monthiversary date the transaction was added to the UL/ISWL table |

**Index key:** `MPOLICY` (policy-level; multiple rows per policy allowed if multiple partial surrenders).

**Boundary vs QuikIssc:**

| Table | Level | Key | Content |
|-------|-------|-----|---------|
| **QuikIssc** (closed) | Plan rate grid | `PLAN + GENDER + UWCLASS + BAND + ISSCNTRY + ISSUEST` | Surrender **charge schedule** (SCHG01–20) |
| **QuikIsrr** (this issue) | Policy transaction | `MPOLICY` | Partial surrender **events** (date + amount + monthiversary) |

Do **not** reuse `QuikIssc.csv` or Rate_Table SL for QuikIsrr emit.

---

## 2. Source tables inspected

### 2.1 In-repo artifacts (derived / profiling)

| Source / artifact | Path | Relevance |
|-------------------|------|-----------|
| Transaction code catalog | `claims_analysis/phase2_semantic_catalog/catalog/Claims_Transaction_Code_Catalog.csv` | Authoritative **0561** = Partial Surrender |
| PACTG frequency profile | `claims_analysis/phase1_pactg_transaction_profiling/transaction_code_frequency.csv` | Fleet **561 DEBIT**: 3,662 rows / 640 policies / $1.24M |
| Claim reconstructor | `claims_analysis/phase4_claim_reconstruction/claim_event_reconstructor.py` | `partial_surrender_amount` = sum of **0561** per chain |
| Claim domain rules | `claims_analysis/config/claim_domain_eligibility_rules.json` | 0561 in claim-domain payout codes |
| Family rules | `claims_analysis/config/claim_family_rules.json` | `"561": PARTIAL_SURRENDER` |
| ISWL status crosswalk | `plan_analysis/status_analysis/quikclms_vs_quikmstr_status_report.csv` | **177** ISWL `Disbursement / Withdrawal` claim rows (partial proxy) |
| QLAdmin Help extract | `claims_analysis/phase17_uat_governance_reporting/_qladmin_pdf_extract.txt` | Partial surrender visible next **monthiversary** in UL/ISWL history |
| Conversion manifest | `plan_analysis/product_business_test_cut/conversion_source_manifest.md` | PACTG drives **quikprmh/quikactg** — **not** QuikIsrr today |
| QuikIssc output (closed) | `QLA_Migration/Output/rates/QuikIssc.csv` | **Rejected** as QuikIsrr source (wrong table type) |

### 2.2 LifePRO extracts — workspace availability

| Extract | Path | Status |
|---------|------|--------|
| **`PACTG_Accounting_Extract20260530.csv`** | `QLA_Migration/Source/PACTG_Accounting_Extract20260530.csv` | **AVAILABLE** — used for Issue #34 profiling (latin-1 encoding) |
| **`PACTG_Accounting_Extract20260427.csv`** | `docs/claims_conversion_reference/PACTG_Accounting_Extract20260427.csv` | **AVAILABLE** (alternate; profiler prefers 20260530) |
| **`PACTG_Accounting_Extract20260427.csv`** | `QLA_Migration/Source/` | **Missing** |
| **`PFNDR_FundHistory_Extract_20260530.csv`** | Not in workspace | **Missing** — MISWL validation deferred |
| **`PFNDRDET_FundHistoryDET_Extract_20260530.csv`** | Not in workspace | Skipped (5.3 GB) |
| **`PPRBNUL_ProductBenefitInformationUL_Extract_20260530.csv`** | Not in workspace | Skipped (7.95 GB) |
| **`PEVNT_*` / `PEVNTFC_*`** | In zip inventory | **Not traced** for partial surrender |
| **`PCHEK_CheckDetail_Extract*.csv`** | Not profiled this pass | Secondary payout evidence (0090 companion) |
| **Rate_Table SL** | Hub `659 CEN II` | **Rejected** — surrender **charge schedule**, not policy events |
| **PDAGE TP/TX** | Tax valuation | **Rejected** — not surrender (same as QUIKISSC closure) |

**PACTG availability status:** **YES** — primary extract present; ISWL-scoped 561 profiling completed 2026-07-01.

---

## 3. PACTG column candidates (from profiler)

Expected columns (`claims_analysis/phase1_pactg_transaction_profiling/profiler/pactg_transaction_profiler.py`):

| PACTG column | QuikIsrr field | Transform |
|--------------|----------------|-----------|
| `POLICY_NUMBER` | **MPOLICY** | Normalize to QLAdmin 10-char policy key (same crosswalk as quikmstr/quikclms) |
| `EFFECTIVE_DATE` | **MSURRDATE** | YYYYMMDD → QLAdmin date |
| `TRANS_AMOUNT` | **MSURRAMT** | Numeric 10.2; debit-side partial surrender amount |
| *(derived)* | **MISWL** | See §5 — **not a direct PACTG column** |
| `DEBIT_CODE` | *(filter)* | **`561` / `0561`** = Partial Surrender |
| `CREDIT_CODE` | *(context)* | Often **`13`** paired with 561 (3,651 pairings observed) |
| `BENEFIT_SEQ` | *(filter)* | UL benefit sequence — may need base-benefit filter |
| `DESCRIPTION` | *(audit)* | Optional human-readable validation |

---

## 4. Transaction-code rules

### 4.1 Authoritative partial surrender code

| Code | LifePRO description | Claim family | Observed (fleet) |
|------|---------------------|--------------|------------------|
| **0561 / 561** | **Partial Surrender** | `PARTIAL_SURRENDER` | 3,662 debit rows; 640 policies; $1,244,149.92 |
| **0560 / 560** | Total Cash (full surrender) | `TOTAL_CASH` | 1,096 debit rows — **exclude from QuikIsrr** |

### 4.2 Disbursement / withdrawal mapping

| Code | Role | QuikIsrr? |
|------|------|-----------|
| **0090** | Cash Disbursements (payout) | **No** — payout leg; may accompany 561 but is not the partial surrender establishment row |
| **Disbursement / Withdrawal** (QLAdmin claim type) | ISWL partial cash-out label in claims emit | **Correlates** with partial activity; derived from PACTG chains, not a separate LifePRO table |
| **1020** | Surrender charge | **No** — fee deduction; separate from MSURRAMT unless SME directs gross vs net |

**Recommended emit filter:** One QuikIsrr row per **PACTG debit row where `DEBIT_CODE = 561`**, after ISWL MPLAN filter and dedupe rules.

### 4.3 Full vs partial distinction

| Event | Code | QuikIsrr | QuikIssc |
|-------|------|----------|----------|
| Partial surrender | **561** | **Yes** | N/A (uses charge schedule at transaction time) |
| Full surrender | **560** | **No** | Schedule applies; event goes to claims/NFO flow |
| UL disbursement-only chain | **0090** without 561 | **No** | No |

### 4.4 Reversals / voids

PACTG profiler tracks **negative `TRANS_AMOUNT`** as reversal candidates. Policy:

| Rule | Recommendation (pending SME) |
|------|------------------------------|
| Negative 561 amounts | **Exclude** or emit reversing row — SME must confirm |
| Offsetting 561 + reversal same date | **Dedupe** to net activity |
| 561-only chains without 0090 payout | **21 deferred chains / 5 policies** in governance packet — SME: include accrual-only 561 or require payout evidence? |

---

## 5. Field population rules

### 5.1 MPOLICY

- Source: `PACTG.POLICY_NUMBER`
- Join: Policy Form Crosswalk / `quikmstr` / `quikridr` for MPLAN filter
- Format: QLAdmin 10-character policy key (e.g. `010741302C` pattern in status report)

### 5.2 MSURRDATE

- Source: `PACTG.EFFECTIVE_DATE` on **561 debit** row
- Format: `YYYYMMDD` (QLAdmin Date 8)

### 5.3 MSURRAMT

- Source: `PACTG.TRANS_AMOUNT` on **561 debit** row
- Format: Numeric **10.2**
- **Open:** Gross partial surrender vs net-of-charge (1020) — SME must confirm

### 5.4 MISWL (monthiversary date)

**LifePRO does not expose a column named MISWL or “monthiversary date added to UL table” in any traced extract.**

QLAdmin Help behavior (extract): partial surrender appears in UL/ISWL history on the **next monthiversary** after the transaction.

**Candidate proxies (validation / derivation inputs):**

| Source | Column | Use |
|--------|--------|-----|
| PFNDR | `VALUATION_DATE` | Monthly fund history anchor — closest monthiversary proxy |
| quikmstr / quikridr | `MEFFDATE` / issue date | Issue-day anchor for monthiversary math |
| PACTG | `EFFECTIVE_DATE` | Transaction date (not monthiversary) |
| PCOVR | `MODAL_ANNIV_FLAG` | Product anniversary behavior hint |

**Recommended provisional rule (SME approval required):**

```text
MISWL = first policy monthiversary date on or after MSURRDATE
  where monthiversary = same day-of-month as policy issue date (MEFFDATE)
  adjusted per modal anniversary rules if issue-day invalid in target month
```

Alternative if PFNDR join proves reliable: **`MISWL` = MIN(PFNDR.VALUATION_DATE WHERE VALUATION_DATE >= MSURRDATE)** for that policy/benefit.

**Status:** **NEEDS SME** — do not implement until rule is approved.

---

## 6. Output scope (provisional)

### 6.1 ISWL MPLAN allowlist

Same 8 MPLANs as approved rate-table fleet:

`1658C1`, `1658CS`, `1659C2`, `1659CR`, `1659CS`, `1659SR`, `1669SR`, `1679CS`

Filter via `quikridr.MPLAN` / crosswalk — **not** all 640 fleet-wide 561 policies are ISWL.

### 6.2 Row-count estimates (profiled 2026-07-01)

**Source:** `QLA_Migration/Source/PACTG_Accounting_Extract20260530.csv`  
**Profiler:** `Issue_Log_Items/Issue_34/tools/quikisrr_pactg_profile.py`  
**Artifacts:** `Issue_Log_Items/Issue_34/output/QuikIsrr_Planning_Profile/`

| Scope | Metric | Value | Notes |
|-------|--------|------:|-------|
| Fleet-wide PACTG 561 | Debit rows | **3,688** | Up from Apr catalog 3,662 (+26) |
| Fleet-wide PACTG 561 | Distinct policies | **640** | |
| Fleet-wide PACTG 561 | Total TRANS_AMOUNT | **$1,254,888.33** | Gross debit amounts |
| ISWL allowlist (8 MPLANs) | 561 debit rows | **3,687** | 1 non-ISWL row excluded |
| ISWL allowlist | Distinct policies | **639** | |
| ISWL allowlist | Total TRANS_AMOUNT | **$1,241,238.33** | |
| ISWL by MPLAN | 1659C2 | **2,575** | `659 CEN II` |
| ISWL by MPLAN | 1659CR | **1,081** | `659 CEN SR` |
| ISWL by MPLAN | 1659CS | **8** | `659 CEN SD` |
| ISWL by MPLAN | 1659SR | **16** | `659 SR GD` |
| ISWL by MPLAN | 1669SR | **7** | `669 SR GD` |
| ISWL by MPLAN | 1658C1 / 1658CS / 1679CS | **0** | No 561 activity in extract for these MPLANs |
| Data quality (ISWL) | Missing EFFECTIVE_DATE | **0** | |
| Data quality (ISWL) | Missing/zero TRANS_AMOUNT | **0** | |
| Data quality (ISWL) | Negative TRANS_AMOUNT | **0** | |
| Terminated policies | 561 rows on terminated/surrendered | ~~3,676~~ | **RETRACTED 2026-07-02** — `TERM_REASON='P'` misread; actual `quikmstr.MSTATUS`: 55% of policies Active (Decision Review §F) |
| Related 560 (full surrender) | Separate 560 rows on ISWL policies | **119** | In `quikisrr_pactg_561_rejected_full_surrender.csv` — excluded from QuikIsrr |
| Related 0090 / 1020 on 561 rows | Same-policy pairing flags | **0** | **Explained 2026-07-02**: LifePRO pairs 0561 with credit **0013 Surrender Clearing** (3,676/3,686 rows), not payout codes |
| Deferred/hold (provisional) | Rows without payout-pair | ~~3,686~~ | **RETIRED 2026-07-02** — payout-pair hold replaced by `REVERSAL_CODE ≠ Y` eligibility (Decision Review §D) |
| Reversal-marked rows | `REVERSAL_CODE = 'Y'` | **61** | **NEW 2026-07-02** — excluded; 52 have corrected reposts; policies `9010718278`/`9011035652` drop out |
| **Eligible after reversal exclusion** | Rows / policies / amount | **3,626 / 637 / $1,218,544.85** | **Authoritative candidate set** (before 9010780411 hold) |
| Governance hold bucket | 1 policy / 3 rows | **3** | `9010780411` only — see §6.5 |

**Prior proxy (status report):** 177 `Disbursement / Withdrawal` claim rows / 157 policies — **undercount** vs authoritative PACTG join (639 ISWL policies with 561).

### 6.3 Terminated policies

**Resolved by evidence (2026-07-02):** **INCLUDE.** `quikmstr.MSTATUS` join (639/639 policies matched): 349 Active (55%), 209 Terminated/Death, 57 Surrendered, 14 Matured, remainder minor. Zero 0561 rows occur on/after a policy's first 0560 — history always precedes termination. No warning tier or hold needed. (SME sign-off Q8 outstanding as formality.)

### 6.4 Output location

QuikIsrr is a **policy table**, not a rate grid.

| Emit target | Recommendation |
|-------------|----------------|
| `QLA_Migration/Output/rates/` | **No** — reserve for plan rate CSVs per output-folder policy |
| `QLA_Migration/Output/QuikIsrr.csv` or dedicated policy-table path | **TBD** with SME / RUN_GUIDE alignment (Q10) |

### 6.5 Deferred / hold bucket (updated 2026-07-02)

**Governance-identified policies** (claims `SURRENDER_OFFSET_BLOCKED`) — per-policy dispositions from the Decision Review:

| Policy | MPLAN | 561 rows | Reversal-marked | Disposition |
|--------|-------|---------:|----------------:|-------------|
| 9010776027 | 1659C2 | 2 | 0 | **Include with warning** — clean; later 560 excluded separately |
| 9010780411 | 1659CR | 11 | 8 | **HOLD** — defective 2018 reverse/repost chain (Q14) |
| 9010780591 | 1659C2 | 8 | 3 | **Include with warning** — self-correcting reverse/repost |
| 9011072813 | 1659C2 | 8 | 0 | **Include with warning** — clean annual series |
| 9011107796 | 1659C2 | 9 | 0 | **Include with warning** — clean annual series |

The original payout-pair hold criterion is **retired** (structurally unsatisfiable; 0013 Surrender Clearing is the true accounting pair). The 2026-07-01 finding that 3,686/3,687 rows lacked payout-pair codes stands as data but no longer drives eligibility.

**Artifacts:** `output/QuikIsrr_Planning_Profile/quikisrr_pactg_561_deferred_review.csv` (superseded), `output/QuikIsrr_Decision_Review/quikisrr_561_governance_rows.csv`, `output/QuikIsrr_Decision_Review/quikisrr_561_reversal_marked.csv`

---

## 7. Candidate mappings summary

| QuikIsrr field | Recommended source | Confidence |
|--------------|-------------------|------------|
| MPOLICY | PACTG.POLICY_NUMBER → QLAdmin key | **High** |
| MSURRDATE | PACTG.EFFECTIVE_DATE (561 debit) | **High** |
| MSURRAMT | PACTG.TRANS_AMOUNT (561 debit) | **Medium** (gross vs net open) |
| MISWL | **Derived** (monthiversary rule) or PFNDR.VALUATION_DATE join | **Low** — SME required |

---

## 8. Rejected sources

| Source | Why rejected |
|--------|--------------|
| **QuikIssc / Rate_Table SL** | Plan-level surrender **charge schedule** — not policy transactions |
| **PDAGE TP/TX** | Tax valuation/reserve — excluded at QUIKISSC closure |
| **PSEGT SR/SL segments** | Full surrender segment path — no partial-surrender segment traced |
| **quikclms / quikclmp** | Claims header/payment tables — related workflow but wrong QLAdmin target table |
| **0090-only disbursement chains** | Payout without 561 — not partial surrender establishment |
| **0560 Total Cash** | Full surrender — exclude |
| **QuikUint / rate phases 1–5** | Unrelated product rates |

---

## 9. Relationship to claims pipeline

Partial surrender already appears in claims conversion research:

- **0561** → `SURRENDER_CLAIM` / `PARTIAL_SURRENDER` family
- ISWL enhancements set **CLAIMSTAT 99** for surrender/disbursement (`qla_core/claims_emit_enhancements.py`)
- **320** `DISBURSEMENT_CLAIM` chains (0090 payout) in Phase 6 analysis

**QuikIsrr emit is orthogonal to quikclms/quikclmp** but may share **PACTG** as upstream source. Coordinate to avoid duplicate logic; do not merge tables.

**Known governance gap:** Rulebook mentions **CLAIMSTAT 98** for partial surrender MSEQ override; active config uses **99** — reconcile before production linking.

---

## 10. Open SME questions (updated 2026-07-02)

**Authoritative SME document:** [`Issue_34_QuikIsrr_SME_Questions.md`](Issue_34_QuikIsrr_SME_Questions.md) — Q1–Q14 with per-question Decision Review status.

| ID | Question | Status after Decision Review |
|----|----------|------------------------------|
| **Q1** | PACTG 561 authoritative source | Evidence-confirmed — sign-off |
| **Q2** | Exclude 560 full surrender | Evidence-confirmed — sign-off |
| **Q3** | MSURRAMT gross vs net | Evidence supports gross — sign-off |
| **Q4** | 1020 role | Evidence-confirmed (110 fleet rows) — sign-off |
| **Q5** | 0090 pairing only | **Resolved** — 0013 Surrender Clearing is the pair |
| **Q6** | 561 without payout-pair | **Retired** — replaced by Q13/Q14 |
| **Q7** | MISWL derivation | **OPEN — blocking**; PFNDR not in workspace |
| **Q8** | Terminated policies | **Resolved** — 55% Active; include |
| **Q9** | 8 MPLAN allowlist | Evidence-confirmed — sign-off |
| **Q10** | Output path | **OPEN — blocking** |
| **Q11** | Companion record scope (QuikClms/QuikClmp/QuikBenh) | **BLOCKED — companions proven missing (0% event coverage); SME scope decision required** |
| **Q12** | "Maintenance date" = EFFECTIVE_DATE | Evidence supports — sign-off |
| **Q13** | Reversal exclusion (`REVERSAL_CODE='Y'`) | Evidence-driven — sign-off |
| **Q14** | 9010780411 disposition | Manual review — non-blocking (hold list) |

---

## 11. Recommended next steps

### Phase A — Research (complete)

1. ~~Add **`PACTG_Accounting_Extract`** to workspace~~ — **DONE** (`20260530`)
2. ~~Profile **`DEBIT_CODE=561`** joined to **8 ISWL MPLANs**~~ — **DONE** (see §6.2, §6.5)
3. ~~Decision review of 12 proposed business rules~~ — **DONE 2026-07-02** ([`Issue_34_QUIKISRR_Decision_Review.md`](Issue_34_QUIKISRR_Decision_Review.md))
4. Extract **QuikIsrr §7.143** full Help text — **pending**
5. Sample **PFNDR** monthiversary alignment — **blocked** (PFNDR not in workspace)
6. SME closure on **Q7, Q10, Q11** (blocking) + sign-offs — **OPEN**

### Phase B — Development (after SME + profiling)

**Gate:** Documented SME answers on Q7/Q10/Q11 + sign-offs required before any loader/emitter work.

1. Create `Sync_Rulebook_quikisrr.csv` (none exists today).
2. Implement isolated loader/validator (mirror claims or policy-table pattern — **not** rate_pipeline Phase 7 grid).
3. Validation gates: schema, 561-only filter, `REVERSAL_CODE ≠ Y`, MPLAN allowlist (PLAN_CODE with logged PRODUCT_ID fallback), no 0560 rows, MISWL populated, duplicate MPOLICY+MSURRDATE+MSURRAMT audit, 9010780411 hold list.
4. Phase 1–6 rate-table regression unchanged.

---

## 12. Go / no-go recommendation (final 2026-07-02)

| Gate | Status |
|------|--------|
| QLAdmin schema documented in repo | **Partial** — 4 fields from intake; full §7.143 extract pending |
| LifePRO source (PACTG 561) | **Yes** — `PACTG_Accounting_Extract20260530.csv` |
| ISWL-scoped profiling | **Yes** — 3,623 candidates / 636 policies / $1,217,593.55 |
| Business decisions (all 9 topics) | **CLOSED** — Final Decision Closure |
| Companion scope (Q11) | **CLOSED** — QuikIsrr-only |
| Output path (Q10) | **CLOSED** — `QLA_Migration/Output/QuikIsrr.csv` |
| MISWL rule (Q7) | **CLOSED** — PFNDR.VALUATION_DATE + exception file |
| **PFNDR extract available** | **Yes** — `PFNDR_FundHistory_Extract_20260530.csv` (6,237,062 bytes) |
| **PFNDR MISWL validation** | **Complete** — 99.83% match; 6 `ONLY_EARLIER` exceptions |
| QuikIssc regression risk | **Low** — isolated policy-table loader |

**Verdict:** **READY AFTER SME CONFIRMATION.** Late SME guidance (2026-07-02) reopened scope and MISWL — see [`Issue_34_Late_SME_Scope_Reconciliation.md`](Issue_34_Late_SME_Scope_Reconciliation.md).

**PR-7 expected emit (if Option B full package confirmed):** 3,623 rows each to QuikIsrr / QuikClms (phase 0, MSEQ 1..n) / QuikClmp / QuikBenh (MBENTYP 8); 9010780411 hold (3 rows) separate; MISWL blank pending Q7.

---

## 13. References

| Artifact | Path |
|----------|------|
| **Decision review (2026-07-02)** | `Issue_Log_Items/Issue_34/Issue_34_QUIKISRR_Decision_Review.md` |
| **Companion reconciliation (2026-07-02)** | `Issue_Log_Items/Issue_34/Issue_34_QUIKISRR_Companion_Table_Reconciliation.md` |
| Companion reconcile artifacts | `Issue_Log_Items/Issue_34/output/QuikIsrr_Companion_Reconciliation/` |
| Blockers | `Issue_Log_Items/Issue_34/Issue_34_Blockers.md` |
| SME questions | `Issue_Log_Items/Issue_34/Issue_34_QuikIsrr_SME_Questions.md` |
| Profiling summary (pass 1) | `Issue_Log_Items/Issue_34/output/QuikIsrr_Planning_Profile/quikisrr_pactg_561_profile_summary.json` |
| Decision review profile (pass 2) | `Issue_Log_Items/Issue_34/output/QuikIsrr_Decision_Review/quikisrr_decision_review_summary.json` |
| **Final decision closure (2026-07-02)** | `Issue_Log_Items/Issue_34/Issue_34_QUIKISRR_Final_Decision_Closure.md` |
| PFNDR readiness (placeholder) | `Issue_Log_Items/Issue_34/output/QuikIsrr_PFNDR_Readiness/quikisrr_pfndr_readiness_summary.json` |
| PACTG source | `QLA_Migration/Source/PACTG_Accounting_Extract20260530.csv` |
| Issue #33 closure | `Issue_Log_Items/Issue_33/Issue_33_PR6_Closure_Report.md` |
| Transaction catalog | `claims_analysis/phase2_semantic_catalog/catalog/Claims_Transaction_Code_Catalog.csv` |
| PACTG profiler | `claims_analysis/phase1_pactg_transaction_profiling/profiler/pactg_transaction_profiler.py` |
| ISWL MPLAN constants | `tools/validators/iswl_common.py` |
| ZIP table profile | `docs/research/iswl_zip_table_profile_20260530.md` |
| Client deferred 561 chains | `claims_analysis/phase26_client_business_review_packet/client_business_review_packet.md` |
