# Issue #152 — Discovery Notes (Search & Discuss)

**Issue:** #152 — Val X Modal Includes Rider  
**Date:** 2026-08-18  
**Framework stage:** Stage 0 Discovery (G-D)  
**Code:** None  

---

## Client ask (verbatim)

Anything with a rider is overstated on the evaluation modal / annual. Eric’s read: QLAdmin is using total premium (base + rider). Rider premium is captured on the rider row. Question for Robert.

---

## Verdict

Granular split of #128 from the 8/18 comparison.

Call math (policy numbers not locked):

| Total (shown) | Rider | Eric’s expected base |
|---:|---:|---:|
| 882 | ~100 | 782 |
| 852 | 100 | 752 |
| 869 | (fee also in play) | 827 |

Eric said conversion of the policies looks encouraging and the mismatch looks like QLAdmin / evaluation programming. Do not strip rider premium from conversion totals until Robert confirms the eval should be base-only.

---

## Related issues

| Issue | Relationship |
|---|---|
| **#128** | Umbrella QuikVal modal. |
| **#26 / #88 / #137** | Conversion premium mapping. Do not reopen unless Output is wrong. |
| **#153** | Policy fee in the same eval numbers. Fix together if Robert says so. |

---

## Proposed work list (Planning will refine)

1. Get the Teams rider-overstated rows.
2. Compare Output base vs rider MPREM vs Val X modal.
3. Robert: eval uses policy total vs base coverage only.

---

## Open questions

1. Policy numbers?
2. Is the overstatement only Val X, or also Names / Coverage Detail?
3. Reduced paid-up examples on the call — same rider rule or a fee-only case (#153)?

---

## Stop

Discovery complete. Awaiting **Proceed to Intake**.
