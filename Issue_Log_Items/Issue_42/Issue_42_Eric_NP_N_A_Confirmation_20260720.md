# Issue #42 — Eric confirmation: 0824 / GPO OL NP not applicable

**Date:** 2026-07-20  
**From:** Eric  
**To:** Warren  
**Issue:** #42 residual NP gaps

---

## Eric message (verbatim summary)

Confirmed the NP rates for **0824 P DTH** and **L10 GPO OL** are **not applicable**.

Based on `PPBEN_PolicyBenefit_Extract`, these plan codes have:
- **Status Code = T**
- **Status Reason = EX**

for the policies they are attached to.

---

## Conversion disposition

| Coverage | TYPE | Action |
|----------|------|--------|
| `0824 P DTH` | NP | **Do not invent / do not load** QuikNps — N/A |
| `L10 GPO OL` | NP | **Do not invent / do not load** QuikNps — N/A |

No engine change required. Residual source-gap follow-up on Issue #42 is **closed**.

---

## Suggested reply to Eric

> Thanks Eric — recorded. We’ll treat NP for 0824 P DTH and L10 GPO OL as not applicable (Status T / Reason EX) and will not invent or load those grids. No further info needed on this item.
