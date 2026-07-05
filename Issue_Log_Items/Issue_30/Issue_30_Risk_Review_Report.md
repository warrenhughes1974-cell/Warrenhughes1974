# Issue 30 — Risk Review Report

**Issue:** 30 — Policies with Missing Owner/Insured Names  
**Framework stage:** Risk Agent  
**Status:** Ready for Development  
**Date:** 2026-07-05  
**Decision:** Go  

---

## Proposed Change

Apply a narrow converter fix so RNA relationship rows with blank `POLICY_NUMBER` can derive `MPOLICY` from `IDENTIFYING_ALPHA`. Deduplicate `quikclid` rows after emission so duplicate source relationship rows do not produce duplicate QLAdmin client-policy rows.

---

## Risk Assessment

| Area | Risk | Mitigation |
|---|---|---|
| Relationship assignment | Incorrect person could be assigned if policy key parsing is too broad | Only derive from numeric `IDENTIFYING_ALPHA` values with recognized `03` prefix and crosswalk through existing policy map |
| Existing relationship output | Duplicate rows may change row count | Dedup by exact target row key only; no role priority changes |
| Client emission | More `quikclnt` rows may emit because RNA names now participate | Validator checks all referenced relationship IDs exist in `quikclnt` |
| Prior fixes | MPOLICY padding and MPREM mapping could regress through batch rerun | Regression includes Issue 25 and Issue 26 validators |
| Scope creep | Relationship inference beyond source roles | Prohibited; use only explicit RNA role rows |

---

## Expected Impact

- `010150910C` should emit `IN`, `PO`, and `PA` relationships for `NAME_ID=590268`.
- `quikmstr.MPRIMID` and `quikmstr.MOWNRID` should populate from the regenerated `quikclid` relationship map.
- Policies where RNA has blank owner `NAME_ID` remain blank by design.
- Duplicate exact relationship rows should be removed from `quikclid`.

---

## Rollback

Revert the Issue 30 converter change and rerun batch from the same source package. The change is isolated to RNA relationship policy-key derivation and `quikclid` row dedupe.

---

## Risk Decision

**G3 — Risk approved:** GO

Proceed to Development. Surgical code changes only; add validation evidence before closure.
