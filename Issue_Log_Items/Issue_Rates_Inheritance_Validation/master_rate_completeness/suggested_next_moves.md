# Suggested Next Moves After Master Rate Inventory

Date: 2026-07-07

## Current Result

The current inventory reviewed 1,153,408 delivered source rate rows across `Rate_Table_Extract_20260427.csv` and `PAAGERAT_AttainedAge_Rates_Extract_20260428.csv`.

- Loaded groups: 873,311 source rows
- Gap/review groups: 280,097 source rows
- `NF` now loads to `QuikNff`
- Known screenshot-only source gaps remain for `L01 10Y` NP and `L10 LP9595` NP/RV

## Recommended Priority 1: Document NN/PN as Not Currently Loadable

The largest remaining source rows are `NN` and `PN`:

- `NN`: 118,642 rows
- `PN`: 110,852 rows

Product Book meanings:

- `NN` = Non-Deduction Reserve Segment
- `PN` = Non-Ded Valuation Prem Segment

These are not `QuikNff`. Do not force them into `QuikNff`, `QuikNps`, or `QuikTvs` unless QLAdmin confirms the destination. For client communication, these should be marked:

> Present in LifePRO source, but no confirmed QLAdmin destination has been identified yet.

## Recommended Priority 2: Build Inherited/Shared Rate Completeness for Confirmed Tables

Now that direct `NF` is loaded, the next real conversion gap is shared/inherited rate ownership beyond the first-pass manifest.

Target confirmed tables:

- `CV -> QuikCvs`
- `DB -> QuikDbs`
- `DV -> QuikDvs`
- `NP -> QuikNps`
- `RV -> QuikTvs`
- `PR -> QuikGps`
- `NF -> QuikNff`

Build a PCOVRSGT-driven candidate list for any issuing coverage that has no direct rows for one of these confirmed types but points to a segment that does have rows.

## Recommended Priority 3: Resolve PAAGERAT Review Rows

PAAGERAT rows still needing review include:

- `BP`: 1,336 rows present but not fully emitted because current BP loading is allowlist-gated
- `NC`: 690 rows, no confirmed destination in this inventory
- PAAGERAT `CV`, `DB`, `NP`, `RV`: present but not mapped through the PAAGERAT scalar loader path
- `PU`, `RD`, `YP`: present but destination not confirmed

Do not load these blindly. The next step is to confirm QLAdmin destination and table shape for each.

## Recommended Priority 4: Ask CSO for Missing Extract Rows

Ask CSO for source extract rows, not screenshots, for:

- `L01 10Y` `NP` rows shown in LifePRO screenshots under `L01 10Y LT`
- `L10 LP9595` `NP/RV` rows referenced under `L10 LP95`

Plain-English wording:

> We can see the product setup pointing to these rates, and we can see screenshots showing some of them, but the actual rows are not in the delivered rate extract files. We need the LifePRO rate extract rows for those segment IDs to load them.

## Recommended Priority 5: Make the Inventory a Regression Gate

After each rate-loader change, rerun:

```powershell
python "Issue_Log_Items\Issue_Rates_Inheritance_Validation\master_rate_completeness\build_rate_completeness_inventory.py"
```

The gap row count should go down only when:

- rows move into a confirmed QLAdmin table, or
- rows are documented as not loadable because no QLAdmin destination exists, or
- CSO confirms the source data was not delivered.
