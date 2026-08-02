# Issue #135 — Claims UAT DBF Rerun Summary

- Generated: `20260802T225239Z`
- Generator result: **SUCCESS / ALIGNMENT PASS**
- Grok second-pass: **PASS**
- Production code changed: **No**
- Output CSVs modified: **Yes** (restored verified TV package to Output root)

## Source CSV

Fresh UAT DBFs generated from verified Output root quikclms/quikclmp (restored from Test_Validation 6044/5495 package before generate).

- Output root quikclms rows: **6044**
- Output root quikclmp rows: **5495**
- Test_Validation rows: 6044 / 5495

## DBF package

- Dir: `C:\Users\warren\Documents\GitHub\Warrenhughes1974\QLA_Migration\Staging\claims_uat_dbf`
- QUIKCLMS rows: **6044**
- QUIKCLMP rows: **5495**
- Alignment: **PASS**
- Archive: `C:\Users\warren\Documents\GitHub\Warrenhughes1974\QLA_Migration\Archive\claims_uat_dbf_pre_mpolicy_c11_20260802T175033Z`

## Policy 9011156655C verification

- DBF MPOLICY key: `9011156655C` (C(11) preserved; matches QUIKMSTR)
- Header MPAID/MFACE/NETDB/MINTAMT: 5145.67 / 5000.0 / 5000.0 / 0.0
- Payees: **4**; sum **5145.67**

- MSEQ 1: LINVILLE L BRASWELL = 1286.42
- MSEQ 2: CHERI ROSE BRASWELL = 1286.41
- MSEQ 3: DANIEL L BRASWELL JR = 1286.42
- MSEQ 4: ROBERT C BRASWELL = 1286.42

## Warren copy instructions

Copy these into QLAdmin from `QLA_Migration/Staging/claims_uat_dbf/` (keep QUIKCLMS DBF+DBT together):

- `QUIKCLMS.DBF`
- `QUIKCLMS.DBT`
- `QUIKCLMP.DBF`

Phase19 aliases (same bytes): `QUIKCLMS_PHASE19_UAT.DBF` + `.DBT`, `QUIKCLMP_PHASE19_UAT.DBF`.

