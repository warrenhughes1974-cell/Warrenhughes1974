# Phase R7B — QuikPlan Rate Variation Integration Summary

Rate-derived plan values option flags are applied as a controlled post-processing
step after quikplan conversion. Only approved variation fields are modified.

## Integration results

| Metric | Value |
|---|---|
| Quikplan rows | 140 |
| Plans with rate-derived updates | 120 |
| Plans with PLANVALOPT = Y | 75 |
| Field diffs recorded | 2520 |
| Validation blockers | 0 |

### Y-flag counts (updated plans)

- GDVARYTV: 43
- GDVARYGP: 31
- GDVARYCV: 28
- UWVARYGP: 16
- BDVARYGP: 12
- UWVARYTV: 9
- GDVARYDV: 5
- UWVARYCV: 4
- GDVARYDB: 2

## Deferred actuarial assumptions (not populated)

Business confirmed no source table is available for:

- `MORT`
- `ETIMORT`
- `RSVINT`
- `RSVMETH`
- `INTMETHCV`
- `INTMETHTV`
- `NFOINT`
- `STOREMEANS`
- `CALCMIDS`

These remain blank/deferred — not defects. Do not infer from rate data.

## Validation

- **ROW_COUNT_PRESERVED**: PASS — before=140 after=140
- **SCHEMA_COLUMN_ORDER**: PASS — expected 79 cols; orig=79 enr=79
- **ONLY_APPROVED_FIELDS_CHANGED**: PASS — blockers=0
- **PLANVALOPT_CONSISTENCY**: PASS — plans_checked=120
- **STVARY_REMAINS_N_UNLESS_STATE_VARIATION**: PASS — none
- **DEFERRED_ACTUARIAL_ASSUMPTIONS_UNCHANGED**: PASS — unchanged
- **PLAN_NO_SPACES**: PASS — invalid=[]
- **NP_VARIATION_FIELDS_NOT_CREATED**: PASS — NP has no quikplan VARY fields; excluded by design
- **EXCLUDED_TYPE_CODES_NOT_USED**: PASS — excluded=NF,NN,PN,SL,TP,TX,UF

## Output files

- `quikplan_variation_field_diffs.csv`
- `quikplan_variation_integration_validation.csv`
- Main quikplan: `QLA_Migration/Output/quikplan.csv`

