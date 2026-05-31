# Recommended Folder Structure (Phase P1C)

## Design Principle

Separate **frozen analysis sources**, **operational governance**, and **shared conversion core** — mirror the claims_analysis pattern without mixing product holds into claims manifests.

```
Warrenhughes1974/
├── plan_analysis/                              # Read-only source + analysis
│   ├── quikplan_source.csv                     # PRIMARY product source (authoritative)
│   ├── PCOMP.csv                               # Component lookup for rulebook
│   ├── phase_p1b_product_lineage/              # P1B discovery artifacts
│   └── phase_p1c_product_setup_isolation/      # P1C architecture (this phase)
│
├── plan_governance/                            # Operational product lifecycle
│   ├── config/
│   │   ├── product_setup_runner_config.json    # Paths, flags, timeouts
│   │   └── product_governance_diagnostics.json # Additive hold rules (optional)
│   ├── manifests/
│   │   ├── product_setup_run_manifest.csv      # Per-run audit trail
│   │   ├── product_governance_diagnostics.csv  # Non-blocking findings
│   │   └── product_emit_manifest.csv           # Emitted row lineage
│   ├── staged/
│   │   └── quikplan_staged.csv                 # Pre-emit staging
│   ├── emitted/
│   │   └── quikplan.csv                        # Governance-cleared emit (copy target)
│   ├── dbf/
│   │   ├── quikplan.dbf                        # Optional UAT DBF
│   │   ├── quikplan_dbf_manifest.csv
│   │   └── quikplan_dbf_alignment_summary.txt
│   ├── logs/
│   │   └── product_setup_runner.log
│   ├── replay/
│   │   └── snapshots/                          # Timestamped rollback copies
│   └── phase_p2_product_setup_runner/
│       ├── product_setup_runner.py             # Subprocess entry point
│       └── product_setup_governance_engine.py  # Additive diagnostics
│
├── qla_core/                                   # NEW — shared extraction (P2)
│   ├── __init__.py
│   ├── quikplan_converter.py                   # Extracted rulebook engine
│   ├── crosswalk_enrichment.py                 # Policy Form Crosswalk join
│   └── schema_constants.py                     # TABLE_SCHEMAS quikplan fields
│
├── QLA_Migration/
│   ├── Configs/
│   │   └── Sync_Rulebook_quikplan.csv          # UNCHANGED — authoritative rulebook
│   ├── Mapping/
│   │   ├── Master_Value_Translation.csv
│   │   └── Master_Crosswalk.csv                # Policy numbers (+ legacy plan rows)
│   └── Output/
│       ├── quikplan.csv                        # Production emit target
│       └── quikplan.dbf                        # QLAdmin load target (future)
│
└── docs/plan_conversion_reference/
    └── Policy Form Crosswalk 5.22.26.xlsx      # Business crosswalk (versioned)
```

## Zone Responsibilities

| Zone | Writable? | Purpose |
|---|---|---|
| `plan_analysis/` | No (source extracts frozen) | Lineage analysis inputs |
| `plan_governance/` | Yes (staged/manifests/logs) | Product lifecycle + replay |
| `qla_core/` | Yes (shared library) | Single transformation engine |
| `QLA_Migration/Output/` | Emit only after signoff | Production catalog consumed by batch |
| `docs/plan_conversion_reference/` | Business-owned | Crosswalk versioning |

## Manifest Files

### product_setup_run_manifest.csv

Per-run record: timestamp, source hash, crosswalk version, rulebook path, row counts, emit flag, rollback snapshot path.

### product_governance_diagnostics.csv

Additive findings (default: WARN, not HOLD):

- `DUPLICATE_PLAN`
- `MISSING_CROSSWALK_MATCH`
- `ORPHAN_MPLAN`
- `BLANK_FORM`
- `CROSSWALK_FIELD_MISMATCH`
- `BLANK_CRITICAL_FIELD`

### product_emit_manifest.csv

Rows actually copied to `output/quikplan.csv` with lineage: `lifepro_coverage_id`, `output_plan`, `emit_timestamp`, `rulebook_lineage`.

## Separation from Claims

| Artifact | Product | Claims |
|---|---|---|
| Hold manifest | `product_governance_diagnostics.csv` | `claims_review_hold_manifest.csv` |
| Runner | `product_setup_runner.py` | `phase22_semantic_governance_runner.py` |
| Rollback flag | `QLA_PRODUCT_SETUP_ROLLBACK` | `QLA_SEMANTIC_GOVERNANCE_HOLD` |
| DBF subdir | `plan_governance/dbf/` | `output/claims_uat_dbf/` |

Do NOT merge product diagnostics into claims governance.
