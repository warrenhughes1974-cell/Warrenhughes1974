# Phase R7A — QuikPlan Rate Variation Flag Summary

## How flags were derived

Segmentation was inferred from in-scope LifePRO rate rows only:

| TYPE_CODE | Rate family | Flag suffix |
|---|---|---|
| PR | Gross Premium | GP |
| DB | Death Benefit | DB |
| CV | Cash Value | CV |
| RV | Terminal Reserve | TV |
| DV | Dividend | DV |

Sources scanned (merged per plan/family):

1. `Rate_Table_Extract` — direct COVERAGE_ID → PLAN crosswalk
2. `PAAGERAT` — segment-resolved via PCOVRSGT → PCOVR → crosswalk
3. Optional emitted `QuikPlxx` key DBFs under `emitted_dbf/`

A dimension is **Y** when more than one distinct mapped value appears for that
plan + rate family (gender / UW class / band / state+country).

Excluded TYPE_CODEs (NN, PN, TP, TX, UF, NF, SL) and NP are not used.
State/country variation is **N** unless distinct ISSCNTRY/ISSUEST keys appear
(source extracts carry no state/country; emitted keys may supplement).

## Results

| Metric | Count |
|---|---|
| Plan/family combinations analyzed | 222 |
| Distinct plans with rate observations | 121 |
| Plans with flag updates | 120 |
| Plans with PLANVALOPT = Y | 75 |
| Validation blockers | 0 |

### Variation by dimension (plan/family rows where Y)

- gender: 109
- uwclass: 29
- band: 12

### Rate families observed

- GROSS_PREMIUM: 86 plan/family rows
- TERMINAL_RESERVE: 54 plan/family rows
- CASH_VALUE: 47 plan/family rows
- DEATH_BENEFIT: 20 plan/family rows
- DIVIDEND: 15 plan/family rows

### Populated flags (plans with Y)

- GDVARYTV: 43 plans
- GDVARYGP: 31 plans
- GDVARYCV: 28 plans
- UWVARYGP: 16 plans
- BDVARYGP: 12 plans
- UWVARYTV: 9 plans
- GDVARYDV: 5 plans
- UWVARYCV: 4 plans
- GDVARYDB: 2 plans

## Assumptions

- SEX/BAND/UWCLS mapped via confirmed `rate_dbf_schema` crosswalks.
- PAAGERAT uses RECORD_SEQ=1 primary tables only.
- Plans without in-scope rate rows are not modified in quikplan output.
- `PLANVALOPT=Y` iff any `*VARY*` flag is Y for that plan.

## Limitations

- Source extracts do not carry issue state/country; STVARY* remains N unless
  emitted rate-key DBFs show multiple ISSCNTRY/ISSUEST combinations.
- Value-difference detection across dimensions uses distinct-value counts only
  (not full actuarial grid equivalence).
- NP net-premium segmentation does not map to quikplan VARY fields.

## Output files

- **Analysis:** `plan_analysis\phase_r7a_quikplan_rate_variation_flags\quikplan_rate_variation_analysis.csv`
- **Flag updates:** `plan_analysis\phase_r7a_quikplan_rate_variation_flags\quikplan_variation_flag_updates.csv`
- **Summary:** `plan_analysis\phase_r7a_quikplan_rate_variation_flags\quikplan_variation_flag_summary.md`
- **Enriched quikplan:** `plan_analysis\phase_r7a_quikplan_rate_variation_flags\quikplan_with_rate_variation_flags.csv`
