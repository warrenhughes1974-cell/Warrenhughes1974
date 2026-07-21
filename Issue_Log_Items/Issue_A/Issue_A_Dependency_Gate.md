# Issue A — Dependency Gate

**Issue:** A — QuikPlan / PVO / rate-key structural defects (internal)  
**Framework stage:** Dependency Gate  
**Generated:** 2026-07-20  
**Gate status:** **FAIL (Blocked — Awaiting Client Clarification)**  
**Track:** Internal only

---

## 1. Checklist

### Source data

| Check | Met? |
|-------|------|
| Required LifePRO extract(s) present for plan/rate scans | **Met** (current Source / Output usable for diagnostics) |
| Extract row count > 0 | **Met** |
| Column headers documented | **Met** |
| Extract date/version matches batch under test | **N/A** until next conversion run |
| Re-extract required? | **No** for planning |

### Field definitions

| Check | Met? |
|-------|------|
| QLAdmin target tables confirmed (quikplan / QuikPl*) | **Met** |
| TESTRD default-key pattern documented by Robert | **Met** (screenshots + description) |
| Exact QuikPlan “supp type” field name | **Missing** (Eric — Go-Live Item 26) |
| Calc Dfcy / deficiency reserve field semantics | **Partial** — UI known; CSO business rule **Missing** |
| Single-prem authoritative plan list | **Missing** (Eric) |

### Client / SME clarification

| Check | Met? |
|-------|------|
| Scope boundary (internal track A1–A9) | **Met** |
| Business rule: single-prem modal + PAYYRS | **Met** (Robert rule clear) |
| Business rule: default keys even with no rates | **Met** (TESTRD) |
| Business rule: category settings match keys | **Met** |
| Business rule: annuity PAR/VarDB/PVO defaults | **Met** (Robert) |
| Eric single-prem plan list | **Missing** |
| CSO Calc Dfcy yes/no for non-indeterminate plans | **Missing** |
| Annuity int + schg load requirements | **Missing** |
| UAT acceptance criteria (internal) | **Partial** — checklist is interim acceptance |

### Evidence

| Check | Met? |
|-------|------|
| Example plans identified | **Met** |
| Screenshots support claims | **Met** |
| Before-state measurable from current Output | **Met** (diagnostic scans OK) |

### Regression guards

| Check | Met? |
|-------|------|
| Plan preserves Issue #25 MPOLICY padding | **Met** (no policy-key changes in scope) |
| Plan preserves Issue #26 MPREM mapping | **Met** |
| Plan does not alter unrelated rulebooks without approval | **Met** |

---

## 2. Status: **FAIL**

Development of the full Issue A package is **blocked** until SME answers arrive for A1 (Eric list), A2 (CSO Calc Dfcy), A9 field identity (supp type), and A8 annuity int/schg scope.

**Allowed now (no Development):**
- Maintain and run `Issue_A_Conversion_Checklist.md` on every conversion
- Read-only diagnostic scripts / inventory counts
- Cross-link updates to Go-Live Items 07/08/09/10/26/32/40

---

## 3. Blocker list

| # | Blocker | Owner | Requested action |
|---|---------|-------|------------------|
| B1 | Authoritative single-premium plan list | Eric | Send list of SP plans (codes) for this region |
| B2 | Deficiency reserves for non-indeterminate-prem plans | CSO | Yes/No (or plan-list) for Calc Dfcy = TRUE |
| B3 | Supp type field name on QuikPlan | Eric | Confirm which column/UI field = “supp type” |
| B4 | Annuity interest + schg required for go-live | Eric | Which tables/schedules to load |

---

## 4. Recommended issue status

**Blocked — Awaiting Client Clarification**  
(Internal SME = Eric/CSO; not a client UAT package)

Next agent when blockers clear (or for risk on unblocked sub-items only):  
**Risk Agent** — prompt in Planning Report §10.

---

## 5. G2 criteria

- [x] Dependency gate document published
- [x] Status FAIL — do not advance to Risk/Development until user proceeds with waiver or answers
- [x] Tracking updated (master + Issue A checklist)
- [x] No code changes
