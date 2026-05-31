# Relocated — Plan Conversion Reference

Source data and QLAdmin reference DBFs have moved to:

**`plan_analysis/source_data/`**

| Former location | New location |
|---|---|
| Rate extracts | `plan_analysis/source_data/rates/` |
| PCOVR / PCOVRSGT | `plan_analysis/source_data/coverage/` |
| Policy Form Crosswalk | `plan_analysis/source_data/crosswalk/` |
| QLAdmin template DBFs | `plan_analysis/source_data/reference_dbf/` |

See `plan_analysis/source_data/README.md` for details.

Path resolution in code uses `qla_core/plan_source_paths.py` (with legacy fallback).
