# Data Folder Cleanup Log (2026-05-29)

## Reorganized into `plan_analysis/source_data/`

| Category | Files |
|---|---|
| `rates/` | Rate_Table_Extract_20260427.csv, PAAGERAT_AttainedAge_Rates_Extract_20260428.csv |
| `coverage/` | PCOVR.csv, **PCOVRSGT.csv** |
| `crosswalk/` | Policy Form Crosswalk 5.22.26.xlsx |
| `reference_dbf/` | 16 QLAdmin template DBFs |

`docs/plan_conversion_reference/` now contains only a redirect README.

## Removed (stale / duplicate)

| Item | Reason |
|---|---|
| `output/` | Duplicate claims UAT artifacts; canonical copy in `QLA_Migration/Output/` |
| `expectred_outputs/` | Old typo-folder test outputs superseded by QLA_Migration |
| `archive/` | Empty |
| `QLA_Migration/Z_SOURCEFORTESTING/` | Obsolete scratch test sources |
| Root duplicate `Sync_Rulebook_*.csv` (11 files) | Byte-identical to `QLA_Migration/Configs/` |
| `python sanitize_test_data.py --inpu.txt` | Accidental junk file |
| Phase temp scripts/json | `_inspect_new.py`, `_inspect_drop3.py`, `_dbf_inventory.json`, `_inspect_for_r5.py`, `_pilot_data.json` |
| `QuikGps(3).dbf` | Duplicate naming in reference DBFs |

## Preserved intentionally

| Item | Reason |
|---|---|
| Root `Sync_Rulebook_quikclmp.csv`, `Sync_Rulebook_quikclms.csv` | **Differ** from QLA_Migration/Configs versions |
| Root `Master_Crosswalk.csv` | Referenced directly by app.py |
| `QLA_Migration/` operational tree | Production batch conversion path |
| All `phase_*/` deliverables | Active analysis and validation packages |
| `phase_r5_rate_loader/emitted_dbf/` | Generated rate library |

## Code updates

- `qla_core/plan_source_paths.py` — canonical path resolver
- `qla_core/crosswalk_enrichment.py` — uses new crosswalk location
- Rate loader config + R2/R3/R4 scripts — updated paths
