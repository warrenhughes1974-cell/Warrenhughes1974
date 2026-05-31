# Executive Crosswalk Governance Findings — Phase P2D

**Date:** 2026-05-26 09:12:43
**Phase:** P2D — Crosswalk / Translation Governance Audit
**Conversion engine:** Unchanged (qla_core/quikplan_converter.py)

## Current State

The product setup conversion architecture is **fundamentally correct** and validated:

- **133 rows × 79 columns** — P2A/P2C parallel validation IDENTICAL (0 cell differences)
- Flow: `quikplan_source` → Master_Crosswalk PLAN enrichment → rulebook → PCOMP → quikplan
- Policy Form Crosswalk overlay **disabled** (`CROSSWALK_OVERLAY=0`) — correct default
- Product setup isolated subprocess operational (P2C)

## Governance Audit Summary

| Metric | Count |
|--------|-------|
| Total audit findings | 715 |
| ERROR severity | 110 |
| WARN severity | 282 |
| INFO severity | 323 |
| Master_Crosswalk policy mappings | 4920 |
| Master_Crosswalk plan/entity mappings | 423 |
| Policy Form Crosswalk rows | 141 |
| Source COVERAGE_IDs | 133 |
| Rulebook unmapped schema fields | 0 |
| Rulebook stale targets | 0 |
| Untranslated output values (candidate) | 230 |
| Unused translation entries | 128 |
| Missing PCOMP lookup rows | 23 |
| Orphan MPLAN codes | 7 |
| Passthrough LifePRO PLAN codes | 31 |

## Authoritative Ownership (Summary)

- **PLAN**: current `Master_Crosswalk Old_Value->New_Value on COVERAGE_ID` → proposed `Policy Form Crosswalk ql_plan_code` (OVERLAP)
- **FORM**: current `LifePRO POLICY_FORM_NUM via rulebook` → proposed `Policy Form Crosswalk ql_form_number` (OVERLAP)
- **DESCR**: current `LifePRO DESCRIPTION via rulebook` → proposed `Policy Form Crosswalk ql_plan_description` (PARTIAL)
- **PLANNAME**: current `LifePRO DESCRIPTION duplicated via rulebook` → proposed `Policy Form Crosswalk ql_friendly_name` (CONFLICT)
- **Policy_Number**: current `Master_Crosswalk (901xxxxxxxx rows)` → proposed `Master_Crosswalk` (CONFIRMED)
- **Value_Translation**: current `Master_Value_Translation.csv` → proposed `Master_Value_Translation.csv` (CONFIRMED)
- **Rulebook_Transforms**: current `Sync_Rulebook_quikplan.csv` → proposed `Sync_Rulebook_quikplan.csv` (CONFIRMED)
- **PCOMP_Lookup**: current `PCOMP.csv via rulebook join` → proposed `PCOMP.csv` (CONFIRMED)
- **HRIGPKEY**: current `Rulebook default blank` → proposed `Future actuarial governance (P5)` (FUTURE)
- **MPLAN**: current `quikridr transactional reference` → proposed `quikplan.PLAN catalog` (DOWNSTREAM)

## Key Gaps & Risks

### 1. Dual PLAN Authority (Highest Priority)

PLAN codes are currently driven by **Master_Crosswalk** (`Old_Value=COVERAGE_ID → New_Value=PLAN`).
Policy Form Crosswalk defines **future authoritative** `ql_plan_code` values.
Overlay simulation produces **249 cell differences** across **4 fields**.
Business must reconcile before overlay activation.

### 2. Duplicate PLAN in Current Catalog

Known ERROR: duplicate PLAN `9DIS25` (2 rows) — blocks emit only when `QLA_PRODUCT_GOVERNANCE_BLOCK=1`.
Overlay duplicate PLAN codes: none simulated

### 3. Master_Crosswalk Scope Drift

Master_Crosswalk contains **423 plan/entity mappings** mixed with **4920 policy-number mappings**.
Policy-number mappings must remain separate from product catalog PLAN authority.

### 4. FORM / PLANNAME Conflicts vs Crosswalk

**119** FORM mapping inconsistencies detected vs Policy Form Crosswalk.
PLANNAME currently mirrors DESCRIPTION; crosswalk provides distinct friendly names.

### 5. Actuarial Readiness

Catalog dimensions (PLAN, FORM, SEX) populated. HRIGPKEY and vary-by fields intentionally blank.
Actuarial attachment (gross premiums, cash values, reserves, dividends) requires **Phase P5** — not blocking catalog emit.

## Crosswalk Overlay Readiness

- **Safe to enable automatically:** NO (`CROSSWALK_OVERLAY` must remain `0`)
- **Simulated cell differences:** 249
- **Baseline unique PLAN:** 132 | **Overlay unique PLAN:** 133
- **Assessment:** Overlay NOT safe for production enablement — differences detected or duplicate PLAN risk

## Recommended Remediation Order

1. **Resolve duplicate PLAN `9DIS25`** — business catalog integrity
2. **Review Policy Form Crosswalk vs current PLAN mappings** — establish signed-off PLAN authority
3. **Quarantine passthrough LifePRO IDs** — see `unresolved_passthrough_ids.csv`
4. **Review FORM conflicts** — see `missing_form_mappings.csv`
5. **Complete missing crosswalk rows** — see `missing_plan_crosswalk_rows.csv`
6. **Validate orphan MPLAN codes** — downstream quikridr linkage
7. **Translation table cleanup** — review unused entries (informational)
8. **Overlay pilot in staged mode only** — after steps 1–5 signed off
9. **Phase P5 actuarial governance** — HRIGPKEY + vary-by dimensions

## Scaffold Artifacts (Detect-Only — No Auto-Remediation)

Generated under `plan_analysis/phase_p2d_governance_audit/scaffold/`:

- `missing_plan_crosswalk_rows.csv`
- `untranslated_values.csv`
- `orphan_plan_codes.csv`
- `missing_form_mappings.csv`
- `unresolved_passthrough_ids.csv`
- `duplicate_plan_mappings.csv`

## Governance Manifests

Updated under `plan_governance/manifests/`:

- `product_governance_manifest.csv`
- `crosswalk_governance_manifest.csv`
- `translation_governance_manifest.csv`
- `unresolved_product_mapping_manifest.csv`

## Engineering Constraints Honored

- No conversion semantic redesign
- No source file mutation
- No app.py changes (audit-only phase)
- No overlay auto-enablement
- Claims / policy / UAT flows untouched
