# Issue #40 — Dependency Gate

**Issue:** #40 — Inherited Cash Value Rate Load (fleet-wide, including `17085M`)  
**Framework stage:** Dependency Gate (G2) — PASS  
**Date:** 2026-07-06  
**Planning reference:** `Issue_40_Planning_Report.md`
**Approval update:** Client / actuarial approval provided by Warren on 2026-07-06 for the documented CV inheritance scope.

---

## 1. Checklist

### Source data

| Check | Status | Notes |
|-------|--------|-------|
| `Rate_Table_Extract*.csv` in Source or `plan_analysis/source_data/rates/` | **Met** | `670 GL85-8` CV rows confirmed (9,121) |
| `670 GL85-M` direct CV rows | **N/A (by design)** | Zero rows — inheritance expected |
| `PCOVRSGT.csv` segment linkage | **Met** | 8 slots inherit `670 GL85-8` |
| `PCOVR.csv` product metadata | **Met** | Pay ages 85 vs 88 documented |
| `product_catalog_crosswalk.csv` | **Met** | `670 GL85-M` → `17085M` stable |
| `CSO_Mortiality_Crosswalk.csv` | **Met** | `INTMETHCV` / MORT for `17085M` |
| Re-extract required? | **No** for inheritance path | Unless actuarial rejects inherited table |
| Fleet inherited-CV scan | **Met** | 10 missing inherited-CV candidates documented in `Issue_40_Fleet_CV_Inheritance_Audit.csv` |

### Field definitions

| Check | Status | Notes |
|-------|--------|-------|
| QLAdmin target — QuikCvs / QuikPlCv | **Met** | Issue #31 + #37 precedent |
| LifePRO segment semantics | **Met** | PCOVRSGT trace complete |
| Issuing plan vs rate-owner plan | **Met** | Documented in Planning Report §2 |
| Pay-age segment vs rate table | **Partial** | `AGE 85` has no Rate_Table rows — cease logic only |

### Client / actuarial clarification

| Check | Status | Notes |
|-------|--------|-------|
| May `17085M` use `670 GL85-8` CV factors? | **Met** | Actuarial-approved for Issue #40 CV inheritance scope. |
| Pay age 85 vs 88 — same table or different? | **Met** | Approved to use inherited `670 GL85-8` CV table for `17085M`; pay-age segment treated as cease-age logic, not alternate CV factors. |
| May other missing inherited-CV plans use their PCOVRSGT rate-owner tables? | **Met** | Approved for the documented inherited-CV candidate list. |
| RV/NP/DV inheritance in scope? | **Deferred** | Issue #40 proceeds as **CV only** unless separately requested. |
| Issue #21E load-vs-calculate | **Missing** | Related UAT criterion |
| UAT sample policies | **Met** | See Population CSV |

### Evidence

| Check | Status | Notes |
|-------|--------|-------|
| Fleet population quantified | **Met** | ~212 policies on `17085M` |
| Sister plan baseline | **Met** | `170858` has 986 QuikCvs keys |
| Before-state measurable | **Met** | `17085M` absent from QuikCvs baseline |
| Inheritance trace documented | **Met** | Planning Report §2 |

### Regression guards

| Check | Status |
|-------|--------|
| Issue #25 MPOLICY padding preserved | Required |
| Issue #26 MPREM preserved | Required |
| Issue #37 CV placement preserved | Required |
| Issue #31 ISWL QuikCvs unchanged | Required |
| `170858` / `170588` emits unchanged | Required |

---

## 2. Gate decision

| Track | Scope | G2 result |
|-------|-------|-----------|
| **Track A — CV inheritance load for `17085M`** | QuikCvs emit via `670 GL85-8` inherited rows | **PASS — Approved for Risk Review** |
| **Track B — Fleet-wide inherited CV loader** | Same PCOVRSGT logic across L10, SAL, SPWL, AI WL, PUA candidates | **PASS — Approved for Risk Review** |
| **Track C — RV/NP/DV inheritance** | Other rate families on same rate-owner segments | **Deferred** — scope after CV |

**Overall G2:** **PASS** — source data, field definitions, inheritance trace, and actuarial approval are sufficient to proceed to Risk Review. Development remains blocked until G3 is published and accepted.

---

## 3. Unblock actions

| Action | Owner | Deliverable |
|--------|-------|-------------|
| Confirm `17085M` may inherit `670 GL85-8` CV table | Client / Actuarial | **Complete** — approval provided. |
| Clarify pay-age 85 impact on CV factors | Client / Actuarial | **Complete** — same inherited CV table approved for Issue #40. |
| Confirm fleet-wide inherited-CV candidates | Client / Actuarial | **Complete** — documented inherited-CV scope approved. |
| Confirm UAT policies for post-fix QLAdmin CV screen | Client | 2–3 policies from Population CSV |

---

## 4. Proceed when

- [x] Actuarial approves inherited-rate approach (Planning Option A)
- [x] Actuarial approves fleet candidates documented in Issue #40
- [x] Scope confirmed: **CV only**
- [ ] Risk Agent (G3) completes blast-radius review

**Next stage after unblock:** Risk Agent → Development Agent
