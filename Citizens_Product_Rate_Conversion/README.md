# Citizens Product and Rate Conversion

## Purpose

This repository is the controlled workspace for converting Citizens/CFIC insurance products and actuarial rates into QLAdmin-compatible plan and rate structures. It covers approximately 308 plan codes and an estimated one to two million rate rows across gross premiums, cash values, reserves, net premiums, dividends, interest rates, fees, riders, and related actuarial factors.

## Scope

- Citizens/CFIC source inventory, classification, and authority tracking
- Plan and rate mapping (working and approved)
- Citizens-specific conversion orchestration and client extensions
- Validation, reconciliation, and release packaging for Citizens UAT

## Explicit Separation from CSO

This project is **not** the CSO Full-System Conversion. Do not use, infer, or import CSO mappings, plan codes, source paths, business rules, actuarial assumptions, conversion exceptions, or validation results unless an approved Citizens requirement explicitly references them.

## Explicit Separation from the Enterprise Conversion Engine

Reusable conversion behavior (file ingestion, normalization, mapping frameworks, validation frameworks, output generation) belongs in the separately owned Enterprise Conversion Engine. This repository contains Citizens configuration, source authority, mappings, orchestration, validation evidence, and client-specific extensions only.

Do not copy Enterprise Engine source modules (for example `qla_core`) into this repository. Engine dependencies are declared in `config/engine_version.yaml` and validated by `tools/engine/check_engine_compatibility.py`.

## Major Workstreams

1. **Source inventory and authority** — classify and track all Citizens source files
2. **Plan conversion** — map ~308 Citizens plans to QLAdmin product setup
3. **Rate conversion** — convert rate segments by type (CV, reserve, gross premium, etc.)
4. **Validation and reconciliation** — source-to-output evidence for every segment
5. **Client UAT and release** — controlled delivery packages

## Directory Overview

| Directory | Purpose |
|-----------|---------|
| `config/` | Citizens paths, engine version pin, controlled status values |
| `source/` | Original and supplemental client source (not generated output) |
| `archive/` | Frozen legacy material from pre-restructure work |
| `quarantine/` | Unclassified, duplicate, sensitive, or obsolete review items |
| `discovery/` | Profiling, gap analysis, missing-data research |
| `mappings/` | Working and approved plan/rate mappings |
| `manifests/` | Plan, rate, source, migration, and delivery control files |
| `conversion/` | Citizens orchestration and client extensions |
| `staging/` | Intermediate normalized/rejected conversion data |
| `validation/` | Validation evidence and reconciliation |
| `reports/` | Human-readable run and migration reports |
| `output/` | Draft and release load packages |
| `issues/` | Issue lifecycle documentation |
| `tests/` | Unit, integration, golden-file, and regression tests |
| `docs/` | Architecture, business rules, runbooks |
| `tools/` | Inventory, profiling, migration, and reporting utilities |

## Current Stage

**Stage 4D** — Enterprise Engine Installation and Pin (complete)

- Engine pinned: `qla-enterprise-conversion-engine==0.1.0` (API compatibility `1`)
- Compatibility checker: **PASS**
- CIT-ENGINE-001: **COMPLETE**
- Conversion remains **disabled** by governance gates
- See `Stage4D_Citizens_Engine_Pin_and_Compatibility_Report.md`

## Enterprise Engine

| Field | Value |
|-------|-------|
| Distribution | `qla-enterprise-conversion-engine` |
| Version | `0.1.0` |
| Import | `qla_core` |
| API compatibility | `1` |
| Wheel SHA-256 | `320165544a8fc63d882508fb478ae77b911c2d6e4de5647a7408414b299ff674` |

Install into Citizens `.venv` from the verified wheel only. Editable installs and `sys.path` fallback are prohibited.

**Compatibility check:** `.venv/Scripts/python tools/engine/check_engine_compatibility.py`

Conversion requires approved mappings and authoritative source in addition to a pinned engine.

## Configuration

| Item | Location |
|------|----------|
| Project root marker | `.citizens-project-root` |
| Base config | `config/citizens.yaml`, `source_locations.yaml`, `output_locations.yaml`, `runtime.yaml` |
| Environment overrides | `config/environments/{local,validation,production}.yaml` |
| Loader | `conversion/orchestration/configuration.py` |
| Path constants | `conversion/orchestration/citizens_paths.py` |
| Engine pin | `config/engine_version.yaml` |

**Environment selection:** set `CITIZENS_ENV` (`local`, `validation`, `production`) or pass `environment=` to `load_config()`. Optional `CITIZENS_PROJECT_ROOT` and `CITIZENS_CONFIG_DIR` — cannot override safety rules.

**Safe defaults:** `dry_run=true`, `validation_only=true`, `write_output=false`, `require_approved_mapping=true`, `require_authoritative_source=true`.

**Engine validation:** `python tools/engine/check_engine_compatibility.py`

No conversion can run without approved mappings, authoritative source, and a pinned installed Enterprise Engine package.

## Current Restrictions

- Do not copy source assets from `CFIC_Rates` until Stage 2B is explicitly approved
- Do not modify conversion logic or retarget engine dependencies
- Do not populate approved mappings or fabricate actuarial decisions
- Do not initialize Git until authorized

## Control Documents

- [PROJECT_STATUS.md](PROJECT_STATUS.md) — current stage, blockers, metrics
- [DECISION_LOG.md](DECISION_LOG.md) — signed business and architecture decisions
- [SOURCE_AUTHORITY.md](SOURCE_AUTHORITY.md) — authoritative source per rate type
- [DATA_DICTIONARY.md](DATA_DICTIONARY.md) — field definitions framework
- [RATE_TYPE_CATALOG.md](RATE_TYPE_CATALOG.md) — rate-type definitions framework
- [CHANGELOG.md](CHANGELOG.md) — release and infrastructure history

## Source Project (Read-Only)

Legacy work remains intact at:

`C:\Users\warren\Documents\GitHub\Warrenhughes1974\CFIC_Rates`

That folder is the audit and rollback source. It must not be modified during migration planning stages.

## Ownership

| Role | Responsibility |
|------|----------------|
| Project Lead | Stage gates, PROJECT_STATUS, DECISION_LOG |
| Actuarial / Product | SOURCE_AUTHORITY, rate-type approval |
| Mapping Owner | Working and approved mappings |
| Development | Citizens orchestration and extensions (gated) |
