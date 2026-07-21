# CIT-ENGINE-001 Package Discovery Report

**Generated:** 2026-07-12  
**Classification:** BLOCKED_BY_EXTERNAL_ENGINE / SOURCE_ONLY_NOT_PACKAGED  

## Discovery scope

Read-only inspection of:

- Monorepo path: `Warrenhughes1974/qla_core/` (~60 Python modules)
- Installed Python environment (`importlib.metadata`)
- Citizens `config/engine_version.yaml`

No Enterprise Engine source was modified or copied.

## Packaging artifacts searched

| Artifact | Result |
|----------|--------|
| `pyproject.toml` (repo root) | Not found |
| `setup.py` | Not found |
| `setup.cfg` | Not found |
| Wheel artifacts in repo | Not found |
| Installed distribution | Not found |

## Recorded identity

| Field | Value |
|-------|-------|
| Distribution package name | `null` (unresolved) |
| Import package name | `qla_core` (confirmed from module layout) |
| Exact package version | `null` (unresolved) |
| Package source | Monorepo source directory (not packaged) |
| Package hash | `null` |
| Engine commit | Not recorded |
| Packaging status | SOURCE_ONLY_NOT_PACKAGED |
| Installation status | NOT_INSTALLED |

## Required API symbols (Citizens)

- `qla_core.rate_dbf_schema`
- `qla_core.rate_factor_loader`
- `qla_core.rate_key_setup`
- `qla_core.rate_member_setup`
- `qla_core.rate_dbf_writer`

See `docs/architecture/ENTERPRISE_ENGINE_API_CONTRACT.md`.

## Compatibility risks

1. No semver pin possible until distribution metadata exists.
2. Active orchestration imports fail without install (`EnginePackageRequiredError`).
3. Monorepo `sys.path` bootstrap removed — no silent fallback.

## Outcome

**BLOCKED_BY_EXTERNAL_ENGINE**

Citizens-side boundary completed:

- `config/engine_version.yaml` — status `PACKAGING_REQUIRED`
- `conversion/orchestration/engine_import.py` — standard import, clear error
- `tools/engine/check_engine_compatibility.py` — read-only checker
- No `pyproject.toml` engine dependency pin (would require fabricated version)

## External packaging requirements

Enterprise Engine owners must:

1. Add `pyproject.toml` with distribution name and version.
2. Publish installable wheel/sdist with recorded SHA-256.
3. Confirm import name `qla_core` (or provide migration map).
4. Document API compatibility version.
5. Enable Citizens pin: `distribution_name == exact_version` in Citizens `pyproject.toml`.

## Corrective action

Install pinned package after external publication. Re-run:

```bash
python tools/engine/check_engine_compatibility.py
```

Expected PASS only when distribution name, exact version, and all required modules import successfully.
