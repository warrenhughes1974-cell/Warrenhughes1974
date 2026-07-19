# DG-R-003 — Examine: QuikDate prior-month-end billing dates

**Status:** DECIDED (Option A + conversion emit)  
**Date:** 2026-07-18  
**Rule IDs (in scope):** DG-QUIKDATE-001, DG-QUIKDATE-002, DG-QUIKDATE-003  
**Related (already compliant — out of write scope unless you expand):** DG-QUIKDATE-004/005/006  
**Primary table:** QuikDate (`QUIKDATE.dbf`)  
**Data region (live):** `Q:\CSO\CSO_Test_6_30_2026` (confirmed)  

---

## 0. Path note (important)

The folder used for DG-R-001 was `Q:\CSO\CSO_Test_6_30_2025`. That path **no longer exists**.

Current matching region appears to be **`Q:\CSO\CSO_Test_6_30_2026`**:

- `quiklist.dbf` has **0** rows (consistent with DG-R-001 deletes)
- `QUIKCHRT.DBF` / `quiklist.dbf` timestamps align with DG-R-001 apply time
- Prior DG-R-001 backup folder is **not** present under `Q:\CSO`

Confirm this is the intended data region before Implement.

---

## 1. What the rules require

| Rule | Field | Required |
|------|--------|----------|
| DG-QUIKDATE-001 | `PACBILL` | Last calendar day of the month **before** the governance run date |
| DG-QUIKDATE-002 | `DIRBILL` | Same prior-month-end |
| DG-QUIKDATE-003 | `REINBILL` | Same prior-month-end |

**Dynamic value:** For a run dated **2026-07-18** (today / baseline report), prior-month-end = **`2026-06-30`**.

Also governed but **already passing** on live data (do not change unless you expand scope):

| Rule | Field | Required | Live value |
|------|--------|----------|------------|
| DG-QUIKDATE-004 | `ACHFILEID` | `0` | `0` |
| DG-QUIKDATE-005 | `ACHFILEID2` | `A` | `A` |
| DG-QUIKDATE-006 | `ESC_DATE` | blank | `None` (blank) |

Authority: [`RULE_CATALOG.md`](../../RULE_CATALOG.md) Item 5; [`Data_Goverence.txt`](../../../../QLA_Migration/Data_Goverence.txt) lines 90–94; [`QuikDate_Schema_Verification.md`](../../QuikDate_Schema_Verification.md).

---

## 2. Live inventory (read 2026-07-18)

**File:** `Q:\CSO\CSO_Test_6_30_2026\QUIKDATE.dbf` — **1** row

| Field | Current value | Governance required (run 2026-07-18) | Status |
|-------|---------------|--------------------------------------|--------|
| PACBILL | 2004-12-05 | 2026-06-30 | FAIL (stale) |
| DIRBILL | 2004-12-19 | 2026-06-30 | FAIL (stale) |
| REINBILL | null | 2026-06-30 | FAIL (null) |
| ACHFILEID | 0 | 0 | PASS |
| ACHFILEID2 | A | A | PASS |
| ESC_DATE | blank | blank | PASS |
| PROCDATE | 2026-07-18 | (not in Item 5 bill rules) | Informational |

### Other date fields present (not in DG-R-003 scope)

| Field | Current | Note |
|-------|---------|------|
| GRPBILL | 2004-12-31 | Stale; not required by DG-QUIKDATE-001..006 |
| APLBILL | 2004-11-30 | Stale; out of scope |
| LOANBILL | 2004-11-30 | Stale; out of scope |
| CPNBILL | (present) | Out of scope |
| CCBILL | 2011-02-24 | Stale; out of scope |
| ANNDATE | (present) | Out of scope |

Baseline pasted report matches PAC/DIR/REIN findings exactly.

---

## 3. Options (business decision)

### Option A — Set the three bill dates to prior month-end `2026-06-30` (recommended)

**Action:** On the single QuikDate row:

- `PACBILL` = 2026-06-30  
- `DIRBILL` = 2026-06-30  
- `REINBILL` = 2026-06-30  

Leave ACHFILEID / ACHFILEID2 / ESC_DATE / PROCDATE / other *BILL fields unchanged.

| Pros | Cons |
|------|------|
| Clears DG-QUIKDATE-001/002/003 for July 2026 governance runs | If ops cycle is not June month-end close, date may be wrong for business |
| Matches baseline “required” value and catalog rule | Next month’s governance run will expect **2026-07-31** — dates must be refreshed each cycle |
| Tiny blast radius (1 row, 3 fields) | Does not refresh GRPBILL / APLBILL / etc. |

### Option B — Set to a user-specified ops cycle date

Same three fields, but to a date you name (e.g. `2025-12-31` if that is the intended close). Governance will still FAIL until the run date’s prior-month-end matches that value.

### Option C — Expand scope: also refresh other stale *BILL dates

Set GRPBILL / APLBILL / LOANBILL / CCBILL / etc. to the same prior-month-end (or another rule). **Not required** by current governance Item 5. Higher product/ops risk.

### Option D — Defer until data-region path is confirmed

If `CSO_Test_6_30_2026` is not the right folder, stop.

---

## 4. Dependencies

| Item | Relationship |
|------|----------------|
| DG-R-001 | CLOSED; List empty confirms we are on the post-001 region (if 2026 folder is the rename) |
| Later items | None |

**Operational caveat:** These three dates are **cycle-dependent**. Fixing to 2026-06-30 is correct for governance run dates in July 2026 only.

---

## 5. Recommended option (discussion — not a decision)

**Option A** on `Q:\CSO\CSO_Test_6_30_2026`, after you confirm the folder rename.

---

## 6. Validation (after Implement)

```bash
python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2026" --output "<item>/validation_out" --item DG-QUIKDATE
```

Expect: DG-QUIKDATE-001/002/003 Passed when run date is in July 2026 (expected 2026-06-30).  
004/005/006 should remain Passed.

---

## 7. Regression guards

- QuikDate row count remains 1  
- ACHFILEID / ACHFILEID2 / ESC_DATE unchanged  
- PROCDATE unchanged unless you explicitly expand scope  
- No QuikPlan / QuikList / QuikChrt edits under this item  
- DG-R-001 CLOSED outcomes still hold (QuikList empty; no G/V on Chrt)

---

## 8. What we need from you

1. Confirm data region: **`Q:\CSO\CSO_Test_6_30_2026`** (rename of 6_30_2025)?  
2. Decision: **A / B / C / D**  
3. If B: the exact target date  

Example:

`Decision: Option A — set PACBILL/DIRBILL/REINBILL to 2026-06-30 on Q:\CSO\CSO_Test_6_30_2026`
