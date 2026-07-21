# Issue #82 — Intake Summary

**Issue:** #82 — CSO Valuation Setup PUA QuikPlCv / QuikPlTv keys vs Issue #60  
**Framework stage:** Intake Agent (G0)  
**Status after intake:** Intake (parked; advance when ready)  
**Generated:** 2026-07-17  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Conversion + CSO / actuarial  
**Priority:** Medium — does not block #80  
**Parent:** Split from Issue #80 (SD-80-5); related to #60 SD-60-1

---

## Client symptom (normalized)

`docs/Valuation_Setup.xlsx` lists PUA QLA plan codes with Cash Value / Reserve assumptions (for example `121PUA`, `1POPUA`, `265PUA`, `170PUA`). Issue #60 directed that we **do not add PA plans to the quikplan file** unless there is a strong reason, and that PUA values should inherit from the base plan.

We need a locked business decision: whether QuikPlCv / QuikPlTv assumption keys may be written for those PUA plan codes without adding the same PA plans to quikplan, or whether PUA must continue to rely only on base-plan assumptions.

---

## Example PUA QLA plans present in Valuation_Setup (have QLA code)

| LifePRO Plan | QLA Plan |
|--------------|----------|
| `621 PUA` | `121PUA` |
| `665 PUA` | `265PUA` |
| `670 PUA` | `170PUA` |
| `960 65 PUA` | `165PUA` |
| `960 LP PUA` | `185PUA` |
| `960 OL PUA` | `1OLPUA` |
| `960 PO PUA` | `1POPUA` |
| `961 PUA` | `261PUA` |
| `970 PUA` | `1970PA` |
| `980 PUA` | `280PUA` |

(Plus four missing-QLA PUA rows on Issue #81.)

---

## In scope

1. Decide whether PUA QuikPlCv / QuikPlTv keys are allowed under #60.  
2. If yes, apply Valuation_Setup (and Help code map) to those PUA plans only.  
3. If no, document that PUA continues to use base-plan assumptions only and close with that rule.

## Out of scope

- Issue #80 non-PUA valuation load  
- Reversing #60 Track A PUA phase rules on quikridr  
- Citizens folder  

---

## Related issues

| Issue | Relationship |
|-------|----------------|
| #80 | Parent; PUA key writes deferred here |
| #81 | Missing QLA codes for four PUA rows |
| #60 | SD-60-1 — do not add PA plans to quikplan |

---

## Immediate blockers

- Business decision on PUA QuikPl* keys vs #60 (Chris / CSO / user).

---

## Gate Criteria (G0)

- [x] Issue folder created  
- [x] Intake summary written  
- [x] No code changes  
- [ ] Planning not started (parked until user advances)
