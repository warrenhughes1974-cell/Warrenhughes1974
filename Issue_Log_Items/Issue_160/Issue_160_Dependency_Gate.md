# Issue #160 — Dependency Gate

**Issue:** #160 — PUA phase stays Expired (56) instead of Surrendered (55) when base surrenders
**Framework stage:** Dependency Gate (G2)
**Generated:** 2026-09-07
**Status:** **PASS (conditional)**

---

## Checklist

### Source data

| Check | Met? |
|---|---|
| Required LifePRO extract(s) present | **Met** — rulebook already maps PPBEN `STATUS_CODE` → `MPHSTAT`; base phase 1 terminal status (55) is already correctly derived from PPOLC before it reaches the PUA cache. No new source field needed. |
| Extract row count > 0 | **Met** — 6,956 current `quikridr` rows; 71 candidate PUA rows identified |
| Column headers documented | **Met** — `STATUS_CODE` in `Sync_Rulebook_quikridr.csv`; base cache fields in `_cache_quikridr_base_phase` |
| Extract date/version matches batch under test | **Met** — current Output is the defect state; fix uses the same PPBEN/PPOLC data already read |
| Re-extract required? | **N/A** — defect is override-logic wiring (missing branch), not missing/incomplete source data |

### Field definitions

| Check | Met? |
|---|---|
| QLAdmin target table confirmed | **Met** — `quikridr.MPHSTAT` (C2) on PUA rider rows |
| QLAdmin target field semantics confirmed | **Met** — status code table confirmed (`55`=Surrendered, `56`=Expired) in `plan_analysis/status_analysis/status_analysis_runner.py` |
| LifePRO source field semantics confirmed | **Met** — base phase terminal sync already resolves 55 correctly; PUA's own PPBEN status is the value currently leaking through |
| Transformation notes identified | **Met** — new `elif base_status == 55` branch in `_apply_pua_rider_inheritance`, mirroring the existing #108D (44/45→54) pattern |

### Client clarification

| Check | Met? |
|---|---|
| Scope boundary agreed | **Conditional** — Brianna/Warren scoped this to **surrenders (55)** specifically. Related base=53/57/50 gaps are documented but explicitly **not** in this pass pending a separate Warren decision (see Planning §5, Open Questions). |
| Business rule for edge cases | **Open** — whether a PUA that lapsed/expired independently *before* the base surrendered should still be forced to 55. Not observed in the current 71-row sample (no counter-examples found); default assumption is "always follow base to 55" unless Warren/Brianna say otherwise. |
| Retention / filtering | N/A |
| UAT acceptance criteria stated | **Met** — all 71 current base=55/PUA=56 policies must show PUA=55; sample of 5 confirmed in Planning §10 |

### Evidence

| Check | Met? |
|---|---|
| Example policies identified | **Met** — 9010360289C, 9010367705C, 9010376522C, 9010379405C, 9010391228C (+ 66 more; full list from Discovery query) |
| Compare support claim | **Met** — direct join on current `Output/quikridr.csv`: 692 base=55 policies, 71 with a PUA phase, 71/71 (100%) currently at PUA=56 |
| Before-state measurable | **Met** — current `quikridr.csv` |

### Regression guards

| Check | Met? |
|---|---|
| Plan preserves #60 SD-60-3/4/5/6/7 (PUA <50→41, date/age inheritance) | **Met** — new branch is additive, does not touch the `< 50` branch |
| Plan preserves #108D (base 44/45 → PUA 54) | **Met** — new branch is `elif`, placed after 44/45 and after <50, does not intercept those cases |
| Plan preserves #119 (PUA MPAR=0) | **Met** — untouched, set earlier in the same function |
| Plan preserves SD-60-11 (overrides gated to PUA only, via `_is_paid_up_addition_product`) | **Met** — new branch stays inside the same gated function |
| Plan does not alter non-PUA rider status logic | **Met** — no other code path touched |
| Plan does not extend to base 53/57/50 without approval | **Met** — explicitly scoped out this pass |

---

## Gate result

**PASS (conditional)** — all data/field/evidence checks pass outright. The one open item is not a data or scope-definition gap but a **direct conflict with the locked SD-60-12 decision** (Issue #60, Risk G3, "terminated-base PUA keep current status"). Per the workspace conflict-notification rule, this must be surfaced to Warren **before Development**, not silently resolved here.

## Blockers

**Soft blocker — requires Warren's explicit approval before Development, not a data blocker:**

> #160 proposes to carve out an exception to **SD-60-12** for base=55 specifically (same pattern already used for base 44/45 → 54 under #108D). Framework auto-chain may continue to Risk, but Development must **not** proceed until Warren confirms this carve-out in writing.

## Recommended status

Risk Complete (pending) — Awaiting Development approval, **conditional on Warren's SD-60-12 carve-out sign-off**.
