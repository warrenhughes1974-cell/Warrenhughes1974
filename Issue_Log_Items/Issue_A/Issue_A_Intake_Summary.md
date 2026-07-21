# Issue A — Intake Summary

**Issue ID:** A (Internal track — not client-facing)  
**Title:** QuikPlan / PVO / rate-key structural defects (Robert CSO review)  
**Framework stage:** Intake  
**Status:** Intake → Planning (auto-chain)  
**Opened:** 2026-07-20  
**Reporter:** Robert (internal / CSO UAT)  
**Owner:** Conversion (Warren) + Eric/CSO decisions where noted  
**Priority:** High — blocks clean plan setup / go-live quality  
**Track:** **Internal only** — do not report to client issue log / UAT packages as a numbered client defect

---

## Client symptom (verbatim + normalized)

Robert reported multiple QuikPlan / PVO / rate-key defects found during CSO UAT review. Normalized:

Plan setup rows in QLAdmin are inconsistent with single-premium rules, default PVO keys, category checkboxes, VarGP/VarDB vs rates, annuity conventions, and supplemental (“9” prefix) rider fields. Defects appear even when plans have no rates. Reference plan **TESTRD** shows the minimum correct default-key pattern.

**Track note:** These are internal conversion/product-setup issues. Do not include in client-facing issue reports unless Warren explicitly elevates an item.

---

## Example plans / evidence

| Example | Symptom |
|---------|---------|
| `10L171` | SINGLE PREMIUM WHOLE LIFE — Prem Years=1 (OK) but S/Q/M mode factors non-zero (should be 0.00) |
| `TESTRD` | Correct pattern: no rates, but default category records + default keys; CV/TV basis empty |
| (empty QuikPl* row) | QuikPITv / QuikPICv show blank `PLAN` default row (`GENDER=0`, `UWCLASS=00`, `BAND=00`, etc.) |
| `130JEB` | Category settings (GP/DB/CV/TV/DV checkboxes) do not match keys |
| `1659C2` | Var GP Code = 4 does not match PVO/rates |
| Annuity plans (A-prefix / annuity LOB) | PAR=1, VarDB=2, no DB rates, no int rates, schg missing, PVO not defaults |
| Supp `9*` plans | Supp type blank; PAR should be 0 |

Screenshots saved under Cursor workspace assets (2026-07-20).

---

## Suspected domain

**Primary:** QuikPlan + QuikPl* (PlGd/PlBd/PlUw/PlSt + PlGp/PlDb/PlCv/PlTv/PlDv) + rate factor tables + modal factors  
**Secondary:** Annuity interest / surrender (schg) setup; supplemental rider type / PAR

---

## In scope (first pass)

1. Single-premium: Prem Years = 1; S/Q/M mode factors = 0.00
2. Deficiency reserves (Calc Dfcy) decision path for non-indeterminate-premium plans
3. Default PVO category rows + default keys for every plan (even with no rates) — TESTRD pattern
4. Empty / orphan QuikPl* records (blank PLAN rows)
5. Missing CV/TV basis info where required
6. Category settings (GP/DB/CV/TV/DV) must match keys
7. VarGP must match PVO/rate grain
8. Annuity conventions: PAR=0, VarDB=0, default PVO (incl. gender 0), interest + schg configuration
9. Supp `9*` plans: supp type populated; PAR=0

## Out of scope (first pass)

- Client-facing issue numbering / UAT defect packages for these items
- Redesign of rate emission architecture
- Changes to #25 MPOLICY padding or #26 MPREM mapping
- Full PVO training rewrite (Robert offered a review session — optional)

---

## Related issues / go-live items

| Related | Overlap |
|---------|---------|
| Go-Live Item 07 | Missing default PVO (PlGd/PlBd/PlUw/PlSt) |
| Go-Live Item 08 | PAYAGE/PAYYRS both 0 (includes SPWL plans) |
| Go-Live Item 09 | Systemic VARGP=4 vs rates |
| Go-Live Item 10 | PAR=1 with no dividend rates |
| Go-Live Item 13 / 32 | VarDB / PVO vs rates |
| Go-Live Item 26 | Supp `9*` type |
| Go-Live Item 40 | PVO=Y on annuity plans |
| Issue #74 | VarDB 4→0 (closed — different grain) |
| Issue #77 | Fleet rate setup / PVO keys (closed — may need re-check vs TESTRD “no rates” minimum) |

---

## Immediate blockers (Intake)

| Blocker | Owner |
|---------|-------|
| Authoritative list of single-premium plans (description unreliable) | Eric |
| CSO decision: Calc Dfcy TRUE for plans without indeterminate premiums? | CSO |
| Exact QuikPlan field for “supp type” | Eric (Go-Live Item 26) |
| TESTRD available in this region’s load for side-by-side? | Warren / Eric |

---

## Artifact inventory

| Artifact | Status |
|----------|--------|
| Robert email / notes | Provided in chat 2026-07-20 |
| Screenshots (10L171, empty PVO, QuikPITv/Cv, 130JEB, 1659C2) | Provided |
| TESTRD example (PVO tab) | Referenced; need in local Output/UAT |
| Eric single-prem list | **Missing** |
| CSO deficiency-reserve answer | **Missing** |

---

## Severity / owner

- **Severity:** High (structural plan-file defects; recurring on every load)
- **Owner:** Conversion for emit/fix; Eric/CSO for product decisions
- **Running checklist:** `Issue_A_Conversion_Checklist.md` — must be run on every conversion request going forward

---

## G0 — Intake complete

- [x] Issue folder created
- [x] Intake summary written
- [x] Example plans listed
- [x] Owner and priority assigned
- [x] No code or rulebook changes made
