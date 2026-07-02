# Issue #34 — QUIKISRR Final Decision Closure

**Issue:** #34 — ISWL QuikIsrr (Partial Surrender)  
**Date:** 2026-07-02  
**Mode:** Final decision documentation + PFNDR readiness validation — **no development**  
**Final recommendation:** ~~READY FOR DEVELOPMENT~~ **SUPERSEDED — READY AFTER SME CONFIRMATION**

> **SUPERSEDED 2026-07-02 (Late SME Scope Reconciliation):** after this closure was written, the SME provided field-level guidance showing QLAdmin partial surrender processing creates **QuikClms + QuikClmp + QuikBenh (converted records) + QuikIsrr (+ audit)**. Decision #1 (QuikIsrr-only) is **reopened**, and Decision #2 (MISWL = PFNDR) is **narrowed** — the SME field list omits MISWL and the PFNDR-matched values are 2026 snapshot dates, not historical monthiversaries. The candidate rule, population (3,623 / 636 / $1,217,593.55), amounts, dates, and output path are **unchanged**. Authoritative current status: [`Issue_34_Late_SME_Scope_Reconciliation.md`](Issue_34_Late_SME_Scope_Reconciliation.md).

---

## A. Final decision summary

All business decisions below are **FINAL** and approved for PR-7 planning. PFNDR MISWL validation **complete** (2026-07-02); PR-7 Development Agent prompt may be issued when requested.

| # | Topic | Final decision | Status |
|---|-------|----------------|--------|
| 1 | Companion record scope | ~~QuikIsrr only~~ — **REOPENED** by late SME guidance (full package recommended; see Late SME Scope Reconciliation §B) | **REOPENED** |
| 2 | MISWL | ~~PFNDR.VALUATION_DATE~~ — **NARROWED**: SME field list omits MISWL; PFNDR values are 2026 snapshot dates. Recommend blank/omitted (QuikPrmh precedent). | **REOPENED (narrowed)** |
| 3 | Output location | **`QLA_Migration/Output/QuikIsrr.csv`** — policy-level transaction table; **not** under `Output/rates/`. | **CLOSED** |
| 4 | Source | **PACTG debit 0561 / 561** = authoritative QuikIsrr source. | **CLOSED** |
| 5 | Exclusions | 0560, 1020, 0090/0092 as source rows; `REVERSAL_CODE = Y`; manual hold **9010780411**. | **CLOSED** |
| 6 | Terminated policies | **Include** all eligible historical 0561 regardless of current policy status. | **CLOSED** |
| 7 | Amount | **MSURRAMT = gross PACTG TRANS_AMOUNT** — do not net surrender charges. | **CLOSED** |
| 8 | Date | **MSURRDATE = PACTG EFFECTIVE_DATE**. | **CLOSED** |
| 9 | MPLAN scope | 8 ISWL MPLANs: `1658C1`, `1658CS`, `1659C2`, `1659CR`, `1659CS`, `1659SR`, `1669SR`, `1679CS`. | **CLOSED** |

**Prior open questions resolved:**

| Question | Resolution |
|----------|------------|
| Q11 Companion scope | **QuikIsrr-only** — companion reconciliation (2026-07-02) proved 0% event-level coverage; SME chose Option 1 |
| Q7 MISWL | **PFNDR.VALUATION_DATE** (not issue-date derivation) |
| Q10 Output path | **`QLA_Migration/Output/QuikIsrr.csv`** |
| Q6 Payout-pair hold | **Retired** |
| Q8 Terminated | **Include** |

---

## B. Updated conversion rule (PR-7 authoritative)

```text
QUIKISRR emit candidate =
      PACTG row
  AND DEBIT_CODE (normalized) = 561
  AND PLAN_CODE (or PRODUCT_ID fallback, logged) maps to ISWL MPLAN allowlist:
        1658C1, 1658CS, 1659C2, 1659CR, 1659CS, 1659SR, 1669SR, 1679CS
  AND REVERSAL_CODE <> 'Y'
  AND POLICY_NUMBER NOT IN manual hold list: {9010780411}

Field mapping:
  MPOLICY   = POLICY_NUMBER -> QLAdmin key (strip leading 9, append 'C')
  MSURRDATE = EFFECTIVE_DATE (YYYYMMDD)
  MSURRAMT  = TRANS_AMOUNT (gross, N10.2)
  MISWL     = MIN(PFNDR.VALUATION_DATE WHERE VALUATION_DATE >= MSURRDATE)
              for same POLICY_NUMBER + base ISWL benefit scope
              -> if no PFNDR match: route to exception file (do NOT emit; do NOT estimate)

Output:
  QLA_Migration/Output/QuikIsrr.csv          (matched rows)
  QLA_Migration/Validation/ or Reports/      (PFNDR exception / hold review — path TBD at PR-7)

PR-7 scope:
  QuikIsrr ONLY — no QuikClms, QuikClmp, QuikBenh, QuikBene, transaction audit
```

### Expected main emit population (before PFNDR exception handling)

| Metric | Value |
|--------|------:|
| Rows | **3,623** |
| Policies | **636** |
| Gross amount | **$1,217,593.55** |

Composition: ISWL PACTG 0561, minus `REVERSAL_CODE = Y` (61 rows excluded upstream), minus **9010780411** hold (3 rows). Independently verified by companion reconciliation (2026-07-02).

**Post-PFNDR emit count:** **~3,617** main emit rows (6 `ONLY_EARLIER` exceptions routed to PFNDR exception file). Hold policy **9010780411** (3 rows) excluded from candidate set.

---

## C. PFNDR availability check

| Attribute | Value |
|-----------|-------|
| **Path** | `QLA_Migration/Source/PFNDR_FundHistory_Extract_20260530.csv` |
| **Status** | **FOUND** (2026-07-02 PFNDR Readiness Agent) |
| **Size** | 6,237,062 bytes |
| **Encoding** | utf-8-sig |
| **Row count** | **2,327** data rows (1 dash header skipped) |
| **Column count** | **41** |

### Structure summary

| Field | Column | Notes |
|-------|--------|-------|
| Policy key | `POLICY_NUMBER` | 0 blank values |
| Benefit sequence | `BENEFIT_SEQ` | Present |
| Valuation date | `VALUATION_DATE` | YYYYMMDD; 0 blank values |
| Other date fields | `END_OF_TERM_DATE` | Not used for MISWL |
| Duplicate keys | `(POLICY_NUMBER, BENEFIT_SEQ, VALUATION_DATE, …)` | **0** duplicate key rows |

**Note:** PFNDR is **not** listed in `docs/LIFEPRO_SOURCE_FILES.txt` as a standard batch-table dependency — it is **QuikIsrr-specific** for MISWL population only.

**Validation script:** `Issue_Log_Items/Issue_34/tools/quikisrr_pfndr_readiness.py`

---

## D. PFNDR match results

**Completed 2026-07-02** — candidate population rebuilt from PACTG; MISWL join per approved rule.

### Candidate population confirmation

| Metric | Rebuilt | Expected | Match |
|--------|--------:|---------:|:-----:|
| Rows | 3,623 | 3,623 | ✓ |
| Policies | 636 | 636 | ✓ |
| Gross amount | $1,217,593.55 | $1,217,593.55 | ✓ |

### Match summary

| Metric | Value |
|--------|------:|
| PFNDR matched rows | **3,617** |
| PFNDR unmatched rows | **6** |
| Match rate | **99.83%** |
| Matched policies | **636** |
| Unmatched policies | **0** |
| Only earlier PFNDR dates (`ONLY_EARLIER`) | **6** |
| No PFNDR policy history | **0** |
| Duplicate PFNDR tie candidates | **0** |

### MISWL validation (matched rows)

| Check | Result |
|-------|--------|
| MISWL >= MSURRDATE | **100%** |
| MISWL from PFNDR.VALUATION_DATE only | **Yes** |
| One selected PFNDR row per candidate | **Yes** |
| No estimated dates | **Yes** |

**MISWL date distribution note:** Most matched rows select May 2026 valuation dates (extract snapshot month). Each policy typically has one PFNDR valuation date; events with MSURRDATE after that date fail the `>= MSURRDATE` rule.

### Six exception rows (`ONLY_EARLIER`)

| Policy | MSURRDATE | Issue |
|--------|-----------|-------|
| 9010759932 | 20220818 | PFNDR valuation predates event |
| 9010761882 | 20200825 | PFNDR valuation predates event |
| 9010764812 | 20231004 | PFNDR valuation predates event |
| 9010825438 | 20230227 | PFNDR valuation predates event |
| 9010941103 | 20220915 | PFNDR valuation predates event |
| 9011039701 | 20230523 | PFNDR valuation predates event |

Per approved rule: route to PFNDR exception file; **do not estimate** MISWL from issue date.

### Artifacts

| File | Rows |
|------|-----:|
| `output/QuikIsrr_PFNDR_Readiness/quikisrr_pfndr_readiness_summary.json` | — |
| `quikisrr_pfndr_matches.csv` | 3,617 |
| `quikisrr_pfndr_unmatched.csv` | 6 |
| `quikisrr_pfndr_duplicate_candidates.csv` | 0 |
| `quikisrr_pfndr_policy_coverage.csv` | 636 |

---

## E. Remaining blockers

| # | Item | Type | Status |
|---|------|------|--------|
| ~~E1~~ | PFNDR extract | Source | **CLOSED** — file present |
| ~~E2~~ | PFNDR readiness profile | Validation | **CLOSED** — 99.83% match |
| N1 | Policy **9010780411** hold | Manual review | 3 rows ($951.30) — non-blocking |
| N2 | 6 `ONLY_EARLIER` exceptions | PR-7 exception file | Route to PFNDR exception output; no SME decision required unless client rejects exception handling |

**Retired blockers:** Q11 companion scope, Q10 output path, Q7 MISWL rule definition, payout-pair hold, terminated-policy hold, PACTG availability, PFNDR source availability, PFNDR historical depth risk (validated acceptable).

---

## F. Updated documentation list

| Document | Change |
|----------|--------|
| `Issue_34_QUIKISRR_Final_Decision_Closure.md` | **New** — this document |
| `Issue_34_QUIKISRR_Decision_Review.md` | Updated — final decisions incorporated; status |
| `Issue_34_QuikIsrr_Planning.md` | Updated — final rule, output path, PFNDR gate |
| `Issue_34_QuikIsrr_SME_Questions.md` | Updated — Q7/Q10/Q11 marked CLOSED with final answers |
| `Issue_34_Blockers.md` | Updated — PFNDR closed; READY FOR DEVELOPMENT |
| `Issue_34_QUIKISRR_Companion_Table_Reconciliation.md` | Unchanged (supports Q11 closure) |
| `output/QuikIsrr_PFNDR_Readiness/quikisrr_pfndr_readiness_summary.json` | Updated — availability true, match results |
| `output/QuikIsrr_PFNDR_Readiness/quikisrr_pfndr_matches.csv` | New — 3,617 matched rows |
| `output/QuikIsrr_PFNDR_Readiness/quikisrr_pfndr_unmatched.csv` | New — 6 exception rows |
| `output/QuikIsrr_PFNDR_Readiness/quikisrr_pfndr_policy_coverage.csv` | New — 636 policies |
| `tools/quikisrr_pfndr_readiness.py` | New — readiness validation script |

---

## G. Final recommendation

## ~~READY FOR DEVELOPMENT~~ — **SUPERSEDED: READY AFTER SME CONFIRMATION**

This recommendation stood for less than a day: late SME field-level guidance (2026-07-02) reopened companion scope (Q11 → full package recommended) and MISWL semantics (Q7 → blank/omitted recommended). See [`Issue_34_Late_SME_Scope_Reconciliation.md`](Issue_34_Late_SME_Scope_Reconciliation.md) for the current gate list (S1–S7) and revised implementation approach.

Facts from this closure that remain authoritative:

1. Candidate set: **3,623 rows / 636 policies / $1,217,593.55** (rebuilt and verified twice)
2. PFNDR source coverage: **99.83%** mechanical match; 6 `ONLY_EARLIER` exceptions; 0 policies without PFNDR history
3. Manual hold: **9010780411** (3 rows) — excluded from candidate set
4. Output path: `QLA_Migration/Output/QuikIsrr.csv`

**Do NOT** create QuikIsrr.csv, loaders, validators, or PR-7 development work until S1–S7 are answered and a Development Agent prompt is issued.
