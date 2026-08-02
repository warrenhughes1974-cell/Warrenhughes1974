# Issue #135 — Rebuild & Deploy Summary (2026-08-02)

**Status:** Ready for Validation (not Closed)  
**Engine:** v58.60  
**Model:** Cursor Grok 4.5  
**Result:** PASS

## Rebuild path

Output root was stale at **5594/5366**. Deterministic restore used the verified `Output/Test_Validation` package (**6044/5495**, quikclmp SHA `5dd6d9da57134da17a81382c58e8cdb2fd3f161a8c99475d780104b778bff0fc`), then generated fresh UAT DBFs from the restored Output CSVs.

## Final counts

| Artifact | Rows |
|---|---:|
| quikclms.csv (Output + TV) | 6044 |
| quikclmp.csv (Output + TV) | 5495 |
| QUIKCLMS.DBF | 6044 |
| QUIKCLMP.DBF | 5495 |

Invariants: MINTAMT nonzero=0; Option-3=43; DERIVED_HIGH=142; CSO header-only marker=308; original 9 HOLDs absent; zero-payee SAFE=137 / HOLD=3.

## Destination

`Q:\CSO\CSO_Test_6_30_2026\QUIKCLMS.DBF`  
`Q:\CSO\CSO_Test_6_30_2026\QUIKCLMS.DBT`  
`Q:\CSO\CSO_Test_6_30_2026\QUIKCLMP.DBF`  

No `QUIKCLMP.DBT`. Destination row/payee verify PASS for 9011156655C (4 payees, sum 5145.67).

## Follow-up: MPOLICY C(11) schema correction (same day)

Blank claim/payee UI was caused by claims DBF `MPOLICY C(10)` truncating `9011156655C`. Layout corrected to `C(11)` for QUIKCLMS/QUIKCLMP only; DBFs regenerated and recopied to Q. See `issue135_mpolicy_c11_correction_summary.md`. **Issue remains open (not Closed).** User must rebuild claims indexes and reopen/refresh the policy in QLAdmin.

## Remaining holds (block Closure)

Nine HOLD_INCOMPLETE_SOURCE policies remain unemitted. Three residual zero-payee HOLD_INCOMPLETE policies remain without safe PRELSA identity.
