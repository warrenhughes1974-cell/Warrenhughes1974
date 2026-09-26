# Issue #158 — Resolution Summary

**Status:** Closed
**Date resolved:** 2026-08-29
**APP_VERSION:** v59.05
**Valuation date:** 20260731

## What was wrong

LifePRO stores a coverage's rate segments as an ordered list in PCOVRSGT, where `SEQ` is the
rate-type slot — SEQ 1 is the premium slot. The conversion's `SegmentResolver` discarded `SEQ`
entirely and kept a single parent per segment (`dict[segt] = parent`, last write wins).

Two consequences followed:

1. A rider or paid-up-addition that referenced a segment in a **non-premium** slot could capture
   that segment's gross premium grid, while the plan LifePRO actually prices on it showed
   *Values Not on File*.
2. When two coverages legitimately share a segment at SEQ 1, only one of them could ever
   receive the grid.

20 of 91 PR segments were mis-attributed, 18 plans were missing premium grids, and 645 QuikGps
cells were being written by more than one segment. The largest exposure was the L10 family
(~405 active policies) and GL LP85 (249 active).

## What changed

| File | Change |
|---|---|
| `qla_core/rate_segment_resolution.py` | `load_pcovrsgt_slots()` builds `(SEQ, SEGT_ID) → [parent COVERAGE_ID]`, keeping **every** owner; new `slot_parents()` and `resolve_all(segment_id, slot=)`. Existing `resolve()` untouched. |
| `qla_core/paagerat_pr_loader.py` | `PR_OWNERSHIP_SLOT = 1`; PR rows resolve via `resolve_all()` and emit to each owning plan. Kill switch `pr_slot_ownership_enabled()`. |
| `qla_core/quikplan_rate_variation_flags.py` | VARGP for `PR` derives from the same one-to-many SEQ 1 grid the loader emits. Other TYPE_CODEs keep single-parent resolution. |
| `qla_core/shared_rate_candidate_loader.py` | `build_shared_manifest(pr_owner_plans=...)` drops a shared **PR** candidate when its issuing plan now owns a SEQ 1 PAAGERAT segment. |
| `qla_core/rate_pipeline.py` | Passes `pr_owner_plans`; reports `shared_rate_candidates.pr_dropped_plans`. |
| `tools/validators/validate_issue158_pr_segment_ownership.py` | New fail-closed validator. |
| `tools/validators/validate_release_closed_issues.py` | `#158 PR segment SEQ 1 ownership` registered in `SMOKE_JOBS`. |
| `tools/validators/validate_issue_log_accountability.py` | `#158` registered in the validator catalog. |
| `app.py`, `QLA_Migration/app.py` | `APP_VERSION` v59.04 → v59.05. |

Scope held to **PR** as approved. CV, RV and NP slot-awareness is a deliberate follow-up — no
other rate type's resolution was altered, and every non-GP rate table is byte-identical.

## Shared-rate manifest

`approved_shared_rate_candidates.csv` carried L10 PR rows keyed on non-SEQ-1 slots — a
workaround for this very bug. Once PAAGERAT routed correctly the manifest supplied a duplicate
of the same rates with F and BL **transposed**, blocking emit with 344 V03 duplicate-cell
errors on `1L1095` and `1L10OD`. Warren approved dropping shared PR rows for any plan that owns
a SEQ 1 segment, which retires the workaround only where it is no longer needed.

## Proof

- **Validator:** `validate_issue158_pr_segment_ownership.py` — PASS (20 segments, 12 plans
  guarded, 0 colliding cells).
- **Regression:** controlled A/B on one commit — baseline generated with
  `QLA_PR_SEGMENT_SLOT_OWNERSHIP=0`. All non-GP rate tables unchanged; every changed plan on
  the expected list. See `Issue_158_Regression_Report.md`.
- **Release gate:** `validate_release_closed_issues.py --smoke-only` → **RELEASE_OK**, 24/24
  smokes PASS.
- **Accountability:** IN_DATA 73 / GAP 1 — the GAP is #135 (claims), pre-existing and unrelated.
- **DBF package:** `build_full_dbf_append_package.py` — APPEND_OK 43/43, Desktop
  `DBF_Append_Tool\output\` refreshed 2026-08-29.

## Rollback

`QLA_PR_SEGMENT_SLOT_OWNERSHIP=0` restores the prior single-parent PR routing (verified: 2219
GROSS_PREMIUM rows, empty `pr_dropped_plans`). `quikplan.csv` backup at
`evidence/quikplan_pre_issue158_*.csv`; run the R7B refresh again after any rollback.

## Follow-ups

1. Extend slot-aware resolution to CV / RV / NP (the same defect exists there).
2. Claims **#135** accountability GAP — separate, pre-existing.
