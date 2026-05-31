# v57.3 — Product Business Test Cut

Generated: 2026-05-31 19:45:58 UTC

## Executive summary

This cut packages completed product governance (P3C/P3E/P3G), non-product row
classification, and R7A/R7B rate variation flags into a single business-testable
build. Claims, policy conversion, and rate loader remain isolated/compatible.

## Validation summary

| Metric | Value |
|---|---|
| Checks passed | 26 |
| Warnings | 0 |
| Blockers | 0 |
| quikplan rows | 140 |
| PLANVALOPT = Y | 75 |
| quikridr rows | 11698 |
| non-blank MPLAN | 9350 |
| orphan MPLAN | 0 |

## Promoted phases

| Phase | Capability |
|---|---|
| P3C | Closed product catalog authority |
| P3E | quikridr MPLAN alignment |
| P3G | Quikplan source completeness (140 rows) |
| NP Gov | EXPECTED_NON_PRODUCT_ROW (BENEFIT_SEQ 99 / UV) |
| R7A/R7B | PLANVALOPT / *VARY* from rate segmentation |
| R5/R6 | Rate DBF infrastructure (isolated, compatible) |

## Deferred (not in this cut)

See `deferred_actuarial_assumptions_note.md` — MORT, RSVINT, etc.

## Rollback

- `QLA_SKIP_RATE_VARIATION_FLAGS=1` — disable R7B enrichment
- `QLA_ALLOW_LEGACY_PRODUCT_FALLBACK=1` — legacy product authority (not recommended)
- `QLA_ALLOW_LEGACY_MPLAN_FALLBACK=1` — legacy MPLAN fallback
- Standalone R7A/R7B runners remain for audit-only regeneration

## Regeneration commands

```bash
python plan_analysis/product_business_test_cut/run_product_business_test_cut.py --regenerate
python plan_governance/phase_p2_product_setup_runner/product_setup_runner.py --emit --uat-overlay --closed-product-authority --output-dir QLA_Migration/Output
python plan_analysis/phase_p3e_quikridr_authority_alignment/phase_p3e_quikridr_authority_runner.py --closed-mplan-authority --emit
python plan_analysis/phase_r7b_quikplan_rate_variation_integration/run_r7b_integration.py
python plan_analysis/phase_r5_rate_loader/rate_loader_emit.py
```

## Check details

- **QUIKPLAN_ROW_COUNT**: PASS — rows=140 expected=140
- **QUIKPLAN_SCHEMA**: PASS — cols=79 expected=79
- **ALL_CATALOG_PLANS_EMITTED**: PASS — all 140 present
- **NO_UNAUTHORIZED_PLANS**: PASS — none
- **NO_PLAN_SPACES**: PASS — none
- **NO_PASSTHROUGH_PLANS**: PASS — none
- **ROW_COUNT_PRESERVED**: PASS — before=140 after=140
- **SCHEMA_COLUMN_ORDER**: PASS — expected 79 cols; orig=79 enr=79
- **ONLY_APPROVED_FIELDS_CHANGED**: PASS — blockers=0
- **PLANVALOPT_CONSISTENCY**: PASS — plans_checked=120
- **STVARY_REMAINS_N_UNLESS_STATE_VARIATION**: PASS — none
- **DEFERRED_ACTUARIAL_ASSUMPTIONS_UNCHANGED**: PASS — unchanged
- **PLAN_NO_SPACES**: PASS — invalid=[]
- **NP_VARIATION_FIELDS_NOT_CREATED**: PASS — NP has no quikplan VARY fields; excluded by design
- **EXCLUDED_TYPE_CODES_NOT_USED**: PASS — excluded=NF,NN,PN,SL,TP,TX,UF
- **EMITTED_MATCHES_RATE_DERIVATION**: PASS — aligned
- **RATE_VARIATION_ENRICHMENT_ENABLED**: PASS — enabled
- **PLANVALOPT_Y_COUNT**: PASS — count=75
- **QUIKRIDR_MPLAN_ALIGNMENT**: PASS — {'emitted_rows': 11698, 'non_blank_mplan': 9350, 'outside_quikplan': 0, 'with_spaces': 0, 'unique_outside': []}
- **QUIKRIDR_NO_ORPHAN_MPLAN**: PASS — outside=0
- **QUIKRIDR_NO_MPLAN_SPACES**: PASS — spaced=0
- **QUIKRIDR_BLANK_MPLAN_ROWS**: PASS — blank_mplan_rows=2348
- **NON_PRODUCT_ROWS_CLASSIFIED**: PASS — expected_non_product_source_rows_sampled=11699 (BENEFIT_SEQ 99/UV)
- **RATE_EMIT_DBF_PRESENT**: PASS — key_tables_present=6/6 dir=C:\Users\warren\Documents\GitHub\Warrenhughes1974\plan_analysis\phase_r5_rate_loader\emitted_dbf
- **RATE_DBF_PLAN_OVERLAP**: PASS — quikplan_rate_plan_overlap=85
- **RATE_LOADER_ISOLATED**: PASS — Rate DBFs under plan_analysis/phase_r5_rate_loader/emitted_dbf; production DBFs untouched
