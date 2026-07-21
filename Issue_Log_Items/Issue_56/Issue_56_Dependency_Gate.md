# Issue #56 — Dependency Gate

**Issue:** #56 — PUA CV is incorrect  
**Framework stage:** Dependency Gate (G2)  
**Generated:** 2026-07-13  
**Model:** Cursor Grok 4.5 (locked)  
**Gate result:** **CONDITIONAL PASS** — source/trace enough for Risk; **Development blocked** until client answers on correct PUA CV + intended plan key  

---

## Decision

| Gate | Result |
|------|--------|
| G0 Intake | **Pass** |
| G1 Planning | **Pass** |
| G2 Dependencies | **Conditional Pass** — extracts and mechanism confirmed; acceptance criteria incomplete |
| G3 Risk | **Ready** — quantify options A/B/(C); expect **conditional Go** only after client Qs |

**Do not start Development** on PUA `MPLAN` rewrite or QuikCvs emit until Risk completes and client confirms LifePRO PUA CV + plan-key design (`1POPUA` vs `*PA`).

---

## Source data

| Check | Met? | Notes |
|-------|------|-------|
| Required LifePRO extract(s) present | **Met** | PPBEN, PPBENTYP, PAAGERAT |
| Extract row count > 0 | **Met** | `960 PO PUA` CV = 200 PAAGERAT rows |
| Column headers documented | **Met** | |
| Extract date/version matches batch | **Met** | 20260630 with current Output |
| Re-extract required? | **N/A** | Not indicated |

## Field definitions

| Check | Met? | Notes |
|-------|------|-------|
| QLAdmin target table confirmed | **Met** | `quikridr` + `QuikCvs` / `QuikPlCv` |
| QLAdmin target field semantics | **Partial** | CV is computed from rates, not loaded `MCV*`; plan key for rate lookup disputed |
| LifePRO source field semantics | **Met** | PAAGERAT attained-age CV for PUA |
| Transformation notes | **Partial** | Attained-age → QuikCvs placement needs Risk/actuarial care (#37/#41 lessons) |

## Client clarification

| Check | Met? | Notes |
|-------|------|-------|
| Scope boundary agreed | **Met** | PUA CV only; base CV out of scope |
| Business rule for plan key (`1POPUA` vs `*PA`) | **Missing** | Blocks choosing Option A vs B |
| Correct LifePRO PUA CV dollar | **Missing** | Needed for UAT acceptance |
| UAT acceptance criteria stated | **Missing** | Pending Q1–Q3 |
| Screenshots | **Missing** | Preferred for $6,628.32 location |

## Evidence

| Check | Met? | Notes |
|-------|------|-------|
| Example policies identified | **Met** | `010310404C` (+ `1960PA` peers) |
| Before-state measurable | **Met** | `MPLAN=1960PA`; no QuikCvs for PUA plans; face $5,942.78 |
| Client wrong-value claim | **Met** | $6,628.32 > face documented |

## Regression guards

| Check | Met? | Notes |
|-------|------|-------|
| Plan preserves #25 MPOLICY | **Met** | Explicit non-touch |
| Plan preserves #26 MPREM | **Met** | Explicit non-touch |
| Plan does not alter unrelated rulebooks | **Met** | Base CV / UL MCV out of scope |

---

## Blockers (for Development — not for Risk)

| ID | Blocker | Owner | Requested action |
|----|---------|-------|------------------|
| OBQ-1 | LifePRO correct PUA CV for `010310404C` | Client (Eric) | Provide dollar + date basis |
| OBQ-2 | Intended QLA PUA plan key | Client / New Era | `1POPUA` catalog vs synthetic `1960PA` |
| OBQ-3 | Screenshot of $6,628.32 | Client | Confirm UI path |

---

## Recommended issue status

**Ready for Risk Review**

Tracking Risk column **No-Go** (Eric) remains appropriate as a **pre-Development** flag until G3 and OBQ-1/2 clear.

---

## Gate G2 checklist

- [x] Dependency gate document published  
- [x] Status Conditional Pass — Risk may proceed; Development may not  
- [x] Tracking sheet update recommended  
- [x] No code changes  
