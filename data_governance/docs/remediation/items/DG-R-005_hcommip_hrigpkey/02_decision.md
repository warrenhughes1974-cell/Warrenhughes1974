# DG-R-005 — Business Decision

**Status:** DECIDED  
**Date:** 2026-07-18  
**Approved by:** User (chat)

## Decision

**Option A — Fix QuikPlan data on CSO:** set `HCOMMIP` and `HRIGPKEY` to **False** (`.F.`) for all non-MEDS plans.

- Confirmed: matches DG-QUIKPLAN-030 and `Data_Goverence.txt` (“MEDS → YES; otherwise F”).
- CSO today: 0 MEDS, 142 blank PLANTYPE → all 142 get both flags False.
- **Do not** modify WPA production until separately inventoriable/approved.
- Conversion: set Sync_Rulebook defaults `HCOMMIP=F` and `HRIGPKEY=F` (system default). Do **not** blind-force over source when a real True/T/Y/1 is mapped later; empty → F. Documented in `data_governance/docs/remediation/CONVERSION_SYSTEM_DEFAULTS.md`.

## Scope

| Target | Action |
|--------|--------|
| `Q:\CSO\CSO_Test_6_30_2026\quikplan.dbf` | Set HCOMMIP/HRIGPKEY = False where PLANTYPE is not MEDS |
| `Q:\WPA\WPA_GABIE` | Out of scope this item |
| Governance rule 030 | No change |

## Backup

`Q:\CSO\CSO_Test_6_30_2026_backup_DG-R-005_20260718` (QuikPlan.* before write)

## Risk acceptance

- Replaces unreadable `?` / space logical bytes with explicit `.F.`  
- Aligns CSO with written business rule; production left untouched for now.
