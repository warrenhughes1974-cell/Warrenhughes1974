# DG-R-010 — Business Decision

**Status:** DECIDED  
**Date:** 2026-07-19  
**Approved by:** User (chat)

## Decision

**Option R1 — Revise DG-QUIKPLAN-026:** require QuikDbs and QuikPlDb only when `VARDB` is **1, 2, or 3**. Skip when VARDB is **0** (level / INITVAL) or **4** (not on file).

- **Do not** create or rewrite QuikDbs / QuikPlDb rows (CSO or WPA).
- Align catalog, rule implementation, tests, report wording, and `Data_Goverence.txt` with QLAdmin Var DB semantics.
- Leave Sync_Rulebook `VARDB` default `0` unchanged (empty-source default for level).

## Evidence

- QLAdmin Help: VARDB=0 = level (Initial Val/Unit); 1/2/3 = varying schedules; 4 = not on file.
- CSO: all 133 findings were VARDB=0; every VARDB 1/2/3 plan already had both tables.
- WPA: almost all VARDB=0 with almost no QuikDbs/QuikPlDb — production pattern matches CSO “failures.”

## Out of scope

- Mass insert of death-benefit rate tables  
- Changing VARDB codes on plans  
- Revising DG-QUIKPLAN-025 (VARGP / QuikGps) — separate item if needed  
