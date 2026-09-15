# Issue #168 — Risk Review Report

**Issue:** #168 — L14 Reserve/Cash Value Class-Key Replication (L05 split out — data-blocked, not in this scope)
**Framework stage:** Risk Agent (G3)
**Status:** **GO — Ready for Development, pending explicit Development approval**
**Fallback simulated:** N/A — additive rate-row replication, no existing row is altered or removed
**Generated:** 2026-09-14

---

## Go / No-Go Recommendation

**GO** — replicate the existing, real `QuikTvs`/`QuikCvs` rows for `1L14SC` currently keyed `UWCLASS=NT` onto `UWCLASS=PQ/ST/PR`, unchanged in every field except the class label. This restores reserve matching for 131 of 232 L14 rider rows without inventing a single new number, without touching `quikridr.MUWCLASS` (#159, correct), and without touching any `*VARY*` flag (#136, correct — those flags stay true: this plan's reserve genuinely does not vary by class).

**Conditions (surgical, not blockers):**

1. Replicate **only** `1L14SC`. No other plan is in scope (L05 is explicitly excluded — no real data to replicate).
2. Source the replicated rows from the **current real NT rows only** — do not hand-author values.
3. Do not change `map_rider_uwclass`, `map_uwclass`, `quikridr.MUWCLASS`, or any `*VARY*`/`PLANVALOPT` flag.
4. Do not touch `QuikGps` (premium) — it correctly varies by class already.
5. New validator + smoke registered before Closure, per `.cursor/rules/closed-issue-smoke-test.mdc`.

---

## 1. Current vs Proposed

| Field | Current | Proposed | Change? |
|---|---|---|---|
| `QuikTvs` rows for `1L14SC`, `UWCLASS=NT` | 2,874 real rows | unchanged | **No** |
| `QuikTvs` rows for `1L14SC`, `UWCLASS ∈ {PQ,ST,PR}` | 0 (no match → $0 reserve) | ~2,874 each, byte-identical to NT except UWCLASS | **Yes (additive)** |
| `QuikCvs` rows, same pattern | 0 for PQ/ST/PR | ~2,836 each, byte-identical to NT except UWCLASS | **Yes (additive)** |
| `QuikPlTv`/`QuikPlCv` key rows, `1L14SC` × PQ/ST/PR | Not present (or `Values=N` stub) | Present, `Values=Y` | **Yes (additive)** |
| `quikridr.MUWCLASS` (all plans) | #159 mapping | unchanged | **No** |
| `UWVARYTV`/`UWVARYCV`, `1L14SC` | `N` | `N` | **No** |
| `QuikGps` (premium), `1L14SC` | 4 real classes | unchanged | **No** |
| L05 (`5L0510`, `9L05WP`) | $0 / no real data | $0 / no real data | **No — out of scope** |

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|---|---|
| `quikridr.MPREM` | No |
| `quikridr.MUWCLASS` | No |
| `QuikGps` values | No |
| `MPOLICY` | No |
| `MBAND` | No |
| `PLANVALOPT` / any `*VARY*` | No |
| L05 / any non-L14 plan | No |

## 3. Population Analysis

| Metric | Count |
|---|---:|
| `1L14SC` total rider rows (9/10 snapshot) | 232 |
| Currently matching (NT) | 101 |
| **Currently $0 / non-matching, fixed by this issue** | **131** (PQ 111 + ST 7 + PR 13) |
| L05 rows affected by this issue | **0** (out of scope; separate data request) |
| New `QuikTvs` rows added | ≈ 8,622 (2,874 × 3 classes) |
| New `QuikCvs` rows added | ≈ 8,508 (2,836 × 3 classes) |
| Existing rows altered or removed | **0** |

## 4. Trace Policies (to confirm at Validation)

| Policy (illustrative — confirm real IDs from `1L14SC` PQ/ST/PR rows at Development) | Class | Expected result after fix |
|---|---|---|
| A PQ-class `1L14SC` policy | PQ | Reserve now matches LifePRO at that age/duration (same number an NT policy of the same age/duration/gender would show) |
| An ST-class `1L14SC` policy | ST | Same |
| A PR-class `1L14SC` policy | PR | Same |
| An NT-class `1L14SC` policy | NT | **Unchanged** — regression control |
| Any L05 policy | ST/PR | **Unchanged, still $0** — confirms L05 correctly stayed out of scope |

## 5. Fallback Recommendation (if Development finds a complication)

| Option | Assessment |
|---|---|
| **A. Output-apply replication script (recommended)** | Matches #118/#159 precedent; low blast radius; fully reversible (delete added rows) |
| B. Change TV/CV rate-emit loader to always replicate at emit time | Defer — only needed if replication must survive a full rebatch without re-running the apply script; adds engine-code risk not needed for first pass |
| C. Ask CSO for confirmation before loading | Not required — this is a mechanical key-completeness fix on data CSO's own LifePRO already computes as class-invariant; no new business judgment is being made on their behalf |

**Recommended fallback:** none needed for Option A. Kill switch: delete the added PQ/ST/PR rows from `QuikTvs`/`QuikCvs`/`QuikPlTv`/`QuikPlCv`; `quikridr` and all other tables are untouched so no other rollback is needed.

## 6. Prior Fix Preservation

| Check | Result |
|---|---|
| #159 `quikridr.MUWCLASS` mapping | Untouched |
| #136 real-variation `*VARY*` rule | Preserved — flags stay `N` and stay true |
| #118 form-aware premium map + keys | Untouched |
| #107 `1L1095` LP9595 | Untouched (different plan) |
| Older-cut newest-plan/rates freeze | N/A this run; replicated rows become part of "newest" package going forward |

## 7. Regression Testing Checklist (for Validation Agent)

- [ ] `1L14SC` NT rows: values unchanged (spot-check 5 ages/durations)
- [ ] `1L14SC` PQ/ST/PR rows: now present, value-identical to NT at same age/gender/duration
- [ ] `1L14SC` `QuikGps` (premium): row count and values unchanged
- [ ] L05 (`5L0510`, `9L05WP`): still $0, unchanged, not touched
- [ ] `quikridr.MUWCLASS` fleet-wide: unchanged (row count + values, full diff = 0)
- [ ] `validate_issue136_pvo_flags.py`: PASS (no flag flipped)
- [ ] `validate_issue159_muwclass_plan_aware.py`: PASS
- [ ] New `validate_issue168_l14_reserve_class_replication.py`: PASS
- [ ] Publish `Output/Test_Validation/{QuikTvs,QuikCvs,QuikPlTv,QuikPlCv}.csv`

## 8. Recommended Development Agent Task

1. New `Issue_Log_Items/Issue_168/tools/apply_issue168_l14_reserve_class_replication.py`:
   - Read current `Output/rates/QuikTvs.csv` and `QuikCvs.csv`.
   - For `PLAN=1L14SC`, `UWCLASS=NT` rows, emit 3 copies each with `UWCLASS` set to `PQ`, `ST`, `PR`, all other fields identical.
   - Same pattern for `QuikPlTv.csv` / `QuikPlCv.csv` key rows.
   - Write an evidence CSV (before/after row counts, sample trace).
2. Do **not** touch `app.py`, `QLA_Migration/app.py`, `map_rider_uwclass`, `map_uwclass`, or `quikplan_rate_variation_flags.py`.
3. Add `tools/validators/validate_issue168_l14_reserve_class_replication.py` (fail-closed).
4. Publish `Output/Test_Validation/` copies on PASS.
5. No `APP_VERSION` bump required unless a follow-on loader change is later scoped (Output-apply only, per Planning).

---

**This report recommends GO. Awaiting explicit "Approved for Development" before any code or Output-apply script is written, per the locked Issue Framework.**
