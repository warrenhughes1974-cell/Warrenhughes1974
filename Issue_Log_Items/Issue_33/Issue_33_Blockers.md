# Issue #33 — QUIKISSC Blockers

**Issue:** #33 — ISWL Phase 6 QUIKISSC  
**Date:** 2026-06-28  
**Mode:** Planning only

---

## Blocker classification key

| Label | Meaning |
|-------|---------|
| **CONFIRMED** | Proven with hierarchy + source evidence |
| **STRONG EVIDENCE** | Multiple independent sources align; SME ack pending |
| **CORRELATION ONLY** | Numeric/type overlap without segment proof |
| **BLOCKED** | Cannot proceed without resolution |
| **NEEDS SME** | Business decision or client confirmation required |
| **IMPLEMENTATION READY** | Gate closed; dev may proceed |

---

## Blocker register

| ID | Finding | Classification | Impact | Resolution path |
|----|---------|----------------|--------|-----------------|
| B-01 | SR/SL on PSEGT 8/8 ISWL coverages via `659 CEN II` | **STRONG EVIDENCE** | Defines segment path | SME Q1 — confirm SR/SL authority |
| B-02 | U7/U8 absent (0/8) | **CONFIRMED** | Legacy fallback not needed | Document only |
| B-03 | TP/TX not surrender (tax data) | **CONFIRMED** | Removes 21,908-row false path | SME Q7 ack |
| B-04 | No PAAGERAT SR/SL/SC/ISSC | **CONFIRMED** | Loader ≠ COI/GCOI pattern | Use duration grid loader |
| B-05 | PSEGT SL payload → `OSLNS00XT` pointer | **STRONG EVIDENCE** | Rate join key candidate | Decode + SME Q2 |
| B-06 | Rate_Table SL 14 rows on hub | **CORRELATION ONLY** | Schedule shape known | Prove via B-05; SME Q3 |
| B-07 | PDAGE SL all zero on hub | **CONFIRMED** | PDAGE not authoritative | Do not emit from PDAGE SL |
| B-08 | QuikIssc schema (Help §7.144) | **CONFIRMED** | Target fields known | Map after rate proof |
| B-09 | Percent format (100 vs 1.0) | **NEEDS SME** | Wrong values if misinterpreted | SME Q4 |
| B-10 | Gender/UW/age dimensional scope | **NEEDS SME** | Row count 8 vs 64+ | SME Q5 |
| B-11 | Shared schedule all 8 MPLANs | **NEEDS SME** | Replication vs per-plan | SME Q6 |
| B-12 | SR→SL PCOVRSGT slot mapping | **NEEDS SME** | Parent/child proof incomplete | SME Q3 |
| B-13 | Policy validation fields untraced | **CORRELATION ONLY** | Post-emit reconcile gap | SME Q8 + sample policies |
| B-14 | SCHG15–20 beyond 14 durations | **NEEDS SME** | Trailing columns blank? | SME Q9 |
| B-15 | PPRDF not in repo | **CONFIRMED** non-blocking | Top hierarchy optional | Accept PCOMP start |
| B-16 | Reference QuikIssc DBF absent | **BLOCKED** for UAT parity | Cannot golden-test | Client Q11 |
| B-17 | Phase 1–5 regression coupling | **IMPLEMENTATION READY** | Must not break prior phases | V-ISSC regression gate |

---

## Critical path (must close before development)

```text
B-05 + B-06 + B-12  →  Prove SR → SL → rate table linkage
        ↓
B-09 + B-10 + B-11  →  SME dimensional + format decisions
        ↓
B-08                →  Field mapping sign-off
        ↓
Development Agent PR-6
```

---

## Withdrawn / closed false paths

| Former candidate | Status | Reason |
|------------------|--------|--------|
| PDAGE TP/TX | **CLOSED — excluded** | Tax valuation/reserve |
| PAAGERAT any type | **CLOSED — excluded** | No surrender TYPE_CODE |
| U7/U8 segments | **CLOSED — absent** | Not in PSEGT for ISWL |
| Rate_Table SL without segment proof | **BLOCKED** | TYPE_CODE-only mapping forbidden |

---

## Overall readiness

| Area | Status |
|------|--------|
| Hierarchy (SR/SL) | **CONFIRMED** (forensic + SME) |
| Rate schedule | **CONFIRMED** (Rate_Table SL hub, 14 durations) |
| QLAdmin schema | **CONFIRMED** |
| SME gates | **CLOSED** |
| Development (PR-6) | **COMPLETE — APPROVED** (2026-07-01) |

**Epic status:** **CLOSED — APPROVED.** PR-6 QUIKISSC is final authority for full surrender charges. See [`Issue_33_PR6_Closure_Report.md`](Issue_33_PR6_Closure_Report.md). Remaining ISWL work (QuikIsrr, Expenses) is out of Issue #33 scope.
