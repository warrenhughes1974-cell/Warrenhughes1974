# DG-R-003 — Business Decision

**Status:** DECIDED  
**Date:** 2026-07-18  
**Approved by:** User (chat)

## Decision

### Part 1 — Live database (Option A)

On **`Q:\CSO\CSO_Test_6_30_2026`** (confirmed correct folder; `6_30_2025` was a misnamed path):

| Field | Set to |
|-------|--------|
| `PACBILL` | `2026-06-30` |
| `DIRBILL` | `2026-06-30` |
| `REINBILL` | `2026-06-30` |

Do **not** change ACHFILEID, ACHFILEID2, ESC_DATE, PROCDATE, or other *BILL fields under this item.

Backup before write: `Q:\CSO\CSO_Test_6_30_2026_backup_DG-R-003_20260718` (at least `QUIKDATE.dbf` + related index if any).

### Part 2 — Conversion program must always follow DG-R-003

**Requirement:** Conversion must always set QuikDate bill dates so they satisfy DG-QUIKDATE-001/002/003 (and keep ACH defaults aligned with 004/005/006 when emitting QuikDate).

**Current state:** `QLA_Migration/QLAdmin_Converted_Tables.txt` lists quikdate under “Group / System Control — not needed”; there is **no** QuikDate emit in `qla_core` / `app.py` today. Live QLA regions keep stale dates unless patched.

**Approved approach (surgical):**

1. Add a small QuikDate emit (or apply-defaults step) that writes `quikdate.csv` (QLA date format) with:
   - `PACBILL` = `DIRBILL` = `REINBILL` = **prior month-end of the conversion run date** (same definition as `data_governance.data_access.normalization.prior_month_end`)
   - `ACHFILEID` = `0`
   - `ACHFILEID2` = `A`
   - `ESC_DATE` blank
2. Prefer a shared helper in `qla_core` (or reuse governance `prior_month_end` if import is clean) — do **not** duplicate divergent date logic.
3. Wire into conversion surgically; bump `APP_VERSION` in **both** root `app.py` and `QLA_Migration/app.py`.
4. Do **not** rewrite unrelated converters; do not auto-patch the live Q: DBF from conversion unless an existing pattern already writes to the governance data folder (CSV Output is the default).

## Out of scope

- Refreshing GRPBILL / APLBILL / LOANBILL / CCBILL  
- Changing governance rule definitions  
- Bulk plan setup items (DG-R-004+)

## Risk acceptance

- `2026-06-30` is correct for July 2026 governance runs; conversion will use **dynamic** prior-month-end of each run date going forward.  
- Emitting QuikDate may be new for this project’s Output package — document in change log / RUN_GUIDE note if Output now includes `quikdate.csv`.
