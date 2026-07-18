# QLAdmin Data Governance

Incremental framework for QLAdmin table governance checks against **any** data region (folder of QLAdmin DBF files).

## Current scope

| Item | ID | Rules |
|------|----|--------|
| 1 — QuikComp Company Code Integrity | `DG-QUIKCOMP` | 001, 002, 003 |
| 2 — QuikMstr Policy Number Integrity | `DG-QUIKMSTR` | 001 |
| 3 — Accounting Company and Account Integrity | `DG-ACCOUNTING` | DG-QUIKACTG-001, 002 |
| 4 — QuikList Group Billing Integrity | `DG-QUIKLIST` | 001–009 |
| 5 — QuikDate Processing Date Integrity | `DG-QUIKDATE` | 001–006 |
| 6 — Plan Value Reference Integrity | `DG-PLANVALUES` | 001–008 |

## Run against any data region

```bash
# All rules
python -m data_governance run --input "D:\QLAdmin\ClientA\Data" --output "D:\Governance\ClientA"

# One governance item
python -m data_governance run --input "D:\QLAdmin\ClientA\Data" --output "D:\Governance\ClientA" --item DG-QUIKCOMP

# One rule
python -m data_governance run --input "D:\QLAdmin\ClientA\Data" --output "D:\Governance\ClientA" --rule DG-QUIKMSTR-001

# Accounting item / rules
python -m data_governance run --input "D:\QLAdmin\ClientA\Data" --output "D:\Governance\ClientA" --item DG-ACCOUNTING
python -m data_governance run --input "D:\QLAdmin\ClientA\Data" --output "D:\Governance\ClientA" --rule DG-QUIKACTG-001
python -m data_governance run --input "D:\QLAdmin\ClientA\Data" --output "D:\Governance\ClientA" --rule DG-QUIKACTG-002

# QuikList group billing item / rules
python -m data_governance run --input "D:\QLAdmin\ClientA\Data" --output "D:\Governance\ClientA" --item DG-QUIKLIST
python -m data_governance run --input "D:\QLAdmin\ClientA\Data" --output "D:\Governance\ClientA" --rule DG-QUIKLIST-001

# QuikDate processing date item / rules
python -m data_governance run --input "D:\QLAdmin\ClientA\Data" --output "D:\Governance\ClientA" --item DG-QUIKDATE
python -m data_governance run --input "D:\QLAdmin\ClientA\Data" --output "D:\Governance\ClientA" --rule DG-QUIKDATE-001

# Plan-value reference integrity item / rules
python -m data_governance run --input "D:\QLAdmin\ClientA\Data" --output "D:\Governance\ClientA" --item DG-PLANVALUES
python -m data_governance run --input "D:\QLAdmin\ClientA\Data" --output "D:\Governance\ClientA" --rule DG-PLANVALUES-001
```

Each run writes an isolated folder with two user-facing reports:

```text
<output>/
  <run_id>/
    1_What_Was_Checked.html            (business summary — open this first)
    2_Items_Needing_Attention.csv      (data problems + incomplete checks only)
    internal/                          (optional technical files for support)
      data_governance_results.csv
      data_governance_findings.csv
      data_governance_summary.csv
      data_governance_report.md
      data_governance_validation_guide.md
      data_governance_validation_manifest.json
      data_governance_run.json
      data_governance.log
```

Source DBF files are opened **read-only** and are never modified.

## Architecture

| Layer | Package |
|-------|---------|
| Table resolution | `data_access/table_resolver.py` |
| Region path validation | `data_access/region_path.py` |
| Data load (read-only) | `data_access/table_loader.py` |
| Rule catalog / registry | `catalog/` |
| Rules | `rules/<area>/` |
| Execution | `execution/runner.py` |
| Reports | `reporting/` |

## Open / future items

See `docs/Open_Items.md` (includes future **QuikChrt Chart of Accounts Integrity** — not implemented).

## Tests

```bash
python -m pytest data_governance/tests -q
```

## After each new governance item (production-style run)

Whenever a new governance item is implemented, run the **full suite** against the current production-style data region and open the results CSV:

```bash
python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2025" --output "Q:\CSO\Governance_Reports"
```

- Reports go under `Q:\CSO\Governance_Reports\<run_id>\`
- Primary Excel file: `data_governance_results.csv`
- Source DBFs are read-only and must not be modified
- Do this in addition to unit tests — not instead of them
