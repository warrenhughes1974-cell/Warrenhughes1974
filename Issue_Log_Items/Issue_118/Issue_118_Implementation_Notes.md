# Issue #118 — Implementation Notes

**Issue:** #118 — UW classes by form remap  
**Engine:** **v58.83**  
**Developed:** 2026-08-09  
**Code + Output remap applied** (surgical Output apply; full rate rebatch still recommended for release)

---

## What changed

1. **Form-aware UW map** in `qla_core/rate_dbf_schema.py` (`map_uwclass` / `map_rider_uwclass` with plan/coverage):
   - `B` → `BL`; `S` → `SM` on L10 else `ST`; `P` → `PR`
   - L14: `N→NT`, `T→ST`, `Q→PQ`, `R→PR`
   - blank/`0` → `00`; non-L14 residual `N/Q/T/R/M` → `00` (retire NS)
2. **Labels:** `00`=STANDARD; SM=STANDARD SMOKER; BL/NT/PQ added (NT/PQ truncated to C20)
3. **Loaders** pass plan/coverage into `map_uwclass` (rate_factor, PAAGERAT, PDAGE, shared, inheritance, variation flags)
4. **app.py / QLA_Migration/app.py** MUWCLASS uses plan-aware `map_rider_uwclass`; **APP_VERSION v58.83**
5. **`UWCLASS_DOMAIN`** updated (no NS; +BL/NT/PQ)
6. **Output apply:** `Issue_118/tools/apply_issue118_output_remap.py` remapped quikridr + rate UWCLASS keys, appended 186 L14 T/Q/R premium keys, rebuilt QuikPlUw/QuikUwpo
7. **Validators:** `validate_issue118_uwclass.py`; `validate_issue59_muwclass.py` samples → 901…C + Q→PQ

---

## Files touched

| File | Change |
|------|--------|
| `qla_core/rate_dbf_schema.py` | Form-aware map + labels |
| `qla_core/rate_*.py` / loaders | Pass plan/coverage |
| `qla_core/rate_validation.py` | Domain |
| `app.py`, `QLA_Migration/app.py` | MUWCLASS + v58.83 |
| `tools/validators/validate_issue118_uwclass.py` | New |
| `tools/validators/validate_issue59_muwclass.py` | Sample update |
| `Issue_Log_Items/Issue_118/tools/apply_issue118_output_remap.py` | Output remap |
| `QLA_Migration/Output/quikridr.csv` + `rates/*` | Remapped |

---

## Not invented

L14 cash value / reserve grids for ST/PQ/PR — source has N only. Final report must note missing CV for those classes.

---

## Reporting

Plan × UW inventory: `Issue_Log_Items/Issue_118/evidence/issue118_plan_uw_inventory.csv`  
Discuss format with Warren after Validation (before Closure).
