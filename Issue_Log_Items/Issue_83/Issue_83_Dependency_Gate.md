# Issue #83 — Dependency Gate

**Issue:** #83 — Fleet gender companion rate keys (Values=N when no factors)  
**Framework stage:** Dependency Gate (G2)  
**Generated:** 2026-07-17  
**Model:** Cursor Grok 4.5 (locked)  
**Gate result:** **PASSED** (with accepted scope assumptions)

---

## Dependency Checklist

### Source data

| Check | Met? |
|-------|------|
| Required LifePRO extract(s) present (existing R5 rate package) | **Met** |
| Extract / current Output rates available for before-state | **Met** |
| Column headers documented (QuikPl* / factor CSVs) | **Met** |
| Extract date/version matches batch under test | **Met** (current Output/rates) |
| Re-extract required? | **N/A** — key emit gap, not missing source cells |

### Field definitions

| Check | Met? |
|-------|------|
| QLAdmin target tables confirmed (QuikPlGp/Db/Cv/Tv/Dv) | **Met** |
| Values column semantics confirmed (UI: factor presence Y/N) | **Met** |
| Gender member source confirmed (QuikPlGd) | **Met** |
| Transformation notes (clone key, no factor invent) | **Met** |

### Client clarification

| Check | Met? |
|-------|------|
| Scope boundary agreed (fleet gender companions, Values=N) | **Met** (user) |
| Business rule for edge cases | **Met** — accepted assumptions below |
| Retention / filtering rules | **N/A** |
| UAT acceptance criteria stated | **Met** — see below |

### Evidence

| Check | Met? |
|-------|------|
| Example plan identified (`221END`) | **Met** |
| Screenshots support client claim | **Met** |
| Before-state measurable | **Met** — 259 gaps; evidence CSV |

### Regression guards

| Check | Met? |
|-------|------|
| Plan preserves Issue #25 MPOLICY padding | **Met** (untouched) |
| Plan preserves Issue #26 MPREM mapping | **Met** (untouched) |
| Plan does not alter unrelated rulebooks | **Met** |
| No factor invent (#77/#80 preserve) | **Met** |

---

## Accepted scope assumptions (locked for Risk/Dev unless user overrides)

| ID | Assumption |
|----|------------|
| **A-83-1** | Scope is **gender F/M companions only** (not UW/Band expansion in #83). |
| **A-83-2** | Companions only when QuikPlGd contains **both** F and M, and the family already has ≥1 F/M key. |
| **A-83-3** | No factor grid invent → QLAdmin **Values=`N`** for companions without factors (fleet audit: 0 unexpected factor orphans). |
| **A-83-4** | Plan Values Options may set **GDVARY\*=Y** when a family gains a second gender key (#77 multi-value rule) — intentional. |
| **A-83-5** | New companion assumption fields filled via existing AssumptionProvider / #80 composite (same as sibling plan codes). |

---

## Open items (non-blocking)

| Item | Status |
|------|--------|
| OBQ — expand to UW companions later? | Parked; not required to start Risk |
| Example policy numbers | None; plan-level UAT sufficient |

---

## UAT acceptance criteria (draft)

1. `221END` QuikPlCv keys include Sex=`F` and Sex=`M`; Female **Values=`N`**; Male remains **Values=`Y`**.
2. Fleet: every plan with QuikPlGd F+M and an F/M key on a family also has the companion gender key on that family.
3. Factor table row counts unchanged for companions (no invent).
4. `app.py` / rate pipeline emits companions on GENERATE RATE TABLES (version bump).
5. Non-candidate plans (no F+M members, or family with no F/M keys) unchanged.

---

## Gate decision

**PASSED** — Ready for Risk Agent on explicit user advance.

**Do not start Development** until Risk clears and user says **Approved for Development** on **Composer 2.5**.

---

## Deliverables

| File | Path |
|------|------|
| Intake | `Issue_Log_Items/Issue_83/Issue_83_Intake_Summary.md` |
| Planning | `Issue_Log_Items/Issue_83/Issue_83_Planning_Report.md` |
| Dependency Gate | `Issue_Log_Items/Issue_83/Issue_83_Dependency_Gate.md` |
| Evidence | `Issue_Log_Items/Issue_83/evidence/issue83_gender_companion_key_gaps.csv` |
| Summary | `Issue_Log_Items/Issue_83/evidence/issue83_gender_companion_summary.md` |
| Research script | `QLA_Migration/_research_issue83_gender_companion_keys.py` |

---

## Recommended next prompt

```
Proceed to Risk Agent for Issue #83.
```
