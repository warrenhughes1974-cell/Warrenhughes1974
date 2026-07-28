# Issue #121 — Regression Report

**Issue:** #121 — Annual Renewable Term must not emit ETI  
**Framework stage:** Regression Agent  
**Engine version:** v58.44  
**Generated:** 2026-07-28  
**Verdict:** **PASS**

---

## 1. Row counts (post rebatch)

| Table | Rows | Notes |
|-------|-----:|-------|
| `quikmstr` | 5,083 | Expected fleet size |
| ART family policies | 197 | Unchanged population |

---

## 2. Intentional status drift (ART only)

| Population | Before ETI | After ETI |
|------------|----------:|----------:|
| ART `MSTATUS` 44 | 90 | **0** |
| Non-ART `MSTATUS` 44 | — | **120** (preserved) |

Fleet ETI dropped only by the 90 ART false positives (206 historical → 120 remaining non-ART).

---

## 3. Prior-fix guards

| Check | Result |
|-------|--------|
| Non-ART ETI retained | **PASS** (120) |
| Sibling ART `5646AT` / `57ATCR` still 54 | **PASS** |
| RPU (`45`) fleet count | 194 (unchanged class of NFO) |
| #25 / #2 MPOLICY path | Untouched by this change |
| #26 MPREM | Untouched |

---

## 4. Verdict

**PASS** — blast radius confined to ART-family status; permanent-product ETI retained.
