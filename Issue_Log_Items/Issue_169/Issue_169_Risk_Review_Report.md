# Issue #169 — Risk Review Report (v2)

**Framework stage:** Risk (G4)
**Date:** 2026-09-15
**Scope assessed:** RC-1 only — `5667AT` (667 ART) `QuikNps` emit from the PAAGERAT attained-age extract.
**Supersedes:** the v1 Risk Review (class-replication scope), which assessed a change since shown to be a no-op.

---

## Recommendation

**GO for Development on RC-1, conditional on Warren clearing Dependency Gate D-1** (Closed-row notification on the PSUBSSEG scope manifest).

Risk is low and the change is additive to a plan that currently emits nothing into the target table. The material risk is not the data — it is that this edits a loader module shared with two Closed premium fixes.

---

## 1. Population and dollar impact

| Measure | Value |
|---|---|
| Plans touched | **1** (`5667AT`) |
| `quikridr` policies on the plan | 195 (95 active per PSUBSSEG Discovery, 2026-08-29) |
| Valued rows at 6/30/2026 | **96** |
| LifePRO reserve currently unmatched | **$132,229.48** |
| QLAdmin reserve today | **$0.00** on all 96 rows |
| Rows whose value changes from non-zero to something else | **0** — every affected row is currently zero |

The last line is what makes this safe: there is no existing non-zero `5667AT` reserve to disturb. The change can only move rows off zero.

## 2. Regression risk

| Risk | Severity | Mitigation |
|---|---|---|
| Editing `paagerat_pr_loader.py` breaks the `PR` leg (Closed #158/#157, 20 re-attributed segments) | **Medium — highest risk in this change** | Add a wrapper only; do not modify `stream_paagerat_rows` behaviour. Hard gate: `QuikGps` byte-identical before/after **and** `validate_issue158_pr_segment_ownership.py` PASS (`1L1095` GP0 = 5.23, `1L10OD` = 4.75) |
| Editing the same module breaks the `NF` leg | Low | `QuikNff` byte-identical before/after |
| Attained-age rows collide with PDAGE-sourced `QuikNps` on another plan | Low | Allowlist is `5667AT` only. `1668SP` (level-NP, 2,128 rows) and `A96DAR` (NP in both extracts) explicitly excluded — see Planning §2.3 |
| CEN/ISWL level-NP flatten disturbed (Closed CEN NP) | Low | `5667AT` is not in `QUIKNPS_LEVEL_NP_MPLANS`. Gate: `1658C1` M/37 PR `QuikNps` all `4.00` |
| PSUBSSEG generations disturbed (Closed PSUB) | Low–Medium | `validate_psubsseg_substitution.py` PASS; `5667AT` `QuikTvs` unchanged (all-zero RV grid preserved per OI-2) |
| New grid emitted without a `QuikPlTv` key row (#77) | Low | Key-row completeness assertion in the new validator |
| **Wrong EFFDATE generation** — NP grid keyed `19950101` while 1985-issue policies need `19000101` | **Medium** | D-7. Fix produces no reserve if wrong, rather than a wrong reserve. Prove against anchor policies before Validation closes |
| Reserve resolves but to the wrong amount | Low–Medium | Acceptance criterion 10: `MRESERVE` must reconcile to LifePRO `RV_MEAN_RV` on `9010764158C` / `9010764248C` / `9010768802C`. A partial match is a FAIL, not a pass |

## 3. Blast radius

- **Tables:** `QuikNps` (additive, one plan), `QuikPlTv` (additive key rows if not already covered).
- **Code:** one new wrapper function, one config block, pipeline wiring. No schema change, no field-order change, no `app.py` engine logic change beyond the `APP_VERSION` bump.
- **Policies:** 96 valued rows on one plan. No policy-level table (`quikmstr`, `quikridr`, `quikclnt`) is touched.
- **Not touched:** `QuikGps`, `QuikNff`, `QuikCvs`, `QuikTvs`, `QuikDbs`, `QuikDvs`, all `*VARY*` flags, `MUWCLASS`, `CSO_Valuation_Setup.csv`.

## 4. Rollback safety

**High.** The change is config-gated (`paagerat_np.enabled`), matching the `paagerat_bp` / `paagerat_coi` / `pua_cv` precedent. Setting the flag false and re-running the rate emit restores the current output exactly, because the plan has no pre-existing rows in the target table to restore. No destructive step, no DBF rebuild (Append-only rule preserved).

## 5. Risk of the change being wrong in the *other* direction

Worth stating explicitly, since v1 got the direction wrong on three plans. If the attained-age NP grid were emitted onto a plan whose LifePRO reserve is genuinely zero, we would create a reserve that should not exist. That is not the case here: LifePRO reports a non-zero `RV_MEAN_RV` on **95 of the 96** `5667AT` rows, totalling $132,229.48. We are moving toward LifePRO, not away from it.

## 6. Risk of inaction

| Item | If we do nothing |
|---|---|
| RC-1 `5667AT` | $132,229.48 stays unreserved on a Go/No-Go valuation issue. Known and documented internally since 2026-08-29 ("reserves are not zero, they were never emitted") — hard to defend if it surfaces again |
| RC-2 `7619PU` / `901ADB` / `996ADB` | ~$293 stays wrong. Small in dollars, but it is the *mechanism* behind the ADB gaps, so leaving it unasked keeps a real cause open |
| RC-3 `196085` | $1,858.42 on one policy stays out |
| RC-4 three rider plans | QLAdmin keeps reporting ~$102 where LifePRO reports $0. Opposite-direction discrepancy; benign but should be confirmed with Jill rather than left ambiguous |

## 7. Conditions on the GO

1. **Warren clears D-1** — Closed-row notification on the PSUBSSEG manifest, and picks option (a) manifest extension or (b) separate `paagerat_np` gate (Planning defaults to (b)).
2. Development resolves **D-7** (EFFDATE generation) from evidence, not assumption, before emitting.
3. No `MORT` / `RSVINT` / `RSVMETH` value is invented for any plan (#80).
4. Full rate re-emit with before/after byte comparison on every table and every plan other than `5667AT`.
5. `validate_release_closed_issues.py --smoke-only` PASS before any handoff.
6. Dollar figures are not quoted to the client until a fresh `QuikValf` is produced against the current package — the 9/2 run predates the 9/13–9/14 rate regeneration.

## 8. Items carried forward, not for Development

- **RC-2 client ask** (`7619PU`, `901ADB`, `996ADB` valuation assumptions) — send to CSO via Jill. This replaces the v1 reserve-factor request, which must **not** be sent.
- **RC-4 confirmation** — ask Jill whether a reserve is expected on 1595 WP, SAL ADB, and 1596-667 ADB, given LifePRO's own ValX shows $0.
- **`967ADB` crosswalk governance** (`CROSSWALK_DIVERGENT` on LifePRO coverage `1596 667`) — real, separately tracked, not a reserve defect.
- **PSUBSSEG process finding** — a Planning-stage emit entry (E4) reached the Dependency Gate as "Met" and then disappeared from the delivered manifest without a recorded decision. Worth a look at how scope entries are reconciled against delivery, independent of this issue.
