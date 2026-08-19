# Issue #141 — Intake Summary

**Issue:** #141 — Reserve Category  
**Framework stage:** Intake Agent (G0)  
**Status recommendation:** Intake Complete → Planning → Dependency Gate → Risk  
**Generated:** 2026-08-19  
**Owner:** Conversion  
**Priority:** Go for framing (client No-Go on sheet until UAT; DBF width already fixed)

---

## Client symptom (verbatim + normalized)

**Verbatim:** Put the reserve category on the User Defined field on the policy. Reserve category used to be the LOB on the plan. Crosswalk plan LOB to policies. Plans populated with ISWL must stay; LifePRO reserve category goes on the policy in QuikSpec. New field `RESRVCAT` char 2.

**Normalized:** Write LifePRO plan reserve category (`PCOVR.PRODUCT_TYPE`) onto each policy’s QuikSpec User Defined tab. Do not overwrite QuikPlan LOB/MKTG/PRODUCT tags such as `ISWLFE`.

Screenshot: Plan Information `A96DAR` shows LOB = **03** (matches `PCOVR.PRODUCT_TYPE` on `896 DAR`).

## Example policies

| QLA policy | Base QLA plan | LifePRO coverage | Plan HLOB (keep) | Proposed RESRVCAT |
|------------|---------------|------------------|------------------|-------------------|
| 9010143726C | 221END | 621 END85 | (blank) | 03 |
| 9010148272C | 221END | 621 END85 | (blank) | 03 |
| 9010713704C | 1659C2 | 659 CEN II | ISWLFE | 05 |

## Suspected domain

Policy User Defined — `quikspec.RESRVCAT`. Same table as resident state and vanish.

## In scope (first pass)

- Add `RESRVCAT` to QuikSpec emit (schema, rulebook/enrichment, validator, CSV).
- Map each policy via **PPBEN BENEFIT_SEQ=1** `PLAN_CODE` → `PCOVR.PRODUCT_TYPE`.
- Traditional base is `BA`; ISWL base is `BF` on seq 1 — do not filter BA-only.
- Leave `quikplan` `MKTG` / `PRODUCT` / `HLOB` = `ISWLFE` on the 8 ISWL plans (#99).

## Out of scope (first pass)

- Changing QuikPlan LOB, MKTG, PRODUCT, or NAIC LOB.
- QuikIswl `MLOB` (#124).
- Vanish (#145) and residence (#132) values.
- Recreating QUIKSPEC.DBF (append-only; template already has char-2 `RESRVCAT`).

## Related issues

| ID | Relationship |
|----|----------------|
| **#99** | ISWLFE on plan — preserve |
| **#124** | QuikIswl MLOB=I — do not touch |
| **#132** | RESSTATE on same QuikSpec row |
| **#145** | VANISH on same QuikSpec row |

## Immediate blockers at intake

None. Warren widened `RESRVCAT` to char 2 on the working DBF and the Append Tool master template (2026-08-19).

## Artifact inventory

| Artifact | Status |
|----------|--------|
| Discovery notes | `Issue_141_Discovery_Notes.md` |
| Plan LOB screenshot | A96DAR LOB=03 |
| PCOVR extract | `PCOVR_Coverage_Extract_20260630.csv` |
| PPBEN extract | `PPBEN_PolicyBenefit_Extract_20260630.csv` |
| Current `quikspec.csv` | 5,083 rows; no RESRVCAT column |

## Severity / owner

- **Severity:** Medium — valuation/user-defined code missing on the policy.
- **Owner:** Conversion (Warren). Eric is issue owner on the sheet.
