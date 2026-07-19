# DG-R-007 — Business Decision

**Status:** DECIDED  
**Date:** 2026-07-18  
**Approved by:** User (chat)

## Decision

**Option R1 — Revise DG-QUIKPLAN-008:** drop the requirement that `LOAGE` must equal 0; keep readable numerics and `LOAGE < HIAGE`.

- **Do not** rewrite QuikPlan LOAGE/HIAGE data (CSO or WPA).
- Align catalog, rule implementation, tests, report wording, schema notes, and `Data_Goverence.txt` with QLAdmin Issue Ages (lowest/highest issue age).
- Conversion: leave `MIN_ISSUE_AGE` → `LOAGE` Default=`0` as empty-source default only; do not force 0 over source.

## Evidence

- QLAdmin Help: Issue Ages = lowest and highest age for which the plan may be issued.
- WPA: 375/1848 plans with LOAGE ≠ 0; CSO: 55/142 — intentional product floors.
- Sync_Rulebook already maps LifePRO min issue age into LOAGE.

## Out of scope

- Mass UPDATE of QuikPlan LOAGE  
- Retiring the entire 008 rule  
- Blank-plan 0/0 cleanup (remains a valid LOAGE &lt; HIAGE fail; overlaps DG-R-008)
