# CIT-ARCH-001 — Centralized Project Configuration

**Final status:** COMPLETE  
**Date:** 2026-07-12  

## Purpose

Implement environment-independent Citizens project-root and path configuration with schema validation and safety defaults.

## Scope

- Configuration YAML, schemas, loader, path registry, project marker
- Active orchestration path migration
- Unit and integration tests

## Out of scope

- Plan/rate conversion logic
- Business mapping decisions
- Engine packaging

## Implementation

- `.citizens-project-root` marker
- `conversion/orchestration/configuration.py` — load, merge, validate
- `conversion/orchestration/citizens_paths.py` — path constants
- `legacy_cfic_paths.py` — deprecated delegate

## Tests

25 pytest cases — all passed.

## Validation evidence

`reports/development/CIT-ARCH-001_Validation_Report.md`

## Risks

Low — configuration-only; business logic preserved in orchestration transforms.

## Open items

None blocking.

## Rollback

Restore files listed in `reports/development/Stage4B_Rollback_Manifest.csv` using prechange SHA-256 hashes.
