# Issue #152 — Dependency Gate

**Issue:** #152 — Val X Modal Includes Rider  
**Framework stage:** Dependency Gate (G2)  
**Generated:** 2026-09-22  
**Stage model:** Cursor Grok 4.6 (Warren override 2026-09-22; Grok 4.5 unavailable)  
**Status:** **PASS (MET)**

---

## Checklist

### Source data

| Check | Met? |
|-------|------|
| Required LifePRO extract(s) present in `QLA_Migration/Source/` | **Met** — `PPBEN_PolicyBenefit_Extract_20260630.csv` and `PPBEN_PolicyBenefit_Extract_20260831.csv` (different MD5s); `PPOLC_PolicyMaster_Extract_20260831.csv` |
| Extract row count > 0 | **Met** — each PPBEN 11,698 data rows |
| Column headers documented | **Met** — `POLICY_NUMBER`, `BENEFIT_SEQ`, `BENEFIT_TYPE`, `STATUS_CODE`, `ANN_PREM_PER_UNIT`, `MODE_PREMIUM`, `NUMBER_OF_UNITS`, `PLAN_CODE` |
| Extract date/version matches batch under test | **Met** — current Output / newest plan-rate package is **20260831**; 6/30 PPBEN + VALXLIFE prove the original 35-policy comparison cut |
| Re-extract required? | **N/A** |

### Field definitions

| Check | Met? |
|-------|------|
| QLAdmin target table confirmed | **Met** — `quikridr.MPREM` (annual Prem/Unit). Valuation multiplies by units (`QuikValf.MPREM1`) |
| QLAdmin target field semantics confirmed | **Met** — Closed #26/#88/#137; Help / current interceptor at `app.py` ~9102 |
| LifePRO source field semantics confirmed | **Met** — base BF `MODE_PREMIUM` includes active rider modal when base ANN is blank; Val X BF seq-1 `MODAL_PREMIUM` is base-only |
| Transformation notes identified | **Met** — subtract rider modal from the blank-ANN MODE input, then existing `blank_ann_annual_ppu`; money via `format_mprem_ppu` |

### Client clarification

| Check | Met? |
|-------|------|
| Scope boundary agreed | **Met for research** — structural BF + blank ANN + active SU/SL/OR MODE>0. Populated ANN out. #128 stays closed. #139/#142/#153 not in this fix |
| Business rule for edge cases | **Met for research** — STATUS A and MODE>0; subtract every such rider; no frozen 35. Negative rider (9010779727) stays out |
| Retention / filtering | **Met** — do not delete rider rows; do not strip terminated SL (#142 / #27) |
| UAT acceptance criteria stated | **Met** — conversion: gold MPREM 7.82 / 7.52 / 8.47 / 7.48; MMODEPREM and rider rows unchanged. **Fresh QLAdmin valuation** is a **UAT criterion after Development**, not a gate blocker. Current `QuikValf.dbf` is **2026-06-30** before-state (882 / 852 / 869) |
| Closed #88 written exception | **Missing for Development** — not a missing extract. Framework rule 13. See Blockers |

### Evidence

| Check | Met? |
|-------|------|
| Example policies identified | **Met** — 9010723388 / 9010723386 / 9011069655 / 9010987095; non-candidates 9010779552 / 9010767171 |
| Screenshots or docx | **Met** — comparison workbook sheet `Mode Premium & Gr Ann Prem ` notes Annual $882 SU $100; $852 SU $100; $869 SU $22. Val X 782 / 752 / 847. Old verbal $827 is not Val X |
| Before-state measurable | **Met** — current Output MPREM 8.82 / 8.52 / 8.69 / 7.841481; QuikValf MPREM1 882 / 852 / 869 / 52.92; 6/30 = 35, 8/31 = 33 |

### Regression guards

| Check | Met? |
|-------|------|
| Plan preserves Issue #25 MPOLICY padding | **Met** |
| Plan preserves Issue #26 MPREM mapping | **Met** — populated ANN unchanged (9 out-of-scope policies) |
| Plan does not alter unrelated rulebooks | **Met** — interceptor only; rulebook comment at most |
| Plan does not undo Closed #139 | **Met** — MMODEPREM / fees untouched |
| Plan does not undo Closed #142 | **Met** — `9SUBLF` rows preserved |
| Plan does not reopen Closed #128 | **Met** |
| Plan does not silently contradict Closed #88 | **Held for Development** — conflict is recorded; Warren’s written exception is required **before code**. This gate does not treat that missing exception as a missing source file |

---

## Gate result

**PASS (MET)** — source, fields, examples, and population proof are in hand. Framework auto-chain continues to Risk in this session.

This is **not** Development approval. This is **not** a Closed **#88** written exception.

Accepted assumptions:

1. Identity is structural (BF seq-1 blank/zero ANN + active SU/SL/OR with MODE>0), not a frozen 35.  
2. Current conversion cut is PPBEN **20260831** (**33**). 6/30 (**35**) is the Val X comparison cut.  
3. `$827` is not Val X for 9011069655.  
4. Fresh QLAdmin valuation has **not** been run and is **not** claimed PASS.  
5. Stage-model override to Cursor Grok 4.6 is Warren-approved **2026-09-22** (same-day as Issue 151 when Grok 4.5 was unavailable).  
6. Negative rider MODE is excluded by the `> 0` filter.

## Blockers

**Development-entry only (does not FAIL this gate):**

| Item | Owner | Required action |
|------|-------|-----------------|
| Closed **#88** written exception | Warren | Explicit written OK to narrow the blank-ANN MODE input by removing separately loaded active rider premiums **before** annualized MODE ÷ units. Then update the #88 guide How-clause at Development/Closure. |
| Development approval | Warren | Separate “Approved for Development” (or equivalent). “Go through the development process” is **neither** of these. |

No missing extracts. No client-data FAIL.

## Recommended tracking status

**Dependency Gate MET → Risk Complete (GO). Awaiting (1) Closed #88 written exception and (2) Development approval. Column B empty. Date Resolved empty.**
