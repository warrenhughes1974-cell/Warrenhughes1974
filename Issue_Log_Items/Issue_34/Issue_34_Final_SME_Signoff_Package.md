# Issue #34 — Final SME Sign-Off Package (PR-7 Partial Surrender)

**Issue:** #34 — ISWL QuikIsrr / Partial Surrender History  
**Date:** 2026-07-02  
**Mode:** Final SME gate closure — **no development**  
**Purpose:** Concise approve/correct package for PR-7 scope and field rules  
**Audience:** Conversion Lead / QLAdmin SME  
**Final recommendation:** **READY AFTER SME CONFIRMATION** (see §I)

**Supporting analysis:** [`Issue_34_Late_SME_Scope_Reconciliation.md`](Issue_34_Late_SME_Scope_Reconciliation.md) · [`Issue_34_QUIKISRR_Companion_Table_Reconciliation.md`](Issue_34_QUIKISRR_Companion_Table_Reconciliation.md) · [`Issue_34_QuikIsrr_SME_Questions.md`](Issue_34_QuikIsrr_SME_Questions.md)

---

## A. Executive summary

Issue #34 converts ISWL partial surrender history from LifePRO PACTG 0561 accounting into QLAdmin. Planning, profiling, companion reconciliation, and PFNDR readiness are complete. The **candidate population rule is stable** (3,623 rows / 636 policies / $1,217,593.55).

Late SME field-level guidance changed the likely PR-7 scope from **QuikIsrr-only** to a **full converted partial surrender package**:

| Table | Role |
|-------|------|
| **QuikClms** | Claim header (CLAIMSTAT 99, CAUSE SRR) |
| **QuikClmp** | Payee/payment detail |
| **QuikBenh** | Benefit history (MBENTYP 8) for converted records |
| **QuikIsrr** | Partial surrender transaction history |
| ~~Transaction audit~~ | **Excluded** from PR-7 (recommendation) |

**Seven questions** below require SME approve/correct before PR-7 development may begin. All source data is present; no technical blockers remain.

---

## B. Stable candidate rule

```text
PR-7 candidate row =
      PACTG row
  AND DEBIT_CODE (normalized) = 561
  AND policy maps to ISWL MPLAN allowlist:
        1658C1, 1658CS, 1659C2, 1659CR, 1659CS, 1659SR, 1669SR, 1679CS
  AND REVERSAL_CODE <> 'Y'
  AND POLICY_NUMBER <> 9010780411   (manual hold — separate review)
```

**Independently verified** by planning profiler, decision review, companion reconciliation, and PFNDR readiness pass.

---

## C. Expected population

| Metric | Value |
|--------|------:|
| Rows | **3,623** |
| Policies | **636** |
| Gross amount | **$1,217,593.55** |

**Excluded upstream:** 61 reversed rows (`REVERSAL_CODE = Y`); 3 rows on hold policy **9010780411** ($951.30).

**If full package approved:** expect **~3,623 new rows** in each of QuikClms, QuikClmp, QuikBenh, and QuikIsrr (minus payee exceptions — see Question 6).

---

## D. Final SME questions

Each item: **☐ APPROVE (recommended)** or **☐ CORRECT** (state alternative).

---

### Question 1 — Full package scope (maps to Q11)

**For converted historical partial surrenders, should PR-7 create the full package?**

- QuikClms  
- QuikClmp  
- QuikBenh  
- QuikIsrr  

**Context:** Companion reconciliation proved **0% event-level coverage** — none of these records exist today for the 3,623 PACTG 0561 events. Late SME guidance describes QLAdmin live processing as creating all four tables for converted records.

| | |
|---|---|
| **Recommended** | **YES** — full package, **excluding transaction audit** |
| **SME** | ☐ **APPROVE**  ☐ **CORRECT:** _________________________________ |

---

### Question 2 — MISWL (maps to Q7)

**Should QuikIsrr.MISWL be left blank/omitted for converted records?**

**Context:**

- Late SME QuikIsrr field list: MPOLICY, MSURRDATE, MSURRAMT only — **no MISWL**.
- QLAdmin Help §7.143 defines MISWL, but converted `quikprmh.csv` **omits its MISWL column** despite schema definition.
- PFNDR is a **May 2026 snapshot** (one valuation date per policy). A mechanical 99.83% match assigns 2026 dates to 2018–2025 events — **not** historical monthiversaries.

| | |
|---|---|
| **Recommended** | **Leave MISWL blank/omitted. Do not use PFNDR.** |
| **SME** | ☐ **APPROVE**  ☐ **CORRECT:** _________________________________ |

---

### Question 3 — MPHASE (maps to Q15)

**Should converted partial surrender QuikClms/QuikClmp records use MPHASE = 0?**

**Context:** SME seek rule: "for a partial, seek **policy + phase 0** in QuikClms; find max sequence; add 1." Existing converted claims are all `MPHASE = 1, MSEQ = 0` — no phase-0 rows, so no key collision.

| | |
|---|---|
| **Recommended** | **YES — MPHASE = 0** on partial surrender claim/payment rows |
| **SME** | ☐ **APPROVE**  ☐ **CORRECT:** _________________________________ |

---

### Question 4 — ORIGSTATUS (maps to Q16)

**How should QuikClms.ORIGSTATUS be populated when historical point-in-time policy status before the surrender is unavailable?**

**Context:** Extracts and converted quikmstr hold **current** status only, not status at each 2018–2025 event date.

| | |
|---|---|
| **Recommended** | Use **best available converted policy status** (`quikmstr.MSTATUS`) if schema requires a value; otherwise **leave blank/default**. Document that point-in-time historical status is unavailable. |
| **SME** | ☐ **APPROVE**  ☐ **CORRECT:** _________________________________ |

---

### Question 5 — QuikBenh coordination (maps to Q18)

**Should PR-7 create QuikBenh records for converted partial surrender history?**

**Context:** SME said "for converted records, use QuikBenh" (MBENTYP 8, MDATE = processed date, MBEN = surrender amount). No QuikBenh output exists in this repo for these events. Client Loyal2QL converter notes say quikbenh is populated client-side for dividend history — **cannot be verified from this workspace**.

| | |
|---|---|
| **Recommended** | **YES** — PR-7 creates QuikBenh for the 3,623 converted partial surrender events **unless** client-side QuikBenh coverage is confirmed and provided before development |
| **SME** | ☐ **APPROVE**  ☐ **CORRECT:** _________________________________ |

---

### Question 6 — Owner / payee exceptions (maps to Q17)

**Confirm fallback logic for QuikClmp payee fields (MPAYNAME, MPAYADDR*, MPAYCITY/ST/ZIP, MTIN).**

| Step | Rule |
|------|------|
| 1 | Use **owner** (quikclid `MRELATION = OWNR` → quikclnt) when available — **634 / 636 policies** |
| 2 | If no owner, use **primary insured** (`MRELATION = INSD`) — **1 policy** |
| 3 | If neither owner nor primary insured, **hold row in exception file** — **1 policy** |

**Known exceptions:**

| Policy | Issue |
|--------|-------|
| `010826551C` | No OWNR or INSD link (only SERV + BENP) → exception file |
| `010834096C` | Insured-only (client 602820) → INSD fallback |

**Additional note:** 59 of 607 owner clients have blank/zero MTIN — emit as-is (consistent with existing death-claim payees) unless corrected.

| | |
|---|---|
| **Recommended** | **APPROVE** fallback chain above |
| **SME** | ☐ **APPROVE**  ☐ **CORRECT:** _________________________________ |

---

### Question 7 — Transaction audit (maps to Q19)

**Should PR-7 create transaction audit (QuikAudt) records?**

**Context:** QuikAudt (§7.41) stores user/date/time and a **memo of before/after policy images**. Authentic before/after images cannot be reproduced for historical events.

| | |
|---|---|
| **Recommended** | **NO** — exclude transaction audit from PR-7. If needed later, handle as a separate audit-history issue. |
| **SME** | ☐ **APPROVE**  ☐ **CORRECT:** _________________________________ |

---

## E. Recommended answers (summary)

| # | Topic | Recommended answer |
|---|-------|-------------------|
| 1 | Full package scope | **YES** — QuikClms + QuikClmp + QuikBenh + QuikIsrr; no audit |
| 2 | MISWL | **Blank/omitted** — do not use PFNDR |
| 3 | MPHASE | **0** on partial claim/payment rows |
| 4 | ORIGSTATUS | **Current quikmstr.MSTATUS** if required; else blank — document limitation |
| 5 | QuikBenh | **YES** — PR-7 creates unless client-side coverage confirmed |
| 6 | Payee fallback | **Owner → insured → exception file** |
| 7 | Transaction audit | **NO** — exclude from PR-7 |

### Stable field rules (already closed — no SME action required)

| Rule | Value |
|------|-------|
| All surrender amount fields | Same gross **PACTG 0561 TRANS_AMOUNT** → MFACE, MPAID, MAMOUNT, MGROSS, MBEN, MSURRAMT |
| Maintenance date | **PACTG.EFFECTIVE_DATE** → MSURRDATE, DTOFDEATH, RPTDATE |
| Processed/system date | **PACTG.DATE_ADDED** → PDDATE, ACCPTDATE, MPMTDATE, QuikBenh MDATE |
| QuikClms fixed values | CLAIMSTAT **99**, CAUSE **SRR** |
| QuikClmp fixed values | MHDPMT **C**, MHDCODE blank, MBANKNO blank, taxes/hold **0.00** |
| QuikBenh fixed values | MBENTYP **8** |
| Claim sequence | MSEQ **1, 2, 3…** per policy, ordered by EFFECTIVE_DATE; seek policy + phase 0 |
| Output path | **`QLA_Migration/Output/QuikIsrr.csv`** (+ append to existing quikclms/quikclmp; new quikbenh) |
| Manual hold | **9010780411** — 3 rows excluded from main emit |

---

## F. Impact of approval (if all seven questions approved as recommended)

| Area | Impact |
|------|--------|
| **PR-7 scope** | Four-table emit (~3,623 rows each) + exception files |
| **QuikClms/QuikClmp** | Append ~3,623 phase-0 partial-surrender rows to existing 2,114 / 1,709-row outputs; reuse claims pipeline formatting, validation, DBF generation |
| **QuikBenh** | New emit in this repo (`quikbenh.csv`); must coordinate with client-side dividend history load (append, not replace) |
| **QuikIsrr** | New policy-table emit; MISWL column omitted |
| **Exception outputs** | 9010780411 hold (3 rows); `010826551C` payee exception (policy-level row count TBD); PFNDR exception file **retired** (MISWL not populated) |
| **Regression risk** | Isolated append to claims outputs; QuikIssc and rate tables unaffected |
| **Status upgrade** | All S1–S7 gates close → **READY FOR DEVELOPMENT** |

---

## G. Impact if corrected

| If SME corrects… | Impact |
|------------------|--------|
| **QuikIsrr-only** (Q1) | PR-7 shrinks to one table (~3,623 rows); companion records remain absent; QLAdmin claim seek on phase 0 will find no partial history |
| **PFNDR for MISWL** (Q2) | Reinstates PFNDR join; 6 `ONLY_EARLIER` exceptions; most rows get May-2026 snapshot dates on historical events |
| **MPHASE ≠ 0** (Q3) | Sequence seek rule and key collision with existing phase-1 claims must be redesigned |
| **Point-in-time ORIGSTATUS** (Q4) | Requires new source research or derivation logic — potential blocker |
| **No QuikBenh from this pipeline** (Q5) | QuikBenh rows absent unless client provides; benefit-type-8 history gap |
| **Different payee fallback** (Q6) | Exception population and QuikClmp derivation rules change |
| **Include transaction audit** (Q7) | New scope — QuikAudt synthesis rules needed; likely separate issue |

Any correction that changes Q1 or Q2 should trigger a brief replan before PR-7 development prompt.

---

## H. Remaining blockers

| # | Gate | Maps to | Status |
|---|------|---------|--------|
| S1 | Full package scope | Q11 / Question 1 | **AWAITING SME** |
| S2 | MISWL blank/omitted | Q7 / Question 2 | **AWAITING SME** |
| S3 | MPHASE = 0 | Q15 / Question 3 | **AWAITING SME** |
| S4 | ORIGSTATUS rule | Q16 / Question 4 | **AWAITING SME** |
| S5 | QuikBenh create/coordinate | Q18 / Question 5 | **AWAITING SME** |
| S6 | Payee fallback | Q17 / Question 6 | **AWAITING SME** |
| S7 | Audit exclusion | Q19 / Question 7 | **AWAITING SME** |

**Not blocking:** candidate rule, population counts, PACTG/PFNDR/owner source availability, claims infrastructure, amount/date semantics (Q1–Q6, Q8–Q14 closed).

**Non-blocking tracked:** Q14 manual hold on 9010780411; 41 backdated DATE_ADDED rows; 59 blank/zero owner TINs.

---

## I. Final recommendation

## **READY AFTER SME CONFIRMATION**

All planning, profiling, companion reconciliation, and source validation are **complete**. The candidate rule and population are **stable**. PR-7 scope and seven field-level decisions are **documented with recommended answers** in this package.

**Path to READY FOR DEVELOPMENT:**

1. SME completes approve/correct on Questions 1–7 (§D).
2. Conversion Lead records answers in [`Issue_34_QuikIsrr_SME_Questions.md`](Issue_34_QuikIsrr_SME_Questions.md) and updates [`Issue_34_Blockers.md`](Issue_34_Blockers.md).
3. If all gates close as recommended → issue PR-7 Development Agent prompt.

**Do NOT** create QuikIsrr.csv, loaders, validators, or begin PR-7 development until SME sign-off is recorded.

---

## SME sign-off record

| Question | SME response | Initials | Date |
|----------|--------------|----------|------|
| 1 — Full package | ☐ Approve  ☐ Correct: _________ | | |
| 2 — MISWL | ☐ Approve  ☐ Correct: _________ | | |
| 3 — MPHASE | ☐ Approve  ☐ Correct: _________ | | |
| 4 — ORIGSTATUS | ☐ Approve  ☐ Correct: _________ | | |
| 5 — QuikBenh | ☐ Approve  ☐ Correct: _________ | | |
| 6 — Payee fallback | ☐ Approve  ☐ Correct: _________ | | |
| 7 — Transaction audit | ☐ Approve  ☐ Correct: _________ | | |

**Signed:** _____________________________  **Date:** _____________
