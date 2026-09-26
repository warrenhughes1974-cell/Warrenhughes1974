# Issue #155 — Dependency Gate

**Date:** 2026-09-24  
**Stage:** Dependency Gate (G2). No code changes.  
**Status:** **FAIL — Blocked on scope decision (Warren) and QLAdmin ISWL engine question**

---

## Source data

| Check | Met? |
|---|---|
| Required LifePRO extracts in `QLA_Migration/Source/` (PFNDR 6/30, PFNDRDET ISWL subset) | Met |
| Row count > 0 | Met (PFNDR 2,245 of 2,268 QL ISWL policies; 23 missing) |
| Column headers documented | Met |
| Extract date matches batch under test (6/30 → `QLA_VALUATION_DATE=20260630`) | Met |
| Re-extract required | No |

## Field definitions

| Check | Met? |
|---|---|
| QLAdmin target tables confirmed (QuikIswl §7.146; quikprmh/QuikIsrr `MISWL`) | Met |
| QuikIswl seed semantics (latest row = current state; MMONTH/MLASTANNV pattern) | Met — from QL's own 9/23 rows |
| LifePRO field semantics (FUND_BALANCE, GROSS_DEPOSITS, VALUATION_DATE) | Met — roll-forward ties |
| Anniversary skips premiums with `MISWL` populated | **Assumed** — QL stamps MISWL when it allocates; not yet proven on a seeded policy |
| Source of QL ISWL interest (7%), COI (0), expense ($5 + 5%) | **Missing** — not table-driven; QLAdmin-owned |

## Client clarification

| Check | Met? |
|---|---|
| Scope boundary — account exact at conversion date vs. QL tracks LifePRO after go-live | **Missing** (Warren) |
| Edge rule: negative funds → 0.00 | Met (Warren 2026-09-24) |
| Edge rule: 23 policies without PFNDR | Proposed: keep month-0 only, list — Warren to confirm |
| Closed-row override #124 | Conditional OK (2026-09-24) — condition was "test matches LifePRO 8/19". **Test result: does not match after month 1** (QL engine). Needs re-confirmation. |
| Closed-row touch #21F (quikprmh `MISWL`) | **Missing** — Warren written OK |
| UAT acceptance criteria | Proposed: QuikValf MACCTBAL at 6/30 = LifePRO PFNDR balance (≤ $0.01) for all seeded policies |

## Evidence

| Check | Met? |
|---|---|
| Example policies | Met (9010713704/05/07, 9010902968) |
| Before-state measurable | Met (Q QuikIswl 9/23; QuikValf 9/2 and 9/22) |

## Regression guards

| Check | Met? |
|---|---|
| #25 MPOLICY padding preserved | Met (keys reused) |
| #26 / #88 MPREM untouched | Met (quikridr not in scope) |
| #124 month-0 rows preserved | Met by design (seed row added, month-0 kept) |
| #21F CONV_ADJ amounts unchanged | Met by design (only `MISWL` added) |
| Unrelated rulebooks untouched | Met |

## Blockers

| # | Blocker | Owner | Action |
|---|---|---|---|
| 1 | Scope: conversion-date match only, or ongoing match | Warren | Decide |
| 2 | Re-confirm #124 override given test result; OK to add `MISWL` to quikprmh/QuikIsrr (#21F table) | Warren | Written OK |
| 3 | Only if scope = ongoing: can ISWLFE interest/COI/expense be table-driven; where does 7% come from | QLAdmin (Robert) | Answer — cannot be tested from data |

**Recommended status:** Blocked — Awaiting Clarification. Risk not started.

---

## Re-gate 2026-09-24 (Warren decisions) — **PASS**

| Blocker | Resolution |
|---|---|
| 1 Scope | **Match at conversion date.** QLAdmin 7% / no COI / $5 fee taken to QLAdmin separately by Warren (not a conversion dependency). |
| 2 Closed-row OK | **Approved in writing 2026-09-24:** seed row alongside #124 month-0 rows; populate `MISWL` on converted premiums (quikprmh, #21F table) and withdrawals (QuikIsrr, #34 table). |
| 3 QLAdmin engine | Out of this issue's scope (see 1). Proof test kept as evidence. |

Proceed to Risk.
