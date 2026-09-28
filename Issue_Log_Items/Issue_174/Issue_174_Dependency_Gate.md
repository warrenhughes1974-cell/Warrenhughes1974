# Issue #174 — Dependency Gate

**Issue:** #174 — Pending Death Benefit Policies
**Framework stage:** Dependency Gate
**Date:** 2026-09-28
**Status:** PASS

---

## Checklist

### Source data

| Check | Result |
|---|---|
| Required LifePRO extracts in `QLA_Migration/Source/` | **Met.** `PPOLC` and `PPBEN` for 20260630 and 20260831. |
| Extract row count > 0 | **Met.** |
| Column headers documented | **Met.** `CONTRACT_CODE`, `CONTRACT_REASON`, `PAID_UP_TYPE`, `STATUS_CODE`, `STATUS_REASON`, `BENEFIT_TYPE`, `BENEFIT_SEQ`, `PLAN_CODE`. |
| Extract date matches the batch under test | **Met.** Current Output is the 6/30 package (`cut_manifest_latest.json`, `QLA_VALUATION_DATE=20260630`). 8/31 is in Source for the later-cut trace. |
| Re-extract required? | **No.** |

### Field definitions

| Check | Result |
|---|---|
| QLAdmin target table confirmed | **Met.** `quikmstr.MSTATUS`, `quikridr.MPHSTAT`, `quikridr.MSAVESTAT`. |
| Target field semantics confirmed | **Met.** 50 = Death Claim Pending. 22 = Active. Brianna: policy 50, phase 22. |
| LifePRO source semantics confirmed | **Met.** `S`/`DP` is the contract. Benefit `STATUS_CODE` stays `A`. |
| Transformation notes | **Met.** Existing `ST_S_DP` → 50 and bare `A` → 22. No new translation row. |

### Client clarification

| Check | Result |
|---|---|
| Scope boundary agreed | **Met.** Pending death only. Actual death, surrender, lapse, and maturity stay as they are. Return of premium is not a load. |
| Business rule for edge cases | **Met, with a documented assumption.** The one paid-up addition stays Active (22) with the base, from Brianna's statement that the phases stay 22. Development approval is the written acceptance of the #60 / #160 / #108 exception. |
| Retention / filtering | **N/A.** |
| UAT acceptance | **Met.** `9011085655C`: policy 50, phase 22, beneficiary edit no longer blocked. Header does not flip to 22. |

### Evidence

| Check | Result |
|---|---|
| Example policies | **Met.** `9011085655C`, plus the two paid-up-addition policies. Population file in `evidence/`. |
| Client support | **Met.** Brianna's email in the issue open. No screenshot filed. Not required to see the status pair; Output already shows 50/50. |
| Before-state measurable | **Met.** Current Output. |

### Regression guards

| Check | Result |
|---|---|
| Issue #25 MPOLICY padding | **Met.** Not touched. |
| Issue #26 MPREM | **Met.** Not touched. |
| Unrelated rulebooks | **Met.** No rulebook edit. The change is the inherit exception in `app.py` and the matching block list in `qla_core`. |

---

## Status

**PASS.** Proceed to Risk.

No blocker. The closed-issue exception is a condition on Development approval, not a missing dependency.

## Recommended tracking status

Risk review next. Do not mark Ready for Development until Risk is published.
