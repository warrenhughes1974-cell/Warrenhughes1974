# Issue #151 — Implementation Notes

**Issue:** #151 — Val X Modal Prem Outlier (9010969231C former-vanish 0561 leftover)  
**Engine:** v59.18  
**Date:** 2026-09-22  
**Stage:** Closed 2026-09-22 (Warren). Fresh QLAdmin valuation of the old $2,899.79 figure remains the next valuation check.  
**Stage model:** Cursor Grok 4.6 (Warren override 2026-09-22; locked Grok 4.5 unavailable)

## Change

Added source key **9010969231** to the Closed #146 allowlist (`ALLOWLIST_SOURCE` 20 → **21**). Warren approved that expansion **2026-09-22**. Existing `filter_issue146_events` covers the new key; no new loader branch. Current `QLA_Migration/Output` was stripped with the existing #146 apply tool. LifePRO PACTG is unchanged. `quikridr` / `quikmstr` / `quikspec` are unchanged except the dual `APP_VERSION` bump.

Identity is the hard allowlist, not `BILLING_REASON=PC`. `quikspec.VANISH` is not set.

**Fresh QLAdmin valuation remains UAT.** Current `docs/Valuation/QuikValf.dbf` is dated 2026-06-30 (MUNIT 3.4952 / MPREM1 $2,899.79 before-state). This Development pass does **not** claim $2,899.79 is already gone from a fresh run.

## Approvals

| Item | Date |
|------|------|
| Expand Closed #146 allowlist 20 → 21 by adding 9010969231 / 9010969231C | Warren 2026-09-22 |
| Development approved | Warren 2026-09-22 |
| Cursor Grok 4.6 stage-model override (Grok 4.5 unavailable) | Warren 2026-09-22 |

## Files

| File | Change |
|------|--------|
| `qla_core/issue146_pc_isrr.py` | Add `9010969231` to `ALLOWLIST_SOURCE`; comments 20 → 21 |
| `tools/validators/validate_issue146_pc_isrr.py` | Docstring 20 → 21 (loop already uses `ALLOWLIST_SOURCE`) |
| `tools/validators/validate_issue151_pc_isrr.py` | New named fail-closed gold for 9010969231C |
| `tools/validators/validate_release_closed_issues.py` | Required `#151` `SMOKE_JOBS` entry; #146 job unchanged |
| `Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md` | #146 locked 20 → 21; high-risk smoke listing for #151; **no Closed #151 row** |
| `app.py` / `QLA_Migration/app.py` | `APP_VERSION` v59.17 → v59.18 only |
| `Issue_Log_Items/Issue_146/tools/apply_issue146_pc_isrr_exclude.py` | Run against current Output (not edited) |

Not edited: `qla_core/quikisrr_loader.py` (existing `filter_issue146_events` after #145B), PR-7 emit, PACTG, `quikridr`, `quikmstr` data, `quikspec`.

## Output apply

`python Issue_Log_Items/Issue_146/tools/apply_issue146_pc_isrr_exclude.py`

Did **not** re-run PR-7 append.

| Table | Before | After | Removed |
|-------|-------:|------:|--------:|
| QuikIsrr | 110 | 102 | **8** |
| quikclms | 2497 | 2489 | **8** |
| quikclmp | 2994 | 2986 | **8** |
| quikbenh | 42071 | 42063 | **8** (type 8 on this policy) |

Those eight rows were **only** 9010969231C. Existing #146 allowlist population remained absent before and after (0 leftover ISRR). Keep golds still present: 9010761639C $271.00 (1 row); 9010760840C $716.40 (2 rows).

## Preserved on 9010969231C

| Field | Value |
|-------|-------|
| quikridr phase 1 MUNIT | 5.00000 |
| quikridr phase 1 MPREM | 37.62 |
| quikridr phase 1 MCV0 | -812.49000 |
| quikmstr MMODEPREM | 163.10 (#139) |
| quikspec.VANISH | F (untouched) |

## Status

Warren marked the sheet Closed on 2026-09-22. Validation PASS is recorded in `Issue_151_Validation_Report.md`. The named smoke is registered. The next QLAdmin valuation should confirm the policy stays premium-paying at 5 units and $2,899.79 is gone.
