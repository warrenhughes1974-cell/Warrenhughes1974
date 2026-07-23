# Phase R7B — QuikPlan Rate Variation Integration Summary

Rate-derived plan values option flags are applied as a controlled post-processing
step after quikplan conversion. Only approved variation fields are modified.

## Integration results

| Metric | Value |
|---|---|
| Quikplan rows | 141 |
| Plans with rate-derived updates | 2 |
| Plans with PLANVALOPT = Y | 134 |
| Field diffs recorded | 19 |
| Validation blockers | 0 |

### Y-flag counts (updated plans)

- BDVARYGP: 134
- BDVARYDB: 134
- BDVARYCV: 134
- BDVARYTV: 134
- BDVARYDV: 134
- STVARYGP: 134
- GDVARYTV: 93
- GDVARYCV: 90
- GDVARYGP: 85
- GDVARYDB: 85
- GDVARYDV: 85
- UWVARYGP: 25
- UWVARYTV: 24
- UWVARYCV: 6

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

- **ROW_COUNT_PRESERVED**: PASS — before=141 after=141
- **SCHEMA_COLUMN_ORDER**: PASS — expected 79 cols; orig=79 enr=79
- **ONLY_APPROVED_FIELDS_CHANGED**: PASS — blockers=0
- **PLANVALOPT_CONSISTENCY**: PASS — plans_checked=136
- **STVARY_NON_GP_ONLY_WHEN_MULTI_STATE**: PASS — none
- **DEFERRED_ACTUARIAL_ASSUMPTIONS_UNCHANGED**: PASS — unchanged
- **PLAN_NO_SPACES**: PASS — invalid=[]
- **NP_VARIATION_FIELDS_NOT_CREATED**: PASS — NP has no quikplan VARY fields; excluded by design
- **EXCLUDED_TYPE_CODES_NOT_USED**: PASS — excluded=NN,PN,SL,TP,TX,UF

## Output files

- `quikplan_variation_field_diffs.csv`
- `quikplan_variation_integration_validation.csv`
- Main quikplan: `QLA_Migration/Output/quikplan.csv`

