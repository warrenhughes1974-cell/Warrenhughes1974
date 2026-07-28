# Issue #121 — Intake Summary

**Issue:** #121 — Annual Renewable Term must not emit ETI status  
**Date:** 2026-07-28  
**Framework stage:** Intake complete (G0); research extended same day  
**Status:** Research complete — Ready for Development pending approval  
**Owner:** Conversion (Warren)  
**Raised by:** Warren  
**Priority:** Go-No Go  
**Note:** Originally staged as #120; renumbered to **#121** per user. Development held until ART-family research complete.  
**Related:** #13 (MSTATUS T-precedence), #49, #72 / #108 (ETI/RPU)

---

## Client / business symptom (verbatim)

> We have an Annual Renewable Term. We have policy statuses for this as ETI. An annual renewable term should not have ETI statuses.  
> This is for plan 5667ART.  
> Can you check if we have any other annual renewable terms and if the same issue is happening. Also This is issue 121. Wait on development until you research.

---

## Normalized finding

QLAdmin plan **`5667AT`** (LifePRO **`667 ART`** — Annual Renewable Term; user shorthand `5667ART`) has **90 of 195** policies emitting `MSTATUS = 44` (ETI).

Root cause: LifePRO `PAID_UP_TYPE = LE` (“Life Extension”) → interceptor `PUT_LE` → `ST_PUT_LE` → **44**.

ART products should never be on Extended Term.

---

## ART family research (full book)

There are **three** Annual Renewable Term / ART products in catalog + current Output:

| LifePRO plan | QL emit | Product name | Policies | ETI (`MSTATUS` 44) | Same defect? |
|--------------|---------|--------------|---------:|-------------------:|--------------|
| `667 ART` | **`5667AT`** | Annual Renewable Term | 195 | **90** | **Yes** |
| `646 ART` | **`5646AT`** | Annual Renewable Term | 1 | **0** | **No** (today) |
| `667 ART CR` | **`57ATCR`** | ART Preferred Credit Life | 1 | **0** | **No** (today) |

Evidence: `evidence/issue121_art_family_status_population.csv`

### Why siblings are clean today

Both `5646AT` (`9010516211C`) and `57ATCR` (`9010916282C`) also have `PAID_UP_TYPE = LE`, but both are **`CONTRACT_CODE = T` / `LP`**. Issue #13 termination-first mapping emits **54 Lapsed**, not 44.

The false ETI pattern only fires when the contract is still **Active** (`A`) with `PUT = LE`. That population exists only on **`5667AT`** (86 Active+LE → 44, plus 4 residual T/LP/LE still at 44).

### Preventive scope note

Same LE coding exists on all three ART plans. A fix scoped only to `5667AT` stops today’s defect; a guard on the **ART family** (`5667AT`, `5646AT`, `57ATCR` / LifePRO `667 ART`, `646 ART`, `667 ART CR`) prevents the sibling Active+LE case if it appears later.

---

## Suspected domain

| Area | In scope? |
|------|-----------|
| `quikmstr.MSTATUS` for ART family | **Yes** |
| `quikridr.MPHSTAT` when leaving false ETI | **Yes** |
| Premium / rates | **No** |

---

## Example policies

| MPOLICY | MPLAN | Source | MSTATUS | Notes |
|---------|-------|--------|---------|-------|
| 9010764158C | 5667AT | A / LE | 44 | Defect |
| 9010780202C | 5667AT | A / RI / LE | 44 | Defect |
| 9010761450C | 5667AT | T / LP / LE | 44 | Defect (should be 54) |
| 9010516211C | 5646AT | T / LP / LE | 54 | Sibling OK via #13 |
| 9010916282C | 57ATCR | T / LP / LE | 54 | Sibling OK via #13 |

---

## Gate G0

- [x] Issue folder `#121`  
- [x] Intake + ART-family research  
- [x] Examples listed  
- [x] No code changes; Development held per user  
