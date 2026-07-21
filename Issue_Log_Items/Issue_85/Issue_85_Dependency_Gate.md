# Issue #85 — Dependency Gate

**Issue:** #85 — Duplicate claim headers sharing the same policy + phase  
**Framework stage:** Dependency Gate (G2)  
**Generated:** 2026-07-17  
**Model:** Cursor Grok 4.5 (locked)  
**Gate result:** **PASS — Ready for Risk Review**  
**Code changes:** None  

---

## Source data

| Check | Met? | Notes |
|-------|:----:|-------|
| Real book authority | **Met** | `quikclms.dbf` / `quikclmp.dbf` — 0 dups; 99.8% money balance |
| Converted before-state | **Met** | Output quikclms/quikclmp |
| Structure evidence | **Met** | Issue #84 join-check script + counts |

---

## Field / structure definitions

| Check | Met? | Notes |
|-------|:----:|-------|
| Defect defined | **Met** | Duplicate MPOLICY+MPHASE headers |
| Target pattern defined | **Met** | Policy-book uniqueness |
| Payee re-attach path | **Met** | SD-85-3; D4 options |

---

## Client clarification

| Check | Met? | Notes |
|-------|:----:|-------|
| Scope boundary | **Met** | Structure only; money components stay #84 |
| Decisions listed | **Met** | D1–D5 in Scope Decisions (defaults available) |
| Sequencing vs #84 | **Met** | D5 recommends #85 before #84 Track B |

Open decisions D1–D5 are **non-blocking for Risk** with documented defaults; user should still pick before Development.

---

## Regression guards

| Check | Met? | Notes |
|-------|:----:|-------|
| Preserve #78 payees | **Met** | No invent; re-attach only |
| Preserve #79 CLAIMSTAT rules | **Met** | SD-85-4 |
| Preserve #25/#26 | **Met** | Untouched |

---

## Blockers

**None** for Risk Review.

---

## Gate decision

| Gate | Result |
|------|--------|
| G0 Intake | **PASS** |
| G1 Planning | **PASS** |
| **G2 Dependency** | **PASS** |
| G3 Risk | Next (user advance) |

**Recommended tracking status:** **Ready for Risk Review**  

**Next:** Say **“Proceed to Risk Agent for Issue 85.”**

**Update 2026-07-17:** Decisions D1–D5 **locked** (expert recommendation adopted; see `Issue_85_Scope_Decisions.md` “DECISIONS — LOCKED”). Risk Agent should quantify impact under: D1 hybrid (merge same-claim duplicates ≈327 rows; re-phase distinct claims ≈3,443 rows), D2 sum-and-survive, D3 drop+audit, D4 payees follow claim, D5 #85 before #84 Track B.
