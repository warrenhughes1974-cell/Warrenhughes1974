# Issue #158 — Validation Report

**Stage:** 6 (Validation)
**Date:** 2026-08-29
**APP_VERSION:** v59.05
**Valuation date:** 20260731
**Result:** PASS

## 1. What was validated

PR (policy gross premium) rate grids must attach to the QLAdmin plan whose LifePRO coverage
carries the segment at **PCOVRSGT SEQ 1**, the premium slot. Before this fix `SegmentResolver`
ignored SEQ and kept only one parent per segment (`dict[segt] = parent`, last write wins), so a
premium grid could land on a rider or PUA that merely referenced the segment elsewhere in its
list, and could never reach two plans that legitimately share it.

## 2. Validator

`python tools/validators/validate_issue158_pr_segment_ownership.py`

```
Issue #158 PR segment ownership — PASS
  segments checked : 20
  plans guarded    : 12
  colliding cells  : 0
```

The validator is **fail-closed** (exit 1) and asserts three things against full
`QLA_Migration/Output/`:

1. Every PR segment's grid is present on its SEQ 1 owning plan(s).
2. No PR grid appears on a plan that does not own the segment at SEQ 1.
3. No two different LifePRO segments write the same QuikGps cell.

## 3. Outcome against the planned impact

| Planned | Observed |
|---|---|
| 20 segments change attribution | 20 segments checked, all landing on SEQ 1 owners |
| 18 plans gain a PR grid | QuikGps +257 rows across the gaining plans |
| 8 plans lose a foreign grid | −199 rows; each loss accounted for by BP or a correct VARGP=4 |
| 0 segments become unresolved | 0 unresolved |
| 0 cross-segment cell collisions | 0 |

## 4. L10 shared-rate conflict

Enabling slot-aware routing initially blocked emit with 344 **V03 duplicate source cell**
errors on `1L1095` and `1L10OD` (UWCLASS `BL`). Cause: `approved_shared_rate_candidates.csv`
carried L10 PR rows keyed on non-SEQ-1 slots — a manifest workaround for the very
segment-resolution bug this issue fixes. With PAAGERAT now routing correctly, the manifest was
supplying a transposed duplicate of the same rates (pre-fix F and BL values were exactly
swapped relative to PAAGERAT).

Resolution (approved by Warren): `shared_rate_candidate_loader.build_shared_manifest()` now
drops a shared **PR** candidate when its `issuing_plan` already owns a SEQ 1 PAAGERAT segment.
The workaround is retired only where it is no longer needed; all other shared candidates and
all non-PR rate types are untouched. Dropped plans are reported as
`shared_rate_candidates.pr_dropped_plans` in the run summary.

Emit gate after the fix: `blocker_count: 0`, `passed: true`.

## 5. Cross-issue checks

- **#138** (SEQ = attained age + 1 for PR) — smoke PASS, offset preserved.
- **#140** (attained-age slot axis) — smoke PASS after the VARGP refresh.
- **#71** (BAND=00) — PASS, 12418 band cells all `00`.
- **A7** (VARGP/VARDB vs emitted grids) — PASS after the VARGP refresh.
- **#142** (SL rider 9SUBLF) — PASS; `9SUBLF` was falsely implicated by a stale baseline and is
  not affected by this fix (see Regression Report section 1).

## 6. Published for partial UAT reload

`QLA_Migration/Output/Test_Validation/`

- `quikplan.csv`
- `rates/QuikGps.csv`, `QuikPlGp.csv`, `QuikPlCv.csv`, `QuikPlDb.csv`, `QuikPlDv.csv`,
  `QuikPlGd.csv`, `QuikPlTv.csv`, `QuikPlUw.csv`

Release handoff must still be **full Output**, not Test_Validation alone.
