# qla_core Versioning Standard

**Distribution:** `qla-enterprise-conversion-engine`  
**Import package:** `qla_core`  

## Version fields

| Field | Location | Purpose |
|-------|----------|---------|
| Distribution version | `pyproject.toml`, `qla_core.__version__` | Semver for installable releases |
| API compatibility version | `qla_core.API_COMPATIBILITY_VERSION` | Stable contract boundary for client checkers |

These are **distinct**:

- Distribution `0.1.0` = first controlled Python distribution (packaging-only initial release)
- API compatibility `1` = Citizens-required rate module contract generation

## Initial version decision (ENG-PKG-001)

No authoritative package version existed. Initialized at **0.1.0** per Stage 4C specification.

This does **not** represent:

- Citizens project version
- CSO project version
- QLAdmin application version
- Client UAT release version

## Semantic versioning rules

| Bump | When |
|------|------|
| PATCH | Compatible fixes; no API or business-behavior change |
| MINOR | Backward-compatible API additions |
| MAJOR | Incompatible API changes |

## API compatibility change rules

Increment `API_COMPATIBILITY_VERSION` when:

- A PUBLIC_STABLE symbol signature changes
- A required module is renamed or removed
- Import paths for Citizens-required modules change

Do **not** increment for packaging-only changes, documentation, or internal refactors with stable public API.

## Client validation

Client projects (Citizens) should verify:

1. `importlib.metadata.version("qla-enterprise-conversion-engine") == config exact_version`
2. `qla_core.__version__` matches distribution metadata
3. `qla_core.API_COMPATIBILITY_VERSION` meets minimum required compatibility

API compatibility does **not** guarantee actuarial or client-rule compatibility.
