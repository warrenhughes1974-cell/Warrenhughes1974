# Missing Source Proof Summary

This proof searches the delivered source files for the exact IDs/rate types raised by the client.

## What These Files Are

- `Rate_Table_Extract_20260427.csv`: the LifePRO age/duration rate-value extract. This is where the converter expects rate rows such as CV, NP, RV, NF, DB, and similar duration-based factors.
- `PAAGERAT_AttainedAge_Rates_Extract_20260428.csv`: the LifePRO attained-age rate-value extract. This is where the converter expects attained-age rows such as PR gross premiums and other scalar attained-age rates.
- `PCOVR.csv`: the LifePRO coverage setup extract. This tells us whether a coverage ID exists as a delivered product/coverage row.
- `PCOVRSGT.csv`: the LifePRO coverage-to-segment setup extract. This can show that one product points to another segment ID, but it does not contain the actual rate values.

## Search Logic Used

For each client-raised ID, the proof checks:

1. Exact `COVERAGE_ID` match in `Rate_Table`.
2. Exact `COVERAGE_ID` match and exact `TYPE_CODE` where a specific rate type is required.
3. Exact `COVERAGE_ID` match in `PAAGERAT`.
4. Exact coverage-row existence in `PCOVR`.
5. Setup references in `PCOVRSGT` where the ID appears as either a coverage or segment.
6. Raw byte occurrences of the ID in the delivered files, so the proof is not dependent on CSV parsing only.

## Files Searched

- `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv`
- `plan_analysis/source_data/rates/PAAGERAT_AttainedAge_Rates_Extract_20260428.csv`
- `plan_analysis/source_data/coverage/PCOVR.csv`
- `plan_analysis/source_data/coverage/PCOVRSGT.csv`

## Conclusions

- `L01 10Y` `NP` in `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv`: MISSING (exact rows=0, raw byte ID occurrences=13001).
- `L01 10Y` `NP` in `plan_analysis/source_data/rates/PAAGERAT_AttainedAge_Rates_Extract_20260428.csv`: MISSING (exact rows=0, raw byte ID occurrences=924).
- `L01 10Y LT` `NP` in `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv`: MISSING (exact rows=0, raw byte ID occurrences=0).
- `L01 10Y LT` `NP` in `plan_analysis/source_data/rates/PAAGERAT_AttainedAge_Rates_Extract_20260428.csv`: MISSING (exact rows=0, raw byte ID occurrences=924).
- `L10 LP9595` `(any)` in `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv`: MISSING (exact rows=0, raw byte ID occurrences=0).
- `L10 LP9595` `(any)` in `plan_analysis/source_data/rates/PAAGERAT_AttainedAge_Rates_Extract_20260428.csv`: MISSING (exact rows=0, raw byte ID occurrences=0).

## Plain-English Explanation

The converter can only load rows that are present in the delivered extract files. `PCOVRSGT` can show that a product points to a segment, but the actual rate values still must exist in `Rate_Table` or `PAAGERAT`. For the listed client gaps, those rate-value rows are not present in the delivered extracts.

## Re-run Command

```powershell
python "Issue_Log_Items\Issue_Rates_Inheritance_Validation\client_l10_l01_followup\source_gap_proof\prove_missing_l01_l10_rows.py"
```
