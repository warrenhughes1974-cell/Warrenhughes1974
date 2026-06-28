# Issue #21J — Files Modified

**Version:** v57.37  
**Date:** 2026-06-28

| File | Type | Description |
|------|------|-------------|
| `qla_core/quikmemo_converter.py` | Modified | Added `ISSUE21J_MODAL_FACTORS`, `format_conversion_modal_factor_memo()`, `_load_mplan_by_mpolicy()`, `_load_converted_memokeys()`, `_merge_conversion_segment()`, `append_issue21j_conversion_memos()` |
| `app.py` | Modified | v57.37; import `append_issue21j_conversion_memos`; quikmemo batch branch invokes #21J append after PNOTE/PENSE merge; logs Issue 21J stats |
| `QLA_Migration/app.py` | Modified | Mirror of root `app.py` changes |
| `QLA_Migration/RUN_GUIDE.md` | Modified | Added operational note for post-conversion modal factor changes; doc version v57.37 |

## Files explicitly NOT modified

- `QLA_Migration/Configs/Sync_Rulebook_*.csv`
- `QLA_Migration/Mapping/Master_Crosswalk.csv`
- `qla_core/quikplan_converter.py`
- Premium / rating / MODE_PREMIUM conversion logic in `app.py`
- `tools/validators/validate_issue21m_quikmemo.py` (Validation Agent to update baselines)
