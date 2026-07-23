# Rate Audit Executive Summary

## Result

- Source-to-package parity: PASS
- Package-to-QLAdmin export parity: NOT RUN - export not provided
- Family controls: PASS

## Key Counts

- Package tables checked: 23
- Package table failures: 0
- QLAdmin table failures: pending export
- Failed controls: 0
- Pending controls: 1

## Blocking Findings

- None.

## Evidence Files

- `evidence/source_inventory.csv`
- `evidence/rate_table_inventory.csv`
- `evidence/canonical_expected_rows.csv`
- `evidence/canonical_expected_cells.csv`
- `evidence/package_table_summary.csv`
- `evidence/package_mismatches.csv`
- `evidence/qla_table_summary.csv` and `evidence/qla_mismatches.csv` when a QLAdmin export is provided
- `evidence/family_controls.csv`

## Acceptance Gate

Do not claim loaded QLAdmin rates are correct until package parity and QLAdmin export parity both pass, with any exceptions explicitly waived.
