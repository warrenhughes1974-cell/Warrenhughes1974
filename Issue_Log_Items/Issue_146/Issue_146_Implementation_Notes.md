# Issue #146 — Implementation Notes

**Issue:** #146 — Non-VB Unit Reductions (PC / former-vanish 0561 exclude)  
**Engine:** v59.03  
**Date:** 2026-08-26  

## Change

PACT 0561 events on the locked 20-policy allowlist (19 `BILLING_REASON=PC` plus 9010808831) are no longer emitted to QuikIsrr or the matching #34 companions. Current Output was stripped the same way. LifePRO PACTG is unchanged. #145B VB exclude is unchanged. Keep golds 9010761639 / 9010760840 stay.

Identity is the hard allowlist, not `BILLING_REASON=PC`. `quikspec.VANISH` is not set.

## Files

| File | Change |
|------|--------|
| `qla_core/issue146_pc_isrr.py` | Allowlist + event split |
| `qla_core/quikisrr_loader.py` | Drop allowlist events after #145B VB filter |
| `Issue_Log_Items/Issue_34/tools/quikisrr_pr7_emit.py` | Fail on allowlist leak |
| `Issue_Log_Items/Issue_146/tools/apply_issue146_pc_isrr_exclude.py` | Strip current Output |
| `tools/validators/validate_issue146_pc_isrr.py` | Fail-closed |
| `tools/validators/validate_release_closed_issues.py` | `SMOKE_JOBS` |
| `tools/validators/validate_issue_log_accountability.py` | `#146` job |
| `app.py` / `QLA_Migration/app.py` | v59.03 |

## Output apply

`python Issue_Log_Items/Issue_146/tools/apply_issue146_pc_isrr_exclude.py`

| Table | Before | After | Removed |
|-------|-------:|------:|--------:|
| QuikIsrr | 205 | 101 | 104 |
| quikclms | 2592 | 2488 | 104 |
| quikclmp | 3084 | 2980 | 104 |
| quikbenh type 8 (allowlist) | — | — | 104 |

## Untouched

- `quikridr.MUNIT` / `MPREM`
- `quikmstr`
- `quikspec.VANISH` / `SOR_POL`
- PACTG extract
- `quikbenh` types 10/11/12
- #145B VB golds (0 QuikIsrr)
- #145B keep golds $271 / $716.40
