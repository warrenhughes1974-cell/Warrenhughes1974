# Issue #60 — Dependency Gate

**Issue:** #60 — PUA phase fields + base plan interest (Chris plan)  
**Framework stage:** Dependency Gate (G2)  
**Generated:** 2026-07-14  
**Model:** Cursor Grok 4.5 (locked)  
**Planning ref:** `Issue_60_Planning_Report.md`  
**Scope:** `Issue_60_Scope_Decisions.md`

---

## Status: **CONDITIONAL PASS**

| Track | Gate | Advance to Risk? |
|-------|------|------------------|
| **A — `quikridr` PUA phase fields** | **PASS** | **Yes** |
| **B — Base `1960PO` interest / reserve methods** | **FAIL** (await rates) | **No** until OBQ-1 |

Overall issue status recommendation: **Ready for Risk Review** (Track A). Track B remains **Blocked — Awaiting Actuarial Rates** (Chris/CSO).

---

## 1. Checklist

### Source data

| Check | Track A | Track B |
|-------|---------|---------|
| Required LifePRO extract(s) present | **Met** (PPBEN) | **Met** (CSO crosswalk documents gap) |
| Extract row count > 0 | **Met** | **Met** |
| Column headers documented | **Met** | **Met** |
| Extract date/version matches batch | **Met** (20260630) | N/A |
| Re-extract required? | **No** | **No** — need actuarial codes, not re-extract |

### Field definitions

| Check | Track A | Track B |
|-------|---------|---------|
| QLAdmin target table confirmed | **Met** (`quikridr`) | **Met** (`QuikPlCv` / `QuikPlTv`) |
| QLAdmin target field semantics confirmed | **Met** (Chris + Help/schema usage) | **Met** (fields known) |
| LifePRO source field semantics confirmed | **Met** — Chris **overrides** PUA ISSUE_DATE/AGE | **Missing** — no NFOINT/RSVINT values in crosswalk for `1960PO` |
| Transformation notes identified | **Met** | Partial |

### Client clarification

| Check | Track A | Track B |
|-------|---------|---------|
| Scope boundary agreed | **Met** — Chris plan locked by user; #56 withdrawn | Partial — pilot vs all CRVM plans (OBQ-2) |
| Business rule for edge cases | **Met** with documented defaults (MPAYUP=eff; terminated status → Risk OBQ-4) | **Missing** — rate values |
| Retention / filtering | **N/A** | N/A |
| UAT acceptance criteria | **Met** — `010310404C` phase fields match Chris; then Data Admin + rebuild CV (needs Track B for $) | Soft until rates |

### Evidence

| Check | Met? |
|-------|------|
| Example policies identified | **Met** — `010310404C` (+ peers) |
| Screenshots support claim | **Met** — `evidence/chris_email_pua_screenshots_20260714.png` |
| Before-state measurable | **Met** — 494/494 PUA mismatches |

### Regression guards

| Check | Met? |
|-------|------|
| Preserves Issue #25 MPOLICY padding | **Met** (plan: no MPOLICY touch) |
| Preserves Issue #26 MPREM mapping | **Met** (plan: no MPREM touch) |
| Does not alter unrelated rulebooks | **Met** (surgical PUA inheritance; rates only when Track B unlocked) |
| Does not add PA plan / factors | **Met** (SD-60-1 / SD-60-2) |

---

## 2. Blockers (Track B only)

| Blocker | Owner | Requested action |
|---------|-------|------------------|
| `1960PO` NFOINT / reserve interest & methods blank (CRVM, no code) | Chris / CSO actuarial | Provide loadable QLA codes (or numeric schedule) for QuikPlCv NFOINT and QuikPlTv RSVINT, RSVMETH, INTMETHTV for `1960PO`; confirm OBQ-2 scope |
| Optional: STOREMEANS / CALCMIDS | CSO | Per existing rate gap grid |

**Waivers:** None for inventing interest. User waiver applies only to **adopting Chris’s phase rules** over #56.

---

## 3. Accepted Planning assumptions (Track A)

| Assumption | Value | Revisit if |
|------------|-------|------------|
| MPAYUP | = MEFFDATE (not +1 year) | Chris/UAT prefers +1 |
| MPHSTAT on terminated base | Risk recommends restrict to active base; default literal Chris = all PUA → 41 until Risk locks | OBQ-4 |
| Synthetic `*PA` MPLAN | Keep; omit from plan file | Chris later requires PA plan |

---

## 4. Recommended issue status update

| Item | Status |
|------|--------|
| **#60** | **Ready for Risk Review** (Track A) · Track B blocked |
| **#56** | **Withdrawn / superseded by #60** (do not Develop) |

---

## Gate G2 checklist

- [x] Dependency gate document published  
- [x] CONDITIONAL PASS documented (A PASS / B FAIL)  
- [x] Tracking sheet to be updated  
- [x] No code changes  

**Next:** Risk Agent (Track A) on Cursor Grok 4.5.
