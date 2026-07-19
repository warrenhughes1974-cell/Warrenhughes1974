# DG-R-005 — Regression

**Date:** 2026-07-18  
**Result:** **PASS** (prior CLOSED items hold; only HCOMMIP/HRIGPKEY on CSO QuikPlan mutated; no WPA writes)

---

## Guards checked

### 1. DG-R-004 — MNAICLOB still NAPLAN

| Check | Expected | Result |
|-------|----------|--------|
| QuikPlan `MNAICLOB` | NAPLAN × 142 | **NAPLAN × 142** |
| DG-QUIKPLAN-024 rule text | NAPLAN (from R1) | **Not edited** this item |

### 2. DG-R-003 — QuikDate unchanged

| Field | Expected | Result |
|-------|----------|--------|
| PACBILL | 2026-06-30 | **2026-06-30** |
| DIRBILL | 2026-06-30 | **2026-06-30** |
| REINBILL | 2026-06-30 | **2026-06-30** |

QuikDate DBF not opened for write under DG-R-005.

### 3. DG-R-001 — QuikList still empty

| Check | Expected | Result |
|-------|----------|--------|
| QuikList row count | 0 | **0** |

### 4. No WPA writes

| Check | Result |
|-------|--------|
| WPA path written? | **No** |
| `Q:\WPA\WPA_GABIE\QuikPlan.dbf` mtime | 2026-07-14 09:18:23 (unchanged; CSO written 2026-07-18 19:13:42) |

### 5. Rule / conversion blast radius

| Check | Result |
|-------|--------|
| DG-QUIKPLAN-030 implementation | **Unchanged** |
| `app.py` / converters | **Unchanged** |
| APP_VERSION | **No bump** |
| Sync_Rulebook HCOMMIP/HRIGPKEY | Still blank (no change) |

### 6. Non-target QuikPlan fields

Only `HCOMMIP` and `HRIGPKEY` written via `dbf.write`. Other columns (PLANTYPE blank, MNAICLOB NAPLAN, etc.) remain as pre-apply.

---

## Residuals (not blocking)

| Item | Detail |
|------|--------|
| PLANTYPE blank on all 142 | Still blank; flags correctly False for non-MEDS. Future MEDS plans must set both True (rule 030). |
| WPA production QuikPlan | Out of scope; still inventoriable/approvable separately |
| Sync_Rulebook blank defaults | Optional emit default False-unless-MEDS deferred; blank today does not emit invalid `?` logicals |

---

## Suggested tracker status

**CLOSED** — control tower to confirm artifacts and open DG-R-006.
