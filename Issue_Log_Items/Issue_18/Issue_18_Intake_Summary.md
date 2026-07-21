# Issue #18 — Intake Summary

**Issue:** #18 — Citizens FoxPro Rate Tables Request  
**Date:** 2026-07-11  
**Status:** OPEN — Awaiting source tables  
**Owner:** Warren  
**Assigned:** Tom · Debbie · Jelaine  
**Priority:** No Go until tables received  

---

## Business need

Citizens rates must be loaded into QLAdmin. We have partial sources (Access proposal tool, green-sheet PDFs) but are missing the **full FoxPro system tables** that hold plan-wide valuation and setup data.

## Request

Provide the **full tables** for:

1. Reserve file (~369K rows)
2. Plans (~301 rows)
3. CIFIANU1.DBF (~154K rows)

Confirm whether separate full tables exist for gross premium (beyond Access), dividends/PUA, COI, and loan values.

## Evidence tables exist

`CFIC_Rates/SourceData_11-18-2024/` — `Rate.cpy`, `Plan.cpy`, `AnnPrems,cpy` describe record counts and field layouts; only small samples were delivered.

## Out of scope for this issue

- Warren `app.py` code changes
- Green-sheet OCR (CFIC Issue #01)
- LifePRO conversion tables

## Success criteria

- Full Reserve, Plans, and CIFIANU1 tables received
- Inventory of any additional rate tables documented
- CFIC rate load tracker updated (`source_received` = Y)
