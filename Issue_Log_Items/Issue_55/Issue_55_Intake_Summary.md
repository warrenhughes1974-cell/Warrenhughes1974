# Issue #55 — Intake Summary

**Issue:** #55 — Unit Issues (RPU / reduced base units)  
**Framework stage:** Intake Agent (G0)  
**Status after intake:** Planning  
**Generated:** 2026-07-13  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Conversion (primary) + Client UAT evidence  
**Priority:** Active / client-reported  
**Tracking note:** Log row shows Risk = **No-Go** (Eric) — treat as pre-research flag; re-evaluate after Planning/Dependency Gate  

---

## Client symptom (verbatim)

> Units for 018495BC, not correct in QLAdmin. Policy is in RPU status and units for base coverage should be 0.00001 and units for Phase 2 should be 0.53. The PU DB should be $530. Note Column AC on the PPEN_PolicyBenefit_Extract has 0.00001 and 0.53 for the units (Column AC). For 018499CC Phase 1 units should be 0.00001 (Phase 2 units of 1.05 pulled into QLAdmin correctly). For 018510C (RPU status), the units should be 0.00001 for Phase 1 and 0.647 for Phase 2 to provide a DB of $647.

## Normalized symptom

QLAdmin Coverage units (`quikridr.MUNIT`) for three policies are believed wrong vs LifePRO Policy Benefit extract Column AC (`NUMBER_OF_UNITS`). Expected:

| Policy | Status context | Phase 1 units | Phase 2 units | Expected face (× $1000 VPU) |
|--------|----------------|---------------|---------------|-------------------------------|
| `018495BC` | RPU | 0.00001 | 0.53 | Phase 2 PU DB **$530** |
| `018499CC` | (Phase 2 OK) | 0.00001 | 1.05 (said correct in QLA) | — |
| `018510C` | RPU | 0.00001 | 0.647 | Phase 2 DB **$647** |

Source citation: client “PPEN_PolicyBenefit_Extract” Column AC → repo file is **`PPBEN_PolicyBenefit_Extract_*.csv`**; Column **AC** = **`NUMBER_OF_UNITS`**.

---

## Example policies

| QLA | LifePRO (crosswalk) |
|-----|---------------------|
| `018495BC` | `9018495B` |
| `018499CC` | `9018499C` |
| `018510C` | `9018510` |

---

## Suspected domain

**Policy / rider units** — `quikridr.MUNIT` (and face = `MUNIT × MVPU`). Not claims, memo, or rates.

---

## In scope (first pass)

- Confirm PPBEN `NUMBER_OF_UNITS` vs current `Output/quikridr.csv` `MUNIT` for the three policies  
- Confirm rulebook path `NUMBER_OF_UNITS → MUNIT`  
- Distinguish converter defect vs stale QLAdmin load / DBF display (related: #21K MUNIT precision)  
- Document RPU master status vs phase statuses  

## Out of scope (first pass)

- Changing unrelated premium / fee / status mappings (#26 MPREM, #49 status) unless Planning proves coupling  
- Redesigning plan inheritance for blank `PLAN_CODE`  
- Wholesale `app.py` changes  

---

## Related issues

| Issue | Relevance |
|-------|-----------|
| **#21K** | Five-decimal `MUNIT`; CSV can be correct while QLAdmin display/storage differs |
| **#26** | `MPREM` — must not regress |
| **#25** | `MPOLICY` padding — must not regress |
| **#49** | RPU (`45`) master preserved when later phase is `22` — sample policies show this pattern |

---

## Artifact inventory

| Artifact | Present? |
|----------|----------|
| Client narrative + expected units | Yes |
| Example policies | Yes |
| Screenshots of wrong QLAdmin units | **No** |
| PPBEN extract in `Source/` | Yes (`…_20260630.csv`) |
| Current `quikridr.csv` | Yes |
| Existing `Issue_55/` analysis | Created this intake |

---

## Immediate blockers visible at intake

1. No screenshot / stored-DBF proof of what QLAdmin currently shows.  
2. Client “No-Go” may already signal non-development path — needs Dependency Gate confirmation after trace.  

---

## Severity / owner

| Field | Value |
|-------|--------|
| Severity | Medium — wrong face/DB on RPU policies if units wrong in admin |
| Owner | Conversion research first; Client if CSV already correct (UAT reload / display) |
| AGENTS.md | Surgical only; no code at Intake |

---

## Gate G0 checklist

- [x] Issue folder `Issue_Log_Items/Issue_55/`  
- [x] Intake summary written  
- [x] Example policies listed  
- [x] Owner and priority assigned  
- [x] No code or rulebook changes  

**Next:** Planning Agent (same model).
