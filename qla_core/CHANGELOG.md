# qla_core Changelog

## [0.1.0] — 2026-07-12

### Added (packaging only)

- Installable distribution `qla-enterprise-conversion-engine` version `0.1.0`
- `qla_core.__version__` and `qla_core.API_COMPATIBILITY_VERSION`
- Repository `pyproject.toml` with setuptools build backend
- Packaging tests under `tests/engine_packaging/`
- Packaging documentation under `docs/packaging/`

### Unchanged

- Rate calculations and normalization
- Rate-key and member construction logic
- DBF schema definitions and field formats
- Writer output formatting
- All public function signatures used by Citizens

### Notes

- Business and actuarial behavior unchanged
- No client rules, mappings, or source data added to package
- Optional dependencies: `dbf`, `openpyxl`, `pandas`, `numpy` (extras)
