# Issue #166 — Implementation Notes

**Issue:** #166 — Div Accumulation Crediting
**Framework stage:** Development Agent (G4)
**Engine:** **v59.13**
**Date:** 2026-09-13
**#21D override:** Warren Approved for Development 2026-09-13 (non-ISWL 4.00 → #95 buckets)

---

## What changed

`quikdvdp.MDEPINT` now uses the #95 plan buckets instead of ISWL-only 4.50 / everyone else 4.00. On deposit rows whose Interest Paid To is a calendar year-end (`*1231`), `MINTDATE` overlays to the prior policy anniversary vs `QLA_VALUATION_DATE`.

QuikUint, `ISWL_MPLAN_ALLOWLIST`, history, and premium/key formatting were not edited.

---

## Files

| File | Change |
|---|---|
| `qla_core/mdepint_buckets.py` | New bucket + anniversary helpers |
| `qla_core/tests/test_mdepint_issue166.py` | Unit tests (4/4 PASS) |
| `app.py` / `QLA_Migration/app.py` | v59.13 emit hook |
| `QLA_Migration/Configs/Sync_Rulebook_quikdvdp.csv` | Fallback comment |
| `tools/validators/validate_issue166_mdepint.py` | New fail-closed validator |
| `QLA_Migration/_validate_issue166_mdepint.py` | Wrapper |
| `tools/validators/validate_issue21d_mdepint.py` | ISWL 4.50 kept; non-ISWL now #95 buckets |
| `tools/validators/validate_issue38_mdeposit.py` | Comment only (no 4.00 lock) |
| `Issue_Log_Items/Issue_166/scripts/rebatch_quikdvdp.py` | Headless rebatch |

---

## Before / after traces (8/31 valuation)

| Policy | Before | After |
|---|---|---|
| **9010728947C** gold | 4.00 / 20251231 / 1875.38 | **3.50 / 20250904 / 1875.38** |
| 9010380808C #116 | 4.00 / 20251231 / 9220.33 | **3.50 / 20251201 / 9220.33** |
| 9010713704C ISWL | 4.50 / 20260719 / 0.00 | **4.50** / date unchanged |
| 9010824098C 1668SP | 4.00 / 19880422 / 0.00 | **4.50** / date unchanged |
| 901122D991C SAL | 4.00 / 20261103 / 0.00 | **2.00** / date unchanged |

---

## Rebatch impact (`QLA_VALUATION_DATE=20260831`)

| Metric | Count |
|---|---:|
| `quikdvdp` rows | 5,083 (unchanged) |
| `MDEPINT` changed | 2,815 |
| `MINTDATE` overlay | **21** (20× 20251231 + 9010497768C 20231231) |
| Gold deposit | Unchanged 1875.38 |
| Unique `MDEPINT` | 2.00 / 3.50 / 4.50 only |

Six other deposits moved with the current 8/31 PPBENTYP/641 re-emit (not gold). Those are source-refresh amounts, not rate-formula edits.

---

## Rollback

1. Revert the v59.13 `app.py` hooks and `mdepint_buckets.py`.
2. Restore `quikdvdp.csv` from `evidence/quikdvdp_pre_issue166.csv`.
3. Restore `validate_issue21d_mdepint.py` v1.0 if a 4.00 lock is required again.
