# DG-R-005 — Change Log

**Status:** Applied  
**Date:** 2026-07-18  
**Data region:** `Q:\CSO\CSO_Test_6_30_2026`  
**Backup:** `Q:\CSO\CSO_Test_6_30_2026_backup_DG-R-005_20260718`  
**Decision:** Option A — set `HCOMMIP` / `HRIGPKEY` to False for all non-MEDS QuikPlan rows  
**APP_VERSION:** unchanged (no QuikPlan conversion emit code changes)  
**Rule DG-QUIKPLAN-030:** unchanged

---

## Pre-flight (before write)

| Check | Result |
|-------|--------|
| QuikPlan rows | **142** |
| MEDS (`PLANTYPE` trim/casefold) | **0** |
| Non-MEDS | **142** (all blank PLANTYPE) |
| HCOMMIP decoded | all `None` (unreadable) |
| HRIGPKEY decoded | all `None` (unreadable) |
| HCOMMIP raw bytes | `?` × **141**, space × **1** |
| HRIGPKEY raw bytes | `?` × **141**, space × **1** |

Pre-flight gates passed; mutation proceeded.

---

## Backup

Created **before** write:

`Q:\CSO\CSO_Test_6_30_2026_backup_DG-R-005_20260718`

| File | Copied |
|------|--------|
| `quikplan.dbf` | Yes (pre-mutation) |
| `QUIKPLAN.ntx` | Yes |

Apply artifact: `_apply_counts.json` / script `_apply_dgr005.py`

---

## Mutation

| Surface | Action | Count |
|---------|--------|------:|
| CSO `quikplan.dbf` | Non-MEDS → `HCOMMIP=False`, `HRIGPKEY=False` | **142** |
| CSO `quikplan.dbf` | MEDS → both True | **0** |
| WPA `QuikPlan.dbf` | **Not touched** | **0** |

- Method: `dbf` package `dbf.write(record, HCOMMIP=False, HRIGPKEY=False)` per row  
- Post raw bytes: `HCOMMIP` = `F` × 142; `HRIGPKEY` = `F` × 142  
- Post decode: `False` / `False` on all 142 non-MEDS rows

---

## Conversion path

| Check | Result |
|-------|--------|
| Initial apply | Rulebook left blank; APP_VERSION unchanged |
| **Follow-up (user 2026-07-18)** | `Sync_Rulebook_quikplan.csv`: `HCOMMIP` and `HRIGPKEY` **Default_Value=`F`** with Transformation_Note (system default; preserve source True when mapped) |
| Principle note | `data_governance/docs/remediation/CONVERSION_SYSTEM_DEFAULTS.md` |
| `app.py` | Not modified (rulebook default sufficient for empty Source_Field) |

---

## Not changed

- DG-QUIKPLAN-030 rule catalog / implementation / tests  
- Other QuikPlan fields (including `MNAICLOB`, `PLANTYPE`, `BACTIVE`, `PLANVALOPT`)  
- QuikDate / QuikList / QuikChrt  
- `Q:\WPA\WPA_GABIE`
