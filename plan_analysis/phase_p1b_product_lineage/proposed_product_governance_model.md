# Proposed Product Governance Model (Phase P1B — Design Only)

## Purpose

Mirror the claims conversion governance pattern: **hold, review, replay, emit** — never silent exclusion or auto-remediation of semantic conflicts.

## Governance Principles

1. Honor confirmed business decisions (MPHASE 1 = base; riders MPHASE > 1).
2. Policy Form Crosswalk 5.22.26 is the business authority for PLAN, FORM, DESCR, PLANNAME — once join key is confirmed.
3. Master_Crosswalk.csv must remain **policy-number authority only**; plan mappings currently embedded (~240 rows) require segregation before production.
4. No HRIGPKEY population or actuarial load until plan catalog is governance-cleared.
5. All holds are reversible via manifest + rollback flag (pattern: `QLA_PRODUCT_GOVERNANCE_HOLD=0`).

## Hold Categories

| Hold Category | Trigger | Review Owner | Emit Behavior |
|---|---|---|---|
| UNMAPPED_PLAN | LifePRO COVERAGE_ID absent from Policy Form Crosswalk | Product / Actuarial | Block quikplan row emit |
| DUPLICATE_PLAN | Duplicate PLAN primary key in staged quikplan | Product | Block affected rows |
| INVALID_FORM | FORM blank or not in crosswalk QL Form Number | Product | Hold row; allow base plan review |
| ORPHAN_RIDER | quikridr.MPLAN not in quikplan.PLAN | Conversion / Product | Hold dependent quikridr rows |
| MISSING_HRIGPKEY | Rate attachment attempted without HRIGPKEY strategy | Actuarial | Block actuarial phase only |
| INVALID_VARYBY | Inconsistent UWVARY/BDVARY/STVARY/GDVARY combination | Actuarial | Hold plan row for rate prep |
| CROSSWALK_CONFLICT | Crosswalk vs source vs output divergence | Product | Hold; business review workbench |
| SEMANTIC_CLASSIFICATION_CONFLICT | Base vs rider vs supplemental ambiguity | Product | Hold; semantic workbench |
| LEGACY_MASTER_CROSSWALK_PLAN | Plan mapping sourced from Master_Crosswalk | Architecture | Hold until segregated |
| EFFECTIVE_DATE_OVERLAP | Superseded form/plan without version key | Product / Compliance | Hold pending version decision |

## Manifest Pattern (Proposed)

`plan_governance/manifests/product_review_hold_manifest.csv`

Columns aligned to claims governance:
- hold_category, lifepro_coverage_id, output_plan, target_field
- source_value, crosswalk_value, current_output_value
- governance_status, business_review_required, remediation_recommendation
- rulebook_lineage, audit_timestamp, rollback_flag

## Replay Model

1. Analyst updates crosswalk or business decision record (not source extracts).
2. Re-run isolated product runner (`phase_p1c+`) against frozen `plan_analysis/quikplan_source.csv`.
3. Diff staged vs prior manifest; append governance delta summary.
4. Business signoff gate before merge to `output/quikplan.csv`.

## Rollback Model

- Staged outputs under `plan_governance/staged/` never overwrite production output directly.
- app.py Product tab emits only governance-cleared rows.
- Rollback = restore prior manifest + prior staged CSV snapshot.

## Relationship to Claims Governance

Product governance is **upstream** of claims/policy conversion:
- quikridr.MPLAN → quikplan.PLAN
- quikactg.MPLAN → quikplan.PLAN
- Orphan plan catalog breaks policy phase linkage and downstream validation

Do NOT alter claims orchestration; product runner remains isolated subprocess.
