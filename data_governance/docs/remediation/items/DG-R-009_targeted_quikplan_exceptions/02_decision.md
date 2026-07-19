# DG-R-009 — Business Decision

**Status:** DECIDED  
**Date:** 2026-07-18  
**Approved by:** User (chat — “Okay lets proceed”)

## Decision package

| Cluster | Decision |
|---------|----------|
| **SP (010)** | **Yes** — CSO set PAYYRS=1, PAYAGE=0 on six SPWL plans; conversion emit override for listed single-premium plans (also SEMI/QTRL/MTHD/MTHB=0) |
| **JPO** | **Defer** — 986JPO, 982JPO |
| **BASIS** | **Defer** — A60MIR, A96DAR until codes known |
| **1970PA** | **Hold/exception** — do not rename; residual on 003 |
| **RRULE WPA** | **Out of scope** — CSO already B |

## SP plans in scope

`1668SP`, `10L171`, `10L172`, `17MJPO`, `1L17SP`, `117JPO`

## Evidence

- WPA SPWL: PAYYRS=1, PAYAGE=0  
- `Data_Goverence.txt` single-premium transform note  
- Conversion ROUTE_PAY_* currently yields 0/0 when LifePRO has no D/A cease type  
