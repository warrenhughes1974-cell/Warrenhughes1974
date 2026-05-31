# Recommended Plan Governance Folder Structure

## Recommendation

Create `plan_governance/` parallel to `claims_analysis/`, with `plan_analysis/` retained as the **read-only authoritative source analysis zone**.

```
plan_analysis/                          # Frozen source extracts + analysis inputs
  quikplan_source.csv                   # PRIMARY product lineage source (authoritative)
  PCOMP.csv                             # Component attributes lookup
  phase_p1b_product_lineage/            # Phase P1B deliverables (this phase)
  README.md                             # Source lineage documentation

plan_governance/                        # Operational governance (future phases)
  config/
    product_governance_rules.json
    semantic_classification_rules.json
    plan_crosswalk_authority_rules.json
  manifests/
    product_review_hold_manifest.csv
    product_governance_delta_summary.txt
  staged/
    quikplan_staged.csv
    quikridr_plan_dependency_report.csv
  workbench/
    product_semantic_classification_workbench.csv  # synced from analysis
    plan_crosswalk_review_queue.csv
  phase_p1c_crosswalk_validation/       # Next phase: join-key proof
  phase_p2_product_runner/              # Isolated conversion runner
  logs/
    product_runner_audit.log
  replay/
    snapshots/                          # Timestamped rollback snapshots

docs/plan_conversion_reference/
  Policy Form Crosswalk 5.22.26.xlsx    # Business authority (versioned)
```

## Rationale

| Zone | Purpose |
|---|---|
| `plan_analysis/` | Discovery, lineage, read-only source analysis — no production emit |
| `plan_governance/` | Holds, manifests, staged emit, replay — mirrors claims_analysis |
| `docs/plan_conversion_reference/` | Business-owned crosswalk artifacts with version dates |

## Manifests

- `product_review_hold_manifest.csv` — active holds blocking emit
- `product_dependency_manifest.json` — machine-readable dependency graph export
- `product_lineage_replay_manifest.csv` — audit trail per rerun

## Do NOT

- Repurpose `Master_Crosswalk.csv` for plan mapping in new architecture
- Write governance artifacts into `QLA_Migration/Output/` without signoff
- Mix product holds into `claims_review_hold_manifest.csv`
