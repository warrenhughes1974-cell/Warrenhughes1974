# Issue #50 — Implementation Notes

**Issue:** #50 — Policy Notes Missing  
**Framework stage:** Development (G4)  
**Engine version:** **v57.75**  
**Date:** 2026-07-11  
**Status:** UAT packaging fix → re-validate Memo tab  

---

## Resolution summary

**Root cause (content):** `quikmemo_converter._read_csv` used pandas `on_bad_lines="skip"`, which dropped PNOTE rows when `LINE_*` text contained unquoted commas (fixed-width LifePRO extract).

**Fix (v57.74):** Added `_read_pnote_csv()` — header-derived fixed-width field parser for PNOTE only. PENSE path unchanged.

**Root cause (UAT blank Memo tab):** Python `dbf` library strips leading spaces on CHARACTER write, so DBF stored `018495BC  ` while `quikmstr.MPOLICY` / SEEK uses `  018495BC` → Memo tab empty even when MEMOTEXT was present.

**Fix (v57.75):** After DBF append, rewrite MEMOKEY bytes to preserve Issue #25 left-padding (`_rewrite_dbf_memokey_bytes`).

---

## Files modified

| File | Change |
|------|--------|
| `qla_core/quikmemo_converter.py` | `_pnote_header_field_specs`, `_read_pnote_csv`; PNOTE branch uses fixed-width reader |
| `qla_core/quikmemo_dbf_generator.py` | Post-write MEMOKEY left-pad rewrite (v57.75) |
| `app.py` | `APP_VERSION` → v57.75 |
| `QLA_Migration/app.py` | `APP_VERSION` → v57.75 (sync) |
| `tools/validators/validate_issue50_pnote_parse.py` | Content + DBF padding asserts |

**Not modified:** Rulebooks, crosswalk, PENSE reader, `#21J` append, `#26` mapping, unrelated tables.

---

## Before / after trace

| Policy | Before | After |
|--------|--------|-------|
| **018495BC** CSV | Last Known only; no Bauerly | Bauerly + Last Known |
| **018495BC** DBF key | `018495BC  ` (right-pad) | `  018495BC` (left-pad = mstr) |
| **018495BC** QLAdmin Memo | Blank (SEEK miss) | Should display after reload of DBF+DBT |

---

## UAT reload steps

1. Copy **both** from `QLA_Migration/Output/quikmemo_uat_dbf/`:
   - `quikmemo.dbf`
   - `quikmemo.dbt`
2. Keep them in the **same folder** (do not load DBF without DBT).
3. Rebuild/refresh QLAdmin memo index if required (`QuikMemo.ntx` on MEMOKEY).
4. Open **018495BC** → Memo tab.

---

## Validation

```text
python tools/validators/validate_issue50_pnote_parse.py
RESULT: PASS  (includes DBF left-pad check)
```

## Rollback

Revert `quikmemo_converter.py` PNOTE reader and `quikmemo_dbf_generator.py` rewrite; restore `APP_VERSION` v57.73; re-emit quikmemo.
