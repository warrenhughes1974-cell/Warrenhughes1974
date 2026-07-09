# Master Rate Completeness Summary

Generated from delivered source extracts and current in-memory rate pipeline.

## High-Level Counts

- Source grouped rows reviewed: 360
- Delivered source rate rows reviewed: 1,153,408
- Actionable source rows reviewed, excluding NN/PN: 923,914
- Source rows in loaded actionable groups: 873,311
- Source rows in actionable gap/review groups: 50,603
- NN/PN source rows separated from actionable load list: 229,494
- Current pipeline blockers: 1

## Status Counts

- Loaded directly: 175 groups / 856,845 source rows
- Loaded directly from PAAGERAT segment resolution: 85 groups / 16,466 source rows
- Present in source but not emitted: 8 groups / 1,553 source rows
- Present in source but not yet mapped: 61 groups / 49,050 source rows
- Separated - no confirmed QLAdmin load target: 31 groups / 229,494 source rows

## Rate Type Disposition

- BP / Present in source but not emitted: 1,336 source rows
- CV / Loaded directly: 237,300 source rows
- CV / Present in source but not yet mapped: 1,435 source rows
- DB / Loaded directly: 12,885 source rows
- DB / Present in source but not yet mapped: 628 source rows
- DV / Loaded directly: 37,030 source rows
- NC / Present in source but not yet mapped: 690 source rows
- NF / Loaded directly: 82,445 source rows
- NF / Loaded directly from PAAGERAT segment resolution: 508 source rows
- NN / Separated - no confirmed QLAdmin load target: 118,642 source rows
- NP / Loaded directly: 244,789 source rows
- NP / Present in source but not yet mapped: 950 source rows
- PN / Separated - no confirmed QLAdmin load target: 110,852 source rows
- PR / Loaded directly: 10,134 source rows
- PR / Loaded directly from PAAGERAT segment resolution: 14,958 source rows
- PU / Present in source but not yet mapped: 1,755 source rows
- RD / Present in source but not yet mapped: 10 source rows
- RV / Loaded directly: 232,262 source rows
- RV / Present in source but not yet mapped: 820 source rows
- SL / Present in source but not yet mapped: 24 source rows
- TP / Present in source but not yet mapped: 22,840 source rows
- TX / Present in source but not yet mapped: 19,780 source rows
- U5 / Loaded directly from PAAGERAT segment resolution: 200 source rows
- U5 / Present in source but not emitted: 217 source rows
- U6 / Loaded directly from PAAGERAT segment resolution: 800 source rows
- UF / Present in source but not yet mapped: 1 source rows
- YP / Present in source but not yet mapped: 117 source rows

## Known Screenshot-Only Source Gaps

- L01 10Y NP: Client screenshot shows L01 10Y NP under L01 10Y LT, but the delivered Rate_Table extract has no L01 10Y NP rows.
- L10 LP9595 NP/RV: LifePRO setup references L10 LP9595 under L10 LP95, but neither delivered rate extract contains L10 LP9595 rows.

## Suggested Next Moves

1. Resolve the largest mapped-but-not-loaded or unmapped source groups in the inventory CSV.
2. Add inherited/shared segment rules for confirmed QLAdmin destinations beyond the first-pass manifest, starting with PR and NF.
3. Ask CSO for missing extract rows where screenshots show rates but the delivered extracts do not contain them.
4. Keep NN and PN separated from the actionable load list until their QLAdmin destination is confirmed.
