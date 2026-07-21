# Run Reproducibility Standard

**Status:** Design only — Stage 3

Every future conversion or validation run must emit `run_manifest.json` (typically under `reports/**/runs/<RUN_ID>/`).

## Required Fields

| Field | Purpose |
|-------|---------|
| RUN_ID | Unique run identifier |
| CLIENT | Citizens / CFIC |
| PROJECT_VERSION | Citizens project version |
| ENGINE_VERSION | Pinned Enterprise Engine version |
| ENGINE_COMMIT | Engine git SHA if applicable |
| CONFIG_VERSION | Config bundle version |
| CONFIG_HASH | SHA-256 of resolved config |
| SOURCE_MANIFEST_VERSION / HASH | Provenance of source set |
| PLAN_MANIFEST_VERSION / HASH | Plan universe control |
| RATE_MANIFEST_VERSION / HASH | Rate segment control |
| MAPPING_VERSION / HASH | Working or approved mapping set used |
| EXECUTION_TIMESTAMP | UTC |
| EXECUTED_BY | Operator identity |
| MACHINE | Host identifier |
| PYTHON_VERSION | Runtime |
| DEPENDENCY_LOCK_HASH | Lockfile hash |
| ENABLED_MODULES | Pipeline modules executed |
| SELECTED_PLANS | Plan filter |
| SELECTED_RATE_TYPES | Rate-type filter |
| INPUT_FILES | Paths + hashes |
| OUTPUT_FILES | Paths + hashes |
| INPUT_ROW_COUNTS | Per segment |
| OUTPUT_ROW_COUNTS | Per segment |
| REJECTED_ROW_COUNTS | Per segment |
| DUPLICATE_COUNTS | Per segment |
| VALIDATION_RESULT | PASS/FAIL/PARTIAL |
| RECONCILIATION_RESULT | RECONCILED/FAILED/NOT_RUN |
| GIT_COMMIT | Citizens repo commit (when Git exists) |
| NOTES | Free text |

## Rules

1. No publish without a run_manifest.
2. Dry-run still writes a run_manifest with `write_output=false`.
3. Rejected rows must be counted — never silently discarded.
4. Blank, zero, missing, unknown, and N/A remain distinct in counts.
5. Engine version mismatch vs `engine_version.yaml` is a hard fail.

## Implementation Issue

`CIT-ARCH-004` — Run-manifest implementation
