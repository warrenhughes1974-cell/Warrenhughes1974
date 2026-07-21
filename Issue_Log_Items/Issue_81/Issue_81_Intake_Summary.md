# Issue #81 — Intake Summary

**Issue:** #81 — CSO Valuation Setup PUA rows missing QLA Plan codes  
**Framework stage:** Intake Agent (G0)  
**Status after intake:** Intake (parked; advance when ready)  
**Generated:** 2026-07-17  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Conversion + CSO  
**Priority:** Medium — does not block #80  
**Parent:** Split from Issue #80 (SD-80-4)

---

## Client symptom (normalized)

`docs/Valuation_Setup.xlsx` includes four PUA LifePRO plans with **no QLA Plan** filled in. Issue #80 will not load them until codes exist or CSO confirms exclusion.

| LifePRO Plan | QLA Plan in workbook | QuikPlTv reserve method (from prose) |
|--------------|----------------------|--------------------------------------|
| `622 PUA` | *(blank)* | 2.50% / NLP / Curtate |
| `675 61 PUA` | *(blank)* | 2.50% / NLP / Curtate |
| `675 AD PUA` | *(blank)* | 2.50% / NLP / Curtate |
| `991 PUA` | *(blank)* | 3.50% / NLP / Curtate |

---

## In scope

1. Obtain QLA Plan codes from CSO, or document permanent exclude.  
2. Once codes exist, map Valuation_Setup assumptions using the same Help code rules as #80.  
3. Coordinate with Issue #82 before writing QuikPl* keys for any PUA plan.

## Out of scope

- Issue #80 non-PUA valuation load  
- Citizens folder  
- Adding PA plans to quikplan unless #82 / #60 explicitly reopen that path  

---

## Related issues

| Issue | Relationship |
|-------|----------------|
| #80 | Parent valuation setup; these four rows deferred here |
| #82 | PUA QuikPl key policy vs #60 |
| #60 | Do not add PA plans to quikplan without strong reason |

---

## Immediate blockers

- Missing QLA Plan codes (or explicit exclude list) from CSO.

---

## Gate Criteria (G0)

- [x] Issue folder created  
- [x] Intake summary written  
- [x] No code changes  
- [ ] Planning not started (parked until user advances)
