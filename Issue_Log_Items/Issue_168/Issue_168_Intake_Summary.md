# Issue #168 — Intake Summary

**Issue:** #168 — L05 / L14 Reserves Partially Match (form-level UW class key gap)
**Framework stage:** Intake
**Date:** 2026-09-14
**Track:** Client-facing (Jill Burns / CSO), Go-No-Go priority (valuation)

---

## Problem statement

For L14 (`1L14SC`), 131 of 232 rider rows (Preferred/Standard/PQ classes) return $0 or a non-matching reserve because the QLAdmin terminal-reserve table (`QuikTvs`) only carries a matching row under one underwriting-class key (`NT`), even though LifePRO's true reserve for this plan does not vary by underwriting class at all. L05 (`5L0510`/`9L05WP`) has the same symptom but no real reserve source data exists to fix from; that half is a separate, already-drafted data request to CSO/New Era, not this issue's Development scope.

## In scope (Development)

- L14 only: replicate the existing real `QuikTvs` (and `QuikCvs` if it has the same single-class shape — to confirm in Planning) rows currently keyed `NT` onto the `PQ`, `ST`, and `PR` class keys, same values, same age/gender/duration grid.
- Confirm `QuikPlTv` (and `QuikPlCv` if applicable) rate-key rows exist for the added classes so QLAdmin's PVO key layer recognizes them.

## Out of scope

- L05 (`5L0510`, `9L05WP`) — no real source reserve data; stays **Blocked — awaiting source data**.
- Any change to `quikridr.MUWCLASS` mapping logic (`map_rider_uwclass` / `map_uwclass`) — #159's plan-aware mapping is correct and untouched.
- Any change to `*VARY*` flag derivation (`quikplan_rate_variation_flags.py`) — #136's real-variation rule stays exactly as-is; `UWVARYTV` correctly remains `N` for both plans (it reports "does this vary by class," and it truthfully does not — that fact does not change).
- Premium (`GP`/`QuikGps`), gross premium keys, `QuikPlUw`, `MPREM`, `MPOLICY` — untouched.
- Any other plan/form not named above.

## Impacted tables (L14 only)

| Table | Change |
|---|---|
| `QuikTvs` (Output/rates) | Add PQ/ST/PR rows mirroring existing NT rows, same PLAN/AGE/CNTL/GENDER grid |
| `QuikCvs` (Output/rates) | Same treatment **if** CV shows the same single-class shape (to confirm) |
| `QuikPlTv` / `QuikPlCv` (Output/rates, key layer) | Add PQ/ST/PR key rows so QLAdmin's PVO screen shows the class as defined |
| `quikridr.MUWCLASS` | **No change** — already correct per #159 |
| `quikplan` (`*VARY*`, `PLANVALOPT`) | **No change** — `UWVARYTV=N` stays correct and true |

## Client commitment

None yet requested for L14 (code-only fix). For L05, the CSO/New Era data ask (reserve/cash-value factors for L05 by class) stands separately and is not blocked by this issue.

## Stakeholders

- Issue owner: Warren
- Client contact: Jill Burns (CSO)
- Prior related issues: #118 (form-aware UW map), #136 (real-variation PVO rule — must not be violated), #159 (L10/L14 MUWCLASS plan-aware fix)
