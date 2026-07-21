# Proposed Configuration Model

**Status:** Design only — Stage 3  
**Do not populate production configs in this stage.**

## Directory Layout

```text
config/
|-- citizens.yaml
|-- engine_version.yaml
|-- source_locations.yaml
|-- output_locations.yaml
|-- runtime.yaml
|-- logging.yaml
|-- environments/
|   |-- local.yaml
|   |-- validation.yaml
|   `-- production.yaml
|-- controlled_status_values.yaml   # exists
|-- engine_boundary/                # exists (docs)
`-- schemas/
    |-- citizens_config.schema.json
    `-- controlled_values.schema.json
```

## Key Domains

### `citizens.yaml`
- `client_id`: CITIZENS / CFIC
- `project_root`: resolved path or `.`
- `project_version`
- `source_manifest_version`
- `mapping_manifest_version`
- `fail_on_rejected_row`: true
- `fail_on_duplicate_key`: true
- `fail_on_missing_rate`: true|false (policy)
- `rate_type_enablement`: map of rate-type → enabled
- `plan_selection`: ALL | list | manifest filter

### `engine_version.yaml`
- `engine_package`: e.g. `enterprise-conversion-engine`
- `engine_version`: pinned SemVer
- `engine_commit`: optional SHA
- `install_method`: package | editable | path | cli
- `allowed_modules`: list of `qla_core.*` (or future names)
- **Never** store a mutable `sys.path` hack as the long-term model

### `source_locations.yaml`
- `original_dbf`, `cash_values`, `access`, `product_documents`, `extracts`
- `authority_status` pointers into SOURCE_AUTHORITY.md
- `legacy_cfic_rates_readonly`: optional audit path (read-only)

### `output_locations.yaml`
- `staging`, `reports`, `validation`, `output_csv`, `output_dbf`, `release_packages`
- `draft_output` (isolated)
- `archive`, `quarantine`

### `runtime.yaml`
- `dry_run`: bool
- `validation_only`: bool
- `write_output`: bool
- `run_id` strategy
- `output_version`
- `selected_plans` / `selected_rate_types`

### `logging.yaml`
- level, format, sink paths under `reports/**/runs/`

### Environments
Override paths and flags for `local`, `validation`, `production`. Production must force `write_output` gates and forbid draft-folder publish.

## Mapping to Stage 4 Issues

| Concern | Issue |
|---------|-------|
| Project root + path config | CIT-ARCH-001 |
| Engine pin | CIT-ENGINE-001 |
| Schemas | CIT-ARCH-002 |
| Runtime flags / dry-run | CIT-ARCH-003 |

## Prohibitions

- Do not put secrets in YAML committed to Git
- Do not point `write_output` at `source/original/`
- Do not enable `mappings/approved` writes from runtime config
- Do not reference CSO paths or configs
