# Issue 133 (client "Policy Status's Incorrect") — Fix + Smoke Note

**Date:** 2026-09-22
**Stage:** Development (code fix) + smoke test built. **Not yet Closed** — see G7 gate below.
**Tracked as:** `133-PS` in `Completed_Issues_Release_Validation_Guide.md` (see ID collision note).

---

## ID collision (unresolved — flagging for Warren)

The local tracking sheet already has `133` **Closed** as "Conversion Rule Book
delivery" (2026-07-30). The client's "Policy Status's Incorrect" report reuses
the **same ID 133**. This was flagged at Discovery
(`Issue_133_Discovery_Notes_Policy_Status.md`) and is still open. Nothing here
overwrites `Issue_133_Tracking_Sheet_Row.tsv` (Rule Book delivery stays
Closed as-is). This fix is filed under the working label `133-PS` until
Warren confirms the client sheet's intended ID (reused ID vs new number).

---

## What was wrong

On a LifePRO policy where `PPOLC CONTRACT_CODE/CONTRACT_REASON = S/DP`
(`Master_Value_Translation.csv` `ST_S_DP` → **50**, Death Claim Pending):

- The base benefit (`PPBEN BENEFIT_TYPE=BA`) correctly inherits **50**.
- The paid-up-addition rider (`PPBEN BENEFIT_TYPE=PU`) is still coded
  `STATUS_CODE=A` (Active) in the source.
- Issue #49's "first active later phase" rule then promoted
  `quikmstr.MSTATUS` from **50 back to 22** (Active), because it only read
  the PUA phase's bare `STATUS_CODE` translation (`A`→22), not the base's
  terminal status.
- Issue #160 already fixed the **row-level** symptom (`quikridr.MPHSTAT` on
  the PUA phase inherits the base's terminal status), but #160 only touches
  `quikridr` emission (`app.py _apply_pua_rider_inheritance`). The **header**
  (`quikmstr.MSTATUS`) is derived separately through the Issue #49 override,
  which reads raw PPBEN `STATUS_CODE` via `_ppben_phase_cache` — untouched by
  #160's fix. That gap is what kept the policy header Active.

Client-cited policies: `9010439999C`, `9010468945C`. On the 8/31 extract,
`9010468945C`'s PUA had already moved to `T/DC` (terminal) in LifePRO, so it
was no longer exhibiting the defect — only `9010439999C` is currently live.

## The fix

`qla_core/quikmstr_active_phase_status.py` (`simulate_display_phase_statuses`,
v59.17): a later phase's `BENEFIT_TYPE` is now carried through
`build_ppben_phase_cache`. When the base (phase 1) display status is
terminal (**>=50, excluding 44/45**) and a later phase is `BENEFIT_TYPE=PU`,
that phase's display status is forced to the base's display status —
mirroring Issue #160's quikridr rule inside the Issue #49 header simulation.
Non-PUA riders (SU/OR) are untouched.

`app.py` / `QLA_Migration/app.py` `APP_VERSION` bumped `v59.16` → `v59.17`
(no other app.py changes — the fix lives entirely in the shared `qla_core`
module both copies already import).

## Proof this does not disturb Closed Issue #49

Re-simulating the #49 override directly from current PPBEN/PPOLC:

| | Before fix | After fix |
|---|---|---|
| Total #49 header overrides | 36 | **35** (matches `Issue_49/evidence/issue49_override_candidates.csv` exactly) |
| `9010439999C` (base 50, PUA `A`/`PU`) | overridden to 22 | **not overridden — stays 50** |
| 35 SU/OR-rider overrides (e.g. `018252C`, `01ML8007C`) | overridden to 22 | **unchanged, still overridden to 22** |

`python tools/validators/validate_issue49_mstatus.py --simulate-only` → **PASS**
(count back to the expected 35, evidence set matches exactly).

## Smoke test

`tools/validators/validate_issue133_pua_header_status.py` (fail-closed):

1. Unit-level checks on the module contract directly (no source dependency):
   PUA on a terminal base never overrides; non-PUA rider on a terminal base
   still overrides (guards against widening into #49's territory); base
   44/45 is untouched (stays #108D's job at the quikridr row level).
2. Source-level re-derivation of `9010439999C` (expect 50) and
   `9010468945C` (control, expect 53) from current PPBEN/PPOLC.
3. Runs `validate_issue49_mstatus.py --simulate-only` as a sub-check.
4. WARNs (does not fail) if `Output/quikmstr.csv` doesn't yet reflect the
   fix — that is the G7 rebatch gate below, not a code defect.

Registered in `SMOKE_JOBS` (`tools/validators/validate_release_closed_issues.py`)
and the high-risk smoke table in the Completed Issues guide.

## G7 Closure gate — code-level check now PASSes; formal Closure still pending

**Update 2026-09-22 (same day):** Warren asked to run the full batch. Ran
`tools/batch_tests/run_full_batch_test.py` with `QLA_VALUATION_DATE=20260831`
(git HEAD `67d9caa`, `APP_VERSION=v59.17`).

- `QLA_Migration/Output/quikmstr.csv` now shows `9010439999C` MSTATUS =
  **50** (was 22 on the stale pre-fix Output).
- `python tools/validators/validate_issue133_pua_header_status.py` PASSes
  fully against this fresh Output (the Output-level check went from WARN to
  PASS — no more stale-package warning).
- `validate_release_closed_issues.py --smoke-only` also shows
  `[PASS] #133 PUA terminal base does not reactivate MSTATUS` on this batch.

**Overall release gate is `RELEASE_BLOCKED`, but for two reasons unrelated
to this fix** (do not treat as a regression from this change):

| Failing check | Cause | Related to #133? |
|---|---|---|
| `#160 PUA terminal status inheritance` | `FAIL: missing archive snapshot QLA_Migration/Archive/issue160_pre_remap/quikridr_pre_issue160.csv` — the drift-comparison archive file is absent on disk | No — pre-existing evidence gap, failed the same way before this fix |
| `#161 POA POFA relation + quikcloth` | `FAIL: missing Output/quikcloth.csv` — this batch script did not emit that table | No — unrelated table, not touched by this fix |

Remaining before this can move to **Closed**:

1. Resolve the ID collision with Warren (`133` vs `133-PS`, see above).
2. Run `python tools/validators/validate_issue_log_accountability.py` and
   confirm IN_DATA for this fix (not run yet in this session).
3. Publish `quikmstr.csv` (and `quikridr.csv`) to `Output/Test_Validation/`
   on PASS.
4. Either waive or separately resolve `#160`/`#161` before treating the
   *overall* release gate as clean — those are pre-existing gaps outside
   this issue's scope.

**Current status: code fix + smoke shipped, proven against a fresh 8/31
full-batch Output (not just source-level simulation). Ready for
Validation/Closure decision. Not yet marked Closed pending the ID
resolution above.**
