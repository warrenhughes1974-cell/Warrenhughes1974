# QuikDate Schema Verification

**Inspected:** `Q:\CSO\CSO_Test_6_30_2025\quikdate.dbf`  
**Date:** 2026-07-18  
**Tool:** dbfread (read-only)

## Verified fields used by DG-QUIKDATE

| Business label | Physical name | Type | Length | Decimal | Notes |
|----------------|---------------|------|--------|---------|--------|
| PAC Bill date | **PACBILL** | D | 8 | 0 | Date |
| Direct Bill date | **DIRBILL** | D | 8 | 0 | Date |
| Reinsurance Bill date | **REINBILL** | D | 8 | 0 | Date; business label “Reinsurance Bill” |
| ACH File ID | **ACHFILEID** | N | 1 | 0 | Numeric; separate from ACHFILEID2 |
| Secondary ACH File ID | **ACHFILEID2** | C | 1 | 0 | Character; separate from ACHFILEID |
| ESCDATE (business) | **ESC_DATE** | D | 8 | 0 | Physical name is `ESC_DATE` (underscore), not `ESCDATE` |

## Other QuikDate fields observed (not governed by Item 5)

| Physical name | Type | Length | Decimal |
|---------------|------|--------|---------|
| PROCDATE | D | 8 | 0 |
| ANNDATE | D | 8 | 0 |
| PDUEDAYS | N | 2 | 0 |
| GRPBILL | D | 8 | 0 |
| APLBILL | D | 8 | 0 |
| LOANBILL | D | 8 | 0 |
| CPNBILL | D | 8 | 0 |
| VERSION | C | 10 | 0 |
| UPDATENUM | N | 5 | 0 |
| CCBILL | D | 8 | 0 |

## Mapping decisions

- PAC Bill → `PACBILL`
- Direct Bill → `DIRBILL`
- Reinsurance Bill → `REINBILL`
- ESCDATE business requirement → physical field `ESC_DATE`
- Empty DBF dates decode as Python `None` via dbfread and are treated as blank/empty for ESCDATE
