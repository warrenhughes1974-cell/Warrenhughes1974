# Changelog

All notable infrastructure and release changes for the Citizens Product and Rate Conversion project.

## [Unreleased]

### Added — Stage 4D (2026-07-12)

- Installed `qla-enterprise-conversion-engine==0.1.0` from verified wheel
- `config/engine_artifact.yaml`, `requirements-lock.txt`
- Enhanced compatibility checker (API version, per-module symbols)
- Stage 4D reports and integration tests

### Changed — Stage 4D

- `config/engine_version.yaml` — status `PINNED`
- `pyproject.toml` — exact engine dependency pin
- CIT-ENGINE-001 closed COMPLETE

### Unchanged — Stage 4D

- Plan/rate conversion logic
- Source authority (PROPOSED)
- mappings/approved (empty)
- Conversion not run

### Test results

- pytest: 29 passed, 0 failed
- Engine compatibility: PASS

### Added — Stage 4B (2026-07-12)

- Centralized configuration: YAML, schemas, loader, `.citizens-project-root` marker
- `citizens_paths` path registry; deprecated `legacy_cfic_paths` wrapper
- Enterprise Engine boundary: `engine_import.py`, compatibility checker, API contract
- Configuration and engine tests (25 passed)
- Stage 4B reports, rollback manifest, issue records CIT-ARCH-001 / CIT-ENGINE-001

### Changed — Stage 4B

- Active orchestration scripts migrated to centralized paths (5 scripts)
- Removed active `sys.path` injection from orchestration layer
- `package_cfic_rates.py` gated by `assert_conversion_allowed()`

### Unchanged — Stage 4B

- Plan/rate conversion business logic
- Source files and manifests (governance)
- mappings/approved (empty)
- Source authority (PROPOSED)

### Test results

- pytest: 25 passed, 0 failed
- Engine compatibility: BLOCKED (PACKAGING_REQUIRED)

### Known blockers

- Enterprise Engine (`qla_core`) requires external packaging and exact version pin

### Added — Stage 4A (2026-07-12)

- Source authority register and domain matrix (PROPOSED only)
- Plan universe master reconciliation (340 codes); 308↔301 bridge
- Crosswalk/reserve coverage analyses; alias relationship candidates
- Rate-requirement authority matrix; working plan_manifest.csv populated
- DECISION_LOG CIT-DEC-001…020 (PROPOSED); SOURCE_AUTHORITY.md updated
- Stage4A_Source_Authority_and_Plan_Universe_Report.md

### Added — Stage 3 (2026-07-12)

- Architecture baseline integrity verification (380/380 hashes)
- Technical asset manifest, entry-point inventory, qla_core dependency matrix
- Current- and target-state pipeline docs; configuration and run-manifest standards
- Plan-universe and rate-universe baselines; unsafe-script register
- Stage 4 technical backlog (24 proposed issues)
- Stage3_Architecture_and_Execution_Readiness_Report.md

### Added — Stage 2B (2026-07-12)

- Executed controlled classified copy migration (380 files verified, 123 excluded)
- Populated `manifests/source_manifest.csv`
- Updated `manifests/migration_inventory.csv` with Stage 2B review/copy columns
- Generated Stage 2B reports and source integrity snapshot
- Added README warnings in archive, quarantine, and draft output folders
- Updated `.gitignore` for large cash-value ZIP protection

### Added — Stage 2A (2026-07-12)

- Created `Citizens_Product_Rate_Conversion` destination directory structure
- Added project-control document stubs (README, PROJECT_STATUS, DECISION_LOG, SOURCE_AUTHORITY, DATA_DICTIONARY, RATE_TYPE_CATALOG)
- Added `.cursor/rules/citizens-project.mdc` project rule
- Added `.gitignore` for Python, C#, generated output, and confidential source exclusions
- Added read-only inventory utility under `tools/inventory/`
- Generated `manifests/migration_inventory.csv` (dry-run; `COPY_APPROVED = NO` on all rows)
- Generated `manifests/preflight_source_snapshot.json` and post-run source comparison
- Generated manifest schema headers (plan, rate, source, delivery)
- Added `config/controlled_status_values.yaml`
- Generated Stage 2A dry-run migration reports under `reports/migration/`

**Not included in Stage 2A:** source asset copy, approved mappings, plan/rate manifest population, Git initialization, conversion execution.
