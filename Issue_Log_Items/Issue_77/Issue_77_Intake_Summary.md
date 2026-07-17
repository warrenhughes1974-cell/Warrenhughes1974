# Issue #77 — Intake Summary (fleet-wide reframe)

**Issue:** #77 — Fleet rate-table setup validation (members, keys, factors, Plan Values Options)  
**Framework stage:** Intake Agent (G0)  
**Status:** Intake Complete → Planning  
**Generated:** 2026-07-17 (reframed same day)  
**Model:** Cursor Grok 4.5 (locked)  
**Code changes:** None  

---

## Client symptom (normalized)

Perform a **full-fleet review** of the rate package we load — not one plan. Validate that **every table** in the rate setup is correct, that **Plan Values Options** checkboxes are right for all plans with rates, and that loaded rates are **100% accurate** relative to the guide package in `docs/EX_Rate_Tables`.

Screenshot of `1658CS` Plan Values Options is **supporting evidence** for UI checkbox meaning, not the scope boundary.

---

## Scope (locked by user 2026-07-17)

| In scope | Out of scope |
|----------|----------------|
| All plans in `quikplan` / `Output/rates/` | Copying foreign EX plan codes into Citizens catalog |
| Member tables QuikPlGd/Uw/Bd/St/Nb | Inventing actuarial factors not in LifePRO |
| Key tables QuikPlGp/Db/Cv/Tv/Dv | Policy table changes (`quikmstr`/`quikridr`) except #25/#26 guards |
| Factor grids QuikGps/Dbs/Cvs/Tvs/Dvs/Nps/Coi/… | Reversing #71 BAND=`00` without client order |
| `quikplan` PLANVALOPT + all *VARY* flags | |
| Defaults/placeholders vs EX conventions | |

---

## Guide package

**Authority for structure/defaults:** `docs/EX_Rate_Tables/` (21 DBFs).  
**Authority for Citizens factor content:** LifePRO extracts already used by the converter.  
**Authority for UI checkbox meaning:** EX patterns + Plan Values Options screenshot (`1658CS`).

EX is a **different product book** (~1,760–1,798 plans). **Zero Citizens `16xx` overlap.** Use EX as the setup guide, not a plan-by-plan clone.

---

## Example policies / artifacts

| Artifact | Role |
|----------|------|
| `docs/EX_Rate_Tables/*.dbf` | Setup guide |
| Screenshot Plan Values Options `1658CS` | Checkbox semantics sample |
| `QLA_Migration/Output/quikplan.csv` + `Output/rates/` | Before-state under test |
| `Issue_77/evidence/*` | Read-only fleet audit (2026-07-17) |

Policy numbers: **N/A** (plan/rate setup validation).

---

## Suspected domain

**Rates / plan setup — fleet-wide.**

---

## First-pass findings (from fleet audit)

| Area | Finding |
|------|---------|
| Package coverage | 141 quikplan plans; **126** have factor rates; member tables cover those **126** (0 member gaps) |
| Key↔factor link | Nearly clean — **1** orphan key (`910RWP` TV key without factor) |
| Plan Values Options | **114 / 126** rated plans fail UI-inferred checkbox matrix (M2); **STVARYGP never Y** fleet-wide |
| PLANVALOPT consistency | **11** plans inconsistent (rates but PVO≠Y, or PVO=Y with no factors) |
| QuikPlTv assumptions | **100% blank** RSVINT/RSVMETH/INTMETHTV/STOREMEANS/CALCMIDS (EX nearly fully populated) |
| QuikPlSt.MLOANINT | All blank (EX ~46% = `0.00`) |
| QuikAint | We emit **2** plans; EX has **181** |

---

## Related issues

| Issue | Relationship |
|-------|----------------|
| #71 | BAND=`00` — drives Band member + BDVARY semantics |
| #60 Track B | QuikPlTv / interest assumptions |
| #40/#41/#42 | CV/TV factor content (separate from checkbox/defaults) |
| #51 | QuikAint stubs (only 2 plans today) |
| #73 | ISSCNTRY=`0000` alignment |

---

## Owner / priority

| Field | Value |
|-------|--------|
| Owner | Conversion (setup/flags/defaults) + CSO/Client (TV assumptions, any invented DB/DV) |
| Priority | High — fleet rate load correctness |
| Severity | Setup / validation defect across rate package |

---

## Immediate blockers

1. Confirm **Plan Values Options rule** fleet-wide (count>1 vs dimension-in-key / screenshot M2).  
2. Confirm whether **QuikPlTv assumption fill** is in this issue or stays #60.  
3. Confirm **QuikAint** expansion expectation vs EX (181 vs 2).

---

## Gate G0

- [x] Issue folder + evidence  
- [x] Fleet scope documented  
- [x] Owner/priority assigned  
- [x] No code/rulebook changes  
