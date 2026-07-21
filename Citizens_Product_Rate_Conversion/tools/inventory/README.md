# CFIC_Rates Read-Only Inventory Tool

## Purpose

Deterministic, read-only inventory of the legacy `CFIC_Rates` source project for Citizens migration planning.

## Safety Rules

- **Never** writes to `CFIC_Rates`
- **Never** opens source files in write mode
- **Never** executes source scripts
- **Never** extracts ZIP files or opens MDB/DBF for modification
- **Never** recalculates Excel workbooks

## Scripts

| Script | Purpose |
|--------|---------|
| `run_stage2a_inventory.py` | Main Stage 2A runner — preflight, inventory, reports, post-scan |
| `cfic_inventory_core.py` | Classification, hashing, collision detection |

## Usage

```powershell
python Citizens_Product_Rate_Conversion\tools\inventory\run_stage2a_inventory.py
```

## Outputs (in destination project)

- `manifests/preflight_source_snapshot.json`
- `manifests/post_stage2a_source_snapshot.json`
- `manifests/migration_inventory.csv`
- `reports/migration/Stage2A_Dry_Run_Migration_Report.md`
- `reports/migration/duplicate_file_report.csv`
- `reports/migration/path_collision_report.csv`
- `reports/migration/hardcoded_path_report.csv`
- `reports/migration/sensitive_data_review.csv`
- `reports/migration/enterprise_dependency_report.csv`

## Determinism

The same unchanged source tree produces identical SHA-256 hashes and stable classification for files whose metadata is unchanged.

## Stage 2B

Do not copy files until `COPY_APPROVED = YES` is set on reviewed inventory rows.
