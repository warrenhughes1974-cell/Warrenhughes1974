# Issue #34 — QuikIsrr Blockers

**Issue:** #34 — ISWL QuikIsrr (Partial Surrender)  
**Updated:** 2026-07-02 (PR-7 implementation complete)  
**Overall status:** **PR-7 COMPLETE — ready for review**

**Implementation:** [`Issue_34_PR7_QUIKISRR_Implementation_Notes.md`](Issue_34_PR7_QUIKISRR_Implementation_Notes.md)

**References:** [`Issue_34_Late_SME_Scope_Reconciliation.md`](Issue_34_Late_SME_Scope_Reconciliation.md) · [`Issue_34_QUIKISRR_Final_Decision_Closure.md`](Issue_34_QUIKISRR_Final_Decision_Closure.md) · [`Issue_34_QUIKISRR_Decision_Review.md`](Issue_34_QUIKISRR_Decision_Review.md) · [`Issue_34_QUIKISRR_Companion_Table_Reconciliation.md`](Issue_34_QUIKISRR_Companion_Table_Reconciliation.md) · [`Issue_34_QuikIsrr_SME_Questions.md`](Issue_34_QuikIsrr_SME_Questions.md) · [`Issue_34_QuikIsrr_Planning.md`](Issue_34_QuikIsrr_Planning.md)

---

## Blocking (SME confirmations required before PR-7 development)

**All closed** — SME sign-off approved; PR-7 implemented 2026-07-02.

## Source readiness (all CLOSED)

| # | Item | Status |
|---|------|--------|
| ~~B1~~ | PFNDR extract | **CLOSED** — `QLA_Migration/Source/PFNDR_FundHistory_Extract_20260530.csv` (6,237,062 bytes) |
| ~~B2~~ | PFNDR MISWL match validation | **CLOSED** — 99.83% mechanical match (3,617/3,623); 6 `ONLY_EARLIER` exceptions. **Semantic caveat:** matched dates are the May-2026 snapshot, not historical monthiversaries — feeds S2 |
| — | Owner/payee source (QuikClmp fields) | **CLOSED** — quikclid/quikclnt cover 634/636 policies direct + 1 INSD fallback; names/addresses 100% complete on owner clients |
| — | Claims infrastructure reuse | **CLOSED** — QuikClms/QuikClmp writers, schemas, DBF pipeline exist; zero phase-0 rows → sequence design clean |

## PFNDR readiness results (2026-07-02)

| Metric | Value |
|--------|------:|
| PFNDR rows | 2,327 (utf-8-sig; 1 dash header skipped) |
| Candidate rows | 3,623 / 636 policies / $1,217,593.55 ✓ |
| Matched (mechanical) | **3,617** (99.83%) |
| Unmatched (`ONLY_EARLIER`) | **6** |
| Policies with no PFNDR history | **0** |
| Duplicate PFNDR ties | **0** |

**Artifacts:** `output/QuikIsrr_PFNDR_Readiness/quikisrr_pfndr_readiness_summary.json`, `_matches.csv`, `_unmatched.csv`, `_policy_coverage.csv`

## Closed business decisions (unchanged by late SME guidance)

| Item | Final decision |
|------|----------------|
| Candidate rule | PACTG 0561, 8 ISWL MPLANs, `REVERSAL_CODE ≠ Y`, exclude 9010780411 → **3,623 / 636 / $1,217,593.55** |
| MSURRDATE | `EFFECTIVE_DATE` (maintenance date) |
| MSURRAMT | Gross `TRANS_AMOUNT` — SME reconfirmed: partials have no adjustments; all amounts identical |
| Q10 Output path | **`QLA_Migration/Output/QuikIsrr.csv`** (not `Output/rates/`) |
| Processed/system date | Recommend `DATE_ADDED` (never blank; historical 2018–2026) — not conversion run date |
| Q1–Q5, Q8, Q9, Q12, Q13 | **Closed** — see Final Decision Closure §A |

## Reopened by late SME guidance

| Item | Was | Now |
|------|-----|-----|
| Q11 Companion scope | CLOSED — QuikIsrr-only | **REOPENED (S1)** — SME field guidance implies full package for converted records |
| Q7 MISWL | CLOSED — PFNDR.VALUATION_DATE | **NARROWED (S2)** — SME omits MISWL; PFNDR value semantically questionable; recommend blank |

## Non-blocking (tracked)

| # | Item | Detail |
|---|------|--------|
| N1 | **Q14 — Policy 9010780411** | 3 rows ($951.30) on manual hold — isolated from 636-policy emit |
| N2 | Backdated postings | 41 fleet 0561 rows have `DATE_ADDED < EFFECTIVE_DATE` — validation flag only |
| N3 | Credit codes 12/126 on 0561 | 10 rows — development validation flag only |

## Retired blockers

| Item | Resolution |
|------|-----------|
| PFNDR source availability | **Closed 2026-07-02** — file imported and profiled |
| PFNDR historical depth risk | **Closed** — validated; snapshot nature documented (feeds S2) |
| Q10 output path | **Closed** — `Output/QuikIsrr.csv` |
| Payout-pair requirement | Retired 2026-07-02 |
| Terminated-policy hold | Resolved 2026-07-02 |
| PACTG availability | Resolved 2026-07-01 |

---

## Approved conversion rule (candidate set — FINAL, unchanged)

Eligible set: **3,626 rows / 637 policies / $1,218,544.85** (ISWL 0561, `REVERSAL_CODE ≠ Y`), minus **9010780411** hold (3 rows) → **3,623 rows / 636 policies / $1,217,593.55** candidate population.

Full rule: [`Issue_34_QUIKISRR_Final_Decision_Closure.md`](Issue_34_QUIKISRR_Final_Decision_Closure.md) §B. Revised table scope: [`Issue_34_Late_SME_Scope_Reconciliation.md`](Issue_34_Late_SME_Scope_Reconciliation.md) §I.

**Status:** **PR-7 COMPLETE — ready for review.** Validator V-ISRR-01..22 pass; Issue #31–#33 regression pass (full run).
