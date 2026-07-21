# Issue #48 — Implementation Notes

**Issue:** #48 — Secondary Rate File (PAAGERAT fallback)  
**Framework stage:** Development (G4)  
**Date:** 2026-07-10  
**Engine:** `app.py` / `QLA_Migration/app.py` **v57.69**  
**Risk authority:** Conditional Go — path wiring + audit only  

---

## What changed

| File | Change |
|------|--------|
| `qla_core/plan_source_paths.py` | Prefer `QLA_Migration/Source/Rate_Table_Extract_Txt.txt`; prefer Source `PAAGERAT_…_20260630.csv` |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | `source_rate_extract` / `paagerat_pr_extract` → Source paths |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.example.json` | Same |
| `QLA_Migration/Configs/variation_classification_config.example.json` | Same Source paths |
| `app.py` | `APP_VERSION` → **v57.69** |
| `QLA_Migration/app.py` | `APP_VERSION` → **v57.69** |
| `QLA_Migration/_validate_issue48_secondary_rate.py` | **New** validation + secondary audit writer |

**Not changed (per Risk):** Rate_Table CV/NP/RV/DB suppress; grain conversion; #42 gaps; policy rulebooks; #25/#26/#31/#37/#40/#41 logic.

---

## Behavior

1. When Source secondary Rate_Table file is present, all resolvers that call `rate_table_extract()` use it.  
2. Content is byte-identical to the prior twin CSV → **0 emit row delta** expected.  
3. Validation writes `Issue_48/evidence/issue48_paagerat_miss_rate_table_secondary_audit.csv` (158 cov+TYPE candidates) — **not** under `Output/`.

---

## Before / after (path)

| Check | Before (v57.68) | After (v57.69) |
|-------|-----------------|---------------|
| `rate_table_extract()` | `plan_analysis/.../Rate_Table_Extract_20260427.csv` | `QLA_Migration/Source/Rate_Table_Extract_Txt.txt` |
| MD5 | twin | same as twin |
| `paagerat_extract()` | `…_20260428.csv` (plan_analysis) | `Source/…_20260630.csv` |
| `7619PU` RV / `A96DAR` NP | Rate_Table retained | Rate_Table retained (no suppress) |
| #42 L01/L10 gaps | Absent | Still absent |

---

## Validation run

```
python QLA_Migration/_validate_issue48_secondary_rate.py
→ ALL CHECKS PASSED (v57.69 path wiring)
```

---

## Rollback

1. Revert `plan_source_paths.py` candidate order.  
2. Revert rate loader config paths to twin CSVs.  
3. Revert `APP_VERSION` to v57.68.  

---

## Next stage

**Validation Agent (G5)** — re-run `_validate_issue48_secondary_rate.py`; confirm no Output pollution; optional dry-run rate path smoke if needed.
