# ENG-PKG-001 Dependency Analysis

**Date:** 2026-07-12  

## Citizens-required modules (import-time)

| Module | Stdlib | Required runtime | Optional at call-time |
|--------|--------|------------------|----------------------|
| rate_dbf_schema | yes | none | none |
| rate_factor_loader | csv, collections | none | openpyxl (`load_plan_crosswalk`) |
| rate_key_setup | collections | none | none |
| rate_member_setup | collections | none | none |
| rate_dbf_writer | os, tempfile | none | dbf (DBF emit functions) |

**Citizens-required import path:** stdlib only — no required third-party dependencies.

## Full qla_core package (optional extras)

| Dependency | Classification | Used by |
|------------|----------------|---------|
| dbf | Optional runtime | `rate_dbf_writer` DBF functions |
| openpyxl | Optional runtime | `rate_factor_loader.load_plan_crosswalk` |
| pandas | Optional runtime | converters (quikplan, quikloan, etc.) |
| numpy | Optional runtime | reinsurance, quikloan converters |

## Not package dependencies

| Item | Reason |
|------|--------|
| Citizens | Client project |
| CSO / QLA_Migration | Client application |
| CFIC_Rates | Client source |
| plan_analysis | Monorepo data path, not pip package |

## pyproject.toml declaration

```toml
dependencies = []

[project.optional-dependencies]
dbf = ["dbf>=0.99.0"]
crosswalk = ["openpyxl>=3.1.0"]
converters = ["pandas>=2.0.0", "numpy>=1.24.0"]
all = [...]
```

## Unknown / unresolved

- License metadata — release review item
