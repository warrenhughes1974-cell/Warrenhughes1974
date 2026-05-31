# Plan Analysis

Enterprise plan and rate conversion analysis, validation packages, and source data.

## Folder guide

| Area | Location |
|---|---|
| **Source data (LifePRO + reference DBFs)** | `source_data/` |
| **Product catalog source** | `quikplan_source.csv`, `PCOMP.csv` |
| **Rate emitted library** | `phase_r5_rate_loader/emitted_dbf/` |
| **Sandbox import package** | `phase_r6b_sandbox_import_execution/` |
| **Phase deliverables** | `phase_p*/`, `phase_r*/`, `status_analysis/` |

## Source data layout

See [`source_data/README.md`](source_data/README.md).

Key files now under `plan_analysis` (not `docs/`):

- `source_data/rates/` — Rate_Table_Extract, PAAGERAT
- `source_data/coverage/` — **PCOVR**, **PCOVRSGT**
- `source_data/crosswalk/` — Policy Form Crosswalk
- `source_data/reference_dbf/` — QLAdmin template DBFs

Code resolves paths via `qla_core/plan_source_paths.py`.

## Cleanup note (2026-05-29)

- Relocated plan/rate reference files from `docs/plan_conversion_reference/` → `source_data/`
- Removed stale duplicate output folders (`output/`, `expectred_outputs/`)
- Operational batch outputs remain in `QLA_Migration/Output/`
