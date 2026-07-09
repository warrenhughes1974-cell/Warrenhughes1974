# Rate Completeness Framework

Date: 2026-07-07

Goal: every LifePRO rate row available in the delivered source data must either be loaded to a confirmed QLAdmin rate table or documented with a plain-English reason why it cannot be loaded.

## Confirmed QLAdmin Destinations

| LifePRO type | Meaning | QLAdmin table | Current disposition |
|---|---|---|---|
| CV | Cash values | QuikCvs | Loaded |
| DB | Death benefits | QuikDbs | Loaded |
| DV | Dividends | QuikDvs | Loaded |
| NP | Net valuation premiums | QuikNps | Loaded |
| RV | Reserve factors | QuikTvs | Loaded |
| PR | Gross premiums | QuikGps | Loaded |
| NF | Nonforfeiture factors | QuikNff | Loaded in current package |

## Still Requires Disposition

| LifePRO type | Product Book meaning | Current disposition |
|---|---|---|
| NN | Non-Deduction Reserve Segment | Do not load until QLAdmin destination is confirmed |
| PN | Non-Ded Valuation Prem Segment | Do not load until QLAdmin destination is confirmed |
| TP/TX/SL/UF and other excluded types | Specialized tax/surrender/fee families | Must be mapped to a QLAdmin destination or documented as not supported |

## Required Status Per Plan/Rate Family

Each plan and rate family should be classified as one of:

- Loaded directly from `Rate_Table_Extract_20260427.csv`
- Loaded directly from `PAAGERAT_AttainedAge_Rates_Extract_20260428.csv`
- Loaded by inherited/shared segment resolution
- Present in source but not yet mapped to QLAdmin
- Screenshot only; missing from delivered extract
- No confirmed QLAdmin destination

## Immediate Known Source Gaps

- `L01 10Y` NP appears in LifePRO screenshots as a segment under `L01 10Y LT`, but no `L01 10Y` NP rows exist in the delivered `Rate_Table_Extract_20260427.csv`.
- `L10 LP9595` appears as a LifePRO segment reference under `L10 LP95`, but no `L10 LP9595` rate rows exist in the delivered rate extracts.

## Next Validation Question

For every plan: did every source rate we have make it into QLAdmin, or do we have a clearly documented reason why not?
