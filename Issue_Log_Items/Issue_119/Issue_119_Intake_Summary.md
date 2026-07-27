# Issue #119 — Intake Summary

**Issue:** #119 — PUA coverage MPAR must be 0 (non-participating), not inherited from base  
**Date:** 2026-07-27  
**Framework stage:** Intake complete (G0)  
**Status:** Proceed to Planning  
**Owner:** Conversion (Warren)  
**Raised by:** Warren, from Robert (QLAdmin / New Era) email correction on PUA §7.2  
**Related:** #105 (quikridr.MPAR from product PAR), #111 (PUA MPAR via base — **superseded on participation**), #60 / #56 (PUA inheritance design)

---

## Client / business symptom (verbatim)

Robert’s stated design (as paraphrased in the CSO briefing draft), then his correction in brackets:

> **7.2 Participating / non-participating**  
> Because there is no separate PA plan in the plan file, the PUA's participating flag follows the base coverage on that policy. If the base is participating, the PUA is participating. If the base is not, the PUA is not. Missing PA plans in the plan file are expected under this design.  
> **[I do not think this is correct, the PUA is not participating, and when QL adds a PA rider, it sets the PAR code on the coverage to 0, that was in my email]**

---

## Normalized finding

QLAdmin treats a Paid-Up Addition coverage as **non-participating**. When QLAdmin adds a PA coverage, it sets the coverage participating flag (`quikridr.MPAR` / plan PAR on that coverage) to **0**, even when the base coverage is participating.

**Our conversion does the opposite today** for nearly all PUA rows:

| Measure (current `QLA_Migration/Output/quikridr.csv`) | Count |
|---|---:|
| Synthetic `*PA` PUA rider rows | **494** |
| PUA rows with `MPAR = 1` | **493** |
| PUA rows with `MPAR = 0` | **1** (`1970PA` on `9010391228C`) |
| PUA `MPAR` equals phase-1 base `MPAR` | **494 / 494** |

So we are coding the **old** “follow the base” rule that Robert is correcting — not the QLAdmin PA-add behavior (`MPAR = 0`).

---

## How we got here (code / validators — no changes at Intake)

1. **Issue #105 (v58.30):** `quikridr.MPAR` = `quikplan.PAR[MPLAN]` at row build. Catalog PUA plans (`170PUA`, `1POPUA`, etc.) mostly have `PAR = 1`.
2. **PUA inheritance** (`_apply_pua_rider_inheritance`): rewrites `MPLAN` to synthetic `base[:4]+"PA"` and inherits dates/age/status — **does not set or clear `MPAR`**.
3. **Issue #111 (closed Not a Defect):** validators were amended so synthetic `*PA` rows must match **phase-1 base** participating (`validate_issue105_mpar.py` v1.1). That locked in the rule Robert now rejects.

Briefing source of truth for Omaha:

| Section | Current text in `tools/_build_pua_omaha_briefing.py` |
|---------|------------------------------------------------------|
| **§7.2** | Already matches Robert: PUA is **not** participating; PAR/MPAR set to **0** |
| **§10 check** | Still wrong: “participating flag on each PUA matches its base coverage” |

---

## Example policies

| MPOLICY | MPHASE | MPLAN | MPAR (now) | Base MPLAN / MPAR | Expected MPAR (Robert) |
|---------|--------|-------|------------|-------------------|------------------------|
| 9010310404C | 2 | 1960PA | **1** | 1960PO / 1 | **0** |
| 9010448806C | (PUA phase) | *PA | **1** (fleet pattern) | participating base | **0** |
| 9010150910C | 3 | 221EPA | **1** | 221END / 1 | **0** |
| 9010391228C | 2 | 1970PA | 0 | 1970JB / 0 | **0** (already correct) |

---

## Suspected domain

**Policy / rider — `quikridr.MPAR` on Paid-Up Addition coverages only.**

Not: face amount, dates, status inheritance, missing PA plans in `quikplan` (still by design), dividends purchase history.

---

## In scope / out of scope

| In scope | Out of scope |
|----------|--------------|
| Force `MPAR = 0` on PUA rider rows (synthetic `*PA` and/or LifePRO PUA products) | Changing base coverage `MPAR` / `quikplan.PAR` for non-PUA plans |
| Update #105 / accountability validators to expect PUA `MPAR = 0` | Emitting PA rows into `quikplan` (#111 design stands) |
| Align briefing §10 check with §7.2 | Reopening full PUA rate / CV work (#56/#60) |

---

## Immediate blockers visible at intake

None for framing. Business rule is explicit from Robert’s email correction. Development must not start until Risk Go + user “Approved for Development”.

---

## Artifact inventory

| Provided | Missing |
|----------|---------|
| Robert correction (bracketed) + §7.2 intent | Named screenshot of QLAdmin PA-add setting PAR=0 (helpful, not required to proceed) |
| Current Output before-state (493 wrong) | — |
| Briefing builder with split §7.2 vs §10 | — |

---

## Severity / owner

| Item | Value |
|------|-------|
| Severity | Medium — wrong participating flag on ~493 PUA coverages; conflicts with QLAdmin PA behavior |
| Owner | Conversion |
| Priority | Go |
| Recommended tracking status | **Intake → Planning → Dependency Gate → Risk** (Pre-Dev chain) |
