# DG-R-011 — Business Decision

**Status:** DECIDED  
**Date:** 2026-07-19  
**Approved by:** User (chat)

## Decision

**Option R1 — Revise DG-PLANVALUES-001 and DG-PLANVALUES-002:** skip blank/null MORT and ETIMORT; validate QuikQxs reference only when the value is populated.

- **Do not** rewrite QuikPlCv / QuikPlTv / QuikQxs (CSO or WPA).
- Align catalog, rule implementation, tests, report wording, and `Data_Goverence.txt` with “populated value must exist in setup.”
- Leave conversion mortality crosswalk blank-safe behavior unchanged.
- **Do not** change DG-PLANVALUES-003 (blank PLAN still fails).

## Evidence

- CSO: 0 missing QuikQxs codes; 390 findings were 100% BLANK_VALUE.
- WPA: same — blanks only (16 Cv rows); all populated codes resolve.
- Rule purpose already said “populated”; failure conditions over-enforced.
- Conversion: blank MORT/ETIMORT stays blank.

## Out of scope

- Filling blanks from crosswalk defaults  
- Deleting blank Cv/Tv rows  
- Revising PLAN reference rule 003  
