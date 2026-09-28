# Issue #174 — Implementation Notes

**Issue:** #174 — Pending Death Benefit Policies
**Framework stage:** Development
**Engine:** v59.26
**Date:** 2026-09-28
**Approval:** Warren, 2026-09-28, including the status-50 exception to #160, #60, and #108

## What changed

Death Claim Pending stays on the policy. It is no longer copied onto the coverage.

1. Both `app.py` copies. Phase 1 does not inherit policy status 50. Statuses 53, 54, 55, and the rest still copy.
2. Both copies. When the policy status is 50, the paid-up addition keeps its own Active status. Issue #60 does not force Paid Up (41). Issue #160 does not copy a terminal base.
3. `qla_core/quikmstr_active_phase_status.py`. `50` is in `PHASE1_INHERIT_BLOCK`, so the header simulation sees an Active first phase and leaves the header at 50.

`MSAVESTAT` follows `MPHSTAT` on the next full emit. On the current 6/30 Output it was set to 22 with `MPHSTAT` on the 17 affected rows. No other column on those rows changed. `quikmstr` was not rewritten.

## Output

17 `quikridr` rows, 16 policies. Before image: `evidence/quikridr_issue174_before_rows.csv`.

| Policy | Phase | Before | After |
|---|---|---|---|
| 9011085655C | 1 `1659CR` | 50 / save 50 | 22 / save 22. Premium 52.656708 unchanged. |
| 9010521213C | 1 `17085M` and 2 `1708PA` | 50 | 22. Header stays 50. |
| The other 14 status-50 policies | phase 1 | 50 | 22. Header stays 50. |

Published `quikridr.csv` to `QLA_Migration/Output/Test_Validation/` for a partial reload.

## Files

- `app.py`
- `QLA_Migration/app.py`
- `qla_core/quikmstr_active_phase_status.py`
- `tools/validators/validate_issue174_pending_death_phase.py`
- `tools/validators/validate_issue160_pua_terminal_status.py` (status-50 PUA may be 22; `MSAVESTAT` on those policies is not a #160 drift)
- `Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md` (#160 and #133-PS wording)
- `QLA_Migration/Output/quikridr.csv`

## Not changed

Premium, units, plan, policy number, `quikmstr.MSTATUS`, translation rows, and every status other than 50.
