# Issue #51 — Intake Summary

**Issue:** #51 — Missing Interest Table (A60MIR / A96DAR) — Projected Values Crash Loop  
**Date:** 2026-07-11  
**Framework stage:** Intake complete (G0)  
**Status:** Approved → Planning  
**Owner:** Conversion (Warren) · **Reporter:** Client UAT (QLAdmin projected values)  
**Business status:** No-Go for Development until G1 + G2 + G3  

**Model:** Cursor Grok 4.5 (locked Intake stage)

---

## 1. Client / business symptom (verbatim + normalized)

**Issue log (verbatim):**

> 5. Tried looking at projected values on a policy with rider plan **A96DAR**. Got error message that int table was missing. it got caught in a loop and had to use task manager to quit QL. I just tested on policy **010348734C** with rider **A60MIR** in **status 56**, and got the same. And it pops up endlessly. I tried reindexing to see if it would at least help the endless loop (I knew Id still get the error) but it did not help. Why do we care about this rider anyway when its terminated? I understand getting the message if it was active.

**Screenshot message:**

> Interest table not found for A60MIR, cannot calculate balance.

Evidence: `evidence/issue51_client_screenshot_010348734C.png`

**Normalized:**

Opening **Projected Values** in QLAdmin for policies that carry rider plans **A60MIR** (Monthly Income Rider) or **A96DAR** (Deposit Annuity Rider) raises a missing **interest table** error and enters an **endless OK-loop** that requires Task Manager kill. The error occurs even when the rider is **status 56 (terminated)**. Client questions why terminated riders participate in the projection.

**Example policy:** `010348734C` (LifePRO `9010348734`) — base Ph1 Stat 22 Plan **196085**; Ph2 Stat **56** Plan **A60MIR**.

---

## 2. Suspected domain

| Layer | Path / table | Role |
|-------|--------------|------|
| Catalog | `quikplan` plans `A60MIR`, `A96DAR` (A-prefix) | Triggers annuity interest table governance (PLAN-023) |
| Coverage | `quikridr` rider rows (MPHSTAT=56) | Projection walks rider MPLANs |
| Target interest | **QuikAint** (Annuity Interest Rates) | QLAdmin Help §7.31 — MPLAN + MEFFDATE + MINTRATE/MINTRATE1 |
| Companion (advisory) | QuikAing / QuikAinf / QuikAexp | PLAN-023 / Data_Goverence A-plan set |
| Not this defect | QuikUint (UL / ISWL #32) | Wrong product class |
| Not this defect | `quikplan.DEPINT` scalar | Insufficient for table lookup |
| Not this defect | `quikdvdp.MDEPINT` (#21D) | Div Deposit Int Rate 4.00 on screen — separate path |

**Domain:** Rates / annuity interest tables (`QuikAint`) for A-prefixed closed riders — **not** premium, claims, or memo.

---

## 3. Intake evidence (measured — Planning formalizes)

| Check | Result |
|-------|--------|
| Example on crosswalk | `9010348734` → `010348734C` |
| Example in `quikridr` | Ph2 A60MIR MPHSTAT=56, expiry 20180113 |
| A* plans in `quikplan` | **Only** A60MIR + A96DAR (2 plans) |
| `Output/rates/QuikAint*` | **Missing** from load package |
| PFSA QuikAint builder | Has PFSA annuity codes; **no** A60MIR / A96DAR |
| `QuikUint.csv` | Present but **0 data rows**; ISWL-only anyway |
| Fleet A60MIR/A96DAR riders | **6 / 6** MPHSTAT=56 (100% terminated) |
| PPBEN `FV_GUAR_RATE` on forms 863 / 896 DAR | **All .00**; balances .00 |

Evidence: `Issue_Log_Items/Issue_51/evidence/` · script: `scripts/research_issue51_quikaint_gap.py`

---

## 4. In scope / out of scope (first pass)

### In scope

- Emit **QuikAint** rows for `A60MIR` and `A96DAR` into the rate load package
- Align rates with LifePRO authority where available (`PPBEN.FV_GUAR_RATE`)
- Validate projected-values path no longer missing-table for example `010348734C` and A96DAR samples
- Document client question on terminated-rider projection scope (QLAdmin vs conversion)

### Out of scope (unless Planning expands)

- Changing QLAdmin application loop behavior (vendor product)
- Filtering status-56 riders out of `quikridr` (would erase history; not requested as conversion rule)
- Extending QuikUint / ISWL PDINT path to these riders
- Redesigning PFSA QuikAint history for other A* annuity products
- Fixing unrelated `LOANINTX=22` catalog anomaly on these plans (separate QA)

---

## 5. Related issues

| Issue | Relationship |
|-------|----------------|
| **#32 QUIKUINT** | UL interest — **must not** expand to MIR/DAR |
| **#21D MDEPINT** | Div Deposit Int Rate — preserved; different table |
| **#21E CV** | Cash value compute — related UX surface; interest table is upstream |
| **#28 PLAN catalog** | A60MIR/A96DAR authorized closed products |
| **#25 / #26** | Unrelated (MPOLICY / MPREM) — must not regress |

---

## 6. Artifact inventory

| Artifact | Status |
|----------|--------|
| Client symptom + screenshot | Provided |
| Example policy `010348734C` | Provided |
| `quikplan` / `quikridr` / `Output/rates/` | Present |
| PPBEN extract (FV_GUAR_RATE) | Present |
| PFSA QuikAint builder artifacts | Present (does not cover MIR/DAR) |
| Product-level historical crediting schedule for 863/896 | **Missing** (soft — fleet rates are .00) |
| Client decision: stub 0% vs actuarial schedule | Soft for Planning / Gate |

---

## 7. Immediate blockers visible at intake

| Blocker | Blocks? | Notes |
|---------|---------|-------|
| Target table identity (QuikAint) | No | Confirmed Help §7.31 + PLAN-023 |
| Example traceability | No | Measurable |
| Historical actuarial schedule | Soft | Fleet PPBEN authority is 0.00 — usable for Conditional Go stub |
| Terminated-rider projection skip | Soft | Client UX question; not required to stop crash if table exists |

---

## 8. Severity / owner / priority

| Field | Value |
|-------|--------|
| Severity | **Critical (UAT blocker)** — endless loop forces hard kill; blocks Projected Values on all 6 policies carrying these riders |
| Owner | **Conversion** (missing QuikAint emit) + **Client** (optional QLAdmin projection-scope question) |
| Priority | Active / No-Go until gates |
| Duplicate of open item? | **No** |

---

## 9. G0 checklist

- [x] Issue folder created under `Issue_Log_Items/Issue_51/`
- [x] Intake summary written
- [x] Example policies listed (`010348734C` + 5 peer riders)
- [x] Owner and priority assigned
- [x] No code or rulebook changes made

**Recommended next status:** **Planning**  
**Next agent:** Planning Agent (Cursor Grok 4.5)
