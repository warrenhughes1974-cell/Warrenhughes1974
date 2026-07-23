# Issue #98 — Implementation Notes

**Issue:** #98 — CV Endpoint Off By One (`010398471C` / `17085M`)  
**Framework stage:** Development Agent (G4)  
**Engine version:** v58.27  
**Implemented:** 2026-07-22

---

## Fix summary

Adjusted CV LifePRO first-duration heuristic for male ages 1–17 so GL85 M/14 placement matches Eric’s LifePRO years (`.06` at duration 3; `975.61` at 85; terminal `1000` at 86), while preserving the Issue #41 age-100 endpoint rule (`return lp_d`).

Also included in the same rate-package release:

- Durable Issue #96 `1SALMI` M/F `QuikPlCv` / `QuikPlTv` companion keys
- Manifest hygiene (skip empty member placeholder rows for special tables)

---

## Files changed

| File | Change |
|------|--------|
| `qla_core/rate_factor_loader.py` | M ages 1–17 → `cv_lifepro_first_duration` = 3 |
| `qla_core/rate_key_setup.py` | `ensure_issue96_sal_gender_companion_keys` |
| `qla_core/rate_pipeline.py` | Call Issue #96 companion-key hook |
| `qla_core/rate_dbf_writer.py` / `rate_emit.py` / `rate_loader_emit.py` | Skip empty member tables in CSV/DBF manifests |
| `app.py` / `QLA_Migration/app.py` | v58.27 |
| `Issue_Log_Items/Issue_98/validate_issue98_quikcvs_endpoint.py` | Anchor validator |
| `tools/validators/validate_issue_log_accountability.py` | `#98` IN_DATA spot-check |

---

## Emit

```text
python plan_analysis/phase_r5_rate_loader/rate_loader_emit.py --csv-only
python tools/publish_test_validation.py --clean --issue Issue_98 --rates QuikCvs QuikPlCv QuikPlTv
```

`QLA_Migration/Output/` is gitignored — network machines must regenerate rate CSVs after pull.
