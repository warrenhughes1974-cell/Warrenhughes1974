# Issue #18 — Tracking Sheet

| Field | Value |
|-------|-------|
| Issue ID | 18 |
| Title | Citizens FoxPro Rate Tables Request |
| Status | **OPEN — Awaiting source tables** |
| Priority (Go-No Go) | **No Go** until full tables received |
| Issue Owner | Warren |
| Assigned | Tom · Debbie · Jelaine |
| Date Raised | 2026-07-11 |
| Date Resolved | — |

## Description

Request **full** Citizens FoxPro rate tables (not exports/samples) needed to load QLAdmin:

| Table | Records (per schema) | Covers |
|-------|---------------------|--------|
| **Reserve file** | ~369,145 | Cash value, terminal reserve, mean reserve, paid-up, ETI, net premium |
| **Plans** | ~301 | Plan master, loan interest rates (`IR1`–`IR8`), fees |
| **CIFIANU1.DBF** | ~153,993 | Annuity premiums |

**Also ask:** separate tables for gross premium (beyond Access), dividends/PUA, COI, loan values — if they exist.

## How we know these tables exist

November 2024 package `CFIC_Rates/SourceData_11-18-2024/` included structure files only:

- `Rate.cpy` — Reserve file layout (369,145 records; 10-row sample in `Rate.txt`)
- `Plan.cpy` — Plans layout (301 records; 9-row sample in `Plan.txt`)
- `AnnPrems,cpy` — points to `C:\CIFIVFP\CIFIANU1.DBF` (10-row sample in `AnnPrem.txt`)

## Already in hand (do not re-request)

- Access proposal tool gross premium — `CFIProposalMakerRev2.mdb` / `extracted/*.csv`
- Green-sheet nonforfeiture PDFs — `CFIC_Rates/CFIC_Cash_Values/`
- Plan crosswalk — `Citizens_Plan_Crosswak.xlsx`
- Rate requirements catalog — `Citizens_Plan_Rate_Requirements_Catalog.xlsx`

## Reserve file does NOT include

Gross premium, dividends, COI, or loan values — only valuation / nonforfeiture columns.

## Related

- CFIC rate load tracker: `CFIC_Rates/tracking/`
- CFIC Issue #01 (green-sheet extract): `CFIC_Rates/Issue_Log/CFIC_Issue_01/`
- Email subject: **Citizens rate tables needed for QLAdmin conversion**

## Stage log

| Date | Stage | Notes |
|------|-------|-------|
| 2026-07-11 | Opened | Issue logged; email to Tom / Debbie / Jelaine pending or sent |
