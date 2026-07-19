# Baseline Findings Snapshot

**Source:** User-pasted governance attention CSV (2026-07-18 session).  
**Note:** Exact data-region path not yet confirmed. Counts below are from the pasted report (problem + warning rows).

## By remediation item

| Item | Rule IDs | Approx. problem rows in paste | Notes |
|------|----------|-------------------------------|-------|
| DG-R-001 | DG-QUIKLIST-002, DG-QUIKPLAN-032 | LIST: 3 groups (GTEST01→V, TERMG→G, TEST1→G); PLAN Group Billing: G×2, V×1; QuikChrt: many G + many V | Company codes absent from QuikComp |
| DG-R-002 | DG-QUIKLIST-004/005/006/008/009 | Defaults on GTEST01, TERMG, TEST1 | Overlaps groups with 001 |
| DG-R-003 | DG-QUIKDATE-001/002/003 | 3 (PAC/DIR/REIN) | Required date in report: 2026-06-30 |
| DG-R-004 | DG-QUIKPLAN-024 | Nearly all plans (`MNAICLOB=NAPLAN`) | Mass default |
| DG-R-005 | DG-QUIKPLAN-030 | Nearly all plans (`/` unreadable logicals) | Mass logical rewrite |
| DG-R-006 | DG-QUIKPLAN-022 | Large closed-book set | PLANVALOPT on when inactive |
| DG-R-007 | DG-QUIKPLAN-008 | Many plans | LOAGE Age-1 ≠ 0 |
| DG-R-008 | DG-QUIKPLAN-001/002 + PLANVALUES-003 (+ cascade) | Blank PLAN + orphan value rows | Cleanup / delete candidates |
| DG-R-009 | DG-018, DG-010, DG-003, DG-005 | Small targeted set | RRULE, pay years, 1970PA, annuity BASIS |
| DG-R-010 | DG-QUIKPLAN-026 | Many plans | Missing QuikDbs / QuikPlDb |
| DG-R-011 | DG-PLANVALUES-001/002 | Large Cash + Tabular set | MORT/ETIMORT vs QuikQxs |
| DG-R-012 | DG-QUIKPLAN-027/028 | Many warnings | Advisory only |

## Company codes observed in baseline paste

| Code | Where referenced | In Company Setup (QuikComp)? |
|------|------------------|------------------------------|
| G | QuikList (TERMG, TEST1), QuikChrt (many), Plan Setup Group Billing | No — fails 002/032 |
| V | QuikList (GTEST01), QuikChrt (many), Plan Setup Group Billing | No — fails 002/032 |
| C | Conversion default / Loyal American pattern in repo | Expected valid if present in QuikComp (confirm on live region) |
