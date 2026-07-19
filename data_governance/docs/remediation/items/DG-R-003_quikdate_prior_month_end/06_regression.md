# DG-R-003 — Regression

**Date:** 2026-07-18  
**Result:** **PASS** (DG-R-001 still holds; non-target QuikDate fields unchanged; unrelated conversion code untouched)

---

## Guards checked

### 1. DG-R-001 CLOSED outcomes

| Check | Result |
|-------|--------|
| QuikList row count | **0** (still empty after DG-R-001 deletes) |
| QuikDate row count | **1** (unchanged) |

### 2. Non-target QuikDate fields unchanged

Compared live post-apply values to pre-apply / backup:

| Field | Expected | Result |
|-------|----------|--------|
| ACHFILEID | 0 | Unchanged |
| ACHFILEID2 | A | Unchanged |
| ESC_DATE | blank | Unchanged |
| PROCDATE | 2026-07-18 | Unchanged |
| GRPBILL | 2004-12-31 | Unchanged |
| APLBILL | 2004-11-30 | Unchanged |
| LOANBILL | 2004-11-30 | Unchanged |
| CCBILL | 2011-02-24 | Unchanged |
| VERSION / UPDATENUM | prior values | Unchanged |

Only PACBILL / DIRBILL / REINBILL differ from backup (expected).

### 3. QuikPlan / QuikList / QuikChrt

| Table | Edited under DG-R-003? |
|-------|------------------------|
| QuikPlan | **No** |
| QuikList | **No** |
| QuikChrt | **No** |

### 4. Conversion blast radius

| Check | Result |
|-------|--------|
| New module | `qla_core/quikdate_converter.py` only |
| Hook | Thin batch finale in both `app.py` copies |
| Other converters modified? | **No** |
| APP_VERSION bumped both files? | **Yes** — `v58.07` |

---

## Residuals (not blocking)

| Item | Detail |
|------|--------|
| Stale other *BILL dates | GRPBILL / APLBILL / LOANBILL / CCBILL remain historical — out of DG-R-003 scope |
| Cycle dependency | Live 2026-06-30 is correct for July 2026 governance runs only; conversion emit is dynamic per run date |
| Quikdate CSV in Output | New for load package when batch runs — intentional per decision |

---

## Suggested tracker status

**CLOSED** — live patch validated; conversion emit in place at `v58.07`.
