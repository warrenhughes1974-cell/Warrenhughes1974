# Issue #95 — Dependency Gate

**Issue:** #95 — Declared Interest Rates Incorrect  
**Framework stage:** Dependency Gate (G2)  
**Generated:** 2026-07-22  
**Status:** **FAIL**

---

## Checklist

### Source data

| Check | Met? |
|-------|------|
| Required LifePRO extract(s) present in `QLA_Migration/Source/` | **Met** — `PDINTTBL_DeclaredInterestRates_Extract_20260630.csv` + `PDINT_…_20260630.csv` |
| Extract row count > 0 | **Met** — PDINTTBL 37 data rows; PDINT 10 |
| Column headers documented | **Met** — IDENT, TYPE_CODE, DINT_RULE, START/END_DATE, DECLARED_RATE |
| Extract date/version matches batch under test | **Met** — midyear 20260630 used by current rate path |
| Re-extract required? | **N/A** — source rates already match Eric’s stated percents |

### Field definitions

| Check | Met? |
|-------|------|
| QLAdmin target table confirmed (Help / schema) | **Missing** — QuikUint (§7.223) is the **planning hypothesis**; Eric has not confirmed the screen/table under No-Go |
| QLAdmin target field semantics confirmed | **Partial** — MCURRATE/MGTDRATE known for ISWL (#32); not confirmed for SAL/residual plans |
| LifePRO source field semantics confirmed | **Met** — PDINTTBL DECLARED_RATE current tiers verified |
| Transformation notes identified | **Partial** — #32 mirror + N(8.4); non-ISWL history vs current-only open |

### Client clarification

| Check | Met? |
|-------|------|
| Scope boundary agreed (in / out) | **Missing** — “everything but SAL and ISWL” MPLAN membership undefined; SPWL/`1668SP` / riders / `A*` silent |
| Business rule for edge cases | **Missing** — `1SALMI`; historical vs current-only for non-CENII |
| Retention / filtering rules | **Missing** — same as scope |
| UAT acceptance criteria stated | **Partial** — rates by IDENT stated; no sample policies or pass/fail screen |

### Evidence

| Check | Met? |
|-------|------|
| Example policies identified | **Missing** |
| Screenshots or docx support client claim | **Missing** |
| Before-state measurable from current output | **Met** — QuikUint ISWL-only 32 rows; SAL/residual absent; PDINTTBL rates measured |

### Regression guards

| Check | Met? |
|-------|------|
| Plan preserves Issue #25 MPOLICY padding | **Met** — plan-level rates; no MPOLICY touch |
| Plan preserves Issue #26 / #88 MPREM mapping | **Met** — out of touch set |
| Plan does not alter unrelated rulebooks | **Met** — rate loader / QuikUint only (when Dev proceeds) |

---

## Gate result

**FAIL** — do **not** proceed to Risk until blockers below are cleared (or user documents a written waiver / assumption set).

Source data is sufficient and already agrees with Eric’s percentages. Blockers are **scope / target confirmation**, not missing extracts.

## Recommended tracking status

**Blocked — Awaiting Client Clarification**

## Blockers

| # | Blocker | Owner | Requested action |
|---|---------|-------|------------------|
| B1 | Confirm QLAdmin target is **QuikUint** (not `MDEPINT` / `QuikAint` / `DEPINT`) | Eric | Name the screen or field showing the wrong rate |
| B2 | Exact **MPLAN list** (or clear rule) for 3.50% residual bucket | Eric | List plans, or confirm “all non-SAL/non-ISWL **base** life plans in quikplan, excluding riders/annuities” |
| B3 | Clarify **668** vs **669** / **1668SP** | Eric | Which product is in the ISWL 4.50% note? |
| B4 | SAL scope: **`1SALMI`** in or out with SAL OL/ML at 2.00%? | Eric | Yes/No |
| B5 | Non-ISWL emit: **current tier only** vs full PDINTTBL history | Eric | Prefer current-only unless history required |
| B6 | Example policy and/or screenshot (SAL + one residual) | Eric | Optional if B1–B5 answered in writing; strongly preferred |

## What is already proven (non-blocking)

- PDINTTBL current rates = Eric’s 3.50 / 2.00 / 4.50 by IDENT.
- ISWL QuikUint current tier already 4.50% for all 8 MPLANs.
- Gap is absence (or wrong table) for SAL + residual families, not a bad CENII current rate in Output.

## Next step after blockers clear

User prompt: `Proceed to Risk Agent for Issue 95` (Cursor Grok 4.5).
