# Issue #168 — Dependency Gate

**Issue:** #168 — L14 Reserve/Cash Value Class-Key Replication
**Framework stage:** Dependency Gate
**Date:** 2026-09-14
**Result:** **GO — not blocked**

---

## Dependency checks

| Dependency | Status | Detail |
|---|---|---|
| **#159** (L10/L14 MUWCLASS plan-aware fix) | **Compatible, required precondition** | #168 depends on #159's `quikridr.MUWCLASS` split (NT/PQ/ST/PR) already being correct. It is (Closed v59.08, confirmed against 9/10 snapshot: 101/111/7/13). #168 does not modify this. |
| **#136** (PVO real-variation rule) | **Compatible — reviewed for conflict, none found** | #168 does not toggle any `*VARY*` flag. `UWVARYTV`/`UWVARYCV` for `1L14SC` stay `N`, which remains factually true (LifePRO's reserve for this plan does not vary by class) both before and after #168. #136's rule governs *flags*, not *rate-table row replication*; adding rows under new UWCLASS keys with unchanged flags does not violate "variation follows real rate differentiation" — the underlying value truly is invariant across the classes it's being posted to. |
| **#118** (form-aware UW map + rate-key build) | **Compatible** | #118 already added `PQ/ST/PR` **premium** (`QuikGps`/`QuikPlUw`) keys for L14 (186 keys). #168 extends the same "add key + factor rows" pattern to the **reserve/cash-value** side only, using the tooling precedent `Issue_118/tools/apply_issue118_output_remap.py` already set. |
| **#107** (`1L1095` RV source vs L10 LP9595) | **Unrelated** | Different plan family (L10, not L14); #168 does not touch `1L1095`. |
| **Older-cut plan/rate freeze rule** (`.cursor/rules/older-cut-keep-newest-plan-rates.mdc`) | **N/A for current batch** | Applies only when converting a valuation older than the current plan/rate package. #168 is a rate-table correction for the current package, not an older-cut conversion. If #168 lands and a subsequent older-cut run needs to "keep newest plan/rates," the replicated PQ/ST/PR rows are part of that newest package and get preserved like any other rate row. |
| **L05 data request (drafted, not yet sent)** | **Independent — not blocking** | L05 has no code fix available; #168's Development scope explicitly excludes L05. Sending the CSO/New Era data request can proceed in parallel, on its own timeline, without waiting on #168's Development/Validation. |
| **Closed-issue smoke suite** (`validate_release_closed_issues.py`) | **No conflict** | #168 does not touch any table owned by an existing Closed-issue smoke (`#159` smoke checks `MUWCLASS` values only, unchanged; `#136` smoke checks flag values only, unchanged). A new #168 smoke will be additive, per `.cursor/rules/closed-issue-smoke-test.mdc`, registered at Closure. |

## Blast radius

- **Tables touched:** `QuikTvs`, `QuikCvs`, `QuikPlTv`, `QuikPlCv` (rates/, Output-apply only) — for `PLAN=1L14SC` and `UWCLASS ∈ {PQ, ST, PR}` only.
- **Rows added:** ~3× the current NT row count in `QuikTvs` (2,874) and `QuikCvs` (2,836) ≈ 8,600 + 8,500 new rows, all replicated (no new values).
- **Policies affected:** 131 of 232 `1L14SC` rider rows (PQ 111 + ST 7 + PR 13). Zero L10, L05, or any other plan.
- **No engine (`app.py`) change anticipated** — see Planning Report for the conditional follow-up if permanence-through-rebatch requires a loader change.

## Conflict-with-Closed-row disclosure (per `.cursor/rules/completed-issues-release-guide.mdc`)

This issue revisits ground #159's own Risk Review (9/2) already covered and, at the time, rejected two similar-sounding options (cloning the grid; touching `UWVARYTV`). Per that rule, this was disclosed to Warren in chat before proceeding to Intake, along with the new evidence (LifePRO's source itself tags 100% of L14's reserve rows with a single class) that was not available to the #159 reviewer. **Warren gave verbal proceed 2026-09-14** ("Yes please" to moving #168 into Intake/Planning/Risk on this basis). Formal Development approval is still requested at the end of Risk, per the standard chain — this Dependency Gate does not itself authorize coding.

## Gate result

**GO.** No blocking dependency. Proceed to Risk.
