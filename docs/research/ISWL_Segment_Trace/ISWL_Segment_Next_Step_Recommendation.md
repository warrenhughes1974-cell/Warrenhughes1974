# ISWL Segment Next Step Recommendation

**Date:** 2026-06-30 (updated)  
**Prior:** 2026-06-28  
**Change:** PSEGT / PDINT / PDINTTBL extracts received (Issue #31 follow-up)

---

## Trace outcome (revised)

**Partial → materially advanced.** PSEGT blocker **removed**. Hierarchy traceable through `PCOVRSGT → PSEGT → rates/PDINT` for all 8 ISWL coverages.

---

## Implementation-ready

| Area | Readiness | Condition |
|------|-----------|-----------|
| **QUIKCVS** | **Ready (conditional)** | PDAGE vs Rate_Table parity PASS; existing CV routing |

---

## Partially resolved — planning + SME before code

| Area | PSEGT | Gap |
|------|:-----:|-----|
| **QUIKUINT** | 8/8 A1/G1/LN slots | PDINT G1/LN sparse; QUIKUINT schema; IDENT→MPLAN |
| **QUIKCOI** | 8/8 U6 | PAAGERAT 2/8; SD parent ID indirection |
| **QUIKGCOI** | 8/8 U5 | PAAGERAT 1/8 |
| **QUIKGPS** | 8/8 BP | PAAGERAT 4/8; PR still absent |
| **QUIKISSC** | 8/8 SR/SL | Surrender rate pointer decode |
| **Expenses** | 8/8 UF only | U1/U2/U3/G2/G3/GF not in PSEGT |

---

## Still blocked (non-source)

- **QLAdmin UL table schemas** (QUIKUINT, QUIKCOI, QUIKGCOI, QUIKISSC)
- **PPRDF** extract (hierarchy top)
- **Reference ISWL rate DBFs** for value validation

---

## Recommended agent sequence

1. ~~**Source Dependency Agent**~~ — **CLOSED** (PSEGT/PDINT delivered 20260629)
2. **SME Review Agent** — PDINT IDENT map; U6 vs NC; SR/SL; expense model
3. **Implementation Planning Agent** — QUIKCVS parity; phased UL loader roadmap
4. **Development Agent** — only after schema + SME sign-off (not yet)

---

## Cursor-ready prompt: Implementation Planning Agent

```
# ISWL Implementation Planning Agent (Post-PSEGT)

**Project:** LifePRO → QLAdmin Conversion Platform
**Issue:** #31 / ISWL segment hierarchy
**Mode:** Planning only — no code until approved

## Context

PSEGT, PDINT, PDINTTBL extracts validated 20260629.
Source dependency CLEARED. See:
- Issue_Log_Items/Issue_31/Issue_31_PSEGT_PDINT_Followup_Report.md
- docs/research/ISWL_Segment_Trace/iswl_segment_trace_bundle_20260629.json

## Objective

Produce phased implementation plan for ISWL QLAdmin targets.

## Phase 1 (immediate)

- QUIKCVS: PDAGE vs Rate_Table parity for 8 ISWL MPLANs
- Document emit validation against reference QuikCvs if available

## Phase 2 (after SME)

- QUIKUINT: PDINT CENII A1 4.50% → QUIKUINT mapping proposal
- QUIKCOI/QUIKGCOI: U6/U5 PAAGERAT segment-ID resolution rules

## Phase 3 (deferred)

- QUIKISSC SR/SL payload decode
- Expenses UF + nested premium segment model

## Constraints

- Do not modify app.py converters until plan approved
- Preserve Issues #21D–#32 protected logic
- Surgical scope only

## Deliverables

1. ISWL_Implementation_Phase_Plan.md
2. ISWL_SME_Signoff_Checklist.md
3. ISWL_CVS_Parity_Test_Matrix.csv
```

---

*Prior Source Dependency Agent prompt archived — dependency met.*
