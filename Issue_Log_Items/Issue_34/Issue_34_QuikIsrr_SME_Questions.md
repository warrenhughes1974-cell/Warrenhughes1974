# Issue #34 — QuikIsrr SME Questions

**Issue:** #34 — ISWL QuikIsrr (Partial Surrender)  
**Date:** 2026-07-01 (updated 2026-07-02 after Late SME Scope Reconciliation)  
**Mode:** SME review — **no development**  
**Status:** **READY AFTER SME CONFIRMATION** — final sign-off package issued (2026-07-02)

> **2026-07-02 (Final SME Sign-Off Package — CURRENT):** [`Issue_34_Final_SME_Signoff_Package.md`](Issue_34_Final_SME_Signoff_Package.md) — **seven approve/correct questions** for PR-7. Recommended scope: full package (QuikClms + QuikClmp + QuikBenh + QuikIsrr; no audit). Awaiting SME signature.

> **2026-07-02 (Late SME Scope Reconciliation):** [`Issue_34_Late_SME_Scope_Reconciliation.md`](Issue_34_Late_SME_Scope_Reconciliation.md) — analysis supporting the sign-off package.

**Final closure (pre-late-SME):** [`Issue_34_QUIKISRR_Final_Decision_Closure.md`](Issue_34_QUIKISRR_Final_Decision_Closure.md)

**Profiling:** Complete — see [`output/QuikIsrr_Planning_Profile/quikisrr_pactg_561_profile_summary.json`](output/QuikIsrr_Planning_Profile/quikisrr_pactg_561_profile_summary.json) and [`output/QuikIsrr_Decision_Review/quikisrr_decision_review_summary.json`](output/QuikIsrr_Decision_Review/quikisrr_decision_review_summary.json)

**Planning reference:** [`Issue_34_QuikIsrr_Planning.md`](Issue_34_QuikIsrr_Planning.md)  
**Decision review:** [`Issue_34_QUIKISRR_Decision_Review.md`](Issue_34_QUIKISRR_Decision_Review.md) — 2026-07-02 review of 12 proposed business decisions against LifePRO accounting documentation and SME comments. **Several questions below are resolved by evidence; see per-question status.**

---

## Key distinction (preserve)

| Table | Purpose |
|-------|---------|
| **QuikIssc** (Issue #33 — CLOSED) | Surrender **charge schedule** (plan rate grid) |
| **QuikIsrr** (Issue #34) | Actual partial surrender **transaction history** (policy-level) |

---

## QLAdmin schema (Help §7.143)

| Field | Type | Length | Meaning |
|-------|------|--------|---------|
| MPOLICY | Character | 10 | Policy number |
| MSURRDATE | Date | 8 | Partial surrender date |
| MSURRAMT | Numeric | 10.2 | Partial surrender amount |
| MISWL | Date | 8 | Monthiversary date added to UL/ISWL table |

**Index:** `MPOLICY` (multiple rows per policy allowed).

---

## Recommended provisional answers (pending SME sign-off)

These reflect the project team's recommended defaults unless source evidence or QLAdmin behavior contradicts them.

| # | Topic | Recommended answer |
|---|-------|------------------|
| R1 | Source | **561 / 0561** PACTG debit = QuikIsrr source |
| R2 | Full surrender | **560 / 0560 excluded** |
| R3 | MSURRAMT | **Gross** partial surrender from `TRANS_AMOUNT` |
| R4 | 1020 charge | **Reconciliation only** — do not reduce MSURRAMT unless QLAdmin expects net |
| R5 | 0090 payout | **Pairing/reconciliation only** — not emitted as QuikIsrr row |
| R6 | Terminated policies | **Include** historical partial surrenders before termination |
| R7 | MISWL | **PFNDR.VALUATION_DATE** — first on/after MSURRDATE; exception file if no match |
| R8 | Output path | **`QLA_Migration/Output/QuikIsrr.csv`** — not `Output/rates/` |
| R9 | Companion scope | **QuikIsrr-only** — no QuikClms/QuikClmp/QuikBenh in PR-7 |

---

## SME questions (approve / correct)

### Q1 — PACTG 561 as authoritative source

**Question:** Confirm that **PACTG debit code 561 / 0561** is the authoritative LifePRO source for QuikIsrr partial surrender rows.

**Evidence:** 3,688 debit rows (May 20260530 extract); claims catalog `PARTIAL_SURRENDER`; pairing `13|561` dominant.

**Recommended:** **APPROVE**

**SME:** ☐ APPROVE  ☐ CORRECT: ____________________

---

### Q2 — Exclude 560 full surrender

**Question:** Confirm that **560 / 0560** (Total Cash / full surrender) rows are **excluded** from QuikIsrr.

**Recommended:** **APPROVE** — QuikIsrr is partial surrender only.

**SME:** ☐ APPROVE  ☐ CORRECT: ____________________

---

### Q3 — MSURRAMT gross vs net

**Question:** Should **MSURRAMT** be the **gross** partial surrender amount, **net** withdrawal, or **amount after surrender charge**?

**Recommended:** **Gross** `TRANS_AMOUNT` on 561 debit row.

**SME:** ☐ GROSS  ☐ NET  ☐ AFTER 1020  ☐ OTHER: ____________________

---

### Q4 — 1020 surrender charge role

**Question:** Should **1020** surrender charge affect MSURRAMT, or be used **only for reconciliation**?

**Recommended:** **Reconciliation only** unless QLAdmin Help requires net withdrawal in MSURRAMT.

**SME:** ☐ RECONCILE ONLY  ☐ REDUCE MSURRAMT  ☐ OTHER: ____________________

---

### Q5 — 0090 payout rows

**Question:** Confirm **0090** payout rows are used **only for pairing/reconciliation**, not emitted as QuikIsrr rows.

**Recommended:** **APPROVE**

**Decision Review (2026-07-02):** **Resolved by evidence.** Fleet-wide 0090 = 20 rows, 0092 = 16 rows — payout legs do not live in the PACTG debit stream for these products. The actual accounting pair for 0561 is **credit code 0013 Surrender Clearing** (3,676 of 3,686 ISWL rows). 0090/0092 are neither emitted nor required.

**SME:** ☐ APPROVE  ☐ CORRECT: ____________________

---

### Q6 — 561 without payout-pairing codes

**Question:** Should **561 rows without approved payout-pairing codes** be **included** or **held**?

**Context:** **21 deferred chains / 5 policies** in claims governance (`SURRENDER_OFFSET_BLOCKED` — 561 only, no 1020/0560/0094/1900/0567):

| Policy | MPLAN | PACTG 561 rows (profile) |
|--------|-------|-------------------------:|
| 9010776027 | 1659C2 | 2 |
| 9010780411 | 1659CR | 11 |
| 9010780591 | 1659C2 | 8 |
| 9011072813 | 1659C2 | 8 |
| 9011107796 | 1659C2 | 9 |

**Profiling note:** Under provisional hold rules (no payout-pair codes on policy), **3,686 of 3,687** ISWL 561 rows are flagged deferred — only **1** row (`9010761882`, 20200825) has a payout-pair code present.

**Decision Review (2026-07-02):** **RETIRED as a hold criterion.** The payout-pair test was structurally unsatisfiable (fleet-wide 0090 = 20, 0092 = 16 rows) and not diagnostic of any defect — LifePRO pairs 0561 with credit 0013 Surrender Clearing instead. Eligibility is now driven by **`REVERSAL_CODE ≠ Y`** (see Q13). Governance policy dispositions moved to per-policy findings: 4 of 5 include-with-warning; `9010780411` held for manual review (Q14).

**SME:** ☐ ACKNOWLEDGE RETIREMENT  ☐ CORRECT: ____________________

---

### Q7 — MISWL derivation rule

**Question:** Confirm MISWL rule.

**Prior decision (2026-07-02):** PFNDR.VALUATION_DATE — first on/after MSURRDATE; exception file if no match. Readiness validation matched **99.83%** (3,617/3,623).

**REOPENED (narrowed) by late SME guidance:** the SME's QuikIsrr field list is **MPOLICY, MSURRDATE, MSURRAMT only — no MISWL**. Findings:

- QuikIsrr schema (Help §7.143, verified from PDF) **does** include MISWL D8 — "Monthiversary date the transaction was added to the UL/ISWL table".
- PFNDR is a **point-in-time snapshot** (one valuation date per policy, May 2026). The matched MISWL values are therefore 2026 snapshot dates on 2018–2025 events — **not** historical monthiversaries.
- Precedent: converted `Output/quikprmh.csv` **omits its MISWL column entirely** even though QuikPrmh schema (§7.191) defines it.

**Recommended:** emit QuikIsrr with **MISWL blank/omitted** (matches SME field list + QuikPrmh precedent); retire the PFNDR population rule (keep readiness artifacts as coverage evidence).

**SME:** ☐ MISWL BLANK/OMITTED (recommended)  ☐ PFNDR SNAPSHOT DATE (accept 2026 dates on historical events)  ☐ OTHER: ____________________

---

### Q8 — Terminated policies

**Question:** Include **terminated/surrendered** policies with historical partial surrender activity?

**Recommended:** **Yes** — QuikIsrr is event history for converted policies.

**Decision Review (2026-07-02):** **Resolved by evidence — INCLUDE.** `quikmstr.MSTATUS` join (639/639 matched): **349 policies (55%) are Active**, 209 Terminated/Death, 57 Surrendered, remainder minor statuses. The prior "~99.7% terminated" figure was a `TERM_REASON='P'` misread and is retracted. Zero 0561 rows occur on/after a policy's first 0560 full surrender — history always precedes termination.

**SME:** ☐ INCLUDE  ☐ ACTIVE ONLY  ☐ OTHER: ____________________

---

### Q9 — ISWL MPLAN scope

**Question:** Confirm QuikIsrr scope is limited to the same **8 ISWL MPLANs**:

`1658C1`, `1658CS`, `1659C2`, `1659CR`, `1659CS`, `1659SR`, `1669SR`, `1679CS`

**Recommended:** **APPROVE** (map via PACTG `PLAN_CODE` / coverage → MPLAN crosswalk).

**SME:** ☐ APPROVE  ☐ CORRECT: ____________________

---

### Q10 — Output location

**Question:** Confirm final output location.

**FINAL DECISION (2026-07-02):** **`QLA_Migration/Output/QuikIsrr.csv`** — policy-level transaction table; **not** under `Output/rates/`.

**Status:** **CLOSED**

**SME:** ☑ **APPROVED**  ☐ CORRECT: ____________________

---

### Q11 — Companion record scope

**Prior decision (2026-07-02):** QuikIsrr-only.

**REOPENED by late SME guidance:** SME states QLAdmin partial surrender processing adds **QuikClms, QuikClmp, QuikBene/QuikBenh ("QuikBenh for converted records"), QuikIsrr, and a transaction audit record**, with full field mappings supplied. Companion reconciliation already proved these records do **not** exist for the 3,623 events (0% coverage) — so if QLAdmin expects them for converted history, this pipeline must create them.

**Recommended:** **Option B — full package** (QuikClms + QuikClmp + QuikBenh + QuikIsrr; exclude audit per Q19). See [`Issue_34_Late_SME_Scope_Reconciliation.md`](Issue_34_Late_SME_Scope_Reconciliation.md) §B/§I.

**SME:** ☐ FULL PACKAGE (recommended)  ☐ QUIKISRR ONLY  ☐ STAGED (PR-7A QuikIsrr / PR-7B companions)  ☐ OTHER: ____________________

---

### Q15 — MPHASE on partial claim rows (NEW — 2026-07-02, late SME)

**Question:** Your seek rule says "for a partial, seek **policy + phase 0** in QuikClms", but the field list says `MPHASE = Phase`. Confirm converted partial QuikClms/QuikClmp rows carry **MPHASE = 0**.

**Evidence:** existing converted claims are all `MPHASE = 1, MSEQ = 0` (2,114 rows); 306 of the 636 candidate policies already have phase-1 death/full-surrender claims. Phase 0 avoids key collision and matches the seek rule.

**Recommended:** **MPHASE = 0.**

**SME:** ☐ PHASE 0  ☐ COVERAGE PHASE  ☐ OTHER: ____________________

---

### Q16 — ORIGSTATUS for historical partials (NEW — 2026-07-02, late SME)

**Question:** `ORIGSTATUS` = "policy status before processing surrender". The point-in-time status at each 2018–2025 event is not in the extracts (PPOLC/quikmstr hold current status only). What should converted rows carry?

**Recommended:** fixed premium-paying status code (converted quikmstr's dominant active code is `22`) or blank — SME to choose.

**SME:** ☐ FIXED ACTIVE CODE: ____  ☐ BLANK  ☐ CURRENT MSTATUS  ☐ OTHER: ____________________

---

### Q17 — Owner/payee exceptions (NEW — 2026-07-02, late SME)

**Question:** QuikClmp payee fields map from converted owner data (quikclid OWNR → quikclnt). Coverage: **634/636** policies direct; `010834096C` has insured-only (fallback per your guidance?); **`010826551C` has no OWNR or INSD link** (only SERV + BENP). Also **59 of 607** owner clients have blank/zero MTAXID.

**Recommended:** INSD fallback approved; `010826551C` → exception file; blank MTIN emitted as-is (consistent with existing death-claim payees).

**SME:** ☐ APPROVE ALL THREE  ☐ CORRECT: ____________________

---

### Q18 — QuikBenh coordination (NEW — 2026-07-02, late SME)

**Question:** No QuikBenh output exists in this repo; the client's Loyal2QL converter notes say quikbenh is populated **client-side** ("Benefit / dividend history — done"). If this pipeline emits `quikbenh.csv` rows (MBENTYP = 8, MDATE = processed date, MBEN = surrender amount), how do they merge with the client-side dividend history load?

**Recommended:** client loader **appends** this pipeline's benefit-type-8 rows; confirm with client before development.

**SME:** ☐ CLIENT APPENDS  ☐ THIS PIPELINE OWNS QUIKBENH  ☐ OTHER: ____________________

---

### Q19 — Transaction audit exclusion (NEW — 2026-07-02, late SME)

**Question:** QuikAudt (§7.41) stores user/date/time and a **memo of before/after policy images**. Authentic before/after images cannot be reproduced for historical events. Confirm the audit record is **excluded** from converted partial surrender history.

**Recommended:** **EXCLUDE.**

**SME:** ☐ EXCLUDE (recommended)  ☐ SYNTHESIZE AUDIT ROWS  ☐ OTHER: ____________________

---

### Q12 — Date semantics (NEW — 2026-07-02, sign-off)

**Question:** Confirm QuikIsrr "maintenance date" (SME comment 4) = LifePRO **`EFFECTIVE_DATE`** (event date), not `DATE_ADDED` (posting date). Reversal chains show reposts keep the original `EFFECTIVE_DATE` while `DATE_ADDED` moves.

**Recommended:** **EFFECTIVE_DATE.**

**SME:** ☐ EFFECTIVE_DATE  ☐ DATE_ADDED  ☐ OTHER: ____________________

---

### Q13 — Reversal exclusion (NEW — 2026-07-02, sign-off)

**Question:** Confirm exclusion of 0561 rows with **`REVERSAL_CODE = 'Y'`** (61 ISWL rows across 31 policies; `DATE_REVERSED`/`CODER_REVERSED` populated). 52 of 61 have a corrected repost on the policy. Consequence: policies `9010718278` and `9011035652` drop out entirely (their only rows are reversed with no repost).

**Recommended:** **EXCLUDE reversal-marked rows** — converting them would double-count withdrawals; QLAdmin has no user-level reversal process to clean them up post-load (SME comment 1).

**SME:** ☐ APPROVE  ☐ CORRECT: ____________________

---

### Q14 — Policy 9010780411 disposition (NEW — 2026-07-02, manual review)

**Question:** This governance policy has a defective 2018 chain: 7 reversed postings of the 2018-02-05 event, one repost with blank PLAN_CODE (2018-03-01), and an unreversed same-date pair 2018-03-20 (2 × $317.10, different control numbers). Which of the 3 unreversed rows (total $951.30) represent real events?

**Recommended:** **HOLD** all 3 rows in the review output; likely a single annual event booked multiple times.

**SME:** ☐ HOLD ALL  ☐ EMIT ONE  ☐ EMIT ALL  ☐ OTHER: ____________________

---

## Gate summary (updated 2026-07-02 — Late SME Scope Reconciliation)

| Gate | Status | Blocks development? |
|------|--------|:-------------------:|
| Q1–Q2 Source + exclude 560 | **CLOSED** | No |
| Q3–Q4 MSURRAMT / 1020 | **CLOSED** (gross / reconcile-only; SME reconfirmed "no adjustments" for partials) | No |
| Q5 0090 pairing | **CLOSED** | No |
| Q6 Deferred 561 | **Retired** | No |
| Q7 MISWL | **REOPENED (narrowed)** — blank/omitted (recommended) vs PFNDR snapshot | **Yes** |
| Q8 Terminated scope | **CLOSED** | No |
| Q9 MPLAN allowlist | **CLOSED** | No |
| Q10 Output path | **CLOSED** — `Output/QuikIsrr.csv` | No |
| Q11 Companion scope | **REOPENED** — full package (recommended) vs QuikIsrr-only vs staged | **Yes** |
| Q12 Date semantics | **CLOSED** — EFFECTIVE_DATE (maintenance); DATE_ADDED recommended for processed/system dates | No |
| Q13 Reversal exclusion | **CLOSED** | No |
| Q14 9010780411 | Manual hold | No |
| Q15 MPHASE = 0 on partials | **NEW — NEEDS SME** | **Yes** |
| Q16 ORIGSTATUS historical | **NEW — NEEDS SME** | **Yes** |
| Q17 Owner/payee exceptions | **NEW — NEEDS SME** | **Yes** (if full package) |
| Q18 QuikBenh coordination | **NEW — NEEDS SME/client** | **Yes** (if full package) |
| Q19 Audit exclusion | **NEW — NEEDS SME sign-off** | No (recommendation stands unless corrected) |
| PFNDR source readiness | **CLOSED** — file imported; 99.83% mechanical match; snapshot semantics feed Q7 | No |

**Development gate:** SME completes [`Issue_34_Final_SME_Signoff_Package.md`](Issue_34_Final_SME_Signoff_Package.md) Questions 1–7 → **READY FOR DEVELOPMENT**.

---

## Final sign-off package (2026-07-02)

**Primary SME action:** [`Issue_34_Final_SME_Signoff_Package.md`](Issue_34_Final_SME_Signoff_Package.md)

| Sign-off Q# | Maps to | Topic |
|-------------|---------|-------|
| 1 | Q11 | Full package scope |
| 2 | Q7 | MISWL blank/omitted |
| 3 | Q15 | MPHASE = 0 |
| 4 | Q16 | ORIGSTATUS |
| 5 | Q18 | QuikBenh create/coordinate |
| 6 | Q17 | Payee fallback |
| 7 | Q19 | Transaction audit exclusion |

Detailed question text, context, and recommended answers are in the sign-off package. This document retains full planning history for Q1–Q19.

---

## Profiling artifacts (2026-07-01)

| File | Purpose |
|------|---------|
| `output/QuikIsrr_Planning_Profile/quikisrr_pactg_561_profile_summary.json` | Fleet + ISWL counts, go/no-go |
| `output/QuikIsrr_Planning_Profile/quikisrr_pactg_561_iswl_candidates.csv` | ISWL-scoped 561 rows with flags |
| `output/QuikIsrr_Planning_Profile/quikisrr_pactg_561_deferred_review.csv` | Hold/review bucket |
| `output/QuikIsrr_Planning_Profile/quikisrr_pactg_561_rejected_full_surrender.csv` | 560 rows on ISWL policies (119) |
| `output/QuikIsrr_Planning_Profile/quikisrr_pactg_561_pairing_analysis.csv` | 561 pairing flags fleet-wide |

**Profiler script (planning only):** `Issue_Log_Items/Issue_34/tools/quikisrr_pactg_profile.py`

---

## Next action after SME

1. Complete approve/correct on [`Issue_34_Final_SME_Signoff_Package.md`](Issue_34_Final_SME_Signoff_Package.md) Questions 1–7.
2. Record answers in the sign-off record table and update [`Issue_34_Blockers.md`](Issue_34_Blockers.md).
3. If all gates close → issue PR-7 Development Agent prompt.
