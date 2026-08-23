# Issue #145B — Implementation Notes

**Issue:** #145B — Vanish 0561s Out of ISRR  
**Engine:** v59.01  
**Date:** 2026-08-23  

## Change

PACT 0561 events on vanishing policies (`PPOLC.BILLING_REASON = VB`) are no longer emitted to QuikIsrr or the matching #34 companions. Current Output was stripped the same way. LifePRO PACTG is unchanged. Non-VB leftovers (#146) stay.

VB identity reuses Issue 145 `load_ppolc_billing_reason`. Do not use `quikspec.VANISH` as the emit source.

PR-7 emit is **not** re-run against already-loaded Output (clms/clmp append). Leftover book is extract-dependent; the old 3657/637 floor is no longer a hard fail.

## Files

| File | Change |
|------|--------|
| `qla_core/issue145b_vb_isrr.py` | PPOLC VB join + event split |
| `qla_core/quikisrr_loader.py` | Drop VB events after #34 eligibility |
| `Issue_Log_Items/Issue_34/tools/quikisrr_pr7_emit.py` | Fail on VB leak / 0 drops; no stale 3657 floor |
| `Issue_Log_Items/Issue_145B/tools/apply_issue145b_vb_isrr_exclude.py` | Strip current Output |
| `tools/validators/validate_issue145b_vb_isrr_exclude.py` | Fail-closed |
| `app.py` / `QLA_Migration/app.py` | v59.01 |

## Output apply

`python Issue_Log_Items/Issue_145B/tools/apply_issue145b_vb_isrr_exclude.py`

## Untouched

- `quikridr.MUNIT` / `MPREM`
- `quikmstr`
- `quikspec.VANISH`
- PACTG extract
- `quikbenh` types 10/11/12
- #146 QuikIsrr rows
