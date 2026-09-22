# Issue #152 — Intake Summary

**Issue:** #152 — Val X Modal Includes Rider  
**Framework stage:** Intake Agent (G0)  
**Status recommendation:** Intake Complete → Planning → Dependency Gate → Risk  
**Generated:** 2026-09-22  
**Owner:** Conversion  
**Priority:** Go-No Go  
**Stage model:** Cursor Grok 4.6 (Warren override 2026-09-22; locked Grok 4.5 unavailable — same-day override already used on this framework)

---

## Client symptom (verbatim + normalized)

**Verbatim (08/18):** Anything with a rider is overstated on the evaluation modal / annual. Eric’s read: QLAdmin is using total premium (base + rider). Rider premium is captured on the rider row. Question for Robert.

**Normalized (09/22):** This is a conversion Prem/Unit defect on interest-sensitive (BF) base rows, not a reason to reopen Closed **#128**. LifePRO already puts the rider’s mode premium on the rider row. When the base `ANN_PREM_PER_UNIT` is blank, Closed **#26 / #88 / #137** still annualize the **full** base `MODE_PREMIUM` (which already includes those riders) and write that into `quikridr.MPREM`. QLAdmin valuation then multiplies Prem/Unit × units on the base **and** still values the rider row, so the rider is counted twice.

Workbook `docs/Valuation File Comparison Research.xlsx` sheet `Mode Premium & Gr Ann Prem ` (trailing space in the sheet name):

| Policy | Val X base modal | Note on the sheet | Current conversion Prem/Unit × units | Current `QuikValf.dbf` base `MPREM1` |
|--------|-----------------:|-------------------|--------------------------------------:|-------------------------------------:|
| 9010723388 | **782** | Annual $882, SU $100 | 8.82 × 100 = **882** | **882.00** |
| 9010723386 | **752** | Annual $852, SU $100 | 8.52 × 100 = **852** | **852.00** |
| 9011069655 | **847** | Annual $869, SU $22 | 8.69 × 100 = **869** | **869.00** |

The old verbal **$827** is not the Val X base for 9011069655. Val X on that policy is **847**. **827** is 9010723386’s billed `MMODEPREM` after Closed **#139** withheld the $25 ISWL fee (852 − 25).

## Example policies

| QLA policy | Role | Current phase-1 `MPREM` | Proposed phase-1 `MPREM` |
|------------|------|------------------------:|-------------------------:|
| **9010723388C** | Eric annual gold | 8.82 | **7.82** |
| **9010723386C** | Eric annual gold | 8.52 | **7.52** |
| **9011069655C** | Eric annual gold | 8.69 | **8.47** |
| **9010987095C** | Two active riders (SU $1.22 + SL $1.22) | 7.841481 | **7.48** |
| 9010779552C | Out of scope — base ANN populated (7.73000) | 7.73000 | **Unchanged** |
| 9010767171C | Out of scope — base ANN populated (2.16800) | 2.16800 | **Unchanged** |
| 9010722550C | Closed **#137** gold — riders terminated | 8.71966 | **Unchanged** |
| 9010779727C | Closed **#88** gold (`010779727C`) — no positive active SU/SL/OR | 5.8615 | **Unchanged** |

## Suspected domain

Rider / premium — `quikridr.MPREM` blank-`ANN_PREM_PER_UNIT` fallback on **phase-1 BF** only. Not billed `quikmstr.MMODEPREM`. Not Issue **#153** fees.

## In scope (first pass)

- When phase-1 BF `ANN_PREM_PER_UNIT` is blank/zero **and** the policy has at least one active `SU` / `SL` / `OR` rider with `MODE_PREMIUM` > 0, subtract the sum of those rider mode premiums from the base `MODE_PREMIUM`, then run the existing **#88 / #137** `blank_ann_annual_ppu` math.
- Keep the rule **structural** (recomputed from the active extract). Do not freeze the old 35-policy 6/30 list. On PPBEN **20260831** the same structure is **33** policies.
- Subtract **every** qualifying active rider on the policy (9010987095 must lose both $1.22 amounts).
- Preserve rider rows, including Closed **#142** `9SUBLF`.
- Preserve `quikmstr.MMODEPREM` (Closed **#139** fee withhold stays).

## Out of scope (first pass)

- Policies with populated base `ANN_PREM_PER_UNIT` — Closed **#26** already uses ANN. Nine such policies on 8/31 have active premium riders (examples 9010779552, 9010767171).
- Changing rider `MPREM`, units, `MVPU`, `VANISH`, or fees.
- Folding Issue **#153** (valuation adding the policy fee back) into this fix, or undoing **#139**.
- Reopening Closed **#128**. Remaining QuikVal modal leftovers stay on **#153** / **#154**.
- Changing modal factors (**#21J / #137**). Quarterly LifePRO 25% vs QLAdmin 27% on 9010987095 is a residual annualized difference, not this issue.
- Claiming a **fresh** QLAdmin valuation has already passed. Current `docs/Valuation/QuikValf.dbf` is dated **2026-06-30** and still shows the doubled base amounts.

## Related issues

| ID | Relationship |
|----|----------------|
| **#128** | Closed 09/22/2026 as the umbrella. **Do not reopen.** This split owns the rider double-count. |
| **#88** | Closed. Blank ANN uses annualized `MODE_PREMIUM` ÷ units. Issue 152 would **narrow that MODE input** by removing separately loaded rider premiums first. **Written conflict until Warren approves the exception.** “Go through the development process” is **not** that exception and is **not** Development approval. |
| **#26** | Closed. Populated `ANN_PREM_PER_UNIT` → `MPREM` stays. |
| **#137** | Engine modal-factor overlay on the blank-ANN path. Keep `blank_ann_annual_ppu`. Gold 9010722550C is not a candidate (riders terminated). Tracking is still Ready for Client UAT; there is no Closed #137 guide row. |
| **#139** | Closed. ISWL fees withheld; billed mode premium reduced. Do not put the fee back. |
| **#142** | Closed. Active SL emits as `9SUBLF`. Preserve those rows; only adjust the base fallback input. |
| **#153** | Separate open issue (valuation fee). Do not fold it in. |
| **#25** | MPOLICY padding — preserve. |

## Immediate blockers at intake

**Development-entry blocker (not an Intake stop):** Closed **#88** guide row currently says blank ANN uses annualized **MODE_PREMIUM** ÷ units. Subtracting rider mode premium before that division conflicts with that written How-clause until Warren approves the exception in writing. Framework rule 13: stop and notify Warren before implementing. This pre-development chain records the conflict and **does not start Development**.

No missing extracts, field definitions, or example policies.

## Artifact inventory

| Artifact | Status |
|----------|--------|
| Discovery notes | `Issue_152_Discovery_Notes.md` (08/18; policy numbers and $827 now superseded by 09/22 source proof) |
| Tracking row | `Issue_152_Tracking_Sheet_Row.tsv` |
| Comparison workbook | `docs/Valuation File Comparison Research.xlsx` sheet `Mode Premium & Gr Ann Prem ` |
| Val X | `docs/Valuation/VALXLIFE.TXT` (6/30; 3,152 rows) |
| QuikValf (before-state) | `docs/Valuation/QuikValf.dbf` MVALDATE 2026-06-30 |
| PPBEN 6/30 | `QLA_Migration/Source/PPBEN_PolicyBenefit_Extract_20260630.csv` — **35** candidates, rider modal total **$319.61** |
| PPBEN 8/31 | `QLA_Migration/Source/PPBEN_PolicyBenefit_Extract_20260831.csv` — **33** candidates, rider modal total **$303.02** |
| Current Output | `quikridr.csv` / `quikmstr.csv` (newest plan/rate package 20260831) |
| Insertion point | Root / `QLA_Migration/app.py` ~9102–9146 (`Issue 26/88/137` MPREM interceptor) plus `qla_core/modal_premium_factors.py` `blank_ann_annual_ppu` (call site only; helper stays) |

## Severity / owner

- **Severity:** Go-No Go on the Val X modal comparison for the structural BF + blank-ANN + active rider population (33 on the current 8/31 extract).
- **Owner:** Conversion (Warren). Sheet owner Eric.
- **Assigned:** Warren.

## Gate criteria (G0)

- [x] Issue folder exists under `Issue_Log_Items/Issue_152/`
- [x] Intake summary written
- [x] Example policies listed
- [x] Owner and priority assigned
- [x] No code or rulebook changes made
- [x] Closed **#128** not reopened
- [x] Closed **#88** written conflict recorded; Development not started
