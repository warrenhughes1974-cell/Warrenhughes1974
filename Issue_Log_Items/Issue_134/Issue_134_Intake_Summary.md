# Issue #134 — Intake Summary

**Issue:** #134 — Death Benefit Notes  
**Date:** 2026-08-01  
**Framework stage:** Intake complete (G0) — after Stage 0 Discovery  
**Status recommendation:** Proceed Planning → Dependency Gate → Risk  
**Owner:** Conversion (Warren)  
**Raised by:** Eric  
**Priority:** No Go (client sheet)  
**Related:** #21M, #50 (QUIKMEMO / PNOTE); claims lineage on `quikclms.MEMOTEXT`  
**Code changes:** None  

---

## Client / business symptom (verbatim)

> Please place any note with a File_Type code of B on the PNOTE_PolicyNotes_Extract in Memo section in the Claims Tab.

---

## Normalized finding

LifePRO **PNOTE** rows with **`FILE_TYPE = B`** are death-benefit / claim-file notes. They must appear on QLAdmin **Claims Tab → Memo** for life death claims.

**Target (locked at Discovery + discussion):** `quikclms.MEMOTEXT`  
**Not** Policy Memo (`quikmemo`).  
**Not** `QuikHcmm` (Help §7.107 = **Health** Claim Memos — wrong product family).

Today all PNOTE types (including B) emit to `quikmemo` via #21M/#50. Claims `MEMOTEXT` holds Phase 10B **lineage** audit text (`mlineage`), not note bodies.

---

## Example policies (from Discovery research)

| QLA MPOLICY | B notes | Sample LINE_1 | Current Claims MEMOTEXT |
|-------------|--------:|---------------|-------------------------|
| `9010150740C` | 2 | PB = VIOLA FAYE WALKER - SPOUSE | Lineage `…DEATH_CLAIM…` |
| `9010150910C` | 2 | PB = SUSAN SWANSON | Lineage `…DEATH_CLAIM…` |
| `9010335038C` | 2 | PB = PATSY MILLER | Lineage `…DEATH_CLAIM…` (#21M control) |

---

## Suspected domain

**Claims memo text** — `quikclms.MEMOTEXT` — plus **exclude B** from policy `quikmemo`.

Out of scope at Intake: `quikclmp`, health tables (`QuikHclm` / `QuikHcmm`), premium/rate tables, CLAIMSTAT remaps.

---

## In scope / out of scope (first pass)

| In scope | Out of scope |
|----------|--------------|
| PNOTE `FILE_TYPE=B` → Claims Tab memo | `QuikHcmm` / health claim memos |
| Stop B on `quikmemo` | Changing payee (`quikclmp`) rows |
| Lineage disposition on `MEMOTEXT` | Non-B FILE_TYPE routing changes (P/R/M/H stay policy memo) |
| Validator for B routing | Inventing new claim headers for orphan B notes |

---

## Related issues

| Issue | Note |
|-------|------|
| #21M / #21M-FU | QUIKMEMO from PNOTE+PENSE; claim memos called out as separate domain |
| #50 | Fixed-width PNOTE parse — preserve for non-B |
| Claims Phase 10B | `mlineage → MEMOTEXT` collision with this issue |

---

## Immediate blockers visible at intake

None blocking Intake. Open decisions carried to Planning (multi-claim attach rule; lineage replace already defaulted at Discovery).

---

## Artifact inventory

| Artifact | Status |
|----------|--------|
| Client sheet row | Present (Active / No Go / Eric / Warren) |
| Discovery notes | `Issue_134_Discovery_Notes.md` |
| PNOTE extract | `QLA_Migration/Source/PNOTE_PolicyNotes_Extract_20260630.csv` |
| Current `quikclms.csv` / `quikmemo.csv` | In `QLA_Migration/Output/` |
| Screenshots | None provided |

---

## Severity / owner

| Dimension | Value |
|-----------|-------|
| Severity | Client No Go — Claims Tab UAT visibility |
| Owner | Conversion |
| Client clarification needed? | Optional confirm lineage replace; QuikHcmm already ruled out via Help |
