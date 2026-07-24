# Issue #106 — Implementation Notes

**Issue:** #106 — RV Rates Off by One Duration (QuikTvs) — **Defect #1 only**  
**Version:** v58.31  
**Date:** 2026-07-24  
**Scope:** Duration identity for RV → QuikTvs. **Out of scope:** `1L1095` / L10 LP9595 source mismatch (Defect #2).

---

## Change

Added type-aware duration routing so RV uses LifePRO Dur labels as QuikTvs Dur (identity). Other non-CV families keep `source − 1`. CV remap untouched.

| File | Change |
|------|--------|
| `qla_core/rate_dbf_schema.py` | `rv_source_duration_to_ql`, `duration_to_ql_for_type` |
| `qla_core/rate_factor_loader.py` | Non-CV branch → `duration_to_ql_for_type` |
| `qla_core/rate_inheritance_loader.py` | Same |
| `qla_core/pdage_missfill.py` | Same |
| `qla_core/shared_rate_candidate_loader.py` | Same |
| `app.py` / `QLA_Migration/app.py` | `APP_VERSION` → **v58.31** |
| `tests/engine_packaging/test_eng_pkg_001_contract.py` | Symbols + RV identity asserts |

## Emit

```text
python plan_governance/phase_r5_rate_loader_runner/rate_loader_gui_runner.py --emit-csv
→ RATE_LOADER_STATUS: SUCCESS; QuikTvs rewritten under Output/rates/
```

## Not changed

- CV `cv_remap_ql_duration` / #37/#41/#98
- NP/DV/DB/PR duration (`source − 1`)
- `1L1095` source segment (still L10 LP95)
