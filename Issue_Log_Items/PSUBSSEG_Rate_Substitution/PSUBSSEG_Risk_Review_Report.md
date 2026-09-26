# PSUBSSEG Rate Substitution — Risk Review Report

**Date:** 2026-08-31
**Framework stage:** Risk (no code)
**Recommendation:** **GO (conditional)** — see conditions below

---

## 1. Blast radius

| Surface | Touched? | Notes |
|---|---|---|
| `Output/rates/` QuikTvs, QuikNps, QuikCvs, QuikGps + QuikPl* keys | **Yes** — 18 plans (E1–E5), ~28k rows | Only tables the issue owns |
| All other rate rows / plans | No — byte-identical regression requirement | |
| Policy tables (quikmstr etc.) | No | No plan splits (EFFDATE confirmed) |
| Rulebooks / crosswalks / app.py logic | No (APP_VERSION bump only) | |
| Existing loaders (#40/#42/#96/#106 paths) | No modification; additive step after them | |

## 2. Risk register

| # | Risk | Sev | Likelihood | Mitigation |
|---|---|---|---|---|
| R1 | First-ever non-19000101 EFFDATE rows: QLAdmin load path or DBF templates mishandle the new band | High | Low | EFFDATE field exists in template DBFs (append-only, no schema change); UAT anchor policies on both sides of the band boundary; partial reload via `Test_Validation/` before full handoff |
| R2 | Wrong reserve basis fields (MORT/RSVINT) on 19950101 QuikPlTv keys (OI-1) | Med | Med | Crosswalk-first; copy-forward fallback is explicitly flagged in validation report for Eric sign-off; factors themselves are authoritative either way |
| R3 | `1L10SO` full replacement changes client-visible reserve values for 449 policies | Med | Certain (intended) | That is the fix; before/after diff published as validation evidence; current values match no authoritative segment (overlap ≤0.37) |
| R4 | Duplicate/colliding cells with shipped L17 RV (#96) or inherited CV (#40) emits | Med | Low | Loader skips already-emitted keys (first-writer wins); existing cell-collision BLOCKER gate remains the hard stop |
| R5 | Premium fills (E5) emit under wrong VarGP mode for some plans | Low | Med | OI-3 skip-and-report guard; skipped plans stay exactly as today |
| R6 | PSUBSSEG mis-parse (sex bands, TYPE_FLAG variants) redirects a slot that shouldn't move | High | Low | Manifest CSV published *before* emit; validator does full-grid source-vs-emitted compare per band; A1 probe re-verifies TYPE_FLAG 2/4 rows are non-rate-bearing |
| R7 | Tranche 2 arrives later and overlaps Tranche 1 plans (e.g. `170858` premium fill now, RV band later) | Low | High | Substitution manifest is idempotent and re-runnable; Tranche 2 is additive bands on distinct segments |

## 3. Closed-row conflict check (Framework rule 13)

Reviewed `Completed_Issues_Release_Validation_Guide.md` rows for #40, #42, #96,
#106, PUA-CV, DV-NATIVE:

- **No conflicts.** This work extends the same duration/emit conventions those
  rows locked; it does not undo, weaken, or bypass any of them.
- #106 identity duration and #96 L17 full-annual expansion are reused untouched.
- Guide row for this issue will be added at Closure (rule 12), plus fail-closed
  smoke in `SMOKE_JOBS` (rule 14).

## 4. Go/No-Go conditions

**GO** for Tranche 1 Development, conditional on:

1. Warren's explicit Development approval (framework gate).
2. OI-2 default accepted: `5667AT` reserves left absent (LifePRO 95-era RV is
   genuinely zero) — say now if you want explicit `.00` rows instead.
3. R3 acknowledged: `1L10SO` reserve/net-premium values will visibly change for
   449 policies (63 active) — this is the intended correction.

**NO-GO** remains on Tranche 2 (13 missing segments) until New Era data lands.

## Gate criteria (G3)

- [x] Risk register published
- [x] Blast radius documented
- [x] Closed-row conflict check performed (none found)
- [x] No code changes
