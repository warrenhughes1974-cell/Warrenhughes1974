# DG-R-003 — Change Log

**Status:** Applied  
**Date:** 2026-07-18  
**Data region:** `Q:\CSO\CSO_Test_6_30_2026`  
**Backup:** `Q:\CSO\CSO_Test_6_30_2026_backup_DG-R-003_20260718`  
**APP_VERSION:** `v58.07` (root `app.py` + `QLA_Migration/app.py`)  
**Decision:** Option A live patch + conversion emit of QuikDate governance defaults

---

## Part 1 — Live QuikDate patch

### Pre-flight

| Check | Result |
|-------|--------|
| Path exists | Yes — `Q:\CSO\CSO_Test_6_30_2026` |
| QuikDate row count | **1** (gate passed) |
| PACBILL before | 2004-12-05 |
| DIRBILL before | 2004-12-19 |
| REINBILL before | null |
| ACHFILEID / ACHFILEID2 / ESC_DATE | 0 / A / blank (already compliant) |
| PROCDATE | 2026-07-18 (unchanged by design) |

### Backup

Created `Q:\CSO\CSO_Test_6_30_2026_backup_DG-R-003_20260718` with:

- `QUIKDATE.dbf` (pre-patch: PAC 2004-12-05, DIR 2004-12-19, REIN null)

Backup completed **before** mutation. Apply artifact: `_apply_counts.json`.

### Mutation (1 row, 3 fields)

| Field | From | To |
|-------|------|-----|
| PACBILL | 2004-12-05 | **2026-06-30** |
| DIRBILL | 2004-12-19 | **2026-06-30** |
| REINBILL | null | **2026-06-30** |

- Method: `dbf` package `dbf.write` on single record  
- Rows after: **1**  
- Unchanged: ACHFILEID, ACHFILEID2, ESC_DATE, PROCDATE, GRPBILL, APLBILL, LOANBILL, CCBILL, VERSION, UPDATENUM, other fields

Script: `_apply_dgr003.py`

---

## Part 2 — Conversion emit (surgical)

### New module

`qla_core/quikdate_converter.py`

- Imports `prior_month_end` from `data_governance.data_access.normalization` (no divergent formula)
- Builds one-row CSV in live QUIKDATE field order
- Sets PACBILL = DIRBILL = REINBILL = prior month-end of conversion run date (QLA format `YYYYMMDD`)
- Sets ACHFILEID = `0`, ACHFILEID2 = `A`, ESC_DATE blank
- Other schema fields blank (no invented business values)

### App wiring

Batch finale in **both** `app.py` and `QLA_Migration/app.py` (after Issue #21G staging, before claims/governance):

- Calls `emit_quikdate_csv(output_dir)` when `is_batch`
- Writes `quikdate.csv` to the conversion Output folder

### Other updates

| File | Change |
|------|--------|
| `QLA_Migration/QLAdmin_Converted_Tables.txt` | Note that quikdate is emitted on batch for DG-R-003 |
| `data_governance/tests/test_quikdate_converter_emit.py` | Unit test for shared prior-month-end + emit |
| APP_VERSION | `v58.06` → **`v58.07`** in both app.py copies |

### Not changed

- Unrelated converters (quikmstr, quikplan, quikmemo, etc.)
- Governance rule definitions
- GRPBILL / APLBILL / LOANBILL / CCBILL on live DBF

---

## Row counts summary

| Surface | Rows / fields |
|---------|----------------|
| Live QuikDate rows | 1 → 1 |
| Live fields updated | 3 (PAC/DIR/REIN) |
| Conversion emit rows | 1 (per batch) |
| Backup files | 1 (`QUIKDATE.dbf`) |

---

## How to verify conversion emit

```bash
python -c "from datetime import date; from qla_core.quikdate_converter import emit_quikdate_csv; print(emit_quikdate_csv(r'QLA_Migration/Output', date(2026,7,18)))"
python -m pytest data_governance/tests/test_quikdate_converter_emit.py -q
```

Or run a full batch conversion and confirm `QLA_Migration/Output/quikdate.csv` has PAC/DIR/REIN = prior month-end.
