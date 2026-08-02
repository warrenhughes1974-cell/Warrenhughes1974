# Issue #135 — Claims DBF MPOLICY C(11) Correction

**Status:** Ready for Validation (not Closed)  
**Result:** PASS  
**Date:** 2026-08-02

## Defect

QLAdmin showed blank claim/payee details for `9011156655C` because `QUIKCLMS` / `QUIKCLMP` used `MPOLICY C(10)`, truncating the trailing `C`. `QUIKMSTR` already uses `MPOLICY C(11)`.

## Fix

Surgical claims-DBF layout correction only:

- `claims_analysis/config/prototype_dbf_generation_rules.json` — `MPOLICY` length 10 → 11 on both layouts
- `docs/claims_conversion_reference/quikclms_quikclmp` — same length correction
- Focused Issue #135 validators/copy scripts no longer treat truncation as expected

No converter/`app.py` changes. No full conversion. Issue remains open.

## Archives (pre-overwrite)

- Staging: `QLA_Migration/Archive/claims_uat_dbf_pre_mpolicy_c11_20260802T175033Z`
- Q destination: `QLA_Migration/Archive/q_claims_pre_mpolicy_c11_20260802T175033Z`

## Regenerated package

| Artifact | Rows | MPOLICY |
|---|---:|---|
| Output quikclms.csv | 6044 | `9011156655C` preserved |
| Output quikclmp.csv | 5495 | `9011156655C` preserved |
| Staging/Q QUIKCLMS.DBF | 6044 | `C(11)` |
| Staging/Q QUIKCLMP.DBF | 5495 | `C(11)` |

Golden policy `9011156655C`: MPAID=5145.67, MFACE=5000, NETDB=5000, MINTAMT=0; 4 payees sum 5145.67. All MINTAMT=0.

Copied to `Q:\CSO\CSO_Test_6_30_2026`: `QUIKCLMS.DBF`, `QUIKCLMS.DBT`, `QUIKCLMP.DBF` (no `QUIKCLMP.DBT`).

## Indexes (manual)

Close QLAdmin if open, reopen on `Q:\CSO\CSO_Test_6_30_2026`, then rebuild claims indexes:

- `QUIKCLMS.ntx`
- `QUIKCLMP.ntx`
- `QUIKCLMB.ntx` / `QUIKCLMBI.ntx` if used by the claims browser

Then reopen/refresh policy `9011156655C` — claim and payee details should appear.
