# ISWL QUIKUINT Implementation Blueprint

**Project:** LifePRO → QLAdmin Conversion Platform  
**Issue:** #32 — ISWL Phase 5 QUIKUINT  
**Version baseline:** v57.39  
**Date:** 2026-06-30 (SME gate closure)  
**Mode:** Planning only — no code changes  
**Authority:** Issue #31 segment trace (20260629), PDINT/PDINTTBL extracts, Product Book addendum, QLAdmin Help §7.223 (PDF p.923), Issue #32 SME answer log  
**SME log:** [`Issue_32_QUIKUINT_SME_Answers.md`](../../Issue_Log_Items/Issue_32/Issue_32_QUIKUINT_SME_Answers.md)

---

## Scope

Implementation blueprint for **QUIKUINT** — UL interest rates for the 8 ISWL MPLAN fleet.

| Target | QLAdmin table | Readiness |
|--------|---------------|-----------|
| QUIKUINT | `QuikUint` | **READY FOR DEVELOPMENT** — all SME gates **CLOSED** |

**ISWL fleet (8 MPLANs):** `1658C1`, `1658CS`, `1659C2`, `1659CR`, `1659CS`, `1659SR`, `1669SR`, `1679CS`

**Prerequisite:** Issue #31 rate-table phases (QUIKCVS, QUIKGPS, QUIKCOI, QUIKGCOI) **CLOSED**.

**Out of scope for Phase 5:** QUIKISSC, expenses, DBF production emit / `app.py` integration (separate issues).

---

## Mandatory hierarchy (QUIKUINT)

```text
PPRDF (not in repo — optional top link)
  ↓
PCOMP (PRODUCT_ID = ISWL coverage)
  ↓
PCOVR (COVERAGE_ID, POLICY_FORM_NUM)
  ↓
PCOVRSGT (SEGT_FLAG=Y → SEGT_ID)
  ↓
PSEGT (SEGMENT_ID + SEGT_TYPE ∈ {A1, G1, LN})
  ↓
PDINT (IDENT=CENII + TYPE_CODE=A1 + DINT_RULE + EFF_DATE)
  ↓
PDINTTBL (IDX + START_DATE + END_DATE + DECLARED_RATE)
  ↓
Policy Form Crosswalk → authoritative MPLAN
  ↓
QuikUint (MPLAN + MEFFDATE + MGTDRATE + MCURRATE)
```

**Non-negotiable rule:** Every row must prove PCOVRSGT → PSEGT(A1) → PDINT(CENII) → PDINTTBL before emit.

---

## SME gate closure (2026-06-30)

| Gate | Decision | Status |
|------|----------|--------|
| MGTDRATE source | **MGTDRATE = MCURRATE** from A1 declared rate | **CLOSED** |
| Emit scope | **All historical PDINTTBL tiers** for CENII/A1; fallback to current tier | **CLOSED** |
| PDINT IDENT | **CENII** for all 8 ISWL MPLANs | **CLOSED** |
| QuikUint schema | 4 fields per Help §7.223 | **CLOSED** |
| Loan interest | Not on QuikUint | **CLOSED** |

---

## Final authoritative mapping

| QUIKUINT field | LifePRO source | Transform |
|----------------|----------------|-----------|
| **MPLAN** | Crosswalk | All **8 ISWL MPLANs** |
| **MEFFDATE** | PDINTTBL | **START_DATE** of each historical tier |
| **MCURRATE** | PDINTTBL | **DECLARED_RATE** from **CENII / A1** |
| **MGTDRATE** | PDINTTBL | **Same value as MCURRATE** on each tier |
| *(loan)* | PSEGT LN | **Not QuikUint** — `QuikPlan.LOANINT` / `QuikPlSt.MLOANINT` |

---

## Authoritative transform (PR-5)

```text
For each ISWL MPLAN in ISWL_MPLAN_ALLOWLIST:
  1. PCOVRSGT → PSEGT gate: A1 slot resolves (8/8)
  2. PDINT IDENT = CENII (SME confirmed)
  3. Collect PDINTTBL tiers from DINT_RULE 0 AND DINT_RULE 3 (TYPE=A1)
  4. Union merge by unique START_DATE:
       - START_DATE in one rule only → include
       - START_DATE in both with same rate → include once
       - START_DATE in both with different rates → prefer Rule 3 (tie-break)
  5. If no historical tiers: emit current tier only (fallback)
  6. For each merged tier, emit QuikUint:
       MPLAN    = crosswalk PLAN
       MEFFDATE = PDINTTBL.START_DATE
       MCURRATE = PDINTTBL.DECLARED_RATE
       MGTDRATE = MCURRATE                    # SME confirmed mirror
  7. Format rates as N(8.4) percent literal (4.50000 = 4.5%)
```

**END_DATE:** Filter-only when selecting active tier in fallback mode; not emitted.

---

## CENII / A1 historical schedule (source)

| DINT_RULE | START_DATE | END_DATE | DECLARED_RATE |
|-----------|------------|----------|---------------|
| 0 | 19800101 | 19981231 | 7.00000 |
| 0 | 19990101 | 20011231 | 5.00000 |
| 0 | 20020101 | 20991231 | 4.50000 |
| 3 | 19800101 | 19881231 | 11.00000 |
| 3 | 19890101 | 20011231 | 9.00000 |
| 3 | 20020101 | 20991231 | 4.50000 |

**Cross-validation (non-authoritative):** PPBEN `FV_GUAR_RATE = 4.50` on 2,159 ISWL policies.

---

## QLAdmin target schema (confirmed)

**Source:** QLAdmin Help §7.223 — `QuikUint` (UL Interest Rates)

| Field | Type | Len | Description |
|-------|------|-----|-------------|
| MPLAN | C | 6 | Plan code |
| MEFFDATE | D | 8 | Effective date |
| MGTDRATE | N | 8.4 | Guaranteed initial interest rate |
| MCURRATE | N | 8.4 | Current interest rate |

**Index key:** `MPLAN + DTOS(MEFFDATE)`

---

## Expected output (SME-approved)

| Scenario | QuikUint rows (ISWL) | Notes |
|----------|---------------------:|-------|
| **Union merge (PR-5 default)** | **32** | 8 MPLANs × 4 unique START_DATEs (Rules 0+3) |
| Fallback — current tier only | **8** | When history unavailable |

**Historical tier validation:** [`Issue_32_QUIKUINT_Historical_Tier_Validation.md`](../../Issue_Log_Items/Issue_32/Issue_32_QUIKUINT_Historical_Tier_Validation.md) — Rule 0 and Rule 3 are **not duplicates**; Rule 3-only emit **violates** SME historical-load instruction.

---

## Implementation approach (PR-5 Development Agent)

1. **New loader:** `qla_core/pdint_uint_loader.py` — PDINT/PDINTTBL + segment resolver.
2. **Schema:** Add `QuikUint` to `rate_dbf_schema.py`.
3. **Pipeline:** Wire `iswl_phase5` in config; separate from PAAGERAT factor grid.
4. **Validator:** `tools/validators/iswl_quikuint_reconcile.py`.

**Do not reuse** PAAGERAT attained-age scalar loader.

---

## Recommendation

**READY FOR DEVELOPMENT** — launch Development Agent with [`ISWL_QUIKUINT_Next_Stage_Prompt.md`](ISWL_QUIKUINT_Next_Stage_Prompt.md).

See also: [`ISWL_QUIKUINT_Table_Design.md`](ISWL_QUIKUINT_Table_Design.md), [`ISWL_QUIKUINT_Validation_Strategy.md`](ISWL_QUIKUINT_Validation_Strategy.md).
