# Issue #134 — Implementation Notes

**Issue:** #134 — Death Benefit Notes  
**Engine:** v58.47  
**Date:** 2026-08-01  
**Code changes:** Surgical only  

---

## What changed

1. **`qla_core/quikmemo_converter.py`** — skip PNOTE `FILE_TYPE=B` (stat `skipped_file_type_b`); add `format_pnote_b_claim_memotext()`.
2. **`qla_core/issue134_claim_memo_overlay.py`** — new helper: join B notes → death `quikclms` rows; replace `MEMOTEXT`; orphan audit.
3. **`app.py` + `QLA_Migration/app.py`** — post-emit hook **after** #79/#85/#84 so lineage-based remaps still see `DEATH_CLAIM` before replace; version **v58.47**.
4. **Apply / validate scripts** — `QLA_Migration/_apply_issue134_output.py`, `_validate_issue134_claim_memos.py`.

## What did not change

- `quikclmp`, money fields, CLAIMSTAT, dates  
- `QuikHcmm` (not used — health only)  
- Non-B PNOTE + PENSE → Policy Memo  
- Fleet `[CONVERSION]` memos on `quikmemo` (re-emit includes 21J append to preserve row grain ~5083)

## Output apply results

| Metric | Value |
|--------|------:|
| Death rows updated with `[PNOTE-B]` | 1,209 |
| Orphan B policies (no death row) | 292 |
| `skipped_file_type_b` | 4,149 |
| `quikmemo` rows after re-emit + 21J | 5,083 |
| `quikclms` / `quikclmp` rows | 5,594 / 6,422 |

## Trace (after)

| Policy | `quikclms.MEMOTEXT` | B on `quikmemo` |
|--------|---------------------|-----------------|
| `9010150740C` | `[PNOTE-B]` + PB notes | No |
| `9010335038C` | `[PNOTE-B]` + PB = PATSY MILLER… | No |

## Files touched

- `qla_core/quikmemo_converter.py`
- `qla_core/issue134_claim_memo_overlay.py` (new)
- `app.py`, `QLA_Migration/app.py`
- `QLA_Migration/_apply_issue134_output.py` (new)
- `QLA_Migration/_validate_issue134_claim_memos.py` (new)
- `QLA_Migration/Output/quikclms.csv`, `quikmemo.csv`
- `QLA_Migration/Output/Test_Validation/quikclms.csv`, `quikmemo.csv`
- `QLA_Migration/Reports/issue134_pnote_b_orphan_audit.csv`
