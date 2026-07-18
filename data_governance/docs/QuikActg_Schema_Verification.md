# QuikActg / QuikChrt schema verification

**Inspected:** `Q:\CSO\CSO_Test_6_30_2025\quikactg.dbf`, `docs\QuikActg.dbf`, `QUIKCHRT.DBF`, `QUIKCOMP.DBF`  
**Date:** 2026-07-18

## QuikActg (Account Number Assignments / plan-event config)

| Physical field | Type | Length | Role |
|----------------|------|--------|------|
| **MCOMP** | C | 1 | Company code |
| **MPLAN** | C | 6 | Plan code (row companion to company) |
| MACCTREC, MACCTPAY, MPREM1ST, … (many) | C | 10 | Event account *assignment values* (not the row key) |

**Finding:** QuikActg has **no** single `MACCOUNT` / account-number key column.  
The verified composite key that identifies a QuikActg assignment **record** is:

```text
MCOMP + MPLAN
```

## QuikChrt (Chart of Accounts) — related table

| Physical field | Type | Length | Role |
|----------------|------|--------|------|
| **MCOMP** | C | 1 | Company code |
| **MACCOUNT** | C | 10 | Account number |
| MDESCR | C | 30 | Description |

`MCOMP + MACCOUNT` matches the business examples for “company + account number” uniqueness.  
**Not used** by DG-QUIKACTG-001 / 002.  

Tracked as a **separate future item** (not part of DG-ACCOUNTING):  
`docs/Open_Items.md` → **Future Data Governance Item — QuikChrt Chart of Accounts Integrity** (proposed `DG-QUIKCHRT-001`).

## QuikComp

| Physical field | Type | Length |
|----------------|------|--------|
| **MCOMP** | C | 1 |

## Implementation choice for DG-QUIKACTG-001

Use verified QuikActg fields **MCOMP + MPLAN** as the composite uniqueness key.  
Business-facing labels may say “plan code (MPLAN)” where the prompt said “account number,” because no QuikActg account-number key field exists.
