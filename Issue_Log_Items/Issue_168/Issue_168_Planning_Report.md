# Issue #168 — Planning Report

**Issue:** #168 — L14 Reserve/Cash Value Class-Key Replication (L05 split out — data-blocked)
**Framework stage:** Planning
**Date:** 2026-09-14

---

## Confirmed shape (from `quikplan_rate_variation_flags.analyze_rate_segmentation()` against live source extracts)

| Plan | Family | Real source rows | Distinct UW classes in source | Conclusion |
|---|---|---:|---:|---|
| `1L14SC` | TERMINAL_RESERVE (RV → `QuikTvs`) | 2,874 | **1** | LifePRO does not vary this plan's reserve by class |
| `1L14SC` | CASH_VALUE (CV → `QuikCvs`) | 2,836 | **1** | Same — CV also class-invariant on this plan |
| `1L14SC` | GROSS_PREMIUM (PR → `QuikGps`) | 268 | 4 | Premium **does** vary by class — untouched, working as designed |
| `5L0510` | TERMINAL_RESERVE / CASH_VALUE | 0 real rows (default stub only) | n/a | No real data anywhere — **not fixable in code**, out of scope for this issue |

So both `QuikTvs` and `QuikCvs` need the same treatment for L14; `QuikGps` (premium) is correct as-is and must not be touched.

## Proposed fix (L14 only)

1. **Read** the current `QuikTvs` and `QuikCvs` rows for `PLAN=1L14SC` where `UWCLASS=NT` (or whatever the single real class label the emit currently uses — confirm exact label at Development time, evidence points to `NT`).
2. **Replicate** each such row three times, changing only the `UWCLASS` field to `PQ`, `ST`, and `PR` — every other field (AGE, CNTL, TV0–TV9/GP columns, GENDER, BAND, ISSCNTRY, ISSUEST, EFFDATE) stays byte-identical to the source `NT` row.
3. **Add matching key rows** to `QuikPlTv` and `QuikPlCv` (the PVO key/enumeration layer) for `PLAN=1L14SC` × `UWCLASS ∈ {PQ, ST, PR}` so the Plan Values Options screen shows real, in-use keys (`Values=Y`) for these combinations, matching the pattern `Issue_118`'s `apply_issue118_output_remap.py` already used to add L14 T/Q/R **premium** keys.
4. **Do not touch** `quikridr.MUWCLASS`, `map_rider_uwclass`, `map_uwclass`, or any `*VARY*` flag. `UWVARYTV`/`UWVARYCV` for `1L14SC` correctly stay `N` — this fix does not change whether the plan varies by class (it truthfully doesn't); it only makes the one true number retrievable under every class key a real policy carries.
5. **No premium, MPREM, MPOLICY, MBAND, or non-L14 plan is touched.**

## Files expected to change

| File | Change |
|---|---|
| New: `Issue_Log_Items/Issue_168/tools/apply_issue168_l14_reserve_class_replication.py` | Standalone Output-apply script (read `QuikTvs`/`QuikCvs`/`QuikPlTv`/`QuikPlCv`, write replicated rows) — mirrors the `Issue_118`/`Issue_159` apply-script pattern; does not touch `app.py` engine logic |
| `QLA_Migration/Output/rates/QuikTvs.csv` | +PQ/ST/PR rows for `1L14SC` (replicated from NT) |
| `QLA_Migration/Output/rates/QuikCvs.csv` | +PQ/ST/PR rows for `1L14SC` (replicated from NT) |
| `QLA_Migration/Output/rates/QuikPlTv.csv` | +PQ/ST/PR key rows for `1L14SC` |
| `QLA_Migration/Output/rates/QuikPlCv.csv` | +PQ/ST/PR key rows for `1L14SC` |
| `tools/validators/validate_issue168_l14_reserve_class_replication.py` (new) | Fail-closed validator: for each of PQ/ST/PR, a `QuikTvs`/`QuikCvs` row exists per age/gender/duration and is byte-identical (except UWCLASS) to the NT row |

No change to `app.py` / `QLA_Migration/app.py` engine code is currently anticipated — this is a rate-table Output enrichment, same class of change as #118's and #159's Output-apply tools. If Development finds the replication needs to be permanent (survive a full rebatch, not just a one-time apply), a small addition to the TV/CV rate-emit path (`qla_core/rate_emit.py` or the TV/CV loader) will be scoped then and version-bumped per `AGENTS.md`.

## Explicitly not invented

- No new reserve **values** — every replicated row is byte-identical to a real, LifePRO-sourced `NT` row except the class label.
- No change to which classes exist on `quikridr` (`map_rider_uwclass` output is unchanged; 101 NT / 111 PQ / 7 ST / 13 PR stays exactly as #159 set it).
- No `PLANVALOPT`/`*VARY*` flag changes — #136's rule is fully preserved; the flags keep telling the truth (class-invariant).
- L05 gets **no code change** in this issue — it has no real source row to replicate from.

## Acceptance criteria

1. Every `1L14SC` policy with MUWCLASS ∈ {PQ, ST, ST, PR} finds a `QuikTvs`/`QuikCvs` row at its exact age/gender/duration, with the same value the NT row carries at that same age/gender/duration.
2. `1L14SC` MUWCLASS=NT population (101 rows) — reserve values **unchanged** (regression control).
3. `QuikGps` (premium) row count and values for `1L14SC` — **unchanged** (regression control; premium correctly still varies by class).
4. L05 (`5L0510`, `9L05WP`) — **untouched**, remains $0/blocked pending source data; not reported as "fixed" by this issue.
5. `validate_issue136_pvo_flags.py` — still PASS (this fix must not flip any `*VARY*` flag).
6. `validate_issue159_muwclass_plan_aware.py` — still PASS (MUWCLASS mapping unchanged).
7. New `validate_issue168_l14_reserve_class_replication.py` — PASS.
